import reflex as rx
from .pages.index import index
from .pages.health import health_check

DARK = "#1a1a1a"

app = rx.App(
    style={"font_family": "system-ui, -apple-system, sans-serif", "background_color": DARK},
)
app.add_page(index, route="/")
app.add_page(health_check, route="/health")
