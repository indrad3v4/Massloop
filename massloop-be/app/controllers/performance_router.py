"""Performance router - Live performance endpoints wired to business logic"""
from fastapi import APIRouter, HTTPException
from app.controllers.usecases import (
    LivePerformanceUseCase, SetupProfileUseCase, DeckStateManager
)
from app.models.entities import ArtistProfile, UndergroundStyle, VenueType

router = APIRouter(prefix="/performance", tags=["performance"])

# Lazy init — will be wired in main.py
use_case: LivePerformanceUseCase = None

@router.post("/start")
async def start_performance(
    event: str = "Live Set",
    profile_name: str = "default",
    style: str = "raw_techno",
    venue: str = "club",
    duration: int = 60,
    theme: str = ""
):
    """Start a live performance with the given artist profile"""
    global use_case
    if not use_case:
        raise HTTPException(503, "Performance service not initialized")

    try:
        # Map enum values
        style_enum = UndergroundStyle(style)
        venue_enum = VenueType(venue)
        profile = ArtistProfile(
            name=profile_name,
            styles=[style_enum],
            bpm_min=130,
            bpm_max=150
        )

        state = await use_case.start_performance(
            event=event,
            profile=profile,
            style=style_enum,
            venue=venue_enum,
            duration=duration,
            theme=theme or None
        )

        return {
            "status": "started",
            "event": state.event_name,
            "bpm": state.current_bpm,
            "style": state.current_style.value,
            "venue": state.venue_type.value,
            "tracks_buffered": len(state.buffer_tracks),
        }
    except ValueError as e:
        raise HTTPException(400, f"Invalid parameter: {e}")

@router.post("/generate")
async def generate_next():
    """Generate next track for the current performance"""
    global use_case
    if not use_case:
        raise HTTPException(503, "Performance service not initialized")

    # For now, return status — full async gen requires connected ports
    return {"status": "pipeline_ready", "ports": {
        "ai_gen": use_case.ai_gen is not None,
        "audio": use_case.audio_port is not None,
        "crowd": use_case.crowd is not None,
        "storage": use_case.storage is not None,
        "voice": use_case.voice_processor is not None,
    }}

@router.get("/status")
def get_status():
    """Get current performance system status"""
    return {
        "status": "initialized" if use_case else "uninitialized",
        "use_case": use_case is not None,
    }
