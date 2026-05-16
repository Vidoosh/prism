"""Pydantic schemas for scrape output, enrichment, pipeline results."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class CtaBlock(BaseModel):
    primary_cta_text: str = ""
    primary_cta_subtext: str = ""
    supporting_proof_point: str = ""


class PainPoint(BaseModel):
    pain_id: str = ""
    description: str = ""
    severity: str = "low"
    evidence: str = ""


class IntentSignal(BaseModel):
    signal_tier: str = "T3"
    signal_type: str = ""
    description: str = ""
    evidence: str = ""
    recommended_action: str = ""


class ScrapedPage(BaseModel):
    """One URL worth of extracted content for enrichment prompts."""

    url: str
    page_kind: str = "other"
    extraction_ok: bool = False
    blocked_http: bool = False
    fetch_exception: Optional[str] = None
    rendered_with_playwright: bool = False
    thin_content: bool = False
    word_count: int = 0
    title: str = ""
    meta_description: str = ""
    headings_h1: list[str] = Field(default_factory=list)
    headings_h2: list[str] = Field(default_factory=list)
    paragraphs: list[str] = Field(default_factory=list)
    list_items: list[str] = Field(default_factory=list)
    job_postings: list[dict[str, str]] = Field(default_factory=list)
    full_text: str = ""


class EnrichmentResult(BaseModel):
    """Structured output from Gemini (Section 9)."""

    company_name: str = ""
    domain: str = ""
    organization_type: str = "unknown"
    organization_subtype: Optional[str] = None
    geographic_footprint: str = "unknown"
    states_mentioned: list[str] = Field(default_factory=list)
    estimated_provider_count_range: str = "unknown"
    provider_types_mentioned: list[str] = Field(default_factory=list)
    funding_stage: str = "unknown"
    icp_fit_score: int = 0
    icp_fit_tier: str = "D"
    primary_product_fit: list[str] = Field(default_factory=list)
    pain_points: list[PainPoint] = Field(default_factory=list)
    intent_signals: list[IntentSignal] = Field(default_factory=list)
    intent_score: int = 0
    competitor_mentions: list[str] = Field(default_factory=list)
    regulatory_mentions: list[str] = Field(default_factory=list)
    accreditation_mentions: list[str] = Field(default_factory=list)
    hook_technique_recommended: str = ""
    personalized_value_proposition: str = ""
    hero_headline: str = ""
    pain_point_paragraph: str = ""
    cta_block: CtaBlock = Field(default_factory=CtaBlock)
    inferred_intent_themes: list[str] = Field(default_factory=list)
    data_confidence: str = "low"
    confidence_rationale: str = ""
    icp_scoring_rationale: str = ""
    non_icp_reason: Optional[str] = None

    requires_review: bool = False
    pain_severity: str = "unknown"


class ScrapedContent(BaseModel):
    """Pre-processed scrape bundle (Section 8 Step 1.5)."""

    domain: str
    homepage_text: str = ""
    about_text: str = ""
    about_available: bool = False
    careers_page_available: bool = False
    career_titles: list[str] = Field(default_factory=list)
    career_descriptions_summary: str = ""
    blog_excerpts: list[str] = Field(default_factory=list)
    press_excerpts: list[str] = Field(default_factory=list)
    total_pages_scraped: int = 0
    pages_blocked: int = 0
    thin_content_pages: int = 0
    scrape_quality: str = "medium"
    token_count_estimate: int = 0
    js_rendered_only: bool = False
    scrape_blocked: bool = False
    tier_used: str = "http"
    raw_page_summaries: list[str] = Field(default_factory=list)
    scraped_pages: list[ScrapedPage] = Field(default_factory=list)
    linkedin_data: Optional[dict[str, Any]] = None
    web_research: Optional[dict[str, Any]] = None


class StageStatus(BaseModel):
    stage: str
    ok: bool
    message: Optional[str] = None
    duration_ms: Optional[int] = None


class PipelineRunResult(BaseModel):
    run_id: str
    status: str
    source_url: str = ""
    domain: str = ""
    scraped: Optional[ScrapedContent] = None
    enrichment: Optional[EnrichmentResult] = None
    sanity_document_id: Optional[str] = None
    sanity_studio_url: Optional[str] = None
    landing_page_url: Optional[str] = None
    landing_page_content: Optional[dict[str, Any]] = None
    hubspot_company_id: Optional[str] = None
    hubspot_portal_url: Optional[str] = None
    stages: list[StageStatus] = Field(default_factory=list)
    error: Optional[str] = None
    updated_at: Optional[datetime] = None


class BatchJobStatus(BaseModel):
    batch_id: str
    status: str
    total: int = 0
    completed: int = 0
    failed: int = 0
    in_progress: int = 0
    results: dict[str, PipelineRunResult] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class DeadLetterEntry(BaseModel):
    id: str
    domain: str
    stage: str
    error: str
    timestamp: str
    partial: dict[str, Any] = Field(default_factory=dict)


class SanityAccountProfile(BaseModel):
    """accountResearchProfile document shape for Sanity writes."""

    document_id: str = Field(alias="_id")
    document_type: str = Field(default="accountResearchProfile", alias="_type")
    domain: str
    company_name: str = ""
    hubspot_company_id: Optional[str] = None
    source_url: str = ""
    scrape_quality: str = "medium"
    first_enriched_at: Optional[str] = None
    last_enriched_at: Optional[str] = None
    scrape_date: Optional[str] = None
    organization_type: str = "unknown"
    organization_subtype: Optional[str] = None
    icp_fit_tier: str = "D"
    icp_fit_score: int = 0
    icp_scoring_rationale: str = ""
    geographic_footprint: str = "unknown"
    states_mentioned: list[str] = Field(default_factory=list)
    estimated_provider_count_range: str = "unknown"
    provider_types_mentioned: list[str] = Field(default_factory=list)
    funding_stage: str = "unknown"
    data_confidence: str = "low"
    primary_product_fit: list[str] = Field(default_factory=list)
    product_fit_rationale: Optional[dict[str, Any]] = None
    pain_points: list[dict[str, Any]] = Field(default_factory=list)
    intent_signals: list[dict[str, Any]] = Field(default_factory=list)
    intent_score: int = 0
    inferred_intent_themes: list[str] = Field(default_factory=list)
    content_blocks: dict[str, Any] = Field(default_factory=dict)
    competitor_mentions: list[str] = Field(default_factory=list)
    regulatory_mentions: list[str] = Field(default_factory=list)
    accreditation_mentions: list[str] = Field(default_factory=list)
    career_page_signals: dict[str, Any] = Field(default_factory=dict)
    expansion_signals: list[str] = Field(default_factory=list)
    claude_reasoning: str = ""
    requires_manual_review: bool = False
    pipeline_run_id: str = ""
    enrichment_version: int = 1
    landing_page_url: str = ""
    landing_page_content: Optional[str] = None
    sanity_document_url: str = ""

    model_config = ConfigDict(populate_by_name=True)
