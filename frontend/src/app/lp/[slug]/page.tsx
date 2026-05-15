import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { FinalCtaSection } from "@/components/landing/cta-section";
import { HeroSection } from "@/components/landing/hero-section";
import { LegacyLanding } from "@/components/landing/legacy-landing";
import { ObjectionSection } from "@/components/landing/objection-section";
import { PainSection } from "@/components/landing/pain-section";
import { PersonalizationMetaRibbon } from "@/components/landing/personalization-meta";
import { ProductSection } from "@/components/landing/product-section";
import { RoiSection } from "@/components/landing/roi-section";
import { SeoBlock } from "@/components/landing/seo-block";
import { SocialProofSection } from "@/components/landing/social-proof-section";
import { SolutionBridgeSection } from "@/components/landing/solution-bridge-section";
import { TrustBar } from "@/components/landing/trust-bar";
import { UrgencySection } from "@/components/landing/urgency-section";
import { getLandingContentByDomain } from "@/lib/api";
import { landingTokenOk } from "@/lib/landing-token";
import { getLandingPageByDomain } from "@/lib/sanity";

function slugToDomain(slug: string) {
  return slug.includes(".") ? slug : slug.replace(/-/g, ".");
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const domain = slugToDomain(slug);
  try {
    const landing = await getLandingContentByDomain(domain);
    const m = landing?.meta;
    if (m?.page_title || m?.meta_description || m?.og_title) {
      return {
        title: m.page_title || m.og_title || "CertifyOS",
        description: m.meta_description || m.og_description,
        openGraph: {
          title: m.og_title || m.page_title,
          description: m.og_description || m.meta_description,
        },
      };
    }
  } catch {
    /* ignore — metadata is best-effort */
  }
  return {
    title: "CertifyOS · Personalized briefing",
    description: "Personalized provider data infrastructure for your organization.",
  };
}

export default async function LandingPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ preview?: string; t?: string }>;
}) {
  const { slug } = await params;
  const sp = await searchParams;
  const domain = slugToDomain(slug);

  const secret = process.env.LANDING_PAGE_SECRET;
  if (!landingTokenOk(slug, sp.t, secret)) {
    notFound();
  }

  const [landing, sanityData] = await Promise.all([
    getLandingContentByDomain(domain).catch(() => null),
    getLandingPageByDomain(domain),
  ]);

  if (!landing && !sanityData) {
    notFound();
  }

  const preview = sp.preview === "true";
  const companyName = sanityData?.company_name || domain.split(".")[0] || domain;

  return (
    <main className="min-h-screen bg-[#fafbff] text-slate-900">
      {preview ? (
        <div className="bg-amber-400 py-2 text-center text-sm font-medium text-amber-950">
          Draft — Internal Preview Only
        </div>
      ) : null}

      <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="text-lg font-bold tracking-tight text-slate-900">CertifyOS</span>
          <Link href="/" className="text-sm font-medium text-blue-700 hover:text-blue-900 hover:underline">
            Home
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-6xl space-y-20 px-6 py-14 md:py-20">
        {landing ? (
          <>
            <HeroSection hero={landing.hero} meta={landing.meta} companyName={companyName} />
            <PainSection section={landing.pain_section} />
            <SolutionBridgeSection bridge={landing.solution_bridge} />
            <SocialProofSection proof={landing.proof_section} />
            <ProductSection section={landing.product_section} />
            <RoiSection section={landing.roi_section} />
            <UrgencySection section={landing.intent_urgency_section} />
            <ObjectionSection section={landing.objection_section} />
            <TrustBar bar={landing.trust_bar} />
            <FinalCtaSection section={landing.final_cta_section} />
            <PersonalizationMetaRibbon meta={landing.personalization_metadata} />
            <SeoBlock block={landing.seo_content_block} />
          </>
        ) : (
          <LegacyLanding data={sanityData!} />
        )}
      </div>
    </main>
  );
}
