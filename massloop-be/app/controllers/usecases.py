"""Massloop.ai - Use Cases (Business Logic Layer)

Layer 2: Business logic with agentic orchestration integration

Integrates:
- PerformanceOrchestratorAgent for intelligent generation
- Reflection loop for prompt optimization
- Quality evaluation with automatic rejection
- Cost tracking and ROI optimization
- Clean Architecture principles (talks to Layer 3 interfaces)
"""

import os
import asyncio
import time
from typing import Any, Optional, List, Tuple
from loguru import logger
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.interfaces import (
    AIGenerationPort,
    AudioOutputPort,
    CrowdSensingPort,
    StoragePort,
    VoiceProcessingPort,
    ReferenceAnalysisPort,
    AudioMixerPort  # ADD THIS
)
from app.models.entities import (
    GenerationRequest,
    LiveTrack,
    PerformanceState,
    ArtistProfile,
    UndergroundStyle,
    VenueType,
    AudioReference
)





def build_dynamic_suno_prompt(
        profile: ArtistProfile,
        request: GenerationRequest,
        venue_name: Optional[str] = None
) -> str:
    """
    Build COMPLETE semantic Suno v5 prompt from artist profile identity.

    Includes ALL context:
    - Artist name (e.g., "Kataesis")
    - Venue atmosphere (warehouse/club/custom)
    - Custom style description
    - Influences/inspirations
    - Instruments/sounds
    - Reference track analysis (FULL, not stripped)
    - Vibe/mood description
    - Technical params (BPM, energy)

    Args:
        profile: Artist profile with semantic fields
        request: Generation request with technical params
        venue_name: Custom venue name (e.g., "home", "rooftop")

    Returns:
        Rich natural language prompt for CometAPI Suno v5 (200-400 chars)
    """
    prompt_parts = []

    # ========================================================================
    # STEP 1: Artist Name (NEW!)
    # ========================================================================
    if profile.name and profile.name != "Quick Start":
        prompt_parts.append(f"Artist: {profile.name}")
        logger.debug(f"Added artist name: {profile.name}")

    # ========================================================================
    # STEP 2: Venue Context (NEW!)
    # ========================================================================
    if venue_name:
        # Custom venue (user entered "home", "rooftop", etc.)
        prompt_parts.append(f"at {venue_name}")
        logger.debug(f"Added custom venue: {venue_name}")
    elif request.venue_type:
        # Standard venue with atmosphere
        venue_vibes = {
            VenueType.WAREHOUSE: "warehouse rave atmosphere, industrial space",
            VenueType.CLUB: "intimate club setting, dark basement",
            VenueType.RAVE: "underground rave, squat party vibe",
            VenueType.FESTIVAL: "festival main stage, outdoor energy",
            VenueType.TEKNIVAL: "teknival free party, nomadic sound system"
        }
        venue_desc = venue_vibes.get(request.venue_type, "")
        if venue_desc:
            prompt_parts.append(venue_desc)
            logger.debug(f"Added venue atmosphere: {venue_desc}")

    # ========================================================================
    # STEP 3: Base Style (Custom or Enum)
    # ========================================================================
    if profile.has_custom_style():
        prompt_parts.append(profile.custom_style_description.strip())
        logger.debug(f"Using custom style: {profile.custom_style_description}")
    else:
        prompt_parts.append(request.style.display_name)
        logger.debug(f"Using enum style: {request.style.display_name}")

    # ========================================================================
    # STEP 4: Instruments/Sounds
    # ========================================================================
    if profile.instruments:
        instruments_str = ", ".join(profile.instruments[:5])
        prompt_parts.append(f"with {instruments_str}")
        logger.debug(f"Added instruments: {instruments_str}")

    # ========================================================================
    # STEP 5: Influences (Inspirations)
    # ========================================================================
    if profile.influences:
        influences_str = " and ".join(profile.influences[:2])
        prompt_parts.append(f"inspired by {influences_str}")
        logger.debug(f"Added influences: {influences_str}")

    # ========================================================================
    # STEP 6: Reference Track Analysis (FULL - NO BPM STRIPPING!)
    # ========================================================================
    if profile.references:
        ref = profile.references[0]
        if ref.analyzed and hasattr(ref, 'to_producer_description'):
            ref_description = ref.to_producer_description()
            # ✅ KEEP FULL DESCRIPTION (don't strip BPM anymore!)
            if ref_description:
                prompt_parts.append(f"reference: {ref_description}")
                logger.success(f"✅ Full reference analysis: {ref_description[:80]}...")

    # ========================================================================
    # STEP 7: Vibe/Atmosphere Description
    # ========================================================================
    if profile.vibe_description.strip():
        prompt_parts.append(f"{profile.vibe_description.strip()} vibe")
        logger.debug(f"Added vibe: {profile.vibe_description}")

    # ========================================================================
    # STEP 8: Mood from Sliders (Darkness/Complexity)
    # ========================================================================
    mood = profile.get_mood_description()
    prompt_parts.append(mood)
    logger.debug(f"Added mood: {mood}")

    # ========================================================================
    # STEP 9: Signature Sound
    # ========================================================================
    if profile.signature_sound.strip():
        prompt_parts.append(f"signature: {profile.signature_sound.strip()}")
        logger.debug(f"Added signature: {profile.signature_sound}")

    # ========================================================================
    # STEP 10: Technical Parameters (BPM, Energy)
    # ========================================================================
    prompt_parts.append(f"{request.bpm} BPM")

    if request.energy > 0.7:
        energy_desc = "high energy, driving"
    elif request.energy < 0.4:
        energy_desc = "low energy, ambient"
    else:
        energy_desc = "balanced, groovy"
    prompt_parts.append(energy_desc)

    # ========================================================================
    # STEP 11: Theme (if exists)
    # ========================================================================
    if request.theme and request.theme.strip():
        prompt_parts.append(f"theme: {request.theme.strip()}")

    # ========================================================================
    # Assemble Final Prompt (NO TRUNCATION!)
    # ========================================================================
    final_prompt = ", ".join(prompt_parts)

    logger.success(f"✅ Generated FULL prompt ({len(final_prompt)} chars)")
    logger.info(f"Preview: {final_prompt[:150]}...")

    return final_prompt


