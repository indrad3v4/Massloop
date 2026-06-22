"""Massloop live performance page — stage monitor + Soundflow Control"""
import reflex as rx
from ..state import MassloopState
from ..components import (
    scanlines_overlay, terminal_box, buffer_bar,
    energy_gradient, status_dot, nav_bar, waveform_bars,
    BLACK, GREEN, PINK, AMBER, GRAY, WHITE, SLATE, RED,
)


def _track_row(track: rx.Var) -> rx.Component:
    """Render a single track row in the Soundflow queue list."""
    return rx.hstack(
        # Status badge
        rx.box(
            rx.text(
                track["status"].to_string(),
                font_size="1",
                color=BLACK,
                font_weight="700",
            ),
            background_color=rx.cond(
                track["status"] == "complete",
                GREEN,
                rx.cond(
                    track["status"] == "generating",
                    AMBER,
                    rx.cond(
                        track["status"] == "failed",
                        RED,
                        SLATE,
                    ),
                ),
            ),
            padding="2px 6px",
            border_radius="2px",
            min_width="80px",
            text_align="center",
        ),

        # Task ID (truncated)
        rx.text(
            track["id"].to_string(),
            font_size="1",
            color=WHITE,
            font_family="monospace",
            max_width="120px",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),

        # BPM from params
        rx.text(
            track["params"]["bpm"].to_string() + " BPM",
            font_size="1",
            color=PINK,
        ),

        # Style from params
        rx.text(
            track["params"]["style"].to_string(),
            font_size="1",
            color=SLATE,
        ),

        rx.spacer(),

        # Action buttons
        rx.cond(
            track["status"] == "pending_approval",
            rx.button(
                "KEEP",
                on_click=MassloopState.approve_track(track["id"].to_string()),
                variant="outline",
                border=f"1px solid {GREEN}44",
                color=GREEN,
                font_size="1",
                padding="2px 8px",
            ),
            rx.text("—", color=GRAY, font_size="1"),
        ),

        width="100%",
        spacing="3",
        padding="4px 0",
        border_bottom=f"1px solid {GREEN}11",
    )


