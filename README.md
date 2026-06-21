# 🎛️ massloop.run

**AI-powered DJ orchestration.** Generate, mix, and deploy live-performance tracks — **free trial, then pay-as-you-go**.

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Reflex](https://img.shields.io/badge/Reflex-0.6-purple)](https://reflex.dev)
[![Railway](https://img.shields.io/badge/Railway-deployed-black)](https://railway.app)
[![MOA](https://img.shields.io/badge/MOA-Mixture%20of%20Agents-orange)](#-ai-orchestrator)

---

## TL;DR

🎵 You pick **venue**, **BPM**, **energy** → AI agents negotiate (Mixture of Agents) → **Suno** generates the track → you **approve or drop** it (Human-in-the-Loop) → ready MP3.

---

## 💰 Pricing

| Stage | What you get |
|-------|-------------|
| 🆓 **Free Trial** | 2 tracks, 1 mix — **free**, no card |
| ⚡ **PAYG** | Buy track packs. Take what you need, spend what you use. **No subscriptions.** |

> **Subscriptions are dead.** No €9/mo, no €29/mo. Just **fuel up and go.**

---

## 🧠 AI Orchestrator (MOA)

**Mixture of Agents** — multiple LLM agents argue, negotiate, and synthesize a track:

| Agent | Role |
|-------|------|
| 🎯 **Director** | Picks track structure + style for the venue |
| 🎛️ **Mixer** | Decides BPM, energy flow, transitions |
| ✍️ **Lyricist** | Writes genre-matching lyrics (when needed) |
| ✅ **Critic** | Scores the result — send to HITL or regenerate |

👉 **You** get the final preview and hit **Approve / Reject**.  
Without your approval, the track never reaches production.

**Synthesis:** CometAPI → Suno v4/v5 (`chirp-v4`, `chirp-auk`, `chirp-crow`).  
**Cost:** ~$0.08–0.15/track.

---

## 🏗️ Architecture

```
massloop.run
  │
  ├── 🖥️ massloop-fe        Reflex frontend (Python)
  │     ├── pages/           mix_trial, stage, health
  │     ├── components/      UI kit (Radix-themed)
  │     └── state.py         Frontend state
  │
  ├── ⚙️  massloop-be        FastAPI backend
  │     ├── controllers/     REST endpoints + HITL queue
  │     ├── services/        CometAPI/Suno adapter, state machine
  │     ├── orchestrator/    OpenAI Agents SDK + MOA pipeline
  │     └── main.py          CORS, routers, middleware
  │
  └── ☁️  Railway            Deployment (BE + FE, single-port)
```

---

## 🔌 API

| Endpoint | What it does |
|----------|-------------|
| `GET /health` | Health check ✅ |
| `POST /api/performance/queue` | Create a track request (pending) |
| `POST /api/performance/approve/{id}` | Human approves → Suno generates |
| `GET /api/performance/status/{id}` | Generation status |
| `GET /api/performance/result/{id}` | Download MP3 / error |
| `POST /api/trial/start` | Start trial (2 tracks) |
| `GET /api/trial/result/{id}` | Trial result |
| `POST /api/stripe/checkout` | Stripe Checkout session |
| `POST /api/stripe/webhook` | Payment confirmation |

---

## 🚀 Railway Deploy

| Service | Root | Start command |
|---------|------|---------------|
| **massloop-be** | `massloop-be/` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **massloop-fe** | `massloop-fe/` | `reflex run --env prod --single-port --frontend-port $PORT` |

**DNS:**
- 🌐 `massloop.run` → massloop-fe
- 🔗 `api.massloop.run` → massloop-be

---

## 🛠️ Local Dev (5 minutes)

### Prerequisites

```bash
# Python 3.13 + uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Keys in .env (or export in shell):
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