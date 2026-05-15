import type { LandingIntentUrgencySection } from "@/lib/types";

export function UrgencySection({ section }: { section?: LandingIntentUrgencySection }) {
  if (!section?.section_heading && !section?.urgency_body && !section?.urgency_stat) return null;

  return (
    <section className="scroll-mt-24 overflow-hidden rounded-3xl border border-orange-200 bg-gradient-to-br from-orange-50 via-white to-amber-50 px-6 py-10 md:px-10 md:py-12">
      <div className="grid gap-8 lg:grid-cols-[2fr_1fr] lg:items-start">
        <div className="space-y-4">
          {section.section_label ? (
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-orange-800">{section.section_label}</p>
          ) : null}
          {section.section_heading ? (
            <h2 className="max-w-3xl text-balance text-3xl font-bold tracking-tight text-slate-900">{section.section_heading}</h2>
          ) : null}
          {section.urgency_body ? (
            <p className="max-w-3xl text-lg leading-relaxed text-slate-700">{section.urgency_body}</p>
          ) : null}
          {section.urgency_signal_used ? (
            <p className="text-sm font-medium text-orange-900">
              <span className="font-semibold text-slate-900">Signal: </span>
              {section.urgency_signal_used}
            </p>
          ) : null}
        </div>
        {section.urgency_stat ? (
          <aside className="rounded-2xl border border-orange-100 bg-white/80 p-6 shadow-inner shadow-orange-100">
            <p className="text-xs font-bold uppercase tracking-wide text-orange-800">Why timing matters</p>
            <p className="mt-3 text-sm leading-relaxed text-slate-800">{section.urgency_stat}</p>
          </aside>
        ) : null}
      </div>
    </section>
  );
}
