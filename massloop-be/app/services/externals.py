"""Massloop.ai - External Adapters with Enhanced Settings Support

Layer 4: Implements interfaces with external services

Features:
- Configurable budget limits
- MIDI controller support
- Enhanced audio device management
- All adapter implementations
"""

import json, os, time, asyncio, numpy as np
from abc import ABC
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import httpx
import tempfile
from datetime import datetime
import librosa
import numpy as np
from io import BytesIO
import time

try:
import pygame
PYGAME_AVAILABLE = True
except ImportError:
PYGAME_AVAILABLE = False
logger.warning("pygame not available")

try:
import soundfile as sf
import io
SOUNDFILE_AVAILABLE = True
except ImportError:
SOUNDFILE_AVAILABLE = False

from app.models.entities import *
from app.services.interfaces import *

try:
  import sounddevice as sd
  SOUNDDEVICE_AVAILABLE = True
  logger.info("sounddevice imported successfully")
except (ImportError, OSError) as e:
  # ImportError: package not installed
  # OSError: package installed but libportaudio missing (Linux/Replit)
  SOUNDDEVICE_AVAILABLE = False
  sd = None  # Prevent NameError later
  logger.warning(f"sounddevice unavailable: {e.__class__.__name__}")
  logger.info("→ Using pygame-only audio mode")



# ============================================================================
# STORAGE ADAPTER
# ============================================================================

class FileStorageAdapter(StoragePort):
"""File-based storage using JSON"""

def __init__(self, data_dir: str = "data"):
    self.data_dir = Path(data_dir)
    self.profiles_dir = self.data_dir / "profiles"
    self.performances_dir = self.data_dir / "performances"
    self.metrics_dir = self.data_dir / "metrics"
    self.voices_dir = self.data_dir / "voices"

    self.profiles_dir.mkdir(parents=True, exist_ok=True)
    self.performances_dir.mkdir(parents=True, exist_ok=True)
    self.metrics_dir.mkdir(parents=True, exist_ok=True)
    self.voices_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"FileStorage initialized: {self.data_dir}")


async def auto_save_checkpoint(
        self,
        phase: int,
        profile: ArtistProfile,
        perf_state: Optional[PerformanceState] = None,
        event_name: str = "",
        duration_minutes: int = 0,
        elapsed_seconds: float = 0.0,
        generated_track: Optional[LiveTrack] = None
) -> bool:
    """Auto-save checkpoint at each phase for crash recovery"""
    try:
        from dataclasses import asdict

        checkpoint = {
            "phase": phase,
            "timestamp": time.time(),
            "profile_name": profile.name,
            "event_name": event_name,
            "duration_minutes": duration_minutes,
            "elapsed_seconds": elapsed_seconds,

            # Performance state
            "perf_state": {
                "venue_type": perf_state.venue_type.value if perf_state and perf_state.venue_type else "",
                "current_energy": perf_state.current_energy if perf_state else 0.5,
                "total_cost_eur": perf_state.total_cost_eur if perf_state else 0.0,
                "buffer_count": len(perf_state.buffer_tracks) if perf_state else 0,
                "played_count": len(perf_state.played_tracks) if perf_state else 0,
            },

            # Generated track (for recovery)
            "pre_generated_track_json": asdict(generated_track) if generated_track else None,
        }

        # Save to checkpoints directory
        checkpoint_dir = self.data_dir / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Keep only latest checkpoint per profile
        old_checkpoints = list(checkpoint_dir.glob(f"{profile.name}_*.json"))
        for old in old_checkpoints:
            try:
                old.unlink()
            except:
                pass

        checkpoint_path = checkpoint_dir / f"{profile.name}_phase_{phase}_{int(time.time())}.json"

        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)

        logger.debug(f"💾 Auto-saved: Phase {phase} checkpoint for {profile.name}")
        return True

    except Exception as e:
        logger.warning(f"⚠️ Auto-save failed (non-fatal): {e}")
        return False

async def load_last_checkpoint(self, profile_name: str) -> Optional[Dict[str, Any]]:
    """Load last checkpoint for recovery"""
    try:
        checkpoint_dir = self.data_dir / "checkpoints"

        if not checkpoint_dir.exists():
            return None

        checkpoints = list(checkpoint_dir.glob(f"{profile_name}_*.json"))

        if not checkpoints:
            logger.info(f"No checkpoint found for {profile_name}")
            return None

        latest = max(checkpoints, key=os.path.getmtime)

        with open(latest, 'r') as f:
            checkpoint = json.load(f)

        logger.success(f"✅ Checkpoint recovered: Phase {checkpoint['phase']}")
        return checkpoint

    except Exception as e:
        logger.warning(f"⚠️ Could not load checkpoint: {e}")
        return None

async def save_profile(self, profile: ArtistProfile) -> bool:
    """Save profile to JSON with ALL fields"""
    try:
        from dataclasses import asdict

        filepath = self.profiles_dir / f"{profile.name}.json"

        # Convert dataclass to dict (includes ALL fields automatically)
        data = asdict(profile)

        # Convert enums to strings for JSON serialization
        data['styles'] = [s.value for s in profile.styles]

        # ✅ Handle reference_tracks
        if hasattr(profile, 'reference_tracks') and profile.reference_tracks:
            data['reference_tracks'] = profile.reference_tracks
            logger.debug(f"📀 Saved {len(profile.reference_tracks)} reference track(s)")
        else:
            data['reference_tracks'] = []

        # Convert references to dicts if they exist
        if profile.references:
            data['references'] = [
                {
                    'file_path': ref.file_path,
                    # ✅ FIX: Check if analysis is already a dict
                    'analysis': ref.analysis if isinstance(ref.analysis, dict) else (
                        ref.analysis.__dict__ if hasattr(ref.analysis, '__dict__') else None
                    )
                }
                for ref in profile.references
            ]

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Profile saved with {len(data)} fields: {filepath}")
        logger.success(f"✓ Profile saved: {filepath}")
        return True

    except Exception as e:
        logger.error(f"Save profile failed: {e}")
        logger.exception(e)
        return False

async def load_profile(self, name: str) -> Optional[ArtistProfile]:
    """Load profile from JSON with ALL fields, including references."""
    try:
        filepath = self.profiles_dir / f"{name}.json"
        if not filepath.exists():
            return None

        with open(filepath, 'r') as f:
            data = json.load(f)

        # Load core profile fields (as before)
        profile = ArtistProfile(
            name=data["name"],
            styles=[UndergroundStyle(s) for s in data["styles"]],
            bpm_min=data["bpm_min"],
            bpm_max=data["bpm_max"],
            created_at=data.get("created_at", time.time()),
            custom_style_description=data.get("custom_style_description", ""),
            influences=data.get("influences", []),
            instruments=data.get("instruments", []),
            vibe_description=data.get("vibe_description", ""),
            darkness_level=data.get("darkness_level", 0.5),
            complexity_level=data.get("complexity_level", 0.5),
            signature_sound=data.get("signature_sound", ""),
            voice_profiles=data.get("voice_profiles", []),
        )

        # Restore reference_tracks
        profile.reference_tracks = data.get("reference_tracks", [])

        # Restore references (audio analysis)
        profile.references = []
        for ref_data in data.get("references", []):
            # Use name from JSON or extract from file_path if missing
            ref_name = ref_data.get("name") or (
                        ref_data.get("file_path") and ref_data["file_path"].split("/")[-1]) or "Unknown"
            ref = AudioReference(
                name=ref_name,
                file_path=ref_data.get("file_path"),
                analysis=ref_data.get("analysis")
            )
            profile.references.append(ref)

        logger.success(f"✓ Profile loaded: {name} ({len(profile.references)} references)")
        return profile

    except Exception as e:
        logger.error(f"Load profile failed: {e}")
        return None

async def list_profiles(self) -> List[str]:
    try:
        return [f.stem for f in self.profiles_dir.glob("*.json")]
    except Exception as e:
        logger.error(f"List profiles failed: {e}")
        return []

async def delete_profile(self, name: str) -> bool:
    try:
        filepath = self.profiles_dir / f"{name}.json"
        if filepath.exists():
            filepath.unlink()
        return True
    except Exception as e:
        logger.error(f"Delete profile failed: {e}")
        return False

