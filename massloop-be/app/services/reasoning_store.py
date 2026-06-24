"""In-memory reasoning storage — agent writes, frontend polls."""
import time
from typing import Optional

# {session_id: {"reasoning": ["token1", "token2", ...], "done": bool, "reply": str}}
_reasoning_store: dict[str, dict] = {}

def create_session() -> str:
    import uuid
    sid = str(uuid.uuid4())[:8]
    _reasoning_store[sid] = {
        "reasoning": [],
        "done": False,
        "reply": "",
        "auto_generate": False,
        "audio_url": "",
        "task_id": "",
        "created_at": time.time(),
    }
    return sid

def append_reasoning(session_id: str, text: str):
    if session_id in _reasoning_store:
        _reasoning_store[session_id]["reasoning"].append(text)

def set_done(session_id: str, reply: str = "", auto_generate: bool = False, audio_url: str = "", task_id: str = ""):
    if session_id in _reasoning_store:
        _reasoning_store[session_id]["done"] = True
        _reasoning_store[session_id]["reply"] = reply
        _reasoning_store[session_id]["auto_generate"] = auto_generate
        _reasoning_store[session_id]["audio_url"] = audio_url
        _reasoning_store[session_id]["task_id"] = task_id

def get_reasoning(session_id: str) -> Optional[dict]:
    return _reasoning_store.get(session_id)

def cleanup_old_sessions(max_age_s: int = 300):
    now = time.time()
    stale = [sid for sid, data in _reasoning_store.items() if now - data.get("created_at", 0) > max_age_s]
    for sid in stale:
        del _reasoning_store[sid]
