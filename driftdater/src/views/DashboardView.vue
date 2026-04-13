<script setup>
import { API } from '../config.js'
/*
 * DashboardView — Discover page (Browse Potential Matches).
 * Shows unswiped profiles with filtering by age, location, interest, and sort.
 * Like/Dislike/Pass call POST /api/v1/swipe. A match toast appears on mutual like.
 * ReportModal is opened via the ProfileCard 'report' emit.
 */
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import ProfileCard from '../components/ProfileCard.vue'
import ReportModal from '../components/ReportModal.vue'

const auth = useAuthStore()

const profiles = ref([])
const loading = ref(true)
const error = ref('')
const matchToast = ref(null)

// Report/block modal state
const showReportModal = ref(false)
const reportTarget = ref(null)

function openReport(profile) {
  reportTarget.value = profile
  showReportModal.value = true
}
function closeReport() {
  showReportModal.value = false
  reportTarget.value = null
}

// Filters
const filters = ref({ min_age: '', max_age: '', location: '', interest: '', sort: 'score' })
const showFilters = ref(false)

async function loadProfiles() {
  loading.value = true; error.value = ''
  try {
    const params = {}
    if (filters.value.min_age) params.min_age = filters.value.min_age
    if (filters.value.max_age) params.max_age = filters.value.max_age
    if (filters.value.location) params.location = filters.value.location
    if (filters.value.interest) params.interest = filters.value.interest
    params.sort = filters.value.sort
    const res = await axios.get(`${API}/discover`, { params, withCredentials: true })
    profiles.value = res.data.profiles
  } catch { error.value = 'Failed to load profiles' }
  finally { loading.value = false }
}

async function handleSwipe(action, profile) {
  try {
    const res = await axios.post(`${API}/swipe`, { target_id: profile.id, action }, { withCredentials: true })
    profiles.value = profiles.value.filter(p => p.id !== profile.id)
    if (res.data.is_match) {
      matchToast.value = `🎉 It's a match with ${profile.first_name}!`
      setTimeout(() => { matchToast.value = null }, 3500)
    }
  } catch {}
}

async function handleFavorite(profile) {
  try { await axios.post(`${API}/favorites/${profile.id}`, {}, { withCredentials: true }) } catch {}
}

function resetFilters() {
  filters.value = { min_age: '', max_age: '', location: '', interest: '', sort: 'score' }
  loadProfiles()
}

onMounted(loadProfiles)
</script>

<template>
  <div class="container" style="padding-bottom:3rem">
    <!-- Match Toast -->
    <div v-if="matchToast" class="match-toast">{{ matchToast }}</div>

    <!-- Report Modal — rendered at top level of this component -->
    <ReportModal
      v-if="showReportModal && reportTarget"
      :target="reportTarget"
      @close="closeReport"
      @done="loadProfiles"
    />

    <div class="page-header flex items-center justify-between">
      <div>
        <div class="page-title">Welcome, {{ auth.user?.first_name }} 👋</div>
        <div class="page-subtitle">Discover people who match your vibe</div>
      </div>
      <button class="btn btn-outline" @click="showFilters = !showFilters">
        {{ showFilters ? '▲ Hide Filters' : '▼ Show Filters' }}
      </button>
    </div>

    <!-- Filters -->
    <div v-if="showFilters" class="filter-panel">
      <div class="filter-row">
        <input v-model="filters.location" type="text" class="form-control" placeholder="Filter by location..." />
        <select v-model="filters.min_age" class="form-control">
          <option value="">Min Age</option>
          <option v-for="a in [18,20,25,30,35,40,45,50]" :key="a" :value="a">{{ a }}+</option>
        </select>
        <select v-model="filters.max_age" class="form-control">
          <option value="">Max Age</option>
          <option v-for="a in [25,30,35,40,45,50,60,70]" :key="a" :value="a">Up to {{ a }}</option>
        </select>
        <input v-model="filters.interest" type="text" class="form-control" placeholder="Filter by interest..." />
        <select v-model="filters.sort" class="form-control">
          <option value="score">Best Match</option>
          <option value="newest">Newest First</option>
        </select>
      </div>
      <div class="flex gap-1" style="margin-top:0.75rem">
        <button class="btn btn-primary btn-sm" @click="loadProfiles">Apply Filters</button>
        <button class="btn btn-secondary btn-sm" @click="resetFilters">Reset</button>
      </div>
    </div>

    <div v-if="loading" class="loading-center">
      <div class="spinner"></div>
      <span>Finding your matches...</span>
    </div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>
    <div v-else-if="profiles.length === 0" class="empty-state">
      <div class="empty-state-icon">💫</div>
      <h3>You've seen everyone!</h3>
      <p>Check back later or adjust your filters.</p>
      <button class="btn btn-primary mt-2" @click="loadProfiles">Refresh</button>
    </div>
    <div v-else class="grid-profiles">
      <ProfileCard
        v-for="p in profiles"
        :key="p.id"
        :profile="p"
        @like="handleSwipe('like', $event)"
        @dislike="handleSwipe('dislike', $event)"
        @pass="handleSwipe('pass', $event)"
        @favorite="handleFavorite($event)"
        @report="openReport($event)"
        @view="$router.push(`/profile/${$event.id}`)"
      />
    </div>
  </div>
</template>

<style scoped>
.filter-panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 1.25rem; margin-bottom: 1.5rem; }
.filter-row { display: flex; gap: 0.75rem; flex-wrap: wrap; }
.filter-row .form-control { flex: 1; min-width: 150px; }
</style>
