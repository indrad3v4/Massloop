"""Artist feedback router — learns from approval/rejection."""
from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger
from ..services.artist_memory import (
    learn_from_approval,
    get_profile,
    learn_from_chat,
)

router = APIRouter(prefix="/api/artist", tags=["artist"])


class FeedbackRequest(BaseModel):
    artist_id: str
    task_id: str
    approved: bool
    track_meta: dict = {}


class ProfileResponse(BaseModel):
    artist_id: str
    name: str = ""
    genre: str = ""
    signature_elements: list[str] = []
    tone: str = ""
    bpm_sweet_spot: list[int] = [120, 160]
    energy_default: float = 0.7
    negative_tags: list[str] = []
    approved_tracks: int = 0
    rejected_tracks: int = 0
    interaction_count: int = 0


@router.post("/feedback")
async def track_feedback(req: FeedbackRequest):
    """Artist approves or rejects a generated track — system learns."""
    learn_from_approval(req.artist_id, req.task_id, req.approved, req.track_meta)
    profile = get_profile(req.artist_id)
    return {
        "status": "ok",
        "interaction_count": profile.get("interaction_count", 0),
        "artist_known": profile.get("name") != "",
    }


@router.get("/profile/{artist_id}", response_model=ProfileResponse)
async def get_artist_profile(artist_id: str):
    """Get the learned artist profile."""
    profile = get_profile(artist_id)
    return ProfileResponse(
        artist_id=artist_id,
        name=profile.get("name", ""),
        genre=profile.get("genre", ""),
        signature_elements=profile.get("signature_elements", [])
            + profile.get("learned_preferences", {}).get("signature_elements", []),
        tone=profile.get("tone", ""),
        bpm_sweet_spot=profile.get("bpm_sweet_spot", [120, 160]),
        energy_default=profile.get("energy_default", 0.7),
        negative_tags=profile.get("negative_tags", [])
            + profile.get("learned_preferences", {}).get("negative_tags", []),
        approved_tracks=len(profile.get("approved_tracks", [])),
        rejected_tracks=len(profile.get("rejected_tracks", [])),
        interaction_count=profile.get("interaction_count", 0),
    )


@router.post("/learn")
async def learn_from_chat_endpoint(artist_id: str, message: str):
    """Orchestrator calls this to learn artist identity from chat messages."""
    profile = learn_from_chat(artist_id, message)
    return {
        "status": "ok",
        "interaction_count": profile.get("interaction_count", 0),
        "learned_elements": profile.get("learned_preferences", {})
            .get("signature_elements", []),
    }
