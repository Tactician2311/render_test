# 💫 DriftDater

A full-stack dating application built with **Vue 3** + **Flask** for INFO3180.

## Team Members & Roles
| Name | Role |
|------|------|
| [Member 1] | Project Manager / Frontend Lead |
| [Member 2] | Backend Lead |
| [Member 3] | QA / Testing Lead |
| [Member 4] | Frontend Developer |
| [Member 5] | Deployment Lead |

## Features
### Core Features
- ✅ User registration & login (bcrypt password hashing)
- ✅ Profile creation & editing with photo upload
- ✅ Smart matching algorithm (interests + age + location)
- ✅ Like / Dislike / Pass swipe system
- ✅ Mutual match detection
- ✅ Real-time messaging (4s polling)
- ✅ Favorites / Bookmarks
- ✅ Search & discovery with filters

### Optional Features
- ✅ **🚫 Report/Block User** — Report profiles with reasons; block to hide from feed; manage blocks in Settings
- ✅ **🌙 Dark Mode** — Full light/dark theme with CSS variables; persisted to localStorage

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Pinia, Vue Router, Axios |
| Backend | Flask, Flask-SQLAlchemy, Flask-Login, Flask-Migrate, Flask-CORS |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | Session-based with bcrypt |

## Database Schema
**Tables:** `users`, `interests`, `user_interests` (junction), `swipes`, `messages`, `favorites`, `reports`

## Setup Instructions

### Backend
```bash
cd driftdater
python -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cp .env.sample .env             # Edit SECRET_KEY
flask --app app db init
flask --app app db migrate -m "initial"
flask --app app db upgrade
flask --app app --debug run     # http://localhost:5000
```

### Frontend
```bash
# In a new terminal, from project root:
npm install
npm run dev                     # http://localhost:5173
```

## API Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/register` | No | Register new user |
| POST | `/api/v1/login` | No | Login |
| POST | `/api/v1/logout` | Yes | Logout |
| GET | `/api/v1/auth/status` | No | Check auth |
| GET/PUT | `/api/v1/profiles/<id>` | Yes | Get/update profile |
| POST | `/api/v1/profiles/<id>/photo` | Yes | Upload photo |
| GET | `/api/v1/discover` | Yes | Browse matches (filterable) |
| POST | `/api/v1/swipe` | Yes | Like/Dislike/Pass |
| GET | `/api/v1/matches` | Yes | Get mutual matches |
| GET/POST | `/api/v1/messages/<id>` | Yes | Get/send messages |
| GET | `/api/v1/conversations` | Yes | All conversations |
| GET/POST/DELETE | `/api/v1/favorites/<id>` | Yes | Manage favorites |
| POST | `/api/v1/report` | Yes | Report/block user |
| GET | `/api/v1/blocks` | Yes | Get blocked users |
| DELETE | `/api/v1/blocks/<id>` | Yes | Unblock user |
| GET | `/api/v1/search` | Yes | Search profiles |
| GET | `/api/v1/interests` | Yes | All interests |

## Matching Algorithm
Scores 0–100 based on:
- **Shared interests** (up to 50 pts) — Jaccard similarity
- **Age preference fit** (up to 20 pts) — within stated range
- **Location proximity** (up to 30 pts) — Haversine distance formula

## Deployed URL
[Add your Render URL here]

## Known Limitations
- Message updates via polling (4s interval); WebSocket not implemented
- Location matching requires lat/lng coordinates (manual entry in profile)
