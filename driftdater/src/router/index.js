/**
 * router/index.js
 * ---------------
 * Vue Router configuration for DriftDater.
 *
 * Route Guard
 * -----------
 * Routes marked with `meta: { requiresAuth: true }` are protected by a
 * navigation guard (beforeEach).  Before entering a protected route the
 * guard checks the auth store:
 *
 *   1. If auth.user is already populated (e.g. same-tab navigation), allow.
 *   2. If auth.user is null, call checkAuth() to attempt token validation
 *      against the server (handles page reloads where state is lost).
 *   3. If still not authenticated after checkAuth(), redirect to /login.
 *
 * Route Lazy Loading
 * ------------------
 * All view components are imported with dynamic import() rather than static
 * imports.  Vite splits each view into a separate JS chunk so the browser
 * only downloads the code for the current page, reducing initial load time.
 *
 * Routes
 * ------
 * /              HomeView            Public landing page
 * /login         LoginView           Login form
 * /register      RegisterView        Sign-up form
 * /dashboard     DashboardView  *    Discover / browse potential matches
 * /profile       ProfileView    *    Own profile view & editor
 * /profile/:id   ProfileViewPublic * Public profile of another user
 * /matches       MatchesView    *    List of mutual matches
 * /messages      MessagesView   *    Conversation list
 * /messages/:id  ConversationView *  Individual chat thread
 * /search        SearchView     *    Search & discover by name/location
 * /favorites     FavoritesView  *    Bookmarked profiles
 * /settings      SettingsView   *    Theme toggle & block management
 *
 * (* = requires authentication)
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../views/ProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile/:id',
    name: 'profile-view',
    component: () => import('../views/ProfileViewPublic.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/matches',
    name: 'matches',
    component: () => import('../views/MatchesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/messages',
    name: 'messages',
    component: () => import('../views/MessagesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/messages/:id',
    name: 'conversation',
    component: () => import('../views/ConversationView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/search',
    name: 'search',
    component: () => import('../views/SearchView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/favorites',
    name: 'favorites',
    component: () => import('../views/FavoritesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

/**
 * Global navigation guard.
 *
 * Runs before every route change.  Protected routes (meta.requiresAuth)
 * require a valid JWT stored in this tab's sessionStorage.  If the user
 * is not authenticated they are redirected to the login page.
 */
router.beforeEach(async (to) => {
  if (to.meta.requiresAuth) {
    const auth = useAuthStore()
    // Attempt to restore auth state if not already loaded (e.g. page reload)
    if (!auth.user) await auth.checkAuth()
    // Redirect to login if still unauthenticated
    if (!auth.user) return { name: 'login' }
  }
})

export default router
