import { importLibrary } from '@googlemaps/js-api-loader';

/**
 * Manages the cafe pins on the map.
 *   layer.show(cafes, { ranked })  replace the pins (ranked = numbered pins, in list order)
 *   layer.focus(cafe)              pan to a cafe and open its card
 */
export async function createCafeLayer(map) {
  const { AdvancedMarkerElement } = await importLibrary('marker');
  const { InfoWindow } = await importLibrary('maps');
  const { LatLngBounds } = await importLibrary('core');

  const infoWindow = new InfoWindow(); // one shared popup, moved to whichever pin is clicked
  let markers = new Map(); // cafe id -> { marker, cafe }

  function openCard(cafe, marker) {
    infoWindow.setContent(cafeCard(cafe));
    infoWindow.open({ map, anchor: marker });
  }

  function show(cafes, { ranked = false } = {}) {
    infoWindow.close();
    for (const { marker } of markers.values()) marker.map = null; // remove old pins
    markers = new Map();

    cafes.forEach((cafe, i) => {
      const marker = new AdvancedMarkerElement({
        map,
        position: { lat: cafe.lat, lng: cafe.lng },
        title: cafe.name,
        gmpClickable: true,
        // Ranked results get a numbered pin matching the list; otherwise Google's default pin.
        content: ranked ? numberedPin(i + 1) : undefined,
        zIndex: ranked ? cafes.length - i : undefined, // best match drawn on top
      });
      marker.addEventListener('gmp-click', () => openCard(cafe, marker));
      markers.set(cafe.id, { marker, cafe });
    });

    if (ranked && cafes.length) {
      const bounds = new LatLngBounds();
      cafes.forEach((c) => bounds.extend({ lat: c.lat, lng: c.lng }));
      // Leave room for the search bar (top) and the preferences sidebar (left, on wider screens).
      const sidebarOpen = window.innerWidth >= 640;
      map.fitBounds(bounds, { top: 100, left: sidebarOpen ? 360 : 40, right: 40, bottom: 40 });
    }
  }

  function focus(cafe) {
    const entry = markers.get(cafe.id);
    if (!entry) return;
    map.panTo({ lat: cafe.lat, lng: cafe.lng });
    openCard(entry.cafe, entry.marker);
  }

  return { show, focus };
}

/** All cafes near the search area, for the default view. */
export async function fetchAllCafes() {
  const res = await fetch('/api/places/cafes');
  const cafes = await res.json();
  if (!res.ok) throw new Error(cafes.error ?? 'Could not load cafes');
  return cafes;
}

function numberedPin(n) {
  const pin = document.createElement('div');
  pin.className =
    'flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-amber-800 text-sm font-bold text-white shadow-md';
  pin.textContent = n;
  return pin;
}

// Built with DOM methods (not an HTML string) so cafe names can't inject HTML.
function cafeCard(cafe) {
  const card = document.createElement('div');
  card.className = 'w-56 text-sm';

  if (cafe.photo_name) {
    const img = document.createElement('img');
    img.src = `/api/places/photo?name=${encodeURIComponent(cafe.photo_name)}`;
    img.alt = cafe.name;
    img.className = 'mb-2 h-32 w-full rounded-md object-cover';
    card.append(img);
    if (cafe.photo_author) card.append(line(`Photo: ${cafe.photo_author}`, 'mb-1 text-[10px] text-stone-400'));
  }

  card.append(line(cafe.name, 'font-semibold text-stone-900'));
  card.append(line(cafe.address, 'text-xs text-stone-500'));

  const rating = cafe.rating ? `★ ${cafe.rating} (${cafe.rating_count})` : 'No rating yet';
  const price = cafe.price_level ? '£'.repeat(cafe.price_level) : '';
  const status = cafe.open_now === true ? 'Open now' : cafe.open_now === false ? 'Closed' : '';
  card.append(line([rating, price, status].filter(Boolean).join(' · '), 'mt-1 text-xs text-stone-700'));

  if (cafe.score != null) {
    card.append(line(`${cafe.score}% match: ${cafe.reason}`, 'mt-2 rounded-md bg-amber-50 p-2 text-xs text-amber-900'));
  }
  // TODO: busyness. Google's API doesn't provide it, so it will come from our own data.

  return card;
}

function line(text, className) {
  const p = document.createElement('p');
  p.className = className;
  p.textContent = text;
  return p;
}
