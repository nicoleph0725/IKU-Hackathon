// Create or edit (if one exists) the current user's review of a cafe.
import { api, formatErrorDetails } from '../api.js';
import { getUser } from '../auth.js';
import { navigate } from '../router.js';
import { toast } from '../components/toast.js';
import { esc } from '../components/ui.js';

const FIELDS = [
  ['rating', 'Overall', true],
  ['space_rating', 'Space & seating', false],
  ['quietness_rating', 'Quietness', false],
  ['wifi_rating', 'Wifi', false],
  ['cost_rating', 'Value for money', false],
];

export async function render(el, { id }) {
  const cafeId = Number(id);
  const me = getUser();
  const [{ cafe }, mine] = await Promise.all([api.getCafe(cafeId), api.listReviews(cafeId, { user_id: me.id })]);
  const existing = mine.items[0];

  el.innerHTML = `
    <div class="mx-auto max-w-lg">
      <a href="#/cafes/${cafeId}" class="mb-3 inline-block text-sm text-amber-800">← ${esc(cafe.name)}</a>
      <h1 class="mb-4 text-2xl font-bold">${existing ? 'Edit your review' : 'Write a review'}</h1>
      <form id="review-form" class="card space-y-4">
        ${FIELDS.map(([name, label, required]) => ratingInput(name, label, required, existing?.[name])).join('')}
        <div>
          <label class="label" for="body">Your review</label>
          <textarea class="input min-h-32" id="body" name="body" maxlength="2000"
            placeholder="Plugs? Noise? Good coffee? How long can you stay?">${esc(existing?.body ?? '')}</textarea>
        </div>
        <button class="btn-primary w-full" type="submit">${existing ? 'Save changes' : 'Post review'}</button>
      </form>
    </div>`;

  const form = el.querySelector('#review-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    const payload = { body: data.body };
    for (const [name, , required] of FIELDS) {
      if (data[name]) payload[name] = Number(data[name]);
      else if (!required) payload[name] = null; // clear an optional rating
    }
    if (!payload.rating) return toast('Please give an overall rating', 'error');

    try {
      if (existing) await api.updateReview(existing.id, payload);
      else await api.createReview(cafeId, payload);
      toast('Review saved', 'success');
      navigate(`/cafes/${cafeId}`);
    } catch (err) {
      toast([err.message, formatErrorDetails(err.details)].filter(Boolean).join('\n'), 'error');
    }
  });
}

/** 1–5 radio group styled as tappable buttons (mobile friendly). */
function ratingInput(name, label, required, value) {
  return `
    <fieldset>
      <legend class="label">${label}${required ? ' *' : ' <span class="normal-case text-stone-400">(optional)</span>'}</legend>
      <div class="grid grid-cols-5 gap-1">
        ${[1, 2, 3, 4, 5]
          .map(
            (n) => `
          <label class="cursor-pointer">
            <input type="radio" name="${name}" value="${n}" class="peer sr-only" ${value === n ? 'checked' : ''} ${required ? 'required' : ''} />
            <span class="block rounded-lg border border-stone-300 py-2 text-center text-sm peer-checked:border-amber-800 peer-checked:bg-amber-800 peer-checked:text-white">${n}★</span>
          </label>`,
          )
          .join('')}
      </div>
    </fieldset>`;
}
