# MASSLOOP.AI — STRATEGIC COMMUNICATION & DEV BRIEF (MLB)
Category: Live Music Performance AI Instrument. [web:232]

╔════════════════════════════════════════════════════════════╗
║                   MASSLOOP.AI STRATEGIC FRAMEWORK         ║
╚════════════════════════════════════════════════════════════╝

1) CHALLENGE (Вызов) [Big Idea]
- Real problem isn’t only “prep vs improv”; it’s tool fragmentation on stage: DAW + DJ software + synths + separate AI apps + audio routing → latency, menu-diving, and broken flow. [attached_file:221]
- Performers need one unified instrument that generates, controls, and streams pro‑quality music instantly with hardware responsiveness and zero-latency output. [attached_file:221]

2) MARKET SITUATION (Рыночная ситуация) — TAM / SAM / SOM (€, 2025)
- Definitions: TAM = total addressable market; SAM = serviceable available market; SOM = serviceable obtainable market. [web:232]
- Exchange note: 2025 average 1 USD ≈ 0.8936 EUR (USD→EUR), used here for transparent conversion. [web:281]

- TAM (Global Live Music): $38.58B (2025) ≈ €34.48B (38.58 × 0.8936). Source: Custom Market Insights. [web:249][web:281]
- SAM (Generative AI in Music software/services addressable by live use): $569.7M (2024) ≈ €0.51B, with forecast to $2.79B by 2030 ≈ €2.50B; Massloop addresses the live-performance slice of this market. [web:238][web:281]
- SOM (Year‑1 realistic target): Use SOM as “achievable share” of SAM given focus on EU clubs/festivals and PAYG model; propose 1–2% of SAM as an initial penetration goal pending early adopter traction and venue pilots, per SOM best‑practice framing. [web:232]

— Interpretation:
- The live music pie (TAM) is massive, but modern AI spend (SAM) is the current “bridge” budget pool; Massloop competes for the live segment within AI music budgets where speed/latency and stage-readiness matter. [web:249][web:238]
- Europe is a strong live-events region, supporting focus for early adoption and venue partnerships before broader expansion. [web:249]

3) TARGET AUDIENCE (Целевая аудитория)
- Primary: Electronic live performers (DJs/live acts) who want to improvise with confidence and without technical fragmentation. [attached_file:221]
- Secondary: Venues/festivals wanting continuous, unique programming and lower prep risk from acts. [attached_file:221]
- Psychographic: Freedom‑seekers, improvisers, risk‑takers, tech‑savvy performers who value flow and crowd‑responsive sets. [attached_file:220]

4) INSIGHT (Инсайт)
- Musicians don’t just want “faster prep”; they want liberation from fragmentation: one unified live instrument that generates pro music in <3s, responds to hardware, adapts to crowd, and streams with near‑zero latency. [attached_file:221]
- Big Idea lens: Move audience belief from “AI is for studio” to “AI is my on‑stage infinite instrument,” i.e., from fragmented prep to unified live flow. [attached_file:220]

5) BRAND MESSAGE / ROLE (Сообщение бренда)
- Message: “Massloop.ai turns your laptop into an infinite live instrument—generate, control, and stream without prep, menus, or lag.” [attached_file:220]
- Role: The Liberator—unifies generation, control, and output into a single stage‑ready instrument rather than “another tool in the chain.” [attached_file:221]

──────────────────────────────────────────────────────────────

PRODUCT STRUCTURE (Clean Architecture — minimal, 1 file per layer)
- Golden Rule: Talk inwards with simple structures; talk outwards via interfaces. [attached_file:221]
- Hard bounds: main.py + src/ with one file per layer to avoid sprawl and force clarity. [attached_file:221]

