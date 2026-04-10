/**
 * stores/theme.js
 * ---------------
 * Pinia store for dark/light theme management.
 * This implements Optional Feature 2: Dark Mode / Theme Customisation.
 *
 * How It Works
 * ------------
 * The active theme is controlled by a `data-theme` attribute on the
 * <html> element (document.documentElement).  The CSS file defines two
 * complete sets of CSS custom properties:
 *
 *   :root, [data-theme="light"] { --bg-primary: #faf8f5; ... }
 *   [data-theme="dark"]         { --bg-primary: #0f0d14; ... }
 *
 * Setting `data-theme="dark"` on the root element causes the browser to
 * apply the dark variable set to every element on the page simultaneously,
 * producing an instant, flicker-free theme switch without re-rendering.
 *
 * Persistence
 * -----------
 * The chosen theme is saved to localStorage under the key 'theme'.
 * Unlike sessionStorage, localStorage is shared across all tabs, so the
 * theme preference is consistent everywhere.  The preference is read and
 * applied immediately on store initialisation (before any component mounts)
 * to prevent a flash of the wrong theme on page load.
 *
 * State
 * -----
 * isDark : ref(bool)  True when the dark theme is active.
 *
 * Actions
 * -------
 * toggle()  Switches between light and dark themes.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  /**
   * Reactive flag — true when the dark theme is currently active.
   * Initialised from localStorage so the previous preference is restored.
   */
  const isDark = ref(localStorage.getItem('theme') === 'dark')

  /**
   * Apply the current isDark value to the DOM and persist it to localStorage.
   *
   * Sets `data-theme="dark"` or `data-theme="light"` on <html>.
   * All CSS custom properties are keyed off this attribute, so the entire
   * colour system switches in a single synchronous DOM write.
   */
  function applyTheme() {
    document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  }

  /**
   * Toggle between dark and light themes.
   *
   * Flips isDark, then calls applyTheme() to update the DOM and storage.
   * Bound to the theme toggle button in AppNavbar and the larger toggle in
   * SettingsView.
   */
  function toggle() {
    isDark.value = !isDark.value
    applyTheme()
  }

  // Apply the stored preference immediately when the store is first used,
  // before any components render, to avoid a flash of the default theme.
  applyTheme()

  return { isDark, toggle }
})
