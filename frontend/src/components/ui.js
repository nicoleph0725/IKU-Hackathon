// Small presentational helpers shared by views. All return HTML strings.

/** Escape user-provided text before putting it into innerHTML. ALWAYS use for user content. */
export function esc(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

export function stars(value, { size = 'text-sm' } = {}) {
  if (value == null) return `<span class="${size} text-stone-400">No ratings</span>`;
  const full = Math.round(value);
  return `<span class="${size} text-amber-500" aria-label="${value} out of 5">${'★'.repeat(full)}<span class="text-stone-300">${'★'.repeat(5 - full)}</span></span>`;
}

export const priceLabel = (level) => '£'.repeat(level ?? 0);

const BUSY_STYLES = {
  1: 'bg-emerald-100 text-emerald-800',
  2: 'bg-lime-100 text-lime-800',
  3: 'bg-amber-100 text-amber-800',
  4: 'bg-orange-100 text-orange-800',
  5: 'bg-red-100 text-red-800',
};

export const BUSY_COLORS = { 1: '#059669', 2: '#65a30d', 3: '#d97706', 4: '#ea580c', 5: '#dc2626' };

export function busynessBadge(busyness) {
  if (!busyness || busyness.level == null) {
    return `<span class="badge bg-stone-100 text-stone-500">Busyness unknown</span>`;
  }
  const cls = BUSY_STYLES[Math.round(busyness.level)];
  return `<span class="badge ${cls}">${esc(busyness.label)} · ${busyness.level}/5</span>`;
}

export function wifiLabel(cafe) {
  if (!cafe.has_wifi) return 'No wifi';
  return `Wifi ${'▮'.repeat(cafe.wifi_quality)}${'▯'.repeat(5 - cafe.wifi_quality)}`;
}

export function timeAgo(iso) {
  const seconds = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return new Date(iso).toLocaleDateString();
}

export function timeUntil(iso) {
  const minutes = Math.max(0, Math.round((new Date(iso).getTime() - Date.now()) / 60000));
  return minutes >= 60 ? `${Math.floor(minutes / 60)} h ${minutes % 60} min` : `${minutes} min`;
}

export function emptyState(message) {
  return `<p class="rounded-xl border border-dashed border-stone-300 p-6 text-center text-sm text-stone-500">${esc(message)}</p>`;
}
