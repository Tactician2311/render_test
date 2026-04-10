import { API } from '../config.js'
<!--
  components/ReportModal.vue
  --------------------------
  Modal dialog for reporting and/or blocking another user.
  Implements Optional Feature 1: Report/Block User Functionality.

  Usage
  -----
  <ReportModal
    v-if="showModal"
    :target="userObject"
    @close="showModal = false"
    @done="handleDone"
  />

  Props
  -----
  target : Object   The user being reported (needs at least .id, .first_name, .last_name).

  Emitted Events
  --------------
  close   Emitted when the user dismisses the modal (cancel button or overlay click).
  done    Emitted after a successful submission, before close, so the parent can
          refresh its data (e.g. reload the discover feed to hide the reported user).

  Block vs Report
  ---------------
  The modal has a checkbox labelled "Also block this user".  When checked,
  the API call sets `is_block: true`, which causes the backend to:
  - Exclude the blocked user from the reporter's Discover, Matches, and Search.
  - Prevent messaging in both directions.
  The block can be lifted from Settings → Blocked Users.

  Overlay Behaviour
  -----------------
  Clicking the dark overlay (mousedown.self) dismisses the modal.
  Clicking inside the modal box (mousedown.stop) does not propagate to the overlay.
  This prevents accidental dismissals when interacting with form elements.

  Why no <teleport>
  -----------------
  An earlier version used <teleport to="body"> but this caused silent failures
  in some Vite configurations.  The modal is now a plain fixed-position overlay
  (z-index: 99999) rendered in-tree, which works reliably in all environments.
-->

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const props = defineProps({
  /** The user being reported. */
  target: Object,
})
const emit = defineEmits(['close', 'done'])


/** Selected reason code for the report. */
const reason      = ref('')
/** Optional free-text description from the reporter. */
const description = ref('')
/** Whether to also block the user in addition to reporting them. */
const isBlock     = ref(false)
/** True while the API call is in flight. */
const loading     = ref(false)
/** Error message to display if the submission fails. */
const error       = ref('')
/** Success message displayed briefly before the modal closes. */
const success     = ref('')

/** Predefined reason options shown as selectable buttons. */
const reasons = [
  { value: 'fake',          label: '🤖 Fake Profile' },
  { value: 'spam',          label: '📧 Spam / Bot' },
  { value: 'harassment',    label: '😠 Harassment' },
  { value: 'inappropriate', label: '⚠️ Inappropriate Content' },
  { value: 'other',         label: '🔴 Other' },
]

/**
 * Submit the report (and optional block) to the API.
 *
 * On success, shows a confirmation message for 1.8 seconds then emits
 * 'done' and 'close' so the parent can refresh and hide the modal.
 */
