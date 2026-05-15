import type { LandingSolutionBridge } from "@/lib/types";
import { PillarIcon } from "@/components/landing/pillar-icon";

export function SolutionBridgeSection({ bridge }: { bridge?: LandingSolutionBridge }) {
  const pillars = bridge?.approach_pillars?.filter((p) => p.pillar_label || p.pillar_body) ?? [];
  if (
    !bridge ||
    (!bridge.section_heading && !bridge.section_subheading && pillars.length === 0)
  ) {
    return null;
  }

  return (
    <section className="scroll-mt-24 space-y-10 rounded-3xl border border-slate-200 bg-white px-6 py-12 shadow-sm md:px-10 md:py-14">
      <div className="space-y-4">
        {bridge.section_label ? (
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-blue-700">{bridge.section_label}</p>
        ) : null}
        {bridge.section_heading ? (
          <h2 className="max-w-3xl text-balance text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
            {bridge.section_heading}
          </h2>
        ) : null}
        {bridge.section_subheading ? (
          <p className="max-w-3xl text-lg leading-relaxed text-slate-600">{bridge.section_subheading}</p>
        ) : null}
      </div>

      <div className="grid gap-8 md:grid-cols-3">
        {pillars.map((p, i) => (
          <div key={`${p.pillar_label}-${i}`} className="flex gap-4 rounded-2xl bg-slate-50/80 p-5 ring-1 ring-slate-100">
            <PillarIcon hint={p.pillar_icon_hint} />
            <div className="space-y-2">
              {p.pillar_label ? <h3 className="text-lg font-semibold text-slate-900">{p.pillar_label}</h3> : null}
              {p.pillar_body ? <p className="text-sm leading-relaxed text-slate-600">{p.pillar_body}</p> : null}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
