# 🎛️ massloop.run

**You are the DJ. You are the performer. You are the artist who doesn't want to waste time on menus.**

This is your seamless live-set generator. You pick venue, BPM, energy → your AI agents negotiate → Suno generates a track in seconds → you approve or drop it → ready MP3 hits the speakers.

No subscriptions. No extra steps. You are on stage — the tool works.

---

## 💰 Your money, your format

| What | What you get |
|------|-------------|
| 🆓 **Free Trial** | 2 tracks, 1 mix — **free**, no card |
| ⚡ **PAYG** | Buy track packs. Take what you need, spend what you use. **No subscriptions.** |

> Subscriptions are dead. No €9/mo, no €29/mo. Just fuel up and go.

---

## 🧠 Your AI agents

**Mixture of Agents** — several LLM agents argue, negotiate, and synthesize a track **for your set**:

| Agent | What it does for you |
|-------|---------------------|
| 🎯 **Director** | Picks track structure + style for the venue |
| 🎛️ **Mixer** | Decides BPM, energy flow, transitions |
| ✍️ **Lyricist** | Writes genre-matching lyrics (when needed) |
| ✅ **Critic** | Scores the result — send to HITL or regenerate |

**You** get the final preview and hit **Approve / Reject**.  
Without your approval, the track never reaches production.

**Synthesis:** CometAPI → Suno v4/v5 (`chirp-v4`, `chirp-auk`, `chirp-crow`).  
**Cost:** ~$0.08–0.15/track.

---

## 🏗️ Your stack

```
massloop.run
  │
  ├── 🖥️ massloop-fe        Your interface (Reflex)
  │     ├── pages/           mix_trial, stage, health
  │     ├── components/      UI kit (Radix-themed)
  │     └── state.py         Your state
  │
  ├── ⚙️  massloop-be        Your backend (FastAPI)
  │     ├── controllers/     endpoints + HITL
  │     ├── services/        CometAPI/Suno adapter
  │     ├── orchestrator/    OpenAI Agents SDK + MOA pipeline
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
| `POST /api/payg/purchase` | Buy a track pack (PAYG) |
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