import { api } from '../api.js';
import { getUser, isLoggedIn, setUser } from '../auth.js';
import { navigate } from '../router.js';
import { getSavedLocation } from '../components/location.js';
import { addCafeMarkers, createMap } from '../components/map.js';
import { toast, toastError } from '../components/toast.js';
import {
  BUSY_COLORS,
  busynessBadge,
  emptyState,
  esc,
  priceLabel,
  stars,
  timeAgo,
  timeUntil,
  wifiLabel,
} from '../components/ui.js';

const DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
const LEVELS = [
  [1, 'Empty'],
  [2, 'Quiet'],
  [3, 'Moderate'],
  [4, 'Busy'],
  [5, 'Packed'],
];

export async function render(el, { id }) {
  const cafeId = Number(id);
  const { lat, lng } = getSavedLocation();
  let cafe;
  try {
    ({ cafe } = await api.getCafe(cafeId, { lat, lng }));
  } catch (err) {
    el.innerHTML = emptyState(err.status === 404 ? 'Cafe not found.' : err.message);
    return;
  }

  el.innerHTML = `
    <a href="#/" class="mb-3 inline-block text-sm text-amber-800">← Back to search</a>
    <div class="grid gap-4 md:grid-cols-3">
      <div class="space-y-4 md:col-span-2">
        <section class="card">
          <h1 class="text-2xl font-bold">${esc(cafe.name)}</h1>
          <p class="text-sm text-stone-500">${esc(cafe.address)}</p>
          <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
            ${stars(cafe.avg_rating, { size: 'text-base' })}
            <span class="text-stone-500">${cafe.avg_rating ?? '–'} · ${cafe.review_count} review${cafe.review_count === 1 ? '' : 's'}</span>
            ${busynessBadge(cafe.busyness)}
          </div>
          <div class="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm text-stone-700">
            <span>${priceLabel(cafe.price_level)}</span>
            <span>🪑 ${cafe.seating_capacity} seats</span>
            <span>${wifiLabel(cafe)}</span>
            ${cafe.distance_km != null ? `<span>📍 ${cafe.distance_km.toFixed(1)} km away</span>` : ''}
          </div>
        </section>

        <section class="card" id="ratings">
          <h2 class="mb-3 font-semibold">What students say</h2>
          ${attributeBars(cafe.attribute_ratings)}
        </section>

        <section class="card">
          <div class="mb-3 flex items-center justify-between gap-2">
            <h2 class="font-semibold">Reviews</h2>
            <div id="review-action"></div>
          </div>
          <div id="reviews" class="divide-y divide-stone-100"></div>
          <button id="more-reviews" class="btn-secondary mt-3 hidden w-full">More reviews</button>
        </section>
      </div>

      <aside class="space-y-4">
        <section class="card" id="checkin"></section>
        <section class="card">
          <h2 class="mb-1 font-semibold">How busy is it?</h2>
          <p class="mb-3 text-xs text-stone-500">Based on ${cafe.busyness.report_count} report(s) in the last ${cafe.busyness.window_minutes} min.</p>
          <div id="busyness-now" class="mb-3">${busynessBadge(cafe.busyness)}</div>
          ${historyChart(cafe.busyness_history)}
          <p class="mb-2 mt-4 text-sm font-medium">Here now? Tell others:</p>
          <div class="grid grid-cols-5 gap-1" id="report-buttons">
            ${LEVELS.map(([lvl, label]) => `<button data-level="${lvl}" class="btn-secondary px-1 text-xs" title="${label}">${label}</button>`).join('')}
          </div>
        </section>
        ${cafe.friends_here?.length ? `
          <section class="card">
            <h2 class="mb-2 font-semibold">Friends here now</h2>
            <ul class="space-y-1 text-sm">${cafe.friends_here.map((f) => `<li>👋 ${esc(f.username)}</li>`).join('')}</ul>
          </section>` : ''}
        <section class="card">
          <h2 class="mb-2 font-semibold">Opening hours</h2>
          ${openingHours(cafe.opening_hours)}
        </section>
        <div id="detail-map" class="map" style="height:14rem"></div>
      </aside>
    </div>`;

  const map = createMap(el.querySelector('#detail-map'), cafe, 15);
  addCafeMarkers(map, [cafe]);

  // --- Busyness reports ---------------------------------------------------------
  el.querySelector('#report-buttons').addEventListener('click', async (e) => {
    const level = e.target.closest('[data-level]')?.dataset.level;
    if (!level) return;
    if (!isLoggedIn()) return navigate(`/login?next=/cafes/${cafeId}`);
    try {
      const { busyness } = await api.reportBusyness(cafeId, Number(level));
      el.querySelector('#busyness-now').innerHTML = busynessBadge(busyness);
      toast('Thanks for reporting!', 'success');
    } catch (err) {
      toastError(err);
    }
  });

  await Promise.all([renderCheckin(el.querySelector('#checkin'), cafe), renderReviews(el, cafe)]);
  return () => map.remove();
}

