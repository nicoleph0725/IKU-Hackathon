import { api } from '../api.js';
import { navigate } from '../router.js';
import { cafeCard } from '../components/cafeCard.js';
import { getSavedLocation, requestBrowserLocation } from '../components/location.js';
import { addCafeMarkers, addUserMarker, createMap } from '../components/map.js';
import { toast, toastError } from '../components/toast.js';
import { emptyState, esc } from '../components/ui.js';

const PER_PAGE = 20;

export function render(el) {
  let location = getSavedLocation();
  let cafes = [];
  let page = 1;
  let totalPages = 0;
  let requestId = 0; // ignore out-of-order responses

  el.innerHTML = `
    <div class="mb-4 flex flex-wrap items-end justify-between gap-2">
      <div>
        <h1 class="text-2xl font-bold">Find a study cafe</h1>
        <p class="text-sm text-stone-500">Near <span id="loc-label">${esc(location.label)}</span></p>
      </div>
      <button id="locate" class="btn-secondary">📍 Use my location</button>
    </div>

    <details class="card mb-4" open>
      <summary class="cursor-pointer select-none font-medium">Filters</summary>
      <form id="filters" class="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-7">
        <div class="col-span-2 md:col-span-4 lg:col-span-1">
          <label class="label" for="q">Search</label>
          <input class="input" id="q" name="q" placeholder="Name or area" />
        </div>
        <div>
          <label class="label" for="max_distance_km">Distance</label>
          <select class="input" id="max_distance_km" name="max_distance_km">
            <option value="">Any</option><option value="1">≤ 1 km</option><option value="2">≤ 2 km</option>
            <option value="5" selected>≤ 5 km</option><option value="10">≤ 10 km</option>
          </select>
        </div>
        <div>
          <label class="label" for="max_price">Price</label>
          <select class="input" id="max_price" name="max_price">
            <option value="">Any</option><option value="1">£</option><option value="2">≤ ££</option><option value="3">≤ £££</option>
          </select>
        </div>
        <div>
          <label class="label" for="min_wifi">Wifi</label>
          <select class="input" id="min_wifi" name="min_wifi">
            <option value="">Any</option><option value="1">Has wifi</option><option value="3">Good (3+)</option><option value="5">Excellent</option>
          </select>
        </div>
        <div>
          <label class="label" for="min_seats">Min seats</label>
          <select class="input" id="min_seats" name="min_seats">
            <option value="">Any</option><option value="20">20+</option><option value="40">40+</option><option value="80">80+</option>
          </select>
        </div>
        <div>
          <label class="label" for="max_busyness">Busyness</label>
          <select class="input" id="max_busyness" name="max_busyness">
            <option value="">Any</option><option value="2">Quiet or less</option><option value="3">Moderate or less</option><option value="4">Not packed</option>
          </select>
        </div>
        <div>
          <label class="label" for="sort">Sort by</label>
          <select class="input" id="sort" name="sort">
            <option value="distance">Distance</option><option value="rating">Rating</option>
            <option value="busyness">Least busy</option><option value="name">Name</option>
          </select>
        </div>
      </form>
    </details>

    <div class="mb-3 flex gap-2 md:hidden" role="tablist">
      <button data-tab="list" class="btn-primary flex-1">List</button>
      <button data-tab="map" class="btn-secondary flex-1">Map</button>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <section id="list-pane" class="md:block">
        <p id="result-count" class="mb-2 text-sm text-stone-500"></p>
        <div id="results" class="space-y-3"></div>
        <button id="more" class="btn-secondary mt-3 hidden w-full">Load more</button>
      </section>
      <section id="map-pane" class="hidden md:block">
        <div id="map" class="map md:sticky md:top-20"></div>
        <p class="mt-2 text-xs text-stone-500">Marker colour = current busyness (green quiet → red packed, grey unknown).</p>
      </section>
    </div>`;

  const form = el.querySelector('#filters');
  const results = el.querySelector('#results');
  const moreBtn = el.querySelector('#more');

  const map = createMap(el.querySelector('#map'), location);
  let userMarker = addUserMarker(map, location);
  let markers = null;

  function filters() {
    const data = Object.fromEntries(new FormData(form));
    return { ...data, lat: location.lat, lng: location.lng, page, per_page: PER_PAGE };
  }

  async function load({ append = false } = {}) {
    const id = ++requestId;
    if (!append) page = 1;
    try {
      const res = await api.searchCafes(filters());
      if (id !== requestId) return;
      cafes = append ? [...cafes, ...res.items] : res.items;
      totalPages = res.pages;
      draw(res.total);
    } catch (err) {
      toastError(err);
    }
  }

  function draw(total) {
    el.querySelector('#result-count').textContent = `${total} cafe${total === 1 ? '' : 's'} found`;
    results.innerHTML = cafes.length
      ? cafes.map(cafeCard).join('')
      : emptyState('No cafes match these filters. Try widening the distance or removing a filter.');
    moreBtn.classList.toggle('hidden', page >= totalPages);

    markers?.remove();
    markers = addCafeMarkers(map, cafes, { onClick: (cafe) => navigate(`/cafes/${cafe.id}`) });
  }

  // Debounce so typing in the search box doesn't fire a request per keystroke.
  let timer;
  form.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => load(), 250);
  });
  form.addEventListener('submit', (e) => e.preventDefault());

  moreBtn.addEventListener('click', () => {
    page += 1;
    load({ append: true });
  });

  el.querySelector('#locate').addEventListener('click', async () => {
    try {
      location = await requestBrowserLocation();
      toast('Using your location', 'success');
    } catch (err) {
      toast(err.message, 'error');
      return;
    }
    el.querySelector('#loc-label').textContent = location.label;
    map.setView([location.lat, location.lng], 14);
    userMarker.remove();
    userMarker = addUserMarker(map, location);
    load();
  });

  // Mobile list/map tabs
  el.querySelectorAll('[data-tab]').forEach((btn) =>
    btn.addEventListener('click', () => {
      const showMap = btn.dataset.tab === 'map';
      el.querySelector('#map-pane').classList.toggle('hidden', !showMap);
      el.querySelector('#list-pane').classList.toggle('hidden', showMap);
      el.querySelectorAll('[data-tab]').forEach((b) => {
        b.className = `${b === btn ? 'btn-primary' : 'btn-secondary'} flex-1`;
      });
      if (showMap) setTimeout(() => map.invalidateSize(), 0); // Leaflet needs a resize after being shown
    }),
  );

  load();
  // TODO: persist filters in the URL (#/?max_price=2...) so searches are shareable.

  return () => map.remove(); // cleanup when navigating away
}
