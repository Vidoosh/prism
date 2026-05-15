import { defineConfig } from "sanity";
import { visionTool } from "@sanity/vision";
import { structureTool } from "sanity/structure";

import { schemaTypes } from "./schemas";

const projectId = process.env.SANITY_STUDIO_PROJECT_ID || process.env.SANITY_PROJECT_ID || "ium78jg9";
const dataset = process.env.SANITY_STUDIO_DATASET || process.env.SANITY_DATASET || "production";

export default defineConfig({
  name: "prism",
  title: "Prism / CertifyOS",
  projectId: projectId || "placeholder",
  dataset,
  plugins: [structureTool(), visionTool()],
  schema: { types: schemaTypes },
});