async def save_performance(self, state: PerformanceState) -> bool:
    try:
        timestamp = int(state.start_time or time.time())
        filename = f"{state.event_name}_{timestamp}.json"
        filepath = self.performances_dir / filename

        data = {
            "event_name": state.event_name,
            "venue": state.venue_type.value,
            "start_time": state.start_time,
            "end_time": state.end_time,
            "duration_minutes": state.duration_minutes,
            "tracks_played": len(state.played_tracks),
            "tracks_generated": len(state.generated_tracks)
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Save performance failed: {e}")
        return False

async def load_performance(self, event_name: str, timestamp: float) -> Optional[PerformanceState]:
    return None

async def save_voice_profile(self, name: str, file_path: str) -> bool:
    return True

async def save_voice_profile_bytes(self, name: str, wav_bytes: bytes) -> bool:
    return True

async def save_metrics(self, metrics: Dict[str, Any]) -> bool:
    try:
        timestamp = metrics.get("timestamp", datetime.now().isoformat())
        filename = f"metrics_{timestamp.replace(':', '-')}.json"
        filepath = self.metrics_dir / filename

        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Save metrics failed: {e}")
        return False

async def load_metrics(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    return []

async def get_voice_profile_path(self, name: str) -> Optional[str]:
    """Get path to voice profile WAV file."""
    try:
        # Try .wav first
        voice_path = self.voices_dir / f"{name}.wav"
        if voice_path.exists():
            logger.debug(f"Found voice profile: {voice_path}")
            return str(voice_path)

        # Try .mp3 fallback
        voice_path = self.voices_dir / f"{name}.mp3"
        if voice_path.exists():
            logger.debug(f"Found voice profile (mp3): {voice_path}")
            return str(voice_path)

        logger.warning(f"Voice profile not found: {name}")
        return None

    except Exception as e:
        logger.error(f"Get voice profile path failed: {e}")
        return None





# ============================================================================
# AUDIO ADAPTER (ENHANCED)
# ============================================================================

class PygameAudioAdapter:
  """
  Audio adapter with REAL device detection

  Uses sounddevice for device enumeration (better than pygame)
  Supports:
  - macOS: Built-in speakers, JBL, AirPods, USB interfaces
  - Linux: PulseAudio, ALSA devices
  - Windows: MME, DirectSound, WASAPI devices
  """

  def __init__(self):
  self.initialized = False
  self.available = PYGAME_AVAILABLE
  self.current_device_id = None
  self.sample_rate = 44100
  self.channels = 2

  if SOUNDDEVICE_AVAILABLE:
      logger.info("✓ sounddevice available - real device detection enabled")
  else:
      logger.warning("⚠ sounddevice missing - using basic device list")

  async def initialize(self, sample_rate: int = 44100, channels: int = 2) -> bool:
  """Initialize audio system"""
  if not self.available:
      logger.warning("pygame not available")
      return False

  try:
      if not self.initialized:
          pygame.mixer.init(sample_rate, -16, channels, 2048)
          self.sample_rate = sample_rate
          self.channels = channels
          self.initialized = True
          logger.info(f"Audio initialized: {sample_rate}Hz, {channels}ch")
      return True
  except Exception as e:
      logger.error(f"Audio init failed: {e}")
      return False

  async def get_available_devices(self) -> List[Dict[str, Any]]:
"""
Get audio devices - Works on Linux/Replit WITHOUT sounddevice

Tries sounddevice first (for real device detection on macOS)
Falls back to pygame-compatible defaults on Linux/Replit
"""
devices = []

# Try sounddevice if available AND working
if SOUNDDEVICE_AVAILABLE:
    try:
        # Attempt to query devices
        all_devices = sd.query_devices()
        default_output = sd.default.device[1]  # [input, output]

        logger.info(f"✓ sounddevice working: {len(all_devices)} devices")

        # Filter to output devices only
        for i, device in enumerate(all_devices):
            if device['max_output_channels'] == 0:
                continue

            hostapi_info = sd.query_hostapis(device['hostapi'])

            device_info = {
                "name": device['name'],
                "id": i,
                "channels": device['max_output_channels'],
                "sample_rate": int(device['default_samplerate']),
                "is_default": (i == default_output),
                "hostapi": hostapi_info['name'],
                "latency_ms": device['default_low_output_latency'] * 1000
            }

            devices.append(device_info)

            default_marker = " [DEFAULT]" if device_info['is_default'] else ""
            logger.info(f"  • {device_info['name']}{default_marker}")

        if devices:
            return devices  # Success!

    except Exception as e:
        logger.warning(f"sounddevice failed ({e.__class__.__name__})")
        logger.info("→ Falling back to pygame-only mode")
else:
    logger.info("sounddevice not available, using pygame-only mode")

# FALLBACK: Platform-specific defaults (works everywhere!)
import platform
system = platform.system()

logger.info(f"Detected platform: {system}")

if system == "Darwin":  # macOS
    devices = [
        {
            "name": "Built-in Output",
            "id": 0,
            "channels": 2,
            "sample_rate": 44100,
            "is_default": True,
            "hostapi": "CoreAudio",
            "latency_ms": 5.0
        }
    ]
elif system == "Linux":  # Linux/Replit/Ubuntu
    devices = [
        {
            "name": "PulseAudio / ALSA Output",
            "id": 0,
            "channels": 2,
            "sample_rate": 44100,
            "is_default": True,
            "hostapi": "ALSA",
            "latency_ms": 10.0
        }
    ]
elif system == "Windows":
    devices = [
        {
            "name": "Default Output Device",
            "id": 0,
            "channels": 2,
            "sample_rate": 44100,
            "is_default": True,
            "hostapi": "WASAPI",
            "latency_ms": 8.0
        }
    ]
else:  # Unknown platform
    devices = [
        {
            "name": "System Audio Output",
            "id": 0,
            "channels": 2,
            "sample_rate": 44100,
            "is_default": True,
            "hostapi": "System Default",
            "latency_ms": 10.0
        }
    ]

logger.info(f"✓ Using fallback: {devices[0]['name']}")
return devices


  async def get_latency_ms(self) -> float:
  """Get current audio output latency"""
  if SOUNDDEVICE_AVAILABLE and self.current_device_id is not None:
      try:
          device = sd.query_devices(self.current_device_id)
          return device['default_low_output_latency'] * 1000
      except:
          pass

  # Default estimate
  return 5.0

  async def set_output_device(self, device_id: int) -> bool:
  """
  Switch to different audio device

  Args:
      device_id: Device ID from get_available_devices()

  Returns:
      True if successful
  """
  try:
      self.current_device_id = device_id

      if SOUNDDEVICE_AVAILABLE:
          # Set sounddevice default output
          sd.default.device[1] = device_id  # [input, output]
          device = sd.query_devices(device_id)
          logger.info(f"Audio output set to: {device['name']}")

      # Reinitialize pygame mixer with new device
      if self.initialized:
          pygame.mixer.quit()
          await self.initialize(self.sample_rate, self.channels)

      return True

  except Exception as e:
      logger.error(f"Set device failed: {e}")
      return False

  async def play_track(self, track) -> bool:
  """Play a LiveTrack"""
  if not track.audio_data or track.is_mock:
      logger.info(f"Mock track: {track.name}")
      return True

  try:
      await self.stream_track(track.audio_data)
      return True
  except Exception as e:
      logger.error(f"Playback failed: {e}")
      return False

  async def stream_track(self, audio_data: bytes) -> bool:
  """Stream audio bytes to output"""
  if not self.initialized:
      await self.initialize()

  try:
      # Save to temp file and play via pygame
      with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
          tmp.write(audio_data)
          tmp_path = tmp.name

      pygame.mixer.music.load(tmp_path)
      pygame.mixer.music.play()

      logger.info(f"Streaming {len(audio_data)} bytes")
      return True

  except Exception as e:
      logger.error(f"Stream failed: {e}")
      return False

  async def stop_playback(self) -> bool:
  """Stop current playback"""
  try:
      pygame.mixer.music.stop()
      return True
  except Exception as e:
      logger.error(f"Stop failed: {e}")
      return False

  async def play_test_tone(self, duration_s: float = 1.0, frequency: float = 440.0) -> bool:
  """
  Play test tone (440Hz A note by default)

  Args:
      duration_s: Duration in seconds
      frequency: Frequency in Hz (440 = A4 note)
  """
  try:
      if not SOUNDDEVICE_AVAILABLE:
          logger.warning("sounddevice not available for test tone")
          return False

      # Generate sine wave
      t = np.linspace(0, duration_s, int(self.sample_rate * duration_s))
      wave = np.sin(2 * np.pi * frequency * t)
      wave = wave * 0.3  # 30% volume

      # Make stereo if needed
      if self.channels == 2:
          wave = np.column_stack((wave, wave))

      logger.info(f"Playing {frequency}Hz test tone for {duration_s}s")

      # Play directly via sounddevice
      sd.play(wave, self.sample_rate, device=self.current_device_id)
      sd.wait()

      return True

  except Exception as e:
      logger.error(f"Test tone failed: {e}")
      return False

  async def get_device_info_detailed(self, device_id: int) -> Dict[str, Any]:
  """
  Get detailed info about specific device

  Returns:
  - Full device capabilities
  - Supported sample rates
  - Latency characteristics
  """
  if not SOUNDDEVICE_AVAILABLE:
      return {}

  try:
      device = sd.query_devices(device_id)
      hostapi = sd.query_hostapis(device['hostapi'])

      return {
          "name": device['name'],
          "max_input_channels": device['max_input_channels'],
          "max_output_channels": device['max_output_channels'],
          "default_samplerate": device['default_samplerate'],
          "default_low_input_latency": device['default_low_input_latency'],
          "default_low_output_latency": device['default_low_output_latency'],
          "default_high_input_latency": device['default_high_input_latency'],
          "default_high_output_latency": device['default_high_output_latency'],
          "hostapi_name": hostapi['name'],
          "hostapi_device_count": hostapi['device_count']
      }
  except Exception as e:
      logger.error(f"Get device info failed: {e}")
      return {}

# ════════════════════════════════════════════════════════════════════════════════
# MASSLOOP AI - COMETAPI SUNO v5 ADAPTER (CLEAN REWRITE)
#
# Production-Ready for:
#   - Generate music with chirp-auk, chirp-v4-tau (text prompts + voice cloning)
#   - Create personas from clips for artist consistency
#   - Poll task completion with enhanced error handling
#   - Real-time music generation with Dagmara voice
#
# Based on: https://api.cometapi.com/doc
# ═══════════════════════════════════════════════════════════════════════════════

class CometSunoAdapter(AIGenerationPort):
    """
    CometAPI Suno v5 Adapter - Clean, Production-Ready Implementation

    **Modes Supported:**
    1. Customization (default) - Prompt + tags only
    2. Artist Consistency - Prompt + persona_id + artist_clip_id
    3. Persona Creation - Upload clip → get persona_id

    **Models:**
    - chirp-auk (v4.5) - supports voice, best for lyrics
    - chirp-v4-tau (v4) - for artist consistency
    - chirp-crow (v5) - latest, fastest

    **Endpoints:**
    - POST /suno/submit/music - Generate track
    - GET /suno/get/music - Poll status
    - POST /suno/persona/create - Create persona
    """

    def __init__(self):
        """Initialize CometAPI adapter with environment config."""
        self.api_key = os.getenv("SUNO_API_KEY", "")
        self.base_url = os.getenv("SUNO_BASE_URL", "https://api.cometapi.com")
        self.available = bool(self.api_key)
        self.timeout = httpx.Timeout(120.0)

        if self.available:
            logger.success(f"✓ CometAPI Suno v5 initialized")
            logger.debug(f"  Base URL: {self.base_url}")
        else:
            logger.warning("⚠️  No SUNO_API_KEY - using mock generation")

    # ════════════════════════════════════════════════════════════════════════════
    # CORE: MUSIC GENERATION
    # ════════════════════════════════════════════════════════════════════════════

    async def generate_track(self, request: GenerationRequest) -> Optional[LiveTrack]:
        """
        Generate music via Suno API.

        **Two modes:**
        1. Customization (default)
           └─ Requires: prompt, tags, mv, title

        2. Artist Consistency (voice cloning)
           └─ Requires: prompt, tags, mv, title, task, persona_id, artist_clip_id
        """
        start_time = time.time()
        request_id = f"track_{int(time.time() * 1000)}"

        logger.info(f"[{request_id}] 🎵 GENERATE START")

        if not self.available:
            logger.warning(f"[{request_id}] ⚠️  No API key - returning mock")
            return self._mock_track(request)

        try:
            # ════════════════════════════════════════════════════════════════
            # EXTRACT REQUEST DATA
            # ════════════════════════════════════════════════════════════════

            prompt = str(request.custom_prompt or request.theme or "Generate music").strip()
            if not prompt:
                prompt = "Generate music"

            tags = request.tags
            if isinstance(tags, (list, tuple)):
                tags = ", ".join(str(t) for t in tags)
            elif not isinstance(tags, str):
                tags = str(tags)
            tags = tags.strip() or "music"

            profile = getattr(request, 'artist_profile', None)
            persona_id = getattr(profile, 'persona_id', None) if profile else None
            artist_clip_id = getattr(profile, 'artist_clip_id', None) if profile else None

            profile_name = profile.name if profile else "Track"
            title = f"{profile_name}_{int(time.time())}"

            logger.info(f"[{request_id}] 🎵 Prompt: {prompt[:70]}...")
            logger.info(f"[{request_id}] 🏷️  Tags: {tags[:60]}...")
            if profile:
                logger.info(f"[{request_id}] 👤 Profile: {profile_name}")

            # ════════════════════════════════════════════════════════════════
            # BUILD PAYLOAD
            # ════════════════════════════════════════════════════════════════

            if persona_id and artist_clip_id:
                # MODE: ARTIST CONSISTENCY (voice cloning)
                logger.info(f"[{request_id}] 🎤 Mode: ARTIST CONSISTENCY")

                payload = {
                    "prompt": prompt,
                    "generation_type": "TEXT",
                    "tags": tags,
                    "mv": "chirp-v4-tau",  # ← REQUIRED for artist_consistency
                    "title": title,
                    "task": "artist_consistency",  # ← MAGIC FIELD
                    "persona_id": persona_id,  # ← FROM PERSONA CREATION
                    "artist_clip_id": artist_clip_id,  # ← FROM STEP 1
                }
                logger.debug(f"[{request_id}] payload: {json.dumps(payload, indent=2)[:200]}...")

            else:
                # MODE: CUSTOMIZATION (default)
                logger.info(f"[{request_id}] 🎵 Mode: CUSTOMIZATION")

                payload = {
                    "prompt": prompt,
                    "tags": tags,
                    "mv": request.mv_version or "chirp-v4",
                    "title": title,
                }
                logger.debug(f"[{request_id}] payload: {json.dumps(payload, indent=2)[:200]}...")

            # ════════════════════════════════════════════════════════════════
            # VALIDATE PAYLOAD
            # ════════════════════════════════════════════════════════════════

            # Ensure all values are JSON-serializable
            for key in list(payload.keys()):
                if payload[key] is not None and not isinstance(payload[key], (str, int, float, bool)):
                    payload[key] = str(payload[key])

            try:
                json.dumps(payload)
                logger.debug(f"[{request_id}] ✓ Payload valid JSON")
            except (TypeError, ValueError) as e:
                logger.error(f"[{request_id}] ❌ Payload JSON error: {e}")
                return self._mock_track(request)

            # ════════════════════════════════════════════════════════════════
            # SUBMIT TO SUNO
            # ════════════════════════════════════════════════════════════════

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            logger.debug(f"[{request_id}] POST {self.base_url}/suno/submit/music")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.post(
                        f"{self.base_url}/suno/submit/music",
                        json=payload,
                        headers=headers
                    )
                except httpx.TimeoutException:
                    logger.error(f"[{request_id}] ❌ Timeout")
                    return self._mock_track(request)
                except Exception as e:
                    logger.error(f"[{request_id}] ❌ HTTP error: {e}")
                    return self._mock_track(request)

                # ════════════════════════════════════════════════════════════
                # PARSE RESPONSE
                # ════════════════════════════════════════════════════════════

                logger.debug(f"[{request_id}] HTTP {response.status_code}")
                logger.debug(f"[{request_id}] Content-Type: {response.headers.get('content-type')}")

                # Check HTTP status
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError:
                    logger.error(f"[{request_id}] ❌ HTTP {response.status_code}")
                    logger.error(f"[{request_id}] {response.text[:300]}")
                    return self._mock_track(request)

                # Parse JSON
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"[{request_id}] ❌ JSON error: {e.msg}")
                    logger.error(f"[{request_id}] {response.text[:300]}")
                    return self._mock_track(request)

                # ✅ VALIDATE COMETAPI RESPONSE STRUCTURE
                if not isinstance(data, dict):
                    logger.error(f"❌ Expected dict, got {type(data).__name__}")
                    await asyncio.sleep(poll_interval)
                    return self._mock_track(request)

                # Check "code" field
                code = data.get("code")
                if code != "success":
                    message = data.get("message", "Unknown error")
                    logger.error(f"❌ API error: code={code}, message={message}")
                    return None

                # Extract "data" array
                clips = data.get("data", [])

                if not clips:
                    logger.debug("No clips yet, still processing...")
                    await asyncio.sleep(poll_interval)
                    return self._mock_track(request)

                if not isinstance(clips, list):
                    logger.error(f"❌ Expected 'data' to be list, got {type(clips).__name__}")
                    return None

                # Get first clip
                clip = clips[0]

                # NOW continue with status checking...
                status = clip.get("status", "UNKNOWN")

                # ════════════════════════════════════════════════════════════
                # VALIDATE RESPONSE
                # ════════════════════════════════════════════════════════════

                if data.get("code") != "success":
                    error = data.get("message", "Unknown error")
                    logger.error(f"[{request_id}] ❌ {error}")
                    return self._mock_track(request)

                task_id = data.get("data")
                if not task_id:
                    logger.error(f"[{request_id}] ❌ No task_id in response")
                    return self._mock_track(request)

                logger.success(f"[{request_id}] ✅ Task submitted: {task_id}")

                # ════════════════════════════════════════════════════════════
                # POLL FOR COMPLETION
                # ════════════════════════════════════════════════════════════

                track = await self._poll_completion(
                    client, headers, task_id, request, start_time
                )

                return track if track else self._mock_track(request)

        except Exception as e:
            logger.error(f"[{request_id}] ❌ Unexpected error: {type(e).__name__}: {e}")
            return self._mock_track(request)

# ════════════════════════════════════════════════════════════════════════════
# POLLING: WAIT FOR GENERATION COMPLETE
# ════════════════════════════════════════════════════════════════════════════

async def _poll_completion(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        task_id: str,
        request: GenerationRequest,
        start_time: float
) -> Optional[LiveTrack]:
    """
    Poll CometAPI /suno/get/music until generation completes.

    CORRECT FLOW (per CometAPI docs):
    1. POST /suno/get/music with {"ids": [task_id]}
    2. Response: {"code": "success", "data": [{"id": clip_id, "status": "complete", ...}]}
    3. Extract clip_id from data[0]['id']
    """

    max_wait = 240
    max_attempts = 60
    poll_interval = 4
    attempt = 0

    logger.info(f"⏳ Polling {task_id} (max {max_wait}s)...")

    # VALIDATE TASK_ID
    if not task_id or not isinstance(task_id, str):
        logger.error(f"❌ Invalid task_id: {task_id}")
        return None

    logger.debug(f"Task ID: {task_id}")
    logger.debug(f"Endpoint: POST {self.base_url}/suno/get/music")

    while True:
        attempt += 1
        elapsed = time.time() - start_time

        if elapsed > max_wait or attempt > max_attempts:
            logger.error(f"❌ Timeout: {elapsed:.0f}s / {max_wait}s")
            return None

        try:
            # MAKE REQUEST (POST per CometAPI docs)
            payload = {"ids": [task_id]}

            logger.debug(f"[Attempt {attempt}] POST /suno/get/music with ids=[{task_id}]")

            response = await client.post(
                f"{self.base_url}/suno/get/music",
                json=payload,
                headers=headers,
                timeout=30.0
            )

            # CHECK HTTP STATUS
            logger.debug(f"HTTP {response.status_code}")

            if response.status_code != 200:
                logger.warning(
                    f"⚠️  Poll HTTP {response.status_code} "
                    f"(attempt {attempt}/{max_attempts})"
                )
                logger.debug(f"Response: {response.text[:200]}")
                await asyncio.sleep(poll_interval)
                continue

            # PARSE JSON
            try:
                data = response.json()
                logger.debug(f"✓ JSON parsed")

            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parse error (attempt {attempt})")
                logger.error(f"   Error: {e.msg} at position {e.pos}")
                logger.error(f"   Content-Type: {response.headers.get('content-type')}")
                logger.error(f"   Response (first 300 chars):\n{response.text[:300]}")

                # If HTML, API is returning error page
                if response.text.strip().startswith('<'):
                    logger.critical("❌ CRITICAL: API returned HTML error page!")
                    logger.critical("   Check: API key, endpoint URL, API status")
                    return None

                await asyncio.sleep(poll_interval)
                continue

            # VALIDATE RESPONSE STRUCTURE (CometAPI format)
            # CometAPI returns: {"code": "success", "message": "", "data": [...]}
            if not isinstance(data, dict):
                logger.error(f"❌ Expected dict, got {type(data).__name__}")
                await asyncio.sleep(poll_interval)
                continue

            # Check "code" field
            code = data.get("code")
            if code != "success":
                message = data.get("message", "Unknown error")
                logger.error(f"❌ API error: code={code}, message={message}")
                return None

            # Extract "data" array
            clips = data.get("data", [])

            if not clips:
                logger.debug("No clips yet, still processing...")
                await asyncio.sleep(poll_interval)
                continue

            if not isinstance(clips, list):
                logger.error(f"❌ Expected 'data' to be list, got {type(clips).__name__}")
                return None

            # Get first clip
            clip = clips[0]

            # CHECK CLIP STATUS
            status = clip.get("status", "UNKNOWN")

            logger.info(
                f"📊 Status: {status:<12} | "
                f"attempt {attempt}/{max_attempts} | {elapsed:.0f}s"
            )

            # HANDLE STATUS
            if status == "complete":
                logger.success(f"✅ Complete! ({attempt} attempts, {elapsed:.0f}s)")

                # Extract clip_id (CRITICAL for persona creation)
                clip_id = clip.get("id")

                if not clip_id:
                    logger.error("❌ Clip missing 'id' field!")
                    logger.debug(f"Clip data: {clip}")
                    return None

                logger.debug(f"Clip ID: {clip_id}")

                # Build LiveTrack with CORRECT field mapping
                track = LiveTrack(
                    name=clip.get("title", f"Track_{int(time.time())}"),
                    style=getattr(request, "style", UndergroundStyle.ACID_TECHNO),
                    bpm=getattr(request, "bpm", 120),
                    duration_seconds=int(clip.get("metadata", {}).get("duration", 240)),
                    energy=getattr(request, "energy", 0.7),

                    # ✅ CRITICAL: Store actual clip_id (no fallback!)
                    clip_id=clip_id,

                    # Store URLs at top level (not in metadata)
                    audio_url=clip.get("audio_url"),
                    video_url=clip.get("video_url"),
                    image_url=clip.get("image_url"),

                    generation_time=elapsed,

                    metadata={
                        "task_id": task_id,
                        "model_version": clip.get("major_model_version"),
                        "tags": clip.get("metadata", {}).get("tags"),
                        "prompt": clip.get("metadata", {}).get("prompt"),
                    }
                )

                logger.success(f"🎵 Track: {track.name} | Clip: {clip_id}")
                return track

            elif status == "error" or status == "failed":
                error = clip.get("error_message", "Unknown error")
                logger.error(f"❌ Generation FAILED: {error}")
                return None

            elif status in ["submitted", "queued", "streaming"]:
                # Still processing
                logger.debug(f"Status: {status}, waiting...")
                await asyncio.sleep(poll_interval)
                continue

            else:
                logger.warning(f"⚠️  Unknown status: {status}, continuing...")
                await asyncio.sleep(poll_interval)
                continue

        except asyncio.TimeoutError:
            logger.warning(f"⚠️  Poll timeout (attempt {attempt})")
            await asyncio.sleep(poll_interval)
            continue

        except httpx.HTTPStatusError as e:
            logger.error(f"⚠️  HTTP error (attempt {attempt}): {e}")
            await asyncio.sleep(poll_interval)
            continue

        except Exception as e:
            logger.error(
                f"⚠️  Poll error (attempt {attempt}): "
                f"{type(e).__name__}: {e}"
            )
            logger.debug("Traceback:", exc_info=True)
            await asyncio.sleep(poll_interval)
            continue

    # Should never reach here
    logger.error("❌ Polling loop exited unexpectedly")
    return None

# ════════════════════════════════════════════════════════════════════════════
# PERSONA MANAGEMENT: VOICE CLONING
# ════════════════════════════════════════════════════════════════════════════

async def create_persona_from_clip(
        self,
        clip_id: str,
        artist_name: str,
        description: str = "",
        is_public: bool = False
) -> Optional[str]:
    """
    Create a Suno persona from a generated clip.

    **Workflow:**
    1. Generate track with chirp-auk → get clip_id
    2. Call this function with clip_id → get persona_id
    3. Use persona_id for future generations with artist_consistency

    **Args:**
    - clip_id: UUID from generated track
    - artist_name: Name for persona (e.g., "Devatara")
    - description: Style/artist description
    - is_public: Make persona public

    **Returns:**
    - persona_id (UUID) if success
    - None if failed
    """

    if not self.available:
        logger.warning("⚠️  No API key - cannot create persona")
        return None

    if not clip_id or not isinstance(clip_id, str):
        logger.error(f"❌ Invalid clip_id: {clip_id}")
        return None

    logger.info(f"🎤 Creating persona: {artist_name}")
    logger.debug(f"   Clip: {clip_id}")
    logger.debug(f"   Description: {description}")

    try:
        # ════════════════════════════════════════════════════════════
        # BUILD PAYLOAD (per CometAPI docs)
        # ════════════════════════════════════════════════════════════

        payload = {
            "root_clip_id": clip_id,
            "name": artist_name,
            "description": description or "",
            "clips": [clip_id],
            "is_public": is_public,
        }

        # Type validation
        for key in ["name", "description"]:
            if not isinstance(payload[key], str):
                payload[key] = str(payload[key])

        if not isinstance(payload["clips"], list):
            payload["clips"] = [clip_id]

        if not isinstance(payload["is_public"], bool):
            payload["is_public"] = bool(payload["is_public"])

        logger.debug(f"Payload: {json.dumps(payload, indent=2)[:200]}...")

        # ════════════════════════════════════════════════════════════
        # SUBMIT
        # ════════════════════════════════════════════════════════════

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        logger.debug(f"POST {self.base_url}/suno/persona/create")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/suno/persona/create",
                json=payload,
                headers=headers
            )

            # ════════════════════════════════════════════════════════
            # PARSE RESPONSE
            # ════════════════════════════════════════════════════════

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError:
                logger.error(f"❌ HTTP {response.status_code}")
                logger.error(f"   {response.text[:300]}")
                return None

            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error(f"❌ JSON parse error")
                logger.error(f"   {response.text[:300]}")
                return None

            # ════════════════════════════════════════════════════════
            # EXTRACT PERSONA_ID
            # ════════════════════════════════════════════════════════

            persona_id = data.get("id")  # ← Per CometAPI docs

            if not persona_id:
                logger.error(f"❌ No persona_id in response")
                logger.debug(f"   Response: {data}")
                return None

            logger.success(f"✅ Persona created: {persona_id}")
            logger.debug(f"   Name: {data.get('name')}")
            logger.debug(f"   Description: {data.get('description')}")

            return persona_id

    except Exception as e:
        logger.error(f"❌ Persona creation failed: {type(e).__name__}: {e}")
        return None

