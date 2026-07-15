import os
import sys
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.controllers.performance_router import router as performance_router, set_orchestrator
from app.controllers.profile_router import router as profile_router
from app.controllers.stripe_router import router as stripe_router
from app.controllers.trial_router import router as trial_router
from app.controllers.orchestrator_router import router as orchestrator_router, set_orchestrator as set_router_orchestrator
from app.controllers.artist_router import router as artist_router
from app.controllers.stream_router import router as stream_router
from app.orchestrator import MusicOrchestratorAgent
# Infrastructure layer: budget guardrails (config-driven, enforced on live path)
from app.services.externals import build_guardrails, BudgetExceededError

# ── Production env validation ──
_MISSING = []
if not os.getenv("COMETAPI_KEY"):
    _MISSING.append("COMETAPI_KEY")
if not os.getenv("STRIPE_SECRET_KEY"):
    logger.warning("STRIPE_SECRET_KEY not set — Stripe checkout disabled")
if not os.getenv("MASSLOOP_DATA_DIR"):
    os.environ.setdefault("MASSLOOP_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
    logger.info(f"MASSLOOP_DATA_DIR defaulted to {os.environ['MASSLOOP_DATA_DIR']}")

if _MISSING:
    raise RuntimeError(
        f"Missing required env vars: {', '.join(_MISSING)}. "
        f"Set them in Railway → Variables or .env file."
    )

app = FastAPI(title="Massloop API", version="0.1.0")

# Budget guardrail is built + surfaced via GET /budget (live enforcement
# SLO is NOT yet consulted on the generation path — tracked as partial fix.
budget_guardrails = build_guardrails(
    daily_limit_eur=settings.daily_budget_eur,
    max_track_cost_eur=settings.max_track_cost_eur,
)
app.state.budget_guardrails = budget_guardrails

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy orchestrator init: only build when OPENAI_API_KEY is set
orchestrator = None
if os.getenv("OPENAI_API_KEY"):
    orchestrator = MusicOrchestratorAgent()
    set_orchestrator(orchestrator)
    set_router_orchestrator(orchestrator)
    logger.info("Orchestrator agent initialized")
else:
    logger.info("OPENAI_API_KEY not set — orchestrator disabled (mock mode)")

app.include_router(performance_router)
app.include_router(profile_router)
app.include_router(stripe_router)
app.include_router(trial_router)
app.include_router(orchestrator_router, tags=["orchestrator"])
app.include_router(artist_router)
app.include_router(stream_router)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/budget")
async def budget() -> Dict[str, Any]:
    """Infrastructure-layer budget status (live enforcement SLO, C1)."""
    return {
        "status": "ok",
        "budget": budget_guardrails.get_budget_status().to_dict(),
    }