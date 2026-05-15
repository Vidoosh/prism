"use client";

import { useState } from "react";

import { getBatch, uploadBatch } from "@/lib/api";

export function BatchUpload({ onBatchStarted }: { onBatchStarted?: (id: string) => void }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setErr(null);
    setBusy(true);
    try {
      const { batch_id } = await uploadBatch(f);
      onBatchStarted?.(batch_id);
      const st = await getBatch(batch_id);
      console.info("batch", st);
    } catch (ex: unknown) {
      setErr(ex instanceof Error ? ex.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-slate-700">Batch CSV (column: url)</label>
      <input type="file" accept=".csv,text/csv" disabled={busy} onChange={onFile} className="text-sm" />
      {busy && <p className="text-sm text-slate-500">Uploading…</p>}
      {err && <p className="text-sm text-red-600">{err}</p>}
    </div>
  );
}
