import { api } from '../api.js';
import { setUser } from '../auth.js';
import { esc } from '../components/ui.js';
import { toast, toastError } from '../components/toast.js';

export async function render(el) {
  const { user } = await api.me();
  setUser(user);

  el.innerHTML = `
    <div class="mx-auto max-w-lg space-y-4">
      <h1 class="text-2xl font-bold">Settings</h1>
      <section class="card">
        <p class="font-semibold">${esc(user.username)}</p>
        <p class="text-sm text-stone-500">${esc(user.email)}</p>
      </section>
      <section class="card">
        <label class="flex items-start justify-between gap-4">
          <span>
            <span class="block font-semibold">Share my check-ins with friends</span>
            <span class="mt-1 block text-sm text-stone-500">
              When on, you can check in at a cafe and accepted friends will see where you are studying.
              We never share live GPS: only the cafe you choose. Check-ins expire after a few hours, and
              turning this off checks you out immediately.
            </span>
          </span>
          <input id="share" type="checkbox" class="mt-1 h-5 w-5 shrink-0 accent-amber-800" ${user.share_location ? 'checked' : ''} />
        </label>
      </section>
      <!-- TODO: change password, delete account, default check-in duration -->
    </div>`;

  el.querySelector('#share').addEventListener('change', async (e) => {
    try {
      const res = await api.updateSettings({ share_location: e.target.checked });
      setUser(res.user);
      toast(res.user.share_location ? 'Sharing on: friends can see your check-ins' : 'Sharing off', 'success');
    } catch (err) {
      e.target.checked = !e.target.checked;
      toastError(err);
    }
  });
}
