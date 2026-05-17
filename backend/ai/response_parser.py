"""Parse and validate model JSON output."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from models.schemas import CtaBlock, EnrichmentResult, IntentSignal, PainPoint

logger = logging.getLogger(__name__)


def _first_str(d: dict[str, Any], *keys: str) -> str:
    for k in keys:
        if k in d and d[k] is not None:
            return str(d[k])
    return ""


def _coerce_item_list(val: Any) -> list[Any]:
    """Model may return a list, a single dict, a JSON string, or wrong key casing."""
    if val is None:
        return []
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
        except json.JSONDecodeError:
            return []
        return _coerce_item_list(parsed)
    if isinstance(val, list):
        return val
    if isinstance(val, dict):
        return [val]
    return []


def _extract_list(data: dict[str, Any], *keys: str) -> list[Any]:
    for k in keys:
        if k in data:
            return _coerce_item_list(data[k])
    return []


def strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a single JSON object from model output; tolerate markdown fences."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty response")
    m = _JSON_FENCE.search(raw)
    if m:
        raw = m.group(1).strip()
    try:
        out = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end <= start:
            raise
        out = json.loads(raw[start : end + 1])
    if not isinstance(out, dict):
        raise TypeError("expected JSON object")
    return out


def _derive_pain_severity(pains: list[PainPoint]) -> str:
    order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    best = 0
    label = "low"
    for p in pains:
        lvl = order.get((p.severity or "low").lower(), 0)
        if lvl > best:
            best = lvl
            label = p.severity or "low"
    if not pains:
        return "unknown"
    return label


def _pain_from_entry(entry: Any) -> PainPoint | None:
    if isinstance(entry, dict):
        return PainPoint(
            pain_id=_first_str(entry, "pain_id", "painId", "id"),
            description=_first_str(entry, "description", "summary", "text"),
            severity=_first_str(entry, "severity", "severity_level") or "low",
            evidence=_first_str(entry, "evidence", "supporting_evidence", "proof"),
        )
    if isinstance(entry, str):
        s = entry.strip()
        if not s:
            return None
        pain_id = ""
        description = s
        m = re.match(r"^(P\d+\.\d+)\s*[:-–—]\s*(.+)$", s, re.I | re.DOTALL)
        if m:
            pain_id, description = m.group(1).upper(), m.group(2).strip()
        else:
            m2 = re.match(r"^(P\d+\.\d+)\s+(.+)$", s, re.I | re.DOTALL)
            if m2:
                pain_id, description = m2.group(1).upper(), m2.group(2).strip()
            else:
                m3 = re.match(r"^(P\d+\.\d+)\s*$", s, re.I)
                if m3:
                    pain_id = m3.group(1).upper()
                    description = s
        return PainPoint(
            pain_id=pain_id,
            description=description,
            severity="medium",
            evidence="",
        )
    return None


def _intent_from_entry(entry: Any) -> IntentSignal | None:
    if isinstance(entry, dict):
        return IntentSignal(
            signal_tier=_first_str(entry, "signal_tier", "signalTier", "tier") or "T3",
            signal_type=_first_str(entry, "signal_type", "signalType", "type"),
            description=_first_str(entry, "description", "summary"),
            evidence=_first_str(entry, "evidence", "supporting_evidence"),
            recommended_action=_first_str(entry, "recommended_action", "recommendedAction", "action"),
        )
    if isinstance(entry, str):
        s = entry.strip()
        if not s:
            return None
        tier_match = re.match(r"^(T[123])\b\s*[:-–—]?\s*", s, re.I)
        tier = "T3"
        rest = s
        if tier_match:
            tier = tier_match.group(1).upper()
            rest = s[tier_match.end() :].strip()
        signal_type = "intent_signal"
        description = rest
        sep = re.match(r"^([^–—:]+?)[:]?\s*[–—]\s*(.+)$", rest, re.DOTALL)
        if sep:
            signal_type = sep.group(1).strip()[:200]
            description = sep.group(2).strip()
        return IntentSignal(
            signal_tier=tier,
            signal_type=signal_type,
            description=description,
            evidence="",
            recommended_action="",
        )
    return None


def parse_enrichment_json(raw: str) -> EnrichmentResult:
    cleaned = strip_fences(raw)
    try:
        data: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error("Malformed JSON from model: %s", raw[:500])
        return EnrichmentResult(
            data_confidence="failed",
            confidence_rationale="Model returned invalid JSON",
            icp_scoring_rationale="",
            requires_review=True,
        )

    def get_list(*keys: str) -> list[Any]:
        return _extract_list(data, *keys)

    pains_raw = get_list("pain_points", "painPoints")
    pains: list[PainPoint] = []
    for p in pains_raw:
        parsed = _pain_from_entry(p)
        if parsed:
            pains.append(parsed)

    intents_raw = get_list("intent_signals", "intentSignals")
    intents: list[IntentSignal] = []
    for s in intents_raw:
        parsed_i = _intent_from_entry(s)
        if parsed_i:
            intents.append(parsed_i)

    cta_raw = data.get("cta_block") or data.get("ctaBlock") or {}
    if not isinstance(cta_raw, dict):
        cta_raw = {}
    cta = CtaBlock(
        primary_cta_text=_first_str(cta_raw, "primary_cta_text", "primaryCtaText"),
        primary_cta_subtext=_first_str(cta_raw, "primary_cta_subtext", "primaryCtaSubtext"),
        supporting_proof_point=_first_str(
            cta_raw, "supporting_proof_point", "supportingProofPoint"
        ),
    )

    result = EnrichmentResult(
        company_name=str(data.get("company_name", "") or ""),
        domain=str(data.get("domain", "") or ""),
        organization_type=str(data.get("organization_type", "unknown") or "unknown"),
        organization_subtype=data.get("organization_subtype"),
        geographic_footprint=str(data.get("geographic_footprint", "unknown") or "unknown"),
        states_mentioned=[str(x) for x in get_list("states_mentioned", "statesMentioned")],
        estimated_provider_count_range=str(
            data.get("estimated_provider_count_range", "unknown") or "unknown"
        ),
        provider_types_mentioned=[
            str(x) for x in get_list("provider_types_mentioned", "providerTypesMentioned")
        ],
        funding_stage=str(data.get("funding_stage", "unknown") or "unknown"),
        icp_fit_score=int(data.get("icp_fit_score") or 0),
        icp_fit_tier=str(data.get("icp_fit_tier", "D") or "D"),
        primary_product_fit=[str(x) for x in get_list("primary_product_fit", "primaryProductFit")],
        pain_points=pains,
        intent_signals=intents,
        intent_score=int(data.get("intent_score") or 0),
        competitor_mentions=[str(x) for x in get_list("competitor_mentions", "competitorMentions")],
        regulatory_mentions=[str(x) for x in get_list("regulatory_mentions", "regulatoryMentions")],
        accreditation_mentions=[
            str(x) for x in get_list("accreditation_mentions", "accreditationMentions")
        ],
        hook_technique_recommended=str(data.get("hook_technique_recommended", "") or ""),
        personalized_value_proposition=str(data.get("personalized_value_proposition", "") or ""),
        hero_headline=str(data.get("hero_headline", "") or ""),
        pain_point_paragraph=str(data.get("pain_point_paragraph", "") or ""),
        cta_block=cta,
        inferred_intent_themes=[
            str(x) for x in get_list("inferred_intent_themes", "inferredIntentThemes")
        ],
        data_confidence=str(data.get("data_confidence", "low") or "low"),
        confidence_rationale=str(data.get("confidence_rationale", "") or ""),
        icp_scoring_rationale=str(data.get("icp_scoring_rationale", "") or ""),
        non_icp_reason=data.get("non_icp_reason"),
        requires_review=False,
        pain_severity=_derive_pain_severity(pains),
    )

    missing_critical = not result.company_name and not result.domain
    if missing_critical or result.data_confidence == "failed":
        result.requires_review = True
    return result
