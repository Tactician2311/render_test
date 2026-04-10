/**
 * main.js
 * -------
 * Application entry point for the DriftDater Vue 3 frontend.
 *
 * Bootstraps the Vue application by:
 *   1. Creating the root Vue app instance from App.vue.
 *   2. Installing Pinia (state management) — must be installed before any
 *      store is accessed, including inside the router guard.
 *   3. Installing Vue Router.
 *   4. Importing the global CSS stylesheet.
 *   5. Mounting the app to the #app div in index.html.
 *
 * Plugin Order
 * ------------
 * Pinia must be registered before Vue Router because the router's
 * beforeEach guard calls useAuthStore(), which requires Pinia to be active.
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'   // Global CSS variables, dark mode, utility classes

const app = createApp(App)

app.use(createPinia())   // Register Pinia before router (router guard uses auth store)
app.use(router)

app.mount('#app')
