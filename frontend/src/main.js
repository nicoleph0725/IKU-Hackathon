import './style.css';

import { renderNavbar } from './components/navbar.js';
import { renderSearchBar } from './components/searchBar.js';
import { renderMap } from './components/map.js';
import { createCafeLayer, fetchAllCafes } from './components/cafeMarkers.js';
import { renderPreferencesSidebar } from './components/preferencesSidebar.js';

renderNavbar(document.getElementById('navbar'));

const map = await renderMap(document.getElementById('map'));
if (map) {
  const cafes = await createCafeLayer(map);

  // Where we look for cafes. null = the backend's default (KCL Strand) until the student searches.
  let center = null;

  // Default view: every cafe near the search area.
  let allCafes = [];
  function loadCafes() {
    fetchAllCafes(center)
      .then((list) => {
        allCafes = list;
        cafes.show(allCafes);
      })
      .catch((err) => console.error('Could not load cafes:', err));
  }
  loadCafes();

  renderSearchBar(document.getElementById('search'), {
    getBias: () => map.getCenter().toJSON(),
    onPlace: ({ lat, lng }) => {
      center = { lat, lng };
      map.panTo(center);
      map.setZoom(15);
      loadCafes();
    },
  });

  renderPreferencesSidebar(document.getElementById('prefs'), {
    onResults: (ranked) => cafes.show(ranked, { ranked: true }),
    onSelect: (cafe) => cafes.focus(cafe),
    onReset: () => cafes.show(allCafes),
    getCenter: () => center,
  });
}
