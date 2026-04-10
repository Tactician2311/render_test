import { API } from '../config.js'
<!--
  components/ProfileCard.vue
  --------------------------
  Reusable card component used in DashboardView, FavoritesView, and
  anywhere a compact profile preview with action buttons is needed.

  Props
  -----
  profile     : Object   The user object to display (from API).
  showActions : Boolean  Whether to show Like/Dislike/Pass/Favorite/Report
                         buttons. Defaults to true.
  showScore   : Boolean  Whether to show the match score badge. Defaults to true.

  Emitted Events
  --------------
  view(profile)     User clicked the photo or name area — navigate to full profile.
  like(profile)     User clicked the Like button.
  dislike(profile)  User clicked the Dislike button.
  pass(profile)     User clicked the Pass button.
  favorite(profile) User clicked the Bookmark button.
  report(profile)   User clicked the Report button — parent opens ReportModal.

  Click Propagation
  -----------------
  The photo and name area uses @click to emit 'view'.
  All action buttons use @click.stop to prevent that click from bubbling up
  to the photo/name handler and accidentally navigating away.

  Photo Display
  -------------
  If the user has a profile_photo filename, it is served from the Flask
  uploads endpoint: GET /api/v1/uploads/<filename>.
  If no photo is set, a coloured circle with the user's initials is shown.
-->

<script setup>
const props = defineProps({
  /** User object from the API (to_dict() output). */
  profile: Object,
  /** Show Like/Dislike/Pass/Favorite/Report buttons. */
  showActions: { type: Boolean, default: true },
  /** Show the match score badge. */
  showScore:   { type: Boolean, default: true },
})

const emit = defineEmits(['like', 'dislike', 'pass', 'report', 'favorite', 'view'])


/**
 * Build the full URL for a profile photo filename.
 * Returns null if no photo is set, triggering the initials fallback.
 *
 * @param {string|null} photo  Filename from user.profile_photo.
 * @returns {string|null}
 */
function photoUrl(photo) {
  if (!photo) return null
  if (photo.startsWith('http')) return photo   // Already absolute URL
  return `${API}/uploads/${photo}`
}

/**
 * Compute two-letter initials from the user's first and last name.
 * Used in the avatar placeholder when no photo is available.
 *
 * @param {Object} p  User object.
 * @returns {string}  e.g. "JD" for Jane Doe.
 */
function initials(p) {
  return ((p.first_name?.[0] || '') + (p.last_name?.[0] || '')).toUpperCase()
}
</script>

<template>
  <div class="profile-card">
    <!-- Photo area — click navigates to full profile -->
    <div
      class="card-photo-wrapper"
      @click="emit('view', profile)"
      style="cursor:pointer"
    >
      <img
        v-if="photoUrl(profile.profile_photo)"
        :src="photoUrl(profile.profile_photo)"
        class="profile-card-photo"
        :alt="profile.first_name"
      />
      <!-- Initials placeholder when no photo is set -->
      <div v-else class="profile-card-photo-placeholder">
        <div class="avatar-placeholder" style="width:80px;height:80px;font-size:1.75rem">
          {{ initials(profile) }}
        </div>
      </div>
    </div>

    <div class="profile-card-body">
      <!-- Name/location — click also navigates to full profile -->
      <div
        class="flex items-center justify-between"
        @click="emit('view', profile)"
        style="cursor:pointer"
      >
        <div>
          <div class="profile-card-name">
            {{ profile.first_name }} {{ profile.last_name }}
            <span v-if="profile.age">, {{ profile.age }}</span>
          </div>
          <div class="profile-card-meta" v-if="profile.location">
            📍 {{ profile.location }}
          </div>
        </div>
      </div>

      <!-- Truncated bio (2 lines max, handled by CSS) -->
      <div class="profile-card-bio" v-if="profile.bio">
        {{ profile.bio }}
      </div>

      <!-- Interest tags (first 4 only to keep card compact) -->
      <div class="tags-list" v-if="profile.interests?.length">
        <span v-for="i in profile.interests.slice(0, 4)" :key="i" class="tag">{{ i }}</span>
      </div>

      <!-- Match score badge -->
      <div
        v-if="showScore && profile.match_score !== undefined"
        class="match-score-badge"
        style="margin-top:0.6rem"
      >
        ✨ {{ profile.match_score }}% Match
      </div>

      <!--
        Action buttons — all use @click.stop so clicks do not bubble up to the
        name/photo area and accidentally trigger navigation.
      -->
      <div v-if="showActions" class="card-actions">
        <button class="btn btn-dislike btn-sm" @click.stop="emit('dislike', profile)">✕ Dislike</button>
        <button class="btn btn-pass    btn-sm" @click.stop="emit('pass',    profile)">Pass</button>
        <button class="btn btn-like    btn-sm" @click.stop="emit('like',    profile)">♥ Like</button>
        <button
          class="btn btn-outline btn-sm"
          @click.stop="emit('favorite', profile)"
          title="Bookmark this profile"
        >☆</button>
        <!-- Report button — emits to parent which opens ReportModal -->
        <button
          class="btn btn-outline btn-sm report-btn"
          @click.stop="emit('report', profile)"
          title="Report this user"
        >⚑ Report</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card-photo-wrapper { overflow: hidden; border-radius: 20px 20px 0 0; }
.card-actions { display: flex; gap: 0.4rem; margin-top: 0.75rem; flex-wrap: wrap; }

/* Report button uses dislike colour variable so it inverts correctly in dark mode */
.report-btn {
  color: var(--dislike-color) !important;
  background: rgba(239,68,68,0.08);
  border-color: rgba(239,68,68,0.2) !important;
}
.report-btn:hover {
  background: var(--dislike-color) !important;
  color: white !important;
}
</style>
