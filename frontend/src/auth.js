// Session storage for the JWT + current user.
// TODO: localStorage is readable by any script on the page (XSS risk). For production,
// move to an httpOnly cookie (Flask-JWT-Extended supports JWT_TOKEN_LOCATION=["cookies"]).
const TOKEN_KEY = 'studyspot.token';
const USER_KEY = 'studyspot.user';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY));
  } catch {
    return null;
  }
}

export function isLoggedIn() {
  return Boolean(getToken());
}

export function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  setUser(user);
}

export function setUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  window.dispatchEvent(new CustomEvent('auth-changed'));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  window.dispatchEvent(new CustomEvent('auth-changed'));
}
