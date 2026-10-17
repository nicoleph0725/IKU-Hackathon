import { api } from '../api.js';
import { clearUser, getUser, isLoggedIn } from '../auth.js';
import { navigate } from '../router.js';
import { esc } from './ui.js';

const link = (href, label) =>
  `<a href="${href}" data-nav="${href}" class="rounded-lg px-3 py-2 text-sm font-medium text-amber-50/90 hover:bg-amber-800">${label}</a>`;

export function renderNavbar(el) {
  const draw = () => {
    const user = getUser();
    el.innerHTML = `
      <nav class="sticky top-0 z-[1000] bg-amber-900 shadow">
        <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-2">
          <a href="#/" class="text-lg font-bold text-white">☕ StudySpot</a>
          <div class="flex items-center gap-1">
            ${link('#/', 'Search')}
            ${
              isLoggedIn()
                ? `${link('#/friends', 'Friends')}
                   ${link('#/settings', esc(user?.username ?? 'Me'))}
                   <button id="logout" class="rounded-lg px-3 py-2 text-sm text-amber-200 hover:bg-amber-800">Log out</button>`
                : `${link('#/login', 'Log in')}
                   <a href="#/register" class="rounded-lg bg-amber-50 px-3 py-2 text-sm font-medium text-amber-900">Sign up</a>`
            }
          </div>
        </div>
      </nav>`;
    el.querySelector('#logout')?.addEventListener('click', async () => {
      await api.logout().catch(() => {}); // clear the server session; ignore if it already expired
      clearUser();
      navigate('/login');
    });
    highlight();
  };

  const highlight = () => {
    const current = '#' + (window.location.hash.slice(1).split('?')[0] || '/');
    el.querySelectorAll('[data-nav]').forEach((a) => {
      a.classList.toggle('bg-amber-800', a.dataset.nav === current);
    });
  };

  window.addEventListener('auth-changed', draw);
  window.addEventListener('hashchange', highlight);
  draw();
}
