# 🎛️ massloop.run

**AI-powered DJ orchestration.** Generate, mix, and deploy live-performance tracks — **free trial, then pay-as-you-go**.

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Reflex](https://img.shields.io/badge/Reflex-0.6-purple)](https://reflex.dev)
[![Railway](https://img.shields.io/badge/Railway-deployed-black)](https://railway.app)
[![MOA](https://img.shields.io/badge/MOA-Mixture%20of%20Agents-orange)](#-ai-orchestrator)

---

## TL;DR

🎵 Выбираешь **venue**, **BPM**, **energy** → AI-агенты договариваются (Mixture of Agents) → **Suno** генерирует трек → ты **одобряешь или дропаешь** (Human-in-the-Loop) → готовый MP3.

---

## 💰 Pricing

| Этап | Что получаешь |
|------|--------------|
| 🆓 **Free Trial** | 2 трека, 1 микс — **бесплатно**, без карты |
| ⚡ **PAYG** | Покупаешь пакеты треков. Сколько взял — столько потратил. **Никаких подписок.** |

> **Подписки умерли.** Ни €9/мес, ни €29/мес. Просто **заправился и поехал.**

---

## 🧠 AI Orchestrator (MOA)

**Mixture of Agents** — несколько LLM-агентов спорят, договариваются и синтезируют трек:

| Агент | Роль |
|-------|------|
| 🎯 **Director** | Выбирает структуру трека + стиль под venue |
| 🎛️ **Mixer** | Решает BPM, energy flow, переходы |
| ✍️ **Lyricist** | Пишет текст под жанр (если нужно) |
| ✅ **Critic** | Оценивает результат — пускать в HITL или перегенерировать |

👉 **Человек** получает финальный превью и нажимает **Approve / Reject**.  
Без одобрения — трек не уходит в продакшен.

**Синтез:** CometAPI → Suno v4/v5 (`chirp-v4`, `chirp-auk`, `chirp-crow`).  
**Себестоимость:** ~$0.08–0.15/трек.

---

## 🏗️ Architecture

```
massloop.run
  │
  ├── 🖥️ massloop-fe        Reflex frontend (Python)
  │     ├── pages/           mix_trial, health, dashboard
  │     ├── components/      UI kit (Radix-themed)
  │     └── state.py         Trial + PAYG state management
  │
  ├── ⚙️  massloop-be        FastAPI backend
  │     ├── controllers/     REST endpoints + HITL queue
  │     ├── services/        CometAPI/Suno adapter, state machine
  │     ├── orchestrator/    OpenAI Agents SDK + MOA pipeline
  │     └── main.py          CORS, routers, middleware
  │
  └── ☁️  Railway            Деплой (BE + FE, single-port)
```

---

## 🔌 API

| Endpoint | Что делает |
|----------|-----------|
| `GET /api/health` | Живой? ✅ |
| `POST /api/performance/queue` | Создать заявку на трек (pending) |
| `POST /api/performance/approve/{id}` | Человек аппрувнул → Suno генерит |
| `GET /api/performance/status/{id}` | Статус генерации |
| `GET /api/performance/result/{id}` | Скачать MP3 / ошибка |
| `POST /api/trial/start` | Запустить триал (2 трека) |
| `GET /api/trial/result/{id}` | Результат триала |
| `POST /api/payg/purchase` | Купить пакет треков (PAYG) |
| `POST /api/stripe/webhook` | Подтверждение оплаты |

---

## 🚀 Railway Deploy

| Service | Root | Start |
|---------|------|-------|
| **massloop-be** | `massloop-be/` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **massloop-fe** | `massloop-fe/` | `reflex run --env prod --single-port --frontend-port $PORT` |

**DNS:**
- 🌐 `massloop.run` → massloop-fe
- 🔗 `api.massloop.run` → massloop-be

---

## 🛠️ Local Dev (за 5 минут)

### Предварительно

```bash
# Python 3.13 + uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ключи в .env (или в ~/.bashrc):
export COMETAPI_KEY="sk-..."
export SUNO_API_KEY="..."
export STRIPE_SECRET_KEY="sk_test_..."
export OPENAI_API_KEY="sk-..."
```

### Бэкенд

```bash
cd massloop-be
uv venv
uv pip sync requirements.txt
uvicorn app.main:app --port 8000 --reload
```

### Фронтенд

```bash
cd massloop-fe
uv venv
uv pip sync requirements.txt
reflex run --env dev
```

---

## License

MIT