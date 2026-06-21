import reflex as rx
from .pages.index import index
from .pages.health import health_check
from .pages.mix_trial_page import mix_trial_page
from .pages.performance import performance_page

# ── Rave aesthetic palette (suckpuck inspo) ──
BLACK  = "#0a0a0a"
GREEN  = "#00ff41"
PINK   = "#ff00ff"
AMBER  = "#ffb000"
GRAY   = "#2a2a2a"
WHITE  = "#e0e0e0"
SLATE  = "#6b7d8d"

def global_styles() -> dict:
    return {
        "font_family": "monospace, 'Courier New', system-ui",
        "background_color": BLACK,
        "color": GREEN,
        "::selection": {
            "background_color": PINK,
            "color": BLACK,
        },
    }

app = rx.App(
    style=global_styles(),
)
app.add_page(index, route="/", title="Massloop · stage")
app.add_page(health_check, route="/health", title="Massloop · health")
app.add_page(mix_trial_page, route="/mix-trial", title="Massloop · mix trial")
app.add_page(performance_page, route="/stage", title="Massloop · live")
