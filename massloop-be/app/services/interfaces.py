"""Massloop.ai - Interface Definitions (Abstract Ports)

Layer 3: Contracts between business logic and external world

Clean Architecture Layer 3 - Interfaces/Ports:
- Define contracts for external dependencies
- Allow dependency inversion (business logic depends on abstractions)
- Enable testability (mock implementations)
- Support multiple adapter implementations
- No business logic, only method signatures

Enhanced for agentic orchestration:
- Evaluation and metrics ports
- Orchestrator integration interfaces
- Extended error handling contracts
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Protocol
from app.models.entities import (
    LiveTrack,
    GenerationRequest,
    ArtistProfile,
    PerformanceState,
    AudioReference,
    VoiceProfile,
    PerformanceCommand,
    UndergroundStyle,
    AudioAnalysisResult
)


# ============================================================================
# AI GENERATION INTERFACE
# ============================================================================

class AIGenerationPort(ABC):
    """
    Interface for AI music generation services.

    Implementations:
    - CometSunoAdapter: Production Suno v5 API via CometAPI
    - MockGenerationAdapter: Testing/development mock
    """

    @abstractmethod
    async def generate_track(self, request: GenerationRequest) -> LiveTrack:
        """
        Generate a music track based on request.

        Args:
            request: Generation parameters (style, BPM, energy, etc.)

        Returns:
            LiveTrack: Generated track with audio data and metadata

        Raises:
            GenerationError: If generation fails
            APIError: If API is unavailable
            BudgetExceededError: If generation would exceed budget
        """
        pass

    @abstractmethod
    async def add_vocals(self, track: LiveTrack, voice_profile_name: str) -> LiveTrack:
        """
        Add vocals to existing instrumental track.

        Args:
            track: Existing track to add vocals to
            voice_profile_name: Name of voice profile to use

        Returns:
            LiveTrack: New track with vocals added

        Raises:
            VoiceProfileNotFoundError: If voice profile doesn't exist
            GenerationError: If vocal generation fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if generation service is available.

        Returns:
            bool: True if service is healthy, False otherwise
        """
        pass

    @abstractmethod
    async def get_service_info(self) -> Dict[str, Any]:
        """
        Get generation service information and capabilities.

        Returns:
            Dict with keys:
                - available: bool
                - version: str (e.g., "v5", "chirp-crow")
                - max_duration_s: int
                - supported_styles: List[str]
                - rate_limit: Optional[int]
        """
        pass


# ============================================================================
# AUDIO OUTPUT INTERFACE
# ============================================================================

class AudioOutputPort(ABC):
    """
    Interface for audio playback and streaming.

    Implementations:
    - PygameAudioAdapter: Local playback via pygame
    - JACKAudioAdapter: Professional audio routing
    - NetworkStreamAdapter: Remote streaming
    """

    @abstractmethod
    async def initialize(self, sample_rate: int = 44100, channels: int = 2) -> bool:
        """
        Initialize audio output system.

        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels (1=mono, 2=stereo)

        Returns:
            bool: True if initialization successful
        """
        pass

    @abstractmethod
    async def play_track(self, track: LiveTrack) -> bool:
        """
        Play a track (blocking until complete).

        Args:
            track: Track to play

        Returns:
            bool: True if playback successful
        """
        pass

    @abstractmethod
    async def stream_track(self, audio_data: bytes) -> bool:
        """
        Stream audio data to output (non-blocking).

        Args:
            audio_data: Raw audio bytes to stream

        Returns:
            bool: True if streaming started successfully
        """
        pass

    @abstractmethod
    async def stop_playback(self) -> bool:
        """
        Stop current playback.

        Returns:
            bool: True if stopped successfully
        """
        pass

    @abstractmethod
    async def get_latency_ms(self) -> float:
        """
        Get current audio output latency in milliseconds.

        Critical for live performance (<10ms target).

        Returns:
            float: Latency in milliseconds
        """
        pass

    @abstractmethod
    async def get_available_devices(self) -> List[Dict[str, Any]]:
        """
        Get list of available audio output devices.

        Returns:
            List of dicts with keys:
                - name: str (device name)
                - id: int (device ID)
                - channels: int (channel count)
                - sample_rate: int (native sample rate)
                - is_default: bool
        """
        pass

    @abstractmethod
    async def set_output_device(self, device_id: int) -> bool:
        """
        Select audio output device.

        Args:
            device_id: Device ID from get_available_devices()

        Returns:
            bool: True if device set successfully
        """
        pass


# ============================================================================
# STORAGE INTERFACE
# ============================================================================

class StoragePort(ABC):
    """
    Interface for data persistence.

    Implementations:
    - FileStorageAdapter: Local file-based storage (JSON)
    - DatabaseStorageAdapter: SQL/NoSQL database
    - CloudStorageAdapter: S3/GCS cloud storage
    """

    @abstractmethod
    async def save_profile(self, profile: ArtistProfile) -> bool:
        """
        Save artist profile.

        Args:
            profile: ArtistProfile to persist

        Returns:
            bool: True if saved successfully
        """
        pass

    @abstractmethod
    async def load_profile(self, name: str) -> Optional[ArtistProfile]:
        """
        Load artist profile by name.

        Args:
            name: Profile name

        Returns:
            ArtistProfile if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_profiles(self) -> List[str]:
        """
        List all saved profile names.

        Returns:
            List of profile names
        """
        pass

    @abstractmethod
    async def delete_profile(self, name: str) -> bool:
        """
        Delete a profile by name.

        Args:
            name: Profile name to delete

        Returns:
            bool: True if deleted successfully
        """
        pass

    @abstractmethod
    async def save_performance(self, state: PerformanceState) -> bool:
        """
        Save complete performance state.

        Args:
            state: PerformanceState to persist

        Returns:
            bool: True if saved successfully
        """
        pass

    @abstractmethod
    async def load_performance(self, event_name: str, timestamp: float) -> Optional[PerformanceState]:
        """
        Load a past performance by event name and timestamp.

        Args:
            event_name: Event name
            timestamp: Performance start timestamp

        Returns:
            PerformanceState if found, None otherwise
        """
        pass

    @abstractmethod
    async def save_voice_profile(self, name: str, file_path: str) -> bool:
        """
        Save reference to on-disk voice profile.

        Args:
            name: Voice profile name
            file_path: Path to audio file

        Returns:
            bool: True if saved successfully
        """
        pass

    @abstractmethod
    async def save_voice_profile_bytes(self, name: str, wav_bytes: bytes) -> bool:
        """
        Save in-memory voice profile audio data.

        Args:
            name: Voice profile name
            wav_bytes: WAV audio data

        Returns:
            bool: True if saved successfully
        """
        pass

    @abstractmethod
    async def save_metrics(self, metrics: Dict[str, Any]) -> bool:
        """
        Save performance metrics for analytics.

        Args:
            metrics: Dict containing performance metrics
                - timestamp: ISO timestamp
                - quality_score: float
                - cost_eur: float
                - duration_s: float
                - success: bool

        Returns:
            bool: True if saved successfully
        """
        pass

    @abstractmethod
    async def load_metrics(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Load metrics for date range.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            List of metric dicts
        """
        pass

    @abstractmethod
    async def get_voice_profile_path(self, name: str) -> Optional[str]:
        """
        Get file path to voice profile WAV file.

        Args:
            name: Voice profile name

        Returns:
            Full path to WAV file or None if not found
        """
        pass


# ============================================================================
# REFERENCE ANALYSIS INTERFACE
# ============================================================================

class ReferenceAnalysisPort(ABC):
    """
    Interface for audio reference track analysis.

    Implementations:
    - LibrosaReferenceAnalyzer: Using librosa for analysis
    - EssentiaAnalyzer: Using Essentia library
    - CloudAnalyzer: Cloud-based audio analysis
    """

    @abstractmethod
    async def analyze_audio_file(self, file_path: str) -> AudioReference:
        """
        Analyze audio file for musical features.

        Extracts:
        - BPM/tempo
        - Key and scale
        - Energy level
        - Spectral characteristics

        Args:
            file_path: Path to audio file

        Returns:
            AudioReference: Analysis results

        Raises:
            FileNotFoundError: If file doesn't exist
            AnalysisError: If analysis fails
        """
        pass

    @abstractmethod
    async def analyze_batch(self, file_paths: List[str]) -> List[AudioReference]:
        """
        Analyze multiple audio files in batch.

        Args:
            file_paths: List of audio file paths

        Returns:
            List of AudioReference objects
        """
        pass

    @abstractmethod
    async def get_supported_formats(self) -> List[str]:
        """
        Get list of supported audio formats.

        Returns:
            List of file extensions (e.g., ["mp3", "wav", "flac"])
        """
        pass


class AudioAnalysisPort(ABC):
    """
    Real-time audio analysis interface (librosa).

    Use cases:
    - Analyze Suno output AFTER generation
    - Compare requested vs actual parameters
    - Build feedback loop for prompt optimization
    - Auto-reject low-quality tracks
    """

    @abstractmethod
    async def analyze_audio_bytes(self, audio_bytes: bytes, requested_bpm: int) -> AudioAnalysisResult:
        """
        Analyze audio from bytes (MP3/WAV).

        Args:
            audio_bytes: Raw audio data
            requested_bpm: Target BPM for accuracy calculation

        Returns:
            AudioAnalysisResult with full analysis
        """
        pass

    @abstractmethod
    async def analyze_audio_file(self, filepath: str, requested_bpm: int) -> AudioAnalysisResult:
        """
        Analyze audio from file path.

        Args:
            filepath: Path to audio file
            requested_bpm: Target BPM for accuracy calculation

        Returns:
            AudioAnalysisResult with full analysis
        """
        pass

    @abstractmethod
    async def quick_quality_check(self, audio_bytes: bytes) -> bool:
        """
        Fast quality check (no full analysis).

        Returns:
            True if track passes basic checks (no clipping, not silent)
        """
        pass


# ============================================================================
# CROWD SENSING INTERFACE
# ============================================================================

class CrowdSensingPort(ABC):
    """
    Interface for crowd energy detection.

    Implementations:
    - MockCrowdSensing: Simulated crowd energy
    - MicrophoneCrowdSensing: Audio level sensing
    - CameraCrowdSensing: Computer vision-based detection
    - WearableCrowdSensing: Heart rate / movement sensors
    """

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize crowd sensing system.

        Returns:
            bool: True if initialized successfully
        """
        pass

    @abstractmethod
    async def get_crowd_energy(self) -> float:
        """
        Get current crowd energy level.

        Returns:
            float: Energy level 0.0 (calm) to 1.0 (peak)
        """
        pass

    @abstractmethod
    async def get_crowd_feedback(self) -> Dict[str, float]:
        """
        Get detailed crowd metrics.

        Returns:
            Dict with keys:
                - energy: float (0.0-1.0)
                - approval: float (0.0-1.0)
                - movement: float (0.0-1.0)
                - volume: float (0.0-1.0)
        """
        pass

    @abstractmethod
    async def calibrate(self, duration_s: float = 10.0) -> bool:
        """
        Calibrate sensors for current environment.

        Args:
            duration_s: Calibration duration in seconds

        Returns:
            bool: True if calibration successful
        """
        pass


# ============================================================================
# VOICE PROCESSING INTERFACE
# ============================================================================

class VoiceProcessingPort(ABC):
    """
    Interface for voice recording and processing.

    Implementations:
    - MicrophoneVoiceAdapter: Local microphone recording
    - CloudVoiceAdapter: Cloud-based voice processing
    """

    @abstractmethod
    async def record_voice_profile(self, duration_s: float, sample_rate: int = 44100) -> bytes:
        """
        Record voice sample from microphone.

        Args:
            duration_s: Recording duration in seconds
            sample_rate: Audio sample rate in Hz

        Returns:
            bytes: Raw WAV audio data

        Raises:
            RecordingError: If recording fails
            MicrophoneError: If microphone unavailable
        """
        pass

    @abstractmethod
    async def process_speech_input(self, audio_data: bytes) -> str:
        """
        Convert speech to text (STT).

        Args:
            audio_data: Audio bytes to transcribe

        Returns:
            str: Transcribed text
        """
        pass

    @abstractmethod
    async def get_available_microphones(self) -> List[Dict[str, Any]]:
        """
        Get list of available microphone devices.

        Returns:
            List of dicts with keys:
                - name: str
                - id: int
                - channels: int
                - is_default: bool
        """
        pass


# ============================================================================
# NEW: EVALUATION INTERFACE (for Agentic Orchestration)
# ============================================================================

class EvaluationPort(ABC):
    """
    Interface for track quality evaluation.

    Implementations:
    - AgenticEvaluationAdapter: LLM-based quality assessment
    - RuleBasedEvaluator: Deterministic metric checking
    """

    @abstractmethod
    async def evaluate_generation_request(
        self,
        request: GenerationRequest
    ) -> Dict[str, Any]:
        """
        Evaluate generation request quality (pre-generation).

        Args:
            request: Generation request to evaluate

        Returns:
            Dict with keys:
                - quality_score: float (0.0-1.0)
                - issues: List[str]
                - suggestions: List[str]
        """
        pass

    @abstractmethod
    async def evaluate_track_quality(
        self,
        track: LiveTrack,
        expected: GenerationRequest
    ) -> Dict[str, Any]:
        """
        Evaluate generated track quality (post-generation).

        Args:
            track: Generated track
            expected: Original request parameters

        Returns:
            Dict with keys:
                - overall_score: float (0.0-1.0)
                - bpm_accuracy: float
                - style_authenticity: float
                - energy_match: float
                - production_quality: float
                - pass_threshold: bool
        """
        pass

    @abstractmethod
    async def calculate_roi_metrics(
        self,
        state: PerformanceState
    ) -> Dict[str, Any]:
        """
        Calculate ROI and cost efficiency metrics.

        Args:
            state: Current performance state

        Returns:
            Dict with keys:
                - total_cost_eur: float
                - cost_per_track: float
                - avg_quality_score: float
                - cost_efficiency: float
                - wasted_credits: float
        """
        pass


# ============================================================================
# NEW: MIDI/HARDWARE CONTROL INTERFACE
# ============================================================================

class HardwareControlPort(ABC):
    """
    Interface for MIDI controllers and hardware input.

    Implementations:
    - MIDIControllerAdapter: Standard MIDI devices
    - KeyboardControlAdapter: Computer keyboard fallback
    - OSCControlAdapter: Open Sound Control protocol
    """

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize hardware control interface."""
        pass

    @abstractmethod
    async def get_available_devices(self) -> List[Dict[str, Any]]:
        """
        Get list of available MIDI/control devices.

        Returns:
            List of dicts with device info
        """
        pass

    @abstractmethod
    async def register_callback(
        self,
        command: PerformanceCommand,
        control_id: int,
        callback: Any
    ) -> bool:
        """
        Register callback for hardware control.

        Args:
            command: Performance command to trigger
            control_id: MIDI CC number or key code
            callback: Async function to call

        Returns:
            bool: True if registered successfully
        """
        pass

    @abstractmethod
    async def read_control_value(self, control_id: int) -> float:
        """
        Read current value from control (e.g., fader, knob).

        Args:
            control_id: Control identifier

        Returns:
            float: Control value 0.0-1.0
        """
        pass


# ============================================================================
# INTERFACE REGISTRY (for documentation)
# ============================================================================

ALL_PORTS = [
    AIGenerationPort,
    AudioOutputPort,
    StoragePort,
    ReferenceAnalysisPort,
    CrowdSensingPort,
    VoiceProcessingPort,
    EvaluationPort,
    HardwareControlPort
]

def get_port_summary() -> Dict[str, str]:
    """Get summary of all available ports."""
    return {
        port.__name__: port.__doc__.split('\n')[0] if port.__doc__ else ""
        for port in ALL_PORTS
    }


# ==============================================================================
# PROFILE PERSONA ANALYSIS PORT (NEW - For v2 AI features)
# ==============================================================================

class ProfilePersonaPort(ABC):
    """
    Interface for AI-powered artist profile analysis.

    This port enables intelligent extraction of musical identity from
    freeform text descriptions, allowing musicians to describe their sound
    in natural language instead of picking rigid genre tags.

    Use Cases:
    - Analyze freeform artist description → suggest UndergroundStyle matches
    - Extract instruments/sounds mentioned in text
    - Generate semantic Suno prompts from artist interviews
    - Match artist influences to sonic characteristics

    Implementation:
    - v1: Simple keyword matching (externals.py)
    - v2: DeepSeek/GPT-4 powered semantic analysis

    Example Flow:
        >>> analyzer = DeepSeekProfileAnalyzer()  # Future implementation
        >>> text = "I make dark melodic techno inspired by Nina Kraviz"
        >>> styles = await analyzer.suggest_styles(text)
        >>> # Returns: [(INDUSTRIAL, 0.85), (MINIMAL, 0.72), (HYPNOTIC, 0.68)]
    """

    @abstractmethod
    async def analyze_freeform_description(self, text: str) -> Dict[str, Any]:
        """
        Analyze freeform artist description and extract musical characteristics.

        Args:
            text: Natural language description of artist's music
                Example: "I create atmospheric techno with modular synths,
                         inspired by Burial and Aphex Twin, perfect for 3am warehouse raves"

        Returns:
            Dict containing:
                - suggested_styles: List[UndergroundStyle] (top 3 matches)
                - confidence_scores: Dict[UndergroundStyle, float]
                - extracted_instruments: List[str]
                - mood_keywords: List[str]
                - suggested_bpm_range: Tuple[int, int]
                - influences: List[str] (detected artist names)

        Example Output:
            {
                "suggested_styles": [UndergroundStyle.INDUSTRIAL, UndergroundStyle.MINIMAL],
                "confidence_scores": {
                    UndergroundStyle.INDUSTRIAL: 0.85,
                    UndergroundStyle.MINIMAL: 0.72
                },
                "extracted_instruments": ["modular synth", "distorted 808"],
                "mood_keywords": ["dark", "atmospheric", "hypnotic"],
                "suggested_bpm_range": (125, 135),
                "influences": ["Burial", "Aphex Twin"]
            }
        """
        pass

    @abstractmethod
    async def suggest_styles(
            self,
            description: str,
            max_suggestions: int = 3
    ) -> List[Tuple[UndergroundStyle, float]]:
        """
        Suggest UndergroundStyle enums based on freeform description.

        Args:
            description: Artist's description of their music
            max_suggestions: Maximum number of style suggestions

        Returns:
            List of (UndergroundStyle, confidence_score) tuples, sorted by confidence

        Example:
            >>> suggestions = await analyzer.suggest_styles("dark industrial beats")
            >>> # Returns: [(INDUSTRIAL, 0.92), (RAW_TECHNO, 0.78), (SCHRANZ, 0.65)]
        """
        pass

    @abstractmethod
    async def generate_instruments_list(self, description: str) -> List[str]:
        """
        Extract or generate list of instruments/sounds from description.

        Args:
            description: Text mentioning instruments or sonic characteristics

        Returns:
            List of instrument/sound names

        Example:
            >>> instruments = await analyzer.generate_instruments_list(
            ...     "I use modular synths, 808 drums, and field recordings"
            ... )
            >>> # Returns: ["modular synth", "808 drums", "field recordings"]
        """
        pass

    @abstractmethod
    async def enrich_profile_with_ai(
            self,
            profile: 'ArtistProfile'
    ) -> Dict[str, Any]:
        """
        Enrich existing profile with AI-generated suggestions.

        Analyzes profile's custom_style_description and influences fields,
        then suggests improvements or missing data.

        Args:
            profile: Existing ArtistProfile

        Returns:
            Dict with suggestions:
                - recommended_tags: List[str]
                - similar_artists: List[str]
                - venue_recommendations: List[VenueType]
                - prompt_improvements: str
        """
        pass


from typing import Protocol, Optional


class AudioMixerPort(Protocol):
    """
    Port for DJ-style beatmatching and crossfading two tracks in real-time.

    Responsibilities:
    - BPM detection and matching
    - Time-stretching to sync tempos
    - Crossfade blending for seamless transitions
    - Sync analysis for UI feedback
    """

    async def beatmatch_and_crossfade(
            self,
            track_a_path: str,
            track_b_path: str,
            fade_duration: float = 3.0
    ) -> bytes:
        """
        Beatmatch track B to track A using librosa DTW,
        then crossfade for smooth transition.

        Args:
            track_a_path: Local path to playing track (anchor)
            track_b_path: Local path to queued track (to be synced)
            fade_duration: Length of crossfade in seconds

        Returns:
            Mixed audio as bytes (WAV format)

        Raises:
            FileNotFoundError: If audio files not found
            RuntimeError: If beatmatching fails
        """
        ...

    async def analyze_sync_percentage(
            self,
            track_a_path: str,
            track_b_path: str
    ) -> float:
        """
        Calculate BPM match percentage between two tracks.

        Args:
            track_a_path: Local path to track A
            track_b_path: Local path to track B

        Returns:
            Sync percentage (0.0-100.0) where 100.0 = perfect match

        Raises:
            FileNotFoundError: If audio files not found
            RuntimeError: If BPM detection fails
        """
        ...

    async def get_bpm(self, track_path: str) -> float:
        """
        Detect BPM of a single track.

        Returns:
            BPM as float
        """
        ...





class VoiceProfilePort(Protocol):
    """
    Type-safe protocol for voice profile handling.
    Enforces that voice_profile is always a string (or None).
    """

    def extract_voice_profile(
            self,
            voice_profiles: List[str]
    ) -> Optional[str]:
        """
        Extract single voice profile from list.

        Args:
            voice_profiles: List of voice profile names

        Returns:
            Single voice profile name (string) or None

        Raises:
            TypeError: If voice_profiles is not a list
            ValueError: If voice_profiles is empty and no default
        """
        ...

    def validate_voice_profile(
            self,
            voice_profile: Optional[str]
    ) -> Optional[str]:
        """
        Validate that voice_profile is correct type.

        Raises:
            TypeError: If not string or None
        """
        ...
