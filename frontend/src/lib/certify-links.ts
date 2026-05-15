/** Build outbound links for landing CTAs (marketing site). */

export function certifyOsHref(path?: string): string {
  const base = "https://certifyos.com";
  const p = (path || "").trim().replace(/^\//, "");
  if (!p) return `${base}/contact`;
  return `${base}/${p}`;
}
