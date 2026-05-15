import type { LandingTrustBar } from "@/lib/types";

export function TrustBar({ bar }: { bar?: LandingTrustBar }) {
  const items = bar?.trust_items?.filter((t) => t.trust_label || t.trust_detail) ?? [];
  if (!bar || (items.length === 0 && !bar.section_label)) return null;

  return (
    <section className="scroll-mt-24 rounded-3xl border border-slate-200 bg-slate-50 px-6 py-10 md:px-10">
      {bar.section_label ? (
        <p className="text-center text-xs font-bold uppercase tracking-[0.25em] text-slate-500">{bar.section_label}</p>
      ) : null}
      <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((t, i) => (
          <div key={`${t.trust_label}-${i}`} className="text-center sm:text-left">
            {t.trust_label ? <p className="font-semibold text-slate-900">{t.trust_label}</p> : null}
            {t.trust_detail ? <p className="mt-2 text-sm leading-relaxed text-slate-600">{t.trust_detail}</p> : null}
          </div>
        ))}
      </div>
    </section>
  );
}
