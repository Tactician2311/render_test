<script setup>
import { API } from '../config.js'
/*
 * MatchesView — Mutual matches list.
 * Fetches GET /api/v1/matches. Each match shows score, bio, interests,
 * and action buttons: Message, View Profile, Block/Report.
 */
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import ReportModal from '../components/ReportModal.vue'

const router = useRouter()
const matches = ref([])
const loading = ref(true)

const showReportModal = ref(false)
const reportTarget = ref(null)
function openReport(m) { reportTarget.value = m; showReportModal.value = true }
function closeReport() { showReportModal.value = false; reportTarget.value = null }

function photoUrl(p) { return p ? `${API}/uploads/${p}` : null }
function initials(p) { return ((p.first_name?.[0]||'')+(p.last_name?.[0]||'')).toUpperCase() }

onMounted(async () => {
  try {
    const res = await axios.get(`${API}/matches`, { withCredentials: true })
    matches.value = res.data.matches
  } catch {} finally { loading.value = false }
})
</script>

<template>
  <div class="container" style="padding-bottom:3rem">
    <ReportModal v-if="showReportModal && reportTarget" :target="reportTarget" @close="closeReport" />

    <div class="page-header">
      <div class="page-title">Your Matches</div>
      <div class="page-subtitle">{{ matches.length }} mutual connections</div>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <div v-else-if="matches.length === 0" class="empty-state">
      <div class="empty-state-icon">💔</div>
      <h3>No matches yet</h3>
      <p>Keep liking profiles — when someone likes you back they'll appear here!</p>
      <RouterLink to="/dashboard" class="btn btn-primary mt-2">Discover People</RouterLink>
    </div>

    <div v-else class="matches-list">
      <div v-for="match in matches" :key="match.id" class="match-item card">
        <div class="match-photo" @click="router.push(`/profile/${match.id}`)" style="cursor:pointer">
          <img v-if="photoUrl(match.profile_photo)" :src="photoUrl(match.profile_photo)" class="avatar avatar-lg" />
          <div v-else class="avatar-placeholder avatar-lg" style="font-size:1.5rem">{{ initials(match) }}</div>
        </div>
        <div class="match-info" @click="router.push(`/profile/${match.id}`)" style="cursor:pointer;flex:1">
          <div class="match-name">{{ match.first_name }} {{ match.last_name }}<span v-if="match.age" class="text-muted">, {{ match.age }}</span></div>
          <div class="text-secondary text-sm" v-if="match.location">📍 {{ match.location }}</div>
          <div class="match-bio text-sm" v-if="match.bio">{{ match.bio }}</div>
          <div class="tags-list" v-if="match.interests?.length" style="margin-top:0.4rem">
            <span v-for="i in match.interests.slice(0,4)" :key="i" class="tag">{{ i }}</span>
          </div>
          <div class="match-score-badge" style="margin-top:0.5rem">✨ {{ match.match_score }}% Match</div>
        </div>
        <div class="match-actions">
          <button class="btn btn-primary btn-sm" @click.stop="router.push(`/messages/${match.id}`)">💬 Message</button>
          <button class="btn btn-outline btn-sm" @click.stop="router.push(`/profile/${match.id}`)">View Profile</button>
          <!-- Block/Report button -->
          <button class="btn btn-sm block-report-btn" @click.stop="openReport(match)">🚫 Block / Report</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.matches-list { display: flex; flex-direction: column; gap: 1rem; }
.match-item { display: flex; gap: 1.25rem; padding: 1.25rem; align-items: flex-start; }
.match-name { font-weight: 700; font-size: 1.05rem; }
.match-bio { color: var(--text-secondary); margin-top: 0.2rem; display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden; }
.match-actions { display: flex; flex-direction: column; gap: 0.5rem; align-items: stretch; min-width: 130px; }
.block-report-btn { background: rgba(239,68,68,0.1); color: var(--dislike-color); border: 1.5px solid rgba(239,68,68,0.25); }
.block-report-btn:hover { background: #ef4444; color: white; }
@media (max-width:600px) { .match-item { flex-wrap: wrap; } .match-actions { flex-direction: row; min-width: unset; } }
</style>
