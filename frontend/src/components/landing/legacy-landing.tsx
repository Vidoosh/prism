import type { LandingPageData } from "@/lib/types";

const PEER_COPY: Record<string, string[]> = {
  health_plan: [
    "Plans like yours use CertifyOS to cut credentialing cycle time while keeping NCQA evidence audit-ready.",
    "Delegated roster standardization is the fastest path to directory accuracy under federal pricing transparency pressure.",
  ],
  digital_health: [
    "High-growth virtual care teams use CertifyOS to collapse licensing bottlenecks across new markets.",
    "Automation here is revenue protection — fewer stranded providers, faster dates of service.",
  ],
  default: [
    "Provider data is the constraint on every AI initiative — CertifyOS builds the infrastructure layer underneath.",
  ],
};

/** Fallback layout when rich landing JSON is not yet generated (Sanity / legacy shape). */
export function LegacyLanding({ data }: { data: LandingPageData }) {
  const h = data.content_blocks?.hero_headline;
  const sub = data.content_blocks?.personalized_value_proposition;
  const points = data.pain_points?.filter((p) => (p.description || p.pain_id)?.trim()) ?? [];
  const signals = data.intent_signals?.filter((s) => (s.description || s.signal_type)?.trim()) ?? [];
  const sev = points[0]?.severity || "medium";
  const border =
    sev === "critical"
      ? "border-red-300 bg-red-50/50"
      : sev === "high"
        ? "border-orange-200 bg-orange-50/30"
        : "border-slate-200 bg-slate-50/50";
  const peerKey = data.organization_type || "default";
  const peerLines = PEER_COPY[peerKey] || PEER_COPY.default;
  const topProduct = data.product_details?.[0];
  const cta = data.content_blocks?.cta_block;

  return (
    <>
      <section className="space-y-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">
          Personalized for {data.company_name || data.domain}
        </p>
        <h1 className="text-3xl font-bold leading-tight text-slate-900 md:text-4xl">{h}</h1>
        <p className="text-lg text-slate-600">{sub}</p>
      </section>

      <section className={`rounded-2xl border p-8 ${border}`}>
        <h2 className="mb-3 text-lg font-semibold">Why this matters now</h2>
        {data.content_blocks?.pain_point_paragraph ? (
          <p className="mb-6 whitespace-pre-wrap leading-relaxed text-slate-700">
            {data.content_blocks.pain_point_paragraph}
          </p>
        ) : null}

        {points.length > 0 ? (
          <div className="mb-6">
            <h3 className="mb-2 text-sm font-semibold text-slate-800">Pain points</h3>
            <ul className="space-y-3">
              {points.map((p, i) => (
                <li key={`${p.pain_id || "p"}-${i}`} className="border-l-4 border-amber-200/80 pl-3 text-sm">
                  <span className="font-medium text-slate-900">{p.pain_id || "—"}</span>
                  {p.severity ? <span className="ml-2 capitalize text-slate-500">({p.severity})</span> : null}
                  {p.description ? <p className="mt-1 text-slate-700">{p.description}</p> : null}
                  {p.evidence ? <p className="mt-1 text-xs text-slate-500">{p.evidence}</p> : null}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {signals.length > 0 ? (
          <div>
            <h3 className="mb-2 text-sm font-semibold text-slate-800">Intent signals</h3>
            <ul className="space-y-2">
              {signals.map((s, i) => (
                <li key={`${s.signal_type || "s"}-${i}`} className="text-sm">
                  <span className="rounded border border-slate-200 bg-white/80 px-1.5 py-0.5 font-mono text-xs">
                    {s.signal_tier || "—"}
                  </span>
                  {s.signal_type ? <span className="ml-2 font-medium text-slate-900">{s.signal_type}</span> : null}
                  {s.description ? <p className="mt-1 text-slate-700">{s.description}</p> : null}
                  {s.evidence ? <p className="mt-1 text-xs text-slate-500">{s.evidence}</p> : null}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {!data.content_blocks?.pain_point_paragraph && points.length === 0 && signals.length === 0 ? (
          <p className="text-sm text-slate-500">No structured pain or intent data for this account yet.</p>
        ) : null}
      </section>

      <section className="border-t border-slate-200 pt-10">
        <h2 className="mb-4 text-lg font-semibold">What peers are solving</h2>
        <ul className="space-y-3 text-sm text-slate-700">
          {peerLines.map((l, i) => (
            <li key={i} className="flex gap-2">
              <span className="font-bold text-blue-600">•</span>
              <span>{l}</span>
            </li>
          ))}
        </ul>
      </section>

      {topProduct ? (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold">How CertifyOS fits: {topProduct.product_name}</h2>
          <p className="text-slate-700">{topProduct.hero_copy}</p>
          <ul className="list-inside list-disc space-y-1 text-slate-700">
            {(topProduct.proof_points || []).map((x, i) => (
              <li key={i}>{x}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {cta?.primary_cta_text ? (
        <section className="rounded-2xl bg-slate-900 p-10 text-center text-white space-y-3">
          <h2 className="text-2xl font-bold">{cta.primary_cta_text}</h2>
          <p className="text-slate-300">{cta.primary_cta_subtext}</p>
          <p className="text-sm text-slate-400">{cta.supporting_proof_point}</p>
          <a
            href="https://certifyos.com"
            className="mt-4 inline-block rounded-lg bg-white px-6 py-3 font-semibold text-slate-900"
          >
            Talk to us
          </a>
        </section>
      ) : null}
    </>
  );
}
