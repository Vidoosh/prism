"""Sanity Content Lake mutations via HTTP API."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from config import get_settings
from models.schemas import EnrichmentResult, ScrapedContent

logger = logging.getLogger(__name__)

SANITY_API_VERSION = "2023-10-01"


def _base_url(project_id: str) -> str:
    return f"https://{project_id}.api.sanity.io/v{SANITY_API_VERSION}"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def product_ref_ids(names: list[str]) -> list[dict[str, Any]]:
    mapping = {
        "credentialing": "product-credentialing",
        "licensing": "product-licensing",
        "compliance monitoring": "product-compliance-monitoring",
        "compliance_monitoring": "product-compliance-monitoring",
        "roster management": "product-roster-management",
        "rosteros": "product-roster-management",
        "provider hub": "product-provider-hub",
    }
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for n in names:
        key = (n or "").strip().lower().replace("-", " ")
        pid = None
        for k, v in mapping.items():
            if k in key:
                pid = v
                break
        if not pid:
            continue
        if pid in seen:
            continue
        seen.add(pid)
        refs.append({"_type": "reference", "_ref": pid, "_key": pid.replace("-", "_")})
    return refs


def build_account_document(
    scraped: ScrapedContent,
    enrichment: EnrichmentResult,
    source_url: str,
    hubspot_company_id: Optional[str],
    landing_page_url: str,
    sanity_studio_url: str,
    pipeline_run_id: str,
    enrichment_version: int,
    prior: Optional[dict[str, Any]],
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    if prior and prior.get("first_enriched_at"):
        first_at = prior["first_enriched_at"]
    else:
        first_at = now

    career_signals = {
        "credentialing_roles_count": sum(
            1
            for t in scraped.career_titles
            if any(
                k in t.lower()
                for k in ("credential", "enrollment", "cvo", "provider data")
            )
        ),
        "compliance_roles_count": sum(
            1 for t in scraped.career_titles if "compliance" in t.lower()
        ),
        "network_ops_roles_count": sum(
            1
            for t in scraped.career_titles
            if any(k in t.lower() for k in ("network", "provider relation", "operations"))
        ),
        "competitor_tool_mentioned": any(
            k in (scraped.career_descriptions_summary or "").lower()
            for k in ("medallion", "modio", "verity", "symplr", "md-staff")
        ),
        "role_titles_extracted": scraped.career_titles,
    }

    content_blocks = {
        "personalized_value_proposition": enrichment.personalized_value_proposition[:120],
        "hero_headline": enrichment.hero_headline[:90],
        "pain_point_paragraph": enrichment.pain_point_paragraph,
        "cta_block": {
            "primary_cta_text": enrichment.cta_block.primary_cta_text,
            "primary_cta_subtext": enrichment.cta_block.primary_cta_subtext,
            "supporting_proof_point": enrichment.cta_block.supporting_proof_point,
        },
        "hook_technique_used": enrichment.hook_technique_recommended,
    }

    doc: dict[str, Any] = {
        "_id": f"account-{scraped.domain}",
        "_type": "accountResearchProfile",
        "domain": scraped.domain,
        "company_name": enrichment.company_name or scraped.domain,
        "hubspot_company_id": hubspot_company_id,
        "source_url": source_url,
        "scrape_quality": scraped.scrape_quality,
        "first_enriched_at": first_at,
        "last_enriched_at": now,
        "scrape_date": now,
        "organization_type": enrichment.organization_type,
        "organization_subtype": enrichment.organization_subtype,
        "icp_fit_tier": enrichment.icp_fit_tier,
        "icp_fit_score": enrichment.icp_fit_score,
        "icp_scoring_rationale": enrichment.icp_scoring_rationale,
        "geographic_footprint": enrichment.geographic_footprint,
        "states_mentioned": enrichment.states_mentioned,
        "estimated_provider_count_range": enrichment.estimated_provider_count_range,
        "provider_types_mentioned": enrichment.provider_types_mentioned,
        "funding_stage": enrichment.funding_stage,
        "data_confidence": enrichment.data_confidence,
        "primary_product_fit": product_ref_ids(enrichment.primary_product_fit),
        "product_fit_rationale": "",
        "pain_points": [p.model_dump() for p in enrichment.pain_points],
        "intent_signals": [s.model_dump() for s in enrichment.intent_signals],
        "intent_score": enrichment.intent_score,
        "inferred_intent_themes": enrichment.inferred_intent_themes,
        "content_blocks": content_blocks,
        "competitor_mentions": enrichment.competitor_mentions,
        "regulatory_mentions": enrichment.regulatory_mentions,
        "accreditation_mentions": enrichment.accreditation_mentions,
        "career_page_signals": career_signals,
        "expansion_signals": [],
        "claude_reasoning": enrichment.icp_scoring_rationale + "\n" + enrichment.confidence_rationale,
        "requires_manual_review": enrichment.requires_review or scraped.scrape_blocked,
        "pipeline_run_id": pipeline_run_id,
        "enrichment_version": enrichment_version,
        "landing_page_url": landing_page_url,
        "sanity_document_url": sanity_studio_url,
    }
    return doc


async def fetch_document(project_id: str, dataset: str, token: str, doc_id: str) -> Optional[dict[str, Any]]:
    query = f'*[_id == "{doc_id}"][0]'
    url = f"{_base_url(project_id)}/data/query/{dataset}"
    params = {"query": query}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, headers=_headers(token), params=params)
        if r.status_code != 200:
            return None
        res = r.json()
        return res.get("result")


async def _mutate(project_id: str, dataset: str, token: str, mutations: list[dict[str, Any]]) -> None:
    body = {"mutations": mutations, "returnDocuments": False}
    url = f"{_base_url(project_id)}/data/mutate/{dataset}"
    delays = [0, 2, 4, 8]
    last_err: Optional[Exception] = None
    for delay in delays:
        if delay:
            await asyncio.sleep(delay)
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(url, headers=_headers(token), content=json.dumps(body))
                if r.status_code >= 500:
                    raise RuntimeError(r.text)
                if r.status_code >= 400:
                    raise RuntimeError(f"Sanity mutate error {r.status_code}: {r.text}")
                return
        except Exception as e:
            last_err = e
            logger.warning("Sanity mutate retry: %s", e)
    raise RuntimeError(f"Sanity mutate failed: {last_err}")


async def upsert_account_with_history(
    scraped: ScrapedContent,
    enrichment: EnrichmentResult,
    source_url: str,
    hubspot_company_id: Optional[str],
    landing_page_url: str,
    sanity_studio_url: str,
    pipeline_run_id: str,
) -> int:
    settings = get_settings()
    if not settings.sanity_project_id or not settings.sanity_api_token:
        raise ValueError("Sanity is not configured")

    doc_id = f"account-{scraped.domain}"
    prior = await fetch_document(
        settings.sanity_project_id, settings.sanity_dataset, settings.sanity_api_token, doc_id
    )
    version = 1
    if prior and isinstance(prior.get("enrichment_version"), int):
        version = prior["enrichment_version"] + 1

    mutations: list[dict[str, Any]] = []

    # Referenced product ids (e.g. product-provider-hub) must exist or Sanity returns 409.
    # Idempotent: createOrReplace all catalog products before account + snapshot.
    for product_doc in PRODUCT_SEED_DOCS:
        mutations.append({"createOrReplace": product_doc})

    if prior:
        snap_id = f"version.{scraped.domain}.{uuid.uuid4().hex}"
        snapshot = {
            "_id": snap_id,
            "_type": "enrichmentVersion",
            "account_reference": {"_type": "reference", "_ref": doc_id},
            "snapshot_date": datetime.now(timezone.utc).isoformat(),
            "icp_fit_score": prior.get("icp_fit_score"),
            "intent_score": prior.get("intent_score"),
            "intent_signals": prior.get("intent_signals"),
            "pain_points": prior.get("pain_points"),
            "content_blocks": prior.get("content_blocks"),
        }
        mutations.append({"create": snapshot})

    doc = build_account_document(
        scraped,
        enrichment,
        source_url,
        hubspot_company_id,
        landing_page_url,
        sanity_studio_url,
        pipeline_run_id,
        version,
        prior,
    )
    mutations.append({"createOrReplace": doc})

    await _mutate(settings.sanity_project_id, settings.sanity_dataset, settings.sanity_api_token, mutations)
    return version


async def set_hubspot_company_id(domain: str, hubspot_company_id: str) -> None:
    settings = get_settings()
    if not settings.sanity_project_id or not settings.sanity_api_token:
        return
    doc_id = f"account-{domain}"
    mutations = [{"patch": {"id": doc_id, "set": {"hubspot_company_id": hubspot_company_id}}}]
    await _mutate(settings.sanity_project_id, settings.sanity_dataset, settings.sanity_api_token, mutations)


PRODUCT_SEED_DOCS: list[dict[str, Any]] = [
    {
        "_id": "product-credentialing",
        "_type": "productPageContent",
        "product_name": "Credentialing",
        "product_slug": {"_type": "slug", "current": "credentialing"},
        "hero_copy": "Automated primary source verification and NCQA-ready credentialing lifecycle management.",
        "proof_points": [
            "NCQA-certified verification services",
            "CAQH auto-rostering and NPDB automation",
            "Faster turnaround vs manual credentialing teams",
        ],
        "relevant_icp_types": ["health_plan", "health_system", "mso_physician_group"],
    },
    {
        "_id": "product-licensing",
        "_type": "productPageContent",
        "product_name": "Licensing",
        "product_slug": {"_type": "slug", "current": "licensing"},
        "hero_copy": "End-to-end provider licensing across all 50 states with compact expertise (NLC/IMLC).",
        "proof_points": [
            "Requirements by state and provider type",
            "Fingerprinting and vendor coordination",
            "One profile powers future applications",
        ],
        "relevant_icp_types": ["digital_health", "mso_physician_group"],
    },
    {
        "_id": "product-compliance-monitoring",
        "_type": "productPageContent",
        "product_name": "Compliance Monitoring",
        "product_slug": {"_type": "slug", "current": "compliance-monitoring"},
        "hero_copy": "Continuous sanctions, license, DEA, and board monitoring with proactive alerts.",
        "proof_points": [
            "Federal + state source coverage",
            "Real-time alerting vs annual snapshots",
            "Audit-ready reporting",
        ],
        "relevant_icp_types": ["health_plan", "health_system", "digital_health"],
    },
    {
        "_id": "product-roster-management",
        "_type": "productPageContent",
        "product_name": "Roster Management",
        "product_slug": {"_type": "slug", "current": "roster-management"},
        "hero_copy": "Ingest, validate, and consolidate delegated rosters into one clean network view.",
        "proof_points": [
            "Flexible schema mapping",
            "Delegated entity self-serve validation",
            "Directory-ready exports",
        ],
        "relevant_icp_types": ["health_plan"],
    },
    {
        "_id": "product-provider-hub",
        "_type": "productPageContent",
        "product_name": "Provider Hub",
        "product_slug": {"_type": "slug", "current": "provider-hub"},
        "hero_copy": "Unified provider data infrastructure with API delivery to every downstream system.",
        "proof_points": [
            "Golden record across fragmented systems",
            "AI-ready data quality foundation",
            "Enterprise-scale provider modeling",
        ],
        "relevant_icp_types": ["health_plan", "health_system"],
    },
]


async def seed_products() -> None:
    settings = get_settings()
    if not settings.sanity_project_id or not settings.sanity_api_token:
        raise ValueError("Sanity is not configured")
    mutations = [{"createOrReplace": doc} for doc in PRODUCT_SEED_DOCS]
    await _mutate(settings.sanity_project_id, settings.sanity_dataset, settings.sanity_api_token, mutations)
