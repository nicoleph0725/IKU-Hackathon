// The user's position, used only on this device for distance search (never sent to friends).
// Falls back to central London so the demo works without granting location permission.
export const DEFAULT_LOCATION = { lat: 51.5074, lng: -0.1278, label: 'Central London' };
const KEY = 'studyspot.location';

export function getSavedLocation() {
  try {
    return JSON.parse(sessionStorage.getItem(KEY)) ?? DEFAULT_LOCATION;
  } catch {
    return DEFAULT_LOCATION;
  }
}

export function requestBrowserLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error('Geolocation is not supported by this browser'));
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude, label: 'Your location' };
        sessionStorage.setItem(KEY, JSON.stringify(loc));
        resolve(loc);
      },
      () => reject(new Error('Could not get your location; using central London')),
      { timeout: 8000, maximumAge: 60000 },
    );
  });
}
