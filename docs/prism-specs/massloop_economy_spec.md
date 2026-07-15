# Massloop — Economy-Lens Fullstack Spec (Lens #46: Economy)

## 1. BACK-END
**Data model:** `User(tier)`, `Asset(type: signature_sound|energy_profile|set, owner, price, license: buy|per_stream)`, `Subscription(tier: Free|Performer|Headliner)`, `TradeListing`, `CreditLedger`, `RoyaltySplit`.
**Currencies (Schell: specialized currency):** real $ (tiers) + earned **Loop Credits** + **Royalty Tokens** (paid to asset owners on reuse).
**APIs:** `/tiers`, `/credits/earn` (live-minutes + audience tips→credits), `/marketplace/list|buy|license|fork`, `/sets/share|fork`, `/royalties/settle`.
**Services:** credit minting on performance + tips; royalty engine pays owners when their sets/sounds are reused; marketplace escrow; tier-gated generation quota.

## 2. FRONT-END
- **Your Library** panel: owned/created assets (lock-in; assets live in Massloop).
- **Trade Board**: buy / license-per-stream / fork signature sounds, energy profiles, full sets.
- **Tier Badge + Credit/Royalty HUD** in performer view.
- **Live Tip Jar** widget: audience sends real $ → performer credits during set.
- **Royalty feed**: shows earnings when others perform your assets.

## 3. ECONOMY-LENS RECOMMENDATION
Use a **dual specialized currency** (Schell): real $ for recurring tiers, earned Loop Credits + Royalty Tokens for in-app trade. Pay creators automatically every time their set/sound is reused live → meaningful earn/spend choices, free value flow, and structural lock-in: performers' reputations and income depend on assets that only exist inside Massloop.
