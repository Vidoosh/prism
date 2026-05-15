import type { LandingObjectionSection } from "@/lib/types";

export function ObjectionSection({ section }: { section?: LandingObjectionSection }) {
  const items = section?.objections?.filter((o) => o.objection_text || o.response_body) ?? [];
  if (!section || (!section.section_heading && items.length === 0)) return null;

  return (
    <section className="scroll-mt-24 space-y-8">
      <div className="space-y-4">
        {section.section_label ? (
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-blue-700">{section.section_label}</p>
        ) : null}
        {section.section_heading ? (
          <h2 className="max-w-3xl text-balance text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
            {section.section_heading}
          </h2>
        ) : null}
      </div>

      <div className="divide-y divide-slate-200 rounded-2xl border border-slate-200 bg-white">
        {items.map((o, i) => (
          <details key={i} className="group p-6 marker:content-none open:bg-slate-50/80">
            <summary className="cursor-pointer list-none font-semibold text-slate-900 [&::-webkit-details-marker]:hidden">
              <span className="flex items-start justify-between gap-4">
                <span>{o.objection_text}</span>
                <span className="mt-1 shrink-0 text-blue-600 transition group-open:rotate-180">⌄</span>
              </span>
            </summary>
            <div className="mt-4 space-y-3 border-l-2 border-blue-200 pl-4">
              {o.response_heading ? (
                <p className="text-sm font-bold uppercase tracking-wide text-blue-900">{o.response_heading}</p>
              ) : null}
              {o.response_body ? <p className="text-sm leading-relaxed text-slate-700">{o.response_body}</p> : null}
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
