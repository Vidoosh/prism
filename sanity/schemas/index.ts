import { type SchemaTypeDefinition } from "sanity";

import accountResearchProfile from "./accountResearchProfile";
import enrichmentVersion from "./enrichmentVersion";
import productPageContent from "./productPageContent";

export const schemaTypes: SchemaTypeDefinition[] = [
  accountResearchProfile,
  enrichmentVersion,
  productPageContent,
];
