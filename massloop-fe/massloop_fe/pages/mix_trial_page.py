"""Massloop DJ Mix Trial page"""
import reflex as rx
from ..state import MassloopState


STYLES = {
    "WHITE": "#f0ede8",
    "AMBER": "#d4a853",
    "SLATE": "#6b7d8d",
    "DARK": "#1a1a1a",
    "ACID_GREEN": "#39ff14",
    "NEON_PURPLE": "#bf5af2",
}


def mix_trial_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Header
            rx.heading("🎛️ Massloop DJ Trial", size="7", color=STYLES["WHITE"], margin_bottom="1rem"),
            rx.text("Generate a 2-track AI mix for your venue. Free trial — no card required.",
                    color=STYLES["SLATE"], margin_bottom="2rem"),

            # Venue selector
            rx.text("Venue", color=STYLES["WHITE"], font_weight="600"),
            rx.select(
                ["club", "warehouse", "festival", "bar", "open_air"],
                default_value="club",
                on_change=MassloopState.set_venue,
                width="100%",
                margin_bottom="1rem",
            ),

            # BPM slider
            rx.text("BPM: " + MassloopState.bpm.to_string(),
                    color=STYLES["WHITE"], font_weight="600"),
            rx.slider(
                default_value=124,
                min=110,
                max=160,
                on_change=MassloopState.set_bpm,
                width="100%",
                margin_bottom="1rem",
            ),

            # Energy
            rx.text("Energy: " + MassloopState.energy.to_string(),
                    color=STYLES["WHITE"], font_weight="600"),
            rx.slider(
                default_value=0.7,
                min=0.0,
                max=1.0,
                step=0.1,
                on_change=MassloopState.set_energy,
                width="100%",
                margin_bottom="1rem",
            ),

            # Style tags input
            rx.text("Style tags", color=STYLES["WHITE"], font_weight="600"),
            rx.input(
                placeholder="e.g. deep house minimal acid",
                on_change=MassloopState.set_tags,
                width="100%",
                margin_bottom="1.5rem",
            ),

            # Generate button
            rx.button(
                "Generate 2-Track Mix Trial",
                on_click=MassloopState.start_trial,
                background_color=STYLES["ACID_GREEN"],
                color=STYLES["DARK"],
                font_weight="700",
                padding="1rem 2rem",
                border_radius="8px",
                width="100%",
                margin_bottom="1rem",
            ),

            # Status
            rx.cond(
                MassloopState.trial_status != "",
                rx.text(MassloopState.trial_status, color=STYLES["NEON_PURPLE"]),
                rx.text("", color=STYLES["SLATE"]),
            ),

            # Result links
            rx.cond(
                MassloopState.audio_url != "",
                rx.vstack(
                    rx.text("Track 1 (raw):", color=STYLES["WHITE"], margin_top="1rem"),
                    rx.audio(
                        src=MassloopState.audio_url,
                        width="100%",
                    ),
                    rx.text("Track 2 (mix):", color=STYLES["WHITE"], margin_top="1rem"),
                    rx.audio(
                        src=MassloopState.audio_url,  # same source for demo
                        width="100%",
                    ),
                    rx.button(
                        "Upgrade to DJ Starter — €9/mo",
                        background_color=STYLES["AMBER"],
                        color=STYLES["DARK"],
                        font_weight="600",
                        on_click=MassloopState.start_checkout,
                        margin_top="1rem",
                    ),
                    spacing="2",
                ),
                rx.text("", color=STYLES["SLATE"]),
            ),

            spacing="2",
            width="100%",
            max_width="600px",
            padding="2rem",
        ),
        background_color=STYLES["DARK"],
        min_height="100vh",
        display="flex",
        align_items="center",
        justify_content="center",
    )