# Massloop — Lens #53: The Lens of Control
*When the performer uses the interface, does it do what is expected? Do they feel they drive the outcome?*

**1. Back-end (real-time control)**
- WS `/ws/control`: bidir commands `set_energy`, `set_section`, `trigger_transition`, `override_ai`, `undo`, `redo`.
- Command queue: FIFO, single-threaded executor. AI applies only queued commands — no autonomous change without one. Makes "does it do what's expected?" a YES.
- Deterministic response: audio params = pure fn of (command log, state). Same command → same result, no drift.
- Latency budget: UI ack <50ms (echo pre-audio); audio change <200ms (next buffer). Breach = degrade, never guess.

**2. Front-end (control surface)**
- 1:1 mapping: Energy slider→energy, Section button→section. No hidden remap; control does what its label says.
- Predictable feedback: show *effective* value, not last-sent.
- Override affordances: "AI Auto" toggle + "AI/HUMAN" indicator so performer always knows who drives. Off = human owns structure.
- Undo/redo: N-step structure history, instant revert.

**3. Recommendation**
Make undo/redo first-class and instant. A live performer's deepest control fear is an unrecoverable AI change; versioned snapshots let them revert mid-set with zero risk — directly reinforcing the feeling of power and control.
