import { API } from './config.js'
<script setup>
/*
 * SettingsView — Application settings.
 * Section 1: Dark Mode toggle (Optional Feature 2) — calls theme.toggle().
 * Section 2: Blocked Users (Optional Feature 1) — GET /api/v1/blocks,
 *            unblock via DELETE /api/v1/blocks/:id.
 * Section 3: Account info, Edit Profile link, Logout.
 */
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useThemeStore } from '../stores/theme'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const theme = useThemeStore()
const auth = useAuthStore()
const router = useRouter()

const blockedUsers = ref([])
const loadingBlocks = ref(true)
const unblockingId = ref(null)
const unblockSuccess = ref('')

async function loadBlocks() {
  loadingBlocks.value = true
  try {
    const res = await axios.get(`${API}/blocks`, { withCredentials: true })
    blockedUsers.value = res.data.blocked_users
  } catch {} finally { loadingBlocks.value = false }
}

async function unblock(userId, name) {
  unblockingId.value = userId
  try {
    await axios.delete(`${API}/blocks/${userId}`, { withCredentials: true })
    blockedUsers.value = blockedUsers.value.filter(u => u.id !== userId)
    unblockSuccess.value = `${name} has been unblocked.`
    setTimeout(() => unblockSuccess.value = '', 3000)
  } catch {} finally { unblockingId.value = null }
}

async function handleLogout() {
  await auth.logout()
  router.push('/')
}

function photoUrl(photo) { return photo ? `${API}/uploads/${photo}` : null }
function initials(u) { return ((u.first_name?.[0]||'')+(u.last_name?.[0]||'')).toUpperCase() }

onMounted(loadBlocks)
</script>

<template>
  <div class="container" style="max-width:680px;padding-bottom:3rem">
    <div class="page-header">
      <div class="page-title">Settings</div>
    </div>

    <!-- ── Dark Mode (Optional Feature 2) ── -->
    <div class="settings-card">
      <div class="settings-section-title">🌙 Appearance</div>
      <div class="setting-row">
        <div>
          <div class="setting-label">Dark Mode</div>
          <div class="setting-desc">Switch between light and dark themes. Your preference is saved automatically.</div>
        </div>
        <button class="theme-toggle-big" @click="theme.toggle" :class="{ active: theme.isDark }">
          <span class="toggle-knob">{{ theme.isDark ? '🌙' : '☀️' }}</span>
        </button>
      </div>
      <div class="theme-preview">
        <span class="theme-pill" :class="{ active: !theme.isDark }" @click="!theme.isDark || theme.toggle()">☀️ Light</span>
        <span class="theme-pill dark" :class="{ active: theme.isDark }" @click="theme.isDark || theme.toggle()">🌙 Dark</span>
      </div>
    </div>

    <!-- ── Block Management (Optional Feature 1) ── -->
    <div class="settings-card" style="margin-top:1.25rem">
      <div class="settings-section-title">🚫 Blocked Users</div>
      <p class="text-secondary text-sm" style="margin-bottom:1rem">
        Blocked users don't appear in your Discover feed, can't message you, and won't see your profile.
        You can block someone from their profile or when reporting them.
      </p>

      <div v-if="unblockSuccess" class="alert alert-success">{{ unblockSuccess }}</div>

      <div v-if="loadingBlocks" class="loading-center" style="padding:1.5rem">
        <div class="spinner" style="width:28px;height:28px;border-width:2px"></div>
        <span class="text-secondary text-sm">Loading blocked users...</span>
      </div>

      <div v-else-if="blockedUsers.length === 0" class="empty-blocks">
        <span style="font-size:2rem">✅</span>
        <p class="text-secondary text-sm">You haven't blocked anyone.</p>
      </div>

      <div v-else class="blocked-list">
        <div v-for="u in blockedUsers" :key="u.id" class="blocked-item">
          <div class="blocked-avatar">
            <img v-if="photoUrl(u.profile_photo)" :src="photoUrl(u.profile_photo)" class="avatar avatar-sm" />
            <div v-else class="avatar-placeholder avatar-sm" style="font-size:0.8rem">{{ initials(u) }}</div>
          </div>
          <div class="blocked-info">
            <div class="font-semibold">{{ u.first_name }} {{ u.last_name }}</div>
            <div class="text-secondary text-sm" v-if="u.location">📍 {{ u.location }}</div>
          </div>
          <button
            class="btn btn-outline btn-sm unblock-btn"
            @click="unblock(u.id, u.first_name)"
            :disabled="unblockingId === u.id"
          >
            {{ unblockingId === u.id ? 'Unblocking...' : 'Unblock' }}
          </button>
        </div>
      </div>

      <p class="hint-text">
        💡 To block someone: go to their profile or click ⚑ Report on any profile card and check "Also block this user".
      </p>
    </div>

    <!-- ── Account ── -->
    <div class="settings-card" style="margin-top:1.25rem">
      <div class="settings-section-title">👤 Account</div>
      <div class="setting-row" style="margin-bottom:1rem">
        <div>
          <div class="setting-label">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</div>
          <div class="setting-desc">{{ auth.user?.email }} · @{{ auth.user?.username }}</div>
        </div>
        <RouterLink to="/profile" class="btn btn-outline btn-sm">Edit Profile</RouterLink>
      </div>
      <hr class="divider" style="margin:0.75rem 0" />
      <button class="btn btn-danger btn-sm" @click="handleLogout">Logout</button>
    </div>
  </div>
</template>

<style scoped>
.settings-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
}
.settings-section-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.15rem; font-weight: 700;
  margin-bottom: 1.25rem;
  color: var(--text-primary);
}
.setting-row { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.setting-label { font-weight: 600; font-size: 0.95rem; }
.setting-desc { color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.15rem; }

/* Theme toggle */
.theme-toggle-big {
  width: 64px; height: 34px; border-radius: 17px;
  background: var(--border); border: none; cursor: pointer;
  position: relative; transition: background 0.3s; flex-shrink: 0;
}
.theme-toggle-big.active { background: var(--accent); }
.toggle-knob {
  position: absolute; top: 5px; left: 5px;
  width: 24px; height: 24px; border-radius: 50%;
  background: white; display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; transition: transform 0.3s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.25);
}
.theme-toggle-big.active .toggle-knob { transform: translateX(30px); }
.theme-preview {
  display: flex; gap: 0.5rem; margin-top: 1rem;
}
.theme-pill {
  padding: 0.3rem 0.9rem; border-radius: 20px; font-size: 0.8rem;
  cursor: pointer; border: 1.5px solid var(--border);
  color: var(--text-secondary); transition: all 0.2s;
}
.theme-pill.active { border-color: var(--accent); color: var(--accent); font-weight: 600; background: var(--border-light); }

/* Blocked users */
.empty-blocks { text-align: center; padding: 1.5rem; display: flex; flex-direction: column; align-items: center; gap: 0.5rem; }
.blocked-list { display: flex; flex-direction: column; gap: 0.6rem; margin-bottom: 1rem; }
.blocked-item {
  display: flex; align-items: center; gap: 0.875rem;
  padding: 0.75rem 1rem;
  background: var(--bg-primary); border-radius: 12px;
  border: 1px solid var(--border);
}
.blocked-info { flex: 1; }
.unblock-btn { color: var(--like-color) !important; border-color: var(--like-color) !important; }
.unblock-btn:hover { background: var(--like-color) !important; color: white !important; }
.hint-text {
  margin-top: 0.75rem; font-size: 0.8rem;
  color: var(--text-muted); line-height: 1.5;
  padding: 0.75rem; background: var(--border-light);
  border-radius: 8px;
}
</style>
