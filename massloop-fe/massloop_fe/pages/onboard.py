"""Massloop Onboarding Page — First-time user setup"""
import reflex as rx
from ..state import MassloopState
from ..components import (
    scanlines_overlay, terminal_box, 
    BLACK, GREEN, PINK, AMBER, GRAY, WHITE, SLATE,
)

def onboard_page() -> rx.Component:
    return rx.fragment(
        scanlines_overlay(),
        rx.vstack(
            # ── Nav Bar ──
            rx.hstack(
                rx.text("massloop", font_weight="700", color=GREEN, font_size="5"),
                rx.text(" · onboarding", color=SLATE, font_size="3"),
                padding="1rem 2rem",
                border_bottom=f"1px solid {GREEN}22",
                background_color=BLACK,
                width="100%",
            ),

            # ── Onboarding Content ──
            rx.vstack(
                rx.text("INITIALIZING STUDIO...", font_size="6", font_weight="700", color=GREEN),
                rx.text("Configure your sonic environment", color=SLATE, font_size="2"),
                
                terminal_box(
                    rx.vstack(
                        # Genre Selection
                        rx.vstack(
                            rx.text("$ select_genre", color=PINK, font_size="1", font_weight="600"),
                            rx.select(
                                ["ACID_TECHNO", "RAW_TECHNO", "INDUSTRIAL", "HARDGROOVE", "SCHRANZ",
                                 "BREAKBEAT", "JUNGLE", "HARDTEK", "DUB_TECHNO", "HYPNOTIC"],
                                default_value="ACID_TECHNO",
                                on_change=MassloopState.set_style,
                                background_color=BLACK,
                                border=f"1px solid {GREEN}44",
                                color=GREEN,
                                font_size="2",
                                width="100%",
                            ),
                            align_items="start",
                            spacing="2",
                            margin_bottom="1.5rem",
                        ),

                        # Venue Selection
                        rx.vstack(
                            rx.text("$ select_venue", color=PINK, font_size="1", font_weight="600"),
                            rx.select(
                                ["club", "warehouse", "festival", "bedroom"],
                                default_value="club",
                                on_change=MassloopState.set_venue,
                                background_color=BLACK,
                                border=f"1px solid {GREEN}44",
                                color=GREEN,
                                font_size="2",
                                width="100%",
                            ),
                            align_items="start",
                            spacing="2",
                            margin_bottom="1.5rem",
                        ),

                        # BPM Control
                        rx.vstack(
                            rx.text("$ set_initial_bpm", color=PINK, font_size="1", font_weight="600"),
                            rx.hstack(
                                rx.button("-", on_click=MassloopState.decrement_bpm,
                                         variant="outline", border=f"1px solid {GREEN}44",
                                         color=GREEN, font_size="2", padding="0.1rem 0.5rem"),
                                rx.text(MassloopState.bpm, font_size="4", color=WHITE),
                                rx.button("+", on_click=MassloopState.increment_bpm,
                                         variant="outline", border=f"1px solid {GREEN}44",
                                         color=GREEN, font_size="2", padding="0.1rem 0.5rem"),
                                spacing="4",
                                align_items="center",
                            ),
                            align_items="start",
                            spacing="2",
                            margin_bottom="1.5rem",
                        ),

                        # Energy Control
                        rx.vstack(
                            rx.text("$ set_initial_energy", color=PINK, font_size="1", font_weight="600"),
                            rx.slider(
                                min=0.1,
                                max=1.0,
                                step=0.1,
                                default_value=0.7,
                                on_change=MassloopState.set_energy,
                                width="100%",
                                color_scheme="green",
                            ),
                            rx.text(
                                "energy level: " + MassloopState.energy.to_string(),
                                color=AMBER, font_size="1",
                            ),
                            align_items="start",
                            spacing="2",
                            margin_bottom="1.5rem",
                        ),

                        spacing="4",
                        width="100%",
                    ),
                    width="90%",
                    max_width="500px",
                    margin_y="2rem",
                ),

                rx.button(
                    "▶ START FREE TRIAL",
                    on_click=MassloopState.complete_onboarding,
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

                rx.link(
                    "skip to studio", 
                    href="/stage", 
                    color=SLATE, 
                    font_size="1", 
                    margin_top="1rem",
                    _hover={"color": GREEN}
                ),

                spacing="6",
                align_items="center",
                padding="4rem 0",
            ),

            spacing="0",
            min_height="100vh",
            background_color=BLACK,
            align_items="center",
        ),
    )