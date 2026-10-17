import { esc } from './ui.js';

/** Show a short notification. type: 'info' | 'success' | 'error' */
export function toast(message, type = 'info') {
  const colors = {
    info: 'bg-stone-800 text-white',
    success: 'bg-emerald-700 text-white',
    error: 'bg-red-700 text-white',
  };
  const el = document.createElement('div');
  el.className = `pointer-events-auto max-w-md whitespace-pre-line rounded-lg px-4 py-2 text-sm shadow-lg ${colors[type]}`;
  el.innerHTML = esc(message);
  document.getElementById('toasts').append(el);
  setTimeout(() => el.remove(), 4000);
}

/** Convenience: toast an ApiError (or any Error). */
export function toastError(err) {
  toast(err?.message ?? 'Something went wrong', 'error');
}
