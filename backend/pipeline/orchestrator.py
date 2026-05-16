"""End-to-end single-URL pipeline execution."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from ai.gemini_client import enrich_stub, enrich_with_gemini, generate_landing_content
from ai.response_parser import parse_enrichment_json
from ai.web_research import research_domain_with_google_search
from config import get_settings
from integrations.hubspot_client import upsert_company_record
from integrations.sanity_client import set_hubspot_company_id, upsert_account_with_history
from models.schemas import EnrichmentResult, PipelineRunResult, ScrapedContent, StageStatus
from pipeline import dead_letter, storage
from scraper.linkedin_scraper import resolve_linkedin_url, scrape_linkedin_company
from scraper.orchestrator import scrape_domain
from scraper.url_utils import normalize_url

logger = logging.getLogger(__name__)


def _ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def build_landing_url(domain: str) -> str:
    settings = get_settings()
    slug = domain.replace(".", "-").lower()
    return f"{settings.frontend_url.rstrip('/')}/lp/{slug}"


def build_sanity_manage_url(domain: str) -> str:
    settings = get_settings()
    if settings.sanity_studio_url:
        base = settings.sanity_studio_url.rstrip("/")
        return f"{base}/structure/accountResearchProfile;account-{domain}"
    pid = settings.sanity_project_id
    if pid:
        return f"https://www.sanity.io/manage/personal/project/{pid}"
    return ""


def build_hubspot_record_url(company_id: str) -> str:
    settings = get_settings()
    if settings.hubspot_portal_id:
        return (
            f"https://app.hubspot.com/contacts/{settings.hubspot_portal_id}/record/0-2/{company_id}"
        )
    return f"https://app.hubspot.com/contacts/company/{company_id}"


async def _do_scrape(
    source_url: str,
    apify_token: str,
    rid: str,
    domain: str,
) -> tuple[ScrapedContent, StageStatus]:
    """Run domain scrape; on failure return minimal ScrapedContent and dead-letter."""
    t0 = time.perf_counter()
    logger.info("[pipeline] step=scrape run_id=%s domain=%s start", rid, domain)
    try:
        scraped = await scrape_domain(source_url, apify_token)
        logger.info(
            "[pipeline] step=scrape run_id=%s domain=%s ok=true duration_ms=%s "
            "quality=%s tier=%s pages=%s tokens_est=%s blocked=%s",
            rid,
            domain,
            _ms(t0),
            scraped.scrape_quality,
            scraped.tier_used,
            scraped.total_pages_scraped,
            scraped.token_count_estimate,
            scraped.scrape_blocked,
        )
        return scraped, StageStatus(stage="scrape", ok=True, duration_ms=_ms(t0))
    except Exception as e:
        logger.exception(
            "[pipeline] step=scrape run_id=%s domain=%s ok=false duration_ms=%s",
            rid,
            domain,
            _ms(t0),
        )
        dead_letter.enqueue("scrape", domain, str(e), {"url": source_url})
        scraped = ScrapedContent(domain=domain, scrape_quality="blocked", scrape_blocked=True)
        logger.warning(
            "[pipeline] step=scrape_fallback run_id=%s domain=%s using_minimal_scraped_bundle",
            rid,
            domain,
        )
        return scraped, StageStatus(stage="scrape", ok=False, message=str(e), duration_ms=_ms(t0))


async def _do_linkedin(
    source_url: str,
    apify_token: str,
    rid: str,
    domain: str,
) -> tuple[Optional[dict[str, Any]], StageStatus]:
    """Resolve + scrape LinkedIn via Apify; skipped when no token."""
    t_li = time.perf_counter()
    if not apify_token:
        return None, StageStatus(stage="linkedin", ok=True, duration_ms=_ms(t_li))
    try:
        url_or_domain = (source_url.strip() if source_url else "").strip() or f"https://{domain}/"
        logger.info(
            "[pipeline] step=linkedin run_id=%s domain=%s url_or_domain=%s start",
            rid,
            domain,
            url_or_domain,
        )
        linkedin_page = await asyncio.to_thread(
            resolve_linkedin_url, url_or_domain, apify_token
        )
        profile: Optional[dict[str, Any]] = None
        if linkedin_page:
            profile = await asyncio.to_thread(
                scrape_linkedin_company, linkedin_page, apify_token
            )
            if profile:
                logger.info(
                    "[pipeline] step=linkedin run_id=%s domain=%s ok=profile_chars=%s",
                    rid,
                    domain,
                    len(str(profile)),
                )
            else:
                logger.info(
                    "[pipeline] step=linkedin run_id=%s domain=%s no_company_dataset_item",
                    rid,
                    domain,
                )
        else:
            logger.info(
                "[pipeline] step=linkedin run_id=%s domain=%s no_linkedin_url_resolved",
                rid,
                domain,
            )
        return profile, StageStatus(stage="linkedin", ok=True, duration_ms=_ms(t_li))
    except Exception as e:
        logger.warning(
            "[pipeline] step=linkedin run_id=%s domain=%s ok=false error=%s",
            rid,
            domain,
            e,
        )
        return None, StageStatus(
            stage="linkedin",
            ok=False,
            message=str(e),
            duration_ms=_ms(t_li),
        )


async def _do_web_research(
    domain: str,
    source_url: str,
    gemini_api_key: str,
    rid: str,
) -> tuple[Optional[dict[str, Any]], StageStatus]:
    """Gemini + Google Search open-web research; skipped when no API key."""
    t_wr = time.perf_counter()
    if not gemini_api_key:
        return None, StageStatus(stage="web_research", ok=True, duration_ms=_ms(t_wr))
    try:
        logger.info(
            "[pipeline] step=web_research run_id=%s domain=%s start",
            rid,
            domain,
        )
        dossier = await asyncio.to_thread(
            research_domain_with_google_search, domain, source_url
        )
        if dossier:
            logger.info(
                "[pipeline] step=web_research run_id=%s domain=%s ok=keys=%s",
                rid,
                domain,
                list(dossier.keys())[:10],
            )
        else:
            logger.info(
                "[pipeline] step=web_research run_id=%s domain=%s no_dossier",
                rid,
                domain,
            )
        return dossier, StageStatus(stage="web_research", ok=True, duration_ms=_ms(t_wr))
    except Exception as e:
        logger.warning(
            "[pipeline] step=web_research run_id=%s domain=%s ok=false error=%s",
            rid,
            domain,
            e,
        )
        return None, StageStatus(
            stage="web_research",
            ok=False,
            message=str(e),
            duration_ms=_ms(t_wr),
        )


async def run_pipeline(source_url: str, run_id: str | None = None) -> PipelineRunResult:
    rid = run_id or str(uuid.uuid4())
    stages: list[StageStatus] = []
    settings = get_settings()
    t_pipeline_start = time.perf_counter()

    logger.info("[pipeline] step=start run_id=%s source_url=%s", rid, source_url)

    result = PipelineRunResult(
        run_id=rid,
        status="running",
        source_url=source_url,
        updated_at=datetime.now(timezone.utc),
    )
    storage.save_run(result)
    logger.info("[pipeline] step=persist_initial run_id=%s status=running", rid)

    scraped: Optional[ScrapedContent] = None
    enrichment: Optional[EnrichmentResult] = None
    domain = ""

    # Normalize
    t0 = time.perf_counter()
    try:
        nu = normalize_url(source_url)
        domain = nu.domain
        result.domain = domain
        stages.append(StageStatus(stage="normalize", ok=True, duration_ms=_ms(t0)))
        logger.info(
            "[pipeline] step=normalize run_id=%s domain=%s ok=true duration_ms=%s",
            rid,
            domain,
            _ms(t0),
        )
    except Exception as e:
        stages.append(
            StageStatus(stage="normalize", ok=False, message=str(e), duration_ms=_ms(t0))
        )
        logger.warning(
            "[pipeline] step=normalize run_id=%s ok=false duration_ms=%s error=%s",
            rid,
            _ms(t0),
            e,
        )
        result.stages = stages
        result.status = "failed"
        result.error = str(e)
        result.updated_at = datetime.now(timezone.utc)
        storage.save_run(result)
        logger.info(
            "[pipeline] step=domain_complete run_id=%s status=failed reason=normalize "
            "total_duration_ms=%s total_duration_s=%s",
            rid,
            _ms(t_pipeline_start),
            round(_ms(t_pipeline_start) / 1000, 3),
        )
        return result

    # Scrape + LinkedIn + web research in parallel (then merge into ScrapedContent)
    logger.info(
        "[pipeline] step=enrichment_parallel run_id=%s domain=%s start "
        "scrape+linkedin+web_research",
        rid,
        domain,
    )
    t_parallel = time.perf_counter()
    (scraped, scrape_stage), (linkedin_profile, linkedin_stage), (dossier, web_stage) = (
        await asyncio.gather(
            _do_scrape(source_url, settings.apify_api_token, rid, domain),
            _do_linkedin(source_url, settings.apify_api_token, rid, domain),
            _do_web_research(domain, source_url, settings.gemini_api_key, rid),
        )
    )
    if linkedin_profile:
        scraped.linkedin_data = linkedin_profile
    if dossier:
        scraped.web_research = dossier
    stages.extend([scrape_stage, linkedin_stage, web_stage])
    result.scraped = scraped
    result.stages = stages.copy()
    result.updated_at = datetime.now(timezone.utc)
    storage.save_run(result)
    logger.info(
        "[pipeline] step=persist_checkpoint run_id=%s after=enrichment_parallel "
        "duration_ms=%s",
        rid,
        _ms(t_parallel),
    )

    # AI
    t2 = time.perf_counter()
    try:
        if settings.gemini_api_key:
            logger.info(
                "[pipeline] step=ai run_id=%s domain=%s mode=gemini start",
                rid,
                domain,
            )
            raw = await asyncio.to_thread(enrich_with_gemini, scraped, source_url)
            logger.info(
                "[pipeline] step=ai_gemini_raw run_id=%s domain=%s response_chars=%s",
                rid,
                domain,
                len(raw),
            )
            logger.info("Gemini raw model output:\n%s", raw)
            enrichment = parse_enrichment_json(raw)
        else:
            logger.info(
                "[pipeline] step=ai run_id=%s domain=%s mode=stub (no GEMINI_API_KEY)",
                rid,
                domain,
            )
            enrichment = enrich_stub(scraped, source_url)
        if not enrichment.domain:
            enrichment.domain = domain
        if careers_penalty(scraped) and enrichment.intent_score > 0:
            enrichment.intent_score = max(0, enrichment.intent_score - 15)
            enrichment.confidence_rationale += (
                " Applied -15 intent_score: no careers page / thin careers signal."
            )
            logger.info(
                "[pipeline] step=ai_post run_id=%s domain=%s careers_penalty=intent_score_reduced_to_%s",
                rid,
                domain,
                enrichment.intent_score,
            )
        result.enrichment = enrichment
        stages.append(StageStatus(stage="ai", ok=True, duration_ms=_ms(t2)))
        logger.info(
            "[pipeline] step=ai run_id=%s domain=%s ok=true duration_ms=%s icp_tier=%s "
            "intent_score=%s pain_points=%s intent_signals=%s data_confidence=%s",
            rid,
            domain,
            _ms(t2),
            enrichment.icp_fit_tier,
            enrichment.intent_score,
            len(enrichment.pain_points),
            len(enrichment.intent_signals),
            enrichment.data_confidence,
        )
        result.stages = stages.copy()
        result.updated_at = datetime.now(timezone.utc)
        storage.save_run(result)
        logger.info("[pipeline] step=persist_checkpoint run_id=%s after=ai", rid)
    except Exception as e:
        logger.exception(
            "[pipeline] step=ai run_id=%s domain=%s ok=false duration_ms=%s",
            rid,
            domain,
            _ms(t2),
        )
        stages.append(StageStatus(stage="ai", ok=False, message=str(e), duration_ms=_ms(t2)))
        dead_letter.enqueue("ai", domain, str(e), {"scraped": scraped.model_dump() if scraped else {}})
        enrichment = EnrichmentResult(
            domain=domain,
            data_confidence="failed",
            confidence_rationale=str(e),
            requires_review=True,
        )
        result.enrichment = enrichment

    # Landing page JSON (second Gemini pass; failure does not fail pipeline)
    t_lp = time.perf_counter()
    last_ai = next((s for s in reversed(stages) if s.stage == "ai"), None)
    try:
        if (
            settings.gemini_api_key
            and enrichment
            and last_ai
            and last_ai.ok
        ):
            logger.info(
                "[pipeline] step=landing_page run_id=%s domain=%s start",
                rid,
                domain,
            )
            payload = json.dumps(enrichment.model_dump(mode="json"), ensure_ascii=False)
            raw_lp = await asyncio.to_thread(generate_landing_content, payload, domain)
            parsed = json.loads(raw_lp)
            if not isinstance(parsed, dict):
                raise ValueError("landing page JSON root must be an object")
            result.landing_page_content = parsed
            stages.append(StageStatus(stage="landing_page", ok=True, duration_ms=_ms(t_lp)))
            logger.info(
                "[pipeline] step=landing_page run_id=%s domain=%s ok=true duration_ms=%s keys=%s",
                rid,
                domain,
                _ms(t_lp),
                list(parsed.keys())[:12],
            )
        else:
            stages.append(
                StageStatus(
                    stage="landing_page",
                    ok=True,
                    duration_ms=_ms(t_lp),
                    message="skipped_no_gemini_or_ai_failed",
                )
            )
            logger.info(
                "[pipeline] step=landing_page run_id=%s domain=%s skipped reason=no_gemini_or_ai_not_ok",
                rid,
                domain,
            )
        result.stages = stages.copy()
        result.updated_at = datetime.now(timezone.utc)
        storage.save_run(result)
    except Exception as e:
        logger.exception(
            "[pipeline] step=landing_page run_id=%s domain=%s ok=false duration_ms=%s",
            rid,
            domain,
            _ms(t_lp),
        )
        stages.append(
            StageStatus(stage="landing_page", ok=False, message=str(e), duration_ms=_ms(t_lp))
        )
        dead_letter.enqueue(
            "landing_page",
            domain,
            str(e),
            {"enrichment": enrichment.model_dump(mode="json") if enrichment else {}},
        )
        result.stages = stages.copy()
        result.updated_at = datetime.now(timezone.utc)
        storage.save_run(result)

    landing = build_landing_url(domain)
    sanity_doc = build_sanity_manage_url(domain)
    result.landing_page_url = landing
    result.sanity_studio_url = sanity_doc
    logger.info(
        "[pipeline] step=urls run_id=%s domain=%s landing_page_url=%s",
        rid,
        domain,
        landing,
    )

    # Sanity
    t3 = time.perf_counter()
    enrichment_version = 1
    try:
        if settings.sanity_project_id and settings.sanity_api_token:
            logger.info(
                "[pipeline] step=sanity run_id=%s domain=%s action=upsert_account_with_history",
                rid,
                domain,
            )
            enrichment_version = await upsert_account_with_history(
                scraped,
                enrichment,
                source_url,
                None,
                landing,
                sanity_doc,
                rid,
                landing_page_content=result.landing_page_content,
            )
            result.sanity_document_id = f"account-{domain}"
            logger.info(
                "[pipeline] step=sanity run_id=%s domain=%s ok=true duration_ms=%s enrichment_version=%s doc_id=%s",
                rid,
                domain,
                _ms(t3),
                enrichment_version,
                result.sanity_document_id,
            )
        else:
            logger.info(
                "[pipeline] step=sanity run_id=%s domain=%s skipped reason=missing_project_or_token",
                rid,
                domain,
            )
        stages.append(StageStatus(stage="sanity", ok=True, duration_ms=_ms(t3)))
    except Exception as e:
        logger.exception(
            "[pipeline] step=sanity run_id=%s domain=%s ok=false duration_ms=%s",
            rid,
            domain,
            _ms(t3),
        )
        stages.append(StageStatus(stage="sanity", ok=False, message=str(e), duration_ms=_ms(t3)))
        dead_letter.enqueue(
            "sanity",
            domain,
            str(e),
            {"enrichment": enrichment.model_dump() if enrichment else {}},
        )

    result.stages = stages.copy()
    result.updated_at = datetime.now(timezone.utc)
    storage.save_run(result)
    logger.info("[pipeline] step=persist_checkpoint run_id=%s after=sanity", rid)

    # HubSpot
    t4 = time.perf_counter()
    try:
        if settings.hubspot_access_token:
            logger.info(
                "[pipeline] step=hubspot run_id=%s domain=%s action=upsert_company",
                rid,
                domain,
            )
            cid = await upsert_company_record(
                scraped,
                enrichment,
                landing,
                rid,
                enrichment_version,
            )
            result.hubspot_company_id = cid
            result.hubspot_portal_url = build_hubspot_record_url(cid)
            logger.info(
                "[pipeline] step=hubspot run_id=%s domain=%s ok=true duration_ms=%s company_id=%s",
                rid,
                domain,
                _ms(t4),
                cid,
            )
            try:
                await set_hubspot_company_id(domain, cid)
                logger.info(
                    "[pipeline] step=hubspot_sanity_patch run_id=%s domain=%s hubspot_company_id=%s",
                    rid,
                    domain,
                    cid,
                )
            except Exception:
                logger.exception(
                    "[pipeline] step=hubspot_sanity_patch run_id=%s domain=%s failed",
                    rid,
                    domain,
                )
        else:
            logger.info(
                "[pipeline] step=hubspot run_id=%s domain=%s skipped reason=no_hubspot_token",
                rid,
                domain,
            )
        stages.append(StageStatus(stage="hubspot", ok=True, duration_ms=_ms(t4)))
    except Exception as e:
        logger.exception(
            "[pipeline] step=hubspot run_id=%s domain=%s ok=false duration_ms=%s",
            rid,
            domain,
            _ms(t4),
        )
        stages.append(StageStatus(stage="hubspot", ok=False, message=str(e), duration_ms=_ms(t4)))
        dead_letter.enqueue(
            "hubspot",
            domain,
            str(e),
            {"enrichment": enrichment.model_dump() if enrichment else {}},
        )

    result.stages = stages
    result.status = "completed"
    result.updated_at = datetime.now(timezone.utc)
    storage.save_run(result)
    stage_summary = ",".join(f"{s.stage}:{'ok' if s.ok else 'fail'}" for s in stages)
    total_ms = _ms(t_pipeline_start)
    logger.info(
        "[pipeline] step=complete run_id=%s domain=%s status=%s stages=[%s] "
        "hubspot_company_id=%s sanity_doc=%s total_duration_ms=%s total_duration_s=%s",
        rid,
        domain,
        result.status,
        stage_summary,
        result.hubspot_company_id or "-",
        result.sanity_document_id or "-",
        total_ms,
        round(total_ms / 1000, 3),
    )
    return result


def careers_penalty(scraped: ScrapedContent) -> bool:
    return (not scraped.careers_page_available) or (not scraped.career_titles)
