import type { LandingProofSection } from "@/lib/types";

function StatCard({ stat, idx }: { stat?: { number?: string; label?: string; relevance_note?: string }; idx: number }) {
  if (!stat?.number && !stat?.label) return null;
  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <span className="text-xs font-semibold uppercase tracking-wide text-blue-700">Proof {idx}</span>
      <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900">{stat.number}</p>
      {stat.label ? <p className="mt-1 text-sm font-medium text-slate-700">{stat.label}</p> : null}
      {stat.relevance_note ? <p className="mt-4 text-sm leading-relaxed text-slate-600">{stat.relevance_note}</p> : null}
    </div>
  );
}

export function SocialProofSection({ proof }: { proof?: LandingProofSection }) {
  const stats = [proof?.anchor_stat_1, proof?.anchor_stat_2, proof?.anchor_stat_3].filter(
    (s) => s && (s.number || s.label),
  );
  if (
    !proof ||
    (!proof.section_heading && stats.length === 0 && !proof.icp_matched_social_proof_label)
  ) {
    return null;
  }

  return (
    <section className="scroll-mt-24 space-y-10">
      <div className="space-y-4">
        {proof.section_label ? (
          <p className="text-xs font-bold uppercase tracking-[0.25em] text-blue-700">{proof.section_label}</p>
        ) : null}
        {proof.section_heading ? (
          <h2 className="max-w-3xl text-balance text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
            {proof.section_heading}
          </h2>
        ) : null}
        {proof.icp_matched_social_proof_label ? (
          <p className="max-w-3xl text-lg font-medium text-slate-700">{proof.icp_matched_social_proof_label}</p>
        ) : null}
      </div>

      {stats.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-3">
          {stats.map((s, i) => (
            <StatCard key={i} stat={s} idx={i + 1} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
