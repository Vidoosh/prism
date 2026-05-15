import { createClient } from "@sanity/client";

import type { LandingPageData } from "./types";

const projectId = process.env.NEXT_PUBLIC_SANITY_PROJECT_ID || "";
const dataset = process.env.NEXT_PUBLIC_SANITY_DATASET || "production";
const token = process.env.SANITY_API_READ_TOKEN || process.env.SANITY_API_TOKEN || "";

export const sanityClient =
  projectId &&
  createClient({
    projectId,
    dataset,
    apiVersion: "2023-10-01",
    useCdn: true,
    token: token || undefined,
  });

const landingQuery = `*[_type == "accountResearchProfile" && domain == $domain][0]{
  company_name,
  domain,
  organization_type,
  pain_points,
  intent_signals,
  content_blocks,
  primary_product_fit,
  "product_details": primary_product_fit[]->{
    product_name,
    hero_copy,
    proof_points
  }
}`;

export async function getLandingPageByDomain(domain: string): Promise<LandingPageData | null> {
  if (!sanityClient) return null;
  return sanityClient.fetch(landingQuery, { domain });
}
