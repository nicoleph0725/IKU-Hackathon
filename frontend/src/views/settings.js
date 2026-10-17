import { getUser } from '../auth.js';
import { esc, todo } from '../components/ui.js';

export function render(el) {
  const user = getUser();
  el.innerHTML = `
    <h1 class="mb-4 text-2xl font-bold">Settings</h1>
    <p class="mb-4">Logged in as <strong>${esc(user?.username)}</strong></p>
    ${todo('Toggle "Share my check-ins with friends" -> api.updateSettings({share_location}). Explain it is opt-in and only shows the cafe, never GPS.')}`;
}
