import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.controllers.performance_router import router as performance_router
from app.controllers.profile_router import router as profile_router
from app.controllers.stripe_router import router as stripe_router
from app.controllers.trial_router import router as trial_router
from app.orchestrator import MusicOrchestratorAgent

app = FastAPI(title="Massloop API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy orchestrator init: only build when OPENAI_API_KEY is set
orchestrator = None
if __import__("os").getenv("OPENAI_API_KEY"):
    orchestrator = MusicOrchestratorAgent()
    performance_router.orchestrator = orchestrator

app.include_router(performance_router)
app.include_router(profile_router)
app.include_router(stripe_router)
app.include_router(trial_router)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}