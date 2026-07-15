# Massloop — Infrastructure Layer Roast

**Scope:** ai-engineering-loop Systematic Investigation Checklist — Infrastructure Layer
**Target:** `/root/massloop-push/massloop-be` (FastAPI) + `/root/massloop-push/massloop-fe` (Reflex), Railway deploy
**Date:** 2025-11-03 (repo state)
**Method:** static read of `main.py`, `config.py`, `controllers/*`, `services/*`, `orchestrator/*`, `railway.toml`, `nixpacks.toml`, `logs/*`. No tests/CI exist to execute.

> NDA: no client/Certrux/MotorsAgent references. Findings are local-only; nothing pushed.

---

## TL;DR — Top 3 CRITICAL findings

1. **C1 — Cost/budget SLO is documented config but never enforced.** `daily_budget_eur`, `max_track_cost_eur`, `max_polling_time_s` exist in `config.py` (lines 20–24) yet are read by **no code on the live generation path**. All enforcement logic (`get_budget_status`, `record_generation`, `BudgetExceededError`) lives in `services/externals.py` — which is **dead, unimportable code** (see C2). → No guard against runaway spend; the "cost tracking" claim is false at runtime.
2. **C2 — No tests, no CI, and a 3,310-line "core" module ships undetected-broken.** There is zero test code and zero CI config anywhere in the repo. `app/services/externals.py` fails to even parse (`IndentationError` at line 26) and is imported nowhere — yet it is the file that supposedly implements the budget, reflection loop, DeepSeek orchestrator, and quality evaluation the docs/pitch describe.
3. **C3 — The live app silently diverged from its documented architecture.** The running system is `orchestrator/agent.py` (hardcoded `gpt-4o-mini`) + `orchestrator/tools.py` (direct CometAPI). The "DeepSeek V3 reflection orchestrator" shown in `logs/massloop_2025-11-03.log:20` and the FE health page (`gpt-4o-mini · cometsuno adapter`) is a fiction layered over dead code. Behaviour in prod is not what the docs claim.

---

## Severity-graded matrix

