import type { LandingSeoContentBlock } from "@/lib/types";

/** Visible, subdued SEO block (still crawlable; avoids `display:none`). */
export function SeoBlock({ block }: { block?: LandingSeoContentBlock }) {
  if (!block?.h2_subpage_heading && !block?.seo_paragraph) return null;

  return (
    <section className="scroll-mt-24 border-t border-slate-200 pt-12 pb-8">
      <div className="mx-auto max-w-3xl rounded-2xl bg-slate-50 px-6 py-8 text-slate-600">
        {block.h2_subpage_heading ? (
          <h2 className="text-xl font-semibold text-slate-800">{block.h2_subpage_heading}</h2>
        ) : null}
        {block.seo_paragraph ? (
          <p className="mt-4 text-sm leading-relaxed text-slate-600">{block.seo_paragraph}</p>
        ) : null}
      </div>
    </section>
  );
}
