import type {
  LandingPageContent,
  LandingPageData,
  PipelineRunResult,
} from "./types";

function apiBase(): string {
  if (typeof window === "undefined") {
    return (
      process.env.INTERNAL_API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000"
    ).replace(/\/$/, "");
  }
  return (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
}

export async function startPipeline(url: string): Promise<{ run_id: string }> {
  const r = await fetch(`${apiBase()}/api/pipeline/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getRunStatus(runId: string): Promise<PipelineRunResult> {
  const r = await fetch(`${apiBase()}/api/pipeline/status/${runId}`, { cache: "no-store" });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function listResults(): Promise<{ items: PipelineRunResult[] }> {
  const r = await fetch(`${apiBase()}/api/results`, { cache: "no-store" });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getResultByDomain(domain: string): Promise<PipelineRunResult> {
  const enc = encodeURIComponent(domain);
  const r = await fetch(`${apiBase()}/api/results/${enc}`, { cache: "no-store" });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getLandingContentByDomain(domain: string): Promise<LandingPageContent | null> {
  const enc = encodeURIComponent(domain);
  const r = await fetch(`${apiBase()}/api/landing/${enc}`, { cache: "no-store" });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(await r.text());
  return r.json() as LandingPageContent;
}

export async function uploadBatch(file: File): Promise<{ batch_id: string }> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${apiBase()}/api/pipeline/batch`, { method: "POST", body: fd });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getBatch(batchId: string): Promise<unknown> {
  const r = await fetch(`${apiBase()}/api/pipeline/batch/${batchId}`, { cache: "no-store" });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export type { LandingPageContent, LandingPageData };
