import reflex as rx
from .pages import (
    index, 
    landing_page, 
    onboard_page, 
    library_page, 
    performance_page,
    health_check, 
    mix_trial_page,
    artist_sound_page,
)

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
app.add_page(index, route="/", title="Massloop · landing")
app.add_page(onboard_page, route="/onboard", title="Massloop · onboarding")
app.add_page(library_page, route="/library", title="Massloop · library")
app.add_page(performance_page, route="/stage", title="Massloop · live")
app.add_page(artist_sound_page, route="/my-sound", title="Massloop · my sound")
app.add_page(health_check, route="/health", title="Massloop · health")
app.add_page(mix_trial_page, route="/mix-trial", title="Massloop · mix trial")
