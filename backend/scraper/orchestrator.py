"""Coordinate Tier 1 http, Tier 2 Playwright, Tier 3 Apify."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import httpx

from models.schemas import ScrapedContent, ScrapedPage
from scraper.apify_scraper import markdown_from_apify_items, run_apify_crawl
from scraper.content_extractor import (
    estimate_tokens,
    extract_clean_text_from_html,
    word_count_text,
)
from scraper.http_scraper import http_get_html, is_js_rendered_hint
from scraper.playwright_scraper import playwright_fetch_html
from scraper.url_utils import (
    construct_high_value_urls,
    discover_links,
    normalize_url,
    prioritize_discovered_urls,
)

logger = logging.getLogger(__name__)


@dataclass
class _PageAccum:
    summaries: list[str] = field(default_factory=list)
    scraped_pages: list[ScrapedPage] = field(default_factory=list)
    homepage_text: str = ""
    about_text: str = ""
    about_available: bool = False
    careers_available: bool = False
    career_titles: list[str] = field(default_factory=list)
    career_desc: list[str] = field(default_factory=list)
    blog_excerpts: list[str] = field(default_factory=list)
    press_excerpts: list[str] = field(default_factory=list)
    pages_scraped: int = 0
    pages_blocked: int = 0
    thin_pages: int = 0
    tier_used: str = "http"
    blocked: bool = False


async def _fetch_page_html(url: str, client: httpx.AsyncClient) -> tuple[Optional[str], bool]:
    res = await http_get_html(url, client)
    if res.html and res.status_code < 400:
        return res.html, False
    if res.status_code in (403, 429, 503):
        return None, True
    return None, False


async def _fetch_with_escalation(url: str, client: httpx.AsyncClient) -> tuple[Optional[str], bool]:
    html, blocked = await _fetch_page_html(url, client)
    if html:
        return html, blocked
    wb = f"https://web.archive.org/web/{url}"
    res = await http_get_html(wb, client)
    if res.html and res.status_code < 400:
        return res.html, False
    return html, blocked


def _classify_url(url: str) -> str:
    low = url.lower()
    path = urlparse(url).path.rstrip("/") or "/"
    if path == "/":
        return "home"
    if any(x in low for x in ("/career", "/jobs", "/join", "/open-position")):
        return "careers"
    if any(x in low for x in ("/about", "/company", "/who-we-are", "/our-story")):
        return "about"
    if any(x in low for x in ("/blog", "/resources", "/insights", "/newsroom")):
        return "blog"
    if any(x in low for x in ("/press", "/news", "/announcement")):
        return "press"
    return "other"


def _merge_rollups(acc: _PageAccum, url: str, extracted: dict, thin: bool) -> None:
    cat = _classify_url(url)
    if thin:
        acc.thin_pages += 1
    full = (extracted.get("full_text") or "").strip()
    acc.summaries.append(full)
    acc.pages_scraped += 1
    if cat == "home":
        acc.homepage_text = full[:12000]
    elif cat == "about":
        acc.about_text = full[:12000]
        acc.about_available = True
    elif cat == "careers":
        acc.careers_available = True
        for jb in extracted.get("job_blocks", []):
            t = jb.get("title", "")
            if t and t not in acc.career_titles:
                acc.career_titles.append(t)
            d = jb.get("description", "")
            if d:
                acc.career_desc.append(d)
    elif cat == "blog":
        acc.blog_excerpts.append(full[:1200])
    elif cat == "press":
        acc.press_excerpts.append(full[:1200])


def _scraped_page_ok(
    url: str,
    extracted: dict,
    *,
    blocked_http: bool,
    used_playwright: bool,
) -> ScrapedPage:
    thin = bool(extracted.get("thin"))
    return ScrapedPage(
        url=url,
        page_kind=_classify_url(url),
        extraction_ok=True,
        blocked_http=blocked_http,
        rendered_with_playwright=used_playwright,
        thin_content=thin,
        word_count=int(extracted.get("word_count") or 0),
        title=str(extracted.get("title") or ""),
        meta_description=str(extracted.get("meta_description") or ""),
        headings_h1=list(extracted.get("h1") or []),
        headings_h2=list(extracted.get("h2") or []),
        paragraphs=list(extracted.get("paragraphs") or []),
        list_items=list(extracted.get("list_items") or []),
        job_postings=[
            {"title": str(jb.get("title", "")), "description": str(jb.get("description", ""))}
            for jb in (extracted.get("job_blocks") or [])
        ],
        full_text=str(extracted.get("full_text") or ""),
    )


async def _fetch_and_extract_one_page(
    url: str, client: httpx.AsyncClient
) -> tuple[str, bool, Optional[dict], bool]:
    """Fetch one URL, optional Playwright escalation.

    Returns ``(url, blocked_when_empty, extracted_or_none, used_playwright)``.
    """
    html, blocked_flag = await _fetch_with_escalation(url, client)
    if not html:
        return url, blocked_flag, None, False
    extracted = extract_clean_text_from_html(html, url)
    used_playwright = False
    if is_js_rendered_hint(html, extracted["word_count"]) and extracted["word_count"] < 400:
        pw_html = await playwright_fetch_html(url)
        if pw_html:
            extracted = extract_clean_text_from_html(pw_html, url)
            used_playwright = True
    return url, blocked_flag, extracted, used_playwright


async def scrape_domain(raw_url: str, apify_token: str = "") -> ScrapedContent:
    nu = normalize_url(raw_url)
    domain = nu.domain
    logger.info("[scraper] step=start domain=%s raw_url=%s apify=%s", domain, raw_url, bool(apify_token))
    acc = _PageAccum()

    limits = httpx.Limits(max_connections=50, max_keepalive_connections=25)
    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        discovered = await discover_links(domain, client)
        ranked = prioritize_discovered_urls(discovered)[:30]
        guessed = [u for _, u in construct_high_value_urls(domain)]

        urls: list[str] = []
        seen: set[str] = set()

        def add(u: str) -> None:
            if u not in seen:
                seen.add(u)
                urls.append(u)

        add(nu.https_url)
        for u in ranked:
            add(u)
        for u in guessed:
            add(u)

        urls = urls[:14]

        page_results = await asyncio.gather(
            *(_fetch_and_extract_one_page(u, client) for u in urls),
            return_exceptions=True,
        )
        for idx, item in enumerate(page_results):
            page_url = urls[idx]
            if isinstance(item, BaseException):
                logger.warning(
                    "[scraper] step=page_fetch domain=%s url=%s error=%s",
                    domain,
                    page_url,
                    item,
                )
                acc.pages_blocked += 1
                acc.scraped_pages.append(
                    ScrapedPage(
                        url=page_url,
                        page_kind=_classify_url(page_url),
                        extraction_ok=False,
                        fetch_exception=f"{type(item).__name__}: {item}"[:500],
                    )
                )
                continue
            _, blocked_flag, extracted, used_playwright = item
            if extracted is None:
                acc.pages_blocked += 1
                acc.blocked = acc.blocked or blocked_flag
                acc.scraped_pages.append(
                    ScrapedPage(
                        url=page_url,
                        page_kind=_classify_url(page_url),
                        extraction_ok=False,
                        blocked_http=blocked_flag,
                    )
                )
                continue
            if used_playwright:
                acc.tier_used = "playwright"
            thin = bool(extracted.get("thin"))
            acc.scraped_pages.append(
                _scraped_page_ok(
                    page_url,
                    extracted,
                    blocked_http=blocked_flag,
                    used_playwright=used_playwright,
                )
            )
            _merge_rollups(acc, page_url, extracted, thin)

    total_words = sum(len(s.split()) for s in acc.summaries)
    if (acc.pages_blocked >= len(urls) or total_words < 120) and apify_token:
        logger.info(
            "[scraper] step=apify_escalation domain=%s pages_blocked=%s total_words=%s",
            domain,
            acc.pages_blocked,
            total_words,
        )
        try:
            items = await asyncio.to_thread(run_apify_crawl, f"https://{domain}", apify_token)
            md = markdown_from_apify_items(items)
            if md:
                wc = word_count_text(md)
                thin_agg = wc < 150
                acc.scraped_pages.append(
                    ScrapedPage(
                        url=f"https://{domain}/",
                        page_kind="crawl_aggregate",
                        extraction_ok=True,
                        thin_content=thin_agg,
                        word_count=wc,
                        full_text=md,
                    )
                )
                acc.summaries.append(md)
                acc.pages_scraped += 1
                if thin_agg:
                    acc.thin_pages += 1
                acc.tier_used = "apify"
                if not acc.homepage_text:
                    acc.homepage_text = md[:8000]
                logger.info("[scraper] step=apify_escalation domain=%s ok=true chars=%s", domain, len(md))
            else:
                logger.info("[scraper] step=apify_escalation domain=%s ok=false empty_markdown", domain)
        except Exception:
            logger.exception("[scraper] step=apify_escalation domain=%s failed", domain)

    scrape_quality = "high"
    if acc.blocked and acc.pages_scraped == 0:
        scrape_quality = "blocked"
    elif acc.thin_pages >= max(1, acc.pages_scraped // 2) and acc.pages_scraped > 0:
        scrape_quality = "thin"
    elif acc.thin_pages > 0 or total_words < 400:
        scrape_quality = "medium"

    career_summary = "\n".join(acc.career_desc[:30])[:8000]
    joined = "\n\n".join(p.full_text for p in acc.scraped_pages if p.full_text)
    if not joined.strip():
        joined = "\n\n".join(acc.summaries)
    token_estimate = estimate_tokens(joined)

    logger.info(
        "[scraper] step=complete domain=%s scrape_quality=%s tier_used=%s "
        "pages_scraped=%s pages_blocked=%s thin_pages=%s token_estimate=%s "
        "careers_available=%s scraped_page_records=%s",
        domain,
        scrape_quality,
        acc.tier_used,
        acc.pages_scraped,
        acc.pages_blocked,
        acc.thin_pages,
        token_estimate,
        acc.careers_available,
        len(acc.scraped_pages),
    )

    return ScrapedContent(
        domain=domain,
        homepage_text=acc.homepage_text or joined[:4000],
        about_text=acc.about_text,
        about_available=acc.about_available,
        careers_page_available=acc.careers_available,
        career_titles=acc.career_titles,
        career_descriptions_summary=career_summary,
        blog_excerpts=acc.blog_excerpts[:10],
        press_excerpts=acc.press_excerpts[:10],
        total_pages_scraped=acc.pages_scraped,
        pages_blocked=acc.pages_blocked,
        thin_content_pages=acc.thin_pages,
        scrape_quality=scrape_quality,
        token_count_estimate=token_estimate,
        js_rendered_only=acc.tier_used == "playwright",
        scrape_blocked=acc.blocked and acc.pages_scraped == 0,
        tier_used=acc.tier_used,
        raw_page_summaries=acc.summaries[:20],
        scraped_pages=acc.scraped_pages,
    )
