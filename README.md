# Massloop

**Live performance, alchemised.**

FastAPI + Reflex monorepo that generates music in real time via CometAPI Suno. Human-in-the-loop queue. AI orchestrator with OpenAI Agents SDK.

---

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI, Uvicorn, Pydantic |
| Frontend | Reflex (Python UI framework) |
| Music | CometAPI Suno (`chirp-v4`, `chirp-auk`, `chirp-crow`) |
| Orchestration | OpenAI Agents SDK |
| Runtime | `uv` + Python 3.13 |

---

## Architecture

```
├── massloop-be/          # FastAPI backend
│   ├── app/
│   │   ├── controllers/  # Routers + use cases
│   │   ├── models/       # Pydantic entities
│   │   └── services/     # CometAPI adapter, externals
│   ├── data/             # Queue persistence (JSONL)
│   └── railway.toml      # Deploy config
│
├── massloop-fe/          # Reflex frontend
│   ├── massloop_fe/      # Pages, state, components
│   ├── assets/
│   └── railway.toml
│
└── massloop_venv/        # Shared Python 3.13 venv
```

---

## State machine

```
PENDING → APPROVED → GENERATING → COMPLETE
                              ↘ FAILED
```

`POST /api/performance/queue` → draft
`POST /api/performance/approve/{id}` → human gates generation
`GET /api/performance/status/{id}` → poll
`GET /api/performance/result/{id}` → fetch audio URL

---

## Quick test

```bash
# Backend
cd massloop-be
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Enqueue a track
curl -X POST http://localhost:8000/api/performance/queue \
  -H "Content-Type: application/json" \
  -d '{"prompt":"sunrise pads","tags":"deep house","mv":"chirp-v4","title":"Test","make_instrumental":true}'

# Frontend
cd massloop-fe
reflex run
```

---

## Env vars

| Key | Required | Purpose |
|-----|----------|---------|
| `COMETAPI_API_KEY` | yes | Suno generation |
| `OPENAI_API_KEY` | optional | Orchestrator agent (gpt-4o-mini) |

---

## License

Private.

---

*Built in Kraków.*
