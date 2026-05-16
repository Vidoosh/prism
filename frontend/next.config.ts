import type { NextConfig } from "next";

/**
 * Use `standalone` output for Docker/production images only.
 * Vercel builds set `VERCEL=1`; omitting `standalone` lets Vercel use its Next adapter.
 * Local/docker builds leave `VERCEL` unset → standalone matches frontend/Dockerfile.
 */
const isVercel = Boolean(process.env.VERCEL);

const nextConfig: NextConfig = {
  ...(!isVercel ? { output: "standalone" as const } : {}),
};

export default nextConfig;
