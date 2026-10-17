import { importLibrary, setOptions } from '@googlemaps/js-api-loader';

// King's College London, Strand campus: the default view (keep in sync with SEARCH_CENTER in backend/places.py).
const KCL_STRAND = { lat: 51.5115, lng: -0.1160 };

function showError(el, message) {
  el.innerHTML = `<p class="p-6 text-center text-sm text-red-700">${message}</p>`;
}

export async function renderMap(el) {
  const apiKey = import.meta.env.MAP_KEY;
  if (!apiKey) {
    showError(el, 'Map unavailable: add MAP_KEY to backend/.env, then restart npm run dev.');
    return;
  }

  try {
    // Load the Google Maps script once, with our key.
    setOptions({ key: apiKey, v: 'weekly' });
    const { Map } = await importLibrary('maps');
    const { ControlPosition } = await importLibrary('core');

    const map = new Map(el, {
      center: KCL_STRAND,
      zoom: 15,
      // Pins (AdvancedMarkerElement) need a map ID, and the map ID decides the map's style
      // (e.g. hiding shops and museums). Styles are set in Google Cloud Console, not in code.
      // MAP_ID comes from backend/.env; DEMO_MAP_ID is Google's unstyled test ID.
      mapId: import.meta.env.MAP_ID || 'DEMO_MAP_ID',
      // Keep the map clean: only zoom buttons, placed away from the search bar.
      disableDefaultUI: true,
      zoomControl: true,
      zoomControlOptions: { position: ControlPosition.RIGHT_BOTTOM },
    });

    return map;
  } catch (err) {
    console.error(err);
    showError(el, 'The map failed to load. Open the browser console (F12) for details.');
  }
}
