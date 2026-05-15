"""Apify actors: domain → LinkedIn company URL → LinkedIn company profile."""

from __future__ import annotations

import logging
from typing import Any, Optional

from apify_client import ApifyClient

logger = logging.getLogger(__name__)

RESOLVE_ACTOR_ID = "RaNQwAwEmV6jLk1jw"
COMPANY_SCRAPER_ACTOR_ID = "ipHw77V2NMJPy8sbS"


def resolve_linkedin_url(url_or_domain: str, token: str) -> Optional[str]:
    """Return linkedin_company_page URL from Apify domain resolver, or None."""
    if not token:
        return None
    try:
        client = ApifyClient(token)
        run_input = {"urlOrDomain": url_or_domain}
        run = client.actor(RESOLVE_ACTOR_ID).call(run_input=run_input, wait_secs=300)
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            url = (item.get("linkedin_company_page") or "").strip()
            if url:
                return url
    except Exception as e:
        logger.warning("[linkedin] resolve failed url_or_domain=%s error=%s", url_or_domain, e)
    return None


def scrape_linkedin_company(linkedin_url: str, token: str) -> Optional[dict[str, Any]]:
    """Fetch first LinkedIn company profile item from Apify dataset, or None."""
    if not token or not linkedin_url:
        return None
    try:
        client = ApifyClient(token)
        run_input = {"identifier": [linkedin_url]}
        run = client.actor(COMPANY_SCRAPER_ACTOR_ID).call(run_input=run_input, wait_secs=300)
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            if item:
                return item
    except Exception as e:
        logger.warning("[linkedin] company_scrape failed url=%s error=%s", linkedin_url, e)
    return None
