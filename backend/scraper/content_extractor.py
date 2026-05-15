"""HTML/markdown cleaning and structured text extraction."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

TOKEN_APPROX_CHARS = 4  # rough chars per token


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def word_count_text(text: str) -> int:
    """Public word count for scraped blobs (e.g. Apify markdown)."""
    return _word_count(text)


def estimate_tokens(text: str) -> int:
    return max(1, len(text or "") // TOKEN_APPROX_CHARS)


def truncate_to_token_budget(text: str, max_tokens: int = 1500) -> str:
    max_chars = max_tokens * TOKEN_APPROX_CHARS
    if len(text) <= max_chars:
        return text
    # Keep first paragraph of each section heuristic: headings + first sentences
    parts: list[str] = []
    budget = max_chars
    for block in re.split(r"\n\s*\n", text):
        if budget <= 0:
            break
        if len(block) <= budget:
            parts.append(block)
            budget -= len(block)
        else:
            first_sentence = re.split(r"(?<=[.!?])\s+", block.strip(), maxsplit=1)[0]
            chunk = first_sentence[:budget]
            parts.append(chunk)
            break
    return "\n\n".join(parts)


JS_FRAMEWORK_MARKERS = (
    "__NEXT_DATA__",
    "data-reactroot",
    "nuxt",
    "__NUXT__",
    'id="__vue"',
    "vite",
    "astro",
)


def detect_js_heavy(html: str) -> bool:
    low = html.lower()
    return any(m.lower() in low for m in JS_FRAMEWORK_MARKERS)


def extract_clean_text_from_html(html: str, url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    for sel in [
        "nav",
        "footer",
        "header",
        '[role="navigation"]',
        '[role="banner"]',
        '[role="contentinfo"]',
        '[aria-modal="true"]',
        '[role="dialog"]',
    ]:
        for el in soup.select(sel):
            el.decompose()

    title = (soup.title.string or "").strip() if soup.title else ""
    meta_desc = ""
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        meta_desc = md["content"].strip()

    h1s = [" ".join(h.get_text(strip=True).split()) for h in soup.find_all("h1")]
    h2s = [" ".join(h.get_text(strip=True).split()) for h in soup.find_all("h2")[:80]]

    paragraphs: list[str] = []
    for p in soup.find_all("p"):
        t = " ".join(p.get_text(separator=" ", strip=True).split())
        if t:
            paragraphs.append(t)

    lists: list[str] = []
    for ul in soup.find_all(["ul", "ol"])[:80]:
        for li in ul.find_all("li", recursive=False):
            t = " ".join(li.get_text(separator=" ", strip=True).split())
            if t:
                lists.append(t)

    body = " ".join(soup.get_text(separator="\n", strip=True).split())
    full_text = "\n".join(
        [title, meta_desc, *h1s, *h2s, *paragraphs, *lists, body]
    )
    wc = _word_count(full_text)
    thin = wc < 150

    is_careers = any(
        x in url.lower()
        for x in ("/career", "/jobs", "/join-us", "/open-position", "greenhouse", "lever.co")
    )

    job_blocks: list[dict[str, str]] = []
    if is_careers:
        for h in soup.find_all(["h2", "h3", "h4", "a"]):
            title_j = " ".join(h.get_text(strip=True).split())
            if not title_j or len(title_j) > 120:
                continue
            if h.name == "a" and not h.get("href"):
                continue
            sib = h.find_next_sibling()
            desc = ""
            if sib:
                desc = " ".join(sib.get_text(separator=" ", strip=True).split())
            words = desc.split()
            if len(words) > 200:
                desc = " ".join(words[:200])
            if title_j:
                job_blocks.append({"title": title_j, "description": desc})

    return {
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "h1": h1s,
        "h2": h2s,
        "paragraphs": paragraphs,
        "list_items": lists,
        "full_text": full_text,
        "word_count": wc,
        "thin": thin,
        "job_blocks": job_blocks[:120],
        "js_heavy": detect_js_heavy(html),
    }


def summarize_page_for_llm(
    extracted: dict[str, Any], max_tokens: int = 1500
) -> tuple[str, bool, int]:
    header = f"URL: {extracted['url']}\nTitle: {extracted['title']}\n"
    meta = f"Meta: {extracted.get('meta_description', '')}\n"
    h1 = "H1: " + " | ".join(extracted.get("h1", [])) + "\n"
    h2 = "H2: " + " | ".join(extracted.get("h2", [])[:15]) + "\n"
    body = "\n".join(extracted.get("paragraphs", [])[:40])
    jobs = ""
    for jb in extracted.get("job_blocks", [])[:25]:
        jobs += f"\nJOB: {jb.get('title','')}\n{jb.get('description','')}\n"
    blob = header + meta + h1 + h2 + "\n" + body + jobs
    thin = bool(extracted.get("thin"))
    truncated = truncate_to_token_budget(blob, max_tokens)
    return truncated, thin, estimate_tokens(truncated)
