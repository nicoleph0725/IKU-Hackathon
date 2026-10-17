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
  'field w-full rounded-xl px-3.5 py-2.5 text-sm';

export function openAuthModal(mode, onSuccess) {
  const isSignup = mode === 'signup';
  const overlay = document.createElement('div');
  overlay.className = 'fixed inset-0 z-[2000] flex items-center justify-center bg-stone-900/35 p-4 backdrop-blur-xs';
  overlay.innerHTML = `
    <form class="surface w-full max-w-sm space-y-3.5 rounded-3xl p-6">
      <div>
        <h2 class="text-lg font-bold tracking-tight text-brand">${isSignup ? 'Create your account' : 'Welcome back'}</h2>
        <p class="mt-0.5 text-xs text-stone-500">${isSignup ? 'Save your favourite study spots and preferences.' : 'Sign in to access your saved study spots.'}</p>
      </div>
      ${isSignup ? `<input name="username" placeholder="Username" required class="${inputClass}" />` : ''}
      <input name="email" type="email" placeholder="Email address" required autocomplete="email" class="${inputClass}" />
      <input name="password" type="password" placeholder="Password${isSignup ? ' (8+ characters)' : ''}"
        required minlength="${isSignup ? 8 : 1}"
        autocomplete="${isSignup ? 'new-password' : 'current-password'}" class="${inputClass}" />
      <p class="error hidden rounded-xl bg-red-50 px-3 py-2 text-xs font-medium text-red-600"></p>
      <div class="flex justify-end gap-2 pt-2">
        <button type="button" class="cancel btn-soft cursor-pointer rounded-xl px-4 py-2 text-xs font-medium">Cancel</button>
        <button type="submit" class="btn-matcha cursor-pointer rounded-xl px-4 py-2 text-xs font-semibold">
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