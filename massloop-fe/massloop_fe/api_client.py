import os
import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

async def get_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BACKEND_URL}/health", timeout=5)
        r.raise_for_status()
        return r.json()

async def get_queue():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BACKEND_URL}/api/performance/queue", timeout=5)
        r.raise_for_status()
        return r.json()

async def create_queue_item(prompt: str, style: str = "ACID_TECHNO", bpm: int = 140, energy: float = 0.7):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BACKEND_URL}/api/performance/queue",
            json={"prompt": prompt, "style": style, "bpm": bpm, "energy": energy},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
