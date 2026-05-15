"""URL normalization, sitemap discovery, high-value path construction."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse, urlunparse

import httpx

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 PrismBot/1.0"
)


@dataclass
class NormalizedUrl:
    original: str
    https_url: str
    domain: str


def normalize_url(raw: str) -> NormalizedUrl:
    raw = raw.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    parsed = urlparse(raw)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/") or ""
    cleaned = urlunparse(("https", netloc, path, "", "", ""))
    return NormalizedUrl(original=raw, https_url=cleaned, domain=netloc)


HIGH_VALUE_PATH_PREFIXES = [
    ("about", 1),
    ("company", 1),
    ("who-we-are", 1),
    ("our-story", 1),
    ("careers", 2),
    ("jobs", 2),
    ("join-us", 2),
    ("open-positions", 2),
    ("products", 3),
    ("services", 3),
    ("solutions", 3),
    ("platform", 3),
    ("what-we-do", 3),
    ("blog", 4),
    ("resources", 4),
    ("insights", 4),
    ("newsroom", 4),
    ("press", 5),
    ("news", 5),
    ("announcements", 5),
    ("customers", 6),
    ("case-studies", 6),
    ("testimonials", 6),
]


def construct_high_value_urls(domain: str) -> list[tuple[int, str]]:
    """Return (priority, full_url) for direct URL guesses."""
    base = f"https://{domain}"
    out: list[tuple[int, str]] = []
    for prefix, pri in HIGH_VALUE_PATH_PREFIXES:
        out.append((pri, f"{base}/{prefix}"))
    return sorted(out, key=lambda x: x[0])


def _extract_sitemap_urls(xml_text: str, domain: str) -> list[str]:
    urls: list[str] = []
    for m in re.findall(r"<loc>([^<]+)</loc>", xml_text, re.I):
        m = m.strip()
        if domain in m:
            urls.append(m)
    return urls


async def discover_links(domain: str, client: httpx.AsyncClient) -> list[str]:
    """Fetch robots.txt and sitemap.xml for additional URLs."""
    found: set[str] = set()
    paths = ("/robots.txt", "/sitemap.xml", "/sitemap_index.xml")

    async def fetch_path(path: str) -> tuple[str, httpx.Response | None]:
        try:
            r = await client.get(f"https://{domain}{path}", timeout=15.0)
            return path, r
        except Exception:
            return path, None

    fetch_results = await asyncio.gather(*(fetch_path(p) for p in paths))

    sitemap_urls_to_fetch: list[str] = []
    for path, r in fetch_results:
        if r is None or r.status_code != 200:
            continue
        text = r.text
        if path == "/robots.txt" and "sitemap:" in text.lower():
            for line in text.splitlines():
                if line.lower().startswith("sitemap:"):
                    sm = line.split(":", 1)[1].strip()
                    if sm:
                        sitemap_urls_to_fetch.append(sm)
        elif "sitemap" in path and (
            "<urlset" in text.lower() or "<sitemapindex" in text.lower()
        ):
            found.update(_extract_sitemap_urls(text, domain))

    if sitemap_urls_to_fetch:
        async def fetch_sitemap(url: str) -> str | None:
            try:
                sr = await client.get(url, timeout=15.0)
                if sr.status_code == 200:
                    return sr.text
            except Exception:
                pass
            return None

        sm_texts = await asyncio.gather(*(fetch_sitemap(u) for u in sitemap_urls_to_fetch))
        for sm_text in sm_texts:
            if sm_text:
                found.update(_extract_sitemap_urls(sm_text, domain))

    return list(found)


def prioritize_discovered_urls(urls: Iterable[str]) -> list[str]:
    def score(u: str) -> tuple[int, str]:
        low = u.lower()
        best = 99
        for prefix, pri in HIGH_VALUE_PATH_PREFIXES:
            if f"/{prefix}" in low or low.rstrip("/").endswith(f"/{prefix}"):
                best = min(best, pri)
        return (best, u)

    return sorted(urls, key=score)
