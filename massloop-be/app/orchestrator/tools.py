"""CometAPI tools for the OpenAI Agents SDK orchestrator."""

import os
import time
from typing import Optional

import httpx
from loguru import logger

from app.config import settings

COMET_BASE_URL = os.getenv("SUNO_BASE_URL", "https://api.cometapi.com")
COMET_API_KEY = settings.suno_api_key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {COMET_API_KEY}",
        "Content-Type": "application/json",
    }


def generate_track(
    prompt: str,
    tags: str,
    title: str = "Massloop Track",
    mv: str = "chirp-v4",
    make_instrumental: bool = True,
    negative_tags: str = "",
) -> dict:
    """
    Submit a music generation task to CometAPI Suno.

    Args:
        prompt: Description or lyrics for the track.
        tags: Style tags separated by commas.
        title: Track title.
        mv: Suno model version (chirp-v3.0, chirp-v3.5, chirp-v4, chirp-auk, chirp-crow).
        make_instrumental: Whether to generate an instrumental track.
        negative_tags: Tags to avoid.

    Returns:
        dict with task_id, status, and raw API response.
    """
    if not COMET_API_KEY:
        logger.error("CometAPI key not configured")
        return {"error": "CometAPI key not configured"}

    payload = {
        "gpt_description_prompt": prompt,
        "tags": tags,
        "mv": mv,
        "title": title,
        "make_instrumental": make_instrumental,
    }
    if negative_tags:
        payload["negative_tags"] = negative_tags

    try:
        response = httpx.post(
            f"{COMET_BASE_URL}/suno/submit/music",
            headers=_headers(),
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != "success":
            msg = data.get("message", "Unknown CometAPI error")
            logger.error(f"CometAPI submit failed: {msg}")
            return {"error": msg, "raw": data}

        task_id = data.get("data")
        logger.success(f"CometAPI task submitted: {task_id}")
        return {"task_id": task_id, "status": "submitted", "raw": data}

    except httpx.HTTPStatusError as e:
        logger.error(f"CometAPI HTTP error: {e.response.status_code} {e.response.text[:200]}")
        return {"error": f"HTTP {e.response.status_code}", "details": e.response.text[:500]}
    except Exception as e:
        logger.error(f"CometAPI submit exception: {e}")
        return {"error": str(e)}


def poll_track(task_id: str, max_wait_s: int = 120) -> dict:
    """
    Poll CometAPI until the track completes or times out.

    Args:
        task_id: The CometAPI task ID.
        max_wait_s: Maximum seconds to wait.

    Returns:
        dict with status, audio_url, and clip metadata.
    """
    if not COMET_API_KEY:
        return {"error": "CometAPI key not configured"}

    deadline = time.time() + max_wait_s
    interval = 5

    while time.time() < deadline:
        try:
            response = httpx.get(
                f"{COMET_BASE_URL}/suno/fetch/{task_id}",
                headers=_headers(),
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "success":
                msg = data.get("message", "Unknown CometAPI error")
                logger.error(f"CometAPI fetch failed: {msg}")
                return {"error": msg, "raw": data}

            task = data.get("data", {})
            status = task.get("status", "UNKNOWN")
            clips = task.get("data", [])

            if status == "SUCCESS" and clips:
                clip = clips[0]
                audio_url = clip.get("audio_url", "")
                if audio_url:
                    logger.success(f"Track ready: {audio_url[:80]}...")
                    return {
                        "status": "SUCCESS",
                        "audio_url": audio_url,
                        "clip_id": clip.get("id"),
                        "title": clip.get("title"),
                        "duration": clip.get("duration"),
                        "raw": clip,
                    }

            if status == "FAILED":
                reason = task.get("fail_reason", "Unknown failure")
                logger.error(f"CometAPI task failed: {reason}")
                return {"status": "FAILED", "error": reason, "raw": task}

            logger.info(f"Task {task_id}: {status} (progress: {task.get('progress', '0%')})")
            time.sleep(interval)

        except httpx.HTTPStatusError as e:
            logger.error(f"CometAPI fetch HTTP error: {e.response.status_code}")
            return {"error": f"HTTP {e.response.status_code}", "details": e.response.text[:500]}
        except Exception as e:
            logger.error(f"CometAPI fetch exception: {e}")
            return {"error": str(e)}

    logger.warning(f"Polling timed out for task {task_id}")
    return {"status": "TIMEOUT", "task_id": task_id}


def get_style_suggestions(bpm: int, energy: float, venue: str) -> str:
    """
    Return style tag suggestions based on performance context.

    Args:
        bpm: Track BPM.
        energy: Energy level 0.0-1.0.
        venue: Venue type (warehouse, club, rave, festival, teknikal).

    Returns:
        Comma-separated style tags.
    """
    tags = []

    if bpm >= 160:
        tags.append("hardtek")
    elif bpm >= 150:
        tags.append("schranz")
    elif bpm >= 140:
        tags.append("hardgroove")
    elif bpm >= 130:
        tags.append("raw techno")
    elif bpm >= 125:
        tags.append("hypnotic techno")
    else:
        tags.append("deep house")

    if energy > 0.8:
        tags.append("high energy")
    elif energy < 0.4:
        tags.append("ambient")
    else:
        tags.append("grooving")

    venue_tags = {
        "warehouse": "industrial warehouse",
        "club": "underground club",
        "rave": "underground rave",
        "festival": "festival main stage",
        "teknikal": "teknival free party",
    }
    tags.append(venue_tags.get(venue.lower(), "underground"))

    return ", ".join(tags)
