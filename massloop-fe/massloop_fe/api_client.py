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


async def get_artist_profile(artist_id: str):
    """GET /api/artist/profile/{artist_id} -> artist identity."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BACKEND_URL}/api/artist/profile/{artist_id}", timeout=10
        )
        r.raise_for_status()
        return r.json()


async def learn_from_chat(artist_id: str, message: str):
    """POST /api/artist/learn -> teach the agent the artist's identity."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BACKEND_URL}/api/artist/learn",
            params={"artist_id": artist_id, "message": message},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()


async def get_budget():
    """GET /budget -> remaining daily budget (EUR)."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BACKEND_URL}/budget", timeout=10)
        r.raise_for_status()
        return r.json()
