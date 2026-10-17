async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Something went wrong.');
  return data;
}

export const api = {
  me: () => request('/api/auth/me'),
  login: (body) => request('/api/auth/login', { method: 'POST', body: JSON.stringify(body) }),
  signup: (body) => request('/api/auth/signup', { method: 'POST', body: JSON.stringify(body) }),
  logout: () => request('/api/auth/logout', { method: 'POST' }),
};

const inputClass =
  'w-full rounded-lg border border-amber-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-600';

export function openAuthModal(mode, onSuccess) {
  const isSignup = mode === 'signup';
  const overlay = document.createElement('div');
  overlay.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4';
  overlay.innerHTML = `
    <form class="w-full max-w-sm space-y-3 rounded-xl bg-white p-6 shadow-xl">
      <h2 class="text-xl font-bold text-brand">${isSignup ? 'Create your account' : 'Welcome back'}</h2>
      ${isSignup ? `<input name="username" placeholder="Username" required class="${inputClass}" />` : ''}
      <input name="email" type="email" placeholder="Email" required autocomplete="email" class="${inputClass}" />
      <input name="password" type="password" placeholder="Password${isSignup ? ' (8+ characters)' : ''}"
        required minlength="${isSignup ? 8 : 1}"
        autocomplete="${isSignup ? 'new-password' : 'current-password'}" class="${inputClass}" />
      <p class="error hidden text-sm text-red-600"></p>
      <div class="flex justify-end gap-2 pt-1">
        <button type="button" class="cancel rounded-lg px-3 py-2 text-sm text-amber-900 hover:bg-amber-100">Cancel</button>
        <button type="submit" class="rounded-lg bg-amber-900 px-4 py-2 text-sm font-medium text-white hover:bg-amber-800">
          ${isSignup ? 'Sign up' : 'Sign in'}
        </button>
      </div>
    </form>`;

  const form = overlay.querySelector('form');
  const errorEl = overlay.querySelector('.error');
  const close = () => {
    document.removeEventListener('keydown', onKey);
    overlay.remove();
  };
  const onKey = (e) => e.key === 'Escape' && close();

  document.addEventListener('keydown', onKey);
  overlay.addEventListener('click', (e) => e.target === overlay && close());
  overlay.querySelector('.cancel').addEventListener('click', close);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(form));
    const submit = form.querySelector('[type=submit]');
    submit.disabled = true;
    errorEl.classList.add('hidden');
    try {
      const { user } = await (isSignup ? api.signup(body) : api.login(body));
      close();
      onSuccess(user);
    } catch (err) {
      errorEl.textContent = err.message;
      errorEl.classList.remove('hidden');
      submit.disabled = false;
    }
  });

  document.body.appendChild(overlay);
  form.querySelector('input').focus();
}