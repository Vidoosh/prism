"""Gemini + Google Search grounding for open-web domain intelligence (google-genai SDK)."""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from google import genai
from google.genai import types

from ai.response_parser import parse_json_object

from ai.prompts import (
    GOOGLE_SEARCH_RESEARCH_SYSTEM_INSTRUCTION,
    build_google_search_research_user_prompt,
)
from config import get_settings

logger = logging.getLogger(__name__)


def research_domain_with_google_search(domain: str, source_url: str) -> Optional[dict[str, Any]]:
    """Run Gemini with Google Search; return structured research dict or None on failure."""
    settings = get_settings()
    if not settings.gemini_api_key:
        logger.info("[web_research] skipped reason=no_gemini_api_key")
        return None

    client = genai.Client(api_key=settings.gemini_api_key)
    user_prompt = build_google_search_research_user_prompt(domain, source_url)
    model_id = settings.gemini_google_search_model

    config = types.GenerateContentConfig(
        system_instruction=GOOGLE_SEARCH_RESEARCH_SYSTEM_INSTRUCTION,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.2,
    )

    delays = [2, 4, 8]
    attempts_total = 1
    last_err: Optional[Exception] = None
    for attempt, delay in enumerate([0, *delays]):
        if delay:
            logger.info(
                "[web_research] retry_backoff domain=%s sleep_s=%s attempt=%s/%s",
                domain,
                delay,
                attempt + 1,
                attempts_total,
            )
            time.sleep(delay)
        try:
            logger.info(
                "[web_research] generate_content attempt=%s/%s domain=%s model=%s",
                attempt + 1,
                attempts_total,
                domain,
                model_id,
            )
            response = client.models.generate_content(
                model=model_id,
                contents=user_prompt,
                config=config,
            )
            text = (response.text or "").strip()
            if not text:
                last_err = RuntimeError("Empty Gemini web_research response")
                continue
            parsed = parse_json_object(text)
            logger.info(
                "[web_research] ok attempt=%s domain=%s keys=%s",
                attempt + 1,
                domain,
                list(parsed.keys())[:12],
            )
            return parsed
        except Exception as e:
            last_err = e
            logger.warning(
                "[web_research] attempt=%s/%s domain=%s error=%s",
                attempt + 1,
                attempts_total,
                domain,
                e,
            )
            continue

    logger.warning("[web_research] failed domain=%s after_retries error=%s", domain, last_err)
    return None
