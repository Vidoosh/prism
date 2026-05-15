import Link from "next/link";

import type { PipelineRunResult } from "@/lib/types";

function tierBadge(tier?: string) {
  const t = (tier || "D").toUpperCase();
  const cls =
    t === "A"
      ? "bg-emerald-100 text-emerald-900"
      : t === "B"
        ? "bg-blue-100 text-blue-900"
        : t === "C"
          ? "bg-amber-100 text-amber-900"
          : "bg-slate-100 text-slate-700";
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded ${cls}`}>{t}</span>
  );
}

export function CompanyCard({ row }: { row: PipelineRunResult }) {
  const d = row.domain || "";
  const slug = encodeURIComponent(d.replace(/\./g, "-"));
  return (
    <div className="border border-slate-200 rounded-lg p-4 flex justify-between items-start gap-4 bg-white">
      <div>
        <Link href={`/results/${slug}`} className="font-semibold text-blue-700 hover:underline">
          {row.enrichment?.company_name || d}
        </Link>
        <p className="text-xs text-slate-500">{d}</p>
      </div>
      <div className="flex flex-col items-end gap-1">
        {tierBadge(row.enrichment?.icp_fit_tier)}
        <span className="text-xs text-slate-600">Intent {row.enrichment?.intent_score ?? "—"}</span>
      </div>
    </div>
  );
}
