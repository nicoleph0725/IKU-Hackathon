// Minimal hash router: '#/cafes/12' -> view module with params {id: '12'}.
// Each view exports `render(container, params)` and may return a cleanup function.
import { isLoggedIn } from './auth.js';

const routes = [];
let cleanup = null;

/** Register a route. Pattern like '/cafes/:id'. */
export function route(pattern, loader, { auth = false, guestOnly = false } = {}) {
  const keys = [];
  const regex = new RegExp(
    '^' + pattern.replace(/:(\w+)/g, (_, key) => (keys.push(key), '([^/]+)')) + '/?$',
  );
  routes.push({ regex, keys, loader, auth, guestOnly });
}

export function navigate(path) {
  window.location.hash = '#' + path;
}

function currentPath() {
  return window.location.hash.slice(1).split('?')[0] || '/';
}

export function queryParams() {
  return new URLSearchParams(window.location.hash.split('?')[1] ?? '');
}

async function resolve(container) {
  const path = currentPath();
  const match = routes.map((r) => ({ r, m: path.match(r.regex) })).find((x) => x.m);
  if (!match) {
    container.innerHTML = `<div class="card text-center"><p class="mb-3">Page not found.</p><a class="btn-primary" href="#/">Go home</a></div>`;
    return;
  }
  const { r, m } = match;
  if (r.auth && !isLoggedIn()) return navigate(`/login?next=${encodeURIComponent(path)}`);
  if (r.guestOnly && isLoggedIn()) return navigate('/');

  const params = Object.fromEntries(r.keys.map((k, i) => [k, decodeURIComponent(m[i + 1])]));
  if (typeof cleanup === 'function') cleanup();
  cleanup = null;
  container.innerHTML = `<p class="py-10 text-center text-stone-500">Loading…</p>`;
  const view = await r.loader();
  cleanup = await view.render(container, params);
  window.scrollTo(0, 0);
}

export function startRouter(container) {
  window.addEventListener('hashchange', () => resolve(container));
  resolve(container);
}