def performance_page() -> rx.Component:
    return rx.fragment(
        scanlines_overlay(),
        rx.vstack(
            nav_bar(),

            rx.vstack(
                rx.text("> live performance", font_size="6", font_weight="700", color=GREEN),
                rx.text("stage monitor · buffer manager · generation control",
                        color=SLATE, font_size="2"),
                padding="2rem 0",
                spacing="1",
                align_items="center",
            ),

            # ═══ Main stage monitor ═══
            terminal_box(
                rx.vstack(
                    # Status header
                    rx.hstack(
                        rx.hstack(
                            status_dot(True),
                            rx.text("LIVE", font_size="2", color=GREEN, font_weight="700"),
                            spacing="2",
                        ),
                        rx.spacer(),
                        rx.text(
                            MassloopState.bpm.to_string() + " BPM · " + MassloopState.style,
                            color=PINK, font_size="2", font_weight="600",
                        ),
                        width="100%",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.75rem 0"),

                    # Buffer visualization
                    rx.hstack(
                        rx.vstack(
                            rx.text("$ buffer", color=SLATE, font_size="1"),
                            rx.hstack(
                                buffer_bar(2, 3),
                                rx.text(MassloopState.queue_length.to_string(),
                                        color=GREEN, font_size="2"),
                                spacing="3",
                            ),
                            rx.text("auto-fill: active · 1 generating",
                                    color=f"{GREEN}88", font_size="1"),
                            align_items="start",
                        ),
                        rx.spacer(),
                        rx.vstack(
                            rx.text("$ crowd", color=SLATE, font_size="1"),
                            energy_gradient(MassloopState.energy_pct),
                            rx.text(
                                "crowd energy: " + MassloopState.energy.to_string() + " · tracking",
                                color=AMBER, font_size="1",
                            ),
                            align_items="end",
                        ),
                        width="100%",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.75rem 0"),

                    # Control panel
                    rx.hstack(
                        # Energy controls
                        rx.vstack(
                            rx.text("control", color=PINK, font_size="1", font_weight="600"),
                            rx.hstack(
                                rx.button("−E", on_click=MassloopState.decrement_energy,
                                         variant="outline", border=f"1px solid {AMBER}44",
                                         color=AMBER, font_size="1"),
                                rx.box(height="80px"),
                                rx.button("+E", on_click=MassloopState.increment_energy,
                                         variant="outline", border=f"1px solid {AMBER}44",
                                         color=AMBER, font_size="1"),
                                spacing="2",
                            ),
                            align_items="center",
                        ),

                        rx.spacer(),

                        # BPM controls
                        rx.vstack(
                            rx.text("tempo", color=PINK, font_size="1", font_weight="600"),
                            rx.hstack(
                                rx.button("−B", on_click=MassloopState.decrement_bpm,
                                         variant="outline", border=f"1px solid {GREEN}44",
                                         color=GREEN, font_size="1"),
                                rx.box(height="80px"),
                                rx.button("+B", on_click=MassloopState.increment_bpm,
                                         variant="outline", border=f"1px solid {GREEN}44",
                                         color=GREEN, font_size="1"),
                                spacing="2",
                            ),
                            align_items="center",
                        ),

                        rx.spacer(),

                        # Big GENERATE button
                        rx.vstack(
                            rx.text("trigger", color=PINK, font_size="1", font_weight="600"),
                            rx.button(
                                "▶ GENERATE NEXT",
                                on_click=MassloopState.generate,
                                background_color=GREEN,
                                color=BLACK,
                                font_weight="700",
                                font_size="4",
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

            # ═══ Audio Player + Latest from GH ═══
            terminal_box(
                rx.vstack(
                    rx.hstack(
                        rx.text("$ audio deck", color=SLATE, font_size="1"),
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

                    # Audio player or empty state
                    rx.cond(
                        MassloopState.audio_url != "",
                        rx.vstack(
                            rx.audio(
                                controls=True,
                                src=MassloopState.audio_url.to_string(),
                                width="100%",
                            ),
                            rx.text(
                                "now: " + MassloopState.last_generated_id.to_string(),
                                color=f"{GREEN}88",
                                font_size="1",
                            ),
                            width="100%",
                            align_items="start",
                        ),
                        rx.text("No track yet", color=GRAY, font_size="2"),
                    ),

                    rx.text(
                        "status: " + MassloopState.last_generated_status.to_string(),
                        color=SLATE,
                        font_size="1",
                    ),

                    width="100%",
                    align_items="start",
                ),
                width="90%",
                max_width="720px",
                margin_top="1rem",
            ),

            # ═══ Soundflow Control — Deck A/B + Crossfader + Master ═══
            terminal_box(
                rx.vstack(
                    rx.text("$ soundflow control", color=PINK, font_size="2", font_weight="700"),
                    rx.text("deck A/B · crossfader · master volume",
                            color=SLATE, font_size="1"),

                    rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),

                    # Deck A / Deck B layout
                    rx.hstack(
                        # Deck A
                        rx.vstack(
                            rx.hstack(
                                rx.text("DECK A", color=GREEN, font_size="2", font_weight="700"),
                                rx.text("●", color=GREEN, font_size="1"),
                                spacing="2",
                            ),
                            waveform_bars(active=True),
                            rx.text("current track", color=SLATE, font_size="1"),
                            rx.text(
                                MassloopState.last_generated_id.to_string(),
                                color=WHITE, font_size="1",
                                max_width="140px",
                                overflow="hidden",
                                text_overflow="ellipsis",
                                white_space="nowrap",
                            ),
                            align_items="center",
                            border=f"1px solid {GREEN}33",
                            padding="0.5rem",
                            border_radius="4px",
                            width="100%",
                        ),

                        rx.spacer(),

                        # Deck B
                        rx.vstack(
                            rx.hstack(
                                rx.text("DECK B", color=AMBER, font_size="2", font_weight="700"),
                                rx.text("○", color=AMBER, font_size="1"),
                                spacing="2",
                            ),
                            waveform_bars(active=False),
                            rx.text("next track", color=SLATE, font_size="1"),
                            rx.text("—", color=GRAY, font_size="1"),
                            align_items="center",
                            border=f"1px solid {AMBER}33",
                            padding="0.5rem",
                            border_radius="4px",
                            width="100%",
                        ),

                        width="100%",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),

                    # Crossfader
                    rx.vstack(
                        rx.hstack(
                            rx.text("A", color=GREEN, font_size="1", font_weight="700"),
                            rx.spacer(),
                            rx.text("CROSSFADER", color=SLATE, font_size="1"),
                            rx.spacer(),
                            rx.text("B", color=AMBER, font_size="1", font_weight="700"),
                            width="100%",
                        ),
                        rx.slider(
                            min=0,
                            max=100,
                            step=1,
                            default_value=50,
                            on_change=MassloopState.set_crossfader,
                            width="100%",
                            color_scheme="green",
                        ),
                        width="100%",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),

                    # Master volume
                    rx.vstack(
                        rx.hstack(
                            rx.text("MASTER VOL", color=SLATE, font_size="1"),
                            rx.spacer(),
                            rx.text(
                                MassloopState.master_volume.to_string(),
                                color=GREEN, font_size="1",
                            ),
                            width="100%",
                        ),
                        rx.slider(
                            min=0,
                            max=100,
                            step=1,
                            default_value=80,
                            on_change=MassloopState.set_master_volume,
                            width="100%",
                            color_scheme="green",
                        ),
                        width="100%",
                    ),

                    width="100%",
                    align_items="start",
                ),
                width="90%",
                max_width="720px",
                margin_top="1rem",
            ),

            # ═══ Track Queue ═══
            terminal_box(
                rx.vstack(
                    rx.hstack(
                        rx.text("$ track queue", color=SLATE, font_size="1"),
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

                    # Queue header
                    rx.hstack(
                        rx.text("STATUS", color=SLATE, font_size="1", min_width="80px"),
                        rx.text("ID", color=SLATE, font_size="1", min_width="120px"),
                        rx.text("BPM", color=SLATE, font_size="1"),
                        rx.text("STYLE", color=SLATE, font_size="1"),
                        rx.spacer(),
                        rx.text("ACTION", color=SLATE, font_size="1"),
                        width="100%",
                        spacing="3",
                        border_bottom=f"1px solid {GREEN}33",
                        padding_bottom="4px",
                    ),

                    # Track list via foreach
                    rx.cond(
                        MassloopState.queue_items.length() > 0,
                        rx.vstack(
                            rx.foreach(MassloopState.queue_items, _track_row),
                            width="100%",
                            spacing="0",
                        ),
                        rx.text("queue empty — hit GENERATE or REFRESH",
                                color=GRAY, font_size="1", padding="1rem 0"),
                    ),

                    width="100%",
                    align_items="start",
                ),
                width="90%",
                max_width="720px",
                margin_top="1rem",
            ),

            # History
            rx.cond(
                MassloopState.last_generated_id != "",
                terminal_box(
                    rx.vstack(
                        rx.text("$ history (last)", color=SLATE, font_size="1"),
                        rx.hstack(
                            rx.text("id: " + MassloopState.last_generated_id.to_string(),
                                    font_size="2", color=WHITE),
                            rx.text("status: " + MassloopState.last_generated_status.to_string(),
                                    font_size="2",
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
                    rx.text("$ hotkeys", color=SLATE, font_size="1"),
                    rx.text("n: next track  ·  +/-: energy  ·  b: bump BPM  ·  space: play/pause",
                            color=f"{WHITE}aa", font_size="1"),
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