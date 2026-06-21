# 🎛️ Massloop

**AI-powered DJ orchestration platform.** Generate, mix, and deploy live-performance tracks via CometAPI Suno, gated by a human-in-the-loop approval queue and Stripe billing.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Reflex](https://img.shields.io/badge/Reflex-0.6-purple)
![Railway](https://img.shields.io/badge/Railway-deployed-black)

---

## 🔥 What it does

| Endpoint | Action |
|----------|--------|
| `POST /api/performance/queue` | Draft a track request (`pending_approval`) |
| `POST /api/performance/approve/{id}` | Human approves → auto-generates via Suno |
| `GET /api/performance/status/{id}` | Poll state |
| `GET /api/performance/result/{id}` | Get final MP3 or error |
| `POST /api/trial/start` | Free 2-track mix trial |
| `GET /api/trial/result/{id}` | Retrieve trial audio |
| `POST /api/stripe/checkout` | Stripe subscription (`DJ Starter` €9/mo) |
| `POST /api/stripe/webhook` | Payment verification |

### Pricing

| Tier | Price | Tracks | Mixes/mo |
|------|-------|--------|----------|
| Trial | €0 | 2 | 1 |
| DJ Starter | €9 | 20 | 10 |
| Pro | €29 | ∞ | ∞ |

---

## 🏗️ Structure

```
Massloopai/
├── massloop-be/           # FastAPI backend
│   ├── app/
│   │   ├── controllers/   # REST routers + HITL queue
│   │   ├── services/      # CometAPI Suno adapter, state manager
│   │   ├── orchestrator/  # OpenAI Agents SDK
│   │   └── main.py        # CORS + router mount
│   └── railway.toml       # uvicorn start command
├── massloop-fe/           # Reflex frontend
│   ├── massloop_fe/
│   │   ├── pages/
│   │   │   ├── mix_trial_page.py   # DJ workflow UI
│   │   │   └── health.py
│   │   └── state.py       # Trial + Stripe state
│   └── railway.toml       # reflex prod start command
└── data/                  # Queue + trial limits (gitignored)
```

---

## 🚀 Deploy

### Railway (production)

| Service | Root directory | Start command |
|---------|---------------|---------------|
| `massloop-be` | `massloop-be` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| `massloop-fe` | `massloop-fe` | `reflex run --env prod --backend-port $PORT` |

**Public URLs:**
- BE: `https://massloop-be-production.up.railway.app`
- FE: `https://massloop-fe-production.up.railway.app`

### DNS (Path A)

```
massloop.run       CNAME → massloop-fe-production.up.railway.app
api.massloop.run   CNAME → massloop-be-production.up.railway.app
```

---

## 🧠 AI Orchestrator

Uses OpenAI Agents SDK to decide: *generate / continue / mix* based on venue, BPM, energy. Calls CometAPI Suno v4/v5 for actual synthesis.

**Models:** `chirp-v4`, `chirp-auk` (lyrics), `chirp-crow` (v5, fastest)

**Cost:** ~$0.08–0.15/track. $13 budget ≈ 87–162 tracks.

---

## 📋 Local dev

```bash
# Backend
cd massloop-be
uv venv .venv --python 3.13
uv pip install -r requirements.txt -p .venv/bin/python
uvicorn app.main:app --port 8000

# Frontend
cd ../massloop-fe
reflex run --env dev
```

**Requirements:** Python 3.13, `uv`, `starlette==0.40.0` (FastAPI 0.115 compat)

---

## 🎨 Branding

Suckpuck aesthetic — dark, glitch-industrial, acid neons. Built with wabi-sabi precision.

---

## License

MIT
