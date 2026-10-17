import { todo } from '../components/ui.js';

export function render(el, { id }) {
  el.innerHTML = `
    <a href="#/" class="mb-3 inline-block text-sm text-amber-800">← Back to search</a>
    <h1 class="mb-4 text-2xl font-bold">Cafe #${Number(id)}</h1>
    <div class="space-y-4">
      ${todo('Cafe info from api.getCafe(id): name, address, price, seats, wifi, average + attribute ratings.')}
      ${todo('Busyness: current level + buttons 1-5 that call api.reportBusyness(id, level).')}
      ${todo('"Check in here" button (api.checkIn) / "Check out" (api.checkOut). Only if share_location is on.')}
      ${todo('Reviews list (api.listReviews) + link to #/cafes/' + Number(id) + '/review.')}
    </div>`;
}
