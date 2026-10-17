import { todo } from '../components/ui.js';

export function render(el, { id }) {
  el.innerHTML = `
    <a href="#/cafes/${Number(id)}" class="mb-3 inline-block text-sm text-amber-800">← Back to cafe</a>
    <h1 class="mb-4 text-2xl font-bold">Write a review</h1>
    ${todo('Form: overall rating 1-5 (required), space / quietness / wifi / cost ratings 1-5 (optional), text. Submit with api.createReview(cafeId, data), then navigate back.')}`;
}
