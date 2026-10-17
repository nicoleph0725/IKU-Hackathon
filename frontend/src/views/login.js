import { api } from '../api.js';
import { setUser } from '../auth.js';
import { navigate, queryParams } from '../router.js';
import { toastError } from '../components/toast.js';

export function render(el) {
  el.innerHTML = `
    <div class="mx-auto max-w-sm pt-6">
      <h1 class="mb-1 text-2xl font-bold">Welcome back</h1>
      <p class="mb-6 text-sm text-stone-500">Log in to review cafes and see where friends are studying.</p>
      <form id="login-form" class="card space-y-4">
        <div>
          <label class="label" for="login">Username or email</label>
          <input class="input" id="login" name="login" autocomplete="username" required />
        </div>
        <div>
          <label class="label" for="password">Password</label>
          <input class="input" id="password" name="password" type="password" autocomplete="current-password" required />
        </div>
        <button class="btn-primary w-full" type="submit">Log in</button>
      </form>
      <p class="mt-4 text-center text-sm">No account? <a class="font-medium text-amber-800 underline" href="#/register">Sign up</a></p>
    </div>`;

  const form = el.querySelector('#login-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      const { login, password } = Object.fromEntries(new FormData(form));
      const { user } = await api.login(login, password); // server sets the session cookie
      setUser(user);
      navigate(queryParams().get('next') ?? '/');
    } catch (err) {
      toastError(err);
    } finally {
      button.disabled = false;
    }
  });
}
