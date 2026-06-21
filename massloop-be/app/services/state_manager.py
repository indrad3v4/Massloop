"""
Massloop.ai - Unified State Manager
Handles ALL application state persistence following Clean Architecture
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger
from dataclasses import asdict

class StateManager:
    """
    Unified state persistence for entire Massloop application.
    Saves:
    - Settings (audio, MIDI, budget)
    - Active profile
    - UI state (current screen, selections)
    - Session data (can resume interrupted performances)
    - Profiles (delegates to StoragePort)
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.config_dir = self.data_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # State files
        self.settings_file = self.config_dir / "settings.json"
        self.ui_state_file = self.config_dir / "ui_state.json"
        self.session_state_file = self.config_dir / "session_state.json"

        # Default state structure
        self.defaults = {
            "settings": {
                "audio": {
                    "output_device": None,
                    "input_device": None,
                    "sample_rate": 44100,
                    "buffer_size": 512,
                    "latency_mode": "low",
                },
                "midi": {
                    "enabled": False,
                    "input_device": None,
                    "channel": 1,
                },
                "performance": {
                    "buffer_tracks": 3,
                    "auto_generation": True,
                    "crowd_sensing_enabled": False,
                },
                "ai": {
                    "default_duration": 240,
                    "default_energy": 0.7,
                    "generation_quality": "high",
                    "quality_threshold": 0.75,
                    "max_retries": 3,
                },
                "budget": {
                    "budget_limit": 50.0,
                    "alert_at": 10.0,
                },
            },
            "ui_state": {
                "last_screen": "main_menu",
                "last_selected_option": 1,
                "active_profile_name": None,
                "window_size": [1920, 1080],
                "show_debug": False,
            },
            "session": {
                "active_performance": None,
                "last_profile": None,
                "last_venue": "club",
            }
        }

        # Load all state on init
        self.state = self._load_all_state()
        logger.info(f"StateManager initialized: {self.data_dir}")

    def _load_all_state(self) -> Dict[str, Any]:
        """Load all state from disk, merging with defaults"""
        state = {
            "settings": self.defaults["settings"].copy(),
            "ui_state": self.defaults["ui_state"].copy(),
            "session": self.defaults["session"].copy()
        }

        # Load settings
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                state["settings"] = self._merge_dicts(
                    self.defaults["settings"],
                    saved_settings
                )
                logger.success(f"Settings loaded: {self.settings_file}")
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")

        # Load UI state
        if self.ui_state_file.exists():
            try:
                with open(self.ui_state_file, 'r') as f:
                    saved_ui = json.load(f)
                state["ui_state"] = {**self.defaults["ui_state"], **saved_ui}
                logger.success(f"UI state loaded: {self.ui_state_file}")
            except Exception as e:
                logger.error(f"Failed to load UI state: {e}")

        # Load session state
        if self.session_state_file.exists():
            try:
                with open(self.session_state_file, 'r') as f:
                    saved_session = json.load(f)
                state["session"] = {**self.defaults["session"], **saved_session}
                logger.success(f"Session state loaded: {self.session_state_file}")
            except Exception as e:
                logger.error(f"Failed to load session: {e}")

        return state

    def save_all(self) -> bool:
        """Save all state to disk - CALL THIS ON EXIT"""
        success = True

        # Save settings
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.state["settings"], f, indent=2)
            logger.success("Settings saved")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            success = False

        # Save UI state
        try:
            with open(self.ui_state_file, 'w') as f:
                json.dump(self.state["ui_state"], f, indent=2)
            logger.success("UI state saved")
        except Exception as e:
            logger.error(f"Failed to save UI state: {e}")
            success = False

        # Save session state
        try:
            with open(self.session_state_file, 'w') as f:
                json.dump(self.state["session"], f, indent=2)
            logger.success("Session state saved")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            success = False

        return success

    def _merge_dicts(self, default: Dict, saved: Dict) -> Dict:
        """Recursively merge saved with defaults"""
        result = default.copy()
        for key, value in saved.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value
        return result

    # ========================================================================
    # SETTINGS ACCESS (backwards compatible with SettingsManager)
    # ========================================================================

    def get(self, category: str, key: str, default: Any = None) -> Any:
        """Get setting value"""
        return self.state["settings"].get(category, {}).get(key, default)

    def set(self, category: str, key: str, value: Any, auto_save: bool = True):
        """Set setting value and optionally auto-save"""
        if category not in self.state["settings"]:
            self.state["settings"][category] = {}
        self.state["settings"][category][key] = value

        if auto_save:
            self.save_all()
        logger.debug(f"Setting updated: {category}.{key} = {value}")

    # ========================================================================
    # UI STATE MANAGEMENT
    # ========================================================================

    def set_ui_screen(self, screen_name: str):
        """Save current UI screen"""
        self.state["ui_state"]["last_screen"] = screen_name
        self.save_all()

    def get_ui_screen(self) -> str:
        """Get last UI screen"""
        return self.state["ui_state"]["last_screen"]

    def set_active_profile(self, profile_name: Optional[str]):
        """Save active profile"""
        self.state["ui_state"]["active_profile_name"] = profile_name
        self.state["session"]["last_profile"] = profile_name
        self.save_all()

    def get_active_profile(self) -> Optional[str]:
        """Get active profile name"""
        return self.state["ui_state"]["active_profile_name"]

    # ========================================================================
    # SESSION STATE (for resuming performances)
    # ========================================================================

    def save_performance_session(self, performance_state: Any):
        """
        Save active performance session for crash recovery.
        Converts PerformanceState to dict.
        """
        try:
            # Convert PerformanceState to JSON-serializable dict
            session_dict = {
                "event_name": performance_state.event_name,
                "venue_type": performance_state.venue_type.value,
                "current_bpm": performance_state.current_bpm,
                "current_energy": performance_state.current_energy,
                "current_style": performance_state.current_style.value,
                "duration_minutes": performance_state.duration_minutes,
                "start_time": performance_state.start_time,
                "is_live": performance_state.is_live,
                "theme": performance_state.theme,
                "tracks_played_count": len(performance_state.played_tracks),
                "tracks_generated_count": len(performance_state.generated_tracks),
            }

            self.state["session"]["active_performance"] = session_dict
            self.save_all()
            logger.info("Performance session saved")
            return True
        except Exception as e:
            logger.error(f"Failed to save performance session: {e}")
            return False

    def get_active_performance(self) -> Optional[Dict[str, Any]]:
        """Get saved performance session"""
        return self.state["session"].get("active_performance")

    def clear_performance_session(self):
        """Clear active performance (on normal exit)"""
        self.state["session"]["active_performance"] = None
        self.save_all()

    # ========================================================================
    # CONVENIENCE METHODS (backwards compatible)
    # ========================================================================

    def get_audio_device(self) -> Optional[str]:
        return self.get("audio", "output_device")

    def set_audio_device(self, device: str):
        self.set("audio", "output_device", device)

    def get_budget_limit(self) -> float:
        return self.get("budget", "budget_limit", 50.0)

    def set_budget_limit(self, limit: float):
        self.set("budget", "budget_limit", limit)

    def get_midi_device(self) -> Optional[str]:
        return self.get("midi", "input_device")

    def set_midi_device(self, device: Optional[str]):
        self.set("midi", "input_device", device)
        self.set("midi", "enabled", device is not None)

    # Backwards compatibility with old SettingsManager API
    @property
    def settings(self) -> Dict[str, Any]:
        """Access settings dict directly (backwards compatible)"""
        return self.state["settings"]

# Global instance
_state_manager_instance = None

def get_state_manager() -> StateManager:
    """Get or create global state manager instance"""
    global _state_manager_instance
    if _state_manager_instance is None:
        _state_manager_instance = StateManager()
    return _state_manager_instance

# Alias for backwards compatibility
get_settings = get_state_manager
