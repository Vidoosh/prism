import Link from "next/link";
import { notFound } from "next/navigation";

import { getResultByDomain } from "@/lib/api";
import type { EnrichmentResult } from "@/lib/types";

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900 mb-4">{title}</h2>
      {children}
    </section>
  );
}

function DlRow({ label, value }: { label: string; value?: React.ReactNode }) {
  const empty =
    value === undefined ||
    value === null ||
    value === "" ||
    (Array.isArray(value) && value.length === 0);
  if (empty) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-[180px_1fr] gap-1 text-sm border-b border-slate-100 py-2 last:border-0">
        <dt className="font-medium text-slate-600">{label}</dt>
        <dd className="text-slate-500">—</dd>
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 sm:grid-cols-[180px_1fr] gap-1 text-sm border-b border-slate-100 py-2 last:border-0">
      <dt className="font-medium text-slate-600">{label}</dt>
      <dd className="text-slate-900">{value}</dd>
    </div>
  );
}

function TagList({ items }: { items?: string[] }) {
  if (!items?.length) return <p className="text-sm text-slate-500">—</p>;
  return (
    <ul className="flex flex-wrap gap-2">
      {items.map((x, i) => (
        <li key={`${x}-${i}`} className="text-xs font-medium px-2 py-1 rounded-md bg-slate-100 text-slate-800">
          {x}
        </li>
      ))}
    </ul>
  );
}

