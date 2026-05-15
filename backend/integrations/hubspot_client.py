"""HubSpot CRM v3 client: properties + company upsert."""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any, Optional

import httpx

from config import get_settings
from models.schemas import EnrichmentResult, ScrapedContent

logger = logging.getLogger(__name__)

HS_BASE = "https://api.hubapi.com"


def _hs_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def _request(
    method: str,
    path: str,
    token: str,
    *,
    json_body: Any | None = None,
) -> httpx.Response:
    url = f"{HS_BASE}{path}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await client.request(method, url, headers=_hs_headers(token), json=json_body)


async def _ensure_property_group(token: str) -> None:
    body = {
        "name": "certifyos_enrichment",
        "label": "CertifyOS Enrichment",
        "displayOrder": 20,
    }
    r = await _request("POST", "/crm/v3/properties/companies/groups", token, json_body=body)
    if r.status_code in (200, 201, 409):
        return
    logger.warning("Property group create returned %s: %s", r.status_code, r.text)


def _opts(labels: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for l in labels:
        val = (
            l.lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("<", "lt")
            .replace("+", "plus")
            .replace(",", "")
            .replace("-", "_")
        )
        out.append({"label": l, "value": val})
    return out


async def create_hubspot_properties(token: str) -> None:
    await _ensure_property_group(token)

    definitions: list[dict[str, Any]] = [
        {
            "name": "certify_icp_fit_score",
            "label": "Certify ICP Fit Score",
            "type": "number",
            "fieldType": "number",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_icp_fit_tier",
            "label": "Certify ICP Fit Tier",
            "type": "enumeration",
            "fieldType": "select",
            "groupName": "certifyos_enrichment",
            "options": _opts(["A", "B", "C", "D", "Not Evaluated"]),
        },
        {
            "name": "certify_intent_score",
            "label": "Certify Intent Score",
            "type": "number",
            "fieldType": "number",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_pain_severity",
            "label": "Certify Pain Severity",
            "type": "enumeration",
            "fieldType": "select",
            "groupName": "certifyos_enrichment",
            "options": _opts(["Critical", "High", "Medium", "Low", "Unknown"]),
        },
        {
            "name": "certify_data_confidence",
            "label": "Certify Data Confidence",
            "type": "enumeration",
            "fieldType": "select",
            "groupName": "certifyos_enrichment",
            "options": _opts(["High", "Medium", "Low", "Failed"]),
        },
        {
            "name": "certify_organization_type",
            "label": "Certify Organization Type",
            "type": "enumeration",
            "fieldType": "select",
            "groupName": "certifyos_enrichment",
            "options": _opts(
                [
                    "Health Plan",
                    "Digital Health",
                    "MSO-Physician Group",
                    "Health System",
                    "Dental Network",
                    "Non-ICP",
                    "Unknown",
                ]
            ),
        },
        {
            "name": "certify_organization_subtype",
            "label": "Certify Organization Subtype",
            "type": "string",
            "fieldType": "text",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_geographic_footprint",
            "label": "Certify Geographic Footprint",
            "type": "enumeration",
            "fieldType": "select",
            "groupName": "certifyos_enrichment",
            "options": _opts(["Single State", "Multi-State", "National", "Unknown"]),
        },
        {
            "name": "certify_estimated_provider_count",
            "label": "Certify Estimated Provider Count",
            "type": "enumeration",
            "fieldType": "select",
            "groupName": "certifyos_enrichment",
            # Explicit values — HubSpot needs stable internal IDs (not e.g. 5000plus).
            "options": [
                {"label": "<50", "value": "lt_50"},
                {"label": "50-200", "value": "50_200"},
                {"label": "200-1000", "value": "200_1000"},
                {"label": "1000-5000", "value": "1000_5000"},
                {"label": "5000+", "value": "5000_plus"},
                {"label": "Unknown", "value": "unknown"},
            ],
        },
        {
            "name": "certify_funding_stage",
            "label": "Certify Funding Stage",
            "type": "enumeration",
            "fieldType": "select",
            "groupName": "certifyos_enrichment",
            "options": _opts(
                ["Pre-Seed", "Seed", "Series A", "Series B", "Series C", "Series D+", "Public", "Unknown"]
            ),
        },
        {
            "name": "certify_primary_product_fit",
            "label": "Certify Primary Product Fit",
            "type": "string",
            "fieldType": "textarea",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_product_fit_rationale",
            "label": "Certify Product Fit Rationale",
            "type": "string",
            "fieldType": "textarea",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_t1_signals_detected",
            "label": "Certify T1 Signals",
            "type": "string",
            "fieldType": "textarea",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_t2_signals_detected",
            "label": "Certify T2 Signals",
            "type": "string",
            "fieldType": "textarea",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_t3_signals_detected",
            "label": "Certify T3 Signals",
            "type": "string",
            "fieldType": "textarea",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_inferred_intent_themes",
            "label": "Certify Inferred Intent Themes",
            "type": "string",
            "fieldType": "textarea",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_competitor_mentions",
            "label": "Certify Competitor Mentions",
            "type": "string",
            "fieldType": "textarea",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_sanity_content_url",
            "label": "Certify Sanity / LP URL",
            "type": "string",
            "fieldType": "text",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_personalized_value_prop",
            "label": "Certify Personalized Value Prop",
            "type": "string",
            "fieldType": "textarea",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_hero_headline",
            "label": "Certify Hero Headline",
            "type": "string",
            "fieldType": "textarea",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_hook_technique",
            "label": "Certify Hook Technique",
            "type": "string",
            "fieldType": "text",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_last_enriched_date",
            "label": "Certify Last Enriched Date",
            "type": "date",
            "fieldType": "date",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_enrichment_version",
            "label": "Certify Enrichment Version",
            "type": "number",
            "fieldType": "number",
            "groupName": "certifyos_enrichment",
        },
        {
            "name": "certify_scrape_quality",
            "label": "Certify Scrape Quality",
            "type": "enumeration",
            "fieldType": "select",
            "groupName": "certifyos_enrichment",
            "options": _opts(["High", "Medium", "Low", "Blocked", "Thin"]),
        },
        {
            "name": "certify_pipeline_run_id",
            "label": "Certify Pipeline Run ID",
            "type": "string",
            "fieldType": "text",
            "groupName": "certifyos_enrichment",
        },
    ]

    for p in definitions:
        r = await _request("POST", "/crm/v3/properties/companies", token, json_body=p)
        if r.status_code in (200, 201):
            continue
        if r.status_code == 409:
            continue
        logger.warning("Property %s: %s %s", p.get("name"), r.status_code, r.text)


def _map_org_type(val: str) -> str:
    m = {
        "health_plan": "Health Plan",
        "digital_health": "Digital Health",
        "mso_physician_group": "MSO-Physician Group",
        "health_system": "Health System",
        "dental_network": "Dental Network",
        "non_icp": "Non-ICP",
        "unknown": "Unknown",
    }
    return m.get((val or "unknown").lower(), "Unknown")


def _map_geo(val: str) -> str:
    m = {
        "single_state": "Single State",
        "multi_state": "Multi-State",
        "national": "National",
        "unknown": "Unknown",
    }
    return m.get((val or "unknown").lower(), "Unknown")


def _map_funding(val: str) -> str:
    m = {
        "pre_seed": "Pre-Seed",
        "seed": "Seed",
        "series_a": "Series A",
        "series_b": "Series B",
        "series_c": "Series C",
        "series_d_plus": "Series D+",
        "public": "Public",
        "unknown": "Unknown",
    }
    return m.get((val or "unknown").lower(), "Unknown")


def _map_provider_count(val: str) -> str:
    v = val or "unknown"
    if v in ("<50", "50-200", "200-1000", "1000-5000", "5000+"):
        return v
    return "Unknown"


def _map_scrape_quality(val: str) -> str:
    m = {"high": "High", "medium": "Medium", "low": "Low", "blocked": "Blocked", "thin": "Thin"}
    return m.get((val or "").lower(), "Medium")


def _map_data_conf(val: str) -> str:
    m = {"high": "High", "medium": "Medium", "low": "Low", "failed": "Failed"}
    return m.get((val or "low").lower(), "Low")


def _map_pain_sev(val: str) -> str:
    m = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low", "unknown": "Unknown"}
    return m.get((val or "unknown").lower(), "Unknown")


def _tier_key(label: str) -> str:
    return (
        label.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("<", "lt")
        .replace("+", "plus")
        .replace(",", "")
        .replace("-", "_")
    )


def hubspot_provider_count_enum(val: str) -> str:
    """Map model output to HubSpot option values (must match portal enum)."""
    v = (val or "unknown").strip().replace("–", "-")
    mapping = {
        "<50": "lt_50",
        "50-200": "50_200",
        "200-1000": "200_1000",
        "1000-5000": "1000_5000",
        "5000+": "5000_plus",
        "unknown": "unknown",
    }
    if v in mapping:
        return mapping[v]
    low = v.lower()
    if "5000" in low and ("+" in v or "plus" in low):
        return "5000_plus"
    if low in ("lt50", "under 50"):
        return "lt_50"
    return "unknown"


def hubspot_product_multiselect(products: list[str]) -> str:
    """Multi-select enum: internal values joined with ; (per HubSpot CRM API)."""
    phrases: list[tuple[str, str]] = [
        ("provider hub", "provider_hub"),
        ("roster management", "roster_management"),
        ("rosteros", "roster_management"),
        ("compliance monitoring", "compliance_monitoring"),
        ("credentialing", "credentialing"),
        ("licensing", "licensing"),
    ]
    out: list[str] = []
    seen: set[str] = set()
    for raw in products:
        text = (raw or "").strip().lower()
        if not text:
            continue
        for needle, hs_val in phrases:
            if needle in text or text.replace(" ", "_") == needle.replace(" ", "_"):
                if hs_val not in seen:
                    seen.add(hs_val)
                    out.append(hs_val)
                break
    return ";".join(out)


def hubspot_intent_themes_multiselect(themes: list[str]) -> str:
    """Map free-text themes to HubSpot checkbox enum internal values."""
    rules: list[tuple[tuple[str, ...], str]] = [
        (("multi-state", "multi state", "state expansion", "geographic expansion"), "multi_state_expansion"),
        (
            ("acquisition", "m&a", "post-acquisition", "post acquisition", "integration"),
            "post_acquisition_integration",
        ),
        (("ncqa", "urac"), "ncqa_certification"),
        (("onboarding", "velocity", "credentialing", "enrollment"), "provider_onboarding_velocity"),
        (("no surprises", "transparency", "directory"), "no_surprises_act"),
        (("cost", "efficiency"), "cost_reduction"),
        (("legacy", "migration", "replacement"), "legacy_system_replacement"),
        (("ai", "machine learning", "data infrastructure", "data quality"), "ai_readiness"),
    ]
    blob = "\n".join(themes).lower()
    picked: list[str] = []
    seen: set[str] = set()
    for needles, hs in rules:
        if hs in seen:
            continue
        if any(n in blob for n in needles):
            seen.add(hs)
            picked.append(hs)
    return ";".join(picked)


async def search_company_by_domain(token: str, domain: str) -> Optional[str]:
    body = {
        "filterGroups": [
            {"filters": [{"propertyName": "domain", "operator": "EQ", "value": domain}]}
        ],
        "properties": ["domain", "name"],
        "limit": 1,
    }
    r = await _request("POST", "/crm/v3/objects/companies/search", token, json_body=body)
    if r.status_code != 200:
        return None
    data = r.json()
    results = data.get("results") or []
    if not results:
        return None
    return str(results[0]["id"])


def build_hubspot_props(
    scraped: ScrapedContent,
    enrichment: EnrichmentResult,
    landing_url: str,
    pipeline_run_id: str,
    enrichment_version: int,
) -> dict[str, Any]:
    def join_unique(items: list[str]) -> str:
        seen: set[str] = set()
        out: list[str] = []
        for i in items:
            i = (i or "").strip()
            if not i or i in seen:
                continue
            seen.add(i)
            out.append(i)
        return "\n".join(out)

    tier = (enrichment.icp_fit_tier or "D").strip()
    tier_val = tier.lower() if tier.upper() in ("A", "B", "C", "D") else "not_evaluated"

    props: dict[str, Any] = {
        "certify_icp_fit_score": enrichment.icp_fit_score,
        "certify_icp_fit_tier": tier_val,
        "certify_intent_score": enrichment.intent_score,
        "certify_pain_severity": _tier_key(_map_pain_sev(enrichment.pain_severity)),
        "certify_data_confidence": _tier_key(_map_data_conf(enrichment.data_confidence)),
        "certify_organization_type": _tier_key(_map_org_type(enrichment.organization_type)),
        "certify_organization_subtype": enrichment.organization_subtype or "",
        "certify_geographic_footprint": _tier_key(_map_geo(enrichment.geographic_footprint)),
        "certify_estimated_provider_count": hubspot_provider_count_enum(
            enrichment.estimated_provider_count_range
        ),
        "certify_funding_stage": _tier_key(_map_funding(enrichment.funding_stage)),
        "certify_primary_product_fit": hubspot_product_multiselect(enrichment.primary_product_fit),
        "certify_product_fit_rationale": enrichment.icp_scoring_rationale[:65000],
        "certify_t1_signals_detected": join_unique(
            [s.signal_type for s in enrichment.intent_signals if s.signal_tier == "T1"]
        ),
        "certify_t2_signals_detected": join_unique(
            [s.signal_type for s in enrichment.intent_signals if s.signal_tier == "T2"]
        ),
        "certify_t3_signals_detected": join_unique(
            [s.signal_type for s in enrichment.intent_signals if s.signal_tier == "T3"]
        ),
        "certify_inferred_intent_themes": hubspot_intent_themes_multiselect(
            enrichment.inferred_intent_themes
        ),
        "certify_competitor_mentions": join_unique(enrichment.competitor_mentions),
        "certify_sanity_content_url": landing_url,
        "certify_personalized_value_prop": enrichment.personalized_value_proposition,
        "certify_hero_headline": enrichment.hero_headline,
        "certify_hook_technique": enrichment.hook_technique_recommended,
        "certify_last_enriched_date": date.today().isoformat(),
        "certify_enrichment_version": enrichment_version,
        "certify_scrape_quality": _tier_key(_map_scrape_quality(scraped.scrape_quality)),
        "certify_pipeline_run_id": pipeline_run_id,
        "domain": scraped.domain,
        "name": enrichment.company_name or scraped.domain,
    }
    return props


def _invalid_option_property_names(error_body: str) -> list[str]:
    """Parse HubSpot 400 body for INVALID_OPTION so we can retry without mis-typed fields."""
    try:
        data = json.loads(error_body)
    except json.JSONDecodeError:
        return []
    names: list[str] = []
    for err in data.get("errors") or []:
        if err.get("code") != "INVALID_OPTION":
            continue
        ctx = err.get("context") or {}
        raw = ctx.get("propertyName")
        if isinstance(raw, list):
            names.extend(str(x) for x in raw)
        elif raw:
            names.append(str(raw))
    return names


def _append_rationale_sections(base: str, sections: list[tuple[str, str]]) -> str:
    parts = [base.strip()]
    for title, body in sections:
        body = (body or "").strip()
        if body:
            parts.append(f"\n\n--- {title} ---\n{body}")
    out = "".join(parts).strip()
    return out[:65000]


def _props_retry_without_invalid_options(
    props: dict[str, Any], bad_property_names: list[str]
) -> dict[str, Any] | None:
    """
    Some portals define certify_t*_signals_detected (or similar) as checkbox enums while
    this integration sends free-form text. Strip offending keys and preserve values in rationale.
    """
    bad_set = {n for n in bad_property_names if n}
    overlap = bad_set & set(props.keys())
    if not overlap:
        return None
    rationale = props.get("certify_product_fit_rationale") or ""
    labels = {
        "certify_t1_signals_detected": "Certify T1 signals",
        "certify_t2_signals_detected": "Certify T2 signals",
        "certify_t3_signals_detected": "Certify T3 signals",
        "certify_inferred_intent_themes": "Inferred intent themes",
        "certify_competitor_mentions": "Competitor mentions",
    }
    sections: list[tuple[str, str]] = []
    for key in sorted(overlap):
        val = props.get(key)
        if val is None or val == "":
            continue
        sections.append((labels.get(key, key), str(val)))
    new_props = {k: v for k, v in props.items() if k not in overlap}
    new_props["certify_product_fit_rationale"] = _append_rationale_sections(rationale, sections)
    return new_props


async def upsert_company(
    token: str,
    props: dict[str, Any],
) -> str:
    attempt_props: dict[str, Any] = dict(props)

    for try_idx in range(2):
        domain = attempt_props.get("domain", "")
        cid = await search_company_by_domain(token, domain)
        if cid:
            r = await _request(
                "PATCH",
                f"/crm/v3/objects/companies/{cid}",
                token,
                json_body={"properties": attempt_props},
            )
            if r.status_code in (200, 204):
                return cid
            if try_idx == 0 and r.status_code == 400:
                bad = _invalid_option_property_names(r.text)
                merged = _props_retry_without_invalid_options(attempt_props, bad)
                if merged is not None:
                    logger.warning(
                        "HubSpot PATCH: INVALID_OPTION on %s; retrying without those fields (merged into certify_product_fit_rationale)",
                        bad,
                    )
                    attempt_props = merged
                    continue
            raise RuntimeError(f"HubSpot update failed {r.status_code}: {r.text}")

        r = await _request(
            "POST",
            "/crm/v3/objects/companies",
            token,
            json_body={"properties": attempt_props},
        )
        if r.status_code in (200, 201):
            return str(r.json()["id"])
        if try_idx == 0 and r.status_code == 400:
            bad = _invalid_option_property_names(r.text)
            merged = _props_retry_without_invalid_options(attempt_props, bad)
            if merged is not None:
                logger.warning(
                    "HubSpot POST: INVALID_OPTION on %s; retrying without those fields (merged into certify_product_fit_rationale)",
                    bad,
                )
                attempt_props = merged
                continue
        raise RuntimeError(f"HubSpot create failed {r.status_code}: {r.text}")

    raise RuntimeError("HubSpot upsert failed after INVALID_OPTION retry")


async def upsert_company_record(
    scraped: ScrapedContent,
    enrichment: EnrichmentResult,
    landing_url: str,
    pipeline_run_id: str,
    enrichment_version: int,
) -> str:
    settings = get_settings()
    if not settings.hubspot_access_token:
        raise ValueError("HUBSPOT_ACCESS_TOKEN is not set")
    props = build_hubspot_props(scraped, enrichment, landing_url, pipeline_run_id, enrichment_version)
    return await upsert_company(settings.hubspot_access_token, props)
