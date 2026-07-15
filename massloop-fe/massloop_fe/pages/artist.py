"""Massloop Artist Identity panel — view learned identity + teach the agent.

Wire the newly-added backend capabilities (GET /api/artist/profile/{id},
POST /api/artist/learn, GET /budget) into the Reflex UI. Loaded on mount via
MassloopState.load_artist + load_budget; users can read their current identity,
send a chat message that teaches the agent who they are, and see the live
remaining daily budget.
"""
import reflex as rx
from ..state import MassloopState
from ..components import (
    scanlines_overlay, terminal_box,
    BLACK, GREEN, PINK, AMBER, GRAY, WHITE, SLATE,
)


def artist_page() -> rx.Component:
    return rx.fragment(
        scanlines_overlay(),
        rx.vstack(
            # ── Nav ──
            rx.hstack(
                rx.text("massloop", font_weight="700", color=GREEN, font_size="5"),
                rx.spacer(),
                rx.link("stage", href="/stage", color=SLATE, _hover={"color": GREEN}, font_size="2"),
                rx.link("my sound", href="/my-sound", color=SLATE, _hover={"color": GREEN}, font_size="2"),
                rx.link("artist", href="/artist", color=GREEN, font_size="2", font_weight="600"),
                padding="1rem 2rem",
                border_bottom=f"1px solid {GREEN}22",
                background_color=BLACK,
                width="100%",
            ),

            rx.text("> artist identity", font_size="5", font_weight="700", color=GREEN,
                     margin_top="2rem"),
            rx.text("your learned sound — every generated track reflects THIS",
                    color=SLATE, font_size="2"),

            # ── Identity load + budget on mount ──
            rx.box(
                on_mount=[MassloopState.load_artist, MassloopState.load_budget],
                display="none",
            ),

            # ── Budget bar ──
            terminal_box(
                rx.vstack(
                    rx.hstack(
                        rx.text("$ daily_budget", color=PINK, font_size="1", font_weight="600"),
                        rx.spacer(),
                        rx.text(
                            rx.cond(
                                MassloopState.budget_loaded,
                                f"€{MassloopState.budget_remaining:.2f}",
                                rx.cond(
                                    MassloopState.budget_error != "",
                                    MassloopState.budget_error,
                                    "loading…",
                                ),
                            ),
                            color=GREEN, font_size="3", font_weight="700",
                        ),
                        width="100%",
                    ),
                    rx.text(
                        rx.cond(
                            MassloopState.budget_loaded,
                            "live budget guardrail — spend resets daily",
                            "connecting to infra budget endpoint…",
                        ),
                        color=SLATE, font_size="1",
                    ),
                    width="100%", align_items="start", spacing="2",
                ),
                width="90%", max_width="720px", margin_y="1rem",
            ),

            # ── Current identity ──
            terminal_box(
                rx.vstack(
                    rx.text("$ current_identity", color=PINK, font_size="1", font_weight="600"),
                    rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),

                    rx.hstack(
                        rx.text("name", color=SLATE, font_size="1", width="30%"),
                        rx.text(
                            rx.cond(MassloopState.artist_name != "", MassloopState.artist_name, "—"),
                            color=WHITE, font_size="1", font_weight="600",
                        ),
                        width="100%", spacing="2",
                    ),
                    rx.hstack(
                        rx.text("genre", color=SLATE, font_size="1", width="30%"),
                        rx.text(
                            rx.cond(MassloopState.artist_genre != "", MassloopState.artist_genre, "—"),
                            color=WHITE, font_size="1", font_weight="600",
                        ),
                        width="100%", spacing="2",
                    ),
                    rx.hstack(
                        rx.text("bpm", color=SLATE, font_size="1", width="30%"),
                        rx.text(
                            MassloopState.artist_bpm_min.to_string()
                            + " – " + MassloopState.artist_bpm_max.to_string(),
                            color=WHITE, font_size="1", font_weight="600",
                        ),
                        width="100%", spacing="2",
                    ),
                    rx.hstack(
                        rx.text("tone", color=SLATE, font_size="1", width="30%"),
                        rx.text(
                            rx.cond(MassloopState.artist_tone != "", MassloopState.artist_tone, "—"),
                            color=WHITE, font_size="1", font_weight="600",
                        ),
                        width="100%", spacing="2",
                    ),
                    rx.hstack(
                        rx.text("signature", color=SLATE, font_size="1", width="30%"),
                        rx.text(
                            rx.cond(MassloopState.artist_signature != "", MassloopState.artist_signature, "—"),
                            color=WHITE, font_size="1", font_weight="600",
                        ),
                        width="100%", spacing="2", align_items="start",
                    ),
                    rx.hstack(
                        rx.text("avoid", color=SLATE, font_size="1", width="30%"),
                        rx.text(
                            rx.cond(MassloopState.artist_negative_tags != "", MassloopState.artist_negative_tags, "—"),
                            color=WHITE, font_size="1", font_weight="600",
                        ),
                        width="100%", spacing="2", align_items="start",
                    ),

                    rx.button(
                        "↻ REFRESH IDENTITY",
                        on_click=MassloopState.load_artist,
                        variant="outline", border=f"1px solid {GREEN}44",
                        color=GREEN, font_weight="600", margin_top="0.5rem",
                        _hover={"background_color": f"{GREEN}22"},
                    ),

                    width="100%", align_items="start", spacing="2", padding="0.5rem",
                ),
                width="90%", max_width="720px", margin_y="1rem",
            ),

            # ── Teach the agent ──
            terminal_box(
                rx.vstack(
                    rx.text("$ teach_the_agent", color=PINK, font_size="1", font_weight="600"),
                    rx.text("tell the agent who you are so future tracks match your vibe.",
                            color=SLATE, font_size="1"),
                    rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),

                    rx.text_area(
                        value=MassloopState.learn_message,
                        on_change=MassloopState.set_learn_message,
                        placeholder=(
                            "e.g. I'm DJ Vega, I make hypnotic acid techno around "
                            "132 BPM with a dark warehouse vibe. Avoid pop vocals and "
                            "bright melodies."
                        ),
                        background_color="#0a0a0a", border=f"1px solid {GREEN}44",
                        color=GREEN, width="100%", min_height="90px",
                    ),

                    rx.hstack(
                        rx.button(
                            rx.cond(MassloopState.is_learning, "⏳ teaching…", "🎓 TEACH AGENT"),
                            on_click=MassloopState.learn,
                            background_color=GREEN, color=BLACK, font_weight="700",
                            padding="0.6rem 1.5rem", border_radius="0",
                            is_disabled=MassloopState.is_learning,
                            _hover={"background_color": PINK},
                        ),
                        rx.spacer(),
                        rx.text(MassloopState.learn_status, color=AMBER, font_size="1"),
                        width="100%", spacing="3", align_items="center",
                    ),

                    width="100%", align_items="start", spacing="3", padding="0.5rem",
                ),
                width="90%", max_width="720px", margin_y="1rem", margin_bottom="2rem",
            ),

            rx.spacer(),
            min_height="100vh",
            background_color=BLACK,
            align_items="center",
        ),
    )
