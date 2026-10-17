import 'leaflet/dist/leaflet.css';
import './style.css';

import { renderNavbar } from './components/navbar.js';
import { renderSearchBar } from './components/searchBar.js';
import { renderMap } from './components/map.js';

renderNavbar(document.getElementById('navbar'));
renderSearchBar(document.getElementById('search'));
renderMap(document.getElementById('map'));
