import type { LandingRoiSection } from "@/lib/types";
import { certifyOsHref } from "@/lib/certify-links";

export function RoiSection({ section }: { section?: LandingRoiSection }) {
  const calcs = section?.roi_calculations?.filter((c) => c.calculation_label || c.calculation_body) ?? [];
  if (!section || (!section.section_heading && !section.roi_intro && calcs.length === 0)) return null;

  return (
    <section className="scroll-mt-24 space-y-10 rounded-3xl border border-slate-900 bg-slate-950 px-6 py-12 text-white md:px-10 md:py-14">
      <div className="space-y-4">
        {section.section_label ? (
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-amber-300">{section.section_label}</p>
        ) : null}
        {section.section_heading ? (
          <h2 className="max-w-3xl text-balance text-3xl font-bold tracking-tight md:text-4xl">{section.section_heading}</h2>
        ) : null}
        {section.roi_intro ? (
          <p className="max-w-3xl text-lg leading-relaxed text-slate-300">{section.roi_intro}</p>
        ) : null}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {calcs.map((c, i) => (
          <div key={`${c.calculation_label}-${i}`} className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
            {c.calculation_label ? (
              <h3 className="text-lg font-semibold text-white">{c.calculation_label}</h3>
            ) : null}
            {c.calculation_body ? (
              <p className="mt-3 text-sm leading-relaxed text-slate-300">{c.calculation_body}</p>
            ) : null}
            {c.calculation_punchline ? (
              <p className="mt-4 border-t border-white/10 pt-4 text-sm font-semibold text-amber-200">
                {c.calculation_punchline}
              </p>
            ) : null}
          </div>
        ))}
      </div>

      {section.roi_cta?.text ? (
        <div className="rounded-2xl border border-blue-400/30 bg-blue-500/10 p-6">
          <a
            href={certifyOsHref()}
            className="text-lg font-semibold text-blue-100 underline-offset-4 hover:text-white hover:underline"
          >
            {section.roi_cta.text}
          </a>
          {section.roi_cta.subtext ? (
            <p className="mt-2 text-sm text-slate-400">{section.roi_cta.subtext}</p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
