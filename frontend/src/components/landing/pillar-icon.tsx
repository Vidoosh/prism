/** Maps model icon hints to simple inline SVGs (no extra deps). */

export function PillarIcon({ hint }: { hint?: string }) {
  const h = (hint || "").toLowerCase();
  const cls = "h-10 w-10 shrink-0 text-blue-600";

  if (h.includes("shield"))
    return (
      <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 3l7 4v5c0 5-3.5 9-7 10-3.5-1-7-5-7-10V7l7-4z"
        />
      </svg>
    );
  if (h.includes("lightning") || h.includes("bolt"))
    return (
      <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 2L4 14h7l-1 8 10-14h-7l0-6z" />
      </svg>
    );
  if (h.includes("network") || h.includes("hub"))
    return (
      <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 3a3 3 0 100 6 3 3 0 000-6zM5 18a3 3 0 106 0 3 3 0 00-6 0zm14 0a3 3 0 106 0 3 3 0 00-6 0z"
        />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v3m-5 6l4-2m6 2l-4-2" />
      </svg>
    );
  if (h.includes("lock"))
    return (
      <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M7 11V8a5 5 0 0110 0v3M6 11h12v10H6V11z"
        />
      </svg>
    );
  if (h.includes("chart") || h.includes("graph"))
    return (
      <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 19V5m8 14V9m8 10v-6" />
      </svg>
    );

  return (
    <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v12m6-6H6" />
    </svg>
  );
}
