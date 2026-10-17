import { importLibrary } from '@googlemaps/js-api-loader';

/**
 * Location search with Google Maps-style suggestions (Places Autocomplete).
 * Must be called after the map has loaded, because it uses the same Google Maps script.
 *
 * @param el          container element
 * @param getBias     returns a {lat, lng} to prefer suggestions near (e.g. the map centre)
 * @param onPlace     called with { name, lat, lng } when the student picks a place
 */
export async function renderSearchBar(el, { getBias, onPlace }) {
  el.innerHTML = `
    <form id="search-form" class="surface pointer-events-auto relative mx-auto flex max-w-xl gap-2 rounded-2xl p-2" autocomplete="off">
      <input
        name="q"
        type="search"
        placeholder="Search for a place, e.g. Shoreditch or UCL…"
        role="combobox" aria-expanded="false" aria-controls="search-suggestions" aria-autocomplete="list"
        class="field min-w-0 flex-1 rounded-xl px-3 py-2 text-sm"
      />
      <button type="submit" class="btn-matcha rounded-xl px-4 py-2 text-sm font-semibold">
        Search
      </button>
      <ul id="search-suggestions" role="listbox"
        class="surface absolute inset-x-0 top-full mt-2 hidden overflow-hidden rounded-2xl py-1"></ul>
    </form>`;

  const form = el.querySelector('#search-form');
  const input = form.querySelector('input');
  const list = form.querySelector('#search-suggestions');

  const { AutocompleteSessionToken, AutocompleteSuggestion } = await importLibrary('places');

  // Google bills typing + picking a place as one "session" when they share a token.
  let sessionToken = new AutocompleteSessionToken();
  let suggestions = []; // Google's placePrediction objects currently shown
  let active = -1; // highlighted suggestion (keyboard)
  let latestRequest = 0;
  let debounce;

  function setOpen(open) {
    list.classList.toggle('hidden', !open);
    input.setAttribute('aria-expanded', open);
  }

  function renderSuggestions() {
    // Built with DOM methods so place names can't inject HTML.
    list.replaceChildren(
      ...suggestions.map((prediction, i) => {
        const li = document.createElement('li');
        li.role = 'option';
        li.className = `cursor-pointer px-4 py-2 text-sm ${i === active ? 'bg-matcha-100' : 'hover:bg-matcha-50'}`;
        const main = document.createElement('p');
        main.className = 'font-medium text-matcha-900';
        main.textContent = prediction.mainText?.text ?? prediction.text.text;
        const secondary = document.createElement('p');
        secondary.className = 'text-xs text-stone-500';
        secondary.textContent = prediction.secondaryText?.text ?? '';
        li.append(main, secondary);
        li.addEventListener('mousedown', (e) => e.preventDefault()); // keep focus in the input
        li.addEventListener('click', () => choose(prediction));
        return li;
      }),
    );
    setOpen(suggestions.length > 0);
  }

  async function fetchSuggestions(text) {
    const requestId = ++latestRequest;
    try {
      const { suggestions: found } = await AutocompleteSuggestion.fetchAutocompleteSuggestions({
        input: text,
        sessionToken,
        locationBias: { center: getBias(), radius: 20000 }, // prefer places within ~20 km
        includedRegionCodes: ['gb'],
      });
      if (requestId !== latestRequest) return; // the student has typed more since; ignore this answer
      suggestions = found.map((s) => s.placePrediction).filter(Boolean).slice(0, 5);
      active = -1;
      renderSuggestions();
    } catch (err) {
      console.error('Autocomplete failed:', err);
    }
  }

  async function choose(prediction) {
    setOpen(false);
    input.value = prediction.text.text;
    try {
      const place = prediction.toPlace();
      await place.fetchFields({ fields: ['displayName', 'location'] });
      sessionToken = new AutocompleteSessionToken(); // a pick ends the billing session
      suggestions = [];
      onPlace({ name: place.displayName, lat: place.location.lat(), lng: place.location.lng() });
    } catch (err) {
      console.error('Could not look up that place:', err);
    }
  }

  input.addEventListener('input', () => {
    clearTimeout(debounce);
    const text = input.value.trim();
    if (!text) {
      suggestions = [];
      setOpen(false);
      return;
    }
    // Wait until typing pauses, so we don't ask Google on every keystroke.
    debounce = setTimeout(() => fetchSuggestions(text), 250);
  });

  input.addEventListener('keydown', (e) => {
    if (!suggestions.length) return;
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      const step = e.key === 'ArrowDown' ? 1 : -1;
      active = (active + step + suggestions.length) % suggestions.length;
      renderSuggestions();
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  });

  input.addEventListener('focus', () => setOpen(suggestions.length > 0));
  document.addEventListener('click', (e) => {
    if (!form.contains(e.target)) setOpen(false);
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault(); // stop the page from reloading
    // Enter / Search picks the highlighted suggestion, or the top one.
    if (suggestions.length) choose(suggestions[Math.max(active, 0)]);
  });
}
