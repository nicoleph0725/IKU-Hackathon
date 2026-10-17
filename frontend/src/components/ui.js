// Small HTML helpers shared by views.

/** Escape user-provided text before putting it into innerHTML. ALWAYS use for user content. */
export function esc(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

/** A "TODO" placeholder box so unbuilt parts of a page are obvious. */
export function todo(text) {
  return `<div class="rounded-xl border-2 border-dashed border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">TODO: ${esc(text)}</div>`;
}

// TODO: add helpers as needed, e.g. stars(rating), priceLabel(level), busynessBadge(busyness), timeAgo(iso)
