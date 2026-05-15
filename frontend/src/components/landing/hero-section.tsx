import type { LandingHero, LandingMetaBlock } from "@/lib/types";
import { certifyOsHref } from "@/lib/certify-links";

export function HeroSection({
  hero,
  meta,
  companyName,
}: {
  hero?: LandingHero;
  meta?: LandingMetaBlock;
  companyName: string;
}) {
  if (!hero?.headline && !hero?.subheadline) return null;

  const primary = hero.cta_primary;
  const secondary = hero.cta_secondary;
  const stat = hero.hero_stat;

  return (
    <section className="relative overflow-hidden rounded-3xl border border-blue-100 bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 px-6 py-14 text-white shadow-2xl shadow-blue-900/30 md:px-12 md:py-16">
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 20%, rgba(59,130,246,0.35), transparent 45%), radial-gradient(circle at 80% 10%, rgba(148,163,184,0.25), transparent 40%)",
        }}
      />
      <div className="relative mx-auto max-w-4xl space-y-8">
        {hero.eyebrow_tag ? (
          <p className="inline-flex max-w-prose rounded-full border border-white/15 bg-white/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-blue-100">
            {hero.eyebrow_tag}
          </p>
        ) : (
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-200">
            Personalized for {companyName}
          </p>
        )}
        {meta?.personalization_signal ? (
          <p className="max-w-2xl text-sm leading-relaxed text-blue-100/90">{meta.personalization_signal}</p>
        ) : null}
        <div className="space-y-5">
          <h1 className="text-balance text-3xl font-bold leading-tight tracking-tight md:text-5xl md:leading-[1.1]">
            {hero.headline}
          </h1>
          {hero.subheadline ? (
            <p className="max-w-3xl text-lg leading-relaxed text-slate-200 md:text-xl">{hero.subheadline}</p>
          ) : null}
        </div>

        {stat?.number ? (
          <div className="grid gap-4 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm md:grid-cols-[1fr_auto] md:items-center">
            <div>
              <p className="text-4xl font-bold tracking-tight text-white md:text-5xl">{stat.number}</p>
              {stat.label ? <p className="mt-2 text-sm font-medium text-blue-100">{stat.label}</p> : null}
            </div>
            {stat.source_hint ? (
              <p className="text-xs uppercase tracking-wide text-slate-400 md:text-right">{stat.source_hint}</p>
            ) : null}
          </div>
        ) : null}

        <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-center">
          {primary?.button_text ? (
            <a
              href={certifyOsHref()}
              className="inline-flex items-center justify-center rounded-xl bg-blue-500 px-6 py-3.5 text-center text-base font-semibold text-white shadow-lg shadow-blue-900/40 transition hover:bg-blue-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              {primary.button_text}
            </a>
          ) : null}
          {secondary?.link_text ? (
            <a
              href={certifyOsHref(secondary.link_url_slug)}
              className="inline-flex items-center justify-center text-base font-semibold text-blue-100 underline-offset-4 hover:text-white hover:underline"
            >
              {secondary.link_text}
            </a>
          ) : null}
        </div>
        {primary?.button_subtext ? (
          <p className="text-sm text-slate-400">{primary.button_subtext}</p>
        ) : null}
      </div>
    </section>
  );
}
