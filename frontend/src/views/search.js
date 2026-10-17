import { createMap } from '../components/map.js';
import { todo } from '../components/ui.js';

export function render(el) {
  el.innerHTML = `
    <h1 class="mb-4 text-2xl font-bold">Find a study cafe</h1>
    <div class="mb-4">${todo('Filters form: distance, max price, wifi, min seats, busyness, sort. On change call api.searchCafes({...filters, lat, lng}).')}</div>
    <div class="grid gap-4 md:grid-cols-2">
      <div>${todo('Results list: one card per cafe linking to #/cafes/<id>, plus a "Load more" button (pagination).')}</div>
      <div>
        <div id="map" class="map"></div>
        <p class="mt-2 text-xs text-stone-500">TODO: add a marker per cafe (see components/map.js).</p>
      </div>
    </div>`;

  const map = createMap(el.querySelector('#map'));
  // TODO: get the user's location with navigator.geolocation (fall back to London) for distance search.

  return () => map.remove(); // cleanup when leaving the page
}
