import { API } from './config.js'
<script setup>
/*
 * SearchView — Search and discover profiles.
 * Debounced (400ms) input queries GET /api/v1/search?q=. Each result
 * has an inline Like button and a Block/Report button. Blocked users excluded.
 */
import { ref, watch } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import ReportModal from '../components/ReportModal.vue'

const router = useRouter()
const query = ref('')
const results = ref([])
const loading = ref(false)

const showReportModal = ref(false)
const reportTarget = ref(null)
function openReport(e, p) { e.stopPropagation(); reportTarget.value = p; showReportModal.value = true }
function closeReport() { showReportModal.value = false; reportTarget.value = null }

function photoUrl(p) { return p ? `${API}/uploads/${p}` : null }
function initials(p) { return ((p.first_name?.[0]||'')+(p.last_name?.[0]||'')).toUpperCase() }

async function doSearch() {
  loading.value = true
  try {
    const res = await axios.get(`${API}/search`, { params: { q: query.value }, withCredentials: true })
    results.value = res.data.results
  } catch {} finally { loading.value = false }
}

async function swipe(e, action, profile) {
  e.stopPropagation()
  try { await axios.post(`${API}/swipe`, { target_id: profile.id, action }, { withCredentials: true }) } catch {}
}

let debounce = null
watch(query, () => { clearTimeout(debounce); debounce = setTimeout(doSearch, 400) })
</script>

<template>
  <div class="container" style="padding-bottom:3rem">
    <ReportModal v-if="showReportModal && reportTarget" :target="reportTarget" @close="closeReport" />

    <div class="page-header">
      <div class="page-title">Search & Discover</div>
      <div class="page-subtitle">Find people by name, bio, or location</div>
    </div>

    <div class="search-bar card card-body" style="margin-bottom:1.5rem">
      <div class="flex gap-2 items-center">
        <span style="font-size:1.2rem">🔍</span>
        <input
          v-model="query" type="text"
          class="form-control"
          placeholder="Search by name, bio, or location..."
          style="flex:1;border:none;background:transparent;padding:0.25rem 0;font-size:1rem;outline:none;color:var(--text-primary)"
        />
        <span v-if="loading" class="spinner" style="width:20px;height:20px;border-width:2px;margin:0"></span>
      </div>
    </div>

    <div v-if="!query" class="empty-state">
      <div class="empty-state-icon">✨</div>
      <h3>Search for someone</h3>
      <p>Start typing to find people by name, bio, or location</p>
    </div>
    <div v-else-if="results.length === 0 && !loading" class="empty-state">
      <div class="empty-state-icon">🔍</div>
      <h3>No results found</h3>
      <p>Try a different name or location</p>
    </div>
    <div v-else class="results-list">
      <div
        v-for="p in results"
        :key="p.id"
        class="result-item card"
        @click="router.push(`/profile/${p.id}`)"
        style="cursor:pointer"
      >
        <div>
          <img v-if="photoUrl(p.profile_photo)" :src="photoUrl(p.profile_photo)" class="avatar avatar-lg" />
          <div v-else class="avatar-placeholder avatar-lg" style="font-size:1.4rem">{{ initials(p) }}</div>
        </div>
        <div class="result-info">
          <div class="font-semibold">{{ p.first_name }} {{ p.last_name }}<span v-if="p.age" class="text-muted">, {{ p.age }}</span></div>
          <div class="text-secondary text-sm" v-if="p.location">📍 {{ p.location }}</div>
          <div class="text-secondary text-sm" style="display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden" v-if="p.bio">{{ p.bio }}</div>
          <div class="tags-list" v-if="p.interests?.length" style="margin-top:0.3rem">
            <span v-for="i in p.interests.slice(0,3)" :key="i" class="tag">{{ i }}</span>
          </div>
        </div>
        <div class="result-actions" @click.stop>
          <div class="match-score-badge" v-if="p.match_score">✨ {{ p.match_score }}%</div>
          <button class="btn btn-like btn-sm" @click.stop="swipe($event, 'like', p)">♥ Like</button>
          <button class="btn btn-sm block-report-btn" @click.stop="openReport($event, p)">🚫 Block / Report</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.results-list { display: flex; flex-direction: column; gap: 0.75rem; }
.result-item { display: flex; gap: 1rem; padding: 1rem 1.25rem; align-items: center; }
.result-info { flex: 1; }
.result-actions { display: flex; flex-direction: column; gap: 0.4rem; align-items: flex-end; }
.block-report-btn { background: rgba(239,68,68,0.1); color: var(--dislike-color); border: 1.5px solid rgba(239,68,68,0.25); white-space: nowrap; }
.block-report-btn:hover { background: #ef4444; color: white; }
</style>