async def setup_artist_persona_workflow(
        self,
        artist_profile: ArtistProfile,
        initial_request: GenerationRequest
) -> bool:
    """
    Complete workflow: Generate → Create Persona → Store.

    **STEP 1:** Generate track with chirp-auk
    **STEP 2:** Create persona from clip_id
    **STEP 3:** Store persona_id in profile

    **Result:** Profile ready for artist_consistency generations
    """

    logger.info(f"🎤 PERSONA SETUP: {artist_profile.name}")

    # ════════════════════════════════════════════════════════════════
    # STEP 1: Generate initial track
    # ════════════════════════════════════════════════════════════════

    logger.info("STEP 1/3: Generating initial track...")
    initial_request.mv_version = "chirp-auk"  # REQUIRED for persona creation

    track = await self.generate_track(initial_request)

    if not track or not track.clip_id:
        logger.error("❌ STEP 1 failed: Could not generate track")
        return False

    logger.success(f"✅ STEP 1 complete: {track.clip_id}")

    # ════════════════════════════════════════════════════════════════
    # STEP 2: Create persona
    # ════════════════════════════════════════════════════════════════

    logger.info("STEP 2/3: Creating persona...")

    persona_id = await self.create_persona_from_clip(
        clip_id=track.clip_id,
        artist_name=artist_profile.name,
        description=artist_profile.signature_sound or artist_profile.default_theme,
        is_public=False
    )

    if not persona_id:
        logger.error("❌ STEP 2 failed: Could not create persona")
        return False

    logger.success(f"✅ STEP 2 complete: {persona_id}")

    # ════════════════════════════════════════════════════════════════
    # STEP 3: Store in profile
    # ════════════════════════════════════════════════════════════════

    logger.info("STEP 3/3: Storing in profile...")

    artist_profile.persona_id = persona_id
    artist_profile.artist_clip_id = track.clip_id

    logger.success(f"✅ STEP 3 complete: Profile updated")
    logger.success(f"✅ PERSONA SETUP COMPLETE!")
    logger.info(f"   Artist: {artist_profile.name}")
    logger.info(f"   Persona: {persona_id}")
    logger.info(f"   Clip: {track.clip_id}")

    return True

