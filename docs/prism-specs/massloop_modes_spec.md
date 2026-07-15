# Massloop — Lens of Modes Spec (Schell #60)

## 1. Back-end
**Mode state machine:** Single source of truth `mode ∈ {PREP, LIVE, JAM}`. Persisted + broadcast over WebSocket to all clients. Explicit transitions only; no silent drift.
- PREP → LIVE requires an armed "GO LIVE" event.
- LIVE → PREP requires explicit "END SET" (with confirm).
- JAM is a sub-mode of PREP (training); never routes to PA.

**Auto-detection (secondary, advisory only):** Detect LIVE candidates from (a) PA/audio-interface output active & level > threshold, (b) app fullscreen + "stage view" layout, (c) clock inside gig-hours window. Auto-hints surface as a non-blocking prompt: "Detected live context — GO LIVE?" Never auto-switch. Director stays in control.

**Per-mode AI autonomy policy:**
- PREP: AI suggests, human confirms every edit. Latency-tolerant (200ms+).
- JAM: AI explores freely, logs changes, no auto-commit to set.
- LIVE: AI = "hands" — executes director cues at <40ms; prohibited from structural edits (no key/tempo changes, no track add/remove) without explicit director command.

## 2. Front-end
**Unambiguous indicator:** Persistent top-bar pill, color + label + icon — red "LIVE", amber "JAM", blue "PREP". Impossible to misread.
**Mode-specific UI:** LIVE hides arrangement/editing panels, shows cue grid + big transport. PREP shows full arranger. JAM shows sandbox + "discard/save" footer.
**One-tap switch + confirm:** GO LIVE / END SET buttons trigger a full-screen confirm ("You are about to go LIVE — PA will engage"). Prevents mid-set confusion.

## 3. Recommendation
Add a **"rehearsal → live" parity check**: on GO LIVE, verify PA routing, latency budget, and cue map match the last PREP state; block switch with a clear diff if they diverge.
