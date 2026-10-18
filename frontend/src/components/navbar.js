import logo from '../assets/logo.jpg';
import { api, openAuthModal, spinner } from './auth.js';

export function renderNavbar(el) {
  el.innerHTML = `
    <nav class="flex items-center justify-between bg-brand px-4 py-3 shadow-xs sm:px-6">
      <a href="/" class="flex items-center gap-2.5 text-lg font-bold tracking-tight text-cream">
        <img src="${logo}" alt="BeanTogether logo" class="h-8 w-8 object-contain" />
        <span>BeanTogether</span>
      </a>
      <div id="auth-area" class="flex items-center gap-2"></div>
    </nav>`;

  const area = el.querySelector('#auth-area');

  function showLoggedOut() {
    area.innerHTML = `
      <button id="sign-in" class=" cursor-pointer rounded-xl px-3.5 py-1.5 text-sm font-medium text-cream/90 transition hover:bg-white/10 hover:text-cream">Sign in</button>
      <button id="sign-up" class="cursor-pointer rounded-xl bg-matcha-200 px-3.5 py-1.5 text-sm font-semibold text-brand transition hover:bg-matcha-300">Sign up</button>`;
    area.querySelector('#sign-in').onclick = () => openAuthModal('login', showLoggedIn);
    area.querySelector('#sign-up').onclick = () => openAuthModal('signup', showLoggedIn);
  }

  function showLoggedIn(user) {
    area.innerHTML = `
      <span id="user-name" class="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-cream"></span>
      <button id="log-out" class="cursor-pointer rounded-xl px-3 py-1.5 text-sm font-medium text-cream/85 transition hover:bg-white/10 hover:text-cream">Log out</button>`;
    area.querySelector('#user-name').textContent = user.username;
    const logOut = area.querySelector('#log-out');
    logOut.onclick = async () => {
      logOut.disabled = true;
      logOut.innerHTML = spinner;
      try {
        await api.logout();
        showLoggedOut();
      } catch {
        logOut.disabled = false;
        logOut.textContent = 'Log out';
      }
    };
  }

  // Show a spinner while checking whether the user is already logged in.
  area.innerHTML = `<span class="text-cream">${spinner}</span>`;
  api.me()
    .then(({ user }) => (user ? showLoggedIn(user) : showLoggedOut()))
    .catch(showLoggedOut);
}
