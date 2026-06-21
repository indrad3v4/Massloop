# 🎛️ massloop.run

**Ты — диджей. Ты — перформер. Ты артист, который не хочет тратить время на меню.**

Это твой бесшовный генератор живых сетов. Ты выбираешь venue, BPM, energy → твои AI-агенты договариваются между собой → Suno генерирует трек за 3 секунды → ты одобряешь или дропаешь → готовый MP3 в колонках.

Никаких подписок. Никаких лишних шагов. Ты на сцене — инструмент работает.

---

## 💰 Твои деньги, твой формат

| Что | Что ты получаешь |
|-----|-----------------|
| 🆓 **Free Trial** | 2 трека, 1 микс — **бесплатно**, без карты |
| ⚡ **PAYG** | Покупаешь пакеты треков. Сколько взял — столько потратил. **Никаких подписок.** |

> Подписки умерли. Ни €9/мес, ни €29/мес. Просто заправился и поехал.

---

## 🧠 Твои AI-агенты

Mixture of Agents — несколько LLM-агентов спорят, договариваются и синтезируют трек **под твой сет**:

| Агент | Его работа для тебя |
|-------|---------------------|
| 🎯 **Director** | Выбирает структуру трека + стиль под venue |
| 🎛️ **Mixer** | Решает BPM, energy flow, переходы |
| ✍️ **Lyricist** | Пишет текст под жанр (если нужно) |
| ✅ **Critic** | Оценивает результат — пускать в HITL или перегенерировать |

**Ты** получаешь финальный превью и нажимаешь **Approve / Reject**.  
Без твоего одобрения — трек не уходит в продакшен.

**Синтез:** CometAPI → Suno v4/v5 (`chirp-v4`, `chirp-auk`, `chirp-crow`).  
**Себестоимость:** ~$0.08–0.15/трек.

---

## 🏗️ Твой стек

```
massloop.run
  │
  ├── 🖥️ massloop-fe        Твой интерфейс (Reflex)
  │     ├── pages/           mix_trial, stage, health
  │     ├── components/      UI kit (Radix-themed)
  │     └── state.py         Твой стейт
  │
  ├── ⚙️  massloop-be        Твой бэкенд (FastAPI)
  │     ├── controllers/     endpoints + HITL
  │     ├── services/        CometAPI/Suno adapter
  │     ├── orchestrator/    OpenAI Agents SDK + MOA pipeline
  │     └── main.py          CORS, routers, middleware
  │
  └── ☁️  Railway            Твой деплой
```

---

## 🔌 Твои endpoints

| Endpoint | Что тебе даёт |
|----------|--------------|
| `GET /api/health` | Проверка: жив? ✅ |
| `POST /api/performance/queue` | Создать заявку на трек (pending) |
| `POST /api/performance/approve/{id}` | Ты аппрувнул → Suno генерит |
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
- 🌐 `massloop.run` → твой фронтенд
- 🔗 `api.massloop.run` → твой бэкенд

---

## 🛠️ Твоя локальная разработка (за 5 минут)

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
