// Who is logged in, from the frontend's point of view.
//
// The real login is the server's session cookie, which the browser sends automatically.
// We only keep a copy of the user object here so the navbar/pages can show the username
// and know whether to show "Log in" or "Log out" without asking the server every time.
const USER_KEY = 'studyspot.user';

export function getUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY));
  } catch {
    return null;
  }
}

export function isLoggedIn() {
  return Boolean(getUser());
}

export function setUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  window.dispatchEvent(new CustomEvent('auth-changed'));
}

export function clearUser() {
  localStorage.removeItem(USER_KEY);
  window.dispatchEvent(new CustomEvent('auth-changed'));
}
