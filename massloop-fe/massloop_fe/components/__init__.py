"""Reusable Reflex UI components for Massloop"""
import reflex as rx

SURFACE = "#2a2a2a"
BORDER = "#333333"

def page_container(*children, **props) -> rx.Component:
    return rx.center(
        rx.container(*children, max_width="1200px", padding="2rem"), **props,
    )

def card(children, *props) -> rx.Component:
    return rx.box(
        *children,
        background_color=SURFACE,
        border=f"1px solid {BORDER}",
        border_radius="8px",
        padding="1.5rem",
        **props,
    )

def nav_bar() -> rx.Component:
    return rx.hstack(
        rx.text("Massloop", font_weight="700", color="#f0ede8"),
        rx.spacer(),
        rx.link("Dashboard", href="/", color="#6b7d8d"),
        rx.link("Health", href="/health", color="#6b7d8d"),
        padding="1rem 2rem",
        border_bottom=f"1px solid {BORDER}",
        background_color=SURFACE,
    )
