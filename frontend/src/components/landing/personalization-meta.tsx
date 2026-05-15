import type { LandingPersonalizationMetadata } from "@/lib/types";

export function PersonalizationMetaRibbon({ meta }: { meta?: LandingPersonalizationMetadata }) {
  if (!meta?.content_confidence && !meta?.hook_technique_deployed && !meta?.icp_archetype) return null;

  const chips: string[] = [];
  if (meta.icp_archetype) chips.push(`ICP: ${meta.icp_archetype}`);
  if (meta.hook_technique_deployed) chips.push(meta.hook_technique_deployed);
  if (meta.tone_deployed) chips.push(meta.tone_deployed.replace(/-/g, " "));
  if (meta.products_featured?.length)
    chips.push(`Products: ${meta.products_featured.slice(0, 3).join(", ")}`);

  return (
    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/80 px-4 py-3 text-xs text-slate-600">
      {meta.content_confidence ? (
        <p className="font-medium text-amber-900">{meta.content_confidence}</p>
      ) : null}
      {chips.length > 0 ? (
        <ul className="mt-2 flex flex-wrap gap-2">
          {chips.map((c) => (
            <li key={c} className="rounded-full bg-white px-3 py-1 ring-1 ring-slate-200">
              {c}
            </li>
          ))}
        </ul>
      ) : null}
      {meta.key_personalization_signals_used?.length ? (
        <ul className="mt-3 list-inside list-disc space-y-1 text-slate-500">
          {meta.key_personalization_signals_used.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
