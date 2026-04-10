import { API } from './config.js'
/**
 * stores/auth.js
 * --------------
 * Pinia store for authentication state and API calls.
 *
 * Tab Isolation via sessionStorage
 * ---------------------------------
 * The app uses JWT tokens stored in sessionStorage rather than cookies.
 * sessionStorage is tab-isolated by the browser spec — each tab gets its own
 * completely separate storage that other tabs cannot read or write.
 *
 * This means two browser tabs can be logged in as two different users
 * simultaneously.  Reloading a tab restores its own token, not the last
 * token that was written anywhere in the browser.
 *
 * Token Key : 'dd_token' in sessionStorage (cleared on tab close).
 *
 * Axios Interceptor
 * -----------------
 * A request interceptor is registered once at module load time.  It reads
 * the token from sessionStorage before every request and adds the header:
 *   Authorization: Bearer <token>
 * This means individual API calls in this store do not need to pass headers
 * manually — the interceptor handles it globally.
 *
 * State
 * -----
 * user    : ref(null | UserObject)  The currently authenticated user's data.
 * loading : ref(bool)               True while an async auth operation is running.
 *
 * Actions
 * -------
 * checkAuth()              Validate the stored token against the server on page load.
 * login(email, password)   Authenticate and store the returned token.
 * register(data)           Create an account and store the returned token.
 * logout()                 Clear the token and reset user state.
 * updateProfile(id, data)  Save profile changes and refresh the stored user.
 * uploadPhoto(id, file)    Upload a new profile photo and update the photo field.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'


// ── sessionStorage helpers ────────────────────────────────────────────────────
// Keeping these as small named functions makes the intent clear and makes it
// easy to swap storage strategy if needed (e.g. in-memory for testing).

/** Read the JWT from this tab's sessionStorage. */
function getToken()      { return sessionStorage.getItem('dd_token') }

/** Write a JWT to this tab's sessionStorage. */
function setToken(t)     { sessionStorage.setItem('dd_token', t) }

/** Remove the JWT from this tab's sessionStorage (logout / expiry). */
function clearToken()    { sessionStorage.removeItem('dd_token') }

// ── Axios request interceptor ─────────────────────────────────────────────────
// Registered once at module import time.  Runs before every axios request
// made anywhere in the application and attaches the Authorization header if
// a token exists for this tab.
axios.interceptors.request.use(config => {
  const token = getToken()
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  return config
})

// ── Store definition ──────────────────────────────────────────────────────────
export const useAuthStore = defineStore('auth', () => {
  /** The authenticated user's profile data, or null if not logged in. */
  const user    = ref(null)

  /** True while an async auth operation (login, register, etc.) is pending. */
  const loading = ref(false)

  /**
   * Validate the stored JWT against the server and restore user state.
   *
   * Called on every page load from App.vue's onMounted hook.  If the tab has
   * no token the user is treated as logged out immediately (no network call).
   * If the token is expired or invalid, it is cleared and user is set to null.
   */
  async function checkAuth() {
    if (!getToken()) { user.value = null; return }
    try {
      const res  = await axios.get(`${API}/auth/status`)
      user.value = res.data.user
    } catch {
      // Token is invalid or expired — clear it for this tab only
      clearToken()
      user.value = null
    }
  }

  /**
   * Authenticate with email and password.
   *
   * On success, stores the returned JWT in this tab's sessionStorage and
   * updates the reactive user state.
   *
   * @param {string} email
   * @param {string} password
   * @returns {object} Server response data including `token` and `user`.
   * @throws  Axios error with response.data.error on 401/400.
   */
  async function login(email, password) {
    const res  = await axios.post(`${API}/login`, { email, password })
    setToken(res.data.token)   // Store token in THIS tab's sessionStorage only
    user.value = res.data.user
    return res.data
  }

  /**
   * Register a new account.
   *
   * @param {object} data  Registration fields (email, username, password, etc.)
   * @returns {object} Server response data including `token` and `user`.
   * @throws  Axios error on validation failure (400) or duplicate (409).
   */
  async function register(data) {
    const res  = await axios.post(`${API}/register`, data)
    setToken(res.data.token)
    user.value = res.data.user
    return res.data
  }

  /**
   * Log out the current tab's user.
   *
   * Calls the logout endpoint (for audit/hook purposes) and then clears only
   * this tab's token.  Other tabs remain logged in as their own users.
   */
  async function logout() {
    await axios.post(`${API}/logout`, {})
    clearToken()       // Only clears THIS tab's token
    user.value = null
  }

  /**
   * Save profile changes for the given user ID.
   *
   * Updates the reactive `user` state with the server's response so the UI
   * reflects changes immediately without a separate checkAuth() call.
   *
   * @param {number} userId
   * @param {object} data  Partial profile fields to update.
   * @returns {object} Server response data.
   */
  async function updateProfile(userId, data) {
    const res  = await axios.put(`${API}/profiles/${userId}`, data)
    user.value = res.data.user
    return res.data
  }

  /**
   * Upload a new profile photo.
   *
   * Sends a multipart/form-data POST and updates the profile_photo field on
   * the reactive user object without a full profile reload.
   *
   * @param {number} userId
   * @param {File}   file    The selected image file from an <input type="file">.
   * @returns {object} Server response data including `photo` (filename).
   */
  async function uploadPhoto(userId, file) {
    const form = new FormData()
    form.append('photo', file)
    const res = await axios.post(`${API}/profiles/${userId}/photo`, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (user.value) user.value.profile_photo = res.data.photo
    return res.data
  }

  return { user, loading, checkAuth, login, register, logout, updateProfile, uploadPhoto }
})
