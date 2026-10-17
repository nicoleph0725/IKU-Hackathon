// Collapsible "Preferences" panel: the student picks what they want, we ask the backend
// (Google Places + Gemini) for the best matches, and show them as a ranked list.

// Each preference is a row of buttons. The first option is the default ("any").
const OPTIONS = [
  { name: 'space', label: 'Space', choices: [['any', 'Any'], ['some', 'Some room'], ['lots', 'Lots']] },
  { name: 'budget', label: 'Budget (max)', choices: [['any', 'Any'], ['1', '£'], ['2', '££'], ['3', '£££']] },
  { name: 'quietness', label: 'Quietness', choices: [['any', 'Any'], ['quiet', 'Quiet'], ['very_quiet', 'Very quiet']] },
  { name: 'wifi', label: 'Wifi', choices: [['any', 'Any'], ['needed', 'Needed'], ['fast', 'Fast']] },
];

/**
 * @param el        container element
 * @param onResults called with the list of cafes to show on the map
 * @param onSelect  called with a cafe when the student clicks it in the list
 * @param onReset   called when the student clears their preferences
 */
export function renderPreferencesSidebar(el, { onResults, onSelect, onReset }) {
  el.innerHTML = `
    <button id="prefs-open" type="button"
      class="rounded-xl bg-white px-4 py-2 text-sm font-medium text-amber-900 shadow-lg hover:bg-amber-50">
      ☰ Preferences
    </button>

    <div id="prefs-panel" class="hidden h-full flex-col rounded-xl bg-white shadow-lg">
      <div class="flex items-center justify-between border-b border-stone-200 px-4 py-3">
        <h2 class="font-semibold">Your preferences</h2>
        <button id="prefs-close" type="button" aria-label="Close preferences"
          class="rounded-lg px-2 py-1 text-stone-500 hover:bg-stone-100">✕</button>
      </div>

      <div class="flex-1 overflow-y-auto px-4 py-3">
        <form id="prefs-form" class="space-y-4">
          ${OPTIONS.map(optionGroup).join('')}

          <label class="flex items-center gap-2 text-sm">
            <input type="checkbox" name="open_now" class="h-4 w-4 accent-amber-800" />
            Open now
          </label>

          <div>
            <label for="prefs-notes" class="mb-1 block text-xs font-medium uppercase tracking-wide text-stone-500">
              Anything else?
            </label>
            <textarea id="prefs-notes" name="notes" maxlength="300" rows="2"
              placeholder="e.g. plug sockets, good matcha, outdoor seating"
              class="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-amber-700/30"></textarea>
          </div>

          <div class="flex gap-2">
            <button type="submit"
              class="flex flex-1 items-center justify-center gap-2 rounded-lg bg-amber-800 px-4 py-2 text-sm font-medium text-white hover:bg-amber-900 disabled:cursor-wait disabled:opacity-70">
              Find cafes
            </button>
            <button type="reset"
              class="rounded-lg border border-stone-300 px-4 py-2 text-sm text-stone-700 hover:bg-stone-100">
              Reset
            </button>
          </div>
        </form>

        <div id="prefs-status" class="mt-4 text-sm text-stone-500"></div>
        <ol id="prefs-results" class="mt-2 space-y-2"></ol>
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
    el.classList.toggle('bottom-3', open); // panel stretches down the screen only while open
  };
  openBtn.addEventListener('click', () => setOpen(true));
  el.querySelector('#prefs-close').addEventListener('click', () => setOpen(false));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    const prefs = { ...data, open_now: data.open_now === 'on' };

    const submit = form.querySelector('[type=submit]');
    const setLoading = (loading) => {
      submit.disabled = loading;
      submit.innerHTML = loading ? `${spinner('border-white/40 border-t-white')} Finding…` : 'Find cafes';
      submit.setAttribute('aria-busy', loading);
    };

    setLoading(true);
    results.innerHTML = '';
    status.innerHTML = `
      <div class="flex items-center gap-2" role="status">
        ${spinner('border-amber-200 border-t-amber-800')}
        <span>Finding the best cafes for you… (this takes a few seconds)</span>
      </div>`;

    try {
      const res = await fetch('/api/cafes/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prefs),
      });
      const cafes = await res.json();
      if (!res.ok) throw new Error(cafes.error ?? 'Something went wrong');

      status.textContent = cafes.length
        ? `${cafes.length} matching cafe${cafes.length === 1 ? '' : 's'}`
        : 'No cafes match. Try relaxing your budget or "open now".';
      results.replaceChildren(...cafes.map((cafe, i) => resultItem(cafe, i + 1, onSelect)));
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

// A small spinning circle. `colors` sets the ring and the moving part, e.g. 'border-white/40 border-t-white'.
function spinner(colors) {
  return `<span class="inline-block h-4 w-4 shrink-0 animate-spin rounded-full border-2 ${colors}" aria-hidden="true"></span>`;
}

// One row of choice buttons (radio inputs styled as buttons).
function optionGroup({ name, label, choices }) {
  return `
    <fieldset>
      <legend class="mb-1 text-xs font-medium uppercase tracking-wide text-stone-500">${label}</legend>
      <div class="flex gap-1">
        ${choices
          .map(
            ([value, text], i) => `
          <label class="flex-1 cursor-pointer">
            <input type="radio" name="${name}" value="${value}" class="peer sr-only" ${i === 0 ? 'checked' : ''} />
            <span class="block rounded-lg border border-stone-300 px-2 py-1.5 text-center text-xs
              peer-checked:border-amber-800 peer-checked:bg-amber-800 peer-checked:text-white
              peer-focus-visible:ring-2 peer-focus-visible:ring-amber-700/40">${text}</span>
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
  button.className = 'w-full rounded-lg border border-stone-200 p-2 text-left hover:border-amber-700';
  button.addEventListener('click', () => onSelect(cafe));

  const title = document.createElement('p');
  title.className = 'flex items-center gap-2 text-sm font-medium';
  const badge = document.createElement('span');
  badge.className = 'flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-800 text-xs text-white';
  badge.textContent = rank;
  const name = document.createElement('span');
  name.textContent = cafe.score != null ? `${cafe.name} · ${cafe.score}% match` : cafe.name;
  title.append(badge, name);
  button.append(title);

  if (cafe.reason) {
    const reason = document.createElement('p');
    reason.className = 'mt-1 text-xs text-stone-600';
    reason.textContent = cafe.reason;
    button.append(reason);
  }
  li.append(button);
  return li;
}
