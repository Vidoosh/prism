import Link from "next/link";

import type { PipelineRunResult } from "@/lib/types";

function tierColor(tier?: string) {
  switch ((tier || "").toUpperCase()) {
    case "A":
      return "bg-emerald-100 text-emerald-900";
    case "B":
      return "bg-blue-100 text-blue-900";
    case "C":
      return "bg-amber-100 text-amber-900";
    default:
      return "bg-slate-100 text-slate-700";
  }
}

export function PipelineResultsTable({ items }: { items: PipelineRunResult[] }) {
  return (
    <div className="overflow-x-auto border border-slate-200 rounded-lg">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-600">
          <tr>
            <th className="p-3">Company</th>
            <th className="p-3">Domain</th>
            <th className="p-3">ICP</th>
            <th className="p-3">Intent</th>
            <th className="p-3">Confidence</th>
            <th className="p-3">Status</th>
            <th className="p-3">Updated</th>
          </tr>
        </thead>
        <tbody>
          {items.map((row) => {
            const d = row.domain || "";
            const slug = d.replace(/\./g, "-");
            return (
              <tr key={row.run_id} className="border-t border-slate-100 hover:bg-slate-50/80">
                <td className="p-3 font-medium text-slate-900">
                  <Link href={`/results/${encodeURIComponent(slug)}`} className="text-blue-700 hover:underline">
                    {row.enrichment?.company_name || d}
                  </Link>
                </td>
                <td className="p-3 text-slate-600">{d}</td>
                <td className="p-3">
                  <span
                    className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold ${tierColor(row.enrichment?.icp_fit_tier)}`}
                  >
                    {row.enrichment?.icp_fit_tier || "—"} ({row.enrichment?.icp_fit_score ?? "—"})
                  </span>
                </td>
                <td className="p-3 text-slate-700">{row.enrichment?.intent_score ?? "—"}</td>
                <td className="p-3 capitalize text-slate-700">{row.enrichment?.data_confidence || "—"}</td>
                <td className="p-3 capitalize text-slate-700">{row.status}</td>
                <td className="p-3 text-slate-500 text-xs">{row.updated_at || "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
