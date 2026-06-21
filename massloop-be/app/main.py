from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .controllers import performance_router as performance_module
from .controllers.performance_router import router as performance_router
from .controllers.profile_router import router as profile_router
from .orchestrator import MusicOrchestratorAgent

app = FastAPI(title="Massloop API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the AI orchestrator and inject it into the performance router.
orchestrator = MusicOrchestratorAgent()
performance_module.set_orchestrator(orchestrator)

app.include_router(performance_router)
app.include_router(profile_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
