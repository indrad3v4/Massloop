"""Massloop health check — terminal-style system status"""
import reflex as rx
from ..state import MassloopState
from ..components import (
    scanlines_overlay, terminal_box, status_dot, nav_bar,
    BLACK, GREEN, PINK, AMBER, GRAY, WHITE, SLATE, RED,
)

def health_check() -> rx.Component:
    return rx.fragment(
        scanlines_overlay(),
        rx.vstack(
            nav_bar(),

            rx.vstack(
                rx.text("> system/health", font_size="1.5rem", font_weight="700", color=GREEN),
                rx.text("status check for massloop backend & orchestrator",
                        color=SLATE, font_size="0.8rem"),
                padding="2rem 0",
                spacing="1",
                align_items="center",
            ),

            # Health card
            terminal_box(
                rx.vstack(
                    rx.hstack(
                        rx.text("$ backend", font_size="0.9rem", color=WHITE, font_weight="600"),
                        status_dot(MassloopState.backend_ok),
                        spacing="2",
                    ),
                    rx.text(MassloopState.backend_status, font_size="0.85rem", color=SLATE,
                            padding_left="1.5rem"),

                    rx.hstack(
                        rx.text("$ queue", font_size="0.9rem", color=WHITE, font_weight="600"),
                        status_dot(True),
                        spacing="2",
                        margin_top="1rem",
                    ),
                    rx.cond(
                        MassloopState.queue_length >= 0,
                        rx.text(f"items: {MassloopState.queue_length}", font_size="0.85rem", color=SLATE,
                                padding_left="1.5rem"),
                        rx.text("queue: unreachable", font_size="0.85rem", color=RED,
                                padding_left="1.5rem"),
                    ),

                    rx.hstack(
                        rx.text("$ orchestrator", font_size="0.9rem", color=WHITE, font_weight="600"),
                        status_dot(True),
                        spacing="2",
                        margin_top="1rem",
                    ),
                    rx.text("gpt-4o-mini · cometsuno adapter · chirp-v4",
                            font_size="0.85rem", color=SLATE, padding_left="1.5rem"),

                    rx.divider(border_color=f"{GREEN}22", margin="1rem 0"),

                    rx.hstack(
                        rx.button("> refresh health", on_click=MassloopState.check_health,
                                 variant="outline",
                                 border=f"1px solid {GREEN}44",
                                 color=GREEN,
                                 background_color="transparent",
                                 _hover={"border_color": GREEN, "color": BLACK, "background_color": GREEN}),
                        rx.button("> poll queue", on_click=MassloopState.poll_queue,
                                 variant="outline",
                                 border=f"1px solid {AMBER}44",
                                 color=AMBER,
                                 background_color="transparent",
                                 _hover={"border_color": AMBER, "color": BLACK, "background_color": AMBER}),
                        spacing="4",
                    ),

                    spacing="2",
                    align_items="start",
                ),
                width="90%",
                max_width="520px",
            ),

            rx.spacer(),
            rx.hstack(
                rx.text("press f5 to re-connect", color=GRAY, font_size="0.7rem"),
                justify="center",
                padding="2rem 0",
            ),

            min_height="100vh",
            background_color=BLACK,
            align_items="center",
        ),
    )
