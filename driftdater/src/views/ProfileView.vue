<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { API } from '../config.js'

const auth = useAuthStore()
const editing = ref(false)
const photoFile = ref(null)
const saving = ref(false)
const error = ref('')
const success = ref('')
const interestInput = ref('')

const form = ref({})
const availableInterests = ref([])

const photoUrl = computed(() => {
  if (!auth.user?.profile_photo) return null
  return `${API}/uploads/${auth.user.profile_photo}`
})
function initials() { return ((auth.user?.first_name?.[0]||'')+(auth.user?.last_name?.[0]||'')).toUpperCase() }

function startEdit() {
  form.value = {
    first_name: auth.user.first_name || '',
    last_name: auth.user.last_name || '',
    bio: auth.user.bio || '',
    location: auth.user.location || '',
    occupation: auth.user.occupation || '',
    education: auth.user.education || '',
    age_min_pref: auth.user.age_min_pref || 18,
    age_max_pref: auth.user.age_max_pref || 99,
    max_distance: auth.user.max_distance || 100,
    is_public: auth.user.is_public !== false,
    looking_for: auth.user.looking_for || 'any',
    interests: [...(auth.user.interests || [])]
  }
  editing.value = true
}

function addInterest() {
  const val = interestInput.value.trim().toLowerCase()
  if (val && !form.value.interests.includes(val) && form.value.interests.length < 15) {
    form.value.interests.push(val)
  }
  interestInput.value = ''
}
function removeInterest(i) { form.value.interests = form.value.interests.filter(x => x !== i) }
function toggleInterest(name) {
  if (form.value.interests.includes(name)) removeInterest(name)
  else if (form.value.interests.length < 15) form.value.interests.push(name)
}

async function saveProfile() {
  error.value = ''; success.value = ''
  if (!form.value.first_name || !form.value.last_name) { error.value = 'Name is required'; return }
  if (form.value.interests.length < 3) { error.value = 'Please add at least 3 interests'; return }
  saving.value = true
  try {
    await auth.updateProfile(auth.user.id, form.value)
    success.value = 'Profile updated!'
    editing.value = false
    setTimeout(() => success.value = '', 3000)
  } catch (e) { error.value = e.response?.data?.error || 'Update failed' }
  finally { saving.value = false }
}

async function uploadPhoto() {
  if (!photoFile.value?.files[0]) return
  try {
    await auth.uploadPhoto(auth.user.id, photoFile.value.files[0])
    success.value = 'Photo updated!'
    setTimeout(() => success.value = '', 3000)
  } catch (e) { error.value = 'Photo upload failed' }
}

onMounted(async () => {
  try {
    const res = await axios.get(`${API}/interests`, { withCredentials: true })
    availableInterests.value = res.data.interests.map(i => i.name)
  } catch {}
})
</script>

