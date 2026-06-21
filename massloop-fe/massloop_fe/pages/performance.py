"""Massloop live performance page — stage monitor"""
import reflex as rx
from ..state import MassloopState
from ..components import (
    scanlines_overlay, terminal_box, buffer_bar,
    energy_gradient, status_dot, nav_bar,
    BLACK, GREEN, PINK, AMBER, GRAY, WHITE, SLATE, RED,
)

def performance_page() -> rx.Component:
    return rx.fragment(
        scanlines_overlay(),
        rx.vstack(
            nav_bar(),

            rx.vstack(
                rx.text("> live performance", font_size="1.5rem", font_weight="700", color=GREEN),
                rx.text("stage monitor · buffer manager · generation control",
                        color=SLATE, font_size="0.8rem"),
                padding="2rem 0",
                spacing="1",
                align_items="center",
            ),

            # Main stage monitor
            terminal_box(
                rx.vstack(
                    # Status header
                    rx.hstack(
                        rx.hstack(
                            status_dot(True),
                            rx.text("LIVE", font_size="0.9rem", color=GREEN, font_weight="700"),
                            spacing="2",
                        ),
                        rx.spacer(),
                        rx.text("140 BPM · ACID TECHNO", color=PINK, font_size="0.8rem",
                                font_weight="600"),
                        width="100%",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.75rem 0"),

                    # Buffer visualization
                    rx.hstack(
                        rx.vstack(
                            rx.text("$ buffer", color=SLATE, font_size="0.75rem"),
                            rx.hstack(
                                buffer_bar(2, 3),
                                rx.text("2/3", color=GREEN, font_size="0.9rem"),
                                spacing="3",
                            ),
                            rx.text("auto-fill: active · 1 generating",
                                    color=f"{GREEN}88", font_size="0.7rem"),
                            align_items="start",
                        ),
                        rx.spacer(),
                        rx.vstack(
                            rx.text("$ crowd", color=SLATE, font_size="0.75rem"),
                            energy_gradient(0.7),
                            rx.text("crowd energy: 70% · tracking",
                                    color=AMBER, font_size="0.7rem"),
                            align_items="end",
                        ),
                        width="100%",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.75rem 0"),

                    # Control panel
                    rx.hstack(
                        # Energy controls
                        rx.vstack(
                            rx.text("control", color=PINK, font_size="0.75rem", font_weight="600"),
                            rx.hstack(
                                rx.button("−E", on_click=rx.set_value("energy_val", max(0.1, rx.State.get().energy - 0.1)),
                                         variant="outline", border=f"1px solid {AMBER}44",
                                         color=AMBER, font_size="0.75rem"),
                                rx.box(height="80px"),
                                rx.button("+E", on_click=rx.set_value("energy_val", min(1.0, rx.State.get().energy + 0.1)),
                                         variant="outline", border=f"1px solid {AMBER}44",
                                         color=AMBER, font_size="0.75rem"),
                                spacing="2",
                            ),
                            align_items="center",
                        ),

                        rx.spacer(),

                        # BPM controls
                        rx.vstack(
                            rx.text("tempo", color=PINK, font_size="0.75rem", font_weight="600"),
                            rx.hstack(
                                rx.button("−B", on_click=rx.set_value("bpm_val", max(80, rx.State.get().bpm - 5)),
                                         variant="outline", border=f"1px solid {GREEN}44",
                                         color=GREEN, font_size="0.75rem"),
                                rx.box(height="80px"),
                                rx.button("+B", on_click=rx.set_value("bpm_val", min(200, rx.State.get().bpm + 5)),
                                         variant="outline", border=f"1px solid {GREEN}44",
                                         color=GREEN, font_size="0.75rem"),
                                spacing="2",
                            ),
                            align_items="center",
                        ),

                        rx.spacer(),

                        # Big GENERATE button
                        rx.vstack(
                            rx.text("trigger", color=PINK, font_size="0.75rem", font_weight="600"),
                            rx.button(
                                "▶ GENERATE NEXT",
                                on_click=MassloopState.generate,
                                background_color=GREEN,
                                color=BLACK,
                                font_weight="700",
                                font_size="1.1rem",
                                padding="0.75rem 1.5rem",
                                border="none",
                                border_radius="0",
                                class_name="glitch-hover",
                                _hover={
                                    "background_color": PINK,
                                    "box_shadow": f"0 0 20px {GREEN}66",
                                },
                            ),
                            align_items="center",
                        ),

                        width="100%",
                    ),

                    spacing="0",
                ),
                width="90%",
                max_width="720px",
            ),

            # History
            rx.cond(
                MassloopState.last_generated_id != "",
                terminal_box(
                    rx.vstack(
                        rx.text("$ history (last)", color=SLATE, font_size="0.75rem"),
                        rx.hstack(
                            rx.text(f"id: {MassloopState.last_generated_id}", font_size="0.8rem", color=WHITE),
                            rx.text(f"status: {MassloopState.last_generated_status}",
                                    font_size="0.8rem",
                                    color=rx.cond(
                                        MassloopState.last_generated_status == "submitted",
                                        AMBER, SLATE
                                    )),
                            spacing="4",
                        ),
                        align_items="start",
                    ),
                    width="90%",
                    max_width="720px",
                    margin_top="1rem",
                ),
            ),

            # Hotkeys hint
            terminal_box(
                rx.vstack(
                    rx.text("$ hotkeys", color=SLATE, font_size="0.75rem"),
                    rx.text("n: next track  ·  +/-: energy  ·  b: bump BPM  ·  space: play/pause",
                            color=f"{WHITE}aa", font_size="0.75rem"),
                    align_items="start",
                ),
                width="90%",
                max_width="720px",
                margin_top="1rem",
            ),

            rx.spacer(),
            min_height="100vh",
            background_color=BLACK,
            align_items="center",
        ),
    )