| Sev | Finding | Evidence (file:line) | Specific Fix | Principle |
|-----|---------|----------------------|--------------|-----------|
| **CRIT** | C1 — Budget/cost SLO config is dead; no spend guard on live path | `config.py:20-24` defines `daily_budget_eur`/`max_track_cost_eur`/`max_polling_time_s`. Grep shows these names appear only in `config.py`, `state_manager.py`, `entities.py`, `interfaces.py` (exception class), `externals.py` — **never** in `tools.py`, `agent.py`, `usecases.py`, `performance_router.py`, `orchestrator_router.py`. Budget enforcement (`externals.py:1876-1892`, `2648-2652`) is in the dead module. | Before any generation, read `settings.daily_budget_eur`/`max_track_cost_eur`; reject/queue when exceeded; record actual cost per call (CometAPI returns billing). Add an integration test asserting rejection at budget. | Cost SLO must be enforced, not decorative. |
| **CRIT** | C2 — Zero tests/CI; broken 3,310-line module ships untested | Repo-wide: no `tests/`, no `test_*.py`, no `pytest.ini`, no `.github/`, no `Makefile`/CI. `externals.py` raises `IndentationError` at line 26 (confirmed via `python3 -c "ast.parse(...)"`); `import` search for `externals` returns **0** references. `nixpacks.toml`/`railway.toml` only run `uvicorn`/`reflex` — never compile-check or test. | Add CI (GitHub Actions) running `ruff`/`mypy` + `pytest` on every push; gate merge on green. Add a smoke import test (`import app.main`) that would have caught the IndentationError. Delete or fix `externals.py` so it compiles. | Quality gates catch dead/broken code before deploy. |
| **CRIT** | C3 — Live architecture silently differs from documented one (dead-code mask) | `agent.py:60` `model="gpt-4o-mini"` hardcoded; `agent.py:142-173` `optimize_generation_request`/`evaluate_track_quality`/`analyze_cost_efficiency` are **no-op shims** returning base request / `0.75`. The real reflection+DeepSeek impl is `externals.py` which doesn't run. `logs/massloop_2025-11-03.log:20` claims "DeepSeek V3 ready"; FE `pages/health.py:56` shows "gpt-4o-mini · cometsuno adapter · chirp-v4". | Either wire the real orchestrator in (and make `externals.py` importable) or delete the dead module and update docs/pitch/FE to reflect the actual gpt-4o-mini + direct-CometAPI path. Hardcode-free model via env. | Docs must match the running system. |
| **HIGH** | H1 — CORS `allow_origins=["*"]` combined with `allow_credentials=True` | `main.py:37-40`. Wildcard origin + credentials is rejected by browsers and is a security smell; any origin can issue credentialed requests. | Use an explicit origin allowlist from `settings.cors_origins` (parse CSV); only enable credentials for known origins. Never pair `*` with `allow_credentials`. | Secure-by-default CORS. |
| **HIGH** | H2 — Errors swallowed into logs + returned as generic truncated strings; no surfacing/alerting | `orchestrator_router.py:209-214` catches broad `Exception` and returns `f"🤖 orchestrator encountered an issue: {str(e)[:100]}"`. `performance_router.py:294-301` swallows all exceptions into `task["error"]`. `errors_2025-11-03.log:21,49` logs `CRITICAL: API returned HTML error page!` **twice** (21:09 and 21:34, identical) — CometAPI returning a GTM login HTML page (auth/endpoint wrong) yet app kept running degraded; persona creation failed silently (`errors_2025-11-03.log:29,57`). No alert fired. | Surface structured errors to the client (status code + error id), emit metrics/alert on repeated CRITICALs, and fail the request instead of returning a fake "ok". Add a log-based alert on N consecutive identical CRITICAL errors. | Fail loud, not silent. |
| **HIGH** | H3 — No reproducibility: no run IDs, no seed, non-deterministic fallback | `orchestrator_router.py:108-115` and `stream_router.py:65` use `random.choice(...)` for fallback replies — non-deterministic. No `run_id`/`trace_id`/`seed` anywhere (grep: 0). LLM call in `agent.py:109` passes no `seed`. Cannot reproduce or attribute a bad/failed generation. | Generate a `run_id` (uuid) per request/orchestration; thread it through logs, queue, and client response. Optionally pass `seed` from config to the model for reproducible runs. Persist per-run input+output. | Reproducibility is a debuggability requirement. |
| **MED** | M1 — Latency SLO mismatch; no latency metric on live path | Chat endpoints cap at `asyncio.wait_for(..., timeout=55)` (`orchestrator_router.py:157`, `stream_router.py:88`) but Suno generation polls up to `max_wait_s=120` (`tools.py:86`, `performance_router.py:261`). Config `max_polling_time_s=120` (`config.py:23`) is unused. No p50/p95 latency logged on the live path. | Align timeouts (decide a single SLO, e.g. 60s chat, 120s gen) and log per-stage latency. Read `settings.max_polling_time_s` in `poll_track`. Expose latency histogram. | SLOs must be measured and consistent. |
| **MED** | M2 — Bare `except:` swallowing + broad `except Exception` hiding root cause | Bare `except:` at `externals.py:122,508,1504,1816` (in dead code, but indicates pattern). Live path also uses broad `except Exception` that returns generic error strings (H2). `usecases.py:318-321` `except Exception` in `_fill_buffer` `break`s, silently dropping the failure. | Replace bare `except:` with specific exceptions; at minimum `except Exception as e:` that logs full traceback. Never `pass`/`return b""` on a recording error silently (`externals.py:1816-1817`). | Catch specific, log fully. |
| **MED** | M3 — Concurrency/state races on the queue file | `_run_approved_generation` (`performance_router.py:206-301`) re-reads/writes `queue.json` **3 times** with no lock; concurrent approvals/commits can clobber. `trial_router.py:87` uses `asyncio.create_task(_run_approved_generation(task_id))` fire-and-forget — task is unrelated to the request lifecycle and can be cancelled when the request coroutine ends. | Use a single in-memory store (dict/async lock) or a real DB; if file-backed, hold one lock for the whole mutation. Prefer `BackgroundTasks` (already used at `performance_router.py:192`) consistently over `create_task`. | Shared mutable state needs locking. |
| **MED** | M4 — Partial/empty config → silent degraded mode (no fail-fast) | `main.py:21-22` `STRIPE_SECRET_KEY` missing → only `logger.warning` (checkout silently disabled). `main.py:44-51` no `OPENAI_API_KEY` → orchestrator disabled, chat returns random canned strings. Mix of hard-fail (`COMETAPI_KEY` raises `RuntimeError`, `main.py:27-31`) and soft-degrade is inconsistent. | Define a per-environment contract: prod must fail-fast on missing required services; dev may degrade. Make degrade mode explicit + advertised in `/health`. | Fail-fast in prod, degrade by intent. |
| **LOW** | L1 — Dead import / unused temp infra | `externals.py:18` `import tempfile` but no `mkdtemp`/`TemporaryDirectory` use; no resource leak on the live path, but the import is dead. | Remove unused import; if temp files are needed later, pair with `try/finally` or `contextlib.closing`. | No leaked handles. |
| **LOW** | L2 — Model hardcoded, no rationale, misleading labels | `agent.py:60` `model="gpt-4o-mini"` is a positional default, no env override, no comment on why mini vs full. FE `pages/health.py:56` and logs claim "DeepSeek V3"/"cometsuno adapter" which is the dead module. | Make model `settings.orchestrator_model` (env-overridable); document the cost/latency rationale; fix FE/health labels to the real model. | Configurable + honest model selection. |
| **LOW** | L3 — `logs/` committed to the repo | `massloop-be/logs/session_*.log`, `massloop_*.log`, `errors_*.log` are present and would be deployed/committed. Session logs may contain user prompts/profile data. | Add `logs/` to `.gitignore`; ship empty log dir or write to a volume; scrub committed logs. | Don't commit runtime/PII logs. |

