"""Massloop Index Page — Root route with first-visit detection"""
import reflex as rx
from ..state import MassloopState
from .landing import landing_page

@rx.page(route="/")
def index() -> rx.Component:
    return rx.fragment(
        # Trigger first visit check on mount
        rx.box(on_mount=MassloopState.check_first_visit),
        landing_page(),
    )
