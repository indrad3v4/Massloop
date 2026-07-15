# Massloop — Feedback-Lens Fullstack Specs (Schell Lens #57)

Lens #57: feedback is judgment, reward, instruction, encouragement. At every moment ask: *what must the director see/hear now, and what must they feel?* Loop-of-interaction demands instant, legible, juicy return.

## 1. Back-end
- **Structural-change event stream** (WebSocket/SSE): emit one event per AI action — add/remove layer, modulate filter, transpose section, energy ramp. Payload: `action, target, before/after state, confidence, timestamp`.
- **Telemetry bus**: rolling `energy_curve` (0–1), current `section` (intro/drop/break), key/BPM, density. Sampled at 100ms, pushed to front-end.
- **Preview-render service**: low-latency headless render of the *pending* structure change (e.g. 2–4s buffer) returned as audio + analysis so director can audition before committing.
- **Confidence scoring**: model outputs `p(accept)` per change; attached to every event.

## 2. Front-end
- **Live visualiser**: scrolling energy/structure timeline — AI-built shape drawn ahead of the playhead so the director *sees the future structure* forming.
- **Change-toast**: non-blocking per-action card (Δ state) with 1.2s decay; stacked, color-coded by type.
- **Confidence badge**: ring around each toast (green/amber/red) — instant "should I trust this?"
- **Waveform preview**: tap-to-audition the preview-render before the change lands in the live mix.

## 3. Recommendation (feedback-grounded)
Render the AI's **proposed structure as a ghost layer on the timeline 2s before it commits**, not after. Lens #57: feedback must precede the next action — seeing the change *before* it lands turns the director's loop from reactive into authored, eliminating the "did the button do anything?" dead-zone.
