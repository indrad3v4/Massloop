"""System health check page"""
import reflex as rx
from ..state import MassloopState
from ..components import page_container

WHITE = "#f0ede8"
AMBER = "#d4a853"
SLATE = "#6b7d8d"
DARK = "#1a1a1a"
BORDER = "#333333"

def health_check() -> rx.Component:
    return page_container(
        rx.vstack(
            rx.heading("System Status", size="6", color=WHITE, font_weight="600"),
            rx.text(f"Backend: {MassloopState.backend_status}",
                    color=rx.cond(MassloopState.backend_ok, AMBER, "#b8544a")),
            rx.button(
                "Refresh",
                on_click=MassloopState.check_health,
                variant="outline",
                border_color=BORDER, color=WHITE,
                _hover={"border_color": AMBER, "color": AMBER},
            ),
            spacing="4", padding="2rem",
        ),
        background_color=DARK, min_height="100vh",
    )
