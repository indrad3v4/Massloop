"""Massloop stage — rave terminal landing page"""
import reflex as rx
from ..state import MassloopState
from ..components import (
    scanlines_overlay, terminal_box, buffer_bar,
    energy_gradient, status_dot, nav_bar,
    BLACK, GREEN, PINK, AMBER, GRAY, WHITE, SLATE,
)

def index() -> rx.Component:
    return rx.fragment(
        scanlines_overlay(),
        rx.vstack(
            nav_bar(),

            # ── Hero section ──
            rx.vstack(
                rx.text("MASSLOOP", font_size="8", font_weight="900",
                        color=GREEN,                        class_name="pulse-glow"),
                rx.text("> stage-confidence amplifier · midi-first instrument",
                        color=SLATE, font_size="2", margin_top="0.25rem"),
                rx.text("> AI-powered live generation for underground electronic music",
                        color=f"{SLATE}aa", font_size="1"),
                spacing="4",
                align_items="center",
                padding="2rem 0",
            ),

            # ── Performance hub ──
            terminal_box(
                rx.vstack(
                    # Status row
                    rx.hstack(
                        rx.hstack(status_dot(True), rx.text(" orchestrator", font_size="2"), spacing="2"),
                        rx.hstack(status_dot(MassloopState.backend_ok),
                                  rx.text(MassloopState.backend_status, font_size="2", color=SLATE),
                                  spacing="2"),
                        rx.spacer(),
                        rx.button("> refresh", on_click=MassloopState.check_health,
                                 variant="outline",
                                 border=f"1px solid {GREEN}44",
                                 color=GREEN,
                                 background_color="transparent",
                                 font_size="1",
                                 padding="0.25rem 0.75rem",
                                 _hover={"border_color": GREEN, "color": BLACK, "background_color": GREEN}),
                        width="100%",
                        padding_bottom="1rem",
                        border_bottom=f"1px solid {GREEN}22",
                    ),

                    # Buffer + controls
                    rx.hstack(
                        # Buffer section
                        rx.vstack(
                            rx.text("$ pre-buffer", color=SLATE, font_size="2"),
                            rx.text("▓▓▓░░", color=GREEN, font_size="6"),                            rx.text("2/3 tracks ready", color=f"{GREEN}aa", font_size="1"),
                            align_items="start",
                        ),

                        rx.spacer(),

                        # Energy section
                        rx.vstack(
                            rx.text("$ energy", color=SLATE, font_size="2"),
                            energy_gradient(70),
                            rx.text("70%", color=AMBER, font_size="1"),
                            align_items="end",
                        ),

                        width="100%",
                        padding="1rem 0",
                    ),

                    # Controls row
                    rx.hstack(
                        # BPM
                        rx.vstack(
                            rx.text("$ bpm", color=SLATE, font_size="1"),
                            rx.hstack(
                                rx.button("-", on_click=MassloopState.decrement_bpm,
                                         variant="outline", border=f"1px solid {GREEN}44",
                                         color=GREEN, font_size="2", padding="0.1rem 0.5rem"),
                                rx.text(MassloopState.bpm, font_size="5", color=WHITE, id="bpm_display"),
                                rx.button("+", on_click=MassloopState.increment_bpm,
                                         variant="outline", border=f"1px solid {GREEN}44",
                                         color=GREEN, font_size="2", padding="0.1rem 0.5rem"),
                                spacing="2",
                                align_items="center",
                            ),
                            align_items="center",
                        ),

                        rx.spacer(),

                        # Style
                        rx.vstack(
                            rx.text("$ style", color=SLATE, font_size="1"),
                            rx.select(["ACID_TECHNO", "RAW_TECHNO", "INDUSTRIAL", "HARDGROOVE", "SCHRANZ",
                                       "BREAKBEAT", "JUNGLE", "HARDTEK", "DUB_TECHNO", "HYPNOTIC"],
                                      default_value="ACID_TECHNO",
                                      on_change=MassloopState.set_style,
                                      background_color=BLACK,
                                      border=f"1px solid {GREEN}44",
                                      color=GREEN,
                                      font_size="2",
                            ),
                            align_items="center",
                        ),

                        rx.spacer(),

                        # GENERATE button
                        rx.button(
                            "> GENERATE",
                            on_click=MassloopState.generate,
                            background_color=GREEN,
                            color=BLACK,
                            font_weight="700",
                            font_size="3",
                            padding="0.75rem 2rem",
                            border="none",
                            border_radius="0",
                            class_name="glitch-hover",
                            _hover={
                                "background_color": PINK,
                                "box_shadow": f"0 0 20px {GREEN}66",
                            },
                        ),

                        width="100%",
                    ),

                    spacing="0",
                ),
                width="90%",
                max_width="720px",
            ),

            # ── Last generation status ──
            rx.cond(
                MassloopState.last_generated_id != "",
                terminal_box(
                    rx.vstack(
                        rx.text("$ last generation", color=SLATE, font_size="1"),
                        rx.text(MassloopState.last_generated_id, font_size="2", color=WHITE),
                        rx.text(MassloopState.last_generated_status, font_size="1", color=AMBER),
                        align_items="start",
                    ),
                    width="90%",
                    max_width="720px",
                    margin_top="1rem",
                ),
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
