import { defineField, defineType } from "sanity";

export default defineType({
  name: "enrichmentVersion",
  title: "Enrichment Version",
  type: "document",
  fields: [
    defineField({
      name: "account_reference",
      type: "reference",
      to: [{ type: "accountResearchProfile" }],
    }),
    defineField({ name: "snapshot_date", type: "datetime" }),
    defineField({ name: "icp_fit_score", type: "number" }),
    defineField({ name: "intent_score", type: "number" }),
    defineField({
      name: "intent_signals",
      type: "array",
      of: [
        {
          type: "object",
          fields: [
            defineField({ name: "signal_tier", type: "string" }),
            defineField({ name: "signal_type", type: "string" }),
            defineField({ name: "description", type: "text" }),
            defineField({ name: "evidence", type: "text" }),
            defineField({ name: "recommended_action", type: "text" }),
          ],
        },
      ],
    }),
    defineField({
      name: "pain_points",
      type: "array",
      of: [
        {
          type: "object",
          fields: [
            defineField({ name: "pain_id", type: "string" }),
            defineField({ name: "description", type: "text" }),
            defineField({ name: "severity", type: "string" }),
            defineField({ name: "evidence", type: "text" }),
          ],
        },
      ],
    }),
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
    defineField({
      name: "landing_page_content",
      title: "Landing Page Content (JSON)",
      type: "text",
    }),
  ],
});
