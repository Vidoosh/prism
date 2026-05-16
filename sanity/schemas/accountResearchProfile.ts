import { defineField, defineType } from "sanity";

const painPoint = defineField({
  name: "pain_points",
  type: "array",
  of: [
    {
      type: "object",
      fields: [
        defineField({ name: "pain_id", type: "string" }),
        defineField({ name: "description", type: "text" }),
        defineField({
          name: "severity",
          type: "string",
          options: { list: ["critical", "high", "medium", "low"] },
        }),
        defineField({ name: "evidence", type: "text" }),
      ],
    },
  ],
});

const intentSignal = defineField({
  name: "intent_signals",
  type: "array",
  of: [
    {
      type: "object",
      fields: [
        defineField({
          name: "signal_tier",
          type: "string",
          options: { list: ["T1", "T2", "T3"] },
        }),
        defineField({ name: "signal_type", type: "string" }),
        defineField({ name: "description", type: "text" }),
        defineField({ name: "evidence", type: "text" }),
        defineField({ name: "recommended_action", type: "text" }),
      ],
    },
  ],
});

export default defineType({
  name: "accountResearchProfile",
  title: "Account Research Profile",
  type: "document",
  fields: [
    defineField({ name: "domain", type: "string", validation: (r) => r.required() }),
    defineField({ name: "company_name", type: "string" }),
    defineField({ name: "hubspot_company_id", type: "string" }),
    defineField({ name: "source_url", type: "url" }),
    defineField({
      name: "scrape_quality",
      type: "string",
      options: { list: ["high", "medium", "low", "blocked", "thin"] },
    }),
    defineField({ name: "first_enriched_at", type: "datetime" }),
    defineField({ name: "last_enriched_at", type: "datetime" }),
    defineField({ name: "scrape_date", type: "datetime" }),
    defineField({
      name: "organization_type",
      type: "string",
      options: {
        list: [
          { title: "Health Plan", value: "health_plan" },
          { title: "Digital Health", value: "digital_health" },
          { title: "MSO", value: "mso_physician_group" },
          { title: "Health System", value: "health_system" },
          { title: "Dental Network", value: "dental_network" },
          { title: "Non ICP", value: "non_icp" },
          { title: "Unknown", value: "unknown" },
        ],
      },
    }),
    defineField({ name: "organization_subtype", type: "string" }),
    defineField({
      name: "icp_fit_tier",
      type: "string",
      options: { list: ["A", "B", "C", "D"] },
    }),
    defineField({ name: "icp_fit_score", type: "number" }),
    defineField({ name: "icp_scoring_rationale", type: "text" }),
    defineField({
      name: "geographic_footprint",
      type: "string",
      options: { list: ["single_state", "multi_state", "national", "unknown"] },
    }),
    defineField({ name: "states_mentioned", type: "array", of: [{ type: "string" }] }),
    defineField({ name: "estimated_provider_count_range", type: "string" }),
    defineField({ name: "provider_types_mentioned", type: "array", of: [{ type: "string" }] }),
    defineField({ name: "funding_stage", type: "string" }),
    defineField({
      name: "data_confidence",
      type: "string",
      options: { list: ["high", "medium", "low", "failed"] },
    }),
    defineField({
      name: "primary_product_fit",
      type: "array",
      of: [{ type: "reference", to: [{ type: "productPageContent" }] }],
    }),
    defineField({ name: "product_fit_rationale", type: "text" }),
    painPoint,
    intentSignal,
    defineField({ name: "intent_score", type: "number" }),
    defineField({ name: "inferred_intent_themes", type: "array", of: [{ type: "string" }] }),
    defineField({
      name: "content_blocks",
      type: "object",
      fields: [
        defineField({ name: "personalized_value_proposition", type: "string" }),
        defineField({ name: "hero_headline", type: "string" }),
        defineField({ name: "pain_point_paragraph", type: "text" }),
        defineField({
          name: "cta_block",
          type: "object",
          fields: [
            defineField({ name: "primary_cta_text", type: "string" }),
            defineField({ name: "primary_cta_subtext", type: "string" }),
            defineField({ name: "supporting_proof_point", type: "string" }),
          ],
        }),
        defineField({ name: "hook_technique_used", type: "string" }),
      ],
    }),
    defineField({ name: "competitor_mentions", type: "array", of: [{ type: "string" }] }),
    defineField({ name: "regulatory_mentions", type: "array", of: [{ type: "string" }] }),
    defineField({ name: "accreditation_mentions", type: "array", of: [{ type: "string" }] }),
    defineField({
      name: "career_page_signals",
      type: "object",
      fields: [
        defineField({ name: "credentialing_roles_count", type: "number" }),
        defineField({ name: "compliance_roles_count", type: "number" }),
        defineField({ name: "network_ops_roles_count", type: "number" }),
        defineField({ name: "competitor_tool_mentioned", type: "boolean" }),
        defineField({ name: "role_titles_extracted", type: "array", of: [{ type: "string" }] }),
      ],
    }),
    defineField({ name: "expansion_signals", type: "array", of: [{ type: "string" }] }),
    defineField({ name: "claude_reasoning", type: "text" }),
    defineField({ name: "requires_manual_review", type: "boolean" }),
    defineField({ name: "pipeline_run_id", type: "string" }),
    defineField({ name: "enrichment_version", type: "number" }),
    defineField({ name: "landing_page_url", type: "url" }),
    defineField({
      name: "landing_page_content",
      title: "Landing Page Content (JSON)",
      type: "text",
      description: "Serialized JSON from the second Gemini landing page pass",
    }),
    defineField({ name: "sanity_document_url", type: "url" }),
  ],
  preview: { select: { title: "company_name", subtitle: "domain" } },
});
