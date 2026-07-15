# MASSLOOP — PROFIT SPECS (Lens #96: The Lens of Profit)

## 1. Back-End
- **Pricing/tiers:** Free (watermarked, 3 tracks) → Creator $9.99/mo (50 tracks) → Pro $29.99/mo (unlimited + stem export) → Venue $199/mo white-label + 5% door rev-share.
- **Cost control:** (a) **Stem cache** — store generated loops/stems in S3+CDN keyed by style hash; reuse on similar prompts → marginal serve cost ~$0.005. (b) **Hybrid model** — own small local model handles rhythm/structure live; Suno only for premium vocal/melody moments, cutting Suno calls ~70%.
- **Margin:** Free = loss-leader (CAC). Creator gross ~82% (Suno cost $0.40→$0.05/track). Pro ~90%. Venue ~95%.
- **B2B tenancy:** multi-tenant workspaces, per-venue subdomain, isolated usage ledger, metered billing.

## 2. Front-End
- **Paywall/upgrade:** gate stem export + venue-mode; contextual upsell modal on limit hit.
- **Usage meter:** live "tracks left / cost-to-serve" bar per session.
- **Venue-mode toggle:** swaps consumer UI for set-list scheduler + white-label branding.

## 3. One profit-grounded recommendation
Kill the $0.50 one-shot. It bleeds margin (Suno ~$0.40/track). Shift to subscription + cached-stem hybrid: same session costs <$0.05 to serve, converting a ~20% gross *loss* into 80%+ margin and giving predictable MRR for venue B2B.
