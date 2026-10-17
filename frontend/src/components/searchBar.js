export function renderSearchBar(el) {
  el.innerHTML = `
    <form id="search-form" class="mx-auto flex max-w-xl gap-2 rounded-xl bg-white p-2 shadow-lg">
      <input
        name="q"
        type="search"
        placeholder="Search for a study cafe…"
        class="min-w-0 flex-1 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-amber-700/30"
      />
      <button type="submit" class="rounded-lg bg-amber-800 px-4 py-2 text-sm font-medium text-white hover:bg-amber-900">
        Search
      </button>
    </form>`;

  el.querySelector('#search-form').addEventListener('submit', (e) => {
    e.preventDefault(); // stop the page from reloading
    // TODO: search for cafes.
  });
}
