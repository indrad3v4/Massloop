# 🎛️ massloop.run

**You are the artist. One AI orchestrator is your backstage crew.**
Describe the vibe. It generates. You approve.

Pick venue, BPM, energy → the orchestrator builds a track → you approve or drop it → ready MP3 hits the speakers. No subscriptions you don't control — you choose the plan that fits.

---

## 💰 Your money, your format
| What | What you get |
|------|-------------|
| 🆓 **Free Trial** | 2 tracks, 1 mix — **free**, no card |
| 🡡 **Subscription** | Unlimited generations, priority queue. Billed via Stripe. |

> Plans are subscription-based (Stripe). No hidden PAYG track-packs yet — the `/api/payg/purchase` endpoint is on the roadmap.

---

## 🧠 Your AI orchestrator
**One orchestrator agent** negotiates a track **for your set** — not 4 separate bots:

| Role | What it does for you |
|-------|---------------------|
| 🎯 **Orchestrator** | Picks structure + style for the venue, runs generation, scores the result |
| ✅ **You** | Get the preview, hit **Approve / Reject**. Without your approval, the track never reaches production. |

**Persistent memory:** the orchestrator learns your artist identity (signature sound, BPM sweet spot, what to avoid) and reflects it in every generation. Edit it anytime via the Artist Identity panel.

**Cost:** ~$0.08–0.15/track (CometAPI → Suno v3/v4). Daily budget is surfaced via `/budget` — you see what you spend.

---

## 🏗️ Your stack
```
massloop.run
  │
  ├── 🖥️ massloop-fe        Your interface (Reflex)
  │     ├── pages/           artist, onboard, performance, health
  │     ├── components/      UI kit (Radix-themed)
  │     └── state.py         Your state
  │
  ├── ⚙️  massloop-be        Your backend (FastAPI)
  │     ├── controllers/     endpoints + HITL + budget guardrail
  │     ├── services/        CometAPI/Suno adapter, artist memory
  │     ├── orchestrator/    OpenAI Agents SDK orchestrator
  │     └── main.py          CORS, routers, middleware
  │
  └── ☁️  Railway            Your deployment
```

---

## 🔌 Your endpoints
| Endpoint | What it gives you |
|----------|------------------|
| `GET /api/health` | Check: alive? ✅ |
| `POST /api/performance/queue` | Create a track request (pending) |
| `POST /api/performance/approve/{id}` | You approve → Suno generates |
| `GET /api/performance/status/{id}` | Generation status |
| `GET /api/performance/result/{id}` | Download MP3 / error |
| `POST /api/trial/start` | Start trial (2 tracks) |
| `GET /api/trial/result/{id}` | Trial result |
| `GET /api/artist/profile/{id}` | Load your learned identity |
| `POST /api/artist/learn` | Teach the orchestrator (chat) |
| `GET /budget` | Remaining daily budget (EUR) |
| `POST /api/stripe/checkout` | Start subscription |
| `POST /api/stripe/webhook` | Payment confirmation |

---

## 🚀 Railway Deploy
| Service | Root | Start |
|---------|------|-------|
| **massloop-be** | `massloop-be/` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **massloop-fe** | `massloop-fe/` | `reflex run --env prod --single-port --frontend-port $PORT` |

**DNS:**
- 🌐 `massloop.run` → your frontend
- 🔗 `api.massloop.run` → your backend

---

## 🛠️ Your local dev (5 minutes)

### Prerequisites
```bash
# Python 3.13 + uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Keys in .env (or in ~/.bashrc):
export COMETAPI_KEY="sk-..."
export SUNO_API_KEY="..."
export STRIPE_SECRET_KEY="sk_test_..."
export OPENAI_API_KEY="sk-..."
```

### Backend
```bash
cd massloop-be
uv venv
uv pip sync requirements.txt
uvicorn app.main:app --port 8000 --reload
```

### Frontend
```bash
cd massloop-fe
uv venv
uv pip sync requirements.txt
reflex run --env dev
```

---

## License
MIT

---

<p align="center">
  <sub>built by <a href="https://github.com/indrad3v4">indradev_</a> · 
  <a href="https://buymeacoffee.com/indradev_">☕ support</a></sub>
</p>
