export function renderNavbar(el) {
  el.innerHTML = `
    <nav class="flex items-center justify-between bg-amber-900 px-4 py-3 shadow">
      <a href="/" class="text-lg font-bold text-white">☕ StudySpot</a>
      <div class="flex items-center gap-2">
        <button id="sign-in" class="rounded-lg px-3 py-2 text-sm font-medium text-amber-50 hover:bg-amber-800">
          Sign in
        </button>
        <button id="sign-up" class="rounded-lg bg-amber-50 px-3 py-2 text-sm font-medium text-amber-900 hover:bg-white">
          Sign up
        </button>
      </div>
    </nav>`;

  // TODO: open the sign in / sign up forms.
}
