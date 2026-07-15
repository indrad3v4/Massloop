# Massloop — Channels & Dimensions Spec (Lens #59)

## 1. Back-End
**Ingest services** (independent, timestamped, 20ms jitter tolerance):
- `audio-analysis`: room-mic → onset/energy/tempo/stem-separation (librosa/onset).
- `midi-in`: note-on/off, CC, clock → structural events.
- `gesture`: touch/mouse → screen-space vector + pressure (normalized 0–1).
- `voice`: wake-word + intent ASR (separate bus from room-mic, gated).
- `transport`: key/BPM dial → scalar params.

**Fusion / conflict-resolution model** (`fusion-core`):
- Each channel emits a weighted intent per control axis (structure, energy, timbre, key/BPM).
- Conflict rule: voice vs music-overlap → voice bus mutes room-mic analysis while ASR active (priority=high). MIDI and gesture both map to "energy" → averaged unless one exceeds ±2σ, then it wins. Transport (key/BPM) is authoritative; other channels may *suggest* but never override.
- Output: unified `DirectorIntent` JSON stream → AI hands.

**Dimension schema** (6 axes): structure, energy, timbre, key, bpm, density. Each channel tagged with which axes it drives + confidence 0–1.

## 2. Front-End
- **Channel strip**: 5 LEDs (gesture/audio/MIDI/voice/transport) + per-axis mini-meters showing active drivers.
- **Conflict warning**: amber banner "VOICE vs MUSIC" when overlap detected; auto-mute indicated.
- **Calibration**: 30s setup — tap gesture range, set mic gain threshold, map BPM dial, voice-profile enroll.

## 3. Recommendation
Ship 5 channels but **gate voice behind explicit activation** — running room-mic + voice ASR simultaneously is the only true conflict; isolate them to keep dimensions clean.
