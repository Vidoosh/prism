import type { LandingProductSection } from "@/lib/types";
import { certifyOsHref } from "@/lib/certify-links";

export function ProductSection({ section }: { section?: LandingProductSection }) {
  const cards = section?.product_cards?.filter((c) => c.product_name || c.product_body) ?? [];
  if (!section || (!section.section_heading && cards.length === 0)) return null;

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
            key={`${card.product_name}-${i}`}
            className="flex flex-col rounded-2xl border border-slate-200 bg-gradient-to-b from-white to-slate-50 p-6 shadow-sm"
          >
            {card.product_name ? (
              <h3 className="text-xl font-bold text-slate-900">{card.product_name}</h3>
            ) : null}
            {card.product_tagline ? (
              <p className="mt-2 text-sm font-semibold text-blue-800">{card.product_tagline}</p>
            ) : null}
            {card.product_body ? (
              <p className="mt-4 flex-1 text-sm leading-relaxed text-slate-700">{card.product_body}</p>
            ) : null}
            {card.product_proof_point ? (
              <p className="mt-4 rounded-lg bg-blue-50 px-3 py-2 text-sm font-medium text-blue-900">
                {card.product_proof_point}
              </p>
            ) : null}
            {card.product_cta_micro ? (
              <a
                href={certifyOsHref()}
                className="mt-6 inline-flex text-sm font-semibold text-blue-700 hover:text-blue-900 hover:underline"
              >
                {card.product_cta_micro}
              </a>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
