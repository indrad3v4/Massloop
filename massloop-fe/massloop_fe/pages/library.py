"""Massloop Library Page — Track history and replay"""
import reflex as rx
from ..state import MassloopState
from ..components import (
    scanlines_overlay, terminal_box, 
    BLACK, GREEN, PINK, AMBER, GRAY, WHITE, SLATE,
)

def library_page() -> rx.Component:
    return rx.fragment(
        scanlines_overlay(),
        rx.vstack(
            # ── Nav Bar ──
            rx.hstack(
                rx.hstack(
                    rx.text("massloop", font_weight="700", color=GREEN, font_size="5"),
                    rx.text(" · library", color=SLATE, font_size="3"),
                    spacing="2",
                ),
                rx.spacer(),
                rx.link("studio", href="/stage", color=SLATE, _hover={"color": GREEN}, font_size="2"),
                padding="1rem 2rem",
                border_bottom=f"1px solid {GREEN}22",
                background_color=BLACK,
                width="100%",
            ),

            # ── Library Content ──
            rx.vstack(
                rx.vstack(
                    rx.text("> track_archive", font_size="6", font_weight="700", color=GREEN),
                    rx.text("historical generations · sonic fingerprints", color=SLATE, font_size="2"),
                    padding="2rem 0",
                    spacing="1",
                    align_items="center",
                ),

                # ── Main Library Area ──
                rx.hstack(
                    # Track List
                    terminal_box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("$ queue_history", color=PINK, font_size="1", font_weight="600"),
                                rx.spacer(),
                                rx.button(
                                    "↻ REFRESH",
                                    on_click=MassloopState.fetch_queue,
                                    variant="outline",
                                    border=f"1px solid {GREEN}44",
                                    color=GREEN,
                                    font_size="1",
                                    padding="2px 8px",
                                ),
                                width="100%",
                            ),
                            rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),
                            
                            # Track items (using a simple list since we avoid rx.foreach on list[dict])
                            rx.cond(
                                MassloopState.has_queue_items,
                                rx.vstack(
                                    rx.text(
                                        "Total tracks in archive: " + MassloopState.queue_length.to_string(),
                                        color=GREEN, font_size="2", font_weight="600",
                                    ),
                                    rx.text(
                                        "Last session ID: " + MassloopState.last_generated_id.to_string(),
                                        color=WHITE, font_size="1", font_family="monospace",
                                    ),
                                    rx.text(
                                        "Status: " + MassloopState.last_generated_status.to_string(),
                                        color=AMBER, font_size="1",
                                    ),
                                    spacing="2",
                                    align_items="start",
                                ),
                                rx.text("Archive empty — no tracks found", color=GRAY, font_size="2", padding="1rem 0"),
                            ),
                            width="100%",
                            align_items="start",
                        ),
                        width="40%",
                        min_width="300px",
                    ),

                    # Player Area
                    terminal_box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("$ playback_deck", color=PINK, font_size="1", font_weight="600"),
                                rx.spacer(),
                                rx.button(
                                    "▶ LATEST FROM GH",
                                    on_click=MassloopState.fetch_latest_generated,
                                    variant="outline",
                                    border=f"1px solid {GREEN}44",
                                    color=GREEN,
                                    font_size="1",
                                    font_weight="600",
                                    padding="4px 12px",
                                    _hover={"background_color": f"{GREEN}22"},
                                ),
                                width="100%",
                            ),
                            rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),
                            
                            rx.cond(
                                MassloopState.audio_url != "",
                                rx.vstack(
                                    rx.audio(
                                        controls=True,
                                        src=MassloopState.audio_url.to_string(),
                                        width="100%",
                                    ),
                                    rx.text(
                                        "playing: " + MassloopState.last_generated_id.to_string(),
                                        color=f"{GREEN}88",
                                        font_size="1",
                                    ),
                                    width="100%",
                                    align_items="start",
                                ),
                                rx.text("No track selected", color=GRAY, font_size="2"),
                            ),
                            
                            rx.text(
                                "deck status: " + MassloopState.last_generated_status.to_string(),
                                color=SLATE,
                                font_size="1",
                            ),
                            width="100%",
                            align_items="start",
                        ),
                        width="60%",
                        min_width="400px",
                    ),
                    width="90%",
                    max_width="1200px",
                    spacing="4",
                ),

                spacing="0",
                align_items="center",
                padding="0 2rem",
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