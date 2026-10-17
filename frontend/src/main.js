import 'leaflet/dist/leaflet.css';
import './style.css';

import { route, startRouter } from './router.js';
import { renderNavbar } from './components/navbar.js';

// Views are lazy-loaded so each page only pulls in what it needs (e.g. Leaflet).
route('/', () => import('./views/search.js'));
route('/login', () => import('./views/login.js'), { guestOnly: true });
route('/register', () => import('./views/register.js'), { guestOnly: true });
route('/cafes/:id', () => import('./views/cafeDetail.js'));
route('/cafes/:id/review', () => import('./views/writeReview.js'), { auth: true });
route('/friends', () => import('./views/friends.js'), { auth: true });
route('/settings', () => import('./views/settings.js'), { auth: true });
// TODO: '/profile/:username' (public profile with reviews), '/me/history' (study stats)

renderNavbar(document.getElementById('navbar'));
startRouter(document.getElementById('app'));
