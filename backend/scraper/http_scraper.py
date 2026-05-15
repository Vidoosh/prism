"""Tier 1: httpx + BeautifulSoup fetch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx

from scraper.content_extractor import extract_clean_text_from_html
from scraper.url_utils import USER_AGENT


@dataclass
class HttpFetchResult:
    url: str
    status_code: int
    html: Optional[str]
    error: Optional[str] = None


async def http_get_html(url: str, client: httpx.AsyncClient) -> HttpFetchResult:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        r = await client.get(url, headers=headers, follow_redirects=True, timeout=15.0)
        if r.status_code >= 400:
            return HttpFetchResult(url=url, status_code=r.status_code, html=None, error=f"HTTP {r.status_code}")
        ctype = r.headers.get("content-type", "")
        if "text/html" not in ctype and "application/xhtml" not in ctype:
            return HttpFetchResult(url=url, status_code=r.status_code, html=r.text, error="non-html")
        return HttpFetchResult(url=url, status_code=r.status_code, html=r.text)
    except Exception as e:
        return HttpFetchResult(url=url, status_code=0, html=None, error=str(e))


def is_js_rendered_hint(html: Optional[str], word_count: int) -> bool:
    if not html:
        return True
    if word_count < 300:
        low = html.lower()
        if any(x in low for x in ("__next", "react", "vue", "nuxt", "svelte", "webpack")):
            return True
    return False