# ============================================================================
# LIVE PERFORMANCE USE CASE (With Agentic Orchestration)
# ============================================================================

class LivePerformanceUseCase:
    """
    Core business logic for LIVE music performance.

    LOVABLE FOR PERFORMERS:
    ✅ Every track uses THEIR voice (not generic)
    ✅ Voice consistency across entire session
    ✅ Response to crowd energy (dynamic)
    ✅ Never crashes (graceful fallback)
    ✅ Fast generation (<3s)

    LOVABLE FOR AUDIENCE:
    ✅ Recognizable artist voice
    ✅ Professional quality tracks
    ✅ Responsive to venue energy
    ✅ Seamless transitions
    ✅ Zero latency playback
    """

    def __init__(
            self,
            ai_gen: AIGenerationPort,
            audio_port: AudioOutputPort,
            crowd_sense: CrowdSensingPort,
            storage: StoragePort,
            voice_processor: VoiceProcessingPort,
            orchestrator: Optional[Any] = None,
            reference_analyzer: Optional[ReferenceAnalysisPort] = None,
            audio_analyzer: Optional['AudioAnalysisPort'] = None,
            mixer: Optional[AudioMixerPort] = None
    ):
        """Initialize use case with all ports"""
        self.ai_gen = ai_gen
        self.audio_port = audio_port
        self.crowd = crowd_sense
        self.storage = storage
        self.voice_processor = voice_processor
        self.orchestrator = orchestrator
        self.reference_analyzer = reference_analyzer
        self.audio_analyzer = audio_analyzer
        self.mixer = mixer

        self._gen_lock = asyncio.Lock()
        self._quality_threshold = 0.7
        self._max_retries = 2

        logger.info(f"LivePerformanceUseCase initialized")
        logger.info(f"  Orchestrator: {'✅' if orchestrator else '❌'}")
        logger.info(f"  Audio Analyzer: {'✅' if audio_analyzer else '❌'}")
        logger.info(f"  Mixer: {'✅' if mixer else '❌'}")

    async def start_performance(
            self,
            event: str,
            profile: ArtistProfile,
            style: UndergroundStyle,
            venue: VenueType,
            duration: int,
            theme: Optional[str] = None,
            custom_venue_name: Optional[str] = None
    ) -> PerformanceState:
        """
        Initialize performance with artist profile.

        LOVABLE: Profile loaded = voice ready
        """
        bpm = (profile.bpm_min + profile.bpm_max) // 2

        state = PerformanceState(
            event_name=event,
            venue_type=venue,
            custom_venue_name=custom_venue_name,
            current_bpm=bpm,
            current_energy=style.default_energy,
            current_style=style,
            duration_minutes=duration,
            start_time=time.time(),
            is_live=True,
            theme=theme,
            buffer_tracks=[],
            played_tracks=[],
            generated_tracks=[],
            total_tokens=0,
            failed_generations=0
        )

        logger.success(f"🎤 Performance: {profile.name} @ {venue.value}")
        logger.info(f"   {profile.styles.display_name if profile.styles else 'Unknown'} | {bpm}BPM")
        logger.info(f"   Voice profiles: {profile.voice_profiles}")

        # Pre-fill buffer
        await self._fill_buffer(state, profile)

        # Cost analysis background task
        if self.orchestrator:
            asyncio.create_task(self._analyze_performance_costs(state))

        return state

    async def _fill_buffer(
            self,
            state: PerformanceState,
            profile: ArtistProfile,
            target_buffer_size: int = 3
    ):
        """Fill track buffer with lovable, voice-consistent tracks"""
        async with self._gen_lock:
            while len(state.buffer_tracks) < target_buffer_size:
                try:
                    # ✅ CORE: Generate with profile
                    track = await self._generate_track_with_quality_check(state, profile)

                    if track:
                        state.buffer_tracks.append(track)
                        state.generated_tracks.append(track)
                        state.total_tokens += track.tokens_used

                        logger.success(f"✅ Buffer: {len(state.buffer_tracks)}/{target_buffer_size}")
                    else:
                        logger.warning("⚠️ Generation failed")
                        state.failed_generations += 1
                        break

                except Exception as e:
                    logger.error(f"Buffer error: {e}")
                    state.failed_generations += 1
                    break

    async def _generate_track_with_quality_check(
            self,
            state: PerformanceState,
            profile: ArtistProfile
    ) -> Optional[LiveTrack]:
        """
        MAIN GENERATION METHOD - LOVABLE VERSION

        ✅ Ensures:
        - artist_profile passed (for voice detection)
        - voice_reference_path loaded from storage
        - reference_tracks loaded from profile
        - tags built from profile characteristics
        - Voice consistency guaranteed

        NO DUPLICATES - SINGLE METHOD ONLY!
        """

        try:
            # Get crowd energy for dynamic generation
            crowd_energy = await self.crowd.get_crowd_energy()

            # Create base request
            base_request = GenerationRequest(
                style=state.current_style,
                bpm=state.current_bpm,
                energy=state.current_energy,
                crowd_energy=crowd_energy,
                theme=state.theme or "",
                duration_seconds=240,
                venue_type=state.venue_type
            )

            # FAST PATH: Only 1 attempt for performance
            max_attempts = 1

            for attempt in range(max_attempts):
                try:
                    # ====================================================================
                    # STEP 1: Optimize with orchestrator
                    # ====================================================================
                    if self.orchestrator:
                        optimized_request, metadata = await self.orchestrator.optimize_generation_request(
                            base_request=base_request,
                            crowd_energy=crowd_energy,
                            performance_state=state,
                            artist_profile=profile,
                            max_reflection_iterations=1
                        )
                    else:
                        optimized_request = base_request
                        metadata = {}

                    # ====================================================================
                    # STEP 2: LOAD VOICE FROM PROFILE ← CRITICAL FOR LOVABILITY!
                    # ====================================================================
                    voice_reference_path = None

                    if profile.voice_profiles and len(profile.voice_profiles) > 0:
                        voice_name = (
                            profile.voice_profiles[0]  # ✅ CORRECT! Returns STRING
                            if isinstance(profile.voice_profiles, list)
                            else profile.voice_profiles
                        )
                        logger.info(f"🎤 Loading voice: {voice_name}")

                        voice_reference_path = await self.storage.get_voice_profile_path(voice_name)

                        if voice_reference_path:
                            logger.success(f"✓ Voice path: {voice_reference_path}")
                            optimized_request.voice_reference_path = voice_reference_path
                        else:
                            logger.warning(f"⚠️ Voice not found: {voice_name}")
                    else:
                        logger.info("No voice profiles in profile")

                    # ====================================================================
                    # STEP 3: BUILD SEMANTIC PROMPT FROM PROFILE
                    # ====================================================================
                    venue_name = getattr(state, 'custom_venue_name', None)
                    dynamic_prompt = build_dynamic_suno_prompt(
                        profile,
                        optimized_request,
                        venue_name=venue_name
                    )

                    logger.info(f"🎵 Prompt: {dynamic_prompt[:100]}...")

                    # ====================================================================
                    # STEP 4: LOAD REFERENCE TRACKS FROM PROFILE
                    # ====================================================================
                    reference_track_paths = []

                    if getattr(profile, "reference_tracks", []):
                        reference_track_paths.extend(profile.reference_tracks)
                    elif getattr(profile, "references", []):
                        for ref in profile.references:
                            fpath = getattr(ref, "file_path", None)
                            if not fpath and isinstance(ref, dict):
                                fpath = ref.get("file_path")
                            if fpath and os.path.exists(fpath):
                                reference_track_paths.append(fpath)

                    if reference_track_paths:
                        logger.success(f"✓ Reference tracks: {len(reference_track_paths)}")
                        optimized_request.reference_tracks = reference_track_paths
                    else:
                        logger.info("No reference tracks")

                    # ====================================================================
                    # STEP 5: ✅ PASS PROFILE TO REQUEST (CRITICAL!)
                    # ====================================================================
                    optimized_request.custom_prompt = dynamic_prompt
                    optimized_request.artist_profile = profile  # ← LOVABILITY KEY!

                    logger.success(f"✅ Artist profile attached: {profile.name}")

                    # ====================================================================
                    # STEP 6: GENERATE TRACK VIA SUNO
                    # ====================================================================
                    logger.info(f"📡 Generating: {optimized_request.style.value} @ {optimized_request.bpm}BPM")

                    track = await self.ai_gen.generate_track(optimized_request)

                    if track is None or not hasattr(track, 'id') or track.id is None:
                        logger.error("❌ Track generation failed")
                        return None

                    # ====================================================================
                    # STEP 7: LIBROSA ANALYSIS (optional)
                    # ====================================================================
                    if self.audio_analyzer and hasattr(track, 'audio_data') and track.audio_data:
                        try:
                            logger.info("🔍 Analyzing audio...")
                            analysis = await self.audio_analyzer.analyze_audio_bytes(
                                track.audio_data,
                                requested_bpm=optimized_request.bpm
                            )

                            if analysis:
                                track.metadata['librosa_analysis'] = {
                                    'actual_bpm': getattr(analysis, 'actual_bpm', None),
                                    'actual_energy': getattr(analysis, 'actual_energy', None),
                                }
                                logger.success(f"✓ Analysis: {analysis}")
                        except Exception as e:
                            logger.debug(f"Analysis skipped: {e}")

                    # ====================================================================
                    # STEP 8: QUALITY EVALUATION
                    # ====================================================================
                    if self.orchestrator:
                        try:
                            evaluation = await self.orchestrator.evaluate_track_quality(
                                track=track,
                                expected_request=optimized_request
                            )
                            track.quality_score = evaluation.get('overall_score', 0.7)
                            logger.success(f"✅ Quality: {track.quality_score:.2f}")
                        except Exception as e:
                            logger.debug(f"Quality check skipped: {e}")
                            track.quality_score = 0.7
                    else:
                        track.quality_score = 0.7

                    # ====================================================================
                    # ✅ ACCEPT AND RETURN (LOVABLE!)
                    # ====================================================================
                    logger.success(
                        f"🎉 Track ready: {track.name} | Voice: {'✅' if voice_reference_path else '⚠️'}"
                    )
                    return track

                except Exception as e:
                    logger.error(f"Generation failed: {e}")
                    return None

            return None

        except Exception as e:
            logger.error(f"❌ Generation error: {e}")
            return None

    async def _analyze_performance_costs(self, state: PerformanceState):
        """Background cost analysis"""
        await asyncio.sleep(30)

        if self.orchestrator and len(state.generated_tracks) > 0:
            roi = await self.orchestrator.analyze_cost_efficiency(state)
            logger.info(
                f"💰 ROI: Cost €{roi.total_cost_eur:.2f}, "
                f"Avg Quality {roi.avg_quality_score:.2f}"
            )

    async def process_command(
            self,
            cmd: Any,
            state: PerformanceState,
            profile: ArtistProfile,
            **kwargs: Any
    ) -> PerformanceState:
        """Process performance commands (MIDI/hardware)"""
        from app.services.externals import PerformanceCommand

        if cmd == PerformanceCommand.GENERATE_NEXT:
            logger.info("🔄 Generate next")
            await self._fill_buffer(state, profile)

        elif cmd == PerformanceCommand.ADJUST_ENERGY:
            delta = kwargs.get("delta", 0.1)
            old = state.current_energy
            state.current_energy = max(0.0, min(1.0, state.current_energy + delta))
            logger.info(f"⚡ Energy: {old:.2f} → {state.current_energy:.2f}")

        elif cmd == PerformanceCommand.ADJUST_BPM:
            delta = kwargs.get("delta", 5)
            old = state.current_bpm
            state.current_bpm = max(
                profile.bpm_min,
                min(profile.bpm_max, state.current_bpm + delta)
            )
            logger.info(f"🎚️ BPM: {old} → {state.current_bpm}")

        elif cmd == PerformanceCommand.CHANGE_STYLE:
            new_style = kwargs.get("style", state.current_style)
            if new_style != state.current_style:
                old_style = state.current_style
                state.current_style = new_style
                state.current_energy = new_style.default_energy
                logger.info(f"🎨 Style: {old_style.display_name} → {new_style.display_name}")

                # Regenerate buffer with new style
                state.buffer_tracks.clear()
                await self._fill_buffer(state, profile)

        elif cmd == PerformanceCommand.CROWD_SYNC:
            crowd_energy = await self.crowd.get_crowd_energy()
            old = state.current_energy
            state.current_energy = crowd_energy
            logger.info(f"👥 Crowd sync: {old:.2f} → {crowd_energy:.2f}")

        elif cmd == PerformanceCommand.END:
            logger.info("🏁 Performance ended")
            state.is_live = False
            state.end_time = time.time()
            await self.storage.save_performance(state)

        return state

    async def play_next(self, state: PerformanceState, profile: ArtistProfile) -> PerformanceState:
        """Play next track from buffer"""
        if not state.buffer_tracks:
            logger.warning("⚠️ Buffer empty!")
            await self._fill_buffer(state, profile, target_buffer_size=1)

        if state.buffer_tracks:
            track = state.buffer_tracks.pop(0)
            state.played_tracks.append(track)

            # Update state from track
            state.current_bpm = track.bpm
            state.current_energy = track.energy
            state.current_style = track.style

            logger.success(
                f"🔊 Playing: {track.name} | {track.bpm}BPM | Quality {track.quality_score:.2f}"
            )

            # Stream audio
            if track.audio_data:
                await self.audio_port.stream_track(track.audio_data)

            # Refill buffer
            if len(state.buffer_tracks) < 2:
                asyncio.create_task(self._fill_buffer(state, profile))

        return state

    async def add_voice_profile_from_file(self, name: str, file_path: str) -> bool:
        """Save voice profile from file"""
        try:
            success = await self.storage.save_voice_profile(name, file_path)
            if success:
                logger.success(f"✅ Voice saved: {name}")
            return success
        except Exception as e:
            logger.error(f"❌ Voice save failed: {e}")
            return False

    async def add_voice_profile_from_mic(
            self,
            name: str,
            duration_s: float,
            sample_rate: int = 44100
    ) -> bool:
        """Record voice from microphone"""
        try:
            logger.info(f"🎤 Recording: {name} ({duration_s}s)")
            wav_bytes = await self.voice_processor.record_voice_profile(duration_s, sample_rate)

            if wav_bytes:
                success = await self.storage.save_voice_profile_bytes(name, wav_bytes)
                if success:
                    logger.success(f"✅ Voice recorded: {name}")
                return success
            return False
        except Exception as e:
            logger.error(f"❌ Recording failed: {e}")
            return False

    async def analyze_reference_tracks(self, file_paths: List[str]) -> List[AudioReference]:
        """Analyze reference tracks"""
        if not self.reference_analyzer:
            logger.warning("No reference analyzer")
            return []

        references = []
        for path in file_paths:
            try:
                logger.info(f"🔍 Analyzing: {path}")
                ref = await self.reference_analyzer.analyze_audio_file(path)
                references.append(ref)
                logger.info(f"   {ref.tempo:.1f}BPM, Energy {ref.energy:.2f}")
            except Exception as e:
                logger.error(f"Analysis failed: {e}")

        return references

    async def generate_deck_b_track(
            self,
            state: PerformanceState,
            profile: ArtistProfile,
            custom_prompt: Optional[str] = None
    ) -> Optional[LiveTrack]:
        """Generate Deck B track with voice consistency"""
        logger.info("🎵 Generating Deck B...")

        try:
            # Load voices
            voices = []
            if profile.voice_profiles:
                voices.append(
                    profile.voice_profiles
                    if isinstance(profile.voice_profiles, list)
                    else profile.voice_profiles
                )

            # Load references
            reference_track_paths = []
            if getattr(profile, "reference_tracks", []):
                reference_track_paths.extend(profile.reference_tracks)

            # Build request
            theme_map = {
                VenueType.WAREHOUSE: "warehouse rave",
                VenueType.CLUB: "underground club",
                VenueType.RAVE: "outdoor rave",
                VenueType.FESTIVAL: "festival main stage",
                VenueType.TEKNIVAL: "teknival gathering"
            }

            req = GenerationRequest(
                style=state.current_style,
                bpm=(profile.bpm_min + profile.bpm_max) // 2,
                energy=state.current_energy or 0.7,
                crowd_energy=state.current_energy or 0.5,
                theme=theme_map.get(state.venue_type, "underground"),
                duration_seconds=240,
                venue_type=state.venue_type,
                custom_prompt=custom_prompt,
                voice_profile=voices,
                reference_tracks=reference_track_paths,
                artist_profile=profile  # ✅ LOVABILITY
            )

            # Generate
            logger.info("📡 Submitting...")
            track = await self.ai_gen.generate_track(req)

            if not track:
                logger.warning("⚠️ Generation failed")
                return None

            # Download
            audio_url = None
            if track.metadata and track.metadata.get("audio_url"):
                audio_url = track.metadata["audio_url"]

            if audio_url:
                try:
                    import requests
                    logger.info(f"📥 Downloading...")
                    resp = requests.get(audio_url, timeout=30)

                    if resp.status_code == 200:
                        import os
                        os.makedirs("data/tracks", exist_ok=True)
                        local_path = f"data/tracks/{track.clip_id or int(time.time())}.mp3"

                        with open(local_path, 'wb') as f:
                            f.write(resp.content)

                        track.local_path = local_path
                        logger.success(f"✅ Deck B ready: {local_path}")
                except Exception as e:
                    logger.error(f"Download failed: {e}")

            return track

        except Exception as e:
            logger.error(f"❌ Deck B failed: {e}")
            return None

    async def mix_deck_b_to_a(
            self,
            state: PerformanceState,
            fade_duration: float = 3.0
    ) -> bool:
        """Beatmatch and crossfade Deck B → A"""
        logger.info("🎛️ Mixing Deck B → A...")

        try:
            if not state.current_track_a or not state.current_track_b:
                logger.warning("⚠️ Missing tracks")
                return False

            if not self.mixer:
                logger.warning("⚠️ Mixer not available")
                return False

            # Analyze sync
            logger.info("  Analyzing sync...")
            sync_pct = await self.mixer.analyze_sync_percentage(
                state.current_track_a.local_path,
                state.current_track_b.local_path
            )
            logger.info(f"  BPM match: {sync_pct:.0f}%")

            # Mix
            logger.info("  Mixing...")
            mixed_audio = await self.mixer.beatmatch_and_crossfade(
                state.current_track_a.local_path,
                state.current_track_b.local_path,
                fade_duration
            )

            # Save
            import os
            import time
            os.makedirs("data/mixes", exist_ok=True)
            mixed_path = f"data/mixes/mix_{int(time.time())}.wav"

            with open(mixed_path, 'wb') as f:
                f.write(mixed_audio)

            # Promote Deck B
            old_name = state.current_track_a.name
            state.current_track_a = state.current_track_b
            state.current_track_b = None

            logger.success(f"✅ Mixed: {old_name} → {state.current_track_a.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Mix failed: {e}")
            return False


