import { defineField, defineType } from "sanity";

export default defineType({
  name: "productPageContent",
  title: "Product Page Content",
  type: "document",
  fields: [
    defineField({ name: "product_name", type: "string" }),
    defineField({ name: "product_slug", type: "slug", options: { source: "product_name" } }),
    defineField({ name: "hero_copy", type: "text" }),
    defineField({ name: "proof_points", type: "array", of: [{ type: "string" }] }),
    defineField({ name: "relevant_icp_types", type: "array", of: [{ type: "string" }] }),
  ],
});
