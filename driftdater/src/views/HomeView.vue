<script setup>
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { computed } from 'vue'

const auth = useAuthStore()
const router = useRouter()
const isLoggedIn = computed(() => !!auth.user)
</script>

<template>
  <div class="home">
    <section class="hero">
      <div class="hero-content container">
        <div class="hero-text">
          <h1 class="hero-title">Find Your <span class="text-gradient">Drift</span></h1>
          <p class="hero-subtitle">Connect with people who share your vibe, your interests, and your world. DriftDater uses smart matching to help you find meaningful connections.</p>
          <div class="hero-actions">
            <RouterLink v-if="!isLoggedIn" to="/register" class="btn btn-primary btn-lg">Get Started Free</RouterLink>
            <RouterLink v-if="!isLoggedIn" to="/login" class="btn btn-outline btn-lg">Sign In</RouterLink>
            <RouterLink v-if="isLoggedIn" to="/dashboard" class="btn btn-primary btn-lg">Discover Matches</RouterLink>
          </div>
        </div>
        <div class="hero-visual">
          <div class="floating-cards">
            <div class="float-card fc1">💜 Shared Interests</div>
            <div class="float-card fc2">📍 Nearby Matches</div>
            <div class="float-card fc3">💬 Real Connections</div>
          </div>
        </div>
      </div>
    </section>

    <section class="features container">
      <h2 class="section-title">How DriftDater Works</h2>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">✨</div>
          <h3>Smart Matching</h3>
          <p>Our algorithm scores compatibility based on shared interests, age preferences, and location proximity.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">💌</div>
          <h3>Mutual Connections</h3>
          <p>Only chat with people who've liked you back. No awkward one-sided messaging.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🛡️</div>
          <h3>Safe & Respectful</h3>
          <p>Report or block anyone making you uncomfortable. Your safety is our priority.</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🌙</div>
          <h3>Night or Day</h3>
          <p>Switch between light and dark mode for comfortable browsing any time of day.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero { min-height: calc(100vh - 64px); display: flex; align-items: center; background: var(--bg-primary); }
.hero-content { display: grid; grid-template-columns: 1fr 1fr; gap: 4rem; align-items: center; }
.hero-title { font-family: 'Playfair Display', serif; font-size: 3.5rem; font-weight: 700; line-height: 1.15; color: var(--text-primary); }
.text-gradient { background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-subtitle { font-size: 1.1rem; color: var(--text-secondary); margin: 1.25rem 0 2rem; line-height: 1.7; }
.hero-actions { display: flex; gap: 1rem; flex-wrap: wrap; }
.floating-cards { position: relative; height: 280px; }
.float-card {
  position: absolute; background: var(--bg-card);
  border: 1px solid var(--border); border-radius: 14px;
  padding: 0.875rem 1.25rem; font-weight: 600;
  box-shadow: var(--shadow-md); font-size: 0.95rem;
  color: var(--text-primary);
  animation: float 3s ease-in-out infinite;
}
.fc1 { top: 0; left: 20px; animation-delay: 0s; }
.fc2 { top: 80px; left: 120px; animation-delay: 0.8s; }
.fc3 { top: 170px; left: 40px; animation-delay: 1.6s; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
.features { padding: 5rem 1.5rem; }
.section-title { font-family: 'Playfair Display', serif; font-size: 2.25rem; text-align: center; margin-bottom: 3rem; color: var(--text-primary); }
.features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem; }
.feature-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 18px; padding: 2rem; text-align: center; transition: all 0.2s; }
.feature-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-md); }
.feature-icon { font-size: 2.5rem; margin-bottom: 1rem; }
.feature-card h3 { font-weight: 700; margin-bottom: 0.5rem; font-size: 1.1rem; }
.feature-card p { color: var(--text-secondary); line-height: 1.6; font-size: 0.9rem; }
@media (max-width: 768px) {
  .hero-content { grid-template-columns: 1fr; }
  .hero-visual { display: none; }
  .hero-title { font-size: 2.5rem; }
}
</style>