Project tree:
.
├── main.py  # CLI Performance Mode entrypoint (big text, hotkeys, zero-typing) [attached_file:221]
└── src/
    ├── layer1_entities.py        # Domain entities: Profile, VoiceProfile, TrackRef, SetState (no I/O) [attached_file:221]
    ├── layer2_usecases.py        # Use cases: StartSet, GenerateNext, AddVocals, CrowdSync, AdjustEnergy [attached_file:221]
    ├── layer3_interfaces.py      # Abstract ports: AudioOutPort, AIGenPort, VoiceClonePort, CrowdSensePort [attached_file:221]
    ├── layer4_adapters.py        # Implementations: SunoGenAdapter, DeepSeekCtlAdapter, PyAudioOut, OpenCVSense [attached_file:221]
    └── layer5_frameworks.py      # CLI/Rich view + keybindings + DI wiring (compose ports/adapters) [attached_file:221]

Notes:
- Entities and use cases never import adapter libs; they only depend on interfaces to keep the core pure and testable. [attached_file:221]
- All external details (audio, models, webcam, cookies/keys) live in adapters and are injected at startup. [attached_file:221]

DEVELOPMENT TASKS (Big Idea → Dev)
- Background: Performers lose flow to menus, routing, and tool‑switching mid‑set; “flow death” is the opponent. [attached_file:220]
- Communication Objective: Prove “one‑key next track in <3s” and “zero‑typing performance window” on a venue system. [attached_file:220]
- Target Audience: Bookable electronic acts and venues hungry for fresh, unique sets nightly. [attached_file:220]
- Message: “Massive loops. Massive freedom.” Live, unified, instant. [attached_file:220]
- Brand Role: Liberator—stage‑ready AI instrument, not a studio assistant. [attached_file:220]

PAYMENTS & UNIT ECONOMICS (No free tier; PAYG tokens, x5 markup)
- Model: Basic Pay‑As‑You‑Go—resell generation tokens at 5× provider cost for simple, transparent unit economics. [attached_file:220]
- Rationale: Aligns cost with minutes generated in live settings; scales linearly with usage; fits SOM capture via low‑friction onboarding. [attached_file:232]

MILESTONES (Stage‑proof outcomes)
- M0: 3‑second “Next” hotkey under venue load; zero‑typing performance window; stable audio stream. [attached_file:221]
- M1: Voice add‑on and reference‑track conditioning (BPM/key/energy analysis); buffer auto‑fill state machine. [attached_file:221]
- M2: Hardware mapping (MIDI) to energy/BPM/style without touching keyboard; crowd‑energy loop with safe bounds. [attached_file:221]

RISK NOTES
- Model/API downtime → prebuffer ≥3 tracks and local fallback patterns to avoid silence. [attached_file:221]
- Latency spikes → larger audio buffer floor + adapter backoff; warn in UI if <2 tracks buffered. [attached_file:221]
- Quality variance → Direction prompts from entities + ref‑track features (BPM/key) for more stable next‑up. [attached_file:221]

METRICS THAT MATTER
- Time‑to‑next (T2N) p95 < 3s, buffer never hits 0, crowd‑energy lift after transitions, and token revenue/act/night. [attached_file:221]

MARKET APPENDIX (TAM/SAM/SOM details)
- TAM: Global live music revenue ≈ €34.48B in 2025 (USD 38.58B × 0.8936), live concerts/festivals worldwide. [web:249][web:281]
- SAM: Generative AI in music market ≈ €0.51B (2024) with path to ≈ €2.50B by 2030; Massloop’s serviceable slice is the live‑performance segment. [web:238][web:281]
- SOM: Start with 1–2% of SAM as achievable near‑term capture based on SOM methodology; refine with early venue pilots. [web:232]

SOURCES
- TAM/SAM/SOM definitions & framing. [web:232]
- Global live music revenues (2025). [web:249]
- Generative AI in music (2024–2030). [web:238]
- USD→EUR average rate reference (2025). [web:281]
- Clean architecture communication rule (“talk inwards with simple structures, outwards via interfaces”). [attached_file:221]