<template>
  <div class="container" style="max-width:700px;padding-bottom:3rem">
    <div class="page-header">
      <div class="page-title">My Profile</div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <!-- View Mode -->
    <div v-if="!editing" class="card card-body">
      <div class="profile-view-top">
        <div class="profile-photo-wrap">
          <img v-if="photoUrl" :src="photoUrl" class="avatar-xl" style="border-radius:50%" />
          <div v-else class="avatar-placeholder avatar-xl" style="font-size:2.5rem">{{ initials() }}</div>
          <label class="photo-upload-btn">
            📷
            <input ref="photoFile" type="file" accept="image/*" style="display:none" @change="uploadPhoto" />
          </label>
        </div>
        <div class="profile-view-info">
          <h2 class="font-serif" style="font-size:1.75rem">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</h2>
          <p class="text-secondary">@{{ auth.user?.username }}</p>
          <p v-if="auth.user?.age" class="text-secondary text-sm">Age: {{ auth.user.age }}</p>
          <p v-if="auth.user?.location" class="text-secondary text-sm">📍 {{ auth.user.location }}</p>
          <p v-if="auth.user?.occupation" class="text-secondary text-sm">💼 {{ auth.user.occupation }}</p>
          <p v-if="auth.user?.education" class="text-secondary text-sm">🎓 {{ auth.user.education }}</p>
        </div>
      </div>

      <hr class="divider" />
      <div v-if="auth.user?.bio">
        <div class="form-label">About</div>
        <p style="line-height:1.7;color:var(--text-primary)">{{ auth.user.bio }}</p>
      </div>

      <div class="mt-2" v-if="auth.user?.interests?.length">
        <div class="form-label">Interests</div>
        <div class="tags-list">
          <span v-for="i in auth.user.interests" :key="i" class="tag">{{ i }}</span>
        </div>
      </div>

      <div class="mt-2">
        <div class="form-label">Preferences</div>
        <p class="text-sm text-secondary">
          Age range: {{ auth.user?.age_min_pref }}–{{ auth.user?.age_max_pref }} •
          Looking for: {{ auth.user?.looking_for || 'any' }} •
          Distance: {{ auth.user?.max_distance }}km •
          Profile: {{ auth.user?.is_public ? 'Public' : 'Private' }}
        </p>
      </div>

      <button class="btn btn-primary mt-3" @click="startEdit">✏️ Edit Profile</button>
    </div>

    <!-- Edit Mode -->
    <div v-else class="card card-body">
      <h3 class="font-serif" style="font-size:1.25rem;margin-bottom:1.25rem">Edit Profile</h3>

      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">First Name *</label>
          <input v-model="form.first_name" type="text" class="form-control" />
        </div>
        <div class="form-group">
          <label class="form-label">Last Name *</label>
          <input v-model="form.last_name" type="text" class="form-control" />
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">Bio / Description</label>
        <textarea v-model="form.bio" class="form-control" rows="3" placeholder="Tell people about yourself..."></textarea>
      </div>

      <div class="form-group">
        <label class="form-label">Location</label>
        <input v-model="form.location" type="text" class="form-control" placeholder="e.g. Kingston, Jamaica" />
      </div>

      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">Occupation</label>
          <input v-model="form.occupation" type="text" class="form-control" placeholder="e.g. Software Developer" />
        </div>
        <div class="form-group">
          <label class="form-label">Education</label>
          <input v-model="form.education" type="text" class="form-control" placeholder="e.g. UWI Mona" />
        </div>
      </div>

      <hr class="divider" />
      <div class="form-group">
        <label class="form-label">Interests * (min 3, max 15)</label>
        <div class="tags-list" style="margin-bottom:0.5rem">
          <span v-for="i in form.interests" :key="i" class="tag selected" style="cursor:pointer" @click="removeInterest(i)">{{ i }} ✕</span>
        </div>
        <div class="flex gap-1">
          <input v-model="interestInput" type="text" class="form-control" placeholder="Add an interest..." @keyup.enter="addInterest" style="flex:1" />
          <button class="btn btn-secondary" @click="addInterest">Add</button>
        </div>
        <div class="tags-list" style="margin-top:0.75rem">
          <span
            v-for="name in ['hiking','gaming','cooking','reading','music','travel','art','photography','fitness','yoga','movies','dancing','sports','tech','fashion'].filter(n => !form.interests.includes(n))"
            :key="name" class="tag" style="cursor:pointer" @click="toggleInterest(name)"
          >+ {{ name }}</span>
        </div>
      </div>

      <hr class="divider" />
      <h4 style="margin-bottom:0.75rem;font-weight:600">Match Preferences</h4>
      <div class="grid-2">
        <div class="form-group">
          <label class="form-label">Min Age</label>
          <input v-model.number="form.age_min_pref" type="number" class="form-control" min="18" max="99" />
        </div>
        <div class="form-group">
          <label class="form-label">Max Age</label>
          <input v-model.number="form.age_max_pref" type="number" class="form-control" min="18" max="99" />
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Max Distance (km)</label>
        <input v-model.number="form.max_distance" type="number" class="form-control" min="5" max="20000" />
      </div>
      <div class="form-group">
        <label class="form-label">Looking For</label>
        <select v-model="form.looking_for" class="form-control">
          <option value="any">Any</option>
          <option value="male">Men</option>
          <option value="female">Women</option>
          <option value="non-binary">Non-binary</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Profile Visibility</label>
        <select v-model="form.is_public" class="form-control">
          <option :value="true">Public</option>
          <option :value="false">Private</option>
        </select>
      </div>

      <div class="flex gap-1" style="margin-top:0.5rem">
        <button class="btn btn-primary" @click="saveProfile" :disabled="saving">{{ saving ? 'Saving...' : 'Save Profile' }}</button>
        <button class="btn btn-outline" @click="editing = false">Cancel</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-view-top { display: flex; gap: 1.5rem; align-items: flex-start; }
.profile-photo-wrap { position: relative; flex-shrink: 0; }
.photo-upload-btn {
  position: absolute; bottom: 0; right: 0;
  background: var(--accent); color: white; border-radius: 50%;
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; cursor: pointer;
}
.profile-view-info { flex: 1; }
.profile-view-info h2 { margin-bottom: 0.25rem; }
.profile-view-info p { margin-top: 0.2rem; }
@media (max-width: 500px) { .profile-view-top { flex-direction: column; align-items: center; text-align: center; } }
</style>
