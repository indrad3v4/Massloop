# Massloop — Lens #82 (Inner Contradiction) Spec

Purpose: HUMAN DIRECTOR stays in control and delivers a great live set; AI handles grunt structure/energy. The hero is the performer. Any feature that makes the AI the hero, or removes director agency, is an inner contradiction.

## 1. Back-end guardrails
- **No autonomous structural mutation.** AI may propose key/section/energy changes only as *pending suggestions* (staged state). Commit requires an explicit director command (`/accept` / tap). Disable any "auto-arange", "auto-mix", or energy-drift daemon by default; require opt-in per session.
- **Hero-framing policy (enforced in event log):** Every system action is attributed as "Director commanded" vs "AI suggested — pending." AI never logs an action as if it performed the show. Telemetry labels the performer as subject, not the model.
- **Override supremacy:** Any human input within 250ms overrides in-flight AI changes; AI cannot re-assert during a manual gesture.

## 2. Front-end contradiction audit
- **Contradiction A:** HUD "AI is performing" status ticker → implies AI is the act. Fix: relabel to "AI assistant: idle / suggestion ready." Hide AI chrome during playback.
- **Contradiction B:** Auto-cue toggle on by default → set runs without director. Fix: default OFF; only a lit "DIRECTOR LIVE" indicator confirms control.
- **Contradiction C:** Cluttered analyzer panels compete with stage awareness. Fix: collapse to one glanceable "energy/key now" strip; bury detail under tap.
- **Hero copy:** "You're running the show. AI handles the busywork." / "Your call — AI drafts, you direct."

## 3. One recommendation
Remove the "Smart Auto-Mode" entirely. It defeats the product's purpose (director control) by design; its value is fully covered by opt-in, director-commanded suggestions.
