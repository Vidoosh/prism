import type { LandingFinalCtaSection } from "@/lib/types";
import { certifyOsHref } from "@/lib/certify-links";

export function FinalCtaSection({ section }: { section?: LandingFinalCtaSection }) {
  if (!section?.headline && !section?.cta_primary?.button_text) return null;

  const primary = section.cta_primary;
  const secondary = section.cta_secondary;

  return (
    <section className="scroll-mt-24 rounded-3xl bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 px-6 py-14 text-center text-white shadow-2xl md:px-12 md:py-16">
      <div className="mx-auto max-w-3xl space-y-6">
        {section.section_label ? (
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-blue-200">{section.section_label}</p>
        ) : null}
        {section.headline ? (
          <h2 className="text-balance text-3xl font-bold tracking-tight md:text-4xl">{section.headline}</h2>
        ) : null}
        {section.subheadline ? (
          <p className="text-lg leading-relaxed text-slate-300">{section.subheadline}</p>
        ) : null}

        <div className="flex flex-col items-center justify-center gap-4 pt-4 sm:flex-row sm:flex-wrap">
          {primary?.button_text ? (
            <a
              href={certifyOsHref()}
              className="inline-flex min-w-[200px] items-center justify-center rounded-xl bg-blue-500 px-8 py-4 text-base font-semibold text-white shadow-lg shadow-blue-900/40 transition hover:bg-blue-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              {primary.button_text}
            </a>
          ) : null}
          {secondary?.link_text ? (
            <a
              href={certifyOsHref(secondary.link_url_slug)}
              className="inline-flex text-base font-semibold text-blue-100 underline-offset-4 hover:text-white hover:underline"
            >
              {secondary.link_text}
            </a>
          ) : null}
        </div>
        {primary?.button_subtext ? (
          <p className="text-sm text-slate-400">{primary.button_subtext}</p>
        ) : null}
        {section.personalization_close ? (
          <p className="border-t border-white/10 pt-8 text-sm italic leading-relaxed text-blue-100">
            {section.personalization_close}
          </p>
        ) : null}
      </div>
    </section>
  );
}
