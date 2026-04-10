import { API } from './config.js'
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import ReportModal from '../components/ReportModal.vue'

const route = useRoute()
const profile = ref(null)
const loading = ref(true)

const showReportModal = ref(false)
function openReport() { showReportModal.value = true }
function closeReport() { showReportModal.value = false }

const swipeMsg = ref('')
const swipeMsgType = ref('success')

function photoUrl(p) { return p ? `${API}/uploads/${p}` : null }
function initials(p) { return ((p?.first_name?.[0]||'')+(p?.last_name?.[0]||'')).toUpperCase() }

async function swipe(action) {
  try {
    const res = await axios.post(`${API}/swipe`, { target_id: profile.value.id, action }, { withCredentials: true })
    if (action === 'like') {
      swipeMsg.value = res.data.is_match ? "🎉 It's a match! Head to Messages to chat." : "❤️ Liked!"
    } else {
      swipeMsg.value = action === 'dislike' ? '👎 Disliked' : '⏭ Passed'
    }
    swipeMsgType.value = 'success'
  } catch (e) {
    swipeMsg.value = e.response?.data?.error || 'Action failed'
    swipeMsgType.value = 'error'
  }
}

async function addFavorite() {
  try {
    await axios.post(`${API}/favorites/${profile.value.id}`, {}, { withCredentials: true })
    swipeMsg.value = '⭐ Added to favorites!'
    swipeMsgType.value = 'success'
  } catch {}
}

onMounted(async () => {
  try {
    const res = await axios.get(`${API}/profiles/${route.params.id}`, { withCredentials: true })
    profile.value = res.data.user
  } catch {} finally { loading.value = false }
})
</script>

<template>
  <div class="container" style="max-width:680px;padding-bottom:3rem">
    <ReportModal v-if="showReportModal && profile" :target="profile" @close="closeReport"
      @done="swipeMsg = profile.first_name + ' has been reported.'; swipeMsgType = 'success'" />

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <div v-else-if="!profile" class="empty-state"><h3>Profile not found</h3></div>
    <div v-else>
      <div class="page-header flex items-center justify-between">
        <button class="btn btn-outline btn-sm" @click="$router.back()">← Back</button>
      </div>

      <div v-if="swipeMsg" :class="`alert alert-${swipeMsgType}`" style="margin-bottom:1rem">{{ swipeMsg }}</div>

      <div class="card" style="overflow:hidden">
        <div style="position:relative">
          <img v-if="photoUrl(profile.profile_photo)" :src="photoUrl(profile.profile_photo)"
            style="width:100%;max-height:380px;object-fit:cover" />
          <div v-else style="height:240px;background:var(--border-light);display:flex;align-items:center;justify-content:center">
            <div class="avatar-placeholder" style="width:110px;height:110px;font-size:2.5rem">{{ initials(profile) }}</div>
          </div>
          <div v-if="profile.match_score !== undefined" class="score-badge">✨ {{ profile.match_score }}% Match</div>
        </div>

        <div class="card-body">
          <h2 class="font-serif" style="font-size:1.75rem">
            {{ profile.first_name }} {{ profile.last_name }}
            <span v-if="profile.age" style="font-size:1.2rem;font-weight:400">, {{ profile.age }}</span>
          </h2>
          <p class="text-secondary mt-1" v-if="profile.location">📍 {{ profile.location }}</p>
          <p class="text-secondary text-sm" v-if="profile.occupation">💼 {{ profile.occupation }}</p>
          <p class="text-secondary text-sm" v-if="profile.education">🎓 {{ profile.education }}</p>

          <hr class="divider" />
          <div v-if="profile.bio">
            <div class="form-label">About</div>
            <p style="line-height:1.7">{{ profile.bio }}</p>
          </div>
          <div class="mt-2" v-if="profile.interests?.length">
            <div class="form-label">Interests</div>
            <div class="tags-list"><span v-for="i in profile.interests" :key="i" class="tag">{{ i }}</span></div>
          </div>

          <hr class="divider" />

          <!-- Swipe actions -->
          <div class="action-grid">
            <button class="btn btn-dislike" @click="swipe('dislike')">✕ Dislike</button>
            <button class="btn btn-pass"    @click="swipe('pass')">Pass</button>
            <button class="btn btn-like"    @click="swipe('like')">♥ Like</button>
            <button class="btn btn-outline" @click="addFavorite">☆ Favorite</button>
          </div>

          <hr class="divider" />

          <!-- Block/Report — clearly visible button -->
          <div class="report-section">
            <p class="text-muted text-sm">Something wrong with this profile?</p>
            <button class="btn block-report-btn" @click="openReport()">
              🚫 Block / Report {{ profile.first_name }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.score-badge {
  position:absolute; bottom:12px; right:12px;
  background: var(--accent-gradient); color:white;
  padding:0.3rem 0.8rem; border-radius:20px;
  font-size:0.8rem; font-weight:600;
}
.action-grid { display:flex; gap:0.75rem; flex-wrap:wrap; }
.report-section { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:0.75rem; }
.block-report-btn { background: rgba(239,68,68,0.1); color: var(--dislike-color); border: 1.5px solid rgba(239,68,68,0.25); }
.block-report-btn:hover { background:#ef4444; color:white; }
</style>
