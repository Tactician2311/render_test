<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  if (!email.value || !password.value) { error.value = 'Please fill in all fields'; return }
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.error || 'Login failed. Please try again.'
  } finally { loading.value = false }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <h1>Login</h1>
        <p>Welcome back to DriftDater</p>
      </div>
      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <div class="form-group">
        <label class="form-label">Email</label>
        <input v-model="email" type="email" class="form-control" placeholder="your@email.com" @keyup.enter="handleLogin" />
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input v-model="password" type="password" class="form-control" placeholder="••••••••••" @keyup.enter="handleLogin" />
      </div>
      <button class="btn btn-primary btn-full" @click="handleLogin" :disabled="loading">
        {{ loading ? 'Signing in...' : 'Login' }}
      </button>
      <p class="auth-footer">Don't have an account? <RouterLink to="/register">Sign up here</RouterLink></p>
    </div>
  </div>
</template>

<style scoped>
.auth-page { min-height: calc(100vh - 64px); display: flex; align-items: center; justify-content: center; padding: 2rem; background: var(--bg-primary); }
.auth-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 24px; padding: 2.5rem; width: 100%; max-width: 420px; box-shadow: var(--shadow-lg); }
.auth-header { text-align: center; margin-bottom: 2rem; }
.auth-header h1 { font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.auth-header p { color: var(--text-secondary); margin-top: 0.25rem; }
.auth-footer { text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--text-secondary); }
.auth-footer a { color: var(--accent); text-decoration: none; font-weight: 600; }
</style>
