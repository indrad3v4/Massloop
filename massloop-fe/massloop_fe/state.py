import reflex as rx

class MassloopState(rx.State):
    backend_status: str = "checking..."
    backend_ok: bool = False
    trial_status: str = ""
    audio_url: str = ""
    venue: str = "club"
    bpm: int = 124
    energy: float = 0.7
    tags: str = ""
    stripe_url: str = ""

    async def check_health(self):
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.get("http://localhost:8000/health", timeout=5)
                if r.status_code == 200:
                    self.backend_status = "connected"
                    self.backend_ok = True
                else:
                    self.backend_status = f"error: {r.status_code}"
        except Exception as e:
            self.backend_status = f"unreachable: {str(e)[:40]}"
            self.backend_ok = False

    async def start_trial(self):
        self.trial_status = "queued..."
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "http://localhost:8000/api/trial/start",
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
                    # Poll for result
                    import asyncio
                    await asyncio.sleep(5)
                    r2 = await client.get(
                        f"http://localhost:8000/api/trial/result/{data.get('task_id')}",
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

    async def start_checkout(self):
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "http://localhost:8000/api/stripe/checkout",
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

    def set_venue(self, value: str):
        self.venue = value

    def set_bpm(self, value: str):
        try:
            self.bpm = int(value)
        except ValueError:
            pass

    def set_energy(self, value: str):
        try:
            self.energy = float(value)
        except ValueError:
            pass

    def set_tags(self, value: str):
        self.tags = value

    def start(self):
        return rx.redirect("/mix-trial")
