import './style.css';

import { renderNavbar } from './components/navbar.js';
import { renderSearchBar } from './components/searchBar.js';
import { renderMap } from './components/map.js';
import { createCafeLayer, fetchAllCafes } from './components/cafeMarkers.js';
import { renderPreferencesSidebar } from './components/preferencesSidebar.js';

renderNavbar(document.getElementById('navbar'));
renderSearchBar(document.getElementById('search'));

const map = await renderMap(document.getElementById('map'));
if (map) {
  const cafes = await createCafeLayer(map);

  // Default view: every cafe near the search area.
  let allCafes = [];
  fetchAllCafes()
    .then((list) => {
      allCafes = list;
      cafes.show(allCafes);
    })
    .catch((err) => console.error('Could not load cafes:', err));

  renderPreferencesSidebar(document.getElementById('prefs'), {
    onResults: (ranked) => cafes.show(ranked, { ranked: true }),
    onSelect: (cafe) => cafes.focus(cafe),
    onReset: () => cafes.show(allCafes),
  });
}
