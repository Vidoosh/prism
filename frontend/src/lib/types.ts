/** Mirrors backend enrichment / pipeline DTOs (`EnrichmentResult` in schemas.py). */


export type IcpTier = "A" | "B" | "C" | "D";

export interface CtaBlock {
  primary_cta_text?: string;
  primary_cta_subtext?: string;
  supporting_proof_point?: string;
}

export interface PainPoint {
  pain_id?: string;
  description?: string;
  severity?: string;
  evidence?: string;
}

export interface IntentSignal {
  signal_tier?: string;
  signal_type?: string;
  description?: string;
  evidence?: string;
  recommended_action?: string;
}

export interface EnrichmentResult {
  company_name?: string;
  domain?: string;
  organization_type?: string;
  organization_subtype?: string | null;
  geographic_footprint?: string;
  states_mentioned?: string[];
  estimated_provider_count_range?: string;
  provider_types_mentioned?: string[];
  funding_stage?: string;
  icp_fit_score?: number;
  icp_fit_tier?: string;
  primary_product_fit?: string[];
  pain_points?: PainPoint[];
  intent_signals?: IntentSignal[];
  intent_score?: number;
  competitor_mentions?: string[];
  regulatory_mentions?: string[];
  accreditation_mentions?: string[];
  hook_technique_recommended?: string;
  personalized_value_proposition?: string;
  hero_headline?: string;
  pain_point_paragraph?: string;
  cta_block?: CtaBlock;
  inferred_intent_themes?: string[];
  data_confidence?: string;
  confidence_rationale?: string;
  icp_scoring_rationale?: string;
  non_icp_reason?: string | null;
  requires_review?: boolean;
  pain_severity?: string;
}

export interface PipelineRunResult {
  run_id: string;
  status: string;
  source_url?: string;
  domain?: string;
  enrichment?: EnrichmentResult;
  sanity_document_id?: string;
  sanity_studio_url?: string;
  landing_page_url?: string;
  landing_page_content?: LandingPageContent | Record<string, unknown>;
  hubspot_company_id?: string;
  hubspot_portal_url?: string;
  error?: string;
  updated_at?: string;
}

export interface LandingProduct {
  product_name?: string;
  hero_copy?: string;
  proof_points?: string[];
}

export interface LandingPageData {
  company_name?: string;
  domain?: string;
  organization_type?: string;
  pain_points?: PainPoint[];
  intent_signals?: IntentSignal[];
  content_blocks?: {
    personalized_value_proposition?: string;
    hero_headline?: string;
    pain_point_paragraph?: string;
    cta_block?: CtaBlock;
    hook_technique_used?: string;
  };
  primary_product_fit?: unknown[];
  product_details?: LandingProduct[];
}

/** Rich landing page JSON from second Gemini pass (`LANDING_PAGE_SYSTEM_PROMPT`). */

export interface LandingMetaBlock {
  page_title?: string;
  meta_description?: string;
  og_title?: string;
  og_description?: string;
  personalization_signal?: string;
}

export interface LandingHeroStat {
  number?: string;
  label?: string;
  source_hint?: string;
}

export interface LandingHeroCtaPrimary {
  button_text?: string;
  button_subtext?: string;
}

export interface LandingHeroCtaSecondary {
  link_text?: string;
  link_url_slug?: string;
}

export interface LandingHero {
  eyebrow_tag?: string;
  headline?: string;
  subheadline?: string;
  hero_stat?: LandingHeroStat;
  cta_primary?: LandingHeroCtaPrimary;
  cta_secondary?: LandingHeroCtaSecondary;
}

export interface LandingPainCard {
  card_number?: number;
  pain_label?: string;
  pain_body?: string;
  pain_evidence_hook?: string;
}

export interface LandingPainSection {
  section_label?: string;
  section_heading?: string;
  section_subheading?: string;
  pain_cards?: LandingPainCard[];
}

export interface LandingApproachPillar {
  pillar_icon_hint?: string;
  pillar_label?: string;
  pillar_body?: string;
}

export interface LandingSolutionBridge {
  section_label?: string;
  section_heading?: string;
  section_subheading?: string;
  approach_pillars?: LandingApproachPillar[];
}

export interface LandingAnchorStat {
  number?: string;
  label?: string;
  relevance_note?: string;
}

export interface LandingProofSection {
  section_label?: string;
  section_heading?: string;
  anchor_stat_1?: LandingAnchorStat;
  anchor_stat_2?: LandingAnchorStat;
  anchor_stat_3?: LandingAnchorStat;
  icp_matched_social_proof_label?: string;
}

export interface LandingProductCard {
  product_name?: string;
  product_tagline?: string;
  product_body?: string;
  product_proof_point?: string;
  product_cta_micro?: string;
}

export interface LandingProductSection {
  section_label?: string;
  section_heading?: string;
  section_subheading?: string;
  product_cards?: LandingProductCard[];
}

export interface LandingRoiCalculation {
  calculation_label?: string;
  calculation_body?: string;
  calculation_punchline?: string;
}

export interface LandingRoiCta {
  text?: string;
  subtext?: string;
}

export interface LandingRoiSection {
  section_label?: string;
  section_heading?: string;
  roi_intro?: string;
  roi_calculations?: LandingRoiCalculation[];
  roi_cta?: LandingRoiCta;
}

export interface LandingIntentUrgencySection {
  section_label?: string;
  section_heading?: string;
  urgency_body?: string;
  urgency_signal_used?: string;
  urgency_stat?: string;
}

export interface LandingObjection {
  objection_text?: string;
  response_heading?: string;
  response_body?: string;
}

export interface LandingObjectionSection {
  section_label?: string;
  section_heading?: string;
  objections?: LandingObjection[];
}

export interface LandingTrustItem {
  trust_label?: string;
  trust_detail?: string;
}

export interface LandingTrustBar {
  section_label?: string;
  trust_items?: LandingTrustItem[];
}

export interface LandingFinalCtaPrimary {
  button_text?: string;
  button_subtext?: string;
}

export interface LandingFinalCtaSecondary {
  link_text?: string;
  link_url_slug?: string;
}

export interface LandingFinalCtaSection {
  section_label?: string;
  headline?: string;
  subheadline?: string;
  cta_primary?: LandingFinalCtaPrimary;
  cta_secondary?: LandingFinalCtaSecondary;
  personalization_close?: string;
}

export interface LandingSeoContentBlock {
  h2_subpage_heading?: string;
  seo_paragraph?: string;
}

export interface LandingPersonalizationMetadata {
  hook_technique_deployed?: string;
  primary_pain_featured?: string;
  key_personalization_signals_used?: string[];
  icp_archetype?: string;
  products_featured?: string[];
  tone_deployed?: string;
  content_confidence?: string;
}

export interface LandingPageContent {
  meta?: LandingMetaBlock;
  hero?: LandingHero;
  pain_section?: LandingPainSection;
  solution_bridge?: LandingSolutionBridge;
  proof_section?: LandingProofSection;
  product_section?: LandingProductSection;
  roi_section?: LandingRoiSection;
  intent_urgency_section?: LandingIntentUrgencySection;
  objection_section?: LandingObjectionSection;
  trust_bar?: LandingTrustBar;
  final_cta_section?: LandingFinalCtaSection;
  seo_content_block?: LandingSeoContentBlock;
  personalization_metadata?: LandingPersonalizationMetadata;
}
