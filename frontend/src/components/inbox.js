// Inbox in the navbar: add friends by username, accept/decline requests, see your friends.
import { request, spinner } from './auth.js';

const friendsApi = {
  list: () => request('/api/friends'),
  add: (username) => request('/api/friends/request', { method: 'POST', body: JSON.stringify({ username }) }),
  accept: (id) => request(`/api/friends/${id}/accept`, { method: 'POST' }),
  decline: (id) => request(`/api/friends/${id}/decline`, { method: 'POST' }),
  location: () => request('/api/friends/location'),
  share: (cafe) => request('/api/friends/location', { method: 'PUT', body: JSON.stringify({ cafe }) }),
  stopSharing: () => request('/api/friends/location', { method: 'DELETE' }),
};

// "Share location" / "Stop sharing location" button for a cafe's popup. Stays hidden when signed out.
export function shareLocationButton(cafeName) {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'share-location btn-matcha mt-2.5 hidden w-full cursor-pointer items-center justify-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold disabled:cursor-wait';

  function show(sharingAt) {
    btn.textContent = sharingAt === cafeName ? 'Stop sharing location' : "Share location: I'm here";
    btn.classList.replace('hidden', 'flex');
    btn.disabled = false;
  }

  friendsApi.location().then(({ cafe }) => show(cafe)).catch(() => {});
  btn.onclick = async () => {
    const stopping = btn.textContent.startsWith('Stop');
    btn.disabled = true;
    btn.innerHTML = spinner;
    try {
      show((await (stopping ? friendsApi.stopSharing() : friendsApi.share(cafeName))).cafe);
    } catch {
      show(stopping ? cafeName : null);
    }
  };
  return btn;
}

