# Massloop PR#1 Forensic Text Audit (every page)

**Branch:** `feat/prism-apply`  **Audit date:** 2025-07-15
**Scope:** every user-facing string + every doc/claim vs. the ACTUAL code (ai-engineering-loop verifier vs. claimed pipeline stages, applied to COPY).
**Method:** full static read of all mandated files + targeted grep cross-checks. Read-only; findings are local.

---

## TL;DR

- **🔴 DEAD-CLAIMS found: 9** (text says X works; code proves it is stub/dead/wrong URL).
- **🟡 CONTRADICTIONS: 4** (two strings disagree, including README vs. README).
- **🟢 STALE-ROASTS: 3** (roast docs describe pre-fix state; fixes landed in PR#1).
- **🔵 NDA-LEAK: 0 true leaks.** `Certrux` / `MotorsAgent` / `UOP` / real-client = **0 hits**. One borderline watch-item: the internal prism-spec label `Client#94` appears in a production code comment — see NDA section. Not a real client.

**Headline:** PR#1 genuinely fixed the model-layer stubs (roast_model 🔴#1/#2/#3) and wired artist memory into generation (roast_application CRITICAL #1). But the **product copy never caught up**: README/landing/stage still advertise a "Mixture of Agents (MOA)" 4-agent negotiate pipeline that does not exist (it is a single orchestrator + cosmetic `asyncio.sleep` stage labels), and the README still sells a PAYG/no-subscription model while the only Stripe path is subscription.

---

## Severity Table

| Sev | Type | String (quoted) | file:line | Contradicts (code evidence) | Fix |
|-----|------|-----------------|-----------|------------------------------|-----|
| 🔴 | DEAD-CLAIM | "**Mixture of Agents** — several LLM agents argue, negotiate, and synthesize a track **for your set**: … 🎯 Director … 🎛️ Mixer … ✍️ Lyricist … ✅ Critic" | README.md:26-34 (both duplicated copies) | No MOA exists. Live gen = single `MusicOrchestratorAgent.decide_and_generate`. The 4 "agents" are cosmetic `asyncio.sleep(0.5)` labels in `performance_router.py:263-273`. | Rewrite README to describe the real single-orchestrator + HITL-approve pipeline; delete the 4-agent table. |
| 🔴 | DEAD-CLAIM | "orchestrator/ OpenAI Agents SDK + **MOA pipeline**" (stack diagram) | README.md:56 (both copies) | Same as above — no MOA pipeline module/code anywhere (grep `Mixture|MOA|mixer.*lyricist` returns only copy + cosmetic sleeps). | Same as above. |
| 🔴 | DEAD-CLAIM | "🧠 Your AI agents / **Mixture of Agents** — several LLM agents argue, negotiate, and synthesize" | README.md:125-134 | Same as above. | Same. |
| 🔴 | DEAD-CLAIM | "It leverages a **Multi-Agent Orchestrator (MOA)** to generate underground electronic music in real-time" | massloop-fe/massloop_fe/pages/landing.py:36-39 | No MOA; single agent. `agent.py` is one `MusicOrchestratorAgent`. | Change copy to "AI orchestrator" (single agent). |
| 🔴 | DEAD-CLAIM | Stage labels `director` / `mixer` / `lyricist` / `critic` shown as live pipeline progress ("🧠 director: choosing track structure…", etc.) | massloop-fe/massloop_fe/state.py:302-311 (STAGE_LABELS) + performance.py:206 | In `_run_approved_generation` the stages are hardcoded `await asyncio.sleep(0.5)` with **no** director/mixer/lyricist/critic logic (`performance_router.py:263-273`). The strings imply 4 real sub-agents. | Either implement the stages or relabel them as cosmetic progress ("queued → generating → ready"). |
| 🔴 | DEAD-CLAIM | "POST `/api/payg/purchase` — Buy a track pack (PAYG)" | README.md:75 (both copies) | Endpoint does **not exist**. Only Stripe routes are `/api/stripe/checkout`, `/portal`, `/webhook` (`stripe_router.py:11,30,47,62`). No PAYG/track-pack purchase anywhere in repo. | Remove the endpoint row, or implement `/api/payg/purchase`. |
| 🔴 | DEAD-CLAIM | "**No subscriptions.** No extra steps. … Subscriptions are dead. No €9/mo, no €29/mo." | README.md:10,20 (both copies) | The ONLY Stripe path is `mode="subscription"` checkout with `price_dj_starter`/`price_pro` (`stripe_router.py:16-17,36-41`). No PAYG purchase exists (see above). Copy contradicts the implemented code. | Either ship PAYG or change copy to "subscription-based". |
| 🔴 | DEAD-CLAIM | "Upgrade to DJ Starter — **€9/mo**" (button on trial page) | massloop-fe/massloop_fe/pages/mix_trial_page.py:103 | Directly contradicts README "Subscriptions are dead. No €9/mo". Also the only Stripe tier is subscription-based. | Align with actual billing model. |
| 🔴 | DEAD-CLAIM | Orchestrator chat panel posts to `/api/chat/orchestrator` (user-facing "tell the orchestrator…" box on stage) | massloop-fe/massloop_fe/state.py:633-634 (`send_chat`) | Route mounts at `/api` (main.py:71) + router prefix `/api/chat` (orchestrator_router.py:13) → real path is **`/api/api/chat/orchestrator`**. FE hits `/api/chat/orchestrator` → **404**. The whole orchestrator-chat feature is dead for the FE. (Double-`/api` bug, pre-flagged in roast_application.md cross-cutting, still open.) | Fix the mount (drop prefix on router or on include_router) so the path matches. |
| 🔴 | DEAD-CLAIM (code comment) | main.py:39-41 — "The live generation path (owned by other subagents) imports `app.main.budget_guardrails` to **enforce** the daily/per-track cost SLO (docs/roast_infrastructure.md C1)." | massloop-be/app/main.py:38-41 | Grep `budget|guardrail|daily_budget` in `performance_router.py` = **0 hits**. `budget_guardrails` is built + exposed at `/budget` but **never imported or consulted** by the generation path. The comment claims enforcement that does not happen. | Either enforce (call `budget_guardrails.check(...)` before generation) or soften the comment to "surfaced via /budget". |
| 🟡 | CONTRADICTION | README: "Cost: **~$0.08–0.15/track**" | README.md:39 (both copies) | vs. landing.py:69 "demo: **$0.50/track**" vs. roast_model/roast_application "**~$0.40/track**" (`tools.py` actual Suno cost). Three different prices in copy. | Pick one true number (per real Suno/CometAPI billing) and use it everywhere. |
| 🟡 | CONTRADICTION | README: "**No subscriptions.**" | README.md:10,20 | vs. README itself: "POST `/api/stripe/webhook` — Payment confirmation" + the only implemented billing is subscription checkout. Internal self-contradiction. | Reconcile (see DEAD-CLAIM #7). |
| 🟡 | CONTRADICTION | README: "Synthesis: CometAPI → Suno **v4/v5** (`chirp-v4`, `chirp-auk`, `chirp-crow`)" | README.md:38 | `tools.py:38` documents `mv` as `chirp-v3.0, chirp-v3.5, chirp-v4, chirp-auk, chirp-crow` — **no "v5"** value. "v5" is fictional in this call path. | Drop "v5" or map to a real mv string. |
| 🟡 | CONTRADICTION | landing.py:69 "demo: $0.50/track · no subscription" | landing.py:69 | Contradicts the subscription-only Stripe implementation (DEAD-CLAIM #7/#8) and the €9/mo upsell. | Align. |
| 🟢 | STALE-ROAST | roast_model.md — three 🔴 findings (#1 stubs return constants, #2 no fallback chain, #3 cost €0.00/unenforced) describe pre-fix `agent.py`. | docs/roast_model.md:13-15 | PR#1 REPLACED the stubs with real `optimize_generation_request` / `evaluate_track_quality` / `analyze_cost_efficiency` and added the gpt-4o-mini→OpenAI→DeepSeek fallback chain (`agent.py:1-16,408-525`). Findings #1 and #2 are **FIXED**. #3 is **PARTIALLY** fixed: `analyze_cost_efficiency` now reads real spend, but the guardrail is still not enforced on the live gen path (see DEAD-CLAIM #10). | Add a "**FIXED in PR#1**" header; downgrade #3 to "partial — surfaced not enforced". |
| 🟢 | STALE-ROAST | roast_application.md CRITICAL #1 — "Persistent-growth memory is dead code … `_run_approved_generation` calls `decide_and_generate` **without `artist_brand`** … every track generated with zero learned identity." | docs/roast_application.md:11-12 | PR#1 ADDED `_load_artist_brand(artist_id)` (performance_router.py:208-260) and calls it at line 260 before `decide_and_generate(..., artist_brand=artist_brand)`. Memory **is now wired into generation**. | Add "**FIXED in PR#1**" header to CRITICAL #1. |
| 🟢 | STALE-ROAST | roast_application.md cross-cutting "Double `/api` prefix bug … `/api/api/chat/orchestrator`" | docs/roast_application.md:44 | This bug is **STILL OPEN** (confirmed above, DEAD-CLAIM #9). The roast presents it as a pre-fix latent issue; it remains a live 404. | Mark as "**STILL OPEN in PR#1**" — not fixed. |
| 🔵 | NDA (watch) | `Client#94` "audience-gap" referenced in a production code comment | massloop-be/app/controllers/performance_router.py:258 | "Client#94" is an **internal prism-spec lens ID** (docs/prism-specs/*), NOT a real customer. No `Certrux`/`MotorsAgent`/`UOP`/customer-name leak anywhere (grep = 0). Flagged only because the forbidden word "client" appears in an internal label. | Safe to keep, but consider renaming the prism label to avoid the "client" token in shipped code comments. |

---

## Per-page / per-doc verdict

| File | Verdict |
|------|---------|
| massloop-be/app/orchestrator/prompts.py | clean (0) — tools listed are real; prompt matches code. |
| massloop-be/app/orchestrator/agent.py | clean (0) — docstring (lines 1-16) accurately describes the PR#1 fixes; `optimize/evaluate/analyze` + fallback chain are real. |
| massloop-be/app/controllers/orchestrator_router.py | 1 finding — imports `learn_from_chat`/`build_artist_context` (line 11) but **never calls them** (dead imports); FE can't reach it anyway (double `/api`, see DEAD-CLAIM #9). |
| massloop-be/docs/systemPrompt.md | clean (0) — historical Replit TUI brief; clearly a pre-refactor artifact, not a live claim. No contradictions with running code worth flagging. |
| massloop-be/docs/massloopBrief.md | clean (0) — strategy brief; architecture described is the CLI/Clean-Arch intent, consistent with its own scope. |
| massloop-be/docs/pitch.md | clean (0) — investor deck; market/feature claims are aspirational, not code-level "X works" claims. |
| massloop-be/app/controllers/performance_router.py | 2 findings — cosmetic MOA stage sleeps (DEAD-CLAIM #5); `Client#94` prism label in comment (NDA watch). Memory wiring (lines 208-260) is correct. |
| massloop-be/app/controllers/artist_router.py | clean (0) — endpoints match FE calls (`/api/artist/profile`, `/api/artist/learn`, `/api/artist/feedback`). |
| massloop-be/app/controllers/stripe_router.py | clean (0) — subscription-only; accurately implements what it implements (no PAYG claim inside the file). |
| massloop-be/app/controllers/trial_router.py | clean (0) — "2-track mix trial" matches FE `mix_trial_page`. |
| massloop-be/app/controllers/stream_router.py | 1 finding — fully implemented SSE chat that **calls** `learn_from_chat`/`build_artist_context`, but is **never mounted** (main.py has no `include_router(stream_router)`). Dead path. |
| massloop-fe/massloop_fe/pages/landing.py | 1 finding — "Multi-Agent Orchestrator (MOA)" dead-claim (#4); also "$0.50/track · no subscription" contradiction (#contra). |
| massloop-fe/massloop_fe/pages/index.py | clean (0). |
| massloop-fe/massloop_fe/pages/performance.py | 1 finding — orchestrator chat panel + STAGE_LABELS imply a 4-agent pipeline (#5, #9). |
| massloop-fe/massloop_fe/pages/artist.py | clean (0) — "teach the agent" → `/api/artist/learn` works; budget wired; copy matches behavior. |
| massloop-fe/massloop_fe/pages/my_sound.py | clean (0) — "every track will sound like YOU" is now TRUE (memory wired into gen). Copy caught up. |
| massloop-fe/massloop_fe/pages/onboard.py | clean (0). |
| massloop-fe/massloop_fe/pages/mix_trial_page.py | 1 finding — "€9/mo" subscription upsell contradicts "no subscriptions" (#8). |
| massloop-fe/massloop_fe/pages/library.py | clean (0). |
| massloop-fe/massloop_fe/pages/health.py | 1 finding — "gpt-4o-mini · **cometsuno adapter** · chirp-v4" (line 56): gpt-4o-mini/chirp-v4 are now accurate post-fix, but "cometsuno adapter" is a fictional product name (no such adapter; it's CometAPI Suno). Low-severity dead-claim. |
| massloop-fe/massloop_fe/state.py | 2 findings — STAGE_LABELS advertise 4 agents (#5); `send_chat` posts to wrong URL (#9). |
| massloop-fe/massloop_fe/components/*.py | clean (0) — UI kit, no claims. |
| README.md | 5 findings — MOA 4-agent claim (#1-#4 duplicated), `/api/payg/purchase` nonexistent (#6), "no subscriptions" vs subscription (#7), price contradictions (#contra), AND the file is **corrupted/duplicated**: the entire body appears twice (lines 1-102 then 103-259) with a broken key literal injected at line 102 (`export COMETAPI_KEY="s# 🎛️ massloop.run`). |
| docs/roast_infrastructure.md | 1 finding — C1 (budget) partially addressed (guardrail built + /budget endpoint) but NOT enforced on gen path (#10); C2 (tests/CI) FIXED (CI + test_budget.py added, externals.py gutted); C3 (arch vs docs) partially open (README still says MOA). Needs "FIXED/PARTIAL" headers. |
| docs/roast_application.md | 3 findings — CRITICAL #1 (memory) FIXED (add header); "double /api" STILL OPEN (add header); "stream_router never mounted" STILL TRUE. |
| docs/roast_model.md | 3 findings — #1, #2 FIXED (#1 fallback + #2 real stubs); #3 PARTIAL (surfaced not enforced). Add headers. |

---

## NDA section (🔵)

- **Forbidden terms searched:** `Certrux`, `MotorsAgent`, `Motors Agent`, `UOP`, real `client` (customer). Result: **0 true leaks** across all `.py` and `.md` files.
- **Watch-item:** the internal prism-spec lens label `Client#94` (and siblings `Economy#46`, `Obstacle#66`, `Profit#96`, `Control#53`, `Feedback#57`, `Transparency#56`, `Inner Contradiction#82`, `Channels#59`, `Physical Interface#54`, `Virtual Interface#55`, `Modes#60`) appears in `performance_router.py:258` and throughout `docs/roast_application.md`. These are Schell-lens spec IDs, **not** customer references. No action required, but flagged because "client" is on the forbidden list — recommend renaming the prism label in shipped code comments to avoid ambiguity.

---

## One-line verdicts (scanned files)

- prompts.py → clean
- agent.py → clean (copy caught up to PR#1 fixes)
- orchestrator_router.py → 1 finding (dead imports + unreachable due to #9)
- systemPrompt.md → clean (historical artifact)
- massloopBrief.md → clean
- pitch.md → clean
- performance_router.py → 2 findings (#5, NDA-watch)
- artist_router.py → clean
- stripe_router.py → clean
- trial_router.py → clean
- stream_router.py → 1 finding (never mounted → dead path)
- landing.py → 1 finding (#4) + price contradiction
- index.py → clean
- performance.py → 1 finding (#5, #9)
- artist.py → clean
- my_sound.py → clean (copy now TRUE)
- onboard.py → clean
- mix_trial_page.py → 1 finding (#8)
- library.py → clean
- health.py → 1 finding (fictional "cometsuno adapter")
- state.py → 2 findings (#5, #9)
- components/*.py → clean
- README.md → 5 findings (MOA, nonexistent PAYG endpoint, subscription contradiction, price contradictions, corrupted/duplicated body)
- roast_infrastructure.md → 1 finding (stale; add FIXED/PARTIAL headers)
- roast_application.md → 3 findings (stale; add FIXED / STILL-OPEN headers)
- roast_model.md → 3 findings (stale; add FIXED / PARTIAL headers)

---

## Recommended copy fixes (highest impact)

1. **README.md** — delete the "Mixture of Agents" / 4-agent table / "MOA pipeline" claims; replace with the real single-orchestrator + HITL-approve description. Remove the `/api/payg/purchase` row (or implement it). Reconcile "no subscriptions" with the subscription-only Stripe code. De-duplicate + repair the corrupted body.
2. **landing.py / mix_trial_page.py / health.py** — drop "MOA"/"Multi-Agent Orchestrator", the €9/mo subscription upsell, and the fictional "cometsuno adapter".
3. **state.py STAGE_LABELS + performance.py** — relabel the cosmetic `director/mixer/lyricist/critic` stages as plain progress, OR implement them.
4. **main.py:38-41 comment** — either enforce `budget_guardrails` in `performance_router` (call before generation) or soften the comment to "surfaced via /budget, not yet blocking".
5. **orchestrator_router mount** — fix the double `/api` prefix so the FE chat panel actually reaches the agent.
6. **Roast docs** — stamp "FIXED in PR#1" (model stubs, fallback chain, artist-memory-in-gen) and "STILL OPEN in PR#1" (double-/api 404, budget not enforced on gen path) headers.