function severityBadge(severity?: string) {
  const s = (severity || "").toLowerCase();
  const map: Record<string, string> = {
    critical: "bg-red-100 text-red-900",
    high: "bg-orange-100 text-orange-900",
    medium: "bg-amber-100 text-amber-900",
    low: "bg-slate-100 text-slate-800",
  };
  const cls = map[s] || "bg-slate-100 text-slate-700";
  return <span className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold capitalize ${cls}`}>{severity || "—"}</span>;
}

export default async function ResultPage({ params }: { params: Promise<{ domain: string }> }) {
  const { domain: raw } = await params;
  const slug = decodeURIComponent(raw);
  const lookup = slug.includes(".") ? slug : slug.replace(/-/g, ".");
  let data;
  try {
    data = await getResultByDomain(lookup);
  } catch {
    notFound();
  }

  const e: EnrichmentResult | undefined = data.enrichment;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="max-w-4xl mx-auto p-8 space-y-8 pb-16">
        <div className="space-y-2">
          <Link href="/" className="text-sm text-blue-700 hover:underline font-medium">
            ← Dashboard
          </Link>
          <div className="flex flex-col gap-1">
            <h1 className="text-3xl font-bold text-slate-900">{e?.company_name || data.domain}</h1>
            <p className="text-slate-600 text-sm">{data.domain}</p>
            {data.source_url ? (
              <p className="text-sm">
                <span className="text-slate-500">Source: </span>
                <a href={data.source_url} className="text-blue-700 underline break-all" target="_blank" rel="noreferrer">
                  {data.source_url}
                </a>
              </p>
            ) : null}
          </div>
          <div className="flex gap-2 mt-3 flex-wrap items-center">
            <span className="text-xs font-semibold px-2 py-1 rounded-md bg-slate-200 text-slate-900">
              ICP tier {e?.icp_fit_tier ?? "—"}
            </span>
            <span className="text-xs font-semibold px-2 py-1 rounded-md bg-slate-200 text-slate-900">
              Score {e?.icp_fit_score ?? "—"}
            </span>
            <span className="text-xs font-semibold px-2 py-1 rounded-md bg-slate-200 text-slate-900">
              Intent {e?.intent_score ?? "—"}
            </span>
            <span className="text-xs font-semibold px-2 py-1 rounded-md bg-slate-200 text-slate-900 capitalize">
              Confidence {e?.data_confidence ?? "—"}
            </span>
            {severityBadge(e?.pain_severity)}
            {e?.requires_review ? (
              <span className="text-xs font-semibold px-2 py-1 rounded-md bg-amber-200 text-amber-950">Needs review</span>
            ) : null}
          </div>
          <p className="text-xs text-slate-500 pt-1">
            Run <span className="font-mono">{data.run_id}</span> · {data.status}
            {data.updated_at ? ` · ${data.updated_at}` : ""}
          </p>
          {data.error ? (
            <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{data.error}</p>
          ) : null}
        </div>

        <SectionCard title="Quick links">
          <div className="flex flex-wrap gap-4 text-sm font-medium">
            {data.landing_page_url ? (
              <a href={data.landing_page_url} className="text-blue-700 underline">
                Landing page
              </a>
            ) : (
              <span className="text-slate-500">Landing page —</span>
            )}
            {data.sanity_studio_url ? (
              <a href={data.sanity_studio_url} className="text-blue-700 underline">
                Sanity Studio
              </a>
            ) : (
              <span className="text-slate-500">Sanity —</span>
            )}
            {data.hubspot_portal_url ? (
              <a href={data.hubspot_portal_url} className="text-blue-700 underline">
                HubSpot
              </a>
            ) : (
              <span className="text-slate-500">HubSpot —</span>
            )}
          </div>
        </SectionCard>

        <SectionCard title="Company profile">
          <dl>
            <DlRow label="Organization type" value={e?.organization_type} />
            <DlRow label="Subtype" value={e?.organization_subtype ?? undefined} />
            <DlRow label="Geographic footprint" value={e?.geographic_footprint} />
            <DlRow label="Funding stage" value={e?.funding_stage} />
            <DlRow label="Estimated provider count" value={e?.estimated_provider_count_range} />
          </dl>
          <div className="mt-4 space-y-2">
            <p className="text-sm font-medium text-slate-700">States mentioned</p>
            <TagList items={e?.states_mentioned} />
          </div>
          <div className="mt-4 space-y-2">
            <p className="text-sm font-medium text-slate-700">Provider types mentioned</p>
            <TagList items={e?.provider_types_mentioned} />
          </div>
        </SectionCard>

        <SectionCard title="ICP scoring & confidence">
          <dl>
            <DlRow label="ICP fit score" value={e?.icp_fit_score !== undefined ? String(e.icp_fit_score) : undefined} />
            <DlRow label="ICP fit tier" value={e?.icp_fit_tier} />
            <DlRow label="Non-ICP reason" value={e?.non_icp_reason ?? undefined} />
          </dl>
          <div className="mt-4 space-y-2">
            <p className="text-sm font-medium text-slate-700">ICP scoring rationale</p>
            <p className="text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">{e?.icp_scoring_rationale || "—"}</p>
          </div>
          <div className="mt-4 space-y-2">
            <p className="text-sm font-medium text-slate-700">Data confidence rationale</p>
            <p className="text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">{e?.confidence_rationale || "—"}</p>
          </div>
        </SectionCard>

        <SectionCard title="Product fit">
          <TagList items={e?.primary_product_fit} />
        </SectionCard>

        <SectionCard title="Pain points">
          {(e?.pain_points || []).length === 0 ? (
            <p className="text-sm text-slate-500">—</p>
          ) : (
            <ul className="space-y-4">
              {(e?.pain_points || []).map((p, i) => (
                <li key={`${p.pain_id}-${i}`} className="border-l-4 border-amber-300 pl-4 py-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-slate-900">{p.pain_id || "—"}</span>
                    {severityBadge(p.severity)}
                  </div>
                  {p.description ? (
                    <p className="text-sm text-slate-800 mt-2 whitespace-pre-wrap">{p.description}</p>
                  ) : null}
                  {p.evidence ? (
                    <p className="text-xs text-slate-600 mt-2 whitespace-pre-wrap">
                      <span className="font-medium text-slate-700">Evidence: </span>
                      {p.evidence}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        <SectionCard title="Intent signals">
          {(e?.intent_signals || []).length === 0 ? (
            <p className="text-sm text-slate-500">—</p>
          ) : (
            <ul className="space-y-5">
              {(e?.intent_signals || []).map((s, i) => (
                <li key={`${s.signal_type}-${i}`} className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs bg-white border border-slate-200 px-2 py-0.5 rounded text-slate-900">
                      {s.signal_tier || "—"}
                    </span>
                    <span className="font-semibold text-slate-900">{s.signal_type || "Signal"}</span>
                  </div>
                  {s.description ? (
                    <p className="text-sm text-slate-800 whitespace-pre-wrap">{s.description}</p>
                  ) : null}
                  {s.evidence ? (
                    <p className="text-xs text-slate-700 whitespace-pre-wrap">
                      <span className="font-semibold text-slate-800">Evidence: </span>
                      {s.evidence}
                    </p>
                  ) : null}
                  {s.recommended_action ? (
                    <p className="text-xs text-slate-700 whitespace-pre-wrap">
                      <span className="font-semibold text-slate-800">Recommended action: </span>
                      {s.recommended_action}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        <SectionCard title="Market & regulatory intelligence">
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-slate-700 mb-2">Competitor mentions</p>
              <TagList items={e?.competitor_mentions} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-700 mb-2">Regulatory mentions</p>
              <TagList items={e?.regulatory_mentions} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-700 mb-2">Accreditation mentions</p>
              <TagList items={e?.accreditation_mentions} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-700 mb-2">Inferred intent themes</p>
              <TagList items={e?.inferred_intent_themes} />
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Generated content (Gemini output)">
          <div className="space-y-4 text-sm">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Hero headline</p>
              <p className="text-lg font-semibold text-slate-900 whitespace-pre-wrap">{e?.hero_headline || "—"}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Personalized value proposition</p>
              <p className="text-slate-800 whitespace-pre-wrap leading-relaxed">{e?.personalized_value_proposition || "—"}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Pain point paragraph</p>
              <p className="text-slate-800 whitespace-pre-wrap leading-relaxed">{e?.pain_point_paragraph || "—"}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Hook technique</p>
              <p className="text-slate-800">{e?.hook_technique_recommended || "—"}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">CTA block</p>
              <p className="font-semibold text-slate-900">{e?.cta_block?.primary_cta_text || "—"}</p>
              <p className="text-slate-800 whitespace-pre-wrap">{e?.cta_block?.primary_cta_subtext || ""}</p>
              <p className="text-xs text-slate-700 whitespace-pre-wrap">{e?.cta_block?.supporting_proof_point || ""}</p>
            </div>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