# ════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ════════════════════════════════════════════════════════════════════════════

def _mock_track(self, request: GenerationRequest) -> LiveTrack:
    """Return mock track for testing/fallback."""
    return LiveTrack(
        # REQUIRED (in order):
        name="Mock Track (testing mode)",
        style=request.style or UndergroundStyle.ACID_TECHNO,  # ← MOVE TO 2nd
        bpm=request.bpm or 120,
        duration_seconds=request.duration_seconds or 30,  # ✅ CORRECT PARAM
        energy=request.energy or 0.7,
    )

async def health_check(self) -> bool:
    """Check if API is available."""
    return self.available

# In CometSunoAdapter class, add:

async def add_vocals(self, track_id: str, vocal_prompt: str) -> Optional[LiveTrack]:
    """
    NOT IMPLEMENTED for MassLoop.
    (Would be for dubbing/overpainting mode)
    """
    logger.warning("⚠️  add_vocals() not supported yet")
    return None

def get_service_info(self) -> Dict:
    """Get service capabilities."""
    return {
        "name": "CometAPI Suno v5",
        "models": ["chirp-auk", "chirp-v4-tau", "chirp-crow"],
        "modes": ["customization", "artist_consistency"],
        "voice_cloning": True,
        "max_duration": 240,
        "supports_lyrics": True,
    }


# ============================================================================
# OTHER ADAPTERS
# ============================================================================

class MockCrowdSensing(CrowdSensingPort):
def __init__(self):
    self.base_energy = 0.7

async def initialize(self) -> bool:
    return True

async def get_crowd_energy(self) -> float:
    variation = (time.time() % 10) / 50
    return min(1.0, max(0.0, self.base_energy + variation - 0.1))

async def get_crowd_feedback(self) -> Dict[str, float]:
    energy = await self.get_crowd_energy()
    return {
        "energy": energy,
        "approval": energy * 0.9,
        "movement": energy * 0.95,
        "volume": energy * 0.85
    }

async def calibrate(self, duration_s: float = 10.0) -> bool:
    return True


class LibrosaReferenceAnalyzer(ReferenceAnalysisPort):
"""
PRO-LEVEL audio analysis using librosa.

Analyzes tracks like a mastering engineer:
- Spectral characteristics
- Frequency distribution
- Transient shaping
- Dynamic range
- Stereo width
"""

def __init__(self):
    self.available = None

async def analyze_audio_file(self, file_path: str) -> AudioReference:
    """
    Deep audio analysis of reference track.

    Returns:
        AudioReference with pro-level metrics
    """
    try:
        import librosa
        import librosa.feature
        import scipy.signal

        logger.info(f"🔬 Analyzing: {os.path.basename(file_path)}")

        # Load audio (30 seconds max for speed)
        y, sr = librosa.load(file_path, duration=60, sr=44100)

        # ============================================================
        # BASIC METRICS
        # ============================================================

        # BPM detection
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

        # Key detection via chroma
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        key_idx = np.argmax(np.mean(chroma, axis=1))
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key = keys[key_idx]

        # Overall energy (RMS)
        rms = librosa.feature.rms(y=y)
        energy = float(np.mean(rms))
        energy_normalized = min(1.0, energy * 2)

        # ============================================================
        # SPECTRAL ANALYSIS
        # ============================================================

        # Spectral centroid (brightness)
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

        # Spectral rolloff (high-freq content)
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85))

        # Spectral bandwidth (spread)
        spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))

        # ============================================================
        # FREQUENCY DISTRIBUTION (6-band analysis)
        # ============================================================

        # Get STFT for frequency analysis
        D = np.abs(librosa.stft(y))
        freqs = librosa.fft_frequencies(sr=sr)

        # Define frequency bands
        def get_band_energy(D, freqs, f_low, f_high):
            band_mask = (freqs >= f_low) & (freqs < f_high)
            band_energy = np.mean(D[band_mask, :])
            return float(band_energy)

        sub_bass = get_band_energy(D, freqs, 20, 60)  # Sub-bass
        bass = get_band_energy(D, freqs, 60, 250)  # Bass
        low_mid = get_band_energy(D, freqs, 250, 500)  # Low-mids
        mid = get_band_energy(D, freqs, 500, 2000)  # Mids
        high_mid = get_band_energy(D, freqs, 2000, 6000)  # High-mids
        high = get_band_energy(D, freqs, 6000, 20000)  # Highs

        # Normalize band energies to 0-1 range
        total_energy = sub_bass + bass + low_mid + mid + high_mid + high
        if total_energy > 0:
            sub_bass /= total_energy
            bass /= total_energy
            low_mid /= total_energy
            mid /= total_energy
            high_mid /= total_energy
            high /= total_energy

        # ============================================================
        # DYNAMICS & TRANSIENTS
        # ============================================================

        # Dynamic range (dB difference between loud and quiet parts)
        rms_db = librosa.amplitude_to_db(rms)
        dynamic_range = float(np.max(rms_db) - np.percentile(rms_db, 10))

        # Onset detection (transient density)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
        transient_density = len(onsets) / (len(y) / sr)  # Transients per second

        # Onset strength (how hard transients hit)
        onset_strength = float(np.mean(onset_env))
        onset_strength_normalized = min(1.0, onset_strength / 5.0)

        # Percussive vs harmonic separation
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        percussive_ratio = float(np.mean(np.abs(y_percussive)) / (np.mean(np.abs(y_harmonic)) + 1e-6))
        percussive_ratio_normalized = min(1.0, percussive_ratio)

        # ============================================================
        # STEREO WIDTH (if stereo file)
        # ============================================================

        stereo_width = 0.5  # Default to centered
        try:
            y_stereo, sr_stereo = librosa.load(file_path, duration=30, sr=44100, mono=False)
            if y_stereo.shape[0] == 2:  # Stereo file
                # Calculate correlation between L/R channels
                correlation = np.corrcoef(y_stereo[0], y_stereo[1])[0, 1]
                stereo_width = float((1.0 - correlation) / 2.0)  # 0=mono, 1=wide
        except:
            pass  # Mono file or error

        # ============================================================
        # RHYTHMIC REGULARITY
        # ============================================================

        # Measure how regular the beat is (4/4 vs broken)
        if len(beats) > 1:
            beat_intervals = np.diff(beats)
            groove_regularity = 1.0 - float(np.std(beat_intervals) / (np.mean(beat_intervals) + 1e-6))
            groove_regularity = min(1.0, max(0.0, groove_regularity))
        else:
            groove_regularity = 0.5

        # ============================================================
        # CREATE REFERENCE OBJECT
        # ============================================================

        reference = AudioReference(
            name=Path(file_path).stem,
            file_path=file_path,

            # Basic
            tempo=float(tempo),
            key=key,
            energy=energy_normalized,
            analyzed=True,

            # Spectral
            spectral_centroid=float(spectral_centroid),
            spectral_rolloff=float(spectral_rolloff),
            spectral_bandwidth=float(spectral_bandwidth),

            # Frequency bands
            sub_bass_energy=sub_bass * 10,  # Scale up for readability
            bass_energy=bass * 10,
            low_mid_energy=low_mid * 10,
            mid_energy=mid * 10,
            high_mid_energy=high_mid * 10,
            high_energy=high * 10,

            # Dynamics
            dynamic_range_db=dynamic_range,
            transient_density=transient_density,
            percussive_ratio=percussive_ratio_normalized,

            # Spatial
            stereo_width=stereo_width,

            # Rhythmic
            onset_strength=onset_strength_normalized,
            groove_regularity=groove_regularity
        )

        logger.success(f"✓ Analyzed: {reference.to_producer_description()[:80]}...")
        return reference

    except ImportError:
        logger.warning("librosa not installed - using basic fallback")
        return AudioReference(
            name=Path(file_path).stem,
            file_path=file_path,
            tempo=130.0,
            key="C",
            energy=0.7,
            analyzed=False
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return AudioReference(
            name=Path(file_path).stem,
            file_path=file_path,
            tempo=130.0,
            key="C",
            energy=0.7,
            analyzed=False
        )

async def analyze_batch(self, file_paths: List[str]) -> List[AudioReference]:
    """Analyze multiple reference tracks"""
    return [await self.analyze_audio_file(p) for p in file_paths]

async def get_supported_formats(self) -> List[str]:
    return ["mp3", "wav", "flac", "ogg", "m4a"]

async def analyze_audio_bytes(self, audio_bytes: bytes, requested_bpm: int) -> AudioAnalysisResult:
    """Analyze audio from bytes (MP3/WAV)."""
    if not self.available:
        return self._mock_analysis(requested_bpm)

    try:
        import librosa
        import librosa.feature
        import io
        import soundfile as sf

        logger.info(f"🔍 Analyzing {len(audio_bytes)} bytes...")

        # Load audio from bytes
        audio_file = io.BytesIO(audio_bytes)
        y, sr = librosa.load(audio_file, sr=44100, duration=30)  # First 30s for speed

        return await self._analyze_waveform(y, sr, requested_bpm)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return self._mock_analysis(requested_bpm)


class LibrosaAudioAnalyzer(AudioAnalysisPort):
"""
PRODUCTION-READY real-time audio analysis using librosa.

Analyzes Suno output to:
- Validate BPM accuracy
- Measure actual energy
- Detect audio issues (clipping, silence)
- Build feedback loop for prompt optimization

Fast enough for stage use (~0.5s per track).
"""

def __init__(self):
    try:
        import librosa
        import librosa.feature
        self.available = True
        logger.success("✅ Librosa analyzer initialized")
    except ImportError:
        self.available = False
        logger.warning("❌ librosa not installed - analysis disabled")

async def analyze_audio_bytes(self, audio_bytes: bytes, requested_bpm: int) -> AudioAnalysisResult:
    """Analyze audio from bytes (MP3/WAV)."""
    if not self.available:
        return self._mock_analysis(requested_bpm)

    try:
        import librosa
        import librosa.feature
        import io
        import soundfile as sf

        logger.info(f"🔍 Analyzing {len(audio_bytes)} bytes...")

        # Load audio from bytes
        audio_file = io.BytesIO(audio_bytes)
        y, sr = librosa.load(audio_file, sr=44100, duration=30)  # First 30s for speed

        return await self._analyze_waveform(y, sr, requested_bpm)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return self._mock_analysis(requested_bpm)

async def analyze_audio_file(self, filepath: str, requested_bpm: int) -> AudioAnalysisResult:
    """Analyze audio from file path."""
    if not self.available:
        return self._mock_analysis(requested_bpm)

    try:
        import librosa

        logger.info(f"🔍 Analyzing {Path(filepath).name}...")
        y, sr = librosa.load(filepath, sr=44100, duration=30)

        return await self._analyze_waveform(y, sr, requested_bpm)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return self._mock_analysis(requested_bpm)

async def quick_quality_check(self, audio_bytes: bytes) -> bool:
    """Fast quality check without full analysis."""
    if not self.available:
        return True  # Pass by default

    try:
        import librosa
        import io

        audio_file = io.BytesIO(audio_bytes)
        y, sr = librosa.load(audio_file, sr=44100, duration=10)  # Only 10s for speed

        # Check for clipping
        if np.max(np.abs(y)) > 0.99:
            logger.warning("⚠️ Audio is clipping!")
            return False

        # Check for silence
        rms = np.mean(librosa.feature.rms(y=y))
        if rms < 0.01:
            logger.warning("⚠️ Track is nearly silent!")
            return False

        return True

    except Exception as e:
        logger.warning(f"Quick check failed: {e}")
        return True  # Pass by default on error

async def _analyze_waveform(self, y: np.ndarray, sr: int, requested_bpm: int) -> AudioAnalysisResult:
    """Core analysis logic."""
    import librosa
    import librosa.feature

    # === 1. BPM DETECTION ===
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    actual_bpm = float(tempo)
    bpm_error = abs(actual_bpm - requested_bpm) / requested_bpm
    bpm_accuracy = max(0.0, 1.0 - bpm_error)

    logger.info(f"🎵 BPM: {actual_bpm:.1f} (requested {requested_bpm}, accuracy {bpm_accuracy:.1%})")

    # === 2. ENERGY (RMS) ===
    rms = librosa.feature.rms(y=y)
    actual_energy = float(np.mean(rms))

    # === 3. SPECTRAL FEATURES ===
    spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    spectral_rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))
    spectral_bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))

    # === 4. FREQUENCY BANDS ===
    D = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)

    subbass = np.mean(D[(freqs >= 20) & (freqs < 60)])
    bass = np.mean(D[(freqs >= 60) & (freqs < 250)])
    mid = np.mean(D[(freqs >= 250) & (freqs < 2000)])
    high = np.mean(D[(freqs >= 2000)])

    total_energy = subbass + bass + mid + high
    if total_energy > 0:
        subbass /= total_energy
        bass /= total_energy
        mid /= total_energy
        high /= total_energy

    # === 5. DYNAMICS ===
    rms_db = librosa.amplitude_to_db(rms)
    dynamic_range = float(np.max(rms_db) - np.percentile(rms_db, 10))

    # === 6. TRANSIENTS ===
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
    transient_density = len(onsets) / (len(y) / sr)  # Per second
    onset_strength = float(np.mean(onset_env))

    # === 7. QUALITY CHECKS ===
    is_clipping = float(np.max(np.abs(y))) > 0.99
    is_silent = actual_energy < 0.01

    duration = len(y) / sr

    logger.success(
        f"✅ Analysis complete: BPM={actual_bpm:.1f}, Energy={actual_energy:.2f}, Brightness={spectral_centroid:.0f}Hz")

    return AudioAnalysisResult(
        actual_bpm=actual_bpm,
        actual_energy=actual_energy,
        duration_seconds=duration,
        spectral_centroid=spectral_centroid,
        spectral_rolloff=spectral_rolloff,
        spectral_bandwidth=spectral_bandwidth,
        subbass_energy=float(subbass),
        bass_energy=float(bass),
        mid_energy=float(mid),
        high_energy=float(high),
        dynamic_range_db=dynamic_range,
        transient_density=transient_density,
        onset_strength=onset_strength / np.max(onset_env) if np.max(onset_env) > 0 else 0.0,
        is_clipping=is_clipping,
        is_silent=is_silent,
        bpm_accuracy=bpm_accuracy,
        raw_waveform=y,
        sample_rate=sr
    )

