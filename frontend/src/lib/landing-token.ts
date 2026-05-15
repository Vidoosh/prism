import { createHmac } from "crypto";

export function expectedLandingToken(slug: string, secret: string): string {
  return createHmac("sha256", secret).update(slug).digest("hex").slice(0, 20);
}

export function landingTokenOk(slug: string, t: string | undefined, secret: string | undefined): boolean {
  if (!secret) return true;
  if (!t) return false;
  try {
    const a = expectedLandingToken(slug, secret);
    return a === t;
  } catch {
    return false;
  }
}
