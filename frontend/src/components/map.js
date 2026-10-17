import { importLibrary, setOptions } from '@googlemaps/js-api-loader';

const LONDON = { lat: 51.5074, lng: -0.1278 };

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

    return new Map(el, {
      center: LONDON,
      zoom: 13,
      // Keep the map clean: only zoom buttons, placed away from the search bar.
      disableDefaultUI: true,
      zoomControl: true,
      zoomControlOptions: { position: ControlPosition.RIGHT_BOTTOM },
    });
  } catch (err) {
    console.error(err);
    showError(el, 'The map failed to load. Open the browser console (F12) for details.');
  }
}
