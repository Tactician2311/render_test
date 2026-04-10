import { API } from './config.js'
<script setup>
/*
 * ConversationView — Individual chat thread.
 * Polls GET /api/v1/messages/:id every 4 seconds for near-real-time updates.
 * Polling stops on 403 block response. Blocked state shows a notice with
 * a link to Settings to unblock.
 */
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const auth = useAuthStore()
const otherId = parseInt(route.params.id)

const messages = ref([])
const otherUser = ref(null)
const newMsg = ref('')
const loading = ref(true)
const sendError = ref('')
const blocked = ref(false)   // true if a block exists between these two users
const messagesEnd = ref(null)
let pollInterval = null

function photoUrl(photo) { return photo ? `${API}/uploads/${photo}` : null }
function initials(p) { if (!p) return '?'; return ((p.first_name?.[0]||'')+(p.last_name?.[0]||'')).toUpperCase() }
function formatTime(dt) { return dt ? new Date(dt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '' }

async function loadMessages() {
  try {
    const res = await axios.get(`${API}/messages/${otherId}`, { withCredentials: true })
    messages.value = res.data.messages
    blocked.value = false
    await nextTick()
    messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
  } catch (e) {
    if (e.response?.status === 403 && e.response?.data?.error?.includes('blocked')) {
      blocked.value = true
      if (pollInterval) clearInterval(pollInterval) // stop polling if blocked
    }
  }
}

async function loadUser() {
  try {
    const res = await axios.get(`${API}/profiles/${otherId}`, { withCredentials: true })
    otherUser.value = res.data.user
  } catch {}
}

async function sendMessage() {
  const content = newMsg.value.trim()
  if (!content) return
  sendError.value = ''
  try {
    const res = await axios.post(`${API}/messages/${otherId}`, { content }, { withCredentials: true })
    newMsg.value = ''
    messages.value.push(res.data.message)
    await nextTick()
    messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
  } catch (e) {
    if (e.response?.status === 403) {
      sendError.value = e.response.data.error || 'You cannot send messages to this user.'
      blocked.value = e.response.data.error?.includes('blocked')
    } else {
      sendError.value = 'Failed to send message. Please try again.'
    }
  }
}

onMounted(async () => {
  await Promise.all([loadUser(), loadMessages()])
  loading.value = false
  if (!blocked.value) {
    pollInterval = setInterval(loadMessages, 4000)
  }
})
onUnmounted(() => { if (pollInterval) clearInterval(pollInterval) })
</script>

<template>
  <div class="container" style="padding-bottom:1rem">
    <!-- Header -->
    <div class="chat-header card" style="margin-top:0.5rem;padding:1rem 1.25rem;display:flex;align-items:center;gap:1rem">
      <RouterLink to="/messages" class="btn btn-outline btn-sm">← Back</RouterLink>
      <div v-if="otherUser" style="display:flex;align-items:center;gap:0.75rem;flex:1">
        <img v-if="photoUrl(otherUser.profile_photo)" :src="photoUrl(otherUser.profile_photo)" class="avatar" />
        <div v-else class="avatar-placeholder">{{ initials(otherUser) }}</div>
        <div>
          <div class="font-semibold">{{ otherUser.first_name }} {{ otherUser.last_name }}</div>
          <div class="text-sm text-secondary" v-if="otherUser.location">📍 {{ otherUser.location }}</div>
        </div>
      </div>
      <RouterLink v-if="otherUser" :to="`/profile/${otherUser.id}`" class="btn btn-outline btn-sm">View Profile</RouterLink>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>

    <div v-else class="chat-window card" style="margin-top:1rem">
      <!-- Blocked state -->
      <div v-if="blocked" class="blocked-notice">
        <span style="font-size:2rem">🚫</span>
        <div>
          <div class="font-semibold">Messaging unavailable</div>
          <div class="text-secondary text-sm" style="margin-top:0.25rem">
            You cannot send or receive messages with this user because a block exists between you.
            To restore messaging, go to <RouterLink to="/settings" style="color:var(--accent)">Settings → Blocked Users</RouterLink> and unblock them.
          </div>
        </div>
      </div>

      <!-- Normal chat -->
      <template v-else>
        <div class="messages-container" style="max-height:55vh">
          <div v-if="messages.length === 0" class="empty-state" style="padding:2rem">
            <p>No messages yet. Say hi! 👋</p>
          </div>
          <div v-for="m in messages" :key="m.id" :class="['msg-row', m.sender_id === auth.user?.id ? 'sent' : 'received']">
            <div class="message-bubble" :class="m.sender_id === auth.user?.id ? 'sent' : 'received'">
              {{ m.content }}
            </div>
            <div class="message-time" :style="m.sender_id === auth.user?.id ? 'text-align:right' : ''">
              {{ formatTime(m.created_at) }}
            </div>
          </div>
          <div ref="messagesEnd"></div>
        </div>

        <!-- Send error -->
        <div v-if="sendError" class="alert alert-error" style="margin:0.5rem 1rem 0">{{ sendError }}</div>

        <!-- Input -->
        <div class="chat-input-row">
          <input
            v-model="newMsg"
            class="form-control"
            placeholder="Type a message..."
            @keyup.enter="sendMessage"
            style="flex:1"
          />
          <button class="btn btn-primary" @click="sendMessage" :disabled="!newMsg.trim()">Send</button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.msg-row { display: flex; flex-direction: column; }
.msg-row.sent { align-items: flex-end; }
.msg-row.received { align-items: flex-start; }
.chat-input-row { display: flex; gap: 0.75rem; padding: 1rem; border-top: 1px solid var(--border); }
.blocked-notice {
  display: flex; gap: 1rem; align-items: flex-start;
  padding: 2rem; background: rgba(239,68,68,0.1);
  border-radius: 0 0 16px 16px;
}
[data-theme="dark"] .blocked-notice { background: rgba(239,68,68,0.12); }
</style>
