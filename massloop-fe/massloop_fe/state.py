import reflex as rx

class MassloopState(rx.State):
    backend_status: str = "checking..."
    backend_ok: bool = False

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

    def start(self):
        return rx.redirect("/health")
