"""Massloop.ai - Domain Entities (Pure Business Logic)

Layer 1: No external dependencies, only Python stdlib

Enhanced with:
- Additional fields for agentic orchestration integration
- Quality tracking and evaluation metrics
- ROI and cost optimization fields
- Metadata for reflection and planning
- Improved type hints and validation
- Comprehensive docstrings
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
import time
from datetime import datetime


# ============================================================================
# ENUMS (Domain Constants)
# ============================================================================

class VenueType(Enum):
    """Underground electronic music venue types"""
    WAREHOUSE = "warehouse"
    CLUB = "club"
    RAVE = "rave"
    FESTIVAL = "festival"
    TEKNIVAL = "teknival"

    @property
    def display_name(self) -> str:
        """Human-readable venue name"""
        names = {
            self.WAREHOUSE: "Warehouse",
            self.CLUB: "Club",
            self.RAVE: "Underground Rave",
            self.FESTIVAL: "Festival",
            self.TEKNIVAL: "Teknival"
        }
        return names.get(self, self.value.title())

    @property
    def typical_capacity(self) -> Tuple[int, int]:
        """Typical capacity range (min, max)"""
        capacities = {
            self.WAREHOUSE: (200, 1000),
            self.CLUB: (100, 500),
            self.RAVE: (50, 500),
            self.FESTIVAL: (1000, 50000),
            self.TEKNIVAL: (500, 10000)
        }
        return capacities.get(self, (100, 1000))


class UndergroundStyle(Enum):
    """15 underground electronic music styles with metadata"""
    RAW_TECHNO = "raw_techno"
    INDUSTRIAL = "industrial"
    ACID_TECHNO = "acid_techno"
    HARDGROOVE = "hardgroove"
    SCHRANZ = "schranz"
    DUB_TECHNO = "dub_techno"
    HYPNOTIC = "hypnotic"
    MINIMAL = "minimal"
    BREAKBEAT = "breakbeat"
    JUNGLE = "jungle"
    DNB = "drum_and_bass"
    EBM = "ebm"
    DARK_DISCO = "dark_disco"
    HARDTEK = "hardtek"
    AMBIENT = "ambient"

    @property
    def display_name(self) -> str:
        """Human-readable style name for UI display"""
        names = {
            self.RAW_TECHNO: "Raw Techno",
            self.INDUSTRIAL: "Industrial Techno",
            self.ACID_TECHNO: "Acid Techno",
            self.HARDGROOVE: "Hardgroove",
            self.SCHRANZ: "Schranz",
            self.DUB_TECHNO: "Dub Techno",
            self.HYPNOTIC: "Hypnotic Techno",
            self.MINIMAL: "Minimal Techno",
            self.BREAKBEAT: "Breakbeat Rave",
            self.JUNGLE: "Jungle",
            self.DNB: "Drum & Bass",
            self.EBM: "EBM",
            self.DARK_DISCO: "Dark Disco",
            self.HARDTEK: "Hardtek",
            self.AMBIENT: "Ambient"
        }
        return names.get(self, self.value.replace("_", " ").title())

    @property
    def default_bpm_range(self) -> Tuple[int, int]:
        """Default BPM range for style (min, max)"""
        ranges = {
            self.RAW_TECHNO: (130, 140),
            self.INDUSTRIAL: (135, 145),
            self.ACID_TECHNO: (128, 138),
            self.HARDGROOVE: (138, 148),
            self.SCHRANZ: (145, 155),
            self.DUB_TECHNO: (120, 130),
            self.HYPNOTIC: (125, 135),
            self.MINIMAL: (125, 133),
            self.BREAKBEAT: (140, 160),
            self.JUNGLE: (160, 180),
            self.DNB: (170, 180),
            self.EBM: (120, 135),
            self.DARK_DISCO: (115, 125),
            self.HARDTEK: (160, 200),
            self.AMBIENT: (80, 110)
        }
        return ranges.get(self, (120, 140))

    @property
    def default_energy(self) -> float:
        """Default energy level 0.0-1.0 for style"""
        energies = {
            self.RAW_TECHNO: 0.75,
            self.INDUSTRIAL: 0.85,
            self.ACID_TECHNO: 0.70,
            self.HARDGROOVE: 0.80,
            self.SCHRANZ: 0.90,
            self.DUB_TECHNO: 0.50,
            self.HYPNOTIC: 0.65,
            self.MINIMAL: 0.60,
            self.BREAKBEAT: 0.85,
            self.JUNGLE: 0.90,
            self.DNB: 0.95,
            self.EBM: 0.70,
            self.DARK_DISCO: 0.60,
            self.HARDTEK: 0.95,
            self.AMBIENT: 0.30
        }
        return energies.get(self, 0.70)

    @property
    def description(self) -> str:
        """Short description for style selection UI"""
        descriptions = {
            self.RAW_TECHNO: "Raw energy, stripped down",
            self.INDUSTRIAL: "Dark machinery",
            self.ACID_TECHNO: "303 squelch",
            self.HARDGROOVE: "Pounding groove",
            self.SCHRANZ: "Aggressive power",
            self.DUB_TECHNO: "Deep atmosphere",
            self.HYPNOTIC: "Trance loops",
            self.MINIMAL: "Subtle elegance",
            self.BREAKBEAT: "Funky breaks",
            self.JUNGLE: "Fast reggae bass",
            self.DNB: "Liquid fury",
            self.EBM: "Body music",
            self.DARK_DISCO: "New wave gloom",
            self.HARDTEK: "Teknival hardcore",
            self.AMBIENT: "Ethereal spaces"
        }
        return descriptions.get(self, "Electronic music")

    @property
    def typical_instruments(self) -> List[str]:
        """Typical instruments/sounds for prompt generation"""
        instruments = {
            self.RAW_TECHNO: ["kick", "hi-hat", "clap", "synth"],
            self.INDUSTRIAL: ["distorted kick", "metallic percussion", "industrial sounds"],
            self.ACID_TECHNO: ["Roland TB-303", "acid bassline", "squelch"],
            self.HARDGROOVE: ["pounding kick", "driving bassline", "percussion"],
            self.SCHRANZ: ["distorted kick", "aggressive synth", "harsh sounds"],
            self.DUB_TECHNO: ["deep chords", "atmospheric pads", "echo", "delay"],
            self.HYPNOTIC: ["repetitive loops", "minimal percussion", "deep groove"],
            self.MINIMAL: ["subtle percussion", "microhouse elements", "deep bass"],
            self.BREAKBEAT: ["amen break", "funky drums", "syncopated rhythm"],
            self.JUNGLE: ["fast breakbeats", "reggae bassline", "ragga samples"],
            self.DNB: ["fast breaks", "sub bass", "liquid funk", "neurofunk"],
            self.EBM: ["aggressive synths", "industrial sounds", "robotic vocals"],
            self.DARK_DISCO: ["analog synths", "post-punk bass", "new wave"],
            self.HARDTEK: ["distorted kick", "tribe sounds", "hardcore"],
            self.AMBIENT: ["atmospheric pads", "drone", "soundscape", "ethereal"]
        }
        return instruments.get(self, ["synth", "drums", "bass"])


class PerformanceCommand(Enum):
    """Commands for live performance control"""
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


# ============================================================================
# VALUE OBJECTS (Immutable)
# ============================================================================

@dataclass
class AudioReference:
    """
    PRO-LEVEL reference track analysis for AI generation influence.
    Analyzes audio like a mastering engineer - spectral characteristics,
    frequency distribution, transient shaping, dynamics, stereo width.
    """
    name: str
    file_path: str

    # ========================================================================
    # BASIC METRICS (existing)
    # ========================================================================
    tempo: float = 130.0  # BPM
    key: str = "C"
    energy: float = 0.7
    analyzed: bool = False

    # Metadata (existing)
    duration_s: Optional[float] = None
    genre: Optional[str] = None
    artist: Optional[str] = None

    # ========================================================================
    # PRO-LEVEL SPECTRAL ANALYSIS (NEW)
    # ========================================================================
    spectral_centroid: float = 0.0  # Brightness (Hz) - where energy is concentrated
    spectral_rolloff: float = 0.0  # High-freq cutoff (Hz)
    spectral_bandwidth: float = 0.0  # Frequency spread

    # ========================================================================
    # FREQUENCY DISTRIBUTION - 6-band analysis (NEW)
    # ========================================================================
    sub_bass_energy: float = 0.0  # 20-60Hz (club kick weight)
    bass_energy: float = 0.0  # 60-250Hz (bassline presence)
    low_mid_energy: float = 0.0  # 250-500Hz (warmth/body)
    mid_energy: float = 0.0  # 500-2kHz (presence)
    high_mid_energy: float = 0.0  # 2k-6kHz (clarity/attack)
    high_energy: float = 0.0  # 6k-20kHz (air/sparkle)

    # ========================================================================
    # DYNAMICS & TRANSIENTS (NEW)
    # ========================================================================
    dynamic_range_db: float = 0.0  # Loudness variation (compressed vs dynamic)
    transient_density: float = 0.0  # Transients per second (busy vs minimal)
    percussive_ratio: float = 0.0  # Percussive vs harmonic content

    # ========================================================================
    # SPATIAL & STEREO (NEW)
    # ========================================================================
    stereo_width: float = 0.5  # 0.0=mono, 1.0=super wide

    # ========================================================================
    # RHYTHMIC CHARACTERISTICS (NEW)
    # ========================================================================
    onset_strength: float = 0.0  # How hard transients hit
    groove_regularity: float = 0.5  # Regular 4/4 vs broken beat

    added_at: float = field(default_factory=time.time)
    # ✅ NEW: Store analysis results
    analysis: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return f"{self.name} ({self.tempo:.1f} BPM, {self.key} key)"

    def to_producer_description(self) -> str:
        """
        Generate natural language description like a producer would describe it.

        Converts technical analysis into semantic description for Suno prompt.

        Returns:
            Rich semantic description (e.g., "driving 140 BPM, dark and brooding,
            massive sub-bass weight, punchy transients, wide stereo image")
        """
        if not self.analyzed:
            return f"{self.tempo:.0f} BPM in {self.key}"

        parts = []

        # ====================================================================
        # TEMPO CONTEXT
        # ====================================================================
        if self.tempo > 0:
            if self.tempo > 150:
                parts.append(f"blistering {self.tempo:.0f} BPM")
            elif self.tempo > 135:
                parts.append(f"driving {self.tempo:.0f} BPM")
            elif self.tempo < 110:
                parts.append(f"deep {self.tempo:.0f} BPM")
            else:
                parts.append(f"{self.tempo:.0f} BPM")

        # ====================================================================
        # KEY/TONALITY
        # ====================================================================
        if self.key:
            parts.append(f"in {self.key}")

        # ====================================================================
        # SPECTRAL CHARACTER (brightness)
        # ====================================================================
        if self.spectral_centroid > 0:
            if self.spectral_centroid > 3000:
                parts.append("bright and aggressive")
            elif self.spectral_centroid < 1500:
                parts.append("dark and brooding")

        # ====================================================================
        # FREQUENCY WEIGHT DISTRIBUTION
        # ====================================================================
        if self.sub_bass_energy > 0.6:
            parts.append("massive sub-bass weight")
        elif self.sub_bass_energy > 0.4:
            parts.append("solid low-end foundation")

        if self.high_energy > 0.6:
            parts.append("crisp high-end shimmer")
        elif self.high_energy > 0.4:
            parts.append("polished top-end")

        if self.mid_energy > 0.6:
            parts.append("forward and present")

        # ====================================================================
        # DYNAMIC CHARACTER
        # ====================================================================
        if self.dynamic_range_db > 0:
            if self.dynamic_range_db < 6:
                parts.append("heavily compressed and loud")
            elif self.dynamic_range_db > 12:
                parts.append("dynamic and breathing")

        # ====================================================================
        # TRANSIENT CHARACTER
        # ====================================================================
        if self.onset_strength > 0.7:
            parts.append("punchy transients")
        elif self.onset_strength > 0.4:
            parts.append("defined attacks")
        elif self.onset_strength < 0.3:
            parts.append("smooth and sustained")

        # ====================================================================
        # RHYTHMIC DENSITY
        # ====================================================================
        if self.transient_density > 15:
            parts.append("complex polyrhythmic")
        elif self.transient_density > 10:
            parts.append("intricate percussion")
        elif self.transient_density < 5:
            parts.append("minimal and hypnotic")

        # ====================================================================
        # STEREO CHARACTER
        # ====================================================================
        if self.stereo_width > 0.7:
            parts.append("wide stereo image")
        elif self.stereo_width < 0.3:
            parts.append("focused mono core")

        # ====================================================================
        # PERCUSSIVE VS HARMONIC
        # ====================================================================
        if self.percussive_ratio > 0.6:
            parts.append("percussion-driven")
        elif self.percussive_ratio < 0.4:
            parts.append("melodic and harmonic")

        # ====================================================================
        # GROOVE CHARACTER
        # ====================================================================
        if self.groove_regularity > 0.8:
            parts.append("locked groove")
        elif self.groove_regularity < 0.4:
            parts.append("broken and syncopated")

        return ", ".join(parts) if parts else f"{self.tempo:.0f} BPM in {self.key}"


@dataclass
class AudioAnalysisResult:
    """
    Real-time audio analysis results from librosa.

    Used to:
    - Validate Suno output quality
    - Compare requested vs actual parameters
    - Improve future generations via feedback loop
    - Auto-reject bad tracks
    """
    # Basic metrics
    actual_bpm: float  # Detected BPM (may differ from requested!)
    actual_energy: float  # RMS energy (0.0-1.0)
    duration_seconds: float

    # Spectral features
    spectral_centroid: float  # Brightness (Hz)
    spectral_rolloff: float  # High-freq cutoff
    spectral_bandwidth: float  # Frequency spread

    # Frequency bands (normalized 0.0-1.0)
    subbass_energy: float  # 20-60Hz
    bass_energy: float  # 60-250Hz
    mid_energy: float  # 250-2kHz
    high_energy: float  # 2k-20kHz

    # Dynamic/rhythmic
    dynamic_range_db: float  # Loudness variation
    transient_density: float  # Transients per second
    onset_strength: float  # Attack intensity

    # Quality checks
    is_clipping: bool  # Audio distortion detected
    is_silent: bool  # Nearly silent track
    bpm_accuracy: float  # How close to requested BPM (0.0-1.0)

    # Raw data for debugging
    raw_waveform: Optional[Any] = None  # numpy array
    sample_rate: int = 44100

    def __str__(self) -> str:
        return (
            f"BPM: {self.actual_bpm:.1f} | "
            f"Energy: {self.actual_energy:.2f} | "
            f"Brightness: {self.spectral_centroid:.0f}Hz | "
            f"Quality: {'⚠️ CLIPPING' if self.is_clipping else '✅ OK'}"
        )

    def quality_issues(self) -> List[str]:
        """Get list of quality issues for automatic rejection."""
        issues = []
        if self.is_clipping:
            issues.append("Audio is clipping")
        if self.is_silent:
            issues.append("Track is nearly silent")
        if self.bpm_accuracy < 0.85:  # >15% BPM error
            issues.append(f"BPM off by {(1 - self.bpm_accuracy) * 100:.0f}%")
        if self.dynamic_range_db < 3:
            issues.append("Over-compressed (brick-walled)")
        return issues

    def passes_quality_check(self) -> bool:
        """Auto-quality check for track acceptance."""
        return len(self.quality_issues()) == 0


@dataclass
class VoiceProfile:
    """Voice profile for vocal generation"""
    name: str
    sample_paths: List[str]
    language: str = "en"
    quality_score: float = 0.0
    description: str = ""

    # Additional metadata
    pitch_range: Optional[tuple[str, str]] = None  # e.g., ("C2", "C5")
    gender: Optional[str] = None
    style: Optional[str] = None  # e.g., "rap", "singing", "spoken"

    def __str__(self) -> str:
        return f"{self.name} ({self.language})"


@dataclass
class ArtistProfile:
    """
    Artist's musical identity and preferences

    Enhanced with semantic fields for dynamic prompt generation:
    - custom_style_description: Freeform style definition
    - influences: Artist/band inspirations
    - instruments: Preferred sounds/instruments
    - vibe_description: Emotional/atmospheric description
    - darkness_level: 0.0 (bright) to 1.0 (dark)
    - complexity_level: 0.0 (minimal) to 1.0 (complex/layered)
    - signature_sound: Unique sonic identity
    """
    # Core fields (required)
    name: str
    styles: List[UndergroundStyle]
    bpm_min: int
    bpm_max: int

    # Voice and references
    voice_profiles: List[str] = field(default_factory=list)
    references: List[AudioReference] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    # Performance defaults
    default_energy: float = 0.7
    default_theme: str = ""
    preferred_duration_s: int = 240  # Default 4min tracks

    # ========================================================================
    # NEW: Semantic identity fields for dynamic prompt generation
    # ========================================================================

    # Freeform style description (overrides rigid genre selection)
    custom_style_description: str = ""
    # Example: "dark melodic techno with industrial textures"
    # Example: "glitch-hop with jazz samples and broken beats"
    # Example: "Balkan brass meets UK garage"

    # Artist/band influences (used in prompt: "inspired by X and Y")
    influences: List[str] = field(default_factory=list)
    # Example: ["Aphex Twin", "Burial", "Four Tet"]

    # Preferred instruments/sounds (used in prompt: "featuring X, Y, Z")
    instruments: List[str] = field(default_factory=list)
    # Example: ["modular synth", "distorted 808", "field recordings", "vinyl crackle"]

    # Emotional/atmospheric description
    vibe_description: str = ""
    # Example: "melancholic 3am warehouse energy where people dance and cry"
    # Example: "hypnotic meditation music for underground raves"

    # Darkness level: 0.0 = bright/uplifting, 1.0 = dark/brooding
    darkness_level: float = 0.5

    # Complexity level: 0.0 = minimal/repetitive, 1.0 = complex/layered
    complexity_level: float = 0.5

    # Signature sound (unique artist identifier)
    signature_sound: str = ""

    # Example: "reverb-drenched pianos with broken 909 kicks"
    # Example: "Arabic oud melodies over Berlin minimal beats"
    reference_tracks: List[str] = field(default_factory=list)

    persona_id: Optional[str] = None
    artist_clip_id: Optional[str] = None

    def __post_init__(self):
        """Validate artist profile data"""
        if self.bpm_min > self.bpm_max:
            raise ValueError(f"Invalid BPM range: {self.bpm_min}-{self.bpm_max}")

        if not self.styles:
            raise ValueError("At least one style required")

        if not (60 <= self.bpm_min <= 200):
            raise ValueError(f"BPM min out of range: {self.bpm_min}")

        if not (60 <= self.bpm_max <= 200):
            raise ValueError(f"BPM max out of range: {self.bpm_max}")

        # Validate semantic fields
        if not (0.0 <= self.darkness_level <= 1.0):
            raise ValueError(f"Darkness level must be 0.0-1.0: {self.darkness_level}")

        if not (0.0 <= self.complexity_level <= 1.0):
            raise ValueError(f"Complexity level must be 0.0-1.0: {self.complexity_level}")

    def get_average_bpm(self) -> int:
        """Calculate average BPM from range"""
        return (self.bpm_min + self.bpm_max) // 2

    def is_style_compatible(self, style: UndergroundStyle) -> bool:
        """Check if style is in artist's repertoire"""
        return style in self.styles

    def has_custom_style(self) -> bool:
        """Check if artist defined custom style description"""
        return bool(self.custom_style_description.strip())

    def get_mood_description(self) -> str:
        """
        Generate mood description from darkness/complexity levels
        Used in dynamic prompt generation
        """
        # Darkness mapping
        if self.darkness_level > 0.7:
            darkness = "dark and brooding"
        elif self.darkness_level < 0.3:
            darkness = "bright and uplifting"
        else:
            darkness = "balanced"

        # Complexity mapping
        if self.complexity_level > 0.7:
            complexity = "complex and layered"
        elif self.complexity_level < 0.3:
            complexity = "hypnotic and minimal"
        else:
            complexity = "groovy"

        return f"{darkness}, {complexity}"

    def __str__(self) -> str:
        styles_str = ", ".join([s.display_name for s in self.styles])

        # Include custom style if defined
        if self.has_custom_style():
            return f"{self.name} | Custom: {self.custom_style_description} | {self.bpm_min}-{self.bpm_max} BPM"
        else:
            return f"{self.name} | {styles_str} | {self.bpm_min}-{self.bpm_max} BPM"


# ============================================================================
# ENTITIES (Mutable)
# ============================================================================

@dataclass
class LiveTrack:
    """Generated track in live performance with quality metrics"""
    name: str
    style: UndergroundStyle
    bpm: int
    duration_seconds: int
    energy: float

    # Audio data
    audio_data: Optional[bytes] = None

    # Generation metadata
    generation_time: float = 0.0
    tokens_used: int = 0
    is_mock: bool = False
    clip_id: Optional[str] = None

    # Quality tracking
    quality_score: float = 0.0
    bpm_accuracy: float = 1.0
    style_authenticity: float = 0.7
    energy_match: float = 0.7
    production_quality: float = 0.7

    # Orchestration metadata
    reflection_iterations: int = 0
    prompt_quality_score: float = 0.0
    actual_bpm: Optional[int] = None

    # Performance tracking
    played_at: Optional[float] = None
    crowd_reaction: Optional[float] = None

    # Metadata dict
    metadata: Dict[str, Any] = field(default_factory=dict)

    # NEW: Mixer-ready audio file
    local_path: Optional[str] = None

    clip_id: Optional[str] = None
    persona_id_used: Optional[str] = None

    def cost_eur(self) -> float:
        """Calculate cost in EUR at €0.05/token"""
        return self.tokens_used * 0.05

    def was_accepted_first_try(self) -> bool:
        """Check if track was accepted on first generation"""
        return self.reflection_iterations == 0 and self.quality_score >= 0.7

    def __str__(self) -> str:
        status = "🎧" if not self.is_mock else "🔇"
        return f"{status} {self.name} ({self.style.display_name} @ {self.bpm} BPM)"


@dataclass
class PerformanceState:
    """Current state of live performance with comprehensive tracking"""
    event_name: str
    venue_type: VenueType
    current_bpm: int
    current_energy: float
    current_style: UndergroundStyle
    custom_venue_name: Optional[str] = None


    # Track management
    buffer_tracks: List[LiveTrack] = field(default_factory=list)
    played_tracks: List[LiveTrack] = field(default_factory=list)
    generated_tracks: List[LiveTrack] = field(default_factory=list)  # All generated (includes buffer + played)

    # Performance status
    is_live: bool = False
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_minutes: int = 60

    # Live metrics
    crowd_energy: float = 0.5
    total_tokens: int = 0

    # NEW: Performance tracking
    failed_generations: int = 0  # Track failures for ROI
    total_cost_eur: float = 0.0

    # Collaboration & customization
    collaborators: List[str] = field(default_factory=list)
    theme: str = ""

    # NEW: Quality metrics aggregation
    avg_quality_score: float = 0.0
    avg_generation_time: float = 0.0
    successful_generations: int = 0

    # NEW: For queue panel display
    is_generating: bool = False
    current_prompt: Optional[str] = None

    # NEW: Track deck tracking
    current_track_a: Optional['LiveTrack'] = None  # What's playing now on Deck A
    current_track_b: Optional['LiveTrack'] = None  # What's queued/ready on Deck B

    # NEW: Session-wide voice accumulation
    session_voices: List[str] = field(default_factory=list)  # Voices recorded/added live

    # NEW: Mixer state
    mixer_sync_percentage: float = 0.0  # BPM match % for Deck A/B
    is_crossfading: bool = False
    crossfade_progress: float = 0.0  # 0.0-1.0

    def time_elapsed(self) -> float:
        """Get elapsed time in minutes"""
        if not self.start_time:
            return 0.0
        return (time.time() - self.start_time) / 60.0

    def time_remaining(self) -> float:
        """Get remaining time in minutes"""
        return max(0, self.duration_minutes - self.time_elapsed())

    def progress_percentage(self) -> float:
        """Get progress as percentage 0.0-100.0"""
        if self.duration_minutes == 0:
            return 0.0
        return min(100.0, (self.time_elapsed() / self.duration_minutes) * 100.0)

    def tracks_remaining_in_buffer(self) -> int:
        """Get buffer count"""
        return len(self.buffer_tracks)

    def needs_generation(self, threshold: int = 2) -> bool:
        """Check if buffer needs refilling"""
        return len(self.buffer_tracks) < threshold

    def calculate_total_cost_eur(self) -> float:
        """Calculate total cost from all tracks"""
        return sum(track.cost_eur() for track in self.generated_tracks)

    def calculate_avg_quality(self) -> float:
        """Calculate average quality score"""
        if not self.generated_tracks:
            return 0.0
        return sum(t.quality_score for t in self.generated_tracks) / len(self.generated_tracks)

    def calculate_success_rate(self) -> float:
        """Calculate generation success rate"""
        total_attempts = self.successful_generations + self.failed_generations
        if total_attempts == 0:
            return 0.0
        return self.successful_generations / total_attempts

    def get_style_distribution(self) -> Dict[UndergroundStyle, int]:
        """Get distribution of styles played"""
        distribution = {}
        for track in self.played_tracks:
            distribution[track.style] = distribution.get(track.style, 0) + 1
        return distribution

    def get_cost_efficiency(self) -> float:
        """Get quality per EUR spent (higher is better)"""
        cost = self.calculate_total_cost_eur()
        if cost == 0:
            return 0.0
        return self.calculate_avg_quality() / cost

    def update_metrics(self):
        """Update aggregated metrics from tracks"""
        if self.generated_tracks:
            self.avg_quality_score = self.calculate_avg_quality()
            self.avg_generation_time = sum(t.generation_time for t in self.generated_tracks) / len(self.generated_tracks)
            self.successful_generations = len([t for t in self.generated_tracks if t.quality_score >= 0.7])
            self.total_cost_eur = self.calculate_total_cost_eur()

    def __str__(self) -> str:
        status = "🔴 LIVE" if self.is_live else "⏸️  PAUSED"
        return f"{status} {self.event_name} @ {self.venue_type.display_name} ({self.time_elapsed():.1f}min)"


@dataclass
class GenerationRequest:
    """
    Request for AI music generation.

    Combines technical parameters (BPM, energy) with semantic context
    (custom prompt, influences) for dynamic Suno v5 prompt generation.
    """
    # ========================================================================
    # REQUIRED: Core generation parameters
    # ========================================================================
    style: UndergroundStyle
    bpm: int
    energy: float  # 0.0-1.0
    crowd_energy: float  # 0.0-1.0
    theme: str
    duration_seconds: int
    venue_type: VenueType
    lyrics: str = ""

    # ========================================================================
    # NEW: Custom semantic prompt (overrides style.value if set)
    # ========================================================================
    custom_prompt: str = ""

    # ========================================================================
    # OPTIONAL: Vocal processing
    # ========================================================================
    include_vocals: bool = False
    voice_profile_name: str = ""
    voice_profile: Optional[VoiceProfile] = None

    reference_tracks: List[str] = field(default_factory=list)
    voice_reference_path: Optional[str] = None
    """
    Local path to voice file.
    ⚠️ ONLY used during persona CREATION (via create_persona_from_voice()).
    NOT used during track generation.
    For generation, use persona_id from artist_profile instead.
    """


    # ========================================================================
    # OPTIONAL: Reference track blending
    # ========================================================================
    reference_track_id: Optional[str] = None
    reference_influence: Optional[AudioReference] = None
    blend_amount: float = 0.0  # 0.0 = no blend, 1.0 = full blend

    # ========================================================================
    # OPTIONAL: Orchestration parameters
    # ========================================================================
    max_budget_eur: Optional[float] = None
    quality_threshold: float = 0.7
    allow_reflection: bool = True
    max_reflection_iterations: int = 3

    # ========================================================================
    # OPTIONAL: Suno API specific parameters
    # ========================================================================
    mv_version: str = "chirp-crow"  # Suno v5 model version
    make_instrumental: bool = True
    tags: Optional[List[str]] = None

    # ✨ NEW: User input
    user_lyrics: Optional[str] = None  # User-provided lyrics/text
    user_theme_addition: Optional[str] = None  # Additional theme info
    user_input_mode: str = "none"  # none|lyrics|theme|both

    # ✨ NEW: DeepSeek optimization metadata
    deepseek_optimized: bool = False  # Was prompt optimized?
    deepseek_optimization_notes: Optional[str] = None  # What DeepSeek did
    original_prompt_before_optimization: Optional[str] = None  # For comparison

    # ✨ NEW: For CometAPI compatibility
    cometapi_mode: str = "generation"  # generation|artist_consistency|extend|overpainting|underpainting
    generation_type: str = "TEXT"  # TEXT|AUDIO



    def has_voice_clone(self) -> bool:
        """Check if voice cloning is requested"""
        return bool(self.voice_url or self.voice_reference_path)

    def __post_init__(self):
        """Validate generation request parameters"""
        if not (60 <= self.bpm <= 200):
            raise ValueError(f"BPM out of range (60-200): {self.bpm}")

        if not (0.0 <= self.energy <= 1.0):
            raise ValueError(f"Energy out of range (0-1): {self.energy}")

        if not (0.0 <= self.crowd_energy <= 1.0):
            raise ValueError(f"Crowd energy out of range (0-1): {self.crowd_energy}")

        if self.duration_seconds < 10 or self.duration_seconds > 300:
            raise ValueError(f"Duration out of range (10-300s): {self.duration_seconds}s")

        if not (0.0 <= self.blend_amount <= 1.0):
            raise ValueError(f"Blend amount out of range (0-1): {self.blend_amount}")

        if (self.persona_id is None) != (self.artist_clip_id is None):
            logger.warning(
                "⚠️ Persona and artist_clip must be together. "
                f"persona_id={self.persona_id}, artist_clip_id={self.artist_clip_id}"
            )

    def estimated_tokens(self) -> int:
        """
        Estimate token usage for cost prediction.

        Returns:
            Estimated tokens for this generation request
        """
        # Base tokens for generation
        if self.duration_seconds <= 120:
            base_tokens = 20
        else:
            base_tokens = 50

        # Add tokens for vocals
        if self.include_vocals:
            base_tokens += 30

        # Add tokens for reflection
        if self.allow_reflection:
            base_tokens += (self.max_reflection_iterations * 10)

        return base_tokens

    def estimated_cost_eur(self) -> float:
        """
        Estimate cost in EUR based on token usage.

        Returns:
            Estimated cost in euros
        """
        return self.estimated_tokens() * 0.05

    def has_custom_prompt(self) -> bool:
        """Check if custom semantic prompt is defined"""
        return bool(self.custom_prompt.strip())

    def __str__(self) -> str:
        if self.has_custom_prompt():
            return f"Generate [{self.custom_prompt[:40]}...] @ {self.bpm} BPM, {self.duration_seconds}s"
        else:
            return f"Generate {self.style.display_name} @ {self.bpm} BPM, Energy: {self.energy:.2f}, {self.duration_seconds}s"

    def __post_init__(self):
        """Validate generation request"""
        if not 60 <= self.bpm <= 200:
            raise ValueError(f"BPM out of range: {self.bpm}")
        if not 0.0 <= self.energy <= 1.0:
            raise ValueError(f"Energy out of range: {self.energy}")
        if self.duration_seconds < 10 or self.duration_seconds > 300:
            raise ValueError(f"Duration out of range: {self.duration_seconds}s")

    def estimated_tokens(self) -> int:
        """Estimate token usage for cost prediction"""
        # Base tokens
        base_tokens = 50

        # Add tokens for longer duration
        if self.duration_seconds > 120:
            base_tokens += 20

        # Add tokens for vocals
        if self.voice_profile:
            base_tokens += 30

        return base_tokens

    def estimated_cost_eur(self) -> float:
        """Estimate cost in EUR"""
        return self.estimated_tokens() * 0.05

    def __str__(self) -> str:
        return f"Generate {self.style.display_name} @ {self.bpm} BPM, Energy {self.energy:.2f}, {self.duration_seconds}s"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_default_profile(name: str = "Default Artist") -> ArtistProfile:
    """Create a default artist profile for quick start"""
    return ArtistProfile(
        name=name,
        styles=[UndergroundStyle.RAW_TECHNO, UndergroundStyle.INDUSTRIAL],
        bpm_min=130,
        bpm_max=145,
        default_energy=0.75,
        default_theme="underground warehouse rave"
    )


def create_quick_generation_request(
    style: UndergroundStyle,
    crowd_energy: float = 0.5
) -> GenerationRequest:
    """Create a quick generation request with sensible defaults"""
    bpm_range = style.default_bpm_range
    return GenerationRequest(
        style=style,
        bpm=(bpm_range[0] + bpm_range[1]) // 2,
        energy=style.default_energy,
        crowd_energy=crowd_energy,
        duration_seconds=240
    )






@dataclass
class DeckState:
    """
    Real-time deck state - ALWAYS synced with actual performance data.
    NO HARDCODED DEFAULTS - all values derived from orchestrator + PerformanceState
    """
    track_name: str = ""  # Empty = no track
    bpm: int = 0  # 0 = not set
    volume: int = 100  # Default max
    is_playing: bool = False
    progress: float = 0.0
    quality_score: Optional[float] = None  # None = unknown
    energy_level: Optional[int] = None  # None = unknown
    voice_match: Optional[float] = None  # None = unknown
    crowd_response: Optional[int] = None  # None = no data
    agent_decision: str = ""  # Empty = no decision yet
    generation_status: str = ""  # Empty = idle

    # Effects - only set if actually available
    effects: Dict[str, float] = field(default_factory=dict)

    # Metadata for troubleshooting
    last_updated: Optional[datetime] = None
    error_message: Optional[str] = None

    def is_ready(self) -> bool:
        """Check if deck has valid track data"""
        return bool(self.track_name and self.bpm > 0)

    def mark_error(self, error: str):
        """Mark deck as errored with message"""
        self.error_message = error
        logger.warning(f"Deck error: {error}")


@dataclass
class PerformanceCheckpoint:
    """Auto-saved checkpoint at each phase"""
    phase: int  # 1-8 (which phase failed)
    timestamp: float
    profile_name: str
    venue_type: str
    event_name: str
    duration_minutes: int

    # State at checkpoint
    pre_generated_track_json: Optional[Dict[str, Any]] = None
    buffer_tracks_json: List[Dict[str, Any]] = field(default_factory=list)
    played_tracks_json: List[Dict[str, Any]] = field(default_factory=list)

    # Cost tracking
    total_cost_eur: float = 0.0

    # Performance metrics
    elapsed_seconds: float = 0.0
    current_energy: float = 0.5
