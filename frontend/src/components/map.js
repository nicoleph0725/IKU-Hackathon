import L from 'leaflet';

const LONDON = [51.5074, -0.1278];

export function renderMap(el) {
  const map = L.map(el, { zoomControl: false }).setView(LONDON, 13);
  L.control.zoom({ position: 'bottomright' }).addTo(map); // keep zoom buttons clear of the search bar

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map);

  return map;
}
