"""Massloop Artist Brand Identity page — define your sound."""
import reflex as rx
from ..state import MassloopState
from ..components import (
    scanlines_overlay, terminal_box,
    BLACK, GREEN, PINK, AMBER, GRAY, WHITE, SLATE,
)


def artist_sound_page() -> rx.Component:
    return rx.fragment(
        scanlines_overlay(),
        rx.vstack(
            # Nav
            rx.hstack(
                rx.text("massloop", font_weight="700", color=GREEN, font_size="5"),
                rx.spacer(),
                rx.link("stage", href="/stage", color=SLATE, _hover={"color": GREEN}, font_size="2"),
                rx.link("my sound", href="/my-sound", color=GREEN, font_size="2", font_weight="600"),
                padding="1rem 2rem",
                border_bottom=f"1px solid {GREEN}22",
                background_color=BLACK,
                width="100%",
            ),

            rx.text("> my sound", font_size="5", font_weight="700", color=GREEN,
                     margin_top="2rem"),
            rx.text("define your artist identity — every track will sound like YOU",
                    color=SLATE, font_size="2"),

            terminal_box(
                rx.vstack(
                    # Artist name
                    rx.text("artist name", color=PINK, font_size="1", font_weight="600"),
                    rx.input(
                        value=MassloopState.artist_name,
                        on_change=MassloopState.set_artist_name,
                        placeholder="e.g. Mateo Kowalski",
                        background_color="#0a0a0a",
                        border=f"1px solid {GREEN}44",
                        color=GREEN, width="100%",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),

                    # Genre
                    rx.text("genre / style", color=PINK, font_size="1", font_weight="600"),
                    rx.select(
                        ["TECHNO", "HARDGROOVE", "ACID_TECHNO", "INDUSTRIAL", "DUB_TECHNO",
                         "HYPNOTIC", "MINIMAL", "SCHRANZ", "DEEP_HOUSE", "HARDCORE", "JUNGLE"],
                        value=MassloopState.artist_genre,
                        on_change=MassloopState.set_artist_genre,
                        background_color="#0a0a0a",
                        border=f"1px solid {GREEN}44",
                        color=GREEN, width="100%",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),

                    # BPM range
                    rx.text("your BPM sweet spot", color=PINK, font_size="1", font_weight="600"),
                    rx.hstack(
                        rx.input(
                            value=MassloopState.artist_bpm_min.to_string(),
                            on_change=lambda v: MassloopState.set_artist_bpm_min(int(v) if v.isdigit() else 120),
                            placeholder="120", width="48%",
                            background_color="#0a0a0a", border=f"1px solid {GREEN}44", color=GREEN,
                        ),
                        rx.text("to", color=SLATE),
                        rx.input(
                            value=MassloopState.artist_bpm_max.to_string(),
                            on_change=lambda v: MassloopState.set_artist_bpm_max(int(v) if v.isdigit() else 160),
                            placeholder="160", width="48%",
                            background_color="#0a0a0a", border=f"1px solid {GREEN}44", color=GREEN,
                        ),
                        width="100%", spacing="2",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),

                    # Signature elements
                    rx.text("your signature sound (comma-separated)", color=PINK, font_size="1", font_weight="600"),
                    rx.text_area(
                        value=MassloopState.artist_signature,
                        on_change=MassloopState.set_artist_signature,
                        placeholder="e.g. distorted 909 kick, TB-303 squelch, tape hiss, minimal hats, dark atmosphere",
                        background_color="#0a0a0a", border=f"1px solid {GREEN}44",
                        color=GREEN, width="100%", min_height="80px",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),

                    # Energy curve
                    rx.text("default energy", color=PINK, font_size="1", font_weight="600"),
                    rx.hstack(
                        rx.slider(
                            min=0, max=100, step=5,
                            default_value=MassloopState.artist_energy_pct.to_int(),
                            on_change=MassloopState.set_artist_energy,
                            width="80%", color_scheme="green",
                        ),
                        rx.text(MassloopState.artist_energy_pct.to_string() + "%",
                                color=GREEN, font_size="2", font_weight="700"),
                        width="100%", spacing="3",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),

                    # Tone
                    rx.text("tone / vibe", color=PINK, font_size="1", font_weight="600"),
                    rx.hstack(
                        rx.select(
                            ["DARK", "BRIGHT", "WARM", "COLD", "INDUSTRIAL", "ORGANIC", "MINIMAL"],
                            value=MassloopState.artist_tone,
                            on_change=MassloopState.set_artist_tone,
                            background_color="#0a0a0a", border=f"1px solid {GREEN}44",
                            color=GREEN, width="100%",
                        ),
                        width="100%",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),

                    # Negative tags (what you DON'T want)
                    rx.text("avoid these (comma-separated)", color=PINK, font_size="1", font_weight="600"),
                    rx.input(
                        value=MassloopState.artist_negative_tags,
                        on_change=MassloopState.set_artist_negative_tags,
                        placeholder="e.g. vocals, melodies, major key, pop structures",
                        background_color="#0a0a0a", border=f"1px solid {GREEN}44",
                        color=GREEN, width="100%",
                    ),

                    rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),

                    # Save + preview
                    rx.hstack(
                        rx.button(
                            "💾 SAVE MY SOUND",
                            on_click=MassloopState.save_artist_brand,
                            background_color=GREEN, color=BLACK, font_weight="700",
                            padding="0.75rem 2rem", border_radius="0",
                            _hover={"background_color": PINK},
                        ),
                        rx.button(
                            "🎧 TRY ON STAGE",
                            on_click=rx.redirect("/stage"),
                            variant="outline", border=f"1px solid {GREEN}44",
                            color=GREEN, font_weight="600",
                            _hover={"background_color": f"{GREEN}22"},
                        ),
                        width="100%", spacing="3", justify="center",
                    ),

                    # Feedback
                    rx.cond(
                        MassloopState.artist_saved,
                        rx.text("✅ Your sound profile is saved — every track will reflect your identity",
                                color=GREEN, font_size="1", font_weight="600"),
                    ),

                    width="100%", max_width="640px",
                    spacing="3", align_items="start",
                    padding="1.5rem",
                ),
                width="90%", max_width="720px",
                margin_y="2rem",
            ),

            # Track history (if any)
            rx.cond(
                MassloopState.has_track_history,
                terminal_box(
                    rx.vstack(
                        rx.text("$ my tracks", color=GREEN, font_size="2", font_weight="700"),
                        rx.text("all tracks generated with your sound profile",
                                color=SLATE, font_size="1"),
                        rx.divider(border_color=f"{GREEN}22", margin="0.5rem 0"),
                        # Track list
                        rx.vstack(
                            rx.foreach(
                                MassloopState.track_history,
                                lambda t: rx.hstack(
                                    rx.cond(
                                        t.approved,
                                        rx.text("✅", font_size="2"),
                                        rx.text("⏳", font_size="2"),
                                    ),
                                    rx.vstack(
                                        rx.text(t.title, color=WHITE, font_size="1", font_weight="600"),
                                        rx.text(t.style, color=SLATE, font_size="0.85"),
                                        spacing="0",
                                    ),
                                    rx.spacer(),
                                    rx.cond(
                                        t.rating > 0,
                                        rx.text("★" * t.rating, color=AMBER, font_size="1"),
                                    ),
                                    rx.button(
                                        "▶",
                                        on_click=lambda: MassloopState.load_track(t.task_id),
                                        variant="outline",
                                        border=f"1px solid {GREEN}44",
                                        color=GREEN, font_size="1",
                                        padding="2px 8px",
                                    ),
                                    width="100%",
                                    padding="4px 0",
                                    border_bottom=f"1px solid {GREEN}11",
                                ),
                            ),
                            width="100%",
                        ),
                        width="100%",
                        align_items="start",
                        padding="1rem",
                    ),
                    width="90%", max_width="720px",
                    margin_bottom="2rem",
                ),
            ),

            rx.spacer(),
            min_height="100vh",
            background_color=BLACK,
            align_items="center",
        ),
    )
