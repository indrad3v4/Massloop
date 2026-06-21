"""Massloop landing page"""
import reflex as rx
from ..state import MassloopState
from ..components import page_container

WHITE = "#f0ede8"
AMBER = "#d4a853"
SLATE = "#6b7d8d"
DARK = "#1a1a1a"

def index() -> rx.Component:
    return page_container(
        rx.vstack(
            rx.spacer(),
            rx.heading("Massloop", size="9", color=WHITE, letter_spacing="-0.02em", font_weight="700"),
            rx.text("AI-powered DJ platform", color=SLATE, font_size="1.125rem", margin_top="0.5rem"),
            rx.button(
                "Get Started",
                on_click=MassloopState.start,
                background_color=AMBER,
                color=DARK,
                font_weight="600",
                padding="0.75rem 2rem",
                border_radius="8px",
                _hover={"background_color": "#c49a48", "transform": "translateY(-1px)"},
                margin_top="2rem",
            ),
            rx.spacer(),
            spacing="0", height="100%", width="100%",
        ),
        background_color=DARK, min_height="100vh",
    )
