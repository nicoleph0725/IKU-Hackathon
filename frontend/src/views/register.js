import { api, formatErrorDetails } from '../api.js';
import { setSession } from '../auth.js';
import { navigate } from '../router.js';
import { toast } from '../components/toast.js';

export function render(el) {
  el.innerHTML = `
    <div class="mx-auto max-w-sm pt-6">
      <h1 class="mb-1 text-2xl font-bold">Create an account</h1>
      <p class="mb-6 text-sm text-stone-500">Find your next study spot.</p>
      <form id="register-form" class="card space-y-4">
        <div>
          <label class="label" for="username">Username</label>
          <input class="input" id="username" name="username" minlength="3" maxlength="30"
                 pattern="[A-Za-z0-9_]+" title="Letters, numbers and underscores" autocomplete="username" required />
        </div>
        <div>
          <label class="label" for="email">Email</label>
          <input class="input" id="email" name="email" type="email" autocomplete="email" required />
        </div>
        <div>
          <label class="label" for="password">Password</label>
          <input class="input" id="password" name="password" type="password" minlength="8" autocomplete="new-password" required />
          <p class="mt-1 text-xs text-stone-500">At least 8 characters.</p>
        </div>
        <button class="btn-primary w-full" type="submit">Sign up</button>
      </form>
      <p class="mt-4 text-center text-sm">Already have an account? <a class="font-medium text-amber-800 underline" href="#/login">Log in</a></p>
    </div>`;

  const form = el.querySelector('#register-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      const { access_token, user } = await api.register(Object.fromEntries(new FormData(form)));
      setSession(access_token, user);
      toast(`Welcome, ${user.username}!`, 'success');
      navigate('/');
    } catch (err) {
      toast([err.message, formatErrorDetails(err.details)].filter(Boolean).join('\n'), 'error');
    } finally {
      button.disabled = false;
    }
  });
}
