# Massloop — Transparency Spec (Lens #56: The Lens of Transparency)

*Through this prism: the interface must make the AI's hidden state visible. The director cannot trust a co-performer it cannot see. Feedback quality determines whether the human understands and trusts what the AI is doing — especially under the stress of a live set.*

## 1. Back-end (AI intent/state broadcast)
- **WebSocket state channel** (`ws://…/ai-state`): server pushes a structured `AIState` object every tick — current mode (build/breakdown/drop/transition), energy, confidence, and the *trigger* that produced it.
- **Explanation stream**: each autonomous action emits a one-line rationale event, e.g. `{action:"build_drop", why:"energy dropped below 0.3 for 8s", confidence:0.74}`. Plain language, not telemetry.
- **Pending-action queue**: high-impact actions (key change, drop, mute section) enter a `pending[]` list with ETA (ms-until-execute) before the engine commits them. Low-impact edits apply live but are logged.

## 2. Front-end (visible AI intent)
- **Intent banner**: persistent strip showing live mode + the current rationale string.
- **"AI is about to…" preview**: renders the next pending action with countdown and its reason; pulses 2s before auto-execute.
- **Transparent state diff**: side panel showing before→after of what the AI changed (BPM, key, layers) since last beat, so nothing is invisible.
- **Approve / Deny affordance**: tap to confirm or veto any pending high-impact action; deny returns control to director with a brief "AI paused" indicator.

## 3. Transparency recommendation
Default to **preview-then-act for all structural changes** (drops, key shifts, mutes); let only texture/energy micro-edits commit silently but logged. Trust is built by the AI *showing its work* before it commits the set's spine.
