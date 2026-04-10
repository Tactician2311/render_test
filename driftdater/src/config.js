/**
 * src/config.js
 * -------------
 * Central API URL configuration.
 *
 * In development (npm run dev):
 *   import.meta.env.VITE_API_URL is undefined → falls back to localhost:5000
 *
 * In production (deployed on Render):
 *   VITE_API_URL is set to your Render backend URL in Render's environment
 *   variables dashboard, e.g. https://driftdater-api.onrender.com/api/v1
 */
export const API = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1'
