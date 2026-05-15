"""Gemini client with retries."""

from __future__ import annotations

import logging
import time
from typing import Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)

from ai.prompts import LANDING_PAGE_SYSTEM_PROMPT, SYSTEM_INSTRUCTION, build_user_payload
from config import get_settings
from models.schemas import EnrichmentResult, ScrapedContent


def enrich_with_gemini(scraped: ScrapedContent, source_url: str) -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set")

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    user_text = build_user_payload(scraped, source_url) + "\nSet domain to: " + scraped.domain

    print("="*100)
    logger.info(f"System instruction: {SYSTEM_INSTRUCTION}")
    print("="*100)
    logger.info(f"User text: {user_text}")
    print("="*100)

    # delays = [2, 4, 8]
    delays = [2]
    # attempts_total = 1 + len(delays)
    attempts_total = 1
    last_err: Optional[Exception] = None
    for attempt, delay in enumerate([0, *delays]):
        if delay:
            logger.info(
                "[gemini] step=retry_backoff source_url=%s sleep_s=%s next_attempt=%s/%s",
                source_url,
                delay,
                attempt + 1,
                attempts_total,
            )
            time.sleep(delay)
        try:
            logger.info(
                "[gemini] step=generate_content attempt=%s/%s domain=%s",
                attempt + 1,
                attempts_total,
                scraped.domain,
            )
            resp = model.generate_content(
                user_text,
                generation_config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json",
                },
            )
            text = (resp.text or "").strip()
            if not text:
                last_err = RuntimeError("Empty Gemini response")
                logger.warning(
                    "[gemini] step=generate_content attempt=%s empty_response",
                    attempt + 1,
                )
                continue
            logger.info(
                "[gemini] step=generate_content ok attempt=%s response_chars=%s",
                attempt + 1,
                len(text),
            )
            return text
        except Exception as e:
            last_err = e
            logger.warning(
                "[gemini] step=generate_content attempt=%s error=%s",
                attempt + 1,
                e,
            )
            continue
    raise RuntimeError(f"Gemini failed after retries: {last_err}")


def generate_landing_content(enrichment_json: str, domain: str) -> str:
    """Second Gemini pass: rich landing page JSON from enrichment profile."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set")

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        system_instruction=LANDING_PAGE_SYSTEM_PROMPT,
    )
    user_text = (
        "Below is the structured intelligence profile JSON for this prospect. "
        "Use it as the sole input for personalization. Return only the landing page JSON as instructed.\n\n"
        f"domain: {domain}\n\n"
        " prospect_profile_json:\n"
        f"{enrichment_json.strip()}"
    )

    delays = [2]
    attempts_total = 1
    last_err: Optional[Exception] = None
    for attempt, delay in enumerate([0, *delays]):
        if delay:
            logger.info(
                "[gemini] landing_page retry_backoff domain=%s sleep_s=%s next_attempt=%s/%s",
                domain,
                delay,
                attempt + 1,
                attempts_total,
            )
            time.sleep(delay)
        try:
            logger.info(
                "[gemini] landing_page generate_content attempt=%s/%s domain=%s",
                attempt + 1,
                attempts_total,
                domain,
            )
            resp = model.generate_content(
                user_text,
                generation_config={
                    "temperature": 0.25,
                    "response_mime_type": "application/json",
                },
            )
            text = (resp.text or "").strip()
            if not text:
                last_err = RuntimeError("Empty Gemini landing page response")
                logger.warning(
                    "[gemini] landing_page generate_content attempt=%s empty_response",
                    attempt + 1,
                )
                continue
            logger.info(
                "[gemini] landing_page generate_content ok attempt=%s response_chars=%s",
                attempt + 1,
                len(text),
            )
            return text
        except Exception as e:
            last_err = e
            logger.warning(
                "[gemini] landing_page generate_content attempt=%s error=%s",
                attempt + 1,
                e,
            )
            continue
    raise RuntimeError(f"Gemini landing page failed after retries: {last_err}")


def enrich_stub(scraped: ScrapedContent, source_url: str) -> EnrichmentResult:
    """Used when API key missing in dev."""
    return EnrichmentResult(
        company_name=scraped.domain.split(".")[0].title(),
        domain=scraped.domain,
        data_confidence="low",
        confidence_rationale="Stub mode: no GEMINI_API_KEY",
        icp_scoring_rationale="Stub",
        requires_review=True,
    )
