"""Tier 3: Apify Website Content Crawler fallback."""

from __future__ import annotations

from typing import Any, Optional

from apify_client import ApifyClient


ACTOR_ID = "aYG0l9s7dbB7j3gbS"


def run_apify_crawl(start_url: str, token: str) -> list[dict[str, Any]]:
    if not token:
        return []
    client = ApifyClient(token)
    run_input = {
        "startUrls": [{"url": start_url}],
        "crawlerType": "playwright:adaptive",
        "includeUrlGlobs": [],
        "excludeUrlGlobs": [],
        "maxCrawlDepth": 2,
        "maxCrawlPages": 25,
        "useSitemaps": True,
        "respectRobotsTxtFile": True,
        "proxyConfiguration": {"useApifyProxy": True},
        "requestTimeoutSecs": 60,
        "dynamicContentWaitSecs": 10,
        "removeCookieWarnings": True,
        "blockMedia": True,
        "saveMarkdown": True,
        "saveHtml": False,
        "htmlTransformer": "readableText",
        "removeElementsCssSelector": (
            "nav, footer, script, style, noscript, svg, img[src^='data:'],"
            '[role="alert"],[role="banner"],[role="dialog"]'
        ),
    }
    run = client.actor(ACTOR_ID).call(run_input=run_input, wait_secs=300)
    items: list[dict[str, Any]] = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        items.append(item)
    return items


def markdown_from_apify_items(items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for it in items:
        md = it.get("markdown") or it.get("text") or ""
        url = it.get("url") or it.get("loadedUrl") or ""
        if md:
            parts.append(f"## {url}\n{md}")
    return "\n\n".join(parts)
