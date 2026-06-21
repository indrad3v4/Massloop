import os
import reflex as rx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

class MassloopState(rx.State):
    backend_status: str = "checking..."
    backend_ok: bool = False

    # ── Stage / performance ──
    queue_length: int = 0
    last_generated_id: str = ""
    last_generated_status: str = ""
    buffer_ready: int = 0
    energy: float = 0.7
    bpm: int = 140
    style: str = "ACID_TECHNO"

    # ── Mix trial ──
    trial_status: str = ""
    audio_url: str = ""
    venue: str = "club"
    tags: str = ""
    stripe_url: str = ""

    # ── Health check ──
    async def check_health(self):
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{BACKEND_URL}/health", timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    self.backend_status = f"v{data.get('version', '?')} — online"
                    self.backend_ok = True
                else:
                    self.backend_status = f"error: {r.status_code}"
                    self.backend_ok = False
        except Exception as e:
            self.backend_status = f"unreachable: {str(e)[:40]}"
            self.backend_ok = False

    # ── Queue polling ──
    async def poll_queue(self):
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{BACKEND_URL}/api/performance/queue", timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    self.queue_length = len(data.get("queue", []))
        except Exception:
            self.queue_length = -1

    # ── Generate (stage) ──
    async def generate(self):
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{BACKEND_URL}/api/performance/queue",
                    json={"prompt": "test", "style": self.style, "bpm": self.bpm, "energy": self.energy},
                    timeout=10,
                )
                if r.status_code == 200:
                    data = r.json()
                    self.last_generated_id = data.get("id", "")
                    self.last_generated_status = "submitted"
                    await self.poll_queue()
                else:
                    self.last_generated_status = f"error: {r.status_code}"
        except Exception as e:
            self.last_generated_status = f"error: {str(e)[:40]}"

    # ── Start trial (mix trial flow) ──
    async def start_trial(self):
        self.trial_status = "queued..."
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{BACKEND_URL}/api/trial/start",
                    json={
                        "prompt": f"{self.tags} for {self.venue}",
                        "tags": self.tags,
                        "bpm": self.bpm,
                        "energy": self.energy,
                        "venue": self.venue,
                        "style": self.tags.split()[0] if self.tags else "deep house",
                    },
                    timeout=10,
                )
                if r.status_code == 200:
                    data = r.json()
                    self.trial_status = f"task_id: {data.get('task_id')}"
                    import asyncio
                    await asyncio.sleep(5)
                    r2 = await client.get(
                        f"{BACKEND_URL}/api/trial/result/{data.get('task_id')}",
                        timeout=15,
                    )
                    if r2.status_code == 200:
                        res = r2.json()
                        if res.get("status") == "complete":
                            self.audio_url = res.get("result", {}).get("audio_url", "")
                            self.trial_status = "✅ Trial ready"
                        else:
                            self.trial_status = f"status: {res.get('status')}"
                    else:
                        self.trial_status = "poll failed"
                else:
                    self.trial_status = f"error: {r.status_code}"
        except Exception as e:
            self.trial_status = f"failed: {str(e)[:40]}"

    # ── Stripe checkout ──
    async def start_checkout(self):
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{BACKEND_URL}/api/stripe/checkout",
                    json={},
                    timeout=10,
                )
                if r.status_code == 200:
                    data = r.json()
                    self.stripe_url = data.get("url", "")
                    return rx.redirect(data.get("url", ""))
                else:
                    self.trial_status = "Stripe not configured"
        except Exception as e:
            self.trial_status = f"checkout error: {str(e)[:40]}"

    # ── Setters ──
    def set_venue(self, value: str):
        self.venue = value

    def set_bpm(self, value: list[float]):
        try:
            self.bpm = int(value[0]) if value else self.bpm
        except (ValueError, IndexError):
            pass

    def set_energy(self, value: list[float]):
        try:
            self.energy = float(value[0]) if value else self.energy
        except (ValueError, IndexError):
            pass

    def set_tags(self, value: str):
        self.tags = value

    def set_style(self, value: str):
        self.style = value

    def increment_bpm(self):
        self.bpm = min(200, self.bpm + 5)

    def decrement_bpm(self):
        self.bpm = max(80, self.bpm - 5)

    def start(self):
        return rx.redirect("/mix-trial")
