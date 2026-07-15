# Massloop — Virtual Interface Spec (Lens #55: Virtual Interface)

Lens asks: what info is needed that the room doesn't show? When? Deliver it without walling off the world.

## 1. Back-End
- **UI State Model**: `interfaceMode ∈ {live, prep}`; slice `{mode, hudVisible, energy, activeNodes, alerts[]}`; reducers `setMode`, `nudgeHUD`, `pushAlert`.
- **HUD Config Service**: per-mode layout registry keyed by `mode` → `{anchors, components[], contrastTier}`; hot-reloadable; live=4 edge anchors, prep=full canvas.
- **Mode-Dependent Tree**:
  - live → `<LiveRoot>`→`<EdgeHUD>`(energy, transport, panic)+`<HiddenConsole>`
  - prep → `<PrepRoot>`→`<Arranger><Timeline><NodePalette><Inspector>`

## 2. Front-End
- **Live HUD (minimal, edge-anchored)**: bottom=energy/intensity meter + transport; left=next-structure cue; top-right=mute/panic. Zero center content — crowd/room stays visible. Glyph-only 44px targets.
- **Prep Arranger (full)**: centered timeline, AI node graph, mixing inspector; rich mouse/keyboard.
- **Stage Legibility**: WCAG AAA (≥7:1); pure-black backdrop, amber/cyan neon tokens; matte non-glare theme; ≥24px type; auto-dim on idle; haptic+audio confirm per control (juicy continuous feedback).

## 3. Recommendation
**Hide everything by default in live mode.** Show info only on peripheral edges; reveal full controls via deliberate director tap-and-hold (mode switch). The screen must stay a window onto the room, never a wall between director and audience.
