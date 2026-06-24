"""Artist memory system — learns artist identity from behavior + feedback."""
import json
import os
import time
from typing import Optional
from loguru import logger

MEMORY_DIR = os.getenv("ARTIST_MEMORY_DIR", "/tmp/artist_memories")


def _profile_path(artist_id: str) -> str:
    os.makedirs(MEMORY_DIR, exist_ok=True)
    return os.path.join(MEMORY_DIR, f"{artist_id}.json")


def get_profile(artist_id: str) -> dict:
    """Load artist profile from file memory."""
    path = _profile_path(artist_id)
    if not os.path.exists(path):
        return {
            "artist_id": artist_id,
            "name": "",
            "genre": "",
            "signature_elements": [],
            "tone": "",
            "bpm_sweet_spot": [120, 160],
            "energy_default": 0.7,
            "negative_tags": [],
            "approved_tracks": [],
            "rejected_tracks": [],
            "learned_preferences": {},
            "interaction_count": 0,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
    with open(path) as f:
        return json.load(f)


def save_profile(profile: dict):
    """Save artist profile to file memory."""
    profile["updated_at"] = time.time()
    path = _profile_path(profile["artist_id"])
    with open(path, "w") as f:
        json.dump(profile, f, indent=2, default=str)
    logger.info(f"Artist profile saved: {profile['artist_id']}")


def learn_from_chat(artist_id: str, message: str, profile: Optional[dict] = None):
    """Extract style preferences from chat messages and update profile."""
    if profile is None:
        profile = get_profile(artist_id)
    
    msg = message.lower()
    learned = profile.get("learned_preferences", {})
    
    # Detect genre mentions
    genres = ["techno", "hardgroove", "acid", "industrial", "dub", "minimal",
              "schranz", "jungle", "drum and bass", "house", "hardcore", "ambient"]
    for g in genres:
        if g in msg and g not in learned.get("confirmed_genres", []):
            learned.setdefault("confirmed_genres", []).append(g)
    
    # Detect energy hints
    if any(w in msg for w in ["harder", "faster", "aggressive", "intense", "dark"]):
        learned["energy_preference"] = "high"
    elif any(w in msg for w in ["chill", "deep", "minimal", "subtle", "soft"]):
        learned["energy_preference"] = "low"
    
    # Detect BPM hints
    import re
    bpm_matches = re.findall(r'(\d+)\s*bpm', msg)
    if bpm_matches:
        bpms = [int(b) for b in bpm_matches]
        if bpms:
            if not learned.get("bpm_hints"):
                learned["bpm_hints"] = []
            learned["bpm_hints"].extend(bpms)
            learned["bpm_hints"] = learned["bpm_hints"][-10:]  # keep last 10
            # Calculate preferred range
            if len(learned["bpm_hints"]) >= 3:
                learned["bpm_sweet_spot"] = [
                    min(learned["bpm_hints"]),
                    max(learned["bpm_hints"]),
                ]
    
    # Detect signature elements
    sig_keywords = ["kick", "bass", "hats", "snare", "clap", "303", "909", "808",
                    "squelch", "distortion", "reverb", "delay", "pad", "stab",
                    "percussion", "ride", "cymbal", "hi-hat", "tom", "vocal",
                    "sample", "break", "loop", "synth", "lead", "chord"]
    found = [kw for kw in sig_keywords if kw in msg]
    if found:
        existing = learned.get("signature_elements", [])
        for f_elem in found:
            if f_elem not in existing:
                existing.append(f_elem)
        learned["signature_elements"] = existing[-15:]  # keep last 15
    
    profile["learned_preferences"] = learned
    profile["interaction_count"] = profile.get("interaction_count", 0) + 1
    
    # Derive name from first chat if not set
    if not profile["name"] and message.strip():
        # Try to extract "I am X" pattern
        name_match = re.search(r'i am (\w+)', msg) or re.search(r"i'm (\w+)", msg) or re.search(r'my name is (\w+)', msg)
        if name_match:
            profile["name"] = name_match.group(1).title()
    
    save_profile(profile)
    return profile


def learn_from_approval(artist_id: str, task_id: str, approved: bool, track_meta: dict = None):
    """Update artist profile based on track approval/rejection."""
    profile = get_profile(artist_id)
    
    entry = {"task_id": task_id, "approved": approved, "timestamp": time.time()}
    if track_meta:
        entry["meta"] = track_meta
    
    if approved:
        profile.setdefault("approved_tracks", []).append(entry)
    else:
        profile.setdefault("rejected_tracks", []).append(entry)
    
    profile["interaction_count"] = profile.get("interaction_count", 0) + 1
    save_profile(profile)
    return profile


def build_artist_context(artist_id: str) -> str:
    """Build a context string from the artist's learned profile for the orchestrator."""
    profile = get_profile(artist_id)
    lines = []
    
    if profile.get("name"):
        lines.append(f"Artist: {profile['name']}")
    if profile.get("genre"):
        lines.append(f"Genre: {profile['genre']}")
    
    sig = profile.get("signature_elements") or []
    learned_sig = profile.get("learned_preferences", {}).get("signature_elements", [])
    all_sig = list(set(sig + learned_sig))
    if all_sig:
        lines.append(f"Signature sound elements: {', '.join(all_sig)}")
    
    if profile.get("tone"):
        lines.append(f"Tone: {profile['tone']}")
    
    bpm_spot = profile.get("bpm_sweet_spot", [120, 160])
    learned_bpm = profile.get("learned_preferences", {}).get("bpm_sweet_spot")
    if learned_bpm:
        lines.append(f"BPM range: {learned_bpm[0]}-{learned_bpm[1]}")
    else:
        lines.append(f"BPM range: {bpm_spot[0]}-{bpm_spot[1]}")
    
    neg = profile.get("negative_tags") or []
    learned_neg = profile.get("learned_preferences", {}).get("negative_tags", [])
    all_neg = list(set(neg + learned_neg))
    if all_neg:
        lines.append(f"AVOID: {', '.join(all_neg)}")
    
    if profile.get("approved_tracks"):
        lines.append(f"Tracks the artist approved: {len(profile['approved_tracks'])}")
    if profile.get("interaction_count", 0) > 0:
        lines.append(f"Interaction count: {profile['interaction_count']}")
    
    return "\n".join(lines)


def generate_onboarding_prompt(artist_id: str) -> str:
    """Generate an initial chat prompt when the artist hasn't set up their profile yet."""
    profile = get_profile(artist_id)
    if profile.get("name") or profile.get("signature_elements"):
        return None  # Already has some identity
    return (
        "Hey! I don't know your sound yet. "
        "Tell me what kind of music you make — "
        "what genre, what BPM range, what signature elements define you?"
    )
