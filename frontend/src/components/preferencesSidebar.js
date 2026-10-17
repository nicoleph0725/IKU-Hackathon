// Collapsible "Preferences" panel: the student picks what they want, we ask the backend
// (Google Places + Gemini) for the best matches, and show them as a ranked list.

// Each preference is a row of buttons. The first option is the default ("any").
const OPTIONS = [
  { name: 'space', label: 'Space', choices: [['any', 'Any'], ['some', 'Some room'], ['lots', 'Spacious']] },
  { name: 'budget', label: 'Max budget', choices: [['any', 'Any'], ['1', '£'], ['2', '££'], ['3', '£££']] },
  { name: 'quietness', label: 'Atmosphere', choices: [['any', 'Any'], ['quiet', 'Quiet'], ['very_quiet', 'Silent']] },
  { name: 'wifi', label: 'Wi-Fi', choices: [['any', 'Any'], ['needed', 'Available'], ['fast', 'Fast']] },
];

/**
 * @param el        container element
 * @param onResults called with the list of cafes to show on the map
 * @param onSelect  called with a cafe when the student clicks it in the list
 * @param onReset   called when the student clears their preferences
 * @param getCenter returns the {lat, lng} to search around, or null for the default (KCL Strand)
 */
export function renderPreferencesSidebar(el, { onResults, onSelect, onReset, getCenter }) {
  el.innerHTML = `
    <button id="prefs-open" type="button"
      class="surface pointer-events-auto inline-flex cursor-pointer items-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-semibold text-brand transition hover:-translate-y-0.5 hover:border-matcha-300">
      <svg class="h-4 w-4 text-matcha-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <line x1="4" x2="4" y1="21" y2="14"></line>
        <line x1="4" x2="4" y1="10" y2="3"></line>
        <line x1="12" x2="12" y1="21" y2="12"></line>
        <line x1="12" x2="12" y1="8" y2="3"></line>
        <line x1="20" x2="20" y1="21" y2="16"></line>
        <line x1="20" x2="20" y1="12" y2="3"></line>
        <line x1="2" x2="6" y1="14" y2="14"></line>
        <line x1="10" x2="14" y1="8" y2="8"></line>
        <line x1="18" x2="22" y1="16" y2="16"></line>
      </svg>
      <span>Filters & Preferences</span>
    </button>

    <div id="prefs-panel" class="surface pointer-events-auto hidden flex-col overflow-hidden rounded-3xl">
      <div class="flex shrink-0 items-center justify-between border-b border-stone-200/70 px-5 py-3.5">
        <div class="flex items-center gap-2.5">
          <span class="flex h-7 w-7 items-center justify-center rounded-xl bg-matcha-100 text-matcha-700">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M17 8h1a4 4 0 1 1 0 8h-1"></path>
              <path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z"></path>
              <line x1="6" x2="6" y1="2" y2="4"></line>
              <line x1="10" x2="10" y1="2" y2="4"></line>
              <line x1="14" x2="14" y1="2" y2="4"></line>
            </svg>
          </span>
          <h2 class="text-sm font-bold tracking-tight text-brand">Study Preferences</h2>
        </div>
        <button id="prefs-close" type="button" aria-label="Close preferences"
          class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-full text-stone-400 transition hover:bg-stone-100 hover:text-stone-700">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M18 6 6 18"></path>
            <path d="m6 6 12 12"></path>
          </svg>
        </button>
      </div>

      <div class="max-h-[calc(100dvh-13rem)] overflow-x-hidden overflow-y-auto px-5 py-3.5 md:max-h-[calc(100dvh-10.5rem)]">
        <form id="prefs-form" class="space-y-3">
          ${OPTIONS.map(optionGroup).join('')}

          <label class="flex cursor-pointer items-center justify-between rounded-xl border border-stone-200/80 bg-stone-50/70 px-3.5 py-2 text-xs font-medium text-stone-700 transition hover:border-matcha-300">
            <span>Only show cafes open now</span>
            <input type="checkbox" name="open_now" class="h-4 w-4 rounded accent-matcha-600" />
          </label>

          <div>
            <label for="prefs-notes" class="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-stone-400">
              Anything else?
            </label>
            <textarea id="prefs-notes" name="notes" maxlength="300" rows="2"
              placeholder="e.g. plug sockets, oat flat white, outdoor seating…"
              class="field w-full resize-none rounded-xl px-3 py-2 text-xs leading-relaxed"></textarea>
          </div>

          <div class="flex gap-2 pt-0.5">
            <button type="submit"
              class="btn-matcha flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold disabled:cursor-wait disabled:opacity-65">
              Find cafes
            </button>
            <button type="reset"
              class="btn-soft cursor-pointer rounded-xl px-3.5 py-2 text-xs font-medium">
              Reset
            </button>
          </div>
        </form>

        <div id="prefs-status" class="mt-3 text-xs font-medium text-stone-500 empty:hidden"></div>
        <ol id="prefs-results" class="mt-2 space-y-2 empty:hidden"></ol>
      </div>
    </div>`;

  const openBtn = el.querySelector('#prefs-open');
  const panel = el.querySelector('#prefs-panel');
  const form = el.querySelector('#prefs-form');
  const status = el.querySelector('#prefs-status');
  const results = el.querySelector('#prefs-results');

  const setOpen = (open) => {
    openBtn.classList.toggle('hidden', open);
    panel.classList.toggle('hidden', !open);
    panel.classList.toggle('flex', open);
  };
  openBtn.addEventListener('click', () => setOpen(true));
  el.querySelector('#prefs-close').addEventListener('click', () => setOpen(false));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    const prefs = { ...data, open_now: data.open_now === 'on', ...getCenter() };

    const submit = form.querySelector('[type=submit]');
    const setLoading = (loading) => {
      submit.disabled = loading;
      submit.innerHTML = loading ? `${spinner('border-brand/30 border-t-brand')} Finding…` : 'Find cafes';
      submit.setAttribute('aria-busy', loading);
    };

    setLoading(true);
    results.innerHTML = '';
    status.innerHTML = `
      <div class="flex items-center gap-2 rounded-xl bg-matcha-50 px-3 py-2.5 text-matcha-800" role="status">
        ${spinner('border-matcha-300 border-t-matcha-700')}
        <span>Curating the best study spots…</span>
      </div>`;
    status.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    try {
      const res = await fetch('/api/cafes/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prefs),
      });
      const cafes = await res.json();
      if (!res.ok) throw new Error(cafes.error ?? 'Something went wrong');

      status.textContent = cafes.length
        ? `${cafes.length} recommended spot${cafes.length === 1 ? '' : 's'}`
        : 'No cafes match. Try relaxing your budget or "open now".';
      results.replaceChildren(...cafes.map((cafe, i) => resultItem(cafe, i + 1, onSelect)));
      status.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      onResults(cafes);
    } catch (err) {
      status.textContent = `Sorry, that didn't work: ${err.message}`;
    } finally {
      setLoading(false);
    }
  });

  form.addEventListener('reset', () => {
    results.innerHTML = '';
    status.textContent = '';
    onReset();
  });
}

