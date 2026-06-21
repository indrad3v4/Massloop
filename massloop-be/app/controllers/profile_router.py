"""Profile router - Artist profile CRUD wired to StateManager"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from app.services.state_manager import get_state_manager
from app.models.entities import ArtistProfile, UndergroundStyle, AudioReference

router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.get("/")
def list_profiles():
    """List all saved artist profiles"""
    sm = get_state_manager()
    profiles_dir = sm.data_dir / "profiles"
    if not profiles_dir.exists():
        return {"profiles": []}
    profiles = []
    for f in sorted(profiles_dir.glob("*.json")):
        if f.stem and not f.stem.startswith("."):
            profiles.append(f.stem)
    return {"profiles": profiles}

@router.get("/{profile_name}")
def get_profile(profile_name: str):
    """Get a specific artist profile by name"""
    sm = get_state_manager()
    profile_file = sm.data_dir / "profiles" / f"{profile_name}.json"
    if not profile_file.exists():
        raise HTTPException(404, f"Profile '{profile_name}' not found")
    try:
        import json
        with open(profile_file) as f:
            data = json.load(f)
        return {"profile": data}
    except Exception as e:
        raise HTTPException(500, f"Failed to load profile: {e}")

@router.post("/")
def create_profile(profile: ArtistProfile):
    """Create or update an artist profile"""
    sm = get_state_manager()
    profile_dir = sm.data_dir / "profiles"
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_file = profile_dir / f"{profile.name}.json"
    try:
        from dataclasses import asdict
        import json
        with open(profile_file, "w") as f:
            data = asdict(profile)
            # Convert enums to strings
            data["styles"] = [s.value for s in profile.styles]
            json.dump(data, f, indent=2, default=str)
        sm.set_active_profile(profile.name)
        return {"status": "saved", "profile": profile.name}
    except Exception as e:
        raise HTTPException(500, f"Failed to save profile: {e}")

@router.delete("/{profile_name}")
def delete_profile(profile_name: str):
    """Delete an artist profile"""
    sm = get_state_manager()
    profile_file = sm.data_dir / "profiles" / f"{profile_name}.json"
    if not profile_file.exists():
        raise HTTPException(404, f"Profile '{profile_name}' not found")
    profile_file.unlink()
    return {"status": "deleted", "profile": profile_name}

@router.get("/{profile_name}/active")
def set_active_profile(profile_name: str):
    """Set and get active profile"""
    sm = get_state_manager()
    sm.set_active_profile(profile_name)
    return {"active_profile": sm.get_active_profile()}