def _mock_analysis(self, requested_bpm: int) -> AudioAnalysisResult:
    """Mock analysis when librosa unavailable."""
    logger.warning("Using mock analysis (librosa not available)")
    return AudioAnalysisResult(
        actual_bpm=float(requested_bpm),
        actual_energy=0.7,
        duration_seconds=120.0,
        spectral_centroid=2000.0,
        spectral_rolloff=8000.0,
        spectral_bandwidth=3000.0,
        subbass_energy=0.3,
        bass_energy=0.4,
        mid_energy=0.2,
        high_energy=0.1,
        dynamic_range_db=10.0,
        transient_density=5.0,
        onset_strength=0.7,
        is_clipping=False,
        is_silent=False,
        bpm_accuracy=1.0,
        raw_waveform=None,
        sample_rate=44100
    )


class MicrophoneVoiceAdapter(VoiceProcessingPort):
async def record_voice_profile(self, duration_s: float, sample_rate: int = 44100) -> bytes:
    try:
        import sounddevice as sd
        recording = sd.rec(int(duration_s * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
        sd.wait()
        return recording.tobytes()
    except:
        return b""

async def process_speech_input(self, audio_data: bytes) -> str:
    return ""

async def get_available_microphones(self) -> List[Dict[str, Any]]:
    return []


# ============================================================================
# MIDI CONTROLLER (ENHANCED)
# ============================================================================

class MIDIControllerAdapter:
"""MIDI controller adapter with device enumeration"""

def __init__(self):
    try:
        import rtmidi
        self.midi_in = rtmidi.MidiIn()
        available_ports = self.midi_in.get_ports()
        self.available = len(available_ports) > 0

        if self.available:
            logger.info(f"MIDI: Found {len(available_ports)} device(s)")
    except ImportError:
        self.available = False
        logger.info("python-rtmidi not installed (MIDI disabled)")

def get_available_ports(self) -> List[str]:
    if not self.available:
        return []
    return self.midi_in.get_ports()

async def listen_for_input(self, port_index: int = 0):
    if not self.available:
        return

    try:
        self.midi_in.open_port(port_index)
        logger.info(f"Listening on MIDI port {port_index}")
    except Exception as e:
        logger.error(f"MIDI listen failed: {e}")


# ============================================================================
# ORCHESTRATOR & GUARDRAILS (ENHANCED)
# ============================================================================

class SunoGuardrails:
"""Budget and cost guardrails with configurable limits"""

def __init__(self, daily_limit_eur: float = 10.0):
    self.daily_spend = 0.0
    self.daily_limit_eur = daily_limit_eur  # Now configurable!
    self.generation_history = []
    self.session_spend = 0.0
    self.session_start_time = None

def get_budget_status(self) -> Dict[str, float]:
    return {
        "daily_spend_eur": self.daily_spend,
        "daily_limit_eur": self.daily_limit_eur,
        "remaining_eur": self.daily_limit_eur - self.daily_spend,
        "utilization_pct": (self.daily_spend / self.daily_limit_eur) * 100 if self.daily_limit_eur > 0 else 0
    }

def record_generation(self, tokens_used: int) -> float:
    cost = tokens_used * 0.05
    self.daily_spend += cost
    self.generation_history.append({
        "timestamp": time.time(),
        "tokens": tokens_used,
        "cost_eur": cost
    })
    return cost


class PerformanceHooks:
"""Performance tracking hooks"""

def __init__(self):
    self.metrics_history = []

def get_session_summary(self) -> Dict[str, Any]:
    if not self.metrics_history:
        return {
            "total_generations": 0,
            "successful": 0,
            "failed": 0,
            "success_rate": 0.0
        }

    successful = [m for m in self.metrics_history if m.get("success", False)]
    return {
        "total_generations": len(self.metrics_history),
        "successful": len(successful),
        "failed": len(self.metrics_history) - len(successful),
        "success_rate": len(successful) / len(self.metrics_history) if self.metrics_history else 0.0
    }


# ==============================================================================
# 🎯 PHASE 2: FULL DEEPSEEK ORCHESTRATOR IMPLEMENTATION (externals.py)
# ==============================================================================
# Production-ready agentic orchestration with:
# - Reflection loop for prompt optimization
# - Semantic quality evaluation
# - Cost-efficiency analysis
# - Intelligent retry strategies
# - Comprehensive hooks for metrics tracking




class PerformanceOrchestratorAgent:
"""🤖 Intelligent agentic orchestration for pro-level music generation.

Uses DeepSeek V3 for:
- Reflection loop: Iteratively optimize prompts before generation
- Semantic evaluation: Analyze track quality beyond BPM matching
- Cost optimization: Balance quality vs. budget constraints
- Adaptive learning: Learn from failures and improve over time

Architecture follows OpenAI agent patterns with reflection and tool use.
"""

def __init__(self):
    self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
    self.available = bool(self.deepseek_api_key)
    self.base_url = "https://api.deepseek.com/v1"
    self.model = "deepseek-chat"  # DeepSeek V3
    self.guardrails = SunoGuardrails()
    self.hooks = PerformanceHooks()

    # Reflection parameters
    self.reflection_enabled = True
    self.max_reflection_iterations = 1
    self.quality_threshold = 0.75

    # Cost tracking
    self.total_cost_eur = 0.0
    self.total_tokens = 0

    # Performance cache for learned patterns
    self.prompt_optimization_cache = {}

    if self.available:
        logger.success(f"🤖 Orchestrator: DeepSeek V3 ready (reflection enabled)")
    else:
        logger.warning(f"⚠️  Orchestrator: No DeepSeek API (set DEEPSEEK_API_KEY)")

async def optimize_prompt_for_cometapi(
        self,
        original_prompt: str,
        generation_mode: str,  # "generation" or "artist_consistency"
        artist_profile: ArtistProfile,
        request: GenerationRequest
) -> Tuple[str, Dict[str, Any]]:
    """
    🎛️ Optimize any prompt to fit CometAPI payload structure.

    DeepSeek analyzes prompt and returns optimized version that:
    1. ✅ Fits CometAPI JSON payload
    2. ✅ Includes proper [Verse], [Chorus] tags if lyrics
    3. ✅ Has clear style/mood/technical parameters
    4. ✅ Maintains artist identity & user input
    5. ✅ Is Suno-v5 compatible

    Args:
        original_prompt: Raw prompt (may contain user lyrics)
        generation_mode: "generation" or "artist_consistency"
        artist_profile: Artist profile for context
        request: Generation request details

    Returns:
        Tuple of (optimized_prompt, metadata)
    """

    if not self.available:
        logger.warning("⚠️ DeepSeek not available, returning prompt unchanged")
        return original_prompt, {
            "optimized": False,
            "reason": "API not available",
            "summary": "No optimization applied"
        }

    # Build system prompt for CometAPI optimization
    system_prompt = """You are an expert Suno AI prompt engineer specializing in CometAPI v5.

Your task: Optimize music generation prompts to maximize compatibility and quality.

COMETAPI PAYLOAD STRUCTURE you must fit:
{
    "prompt": "[Verse]\\nLyrics...\\n[Chorus]\\nLyrics...",  ← Must have structure
    "generation_type": "TEXT" or "AUDIO",
    "tags": "genre1, genre2, mood",  ← Comma-separated, specific
    "mv": "chirp-v4-tau",
    "title": "Track Name",
    "task": "generation" or "artist_consistency"
}

RULES:
1. If prompt contains lyrics, keep them structured with [Verse], [Chorus], [Bridge] tags
2. Extract technical parameters (BPM, energy, instruments) into description
3. Create "tags" field: genre, mood, instruments (comma-separated, max 5 tags)
4. Ensure prompt is vivid but concise
5. Maintain artist identity and user intent
6. Output ONLY the optimized prompt, no explanations

RESPONSE FORMAT:
```json
{
    "optimized_prompt": "The full optimized prompt here",
    "tags": "genre, mood, instruments",
    "generation_type": "TEXT",
    "summary": "What was changed"
}
```"""

    user_prompt = f"""OPTIMIZE THIS PROMPT FOR COMETAPI:

**Original Prompt:**
{original_prompt}

**Context:**
- Artist: {artist_profile.name}
- Mode: {generation_mode}
- BPM: {request.bpm}
- Energy: {request.energy:.1f}
- Style: {request.style.display_name}
- Venue: {request.venue_type.display_name}

Return optimized version in JSON format."""

    try:
        response = await self._call_deepseek(system_prompt, user_prompt)

        # Parse JSON response
        result = json.loads(response)

        optimized = result.get("optimized_prompt", original_prompt)
        tags = result.get("tags", "electronic")
        gen_type = result.get("generation_type", "AUDIO")
        summary = result.get("summary", "Optimized for CometAPI")

        logger.success(f"✅ DeepSeek optimized prompt: {summary}")

        return optimized, {
            "optimized": True,
            "tags": tags,
            "generation_type": gen_type,
            "summary": summary,
            "original_length": len(original_prompt),
            "optimized_length": len(optimized)
        }

    except json.JSONDecodeError:
        logger.error("❌ DeepSeek returned invalid JSON")
        return original_prompt, {
            "optimized": False,
            "reason": "JSON parse error",
            "summary": "Failed to parse DeepSeek response"
        }

    except Exception as e:
        logger.error(f"❌ DeepSeek optimization failed: {e}")
        return original_prompt, {
            "optimized": False,
            "reason": str(e),
            "summary": "Optimization failed"
        }

async def optimize_generation_request(
        self,
        base_request: GenerationRequest,
        crowd_energy: float,
        performance_state: PerformanceState,
        artist_profile: ArtistProfile,
        max_reflection_iterations: int = 3
) -> Tuple[GenerationRequest, Dict[str, Any]]:
    """🔄 Optimize generation request using reflection loop with DeepSeek.

    Reflection Loop Pattern (from agent best practices):
    1. Generate initial prompt from artist profile + request
    2. DeepSeek reflects: "How can this prompt be improved for Suno?"
    3. DeepSeek optimizes: Rewrites prompt with improvements
    4. Evaluate quality score for optimized prompt
    5. Repeat until quality threshold met or max iterations reached

    Args:
        base_request: Initial generation parameters
        crowd_energy: Current crowd energy (0.0-1.0)
        performance_state: Performance state with history
        artist_profile: Artist profile with semantic fields
        max_reflection_iterations: Max reflection cycles

    Returns:
        Tuple of (optimized_request, reflection_metadata)
    """

    if not self.available:
        # Graceful degradation: return unchanged request
        return base_request, {
            "reflection_iterations": 0,
            "final_quality_score": 0.70,
            "optimized": False,
            "stub_mode": True,
            "reason": "DeepSeek API not available"
        }

    # Build initial prompt from artist identity
    initial_prompt = self._build_semantic_prompt(
        artist_profile,
        base_request,
        crowd_energy
    )

    logger.info(f"🎯 Starting reflection loop (max {max_reflection_iterations} iterations)")
    logger.debug(f"📝 Initial prompt: {initial_prompt[:100]}...")

    current_prompt = initial_prompt
    reflection_history = []

    for iteration in range(max_reflection_iterations):
        logger.info(f"🔄 Reflection iteration {iteration + 1}/{max_reflection_iterations}")

        # Step 1: Reflect on current prompt
        reflection = await self._reflect_on_prompt(
            current_prompt,
            base_request,
            artist_profile,
            performance_state
        )

        reflection_history.append({
            "iteration": iteration + 1,
            "original_prompt": current_prompt,
            "reflection": reflection["critique"],
            "improvements": reflection["improvements"],
            "quality_estimate": reflection["quality_score"]
        })

        logger.debug(f"💭 Reflection: {reflection['critique'][:80]}...")

        # Step 2: Check if quality threshold met
        if reflection["quality_score"] >= self.quality_threshold:
            logger.success(
                f"✅ Quality threshold met: {reflection['quality_score']:.2f} "
                f">= {self.quality_threshold:.2f}"
            )
            break

        # Step 3: Optimize prompt based on reflection
        optimized_prompt = await self._optimize_prompt(
            current_prompt,
            reflection,
            artist_profile,
            base_request
        )

        logger.info(f"✨ Optimized prompt: {optimized_prompt[:100]}...")
        current_prompt = optimized_prompt

    # Create optimized request with final prompt
    optimized_request = GenerationRequest(
        style=base_request.style,
        bpm=base_request.bpm,
        energy=base_request.energy,
        crowd_energy=crowd_energy,
        theme=base_request.theme,
        duration_seconds=base_request.duration_seconds,
        venue_type=base_request.venue_type,
        custom_prompt=current_prompt,  # Inject optimized prompt
        allow_reflection=False  # Already reflected
    )

    final_quality = reflection_history[-1]["quality_estimate"] if reflection_history else 0.75

    metadata = {
        "reflection_iterations": len(reflection_history),
        "final_quality_score": final_quality,
        "optimized": True,
        "changes_made": [h["improvements"] for h in reflection_history],
        "initial_prompt": initial_prompt,
        "final_prompt": current_prompt,
        "reflection_history": reflection_history,
        "stub_mode": False
    }

    logger.success(
        f"🎯 Reflection complete: {len(reflection_history)} iterations, "
        f"quality={final_quality:.2f}"
    )

    return optimized_request, metadata

def _build_semantic_prompt(
        self,
        profile: ArtistProfile,
        request: GenerationRequest,
        crowd_energy: float
) -> str:
    """Build rich semantic prompt from artist identity fields."""

    parts = []

    # Style foundation
    if profile.has_custom_style():
        parts.append(profile.custom_style_description)
    else:
        parts.append(request.style.display_name)

    # Influences (inspiration)
    if profile.influences:
        influences_str = " and ".join(profile.influences[:2])
        parts.append(f"inspired by {influences_str}")

    # Instruments/sounds
    if profile.instruments:
        instruments_str = ", ".join(profile.instruments[:5])
        parts.append(f"featuring {instruments_str}")

    # Vibe/mood
    if profile.vibe_description:
        parts.append(f"with a vibe of {profile.vibe_description}")

    # Darkness/complexity (semantic dimensions)
    mood = profile.get_mood_description()
    parts.append(mood)

    # Signature sound
    if profile.signature_sound:
        parts.append(f"signature {profile.signature_sound}")

    # Technical parameters
    parts.append(f"{request.bpm} BPM")

    # Energy level
    if request.energy > 0.7:
        parts.append("high energy")
    elif request.energy < 0.4:
        parts.append("low energy")

    # Crowd adaptation
    if crowd_energy > 0.8:
        parts.append("explosive crowd energy")
    elif crowd_energy < 0.3:
        parts.append("intimate atmosphere")

    # Theme
    if request.theme:
        parts.append(f"theme: {request.theme}")

    return ", ".join(parts)

async def _reflect_on_prompt(
        self,
        prompt: str,
        request: GenerationRequest,
        profile: ArtistProfile,
        state: PerformanceState
) -> Dict[str, Any]:
    """🤔 Use DeepSeek to reflect on prompt quality and suggest improvements.

    Reflection prompt pattern: Ask LLM to critique and improve.
    """

    system_prompt = """You are an expert music producer and prompt engineer for Suno AI v5.

Your job is to analyze music generation prompts and provide constructive critique with specific improvements.

For each prompt, evaluate:
1. **Clarity**: Is the style, mood, and technical direction clear?
2. **Specificity**: Does it paint a vivid sonic picture, or is it too generic?
3. **Suno Compatibility**: Will Suno v5 understand and execute this well?
4. **Emotional Impact**: Does it evoke the intended atmosphere?
5. **Technical Precision**: Are BPM, energy, instruments well-specified?

Provide:
- Quality score (0.0-1.0)
- Constructive critique (what's working, what's not)
- Specific improvements (concrete changes to make)

Be brutally honest but constructive."""

    # Build context about performance
    context_parts = [
        f"Event: {state.event_name} at {state.venue_type.display_name}",
        f"Artist: {profile.name}",
        f"Tracks generated so far: {len(state.generated_tracks)}",
        f"Current energy: {state.current_energy:.2f}",
    ]

    if state.generated_tracks:
        avg_quality = sum(t.quality_score for t in state.generated_tracks) / len(state.generated_tracks)
        context_parts.append(f"Average quality so far: {avg_quality:.2f}")

    context = "\n".join(context_parts)

    user_prompt = f"""**Performance Context:**
{context}

**Current Prompt:**
"{prompt}"

**Target:**
- Style: {request.style.display_name}
- BPM: {request.bpm}
- Energy: {request.energy:.2f}
- Venue: {request.venue_type.display_name}

Analyze this prompt and provide your reflection in JSON format:
{{
"quality_score": <float 0.0-1.0>,
"critique": "<honest assessment>",
"improvements": ["<specific improvement 1>", "<specific improvement 2>", ...]
}}"""

    try:
        response = await self._call_deepseek(system_prompt, user_prompt)
        reflection = json.loads(response)

        return {
            "quality_score": reflection.get("quality_score", 0.70),
            "critique": reflection.get("critique", "No critique provided"),
            "improvements": reflection.get("improvements", [])
        }

    except Exception as e:
        logger.error(f"Reflection failed: {e}")
        # Fallback reflection
        return {
            "quality_score": 0.70,
            "critique": "Reflection failed, using prompt as-is",
            "improvements": []
        }

async def _optimize_prompt(
        self,
        original_prompt: str,
        reflection: Dict[str, Any],
        profile: ArtistProfile,
        request: GenerationRequest
) -> str:
    """✨ Use DeepSeek to rewrite prompt based on reflection insights."""

    system_prompt = """You are an expert Suno AI prompt engineer.

Rewrite music generation prompts to maximize quality based on reflection insights.

Rules:
- Keep all essential technical details (BPM, style, instruments)
- Enhance emotional and atmospheric descriptions
- Make it vivid, specific, and Suno-friendly
- Stay true to the artist's identity
- Output ONLY the rewritten prompt, no explanations"""

    improvements_str = "\n".join(f"- {imp}" for imp in reflection["improvements"])

    user_prompt = f"""**Original Prompt:**
"{original_prompt}"

**Critique:**
{reflection['critique']}

**Suggested Improvements:**
{improvements_str}

**Artist Identity:**
- Darkness level: {profile.darkness_level:.1f} (0=bright, 1=dark)
- Complexity: {profile.complexity_level:.1f} (0=minimal, 1=complex)
- Signature: {profile.signature_sound or 'None'}

Rewrite this prompt incorporating the improvements while preserving the artist's identity:"""

    try:
        optimized = await self._call_deepseek(system_prompt, user_prompt)
        return optimized.strip()

    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return original_prompt

async def evaluate_track_quality(
        self,
        track: LiveTrack,
        expected_request: GenerationRequest
) -> Dict[str, Any]:
    """🎯 Semantic quality evaluation using DeepSeek + rule-based metrics.

    Combines:
    - Rule-based: BPM accuracy, duration, energy
    - LLM-based: Style authenticity, vibe match, production quality
    """

    # === RULE-BASED METRICS ===
    bpm_diff = abs(track.bpm - expected_request.bpm)
    bpm_accuracy = max(0.0, 1.0 - (bpm_diff / 20.0))

    duration_match = 1.0 if track.duration_seconds >= 50 else 0.8

    # === LLM SEMANTIC EVALUATION ===
    if self.available and expected_request.has_custom_prompt():
        semantic_eval = await self._semantic_evaluation(track, expected_request)
    else:
        # Fallback to reasonable defaults
        semantic_eval = {
            "style_authenticity": 0.80,
            "energy_match": 0.85,
            "production_quality": 0.75,
            "vibe_alignment": 0.80
        }

    # === WEIGHTED OVERALL SCORE ===
    overall = (
            bpm_accuracy * 0.20 +
            semantic_eval["style_authenticity"] * 0.30 +
            semantic_eval["energy_match"] * 0.20 +
            semantic_eval["production_quality"] * 0.15 +
            semantic_eval["vibe_alignment"] * 0.10 +
            duration_match * 0.05
    )

    evaluation = {
        "overall_score": round(overall, 2),
        "bpm_accuracy": round(bpm_accuracy, 2),
        "duration_match": round(duration_match, 2),
        **semantic_eval,
        "pass_threshold": overall >= 0.70,
        "issues": []
    }

    # Identify specific issues
    if bpm_accuracy < 0.7:
        evaluation["issues"].append(
            f"BPM mismatch: {track.bpm} vs {expected_request.bpm} (±{bpm_diff})"
        )

    if track.duration_seconds < 50:
        evaluation["issues"].append(f"Track too short: {track.duration_seconds}s")

    if semantic_eval["style_authenticity"] < 0.6:
        evaluation["issues"].append("Style authenticity below expectations")

    logger.info(
        f"📊 Quality: {overall:.2f} "
        f"({'✅ PASS' if evaluation['pass_threshold'] else '❌ FAIL'})"
    )

    if evaluation["issues"]:
        logger.warning(f"⚠️  Issues: {', '.join(evaluation['issues'])}")

    return evaluation

async def _semantic_evaluation(
        self,
        track: LiveTrack,
        expected_request: GenerationRequest
) -> Dict[str, float]:
    """🧠 Use DeepSeek to semantically evaluate track quality."""

    system_prompt = """You are a professional music critic specializing in underground electronic music.

Evaluate generated tracks on these dimensions (score each 0.0-1.0):
1. **style_authenticity**: Does it truly capture the requested style?
2. **energy_match**: Does the energy level match expectations?
3. **production_quality**: Is the mix, sound design, and production professional?
4. **vibe_alignment**: Does the overall vibe match the prompt?

Be critical but fair. Output JSON only."""

    user_prompt = f"""**Expected Prompt:**
"{expected_request.custom_prompt}"

**Generated Track:**
- Name: {track.name}
- Style: {track.style.display_name}
- BPM: {track.bpm}
- Duration: {track.duration_seconds}s
- Energy: {track.energy:.2f}

**Metadata:**
{json.dumps(track.metadata, indent=2) if track.metadata else "No metadata"}

Evaluate this track in JSON:
{{
"style_authenticity": <float>,
"energy_match": <float>,
"production_quality": <float>,
"vibe_alignment": <float>,
"reasoning": "<brief explanation>"
}}"""

    try:
        response = await self._call_deepseek(system_prompt, user_prompt)
        eval_data = json.loads(response)

        return {
            "style_authenticity": eval_data.get("style_authenticity", 0.80),
            "energy_match": eval_data.get("energy_match", 0.85),
            "production_quality": eval_data.get("production_quality", 0.75),
            "vibe_alignment": eval_data.get("vibe_alignment", 0.80)
        }

    except Exception as e:
        logger.warning(f"Semantic evaluation failed: {e}")
        return {
            "style_authenticity": 0.75,
            "energy_match": 0.80,
            "production_quality": 0.75,
            "vibe_alignment": 0.75
        }

async def analyze_cost_efficiency(
        self,
        state: PerformanceState
) -> Dict[str, Any]:
    """💰 ROI analysis: Quality per euro spent."""

    total_cost_eur = state.total_cost_eur if hasattr(state, 'total_cost_eur') else 0.0
    tracks_generated = len(state.generated_tracks)
    tracks_played = len(state.played_tracks)

    cost_per_track = total_cost_eur / tracks_generated if tracks_generated > 0 else 0.0
    utilization_rate = tracks_played / tracks_generated if tracks_generated > 0 else 0.0

    # Average quality
    quality_scores = [
        t.quality_score for t in state.generated_tracks
        if hasattr(t, 'quality_score') and t.quality_score is not None
    ]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.75

    # Cost efficiency: quality per EUR
    cost_efficiency = avg_quality / (cost_per_track + 0.01) if cost_per_track > 0 else 0.0

    # Wasted spend
    wasted_tracks = tracks_generated - tracks_played
    wasted_cost = wasted_tracks * cost_per_track

    # Reflection cost
    reflection_cost = self.total_cost_eur

    metrics = {
        "total_cost_eur": round(total_cost_eur + reflection_cost, 2),
        "generation_cost_eur": round(total_cost_eur, 2),
        "reflection_cost_eur": round(reflection_cost, 2),
        "cost_per_track": round(cost_per_track, 2),
        "avg_quality_score": round(avg_quality, 2),
        "cost_efficiency": round(cost_efficiency, 2),
        "utilization_rate": round(utilization_rate, 2),
        "wasted_cost_eur": round(wasted_cost, 2),
        "tracks_generated": tracks_generated,
        "tracks_played": tracks_played,
        "reflection_enabled": self.available
    }

    logger.info(
        f"💰 ROI: €{metrics['total_cost_eur']:.2f} total, "
        f"efficiency={cost_efficiency:.2f}, "
        f"utilization={utilization_rate:.0%}"
    )

    return metrics

async def _call_deepseek(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
) -> str:
    """Call DeepSeek API with retries and error handling."""

    headers = {
        "Authorization": f"Bearer {self.deepseek_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": self.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": 1000
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(3):
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # ✅ NEW: Validate content is not empty
                if not content or not content.strip():
                    logger.warning(f"Empty response from DeepSeek (attempt {attempt + 1}/3)")
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    raise ValueError("DeepSeek returned empty content after 3 attempts")

                # ✅ NEW: Strip markdown code blocks if present
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]  # Remove ```
                if content.startswith("```"):
                    content = content[3:]  # Remove ```
                if content.endswith("```"):
                    content = content[:-3]  # Remove trailing ```
                content = content.strip()

                # ✅ NEW: Validate JSON structure if caller expects JSON
                if "JSON" in system_prompt or "json" in user_prompt:
                    try:
                        json.loads(content)  # Validate it's parseable
                    except json.JSONDecodeError as json_err:
                        logger.warning(f"Response not valid JSON: {content[:200]}")
                        if attempt < 2:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        raise ValueError(f"DeepSeek returned non-JSON: {json_err}")

                # Track usage
                usage = data.get("usage", {})
                tokens = usage.get("total_tokens", 0)
                self.total_tokens += tokens
                self.total_cost_eur += tokens * 0.00001

                logger.debug(f"✅ DeepSeek API call: {tokens} tokens")

                return content

            except httpx.HTTPStatusError as e:
                logger.error(f"DeepSeek API error (attempt {attempt + 1}/3): {e}")
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                logger.error(f"DeepSeek API failed: {e}")
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)

    raise RuntimeError("DeepSeek API call failed after retries")

def get_service_info(self) -> Dict[str, Any]:
    """Analyze REAL class state, not mock data"""
    import time

    # Real uptime calculation
    uptime = 0
    if hasattr(self, 'session_start_time') and self.session_start_time:
        uptime = time.time() - self.session_start_time

    # Real status based on actual configuration
    api_configured = bool(getattr(self, 'api_key', None))
    reflection_on = getattr(self, 'reflection_enabled', False)
    status = 'ready' if api_configured else 'not_configured'

    # Return REAL metrics from class attributes
    return {
        'service_name': 'DeepSeek V3',
        'model': getattr(self, 'model', 'unknown'),  # ← Real
        'status': status,  # ← Real
        'api_key_configured': api_configured,  # ← Real
        'reflection_enabled': reflection_on,  # ← Real
        'max_reflection_iterations': getattr(self, 'max_reflection_iterations', 0),

        'session_metrics': {
            'uptime_seconds': round(uptime, 2),  # ← Real
            'total_tokens_used': getattr(self, 'total_tokens', 0),  # ← Real
            'budget_eur': getattr(self, 'budget', 0.0),  # ← Real
            'failed_requests': getattr(self, 'failed_requests', 0),  # ← Real
        },

        'features': {
            'semantic_evaluation': hasattr(self, 'semantic_evaluation'),
            'cost_efficiency_analysis': hasattr(self, 'analyze_cost_efficiency'),
            'reflection_optimization': hasattr(self, 'optimize_generation_request'),
            'session_management': hasattr(self, 'get_session_summary'),
        }
    }

async def generate_next_track(
        self,
        crowd_energy: float,
        style_prompt: str = None,
        voice_prompt: str = None,
        performance_state: PerformanceState = None,
        artist_profile: ArtistProfile = None,
        generation_request: GenerationRequest = None
) -> LiveTrack:
    """Generate track with optional reflection optimization"""

    # Step 1: Build GenerationRequest from prompts
    if generation_request is None:
        request = self._build_generation_request_from_prompts(
            style_prompt=style_prompt,
            voice_prompt=voice_prompt,
            crowd_energy=crowd_energy,
            artist_profile=artist_profile
        )
    else:
        request = generation_request

    # Step 2: Optional - Optimize via reflection loop (agentic)
    if self.reflection_enabled and performance_state and artist_profile:
        optimized_request, meta = await self.optimize_generation_request(
            base_request=request,
            crowd_energy=crowd_energy,
            performance_state=performance_state,
            artist_profile=artist_profile
        )
        request = optimized_request

    # Step 3: Generate track
    track = await self.suno_adapter.generate_track(request)

    # Step 4: Evaluate quality semantically
    if self.available:
        evaluation = await self.evaluate_track_quality(track, request)
        track.quality_score = evaluation["overall_score"]

    return track

def _build_generation_request_from_prompts(
        self,
        style_prompt: str = None,
        voice_audio_path: str = None,
        crowd_energy: float = 0.5,
        artist_profile: ArtistProfile = None
) -> GenerationRequest:
    """Analyze voice with librosa, build prompt"""

    logger.info("🎨 Building generation request...")

    # Analyze voice with librosa
    voice_analysis = None
    if voice_audio_path:
        logger.info(f"🎤 Analyzing: {voice_audio_path}")

        try:
            y, sr = librosa.load(voice_audio_path, sr=None)

            # Extract features
            energy = np.mean(librosa.feature.melspectrogram(y=y, sr=sr))
            zero_crossing = np.mean(librosa.feature.zero_crossing_rate(y)[0])
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

            voice_analysis = {
                "energy": energy,
                "brightness": spectral_centroid / sr,
                "aggression": zero_crossing
            }

            logger.success(f"✓ Analyzed: energy={energy:.2f}, brightness={spectral_centroid / sr:.2f}")

        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")

    # Build prompt parts
    prompt_parts = []

    if style_prompt:
        prompt_parts.append(style_prompt)

    if voice_analysis:
        if voice_analysis["energy"] > 0.7:
            prompt_parts.append("high intensity, powerful expression")
        elif voice_analysis["energy"] < 0.3:
            prompt_parts.append("intimate, subtle dynamics")

        if voice_analysis["brightness"] > 0.7:
            prompt_parts.append("bright, piercing tones")
        else:
            prompt_parts.append("dark, deep tones")

        if voice_analysis["aggression"] > 0.5:
            prompt_parts.append("aggressive articulation")

    custom_prompt = ", ".join(prompt_parts) if prompt_parts else "underground warehouse techno"

    logger.debug(f"📋 Prompt: {custom_prompt[:80]}...")

    # Build request
    request = GenerationRequest(
        style=artist_profile.styles[0] if artist_profile and artist_profile.styles else UndergroundStyle.RAW_TECHNO,
        bpm=130,
        energy=voice_analysis["energy"] if voice_analysis else 0.7,
        crowd_energy=crowd_energy,
        theme="underground warehouse",
        duration_seconds=240,
        venue_type=VenueType.WAREHOUSE,
        custom_prompt=custom_prompt,
        voice_profile=artist_profile.voice_profiles[
            0] if artist_profile and artist_profile.voice_profiles else None,
        allow_reflection=True
    )

    logger.success("✅ Request built")
    return request





# ==============================================================================
# 📊 PERFORMANCE HOOKS - Comprehensive Metrics Tracking
# ==============================================================================

class PerformanceHooks:
"""Performance event hooks for comprehensive metrics tracking."""

def __init__(self):
    self.metrics_history: List[Dict[str, Any]] = []

async def on_generation_start(self, request: GenerationRequest):
    """🎬 Hook: Track generation starts."""
    logger.debug(f"🎬 Generation: {request.style.display_name} @ {request.bpm} BPM")

    self.metrics_history.append({
        "timestamp": time.time(),
        "event": "generation_start",
        "style": request.style.value,
        "bpm": request.bpm,
        "energy": request.energy,
        "has_custom_prompt": request.has_custom_prompt()
    })

async def on_generation_complete(
        self,
        track: LiveTrack,
        quality_score: float,
        cost_eur: float
):
    """✅ Hook: Track generation succeeds."""

    # FIX: Handle None track
    if track is None:
        logger.warning("⚠️ Track is None in on_generation_complete, skipping")
        return

    # Safe attribute access
    track_name = getattr(track, 'name', None) or 'Unnamed Track'
    gen_time = getattr(track, 'generation_time', 0) or 0

    logger.success(
        f"✅ Complete: {track_name} "
        f"(Q={quality_score:.2f}, €{cost_eur:.3f}, {gen_time:.1f}s)"
    )

    self.metrics_history.append({
        "timestamp": time.time(),
        "event": "generation_complete",
        "track_name": track_name,
        "quality_score": quality_score,
        "cost_eur": cost_eur,
        "generation_time": gen_time,
        "success": True
    })

async def on_generation_failed(
        self,
        error: Exception,
        request: GenerationRequest
):
    """❌ Hook: Track generation fails."""
    logger.error(f"❌ Generation failed: {str(error)}")

    self.metrics_history.append({
        "timestamp": time.time(),
        "event": "generation_failed",
        "error": str(error),
        "error_type": type(error).__name__,
        "style": request.style.value,
        "bpm": request.bpm,
        "success": False
    })

async def on_quality_rejection(
        self,
        track: LiveTrack,
        score: float,
        threshold: float
):
    """⚠️  Hook: Track rejected for low quality."""
    logger.warning(
        f"⚠️  Quality rejection: {track.name} "
        f"({score:.2f} < {threshold:.2f}, gap: {threshold - score:.2f})"
    )

    self.metrics_history.append({
        "timestamp": time.time(),
        "event": "quality_rejection",
        "track_name": track.name,
        "quality_score": score,
        "threshold": threshold,
        "gap": threshold - score,
        "success": False
    })

def get_session_summary(self) -> Dict[str, Any]:
    """📈 Session statistics."""
    if not self.metrics_history:
        return {
            "total_events": 0,
            "successful": 0,
            "failed": 0,
            "success_rate": 0.0
        }

    successful = [m for m in self.metrics_history if m.get("success", False)]
    failed = [m for m in self.metrics_history if m.get("event") in ["generation_failed", "quality_rejection"]]

    return {
        "total_events": len(self.metrics_history),
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / (len(successful) + len(failed)) if (len(successful) + len(
            failed)) > 0 else 0.0,
        "avg_quality": sum(m.get("quality_score", 0) for m in successful) / len(successful) if successful else 0.0,
        "total_cost_eur": sum(m.get("cost_eur", 0) for m in successful)
    }


# ==============================================================================
# 💸 SUNO GUARDRAILS - Budget Management
# ==============================================================================

class SunoGuardrails:
"""Budget and cost guardrails with configurable limits."""

def __init__(self, daily_limit_eur: float = 10.0):
    self.daily_spend = 0.0
    self.daily_limit_eur = daily_limit_eur
    self.generation_history = []
    self.session_spend = 0.0
    self.session_start_time = None

def get_budget_status(self) -> Dict[str, float]:
    return {
        "daily_spend_eur": self.daily_spend,
        "daily_limit_eur": self.daily_limit_eur,
        "remaining_eur": max(0, self.daily_limit_eur - self.daily_spend),
        "session_spend_eur": self.session_spend
    }

def can_generate(self, estimated_cost_eur: float) -> bool:
    return (self.daily_spend + estimated_cost_eur) <= self.daily_limit_eur

def record_generation(self, cost_eur: float):
    self.daily_spend += cost_eur
    self.session_spend += cost_eur
    self.generation_history.append({
        "timestamp": time.time(),
        "cost_eur": cost_eur
    })


# ============================================================================
# PERFORMANCE COMMAND ENUM
# ============================================================================

class PerformanceCommand:
"""Performance commands"""
GENERATE_NEXT = "generate_next"
ADD_VOCALS = "add_vocals"
ADJUST_ENERGY = "adjust_energy"
ADJUST_BPM = "adjust_bpm"
CHANGE_STYLE = "change_style"
BLEND_REFERENCE = "blend_reference"
CROWD_SYNC = "crowd_sync"
COLLABORATOR_INPUT = "collaborator_input"
PAUSE = "pause"
END = "end"



def load_last_checkpoint(self, profile_name: str) -> Optional[PerformanceCheckpoint]:
"""Load last checkpoint for this profile"""
try:
    checkpoint_dir = Path("data/checkpoints")
    checkpoints = list(checkpoint_dir.glob(f"{profile_name}_*.json"))

    if not checkpoints:
        return None

    latest = max(checkpoints, key=os.path.getmtime)

    with open(latest, 'r') as f:
        data = json.load(f)

    checkpoint = PerformanceCheckpoint(
        phase=data['phase'],
        timestamp=data['timestamp'],
        profile_name=data['profile_name'],
        venue_type=data['venue_type'],
        event_name=data.get('event_name', ''),
        duration_minutes=data.get('duration_minutes', 0),
        pre_generated_track_json=data.get('pre_generated_track_json'),
        buffer_tracks_json=data.get('buffer_tracks_json', []),
        played_tracks_json=data.get('played_tracks_json', []),
        total_cost_eur=data.get('total_cost_eur', 0.0),
        elapsed_seconds=data.get('elapsed_seconds', 0.0),
        current_energy=data.get('current_energy', 0.5)
    )

    logger.success(f"✅ Checkpoint recovered: {profile_name} Phase {checkpoint.phase}")
    return checkpoint

except Exception as e:
    logger.warning(f"Could not load checkpoint: {e}")
    return None


class LibrosaAudioMixer:
"""
Production DJ mixer adapter using librosa for beatmatching + crossfade.

Features:
- Tempo detection (librosa.beat.beat_track)
- Time-stretching (librosa.effects.time_stretch)
- Crossfade synthesis (linear/cosine envelope)
- BPM sync analysis
"""

def __init__(self, sr: int = 44100):
    """
    Initialize mixer.

    Args:
        sr: Sample rate for all audio (default 44.1kHz for DJ standard)
    """
    self.sr = sr
    self._cache = {}  # Cache BPM calculations

async def get_bpm(self, track_path: str) -> float:
    """Detect BPM of a track with caching."""
    if track_path in self._cache:
        return self._cache[track_path]

    try:
        # Load audio
        y, _ = librosa.load(track_path, sr=self.sr, mono=True)

        # Detect tempo
        tempo, _ = librosa.beat.beat_track(y=y, sr=self.sr)

        self._cache[track_path] = tempo
        logger.debug(f"🎛️ BPM detected: {track_path} @ {tempo:.1f} BPM")
        return tempo

    except Exception as e:
        logger.error(f"❌ BPM detection failed for {track_path}: {e}")
        return 0.0

async def analyze_sync_percentage(
        self,
        track_a_path: str,
        track_b_path: str
) -> float:
    """
    Analyze how well two tracks match in BPM.

    Returns:
        0.0 = completely mismatched
        100.0 = perfect BPM match
    """
    try:
        tempo_a = await self.get_bpm(track_a_path)
        tempo_b = await self.get_bpm(track_b_path)

        if tempo_a == 0 or tempo_b == 0:
            return 0.0

        # Calculate difference
        diff = abs(tempo_a - tempo_b)
        max_bpm = max(tempo_a, tempo_b)

        # Sync percentage: 100% if perfect, 0% if very different
        sync_pct = max(0, 100 - (diff / max_bpm * 100))

        logger.info(f"🎛️ Sync analysis: A={tempo_a:.1f} BPM, B={tempo_b:.1f} BPM → {sync_pct:.0f}% match")
        return sync_pct

    except Exception as e:
        logger.error(f"❌ Sync analysis failed: {e}")
        return 0.0

async def beatmatch_and_crossfade(
        self,
        track_a_path: str,
        track_b_path: str,
        fade_duration: float = 3.0
) -> bytes:
    """
    Full DJ transition: beatmatch + crossfade.

    Process:
    1. Load both tracks
    2. Detect BPMs
    3. Time-stretch B to match A
    4. Crossfade A→B with linear envelope
    5. Return mixed audio as WAV bytes
    """
    try:
        logger.info(f"🎛️ Starting beatmatch & crossfade: {fade_duration}s fade")
        start = time.time()

        # STEP 1: Load audio (runs in thread to avoid blocking)
        def _load():
            y_a, _ = librosa.load(track_a_path, sr=self.sr, mono=True)
            y_b, _ = librosa.load(track_b_path, sr=self.sr, mono=True)
            return y_a, y_b

        loop = asyncio.get_event_loop()
        y_a, y_b = await loop.run_in_executor(None, _load)
        logger.debug(f"✅ Loaded tracks: A={len(y_a) / self.sr:.1f}s, B={len(y_b) / self.sr:.1f}s")

        # STEP 2: Detect tempos
        def _detect_tempo():
            tempo_a, _ = librosa.beat.beat_track(y=y_a, sr=self.sr)
            tempo_b, _ = librosa.beat.beat_track(y=y_b, sr=self.sr)
            return tempo_a, tempo_b

        tempo_a, tempo_b = await loop.run_in_executor(None, _detect_tempo)
        logger.info(f"🎵 BPM detected: A={tempo_a:.1f}, B={tempo_b:.1f}")

        # STEP 3: Time-stretch B to match A
        if abs(tempo_a - tempo_b) > 1.0:  # Only stretch if diff > 1 BPM
            stretch_rate = tempo_a / tempo_b

            def _stretch():
                return librosa.effects.time_stretch(y_b, rate=stretch_rate)

            y_b = await loop.run_in_executor(None, _stretch)
            logger.info(f"🎛️ Time-stretched track B by {stretch_rate:.2f}x")
        else:
            logger.info(f"🎛️ BPMs close enough, no stretch needed")

        # STEP 4: Create crossfade
        nsamples = int(fade_duration * self.sr)

        # Ensure we have enough samples
        if nsamples > len(y_a) or nsamples > len(y_b):
            nsamples = min(len(y_a), len(y_b)) // 2
            logger.warning(f"⚠️ Fade duration too long, reducing to {nsamples / self.sr:.1f}s")

        # Linear crossfade envelope
        fade_in = np.linspace(0, 1, nsamples)
        fade_out = 1 - fade_in

        # Extract last part of A, first part of B
        seg_a = y_a[-nsamples:]
        seg_b = y_b[:nsamples]

        # Blend: fade out A, fade in B
        cross = (seg_a * fade_out) + (seg_b * fade_in)

        # Concatenate: A (before fade) + crossfade + B (after fade)
        y_mixed = np.concatenate([y_a[:-nsamples], cross, y_b[nsamples:]])

        # Normalize to prevent clipping
        max_val = np.max(np.abs(y_mixed))
        if max_val > 1.0:
            y_mixed = y_mixed / max_val
            logger.debug(f"🎛️ Normalized mixed track (peak was {max_val:.2f})")

        logger.debug(f"✅ Crossfade complete: {len(y_mixed) / self.sr:.1f}s total")

        # STEP 5: Convert to WAV bytes
        def _to_bytes():
            buffer = BytesIO()
            sf.write(buffer, y_mixed, self.sr, format='WAV')
            buffer.seek(0)
            return buffer.read()

        wav_bytes = await loop.run_in_executor(None, _to_bytes)

        elapsed = time.time() - start
        logger.success(f"🎛️ Beatmatch & crossfade complete in {elapsed:.1f}s ({len(wav_bytes) / 1024:.1f}KB)")

        return wav_bytes

    except FileNotFoundError as e:
        logger.error(f"❌ Audio file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Beatmatch & crossfade failed: {e}")
        raise RuntimeError(f"Mixer error: {e}")


# In externals.py - Add voice similarity checking (optional enhancement)

class LibrosaVoiceSimilarity:
"""
Free voice similarity checking using librosa + speaker embeddings.
Validates that uploaded voice sample matches profile.
"""

async def compute_voice_embedding(self, audio_path: str) -> np.ndarray:
    """
    Compute speaker embedding using librosa MFCCs.

    Uses MFCC (Mel-Frequency Cepstral Coefficients) as proxy for speaker embedding.
    Not as accurate as neural embeddings but FREE and FAST.
    """
    try:
        import librosa

        y, sr = librosa.load(audio_path, sr=16000)

        # Extract MFCC features
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

        # Average across time axis to get single vector per audio
        mfcc_mean = np.mean(mfcc, axis=1)

        return mfcc_mean

    except Exception as e:
        logger.error(f"Embedding computation failed: {e}")
        return np.array([])

async def compare_voice_samples(self,
                                voice_path_1: str,
                                voice_path_2: str) -> Dict[str, float]:
    """
    Compare two voice samples and return similarity score.

    Args:
        voice_path_1: Path to voice sample 1
        voice_path_2: Path to voice sample 2

    Returns:
        Dict with:
        - cosine_similarity: float (0.0-1.0)
        - euclidean_distance: float
        - recommendation: str
    """
    try:
        from scipy.spatial.distance import cosine, euclidean

        emb1 = await self.compute_voice_embedding(voice_path_1)
        emb2 = await self.compute_voice_embedding(voice_path_2)

        if len(emb1) == 0 or len(emb2) == 0:
            return {
                "cosine_similarity": 0.0,
                "euclidean_distance": float('inf'),
                "recommendation": "Could not compute embeddings"
            }

        # Normalize embeddings
        emb1_norm = emb1 / np.linalg.norm(emb1)
        emb2_norm = emb2 / np.linalg.norm(emb2)

        # Compute distances
        cosine_sim = 1 - cosine(emb1_norm, emb2_norm)
        euclidean_dist = euclidean(emb1_norm, emb2_norm)

        # Make recommendation
        if cosine_sim > 0.8:
            recommendation = "✅ Very similar voices"
        elif cosine_sim > 0.6:
            recommendation = "✓ Similar voices"
        elif cosine_sim > 0.4:
            recommendation = "⚠️ Somewhat different voices"
        else:
            recommendation = "❌ Voices are very different"

        return {
            "cosine_similarity": float(cosine_sim),
            "euclidean_distance": float(euclidean_dist),
            "recommendation": recommendation
        }

    except Exception as e:
        logger.error(f"Voice comparison failed: {e}")
        return {
            "cosine_similarity": 0.0,
            "euclidean_distance": float('inf'),
            "recommendation": f"Error: {e}"
        }
