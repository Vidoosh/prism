"use client";

import { useCallback, useState } from "react";

import { getRunStatus, startPipeline } from "@/lib/api";

export function UrlSubmitForm({ onCompleted }: { onCompleted?: () => void }) {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const poll = useCallback(
    async (runId: string) => {
      for (let i = 0; i < 120; i++) {
        const st = await getRunStatus(runId);
        if (st.status === "completed" || st.status === "failed") {
          return st;
        }
        await new Promise((r) => setTimeout(r, 2000));
      }
      return null;
    },
    []
  );

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    setBusy(true);
    try {
      const { run_id } = await startPipeline(url);
      setMsg(`Run ${run_id} started…`);
      const final = await poll(run_id);
      if (final?.status === "completed") setMsg(`Done — ${final.domain}`);
      else if (final?.status === "failed") setErr(final.error || "failed");
      else setErr("timeout waiting for pipeline");
      onCompleted?.();
    } catch (ex: unknown) {
      setErr(ex instanceof Error ? ex.message : "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-3 max-w-xl">
      <label className="text-sm font-medium text-slate-700">Company URL</label>
      <input
        className="border border-slate-300 rounded-lg px-3 py-2 text-sm"
        placeholder="https://example-health.com"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        required
      />
      <button
        type="submit"
        disabled={busy}
        className="bg-slate-900 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
      >
        {busy ? "Running…" : "Run pipeline"}
      </button>
      {msg && <p className="text-sm text-emerald-700">{msg}</p>}
      {err && <p className="text-sm text-red-600">{err}</p>}
    </form>
  );
}