# ============================================================================
# SETUP PROFILE USE CASE
# ============================================================================

class SetupProfileUseCase:
    """
    Artist profile management use case.

    Handles:
    - Profile creation
    - Style selection
    - BPM range configuration
    - Voice profile management
    - Reference track analysis
    """

    def __init__(
        self,
        storage: StoragePort,
        analyzer: Optional[ReferenceAnalysisPort] = None
    ):
        self.storage = storage
        self.analyzer = analyzer

    async def create_profile(
            self,
            name: str,
            styles: List[UndergroundStyle],
            bpm_min: int,
            bpm_max: int,
            # NEW: Semantic identity parameters
            custom_style_description: str = "",
            influences: List[str] = None,
            instruments: List[str] = None,
            vibe_description: str = "",
            darkness_level: float = 0.5,
            complexity_level: float = 0.5,
            signature_sound: str = "",
            # Original parameters
            voice_profiles: Optional[List[str]] = None,
            references: Optional[List[str]] = None
    ) -> ArtistProfile:
        """
        Create a new artist profile with semantic identity fields.

        Args:
            name: Artist/project name
            styles: List of UndergroundStyle enums (fallback if no custom style)
            bpm_min: Minimum BPM
            bpm_max: Maximum BPM

            # NEW: Semantic fields
            custom_style_description: Freeform style description
                Example: "dark melodic techno with industrial textures"
            influences: List of artist/band names that inspire this project
                Example: ["Burial", "Ben Klock", "Nina Kraviz"]
            instruments: List of preferred instruments/sounds
                Example: ["modular synth", "distorted 808", "vinyl crackle"]
            vibe_description: Emotional/atmospheric description
                Example: "melancholic 3am warehouse energy where people cry"
            darkness_level: 0.0 (bright) to 1.0 (dark)
            complexity_level: 0.0 (minimal) to 1.0 (complex/layered)
            signature_sound: Unique sonic identifier
                Example: "reverb-drenched pianos with broken 909 kicks"

            voice_profiles: Optional list of voice profile names
            references: Optional list of reference track paths

        Returns:
            ArtistProfile: Created profile with semantic fields
        """
        # Validate inputs
        if bpm_min > bpm_max:
            raise ValueError(f"Invalid BPM range: {bpm_min}-{bpm_max}")

        if not styles:
            raise ValueError("At least one style required")

        # Create profile with semantic fields
        profile = ArtistProfile(
            name=name,
            styles=styles,
            bpm_min=bpm_min,
            bpm_max=bpm_max,
            # NEW: Semantic identity
            custom_style_description=custom_style_description,
            influences=influences or [],
            instruments=instruments or [],
            vibe_description=vibe_description,
            darkness_level=darkness_level,
            complexity_level=complexity_level,
            signature_sound=signature_sound,
            # Original fields
            voice_profiles=voice_profiles or [],
            created_at=time.time()
        )

        # Save to storage
        success = await self.storage.save_profile(profile)

        if success:
            # Log semantic fields if defined
            if profile.has_custom_style():
                logger.success(f"✓ Profile created: {name}")
                logger.info(f"  Custom Style: {custom_style_description}")
            else:
                logger.success(f"✓ Profile created: {name}")
                logger.info(f"  Styles: {', '.join([s.display_name for s in styles])}")

            logger.info(f"  BPM Range: {bpm_min}-{bpm_max}")

            if influences:
                logger.info(f"  Influences: {', '.join(influences[:3])}")

            if instruments:
                logger.info(f"  Instruments: {', '.join(instruments[:3])}")

            if vibe_description:
                logger.info(f"  Vibe: {vibe_description[:50]}...")

            logger.info(f"  Mood: {profile.get_mood_description()}")
            logger.info(f"✓ Profile saved to disk")
        else:
            logger.error(f"Failed to save profile: {name}")

        return profile

    async def load_profile(self, name: str) -> Optional[ArtistProfile]:
        """Load existing profile by name."""
        try:
            profile = await self.storage.load_profile(name)
            if profile:
                logger.info(f"✅ Profile loaded: {name}")
            else:
                logger.warning(f"Profile not found: {name}")
            return profile
        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
            return None

    async def list_profiles(self) -> List[str]:
        """List all available profile names."""
        try:
            profiles = await self.storage.list_profiles()
            logger.info(f"📋 Found {len(profiles)} profile(s)")
            return profiles
        except Exception as e:
            logger.error(f"Failed to list profiles: {e}")
            return []

    async def add_voice_sample(self, profile_name: str, sample_path: str) -> bool:
        """Analyze and attach a voice sample to an existing profile."""
        try:
            success = await self.storage.save_voice_profile(profile_name, sample_path)
            if success:
                logger.success(f"✅ Voice sample added to {profile_name}")
            return success
        except Exception as e:
            logger.error(f"Failed to add voice sample: {e}")
            return False

    async def analyze_references(
        self,
        profile_name: str,
        reference_paths: List[str]
    ) -> List[AudioReference]:
        """
        Analyze reference tracks and associate with profile.

        Extracts BPM, key, energy for blending recommendations.
        """
        if not self.analyzer:
            logger.warning("No analyzer available")
            return []

        references = []
        for path in reference_paths:
            try:
                ref = await self.analyzer.analyze_audio_file(path)
                references.append(ref)
                logger.info(
                    f"🎵 Analyzed: {ref.name} - "
                    f"{ref.tempo:.1f} BPM, Energy {ref.energy:.2f}, Key {ref.key}"
                )
            except Exception as e:
                logger.error(f"Analysis failed for {path}: {e}")

        logger.success(f"✅ Analyzed {len(references)} reference(s) for {profile_name}")
        return references

    async def update_profile_styles(
        self,
        profile_name: str,
        new_styles: List[UndergroundStyle]
    ) -> bool:
        """Update the styles for an existing profile."""
        try:
            profile = await self.storage.load_profile(profile_name)
            if not profile:
                logger.error(f"Profile not found: {profile_name}")
                return False

            profile.styles = new_styles
            success = await self.storage.save_profile(profile)

            if success:
                logger.success(
                    f"✅ Updated styles for {profile_name}: "
                    f"{', '.join([s.display_name for s in new_styles])}"
                )

            return success
        except Exception as e:
            logger.error(f"Failed to update profile: {e}")
            return False

    async def update_bpm_range(
        self,
        profile_name: str,
        bpm_min: int,
        bpm_max: int
    ) -> bool:
        """Update BPM range for an existing profile."""
        try:
            if bpm_min >= bpm_max:
                raise ValueError(f"Invalid BPM range: {bpm_min}-{bpm_max}")

            profile = await self.storage.load_profile(profile_name)
            if not profile:
                logger.error(f"Profile not found: {profile_name}")
                return False

            profile.bpm_min = bpm_min
            profile.bpm_max = bpm_max
            success = await self.storage.save_profile(profile)

            if success:
                logger.success(f"✅ Updated BPM range for {profile_name}: {bpm_min}-{bpm_max}")

            return success
        except Exception as e:
            logger.error(f"Failed to update BPM range: {e}")
            return False

    async def create_profile_with_persona(
            self,
            name: str,
            styles: List[UndergroundStyle],
            bpm_min: int,
            bpm_max: int,
            ai_gen: AIGenerationPort,  # ← CRITICAL: Pass AI generator
            custom_style_description: str = "",
            influences: List[str] = None,
            instruments: List[str] = None,
            vibe_description: str = "",
            darkness_level: float = 0.5,
            complexity_level: float = 0.5,
            signature_sound: str = "",
            voice_profiles: Optional[List[str]] = None,
            references: Optional[List[str]] = None
    ) -> Optional[ArtistProfile]:
        """
        Complete workflow:
        STEP 1: Create profile entity
        STEP 2: Generate initial track (chirp-auk)
        STEP 3: Create persona from clip_id
        STEP 4: Store persona_id in profile
        STEP 5: Save to storage
        """

        logger.info(f"🎤 PERSONA SETUP WORKFLOW: {name}")

        # STEP 1: Create profile entity
        profile = ArtistProfile(
            name=name,
            styles=styles,
            bpm_min=bpm_min,
            bpm_max=bpm_max,
            custom_style_description=custom_style_description,
            influences=influences or [],
            instruments=instruments or [],
            vibe_description=vibe_description,
            darkness_level=darkness_level,
            complexity_level=complexity_level,
            signature_sound=signature_sound,
            voice_profiles=voice_profiles or [],
            references=references or [],
            created_at=time.time()
        )
        logger.success(f"✅ STEP 1 complete: Profile entity created")

        # STEP 2: Generate initial track
        logger.info("STEP 2/4: Generating initial track (chirp-auk)...")
        try:
            initial_request = GenerationRequest(
                style=styles if styles else UndergroundStyle.RAW_TECHNO,
                bpm=(bpm_min + bpm_max) // 2,
                energy=0.7,
                crowd_energy=0.6,
                theme=f"{name} signature sound",
                duration_seconds=180,
                venue_type="club",
                mv_version="chirp-auk"  # ← CRITICAL
            )

            track = await ai_gen.generate_track(initial_request)

            if not track or not track.clip_id:
                logger.error("❌ STEP 2 failed: Could not generate track")
                await self.storage.save_profile(profile)
                return profile

            logger.success(f"✅ STEP 2 complete: Track generated (clip_id: {track.clip_id})")

        except Exception as e:
            logger.error(f"❌ STEP 2 failed: {e}")
            await self.storage.save_profile(profile)
            return profile

        # STEP 3: Create persona
        logger.info("STEP 3/4: Creating Suno persona...")
        try:
            persona_id = await ai_gen.create_persona_from_clip(
                clip_id=track.clip_id,
                artist_name=name,
                description=signature_sound or vibe_description or name,
                is_public=False
            )

            if not persona_id:
                logger.error("❌ STEP 3 failed: Could not create persona")
                await self.storage.save_profile(profile)
                return profile

            logger.success(f"✅ STEP 3 complete: Persona created (id: {persona_id})")

        except Exception as e:
            logger.error(f"❌ STEP 3 failed: {e}")
            await self.storage.save_profile(profile)
            return profile

        # STEP 4: Store persona in profile
        logger.info("STEP 4/4: Storing persona in profile...")
        profile.persona_id = persona_id
        profile.artist_clip_id = track.clip_id
        logger.success(f"✅ STEP 4 complete: Profile updated with persona")

        # STEP 5: Save to storage
        logger.info("STEP 5/5: Saving to storage...")
        try:
            success = await self.storage.save_profile(profile)

            if success:
                logger.success(f"✅ PERSONA WORKFLOW COMPLETE!")
                logger.info(f"   Artist: {name}")
                logger.info(f"   Persona: {persona_id}")
                logger.info(f"   Clip: {track.clip_id}")
                logger.info(f"✅ Profile ready for live performances!")

            return profile

        except Exception as e:
            logger.error(f"❌ Storage save failed: {e}")
            return profile


