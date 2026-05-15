import type { LandingPainSection } from "@/lib/types";

function cardAccent(i: number) {
  const accents = [
    "border-rose-200/80 bg-gradient-to-br from-rose-50 to-white",
    "border-amber-200/80 bg-gradient-to-br from-amber-50 to-white",
    "border-slate-300/80 bg-gradient-to-br from-slate-50 to-white",
  ];
  return accents[i % accents.length];
}

export function PainSection({ section }: { section?: LandingPainSection }) {
  const cards = section?.pain_cards?.filter((c) => c.pain_label || c.pain_body) ?? [];
  if (
    !section ||
    (!section.section_heading && !section.section_subheading && cards.length === 0)
  ) {
    return null;
  }

  return (
    <section className="scroll-mt-24 space-y-10">
      <div className="space-y-4">
        {section.section_label ? (
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-blue-700">{section.section_label}</p>
        ) : null}
        {section.section_heading ? (
          <h2 className="max-w-3xl text-balance text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
            {section.section_heading}
          </h2>
        ) : null}
        {section.section_subheading ? (
          <p className="max-w-3xl text-lg leading-relaxed text-slate-600">{section.section_subheading}</p>
        ) : null}
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {cards.map((card, i) => (
          <article
            key={`${card.pain_label}-${i}`}
            className={`flex flex-col rounded-2xl border p-6 shadow-sm ${cardAccent(i)}`}
          >
            <div className="mb-4 flex items-start justify-between gap-3">
              <span className="font-mono text-sm font-bold text-slate-400">
                {String(card.card_number ?? i + 1).padStart(2, "0")}
              </span>
            </div>
            {card.pain_label ? (
              <h3 className="text-lg font-semibold leading-snug text-slate-900">{card.pain_label}</h3>
            ) : null}
            {card.pain_body ? (
              <p className="mt-3 flex-1 text-sm leading-relaxed text-slate-700">{card.pain_body}</p>
            ) : null}
            {card.pain_evidence_hook ? (
              <p className="mt-4 border-t border-slate-200/80 pt-4 text-sm font-medium italic text-blue-900">
                {card.pain_evidence_hook}
              </p>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
