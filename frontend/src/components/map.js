// Leaflet + OpenStreetMap helpers.
import L from 'leaflet';
import { BUSY_COLORS, esc } from './ui.js';

const TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

export function createMap(el, center, zoom = 13) {
  const map = L.map(el, { scrollWheelZoom: false }).setView([center.lat, center.lng], zoom);
  L.tileLayer(TILE_URL, { attribution: ATTRIBUTION, maxZoom: 19 }).addTo(map);
  return map;
}

/** Circle markers (no image assets needed) coloured by busyness. Returns the layer group. */
export function addCafeMarkers(map, cafes, { onClick } = {}) {
  const layer = L.featureGroup().addTo(map);
  for (const cafe of cafes) {
    const level = cafe.busyness?.level != null ? Math.round(cafe.busyness.level) : null;
    const marker = L.circleMarker([cafe.lat, cafe.lng], {
      radius: 9,
      weight: 2,
      color: '#fff',
      fillColor: level ? BUSY_COLORS[level] : '#78716c',
      fillOpacity: 0.95,
    }).addTo(layer);
    marker.bindTooltip(esc(cafe.name));
    if (onClick) marker.on('click', () => onClick(cafe));
  }
  return layer;
}

export function addUserMarker(map, coords) {
  return L.circleMarker([coords.lat, coords.lng], {
    radius: 7,
    color: '#1d4ed8',
    fillColor: '#3b82f6',
    fillOpacity: 1,
  })
    .bindTooltip('You')
    .addTo(map);
}
