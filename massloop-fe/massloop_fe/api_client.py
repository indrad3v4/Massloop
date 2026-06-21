import httpx

BACKEND_URL = "http://localhost:8000"

async def get_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BACKEND_URL}/health", timeout=5)
        r.raise_for_status()
        return r.json()