// --- Check-in card --------------------------------------------------------------
async function renderCheckin(box, cafe) {
  if (!isLoggedIn()) {
    box.innerHTML = `<h2 class="mb-2 font-semibold">Studying here?</h2>
      <a class="btn-primary w-full" href="#/login?next=/cafes/${cafe.id}">Log in to check in</a>`;
    return;
  }
  const [{ user }, { checkin }] = await Promise.all([api.me(), api.myCheckin()]);
  setUser(user);

  if (!user.share_location) {
    box.innerHTML = `<h2 class="mb-2 font-semibold">Studying here?</h2>
      <p class="mb-3 text-sm text-stone-600">Check-ins are off. Turn on sharing to let friends see which cafe you're at (never your exact location).</p>
      <a class="btn-secondary w-full" href="#/settings">Open privacy settings</a>`;
    return;
  }

  if (checkin && checkin.cafe.id === cafe.id) {
    box.innerHTML = `<h2 class="mb-2 font-semibold">✅ You're checked in</h2>
      <p class="mb-3 text-sm text-stone-600">Friends can see you're here. Expires in ${timeUntil(checkin.expires_at)}.</p>
      <button id="checkout" class="btn-danger w-full">Check out</button>`;
    box.querySelector('#checkout').addEventListener('click', async () => {
      try {
        await api.checkOut();
        toast('Checked out', 'success');
        renderCheckin(box, cafe);
      } catch (err) {
        toastError(err);
      }
    });
    return;
  }

  box.innerHTML = `<h2 class="mb-2 font-semibold">Studying here?</h2>
    ${checkin ? `<p class="mb-2 text-xs text-stone-500">You're currently checked in at ${esc(checkin.cafe.name)}; checking in here will end that.</p>` : ''}
    <label class="label" for="duration">For how long?</label>
    <select id="duration" class="input mb-3">
      <option value="60">1 hour</option><option value="120">2 hours</option>
      <option value="180" selected>3 hours</option><option value="240">4 hours</option>
    </select>
    <button id="checkin-btn" class="btn-primary w-full">Check in here</button>
    <p class="mt-2 text-xs text-stone-500">Only your accepted friends will see this.</p>`;
  box.querySelector('#checkin-btn').addEventListener('click', async () => {
    try {
      await api.checkIn(cafe.id, Number(box.querySelector('#duration').value));
      toast(`Checked in at ${cafe.name}`, 'success');
      renderCheckin(box, cafe);
    } catch (err) {
      toastError(err);
    }
  });
}

// --- Reviews --------------------------------------------------------------------
async function renderReviews(el, cafe) {
  const me = getUser();
  const list = el.querySelector('#reviews');
  const moreBtn = el.querySelector('#more-reviews');
  let page = 1;

  if (me) {
    const mine = await api.listReviews(cafe.id, { user_id: me.id });
    el.querySelector('#review-action').innerHTML = mine.total
      ? `<a class="btn-secondary" href="#/cafes/${cafe.id}/review">Edit my review</a>`
      : `<a class="btn-primary" href="#/cafes/${cafe.id}/review">Write a review</a>`;
  } else {
    el.querySelector('#review-action').innerHTML = `<a class="btn-secondary" href="#/login?next=/cafes/${cafe.id}/review">Log in to review</a>`;
  }

  async function loadPage() {
    const res = await api.listReviews(cafe.id, { page, per_page: 10 });
    if (page === 1 && !res.items.length) list.innerHTML = emptyState('No reviews yet. Be the first!');
    else list.insertAdjacentHTML('beforeend', res.items.map((r) => reviewItem(r, me)).join(''));
    moreBtn.classList.toggle('hidden', page >= res.pages);
  }

  moreBtn.addEventListener('click', () => {
    page += 1;
    loadPage().catch(toastError);
  });

  list.addEventListener('click', async (e) => {
    const id = e.target.closest('[data-delete-review]')?.dataset.deleteReview;
    if (!id || !confirm('Delete your review?')) return;
    try {
      await api.deleteReview(id);
      toast('Review deleted', 'success');
      // Re-render the whole view so averages refresh.
      window.dispatchEvent(new HashChangeEvent('hashchange'));
    } catch (err) {
      toastError(err);
    }
  });

  await loadPage();
}

function reviewItem(r, me) {
  const attrs = [
    ['Space', r.space_rating],
    ['Quiet', r.quietness_rating],
    ['Wifi', r.wifi_rating],
    ['Value', r.cost_rating],
  ].filter(([, v]) => v != null);
  return `
    <article class="py-3">
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-2">
          <span class="font-medium">${esc(r.user?.username)}</span>${stars(r.rating)}
        </div>
        <span class="text-xs text-stone-400">${timeAgo(r.created_at)}${r.updated_at ? ' (edited)' : ''}</span>
      </div>
      ${attrs.length ? `<p class="mt-1 text-xs text-stone-500">${attrs.map(([k, v]) => `${k} ${v}/5`).join(' · ')}</p>` : ''}
      ${r.body ? `<p class="mt-1 whitespace-pre-line text-sm text-stone-700">${esc(r.body)}</p>` : ''}
      ${me && r.user?.id === me.id ? `<button data-delete-review="${r.id}" class="mt-1 text-xs text-red-700 underline">Delete</button>` : ''}
    </article>`;
}

// --- Small render helpers -----------------------------------------------------
function attributeBars(ratings) {
  const rows = [
    ['Space', ratings.space],
    ['Quietness', ratings.quietness],
    ['Wifi', ratings.wifi],
    ['Value for money', ratings.cost],
  ];
  return `<div class="space-y-2">${rows
    .map(
      ([label, v]) => `
      <div class="flex items-center gap-3 text-sm">
        <span class="w-32 shrink-0 text-stone-600">${label}</span>
        <div class="h-2 flex-1 overflow-hidden rounded-full bg-stone-100">
          <div class="h-full rounded-full bg-amber-600" style="width:${v ? (v / 5) * 100 : 0}%"></div>
        </div>
        <span class="w-8 text-right text-stone-500">${v ?? '–'}</span>
      </div>`,
    )
    .join('')}</div>`;
}

function historyChart(history) {
  if (!history?.length) return `<p class="text-xs text-stone-400">No reports in the last 12 hours.</p>`;
  return `
    <p class="mb-1 text-xs text-stone-500">Last 12 hours (hourly average)</p>
    <div class="flex h-16 items-end gap-1" role="img" aria-label="Busyness over the last 12 hours">
      ${history
        .map((h) => {
          const hour = new Date(h.hour).getHours();
          return `<div class="flex-1 rounded-t" title="${hour}:00 – ${h.level}/5 (${h.report_count} reports)"
                    style="height:${(h.level / 5) * 100}%;background:${BUSY_COLORS[Math.round(h.level)]}"></div>`;
        })
        .join('')}
    </div>`;
}

function openingHours(hours) {
  if (!hours) return `<p class="text-sm text-stone-400">Not available</p>`;
  const today = DAYS[(new Date().getDay() + 6) % 7];
  return `<table class="w-full text-sm">${DAYS.map((d) => {
    const slots = hours[d] ?? [];
    const text = slots.length ? slots.map(([a, b]) => `${a}–${b}`).join(', ') : 'Closed';
    return `<tr class="${d === today ? 'font-semibold' : 'text-stone-600'}">
      <td class="py-0.5 capitalize">${d}</td><td class="text-right">${esc(text)}</td></tr>`;
  }).join('')}</table>`;
}
