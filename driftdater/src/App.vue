<!--
  App.vue
  -------
  Root component of the DriftDater Vue application.

  Responsibilities
  ----------------
  - Renders the persistent AppNavbar at the top of every page.
  - Renders the current route's component via <RouterView> inside <main>.
  - On mount, calls auth.checkAuth() to validate the stored JWT and restore
    the user's session state before any child component renders.

  Layout
  ------
  <AppNavbar>  — Fixed top navigation bar (height: 64px).
  <main>       — Scrollable page content. Padded from top in main.css to
                 clear the fixed navbar (padding-top: 80px).
  <RouterView> — Swapped out by Vue Router to show the active page component.

  Theme
  -----
  The ThemeStore is imported to ensure the theme store is initialised and the
  correct `data-theme` attribute is applied to <html> before the first render,
  preventing a flash of the default (light) theme on a user who prefers dark.
-->

<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import AppNavbar from './components/AppNavbar.vue'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'

const auth  = useAuthStore()
const theme = useThemeStore()  // Initialises theme store — applies data-theme attribute

/**
 * On mount, validate the JWT stored in sessionStorage.
 * checkAuth() hits GET /api/v1/auth/status with the stored token.
 * If valid, auth.user is populated; if invalid/expired, auth.user stays null.
 */
onMounted(() => {
  auth.checkAuth()
})
</script>

<template>
  <AppNavbar />

  <main>
    <RouterView />
  </main>
</template>