async function submit() {
  if (!reason.value) { error.value = 'Please select a reason'; return }
  loading.value = true
  error.value   = ''
  try {
    await axios.post(`${API}/report`, {
      reported_id: props.target.id,
      reason:      reason.value,
      description: description.value,
      is_block:    isBlock.value,
    })
    success.value = isBlock.value
      ? `${props.target.first_name} has been blocked and reported.`
      : `${props.target.first_name} has been reported. Thank you.`
    setTimeout(() => {
      emit('done')
      emit('close')
    }, 1800)
  } catch (e) {
    error.value = e.response?.data?.error || 'Failed to submit. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <!-- Full-screen overlay — mousedown.self closes modal when clicking outside -->
  <div class="rm-overlay" @mousedown.self="emit('close')">
    <!-- Modal box — mousedown.stop prevents clicks from reaching the overlay -->
    <div class="rm-box" @mousedown.stop>

      <!-- Header row -->
      <div class="rm-header">
        <span class="rm-title">Report User</span>
        <button class="rm-close" @click="emit('close')">✕</button>
      </div>

      <p class="rm-subtitle">
        Reporting <strong>{{ target?.first_name }} {{ target?.last_name }}</strong>.
        All reports are private.
      </p>

      <!-- Success state: shown for 1.8s then modal auto-closes -->
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <!-- Form state -->
      <template v-else>
        <div v-if="error" class="alert alert-error">{{ error }}</div>

        <!-- Reason picker — each option is a styled button acting as a radio -->
        <p class="rm-label">Why are you reporting this user? *</p>
        <div class="rm-reasons">
          <button
            v-for="r in reasons"
            :key="r.value"
            class="rm-reason"
            :class="{ active: reason === r.value }"
            @click="reason = r.value"
            type="button"
          >{{ r.label }}</button>
        </div>

        <!-- Optional description -->
        <p class="rm-label" style="margin-top:1rem">Additional details (optional)</p>
        <textarea
          v-model="description"
          class="form-control"
          rows="3"
          placeholder="Describe the issue..."
          style="margin-top:0.25rem"
        ></textarea>

        <!--
          Block toggle — clicking anywhere on this row toggles the checkbox.
          Uses a custom visual checkbox instead of a native one for consistent
          cross-browser styling and dark mode support.
        -->
        <div class="rm-block-row" @click="isBlock = !isBlock">
          <div class="rm-checkbox" :class="{ checked: isBlock }">
            <span v-if="isBlock">✓</span>
          </div>
          <div>
            <div class="rm-block-label">🚫 Also block this user</div>
            <div class="rm-block-desc">
              They won't appear in your feed or be able to contact you
            </div>
          </div>
        </div>

        <!-- Submit / Cancel -->
        <div class="rm-actions">
          <button class="btn btn-outline" @click="emit('close')" type="button">Cancel</button>
          <button
            class="btn"
            :class="isBlock ? 'btn-danger' : 'btn-primary'"
            @click="submit"
            :disabled="loading || !reason"
            type="button"
          >
            <span v-if="loading">Submitting...</span>
            <span v-else-if="isBlock">🚫 Block &amp; Report</span>
            <span v-else>Submit Report</span>
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
/* Overlay: full-screen fixed backdrop */
.rm-overlay {
  position: fixed; inset: 0; z-index: 99999;
  background: rgba(0,0,0,0.65);
  display: flex; align-items: center; justify-content: center; padding: 1rem;
}

/* Modal box */
.rm-box {
  background: var(--bg-card); border-radius: 20px; padding: 1.75rem;
  width: 100%; max-width: 460px; max-height: 90vh; overflow-y: auto;
  box-shadow: 0 24px 60px rgba(0,0,0,0.4);
  animation: rmIn 0.2s ease;
}
@keyframes rmIn {
  from { opacity: 0; transform: translateY(16px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0)    scale(1); }
}

.rm-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem; }
.rm-title { font-family:'Playfair Display',serif; font-size:1.35rem; font-weight:700; color:var(--text-primary); }
.rm-close {
  background:var(--border-light); border:none; width:32px; height:32px;
  border-radius:50%; cursor:pointer; font-size:0.9rem; color:var(--text-secondary);
  display:flex; align-items:center; justify-content:center; transition:background 0.15s;
}
.rm-close:hover { background:var(--border); }
.rm-subtitle { font-size:0.875rem; color:var(--text-secondary); margin-bottom:1.25rem; line-height:1.5; }
.rm-label { font-size:0.8rem; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.5rem; }

/* Reason buttons */
.rm-reasons { display:flex; flex-direction:column; gap:0.35rem; }
.rm-reason {
  padding:0.65rem 1rem; border:1.5px solid var(--border); border-radius:10px;
  cursor:pointer; font-size:0.9rem; font-family:'DM Sans',sans-serif;
  background:var(--bg-card); color:var(--text-primary); text-align:left; transition:all 0.15s;
}
.rm-reason:hover  { border-color:var(--accent); background:var(--border-light); }
.rm-reason.active { border-color:var(--accent); background:var(--border-light); color:var(--accent); font-weight:600; }

/* Block toggle row */
.rm-block-row {
  display:flex; align-items:flex-start; gap:0.75rem; margin:1rem 0 1.25rem;
  padding:0.875rem; border:1.5px solid var(--border); border-radius:12px;
  cursor:pointer; transition:border-color 0.15s; background:var(--bg-primary);
}
.rm-block-row:hover { border-color:var(--dislike-color); }
.rm-checkbox {
  width:20px; height:20px; border:2px solid var(--border); border-radius:5px;
  flex-shrink:0; margin-top:2px; display:flex; align-items:center; justify-content:center;
  font-size:0.75rem; font-weight:700; transition:all 0.15s; color:white;
}
.rm-checkbox.checked { background:var(--dislike-color); border-color:var(--dislike-color); }
.rm-block-label { font-weight:600; font-size:0.9rem; color:var(--text-primary); }
.rm-block-desc  { font-size:0.78rem; color:var(--text-secondary); margin-top:0.2rem; }

.rm-actions { display:flex; gap:0.75rem; justify-content:flex-end; }
</style>
