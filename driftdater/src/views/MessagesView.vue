import { API } from '../config.js'
<script setup>
/*
 * MessagesView — Conversation inbox.
 * Fetches GET /api/v1/conversations. Shows avatar, name, last message,
 * relative timestamp (timeAgo), and unread badge. Blocked users excluded.
 */
import { ref, onMounted } from 'vue'
import axios from 'axios'

const conversations = ref([])
const loading = ref(true)

function photoUrl(photo) { return photo ? `${API}/uploads/${photo}` : null }
function initials(p) { return ((p.first_name?.[0]||'')+(p.last_name?.[0]||'')).toUpperCase() }
function timeAgo(dt) {
  if (!dt) return ''
  const d = new Date(dt), now = new Date()
  const diff = Math.floor((now - d) / 60000)
  if (diff < 1) return 'just now'
  if (diff < 60) return `${diff}m ago`
  if (diff < 1440) return `${Math.floor(diff/60)}h ago`
  return d.toLocaleDateString()
}

onMounted(async () => {
  try {
    const res = await axios.get(`${API}/conversations`, { withCredentials: true })
    conversations.value = res.data.conversations
  } catch {} finally { loading.value = false }
})
</script>

<template>
  <div class="container" style="padding-bottom:3rem">
    <div class="page-header">
      <div class="page-title">Messages</div>
      <div class="page-subtitle">Your conversations with matches</div>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <div v-else-if="conversations.length === 0" class="empty-state">
      <div class="empty-state-icon">💬</div>
      <h3>No conversations yet</h3>
      <p>Get some mutual matches first, then start chatting!</p>
      <RouterLink to="/matches" class="btn btn-primary mt-2">View Matches</RouterLink>
    </div>

    <div v-else class="card" style="overflow:hidden">
      <RouterLink
        v-for="c in conversations"
        :key="c.user.id"
        :to="`/messages/${c.user.id}`"
        class="convo-item"
        style="text-decoration:none;color:var(--text-primary)"
      >
        <div>
          <img v-if="photoUrl(c.user.profile_photo)" :src="photoUrl(c.user.profile_photo)" class="avatar" />
          <div v-else class="avatar-placeholder">{{ initials(c.user) }}</div>
        </div>
        <div style="flex:1;min-width:0">
          <div class="flex items-center justify-between">
            <span class="font-semibold">{{ c.user.first_name }} {{ c.user.last_name }}</span>
            <span class="text-muted text-sm time-text">
              {{ c.last_message ? timeAgo(c.last_message.created_at) : '' }}
            </span>
          </div>
          <div class="text-sm text-secondary" style="overflow:hidden;white-space:nowrap;text-overflow:ellipsis;margin-top:0.2rem">
            {{ c.last_message ? c.last_message.content : 'No messages yet' }}
          </div>
        </div>
        <div v-if="c.unread_count > 0" class="unread-badge">{{ c.unread_count }}</div>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
/* Ensure time-ago text uses the muted variable, not inherited link color */
.time-text {
  color: var(--text-muted) !important;
  white-space: nowrap;
  margin-left: 0.5rem;
}
</style>
