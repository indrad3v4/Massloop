# Massloop — Physical Interface Spec (Lens #54: Physical Interface)

## 1. Back-End
- **Input adapters**: MIDI (class-compliant over USB/wireless), OSC (TouchOSC/phone), and a WebSocket relay for web controllers. One normalized `ControlEvent{device, control, value, ts}` stream into FastAPI.
- **Device-profile model**: YAML/DB record per device (Akai APC, Launchpad, phone, touchpad) mapping raw CC/note → semantic action (intensity, drop, key, add-layer, cue-AI). Hot-swappable; performer picks profile pre-show.
- **Latency budget**: hardware→adapter <5 ms, adapter→FastAPI <10 ms (local loopback), FastAPI→AI command <50 ms. Target end-to-end physical-to-audible ≤120 ms; reject/stage any hop >30 ms.

## 2. Front-End (stage surface)
- **Surface**: 4×4 giant velocity pads (quantize/drop/energy), 4 rotary encoders (intensity, tempo, texture, crowd), 2 faders (structure, AI-autonomy). Mirrors mapped semantics; no hidden modes.
- **Mapping config**: visual editor binds device control → AI command; saved per show. Live "what-does-this-do" label overlay.
- **Tactile feedback**: pads light + haptic pulse on trigger; encoders show LED ring; screen-free operation so eyes stay on crowd.

## 3. Recommendation
Use a **dedicated MIDI grid controller (e.g. Novation Launchpad/APC40) as the primary stage interface**, not a laptop/phone. Tactile, eyes-up, fail-safe, zero-boot-risk; map AI "hands" (structure/energy) to pads, "director" intent (autonomy) to encoders. Reserve phone/OSC as backup only.
