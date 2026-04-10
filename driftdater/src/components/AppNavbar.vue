<!--
  components/AppNavbar.vue
  ------------------------
  Persistent top navigation bar rendered on every page.

  Features
  --------
  - Brand logo linking to the home page.
  - Navigation links (Discover, Matches, Messages, Search, Favorites) shown
    only when the user is authenticated.
  - Right-side controls: theme toggle, Profile link, Logout button (auth) or
    Login/Sign Up buttons (guest).
  - Active link highlighting via Vue Router's `active-class`.

  Theme Toggle (Optional Feature 2)
  ----------------------------------
  A small toggle button in the nav bar switches between light and dark themes.
  It calls themeStore.toggle() which updates the data-theme attribute on <html>
  and persists the preference to localStorage.
  The sun/moon emoji updates to reflect the current theme.

  Responsive
  ----------
  On small screens the nav links collapse — handled via CSS media queries in
  main.css.  The brand and actions remain visible.
-->

<script setup>
import { computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'

const auth   = useAuthStore()
const theme  = useThemeStore()
const router = useRouter()

/** True when a user is currently logged in for this tab. */
const isLoggedIn = computed(() => !!auth.user)

/**
 * Log out the current user, clear the tab's token, and navigate to home.
 */
async function handleLogout() {
  await auth.logout()
  router.push('/')
}
</script>

<template>
  <nav class="navbar">
    <!-- Brand -->
    <RouterLink to="/" class="navbar-brand">
      💫 DriftDater
    </RouterLink>

    <!-- Authenticated navigation links -->
    <div class="navbar-links" v-if="isLoggedIn">
      <RouterLink to="/dashboard" class="nav-link" active-class="active">Discover</RouterLink>
      <RouterLink to="/matches"   class="nav-link" active-class="active">Matches</RouterLink>
      <RouterLink to="/messages"  class="nav-link" active-class="active">Messages</RouterLink>
      <RouterLink to="/search"    class="nav-link" active-class="active">Search</RouterLink>
      <RouterLink to="/favorites" class="nav-link" active-class="active">Favorites</RouterLink>
    </div>

    <!-- Right-side actions -->
    <div class="nav-actions">
      <!--
        Dark Mode Toggle — Optional Feature 2.
        Pressing this calls theme.toggle() which flips isDark and sets the
        data-theme attribute on <html>, causing all CSS variables to switch.
        Title attribute provides accessibility context.
      -->
      <button
        class="theme-toggle"
        @click="theme.toggle"
        :title="theme.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
        style="position:relative"
      >
        <span style="position:absolute;left:4px;top:2px;font-size:11px;pointer-events:none">
          {{ theme.isDark ? '🌙' : '☀️' }}
        </span>
      </button>

      <!-- Authenticated actions -->
      <template v-if="isLoggedIn">
        <RouterLink to="/profile"  class="nav-link" active-class="active">Profile</RouterLink>
        <RouterLink to="/settings" class="nav-link" active-class="active">Settings</RouterLink>
        <button class="btn btn-outline btn-sm" @click="handleLogout">Logout</button>
      </template>

      <!-- Guest actions -->
      <template v-else>
        <RouterLink to="/login"    class="btn btn-outline btn-sm">Login</RouterLink>
        <RouterLink to="/register" class="btn btn-primary btn-sm">Sign Up</RouterLink>
      </template>
    </div>
  </nav>
</template>
