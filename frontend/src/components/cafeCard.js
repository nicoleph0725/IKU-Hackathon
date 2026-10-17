import { busynessBadge, esc, priceLabel, stars, wifiLabel } from './ui.js';

export function cafeCard(cafe) {
  const distance = cafe.distance_km != null ? `${cafe.distance_km.toFixed(1)} km` : '';
  return `
    <a href="#/cafes/${cafe.id}" data-cafe-id="${cafe.id}"
       class="card block transition hover:border-amber-700 hover:shadow-md">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <h3 class="truncate font-semibold">${esc(cafe.name)}</h3>
          <p class="truncate text-xs text-stone-500">${esc(cafe.address)}</p>
        </div>
        <span class="shrink-0 text-sm font-medium text-stone-600">${distance}</span>
      </div>
      <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        ${stars(cafe.avg_rating)}
        <span class="text-xs text-stone-500">(${cafe.review_count})</span>
        ${busynessBadge(cafe.busyness)}
      </div>
      <div class="mt-2 flex flex-wrap gap-x-4 text-xs text-stone-600">
        <span>${priceLabel(cafe.price_level)}</span>
        <span>🪑 ${cafe.seating_capacity} seats</span>
        <span>${wifiLabel(cafe)}</span>
      </div>
    </a>`;
}