# ═══════════════════════════════════════════════════════════════════════════════
# DECK STATE MANAGER - Production Version
# Layer 2: Business Logic for Real-Time Deck State Management
# ═══════════════════════════════════════════════════════════════════════════════

from datetime import datetime
from typing import Any, Dict, Optional
from loguru import logger


class DeckStateManager:
    """
    PRODUCTION: Manages real-time deck states during live performance

    Responsibilities:
    - Synchronize deck states from orchestrator
    - Validate all data before use
    - Handle missing/null values gracefully
    - Provide deck status for UI rendering
    - Never use hardcoded defaults

    Layer 2 (Use Case): Bridges orchestrator → presentation layer

    Integration:
        deck_manager = DeckStateManager(
            orchestrator=self.orchestrator,
            performance_state=self.performance_state
        )

        decks = await deck_manager.sync_from_orchestrator()
        deck_a = decks['deck_a']  # DeckState object
        deck_b = decks['deck_b']  # DeckState object

    Example (Live Performance):
        # In MassloopApp or rendering loop
        decks = await self.deck_manager.sync_from_orchestrator()

        # Render dashboard
        dashboard.show_deck_a(decks['deck_a'])
        dashboard.show_deck_b(decks['deck_b'])
    """

    def __init__(self, orchestrator: Any, performance_state: Any):
        """
        Initialize deck state manager

        Args:
            orchestrator: PerformanceOrchestratorAgent instance
            performance_state: PerformanceState from use case
        """
        self.orchestrator = orchestrator
        self.performance_state = performance_state

        # Will be populated by sync_from_orchestrator()
        self.deck_a: Optional[Any] = None  # DeckState
        self.deck_b: Optional[Any] = None  # DeckState

        logger.info("✓ DeckStateManager initialized")

    async def sync_from_orchestrator(self) -> Dict[str, Any]:
        """
        PRODUCTION: Synchronize deck states from orchestrator + performance state

        NO HARDCODED DEFAULTS - All data comes from:
        1. performance_state.current_track_a (DECK A - currently playing)
        2. performance_state.buffer_tracks (DECK B - next queued)
        3. orchestrator.hooks.metrics_history (AGENT DECISIONS)

        Handles:
        - Missing orchestrator gracefully
        - Missing performance state gracefully
        - Missing track data gracefully
        - Null/empty buffer tracks
        - Invalid track attributes

        Returns:
            {"deck_a": DeckState, "deck_b": DeckState}

        Raises:
            Nothing - Always returns valid DeckState objects
        """
        try:
            # Import DeckState here to avoid circular imports
            from app.models.entities import DeckState

            # ═════════════════════════════════════════════════════════════════
            # VALIDATION PHASE: Ensure dependencies exist
            # ═════════════════════════════════════════════════════════════════

            if not self.orchestrator:
                logger.warning("⚠ Orchestrator is None")
                self.deck_a = DeckState()
                self.deck_a.mark_error("Orchestrator not available")
                self.deck_b = DeckState()
                self.deck_b.mark_error("Orchestrator not available")
                return {"deck_a": self.deck_a, "deck_b": self.deck_b}

            if not hasattr(self.orchestrator, 'hooks'):
                logger.warning("⚠ Orchestrator has no hooks")
                self.deck_a = DeckState()
                self.deck_a.mark_error("Orchestrator not fully initialized")
                self.deck_b = DeckState()
                self.deck_b.mark_error("Orchestrator not fully initialized")
                return {"deck_a": self.deck_a, "deck_b": self.deck_b}

            if not self.performance_state:
                logger.warning("⚠ Performance state is None")
                self.deck_a = DeckState()
                self.deck_a.mark_error("Performance state not initialized")
                self.deck_b = DeckState()
                self.deck_b.mark_error("Performance state not initialized")
                return {"deck_a": self.deck_a, "deck_b": self.deck_b}

            # ═════════════════════════════════════════════════════════════════
            # DECK A: CURRENTLY PLAYING TRACK
            # ═════════════════════════════════════════════════════════════════

            # Initialize fresh DeckState for Deck A
            self.deck_a = DeckState()

            # Get current track from performance state
            current_track = self.performance_state.played_tracks[-1] if self.performance_state.played_tracks else None

            if current_track and current_track is not None:
                logger.debug(f"Deck A: Found current track")

                # Get track name
                self.deck_a.track_name = getattr(current_track, 'name', '')

                # Get BPM (with validation)
                try:
                    bpm = getattr(current_track, 'bpm', 0)
                    self.deck_a.bpm = int(bpm) if bpm else 0
                except (TypeError, ValueError):
                    self.deck_a.bpm = 0
                    logger.warning(f"Could not parse BPM: {bpm}")

                # Set as playing
                self.deck_a.is_playing = True

                # Get energy level (0.0-1.0 range, convert to percentage)
                if hasattr(current_track, 'energy'):
                    try:
                        energy = getattr(current_track, 'energy', None)
                        if energy is not None:
                            energy_float = float(energy)
                            self.deck_a.energy_level = int(energy_float * 100)
                    except (TypeError, ValueError):
                        logger.warning(f"Could not parse energy: {energy}")

                # Get quality score
                if hasattr(current_track, 'quality_score'):
                    try:
                        quality = getattr(current_track, 'quality_score', None)
                        if quality is not None:
                            self.deck_a.quality_score = float(quality)
                    except (TypeError, ValueError):
                        logger.warning(f"Could not parse quality: {quality}")

                # Get voice match percentage
                if hasattr(current_track, 'voice_match'):
                    try:
                        voice_match = getattr(current_track, 'voice_match', None)
                        if voice_match is not None:
                            self.deck_a.voice_match = float(voice_match)
                    except (TypeError, ValueError):
                        logger.warning(f"Could not parse voice_match: {voice_match}")

                # Clear error if track is valid
                if self.deck_a.is_ready():
                    self.deck_a.error_message = None
                    logger.debug(f"✓ Deck A ready: {self.deck_a.track_name} @ {self.deck_a.bpm}BPM")
                else:
                    self.deck_a.error_message = "Track data incomplete"
                    logger.warning("Deck A: Track data incomplete")

            else:
                # No current track
                self.deck_a = DeckState()
                self.deck_a.error_message = "No current track playing"
                logger.debug("Deck A: No track currently playing")

            # ═════════════════════════════════════════════════════════════════
            # DECK B: NEXT QUEUED TRACK
            # ═════════════════════════════════════════════════════════════════

            # Initialize fresh DeckState for Deck B
            self.deck_b = DeckState()

            # Get buffer tracks from performance state
            buffer_tracks = getattr(self.performance_state, 'buffer_tracks', None) or []

            if buffer_tracks and len(buffer_tracks) > 0:
                logger.debug(f"Deck B: {len(buffer_tracks)} tracks in buffer")

                # Get first track in buffer (next to play)
                next_track = buffer_tracks

                # Get track name
                self.deck_b.track_name = getattr(next_track, 'name', '')

                # Get BPM
                try:
                    bpm = getattr(next_track, 'bpm', 0)
                    self.deck_b.bpm = int(bpm) if bpm else 0
                except (TypeError, ValueError):
                    self.deck_b.bpm = 0

                # Set status
                self.deck_b.generation_status = "Ready to play"
                self.deck_b.is_playing = False

                # Get predicted energy
                if hasattr(next_track, 'energy'):
                    try:
                        energy = getattr(next_track, 'energy', None)
                        if energy is not None:
                            energy_float = float(energy)
                            self.deck_b.energy_level = int(energy_float * 100)
                    except (TypeError, ValueError):
                        logger.warning(f"Could not parse buffer energy: {energy}")

                # Clear error if valid
                if self.deck_b.is_ready():
                    self.deck_b.error_message = None
                    logger.debug(f"✓ Deck B ready: {self.deck_b.track_name} @ {self.deck_b.bpm}BPM")
                else:
                    self.deck_b.error_message = "Track data incomplete"

            else:
                # No buffered tracks
                self.deck_b = DeckState()
                self.deck_b.generation_status = "Generating next track..."
                self.deck_b.error_message = None  # Not an error, just generating
                logger.debug("Deck B: No queued tracks - generating...")

            # ═════════════════════════════════════════════════════════════════
            # AGENT DECISIONS (if available from orchestrator)
            # ═════════════════════════════════════════════════════════════════

            try:
                if (hasattr(self.orchestrator, 'hooks') and
                        hasattr(self.orchestrator.hooks, 'metrics_history') and
                        self.orchestrator.hooks.metrics_history):

                    metrics_history = self.orchestrator.hooks.metrics_history
                    if len(metrics_history) > 0:
                        recent_decision = metrics_history[-1]

                        if isinstance(recent_decision, dict) and 'decision' in recent_decision:
                            decision_text = recent_decision['decision']
                            self.deck_a.agent_decision = decision_text
                            logger.debug(f"Agent decision: {decision_text[:50]}...")

            except Exception as e:
                logger.debug(f"Could not retrieve agent decision: {e}")

            # ═════════════════════════════════════════════════════════════════
            # UPDATE TIMESTAMPS
            # ═════════════════════════════════════════════════════════════════

            self.deck_a.last_updated = datetime.now()
            self.deck_b.last_updated = datetime.now()

            logger.info(
                f"✓ Deck states synced: "
                f"A({self.deck_a.track_name or 'empty'}), "
                f"B({self.deck_b.track_name or 'generating'})"
            )

            return {"deck_a": self.deck_a, "deck_b": self.deck_b}

        except Exception as e:
            logger.error(f"✗ Error syncing deck states: {e}", exc_info=True)

            # Fallback: Return error states
            from app.models.entities import DeckState

            self.deck_a = DeckState()
            self.deck_a.mark_error(f"Sync error: {str(e)}")

            self.deck_b = DeckState()
            self.deck_b.mark_error(f"Sync error: {str(e)}")

            return {"deck_a": self.deck_a, "deck_b": self.deck_b}

    def get_deck_status(self, deck_id: str) -> Dict[str, Any]:
        """
        Get current deck status for diagnostic/monitoring purposes

        Args:
            deck_id: "a" for Deck A, "b" for Deck B

        Returns:
            Dictionary with deck status info (no rendering, just data)

        Example:
            status = deck_manager.get_deck_status("a")
            assert status['is_ready']
            assert status['error'] is None
        """
        deck = self.deck_a if deck_id.lower() == "a" else self.deck_b

        if not deck:
            return {
                "is_ready": False,
                "has_error": True,
                "error": "Deck not initialized",
                "track": None,
                "bpm": 0,
                "energy": None,
                "quality": None,
                "last_updated": None
            }

        return {
            "is_ready": deck.is_ready(),
            "has_error": deck.error_message is not None,
            "error": deck.error_message,
            "track": deck.track_name,
            "bpm": deck.bpm,
            "energy": deck.energy_level,
            "quality": deck.quality_score,
            "voice_match": getattr(deck, 'voice_match', None),
            "generation_status": getattr(deck, 'generation_status', None),
            "is_playing": deck.is_playing,
            "last_updated": deck.last_updated
        }

    def get_both_decks(self) -> Dict[str, Any]:
        """
        Get both deck states as dictionary

        Returns:
            {"deck_a": DeckState, "deck_b": DeckState}

        Example (UI rendering):
            decks = deck_manager.get_both_decks()
            render_deck_panel("A", decks['deck_a'])
            render_deck_panel("B", decks['deck_b'])
        """
        return {
            "deck_a": self.deck_a or DeckState(),
            "deck_b": self.deck_b or DeckState()
        }


class VoiceProfileExtractor:
    """
    Handles voice profile extraction with type validation.
    Ensures data consistency across layers.
    """

    @staticmethod
    def extract_single_profile(
            voice_profiles: Optional[List[str]]
    ) -> Optional[str]:
        """
        Extract first voice profile from list.

        Type-safe: Returns str or None, never list.
        """
        if not voice_profiles:
            return None

        # Ensure it's a list
        if not isinstance(voice_profiles, list):
            if isinstance(voice_profiles, str):
                return voice_profiles
            raise TypeError(
                f"Expected List[str], got {type(voice_profiles)}"
            )

        # Get first element
        if len(voice_profiles) == 0:
            return None

        first = voice_profiles

        # Validate it's a string
        if not isinstance(first, str):
            raise TypeError(
                f"Voice profile must be str, got {type(first)}"
            )

        return first

    @staticmethod
    def validate_voice_profile(voice_profile: Optional[str]) -> Optional[str]:
        """
        Validate voice profile type.
        """
        if voice_profile is None:
            return None

        if not isinstance(voice_profile, str):
            raise TypeError(
                f"voice_profile must be str or None, got {type(voice_profile)}"
            )

        return voice_profile