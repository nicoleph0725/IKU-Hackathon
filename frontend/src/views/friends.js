import { api } from '../api.js';
import { setUser } from '../auth.js';
import { navigate } from '../router.js';
import { addCafeMarkers, createMap } from '../components/map.js';
import { getSavedLocation } from '../components/location.js';
import { toast, toastError } from '../components/toast.js';
import { emptyState, esc, timeAgo, timeUntil } from '../components/ui.js';

export function render(el) {
  el.innerHTML = `
    <h1 class="mb-4 text-2xl font-bold">Friends</h1>
    <div class="grid gap-4 md:grid-cols-2">
      <div class="space-y-4">
        <section class="card" id="my-status"></section>
        <section class="card">
          <h2 class="mb-3 font-semibold">Where friends are studying now</h2>
          <div id="friend-checkins" class="mb-3 space-y-2"></div>
          <div id="friends-map" class="map" style="height:16rem"></div>
        </section>
      </div>
      <div class="space-y-4">
        <section class="card">
          <h2 class="mb-3 font-semibold">Add a friend</h2>
          <form id="add-friend" class="flex gap-2">
            <input class="input" name="username" placeholder="Username" required autocomplete="off" />
            <button class="btn-primary shrink-0" type="submit">Send</button>
          </form>
        </section>
        <section class="card">
          <h2 class="mb-3 font-semibold">Requests</h2>
          <div id="requests" class="space-y-2"></div>
        </section>
        <section class="card">
          <h2 class="mb-3 font-semibold">Your friends</h2>
          <ul id="friend-list" class="divide-y divide-stone-100"></ul>
        </section>
      </div>
    </div>`;

  const map = createMap(el.querySelector('#friends-map'), getSavedLocation(), 12);
  let markers = null;

  async function refresh() {
    try {
      const [me, mine, checkins, incoming, outgoing, friends] = await Promise.all([
        api.me(),
        api.myCheckin(),
        api.friendsCheckins(),
        api.listFriendRequests('incoming'),
        api.listFriendRequests('outgoing'),
        api.listFriends({ per_page: 100 }), // TODO: paginate / search once friend lists get long
      ]);
      setUser(me.user);
      drawStatus(me.user, mine.checkin);
      drawCheckins(checkins.items);
      drawRequests(incoming.items, outgoing.items);
      drawFriends(friends.items);
    } catch (err) {
      toastError(err);
    }
  }

  function drawStatus(user, checkin) {
    const box = el.querySelector('#my-status');
    if (!user.share_location) {
      box.innerHTML = `<h2 class="mb-1 font-semibold">Your status: hidden</h2>
        <p class="mb-3 text-sm text-stone-600">Location sharing is off, so friends can't see you. You can still see friends who share with you.</p>
        <a class="btn-secondary" href="#/settings">Turn on sharing</a>`;
    } else if (checkin) {
      box.innerHTML = `<h2 class="mb-1 font-semibold">You're at ${esc(checkin.cafe.name)}</h2>
        <p class="mb-3 text-sm text-stone-600">Visible to friends for another ${timeUntil(checkin.expires_at)}.</p>
        <button id="checkout" class="btn-danger">Check out</button>`;
      box.querySelector('#checkout').addEventListener('click', async () => {
        try {
          await api.checkOut();
          toast('Checked out', 'success');
          refresh();
        } catch (err) {
          toastError(err);
        }
      });
    } else {
      box.innerHTML = `<h2 class="mb-1 font-semibold">You're not checked in</h2>
        <p class="text-sm text-stone-600">Open a cafe and tap “Check in here” to let friends know where you are.</p>`;
    }
  }

  function drawCheckins(items) {
    el.querySelector('#friend-checkins').innerHTML = items.length
      ? items
          .map(
            (c) => `
          <a href="#/cafes/${c.cafe.id}" class="flex items-center justify-between rounded-lg bg-stone-50 px-3 py-2 text-sm hover:bg-amber-50">
            <span><strong>${esc(c.user.username)}</strong> at ${esc(c.cafe.name)}</span>
            <span class="text-xs text-stone-500">${timeAgo(c.checked_in_at)}</span>
          </a>`,
          )
          .join('')
      : emptyState('No friends are checked in right now.');

    // One marker per cafe, labelled with who is there.
    const byCafe = new Map();
    for (const c of items) {
      const entry = byCafe.get(c.cafe.id) ?? { ...c.cafe, names: [] };
      entry.names.push(c.user.username);
      byCafe.set(c.cafe.id, entry);
    }
    markers?.remove();
    const cafes = [...byCafe.values()].map((c) => ({ ...c, name: `${c.name}: ${c.names.join(', ')}` }));
    markers = addCafeMarkers(map, cafes, { onClick: (c) => navigate(`/cafes/${c.id}`) });
    if (cafes.length) map.fitBounds(markers.getBounds(), { padding: [30, 30], maxZoom: 15 });
  }

  function drawRequests(incoming, outgoing) {
    const row = (r, actions) => `
      <div class="flex items-center justify-between gap-2 rounded-lg bg-stone-50 px-3 py-2 text-sm">
        <span>${actions}</span>
      </div>`;
    const html = [
      ...incoming.map((r) =>
        row(r, `<strong>${esc(r.requester.username)}</strong> wants to be friends</span>
          <span class="flex gap-1">
            <button class="btn-primary px-3 py-1" data-accept="${r.id}">Accept</button>
            <button class="btn-secondary px-3 py-1" data-decline="${r.id}">Decline</button>`),
      ),
      ...outgoing.map((r) =>
        row(r, `Waiting for <strong>${esc(r.addressee.username)}</strong></span>
          <span><button class="btn-secondary px-3 py-1" data-decline="${r.id}">Cancel</button>`),
      ),
    ];
    el.querySelector('#requests').innerHTML = html.length ? html.join('') : emptyState('No pending requests.');
  }

  function drawFriends(items) {
    el.querySelector('#friend-list').innerHTML = items.length
      ? items
          .map(
            (f) => `
          <li class="flex items-center justify-between py-2 text-sm">
            <span>${esc(f.user.username)}</span>
            <button class="text-xs text-red-700 underline" data-remove="${f.user.id}" data-name="${esc(f.user.username)}">Remove</button>
          </li>`,
          )
          .join('')
      : `<li>${emptyState('No friends yet. Add someone by username!')}</li>`;
  }

  // --- Event handlers (delegated) ---------------------------------------------
  el.querySelector('#add-friend').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = e.target.username;
    try {
      const res = await api.sendFriendRequest(input.value.trim());
      toast(res.friendship.status === 'accepted' ? 'You are now friends!' : 'Friend request sent', 'success');
      input.value = '';
      refresh();
    } catch (err) {
      toastError(err);
    }
  });

  el.addEventListener('click', async (e) => {
    const t = e.target.closest('button');
    if (!t) return;
    try {
      if (t.dataset.accept) {
        await api.acceptFriendRequest(t.dataset.accept);
        toast('Friend added', 'success');
      } else if (t.dataset.decline) {
        await api.declineFriendRequest(t.dataset.decline);
      } else if (t.dataset.remove) {
        if (!confirm(`Remove ${t.dataset.name} from your friends?`)) return;
        await api.removeFriend(t.dataset.remove);
      } else {
        return;
      }
      refresh();
    } catch (err) {
      toastError(err);
    }
  });

  refresh();
  // Friends' check-ins change over time; poll while the page is open.
  // TODO: replace polling with Server-Sent Events or WebSockets.
  const interval = setInterval(refresh, 60_000);

  return () => {
    clearInterval(interval);
    map.remove();
  };
}
