"""Rave-themed Reflex components for Massloop — terminal/rave aesthetic"""
import reflex as rx

BLACK  = "#0a0a0a"
GREEN  = "#00ff41"
GREEN2 = "#00cc33"
PINK   = "#ff00ff"
AMBER  = "#ffb000"
GRAY   = "#2a2a2a"
WHITE  = "#e0e0e0"
SLATE  = "#6b7d8d"
RED    = "#ff0044"

def scanlines_overlay() -> rx.Component:
    return rx.html(
        r"""<style>
        body::after {
            content: '';
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            pointer-events: none;
            z-index: 9999;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0, 255, 65, 0.03) 2px,
                rgba(0, 255, 65, 0.03) 4px
            );
        }
        @keyframes glitch {
            0% { transform: translate(0); }
            20% { transform: translate(-2px, 1px); }
            40% { transform: translate(2px, -1px); }
            60% { transform: translate(-1px, 2px); }
            80% { transform: translate(1px, -2px); }
            100% { transform: translate(0); }
        }
        .glitch-hover:hover {
            animation: glitch 0.3s ease-in-out;
        }
        @keyframes pulse-glow {
            0%, 100% { filter: drop-shadow(0 0 4px rgba(0, 255, 65, 0.4)); }
            50% { filter: drop-shadow(0 0 12px rgba(0, 255, 65, 0.8)); }
        }
        .pulse-glow {
            animation: pulse-glow 2s ease-in-out infinite;
        }
        </style>"""
    )

def terminal_box(*children, **props) -> rx.Component:
    return rx.box(
        *children,
        border=f"1px solid {GREEN}33",
        border_radius="4px",
        padding="1rem",
        background_color=f"{BLACK}99",
        font_family="monospace",
        **props,
    )

def buffer_bar(count: int, total: int = 3) -> rx.Component:
    bars = []
    for i in range(total):
        filled = i < count
        bars.append(
            rx.box(
                width="24px",
                height="8px",
                background_color=GREEN if filled else f"{GREEN}22",
                border=f"1px solid {GREEN}44",
                border_radius="1px",
            )
        )
    return rx.hstack(*bars, spacing="1", align_items="center")

def energy_gradient(pct: int) -> rx.Component:
    return rx.box(
        rx.box(
            height="100%",
            width=f"{pct}%",
            background=f"linear-gradient(90deg, {GREEN}, {AMBER}, {RED})",
            transition="width 0.5s ease",
        ),
        width="200px",
        height="12px",
        border=f"1px solid {GREEN}44",
        border_radius="2px",
        background_color=f"{BLACK}88",
        overflow="hidden",
    )

def status_dot(ok) -> rx.Component:
    return rx.box(
        width="8px",
        height="8px",
        border_radius="50%",
        background_color=rx.cond(ok, GREEN, RED),
        box_shadow=rx.cond(ok, f"0 0 6px {GREEN}", f"0 0 6px {RED}"),
    )

def waveform_bars(active: bool = True) -> rx.Component:
    """Animated CSS waveform visualization (placeholder)."""
    bars = []
    heights = [40, 70, 50, 90, 60, 80, 45, 75, 55, 85, 35, 65, 50, 70, 40, 60]
    for h in heights:
        bars.append(
            rx.box(
                width="3px",
                height=f"{h}%",
                background_color=GREEN if active else f"{GREEN}44",
                border_radius="1px",
                margin="0 1px",
                class_name="wave-bar" if active else "",
                transition="height 0.2s ease",
            )
        )
    return rx.hstack(
        *bars,
        height="40px",
        align_items="center",
        spacing="0",
    )


def nav_bar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.text("massloop", font_weight="700", color=GREEN, font_size="5"),
            rx.text("·", color=PINK),
            rx.text("stage", color=SLATE, font_size="3"),
            spacing="2",
        ),
        rx.spacer(),
        rx.link("stage", href="/", color=SLATE, _hover={"color": GREEN}, font_size="2"),
        rx.text("|", color=GRAY),
        rx.link("live", href="/stage", color=SLATE, _hover={"color": GREEN}, font_size="2"),
        rx.text("|", color=GRAY),
        rx.link("health", href="/health", color=SLATE, _hover={"color": GREEN}, font_size="2"),
        padding="1rem 2rem",
        border_bottom=f"1px solid {GREEN}22",
        background_color=BLACK,
    )