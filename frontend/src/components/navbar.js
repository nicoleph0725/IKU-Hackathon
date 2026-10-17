import logo from '../assets/logo.jpg';
import { api, openAuthModal } from './auth.js';

export function renderNavbar(el) {
  el.innerHTML = `
    <nav class="flex items-center justify-between bg-brand px-4 py-3 shadow">
      <a href="/" class="flex items-center gap-2 text-lg font-bold text-cream">
      <img src="${logo}" alt="BeanTogether logo" class="h-8 w-8 object-contain" />
      BeanTogether</a>
      <div id="auth-area" class="flex items-center gap-2"></div>
    </nav>`;

  const area = el.querySelector('#auth-area');

  function showLoggedOut() {
    area.innerHTML = `
      <button id="sign-in" class="rounded-lg px-3 py-2 text-sm font-medium text-cream hover:bg-brand-dark">Sign in</button>
      <button id="sign-up" class="rounded-lg bg-brand px-3 py-2 text-sm font-medium text-cream hover:bg-brand-dark">Sign up</button>`;
    area.querySelector('#sign-in').onclick = () => openAuthModal('login', showLoggedIn);
    area.querySelector('#sign-up').onclick = () => openAuthModal('signup', showLoggedIn);
  }

  function showLoggedIn(user) {
    area.innerHTML = `
      <span id="user-name" class="text-sm text-amber-50"></span>
      <button id="log-out" class="rounded-lg px-3 py-2 text-sm font-medium text-amber-50 hover:bg-amber-800">Log out</button>`;
    area.querySelector('#user-name').textContent = user.username;
    area.querySelector('#log-out').onclick = async () => {
      await api.logout();
      showLoggedOut();
    };
  }

  showLoggedOut();
  api.me().then(({ user }) => user && showLoggedIn(user)).catch(() => {});
}