---

## Checklist answers (yes/no + evidence)

| Checklist item | Result | Evidence |
|----------------|--------|----------|
| Bare `except:` swallowing? | **Yes (4)** — all in dead `externals.py` (122, 508, 1504, 1816); live path uses broad `except Exception` that hides cause (H2/M2) | see H2, M2 |
| Tests at all? | **No** — zero test files, no `pytest` | see C2 |
| CI/CD quality gates? | **No** — no `.github/`, no lint/test in `railway.toml`/`nixpacks.toml` | see C2 |
| Reproducible runs (run IDs/seed)? | **No** — no run_id/seed/trace_id; `random.choice` fallback is non-deterministic | see H3 |
| `shell=True` with user input? | **No** — 0 occurrences in BE; no subprocess calls in generation path | grep: 0 |
| Temp file cleanup (mkdtemp)? | **N/A / clean** — `tempfile` imported but unused; no `mkdtemp` leaks on live path | see L1 |
| Model selection rationale? | **Weak** — hardcoded `gpt-4o-mini`, no env, misleading "DeepSeek V3" labels | see C3, L2 |
| Cost tracking? | **Broken/absent on live path** — config exists but unenforced; tracking code is dead | see C1 |
| Latency SLOs? | **Inconsistent/unmeasured** — 55s chat vs 120s gen; config unused; no metrics | see M1 |
| Fallback depth? | **Shallow, non-deterministic** — 1-level rule-based/random fallback; primary→direct-CometAPI in `_run_approved_generation` | see H3, C3 |

---

## Recommended remediation order

1. **Fix/delete `externals.py`** so the repo compiles; reconcile docs with the real `agent.py`+`tools.py` path (C2, C3).
2. **Enforce the budget SLO** on the live generation path and add a test (C1).
3. **Add CI** (lint + import smoke test + pytest) gating deploys (C2).
4. **Lock down CORS** and **surface errors** with alerting instead of swallowing (H1, H2).
5. **Add run IDs/seed + latency metrics** for reproducibility and SLO observability (H3, M1).

---

*Roast generated by static analysis only. No code was executed against live services; `logs/` files were read as evidence of runtime behaviour.*
