// Leaflet + OpenStreetMap setup.
import L from 'leaflet';

export const LONDON = { lat: 51.5074, lng: -0.1278 };

export function createMap(el, center = LONDON, zoom = 13) {
  const map = L.map(el).setView([center.lat, center.lng], zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map);
  return map;
}

// TODO: addCafeMarkers(map, cafes) - e.g. L.circleMarker([cafe.lat, cafe.lng]).bindTooltip(cafe.name).addTo(map)
//       (circle markers avoid Leaflet's default marker-image path issues with Vite)
