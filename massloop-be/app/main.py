from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .controllers.performance_router import router as performance_router
from .controllers.profile_router import router as profile_router

app = FastAPI(title="Massloop API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(performance_router)
app.include_router(profile_router)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