export function renderInbox(el) {
  el.className = 'relative';
  el.innerHTML = `
    <button id="inbox-open" type="button"
      class="flex cursor-pointer items-center gap-1.5 rounded-xl px-3 py-1.5 text-sm font-medium text-cream/85 transition hover:bg-white/10 hover:text-cream">
      Inbox
      <span id="inbox-count" class="hidden min-w-5 rounded-full bg-matcha-200 px-1.5 text-center text-[11px] font-bold text-brand"></span>
    </button>

    <div id="inbox-panel" class="surface fixed right-3 top-16 hidden w-[calc(100vw-1.5rem)] max-w-sm flex-col overflow-hidden rounded-3xl text-stone-800 sm:right-6">
      <div class="flex shrink-0 items-center justify-between border-b border-stone-200/70 px-5 py-3.5">
        <h2 class="text-sm font-bold tracking-tight text-brand">Inbox</h2>
        <button id="inbox-close" type="button" aria-label="Close inbox"
          class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-full text-stone-400 transition hover:bg-stone-100 hover:text-stone-700">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M18 6 6 18"></path>
            <path d="m6 6 12 12"></path>
          </svg>
        </button>
      </div>

      <div class="max-h-[calc(100dvh-8rem)] space-y-4 overflow-y-auto px-5 py-4">
        <form id="inbox-add" class="space-y-2">
          <label class="text-xs font-semibold text-stone-500" for="inbox-username">Add a friend</label>
          <div class="flex gap-2">
            <input id="inbox-username" name="username" placeholder="Username" required autocomplete="off"
              class="field min-w-0 flex-1 rounded-xl px-3.5 py-2 text-sm" />
            <button type="submit" class="btn-matcha flex cursor-pointer items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold disabled:cursor-wait disabled:opacity-80">Add</button>
          </div>
          <p id="inbox-msg" class="hidden rounded-xl px-3 py-2 text-xs font-medium"></p>
        </form>
        <div id="inbox-lists"></div>
      </div>
    </div>`;

  const openBtn = el.querySelector('#inbox-open');
  const panel = el.querySelector('#inbox-panel');
  const count = el.querySelector('#inbox-count');
  const lists = el.querySelector('#inbox-lists');
  const form = el.querySelector('#inbox-add');
  const msg = el.querySelector('#inbox-msg');

  function showMessage(text, ok) {
    msg.textContent = text;
    msg.className = `rounded-xl px-3 py-2 text-xs font-medium ${ok ? 'bg-matcha-100 text-matcha-800' : 'bg-red-50 text-red-600'}`;
  }

  // One titled section of users, each with optional action buttons.
  function section(title, users, empty, actions = []) {
    const wrap = document.createElement('div');
    wrap.className = 'space-y-2';
    wrap.innerHTML = `<h3 class="text-xs font-semibold text-stone-500"></h3><ul class="space-y-1.5"></ul>`;
    wrap.querySelector('h3').textContent = `${title} (${users.length})`;
    const ul = wrap.querySelector('ul');
    if (!users.length) {
      ul.innerHTML = `<li class="text-xs text-stone-400">${empty}</li>`;
    }
    for (const user of users) {
      const li = document.createElement('li');
      li.className = 'flex items-center justify-between gap-2 rounded-xl bg-white/70 px-3 py-2';
      li.innerHTML = `<div class="min-w-0"><p class="truncate text-sm font-medium text-brand"></p></div><div class="flex shrink-0 gap-1.5"></div>`;
      li.querySelector('p').textContent = user.username;
      if (user.cafe) {
        const at = document.createElement('p');
        at.className = 'truncate text-xs text-matcha-700';
        at.textContent = `At ${user.cafe}`;
        li.firstElementChild.appendChild(at);
      }
      for (const { label, cls, run } of actions) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `${cls} flex cursor-pointer items-center rounded-xl px-3 py-1 text-xs font-semibold disabled:cursor-wait`;
        btn.textContent = label;
        btn.onclick = async () => {
          li.querySelectorAll('button').forEach((b) => (b.disabled = true));
          btn.innerHTML = spinner;
          try {
            await run(user.id);
          } catch (err) {
            showMessage(err.message, false);
          }
          load();
        };
        li.querySelector('div').appendChild(btn);
      }
      ul.appendChild(li);
    }
    return wrap;
  }

  // Where I'm sharing that I am, with a button to stop.
  function myStatus(cafe) {
    const box = document.createElement('div');
    box.className = 'flex items-center justify-between gap-2 rounded-xl border border-matcha-200 bg-matcha-50 px-3 py-2';
    box.innerHTML = `<div class="min-w-0"><p class="text-xs font-semibold text-stone-500">Your status</p><p class="truncate text-sm font-medium text-brand"></p></div>`;
    box.querySelector('p:last-child').textContent = cafe ? `At ${cafe}` : 'Not sharing your location';
    if (cafe) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn-soft flex shrink-0 cursor-pointer items-center rounded-xl px-3 py-1 text-xs font-semibold disabled:cursor-wait';
      btn.textContent = 'Stop sharing';
      btn.onclick = async () => {
        btn.disabled = true;
        btn.innerHTML = spinner;
        try {
          await friendsApi.stopSharing();
        } catch (err) {
          showMessage(err.message, false);
        }
        load();
      };
      box.appendChild(btn);
    }
    return box;
  }

  async function load() {
    if (!lists.children.length) lists.innerHTML = `<div class="flex justify-center py-4 text-matcha-600">${spinner}</div>`;
    try {
      const [{ friends, incoming, outgoing }, { cafe }] = await Promise.all([friendsApi.list(), friendsApi.location()]);
      count.textContent = incoming.length;
      count.classList.toggle('hidden', !incoming.length);
      lists.className = 'space-y-4';
      lists.replaceChildren(
        myStatus(cafe),
        section('Requests', incoming, 'No new requests.', [
          { label: 'Accept', cls: 'btn-matcha', run: friendsApi.accept },
          { label: 'Decline', cls: 'btn-soft', run: friendsApi.decline },
        ]),
        ...(outgoing.length
          ? [section('Sent', outgoing, '', [{ label: 'Cancel', cls: 'btn-soft', run: friendsApi.decline }])]
          : []),
        section('Friends', friends, 'No friends yet. Add someone by username above.'),
      );
    } catch (err) {
      lists.innerHTML = `<p class="rounded-xl bg-red-50 px-3 py-2 text-xs font-medium text-red-600"></p>`;
      lists.querySelector('p').textContent = err.message;
    }
  }

  const isOpen = () => !panel.classList.contains('hidden');
  function setOpen(open) {
    panel.classList.toggle('hidden', !open);
    panel.classList.toggle('flex', open);
    if (open) load();
  }

  openBtn.onclick = () => setOpen(!isOpen());
  el.querySelector('#inbox-close').onclick = () => setOpen(false);

  // Close on Escape or a click outside. Listeners remove themselves once the inbox is gone (after logout).
  function onDocClick(e) {
    if (!el.isConnected) return document.removeEventListener('click', onDocClick);
    if (isOpen() && !el.contains(e.target)) setOpen(false);
  }
  function onKey(e) {
    if (!el.isConnected) return document.removeEventListener('keydown', onKey);
    if (e.key === 'Escape' && isOpen()) setOpen(false);
  }
  document.addEventListener('click', onDocClick);
  document.addEventListener('keydown', onKey);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = form.querySelector('input');
    const submit = form.querySelector('[type=submit]');
    submit.disabled = true;
    submit.innerHTML = spinner;
    msg.classList.add('hidden');
    try {
      const { status } = await friendsApi.add(input.value);
      showMessage(status === 'accepted' ? `You and ${input.value.trim()} are now friends.` : `Request sent to ${input.value.trim()}.`, true);
      input.value = '';
      load();
    } catch (err) {
      showMessage(err.message, false);
    }
    submit.disabled = false;
    submit.textContent = 'Add';
  });

  // Fill in the request count badge straight away.
  load();
}
