"""Massloop Landing Page — Entry point for the user journey"""
import reflex as rx
from ..state import MassloopState
from ..components import (
    scanlines_overlay, terminal_box, 
    BLACK, GREEN, PINK, AMBER, GRAY, WHITE, SLATE,
)

def landing_page() -> rx.Component:
    return rx.fragment(
        scanlines_overlay(),
        rx.vstack(
            # ── Nav Bar (Simplified for landing) ──
            rx.hstack(
                rx.text("massloop", font_weight="700", color=GREEN, font_size="5"),
                rx.spacer(),
                rx.link("studio", href="/stage", color=SLATE, _hover={"color": GREEN}, font_size="2"),
                padding="1rem 2rem",
                border_bottom=f"1px solid {GREEN}22",
                background_color=BLACK,
                width="100%",
            ),

            # ── Hero Section ──
            rx.vstack(
                rx.text("MASSLOOP", font_size="9", font_weight="900",
                        color=GREEN, class_name="pulse-glow"),
                rx.text("AI handles grunt work, you handle the soul",
                        color=WHITE, font_size="4", font_weight="600",
                        text_align="center", margin_top="1rem"),
                
                terminal_box(
                    rx.vstack(
                        rx.text(
                            "Massloop is a stage-confidence amplifier. "
                            "It leverages a Multi-Agent Orchestrator (MOA) to generate "
                            "underground electronic music in real-time, allowing you to "
                            "focus on the performance while the AI manages the technical "
                            "grunt work of track structure, energy flow, and sonic cohesion.",
                            color=SLATE, font_size="2", text_align="center",
                            line_height="1.5",
                        ),
                        spacing="4",
                        align_items="center",
                    ),
                    width="90%",
                    max_width="600px",
                    margin_y="2rem",
                ),

                rx.button(
                    "▶ ENTER THE STUDIO",
                    on_click=rx.redirect("/onboard"),
                    background_color=GREEN,
                    color=BLACK,
                    font_weight="700",
                    font_size="4",
                    padding="1rem 3rem",
                    border="none",
                    border_radius="0",
                    class_name="glitch-hover",
                    _hover={
                        "background_color": PINK,
                        "box_shadow": f"0 0 20px {GREEN}66",
                    },
                ),

                rx.text(
                    "demo: $0.50/track · no subscription",
                    color=AMBER, font_size="1", margin_top="1rem",
                ),

                spacing="6",
                align_items="center",
                padding="4rem 0",
            ),

            # ── Footer ──
            rx.hstack(
                rx.text("v0.1.0 · ", color=GRAY, font_size="1"),
                rx.link("massloop.run", href="https://massloop.run", color=GREEN, font_size="1"),
                rx.text(" · built with fastapi + reflex + suno", color=GRAY, font_size="1"),
                justify="center",
                padding="2rem 0",
            ),

            spacing="0",
            min_height="100vh",
            background_color=BLACK,
            align_items="center",
        ),
    )