// A small spinning circle. `colors` sets the ring and the moving part.
function spinner(colors) {
  return `<span class="inline-block h-3.5 w-3.5 shrink-0 animate-spin rounded-full border-2 ${colors}" aria-hidden="true"></span>`;
}

// One row of choice buttons styled as a sleek segmented control.
function optionGroup({ name, label, choices }) {
  return `
    <fieldset>
      <legend class="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-stone-400">${label}</legend>
      <div class="flex gap-1 rounded-xl bg-stone-100/90 p-1">
        ${choices
          .map(
            ([value, text], i) => `
          <label class="flex-1 cursor-pointer">
            <input type="radio" name="${name}" value="${value}" class="peer sr-only" ${i === 0 ? 'checked' : ''} />
            <span class="chip block rounded-lg px-2 py-1.5 text-center text-xs font-medium">${text}</span>
          </label>`,
          )
          .join('')}
      </div>
    </fieldset>`;
}

// Built with DOM methods so cafe names / Gemini text can't inject HTML.
function resultItem(cafe, rank, onSelect) {
  const li = document.createElement('li');
  const button = document.createElement('button');
  button.type = 'button';
  button.className =
    'group w-full cursor-pointer rounded-2xl border border-stone-200/80 bg-white p-3 text-left transition hover:-translate-y-0.5 hover:border-matcha-300 hover:bg-matcha-50/40 hover:shadow-sm';
  button.addEventListener('click', () => onSelect(cafe));

  const header = document.createElement('div');
  header.className = 'flex items-start justify-between gap-2';

  const title = document.createElement('p');
  title.className = 'flex min-w-0 flex-1 items-start gap-2.5 text-sm font-semibold text-stone-800 group-hover:text-brand';

  const badge = document.createElement('span');
  badge.className = 'badge mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold';
  badge.textContent = rank;

  const name = document.createElement('span');
  name.className = 'min-w-0 flex-1 break-words leading-snug';
  name.textContent = cafe.name;

  title.append(badge, name);
  header.append(title);

  if (cafe.score != null) {
    const scorePill = document.createElement('span');
    scorePill.className =
      'shrink-0 rounded-full bg-matcha-100 px-2 py-0.5 text-[11px] font-semibold text-matcha-800';
    scorePill.textContent = `${cafe.score}%`;
    header.append(scorePill);
  }

  button.append(header);

  if (cafe.reason) {
    const reason = document.createElement('p');
    reason.className = 'mt-1.5 pl-7 text-xs leading-relaxed break-words text-stone-500';
    reason.textContent = cafe.reason;
    button.append(reason);
  }
  li.append(button);
  return li;
}
