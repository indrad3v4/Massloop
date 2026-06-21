import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.controllers.performance_router import router as performance_router, set_orchestrator
from app.controllers.profile_router import router as profile_router
from app.orchestrator import MusicOrchestratorAgent

app = FastAPI(title="Massloop API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator when COMETAPI_KEY is configured.
if settings.cometapi_key:
    orchestrator = MusicOrchestratorAgent()
    set_orchestrator(orchestrator)

app.include_router(performance_router)
app.include_router(profile_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
