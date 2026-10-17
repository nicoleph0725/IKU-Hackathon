import { todo } from '../components/ui.js';

export function render(el) {
  el.innerHTML = `
    <h1 class="mb-4 text-2xl font-bold">Friends</h1>
    <div class="grid gap-4 md:grid-cols-2">
      ${todo('Where friends are now: api.friendsCheckins() as a list (and maybe a map).')}
      ${todo('Add friend by username: api.sendFriendRequest(username).')}
      ${todo('Incoming requests with Accept buttons: api.listFriendRequests() / api.acceptFriendRequest(id).')}
      ${todo('Friend list with Remove buttons: api.listFriends() / api.removeFriend(userId).')}
    </div>`;
}
