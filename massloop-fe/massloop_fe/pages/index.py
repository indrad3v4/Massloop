"""Massloop Index Page — Root route with first-visit detection"""
import reflex as rx
from ..state import MassloopState
from .landing import landing_page

@rx.page(route="/", on_mount=MassloopState.check_first_visit)
def index() -> rx.Component:
    return landing_page()