"use client";

import { useCallback, useEffect, useState } from "react";

import { BatchUpload } from "@/components/batch-upload";
import { PipelineResultsTable } from "@/components/pipeline-results";
import { UrlSubmitForm } from "@/components/url-submit-form";
import { listResults } from "@/lib/api";
import type { PipelineRunResult } from "@/lib/types";

export default function DashboardPage() {
  const [items, setItems] = useState<PipelineRunResult[]>([]);

  const refresh = useCallback(async () => {
    try {
      const { items: rows } = await listResults();
      setItems(rows);
    } catch {
      setItems([]);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-6xl mx-auto p-8 space-y-10">
        <header>
          <h1 className="text-3xl font-bold text-slate-900">Prism: Account enrichment</h1>
          <p className="text-slate-600 mt-1">URL → Scrape → Research → Insight → Content → Sanity → HubSpot</p>
        </header>

        <section className="grid md:grid-cols-2 gap-8">
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
            <h2 className="font-semibold text-slate-800">Single URL</h2>
            <UrlSubmitForm onCompleted={refresh} />
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
            <h2 className="font-semibold text-slate-800">Batch CSV</h2>
            <BatchUpload onBatchStarted={() => refresh()} />
          </div>
        </section>

        <section className="space-y-3">
          <div className="flex justify-between items-center">
            <h2 className="font-semibold text-slate-800">Recent runs</h2>
            <button type="button" onClick={refresh} className="text-sm text-blue-600 hover:underline">
              Refresh
            </button>
          </div>
          {items.length === 0 ? (
            <p className="text-sm text-slate-500">No runs yet.</p>
          ) : (
            <PipelineResultsTable items={items} />
          )}
        </section>
      </div>
    </div>
  );
}
