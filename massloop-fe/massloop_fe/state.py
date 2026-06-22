import os
import reflex as rx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class MassloopState(rx.State):
    # ── Energy controls ──
    def decrement_energy(self):
        """Decrease energy by 0.1, not going below 0.1."""
        self.energy = max(0.1, self.energy - 0.1)

    def increment_energy(self):
        """Increase energy by 0.1, not exceeding 1.0."""
        self.energy = min(1.0, self.energy + 0.1)

    @rx.var
    def energy_pct(self) -> int:
        return max(1, min(100, int(self.energy * 100)))

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

    # ── Soundflow Control (deck / queue) ──
    queue_items: list[dict] = []
    crossfader: float = 0.5
    master_volume: float = 0.8
    active_deck: str = "A"

    @rx.var
    def has_queue_items(self) -> bool:
        return len(self.queue_items) > 0

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
        """Full gen→play cycle: queue → approve → poll → result."""
        import httpx
        import asyncio

        try:
            async with httpx.AsyncClient() as client:
                # 1. Create queue item
                r = await client.post(
                    f"{BACKEND_URL}/api/performance/queue",
                    json={
                        "prompt": f"{self.style} at {self.bpm} BPM",
                        "style": self.style,
                        "bpm": self.bpm,
                        "energy": self.energy,
                        "venue": self.venue,
                    },
                    timeout=10,
                )
                if r.status_code != 200:
                    self.last_generated_status = f"queue error: {r.status_code}"
                    return

                task_id = r.json().get("id", "")
                self.last_generated_id = task_id
                self.last_generated_status = "pending_approval"

                # 2. Approve (triggers background generation)
                r2 = await client.post(
                    f"{BACKEND_URL}/api/performance/approve/{task_id}",
                    json={"approved_by": "stage_operator"},
                    timeout=10,
                )
                if r2.status_code != 200:
                    self.last_generated_status = f"approve error: {r2.status_code}"
                    return

                self.last_generated_status = "generating"

                # 3. Poll status until complete or failed
                for _ in range(24):  # max ~120s
                    await asyncio.sleep(5)
                    r3 = await client.get(
                        f"{BACKEND_URL}/api/performance/status/{task_id}",
                        timeout=10,
                    )
                    if r3.status_code != 200:
                        continue
                    status = r3.json().get("status", "")
                    self.last_generated_status = status

                    if status == "complete":
                        # 4. Fetch result
                        r4 = await client.get(
                            f"{BACKEND_URL}/api/performance/result/{task_id}",
                            timeout=10,
                        )
                        if r4.status_code == 200:
                            result = r4.json().get("result") or {}
                            self.audio_url = result.get("audio_url", "")
                            self.last_generated_status = "✅ ready"
                        else:
                            self.last_generated_status = "result error"
                        break

                    if status == "failed":
                        self.last_generated_status = "❌ failed"
                        break

                await self.poll_queue()
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

    # ── Soundflow Control events ──
    async def fetch_latest_generated(self):
        """GET /queue → find last completed task → GET /result/{id} → set audio_url."""
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{BACKEND_URL}/api/performance/queue", timeout=10)
                if r.status_code != 200:
                    self.last_generated_status = f"queue error: {r.status_code}"
                    return

                queue = r.json().get("queue", [])
                if not queue:
                    self.last_generated_status = "queue empty"
                    return

                # Find last completed task
                completed = [t for t in queue if t.get("status") == "complete"]
                if not completed:
                    self.last_generated_status = "no completed tracks"
                    return

                last = completed[-1]
                task_id = last.get("id", "")
                self.last_generated_id = task_id

                r2 = await client.get(
                    f"{BACKEND_URL}/api/performance/result/{task_id}", timeout=10
                )
                if r2.status_code == 200:
                    result = r2.json().get("result") or {}
                    self.audio_url = result.get("audio_url", "")
                    self.last_generated_status = "✅ loaded from queue"
                else:
                    self.last_generated_status = f"result error: {r2.status_code}"
        except Exception as e:
            self.last_generated_status = f"error: {str(e)[:40]}"

    async def fetch_queue(self):
        """Load full queue into queue_items for the Soundflow track list."""
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{BACKEND_URL}/api/performance/queue", timeout=10)
                if r.status_code == 200:
                    self.queue_items = r.json().get("queue", [])
                    self.queue_length = len(self.queue_items)
                else:
                    self.queue_items = []
        except Exception:
            self.queue_items = []

    async def approve_track(self, task_id: str):
        """Approve a pending track in the queue."""
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{BACKEND_URL}/api/performance/approve/{task_id}",
                    json={"approved_by": "stage_operator"},
                    timeout=10,
                )
                if r.status_code == 200:
                    await self.fetch_queue()
        except Exception:
            pass

    def set_crossfader(self, value: list[float]):
        try:
            self.crossfader = float(value[0]) if value else self.crossfader
        except (ValueError, IndexError):
            pass

    def set_master_volume(self, value: list[float]):
        try:
            self.master_volume = float(value[0]) if value else self.master_volume
        except (ValueError, IndexError):
            pass

    def start(self):
        return rx.redirect("/mix-trial")