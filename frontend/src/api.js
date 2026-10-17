// Thin wrapper around fetch: JSON in/out, attaches the JWT, normalises errors.
//
// Every backend error looks like {"error": {"code", "message", "details"}} and is thrown
// here as an ApiError so views can `try { ... } catch (e) { toast(e.message) }`.
import { getToken, clearSession } from './auth.js';

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api';

export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request(method, path, { body, query } = {}) {
  const url = new URL(BASE_URL + path, window.location.origin);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value);
  }

  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(url, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  } catch {
    throw new ApiError(0, 'network_error', 'Cannot reach the server. Is the backend running?');
  }

  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const err = data?.error ?? {};
    // Expired/invalid token: drop the session and send the user to login.
    if (res.status === 401 && token && !path.startsWith('/auth/')) {
      clearSession();
      window.location.hash = '#/login';
    }
    throw new ApiError(res.status, err.code ?? 'error', err.message ?? `Request failed (${res.status})`, err.details);
  }
  return data;
}

/** Turn marshmallow-style {field: [messages]} details into one readable string. */
export function formatErrorDetails(details) {
  if (!details || typeof details !== 'object') return '';
  return Object.entries(details)
    .map(([field, msgs]) => `${field}: ${[].concat(msgs).join(', ')}`)
    .join('\n');
}

// --- Endpoint helpers -------------------------------------------------------
export const api = {
  // auth
  register: (data) => request('POST', '/auth/register', { body: data }),
  login: (login, password) => request('POST', '/auth/login', { body: { login, password } }),
  me: () => request('GET', '/auth/me'),
  updateSettings: (settings) => request('PATCH', '/users/me/settings', { body: settings }),

  // cafes
  searchCafes: (params) => request('GET', '/cafes', { query: params }),
  getCafe: (id, coords) => request('GET', `/cafes/${id}`, { query: coords }),
  reportBusyness: (id, level) => request('POST', `/cafes/${id}/busyness`, { body: { level } }),

  // reviews
  listReviews: (cafeId, params) => request('GET', `/cafes/${cafeId}/reviews`, { query: params }),
  createReview: (cafeId, data) => request('POST', `/cafes/${cafeId}/reviews`, { body: data }),
  updateReview: (id, data) => request('PUT', `/reviews/${id}`, { body: data }),
  deleteReview: (id) => request('DELETE', `/reviews/${id}`),

  // friends
  listFriends: (params) => request('GET', '/friends', { query: params }),
  listFriendRequests: (direction = 'incoming') => request('GET', '/friends/requests', { query: { direction } }),
  sendFriendRequest: (username) => request('POST', '/friends/requests', { body: { username } }),
  acceptFriendRequest: (id) => request('POST', `/friends/requests/${id}/accept`),
  declineFriendRequest: (id) => request('DELETE', `/friends/requests/${id}`),
  removeFriend: (userId) => request('DELETE', `/friends/${userId}`),
  friendsCheckins: () => request('GET', '/friends/checkins'),

  // check-ins
  checkIn: (cafeId, durationMinutes) =>
    request('POST', '/checkins', { body: { cafe_id: cafeId, duration_minutes: durationMinutes } }),
  checkOut: () => request('POST', '/checkins/checkout'),
  myCheckin: () => request('GET', '/checkins/me'),
};
