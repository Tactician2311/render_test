<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const error = ref('')
const loading = ref(false)

const form = ref({
  email: '', username: '', first_name: '', last_name: '',
  date_of_birth: '', gender: '', looking_for: 'any', password: ''
})

async function handleRegister() {
  error.value = ''
  const required = ['email','username','first_name','last_name','password']
  for (const f of required) {
    if (!form.value[f]) { error.value = `${f.replace('_',' ')} is required`; return }
  }
  if (form.value.password.length < 6) { error.value = 'Password must be at least 6 characters'; return }
  loading.value = true
  try {
    await auth.register(form.value)
    router.push('/profile')
  } catch (e) {
    error.value = e.response?.data?.error || 'Registration failed. Please try again.'
  } finally { loading.value = false }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <h1>Sign Up</h1>
        <p>Join DriftDater today</p>
      </div>
      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <div class="form-group">
        <label class="form-label">Email</label>
        <input v-model="form.email" type="email" class="form-control" placeholder="your@email.com" />
      </div>
      <div class="form-group">
        <label class="form-label">Username</label>
        <input v-model="form.username" type="text" class="form-control" placeholder="username" />
      </div>
      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">First Name</label>
          <input v-model="form.first_name" type="text" class="form-control" placeholder="First Name" />
        </div>
        <div class="form-group">
          <label class="form-label">Last Name</label>
          <input v-model="form.last_name" type="text" class="form-control" placeholder="Last Name" />
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Date of Birth</label>
        <input v-model="form.date_of_birth" type="date" class="form-control" />
      </div>
      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">Gender</label>
          <select v-model="form.gender" class="form-control">
            <option value="">Select gender</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="non-binary">Non-binary</option>
            <option value="other">Other</option>
            <option value="prefer-not-to-say">Prefer not to say</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Looking For</label>
          <select v-model="form.looking_for" class="form-control">
            <option value="any">Any</option>
            <option value="male">Men</option>
            <option value="female">Women</option>
            <option value="non-binary">Non-binary</option>
          </select>
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input v-model="form.password" type="password" class="form-control" placeholder="Password (min 6 chars)" />
      </div>
      <button class="btn btn-primary btn-full" @click="handleRegister" :disabled="loading">
        {{ loading ? 'Creating account...' : 'Sign Up' }}
      </button>
      <p class="auth-footer">Already have an account? <RouterLink to="/login">Login here</RouterLink></p>
    </div>
  </div>
</template>

<style scoped>
.auth-page { min-height: calc(100vh - 64px); display: flex; align-items: center; justify-content: center; padding: 2rem; background: var(--bg-primary); }
.auth-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 24px; padding: 2.5rem; width: 100%; max-width: 480px; box-shadow: var(--shadow-lg); }
.auth-header { text-align: center; margin-bottom: 2rem; }
.auth-header h1 { font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.auth-header p { color: var(--text-secondary); margin-top: 0.25rem; }
.auth-footer { text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--text-secondary); }
.auth-footer a { color: var(--accent); text-decoration: none; font-weight: 600; }
</style>
