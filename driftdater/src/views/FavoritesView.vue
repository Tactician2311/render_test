import { API } from './config.js'
<script setup>
/*
 * FavoritesView — Bookmarked profiles grid.
 * GET /api/v1/favorites. Each card has Like (swipe), Remove (DELETE favorite),
 * and Block/Report buttons.
 */
import { ref, onMounted } from 'vue'
import axios from 'axios'
import ReportModal from '../components/ReportModal.vue'

const favorites = ref([])
const loading = ref(true)
const reportTarget = ref(null)

function photoUrl(photo) { return photo ? `${API}/uploads/${photo}` : null }
function initials(p) { return ((p.first_name?.[0]||'')+(p.last_name?.[0]||'')).toUpperCase() }

async function loadFavorites() {
  try {
    const res = await axios.get(`${API}/favorites`, { withCredentials: true })
    favorites.value = res.data.favorites
  } catch {} finally { loading.value = false }
}

async function removeFavorite(id) {
  try {
    await axios.delete(`${API}/favorites/${id}`, { withCredentials: true })
    favorites.value = favorites.value.filter(f => f.id !== id)
  } catch {}
}

async function swipe(action, profile) {
  try { await axios.post(`${API}/swipe`, { target_id: profile.id, action }, { withCredentials: true }) } catch {}
}

onMounted(loadFavorites)
</script>

<template>
  <div class="container" style="padding-bottom:3rem">
    <ReportModal v-if="reportTarget" :target="reportTarget" @close="reportTarget = null" />
    <div class="page-header">
      <div class="page-title">Favorites</div>
      <div class="page-subtitle">Profiles you've bookmarked</div>
    </div>

    <div v-if="loading" class="loading-center"><div class="spinner"></div></div>
    <div v-else-if="favorites.length === 0" class="empty-state">
      <div class="empty-state-icon">⭐</div>
      <h3>No favorites yet</h3>
      <p>Bookmark profiles from Discover or Search to save them here.</p>
      <RouterLink to="/dashboard" class="btn btn-primary mt-2">Discover People</RouterLink>
    </div>
    <div v-else class="grid-profiles">
      <div v-for="p in favorites" :key="p.id" class="profile-card">
        <div style="cursor:pointer" @click="$router.push(`/profile/${p.id}`)">
          <img v-if="photoUrl(p.profile_photo)" :src="photoUrl(p.profile_photo)" class="profile-card-photo" />
          <div v-else class="profile-card-photo-placeholder">
            <div class="avatar-placeholder" style="width:80px;height:80px;font-size:1.75rem">{{ initials(p) }}</div>
          </div>
        </div>
        <div class="profile-card-body">
          <div class="profile-card-name">{{ p.first_name }} {{ p.last_name }}<span v-if="p.age">, {{ p.age }}</span></div>
          <div class="profile-card-meta" v-if="p.location">📍 {{ p.location }}</div>
          <div class="profile-card-bio" v-if="p.bio">{{ p.bio }}</div>
          <div class="tags-list" v-if="p.interests?.length">
            <span v-for="i in p.interests.slice(0,3)" :key="i" class="tag">{{ i }}</span>
          </div>
          <div class="card-actions">
            <button class="btn btn-like btn-sm" @click="swipe('like', p)">♥ Like</button>
            <button class="btn btn-danger btn-sm" @click="removeFavorite(p.id)">✕ Remove</button>
            <button class="btn btn-outline btn-sm" style="color:var(--dislike-color)" @click="reportTarget = p">⚑</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card-actions { display:flex; gap:0.4rem; margin-top:0.75rem; flex-wrap:wrap; }
</style>
