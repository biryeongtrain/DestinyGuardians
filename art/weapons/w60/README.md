# W60 — first optional supported weapon trait

Exact official selected item and randomized trait socket membership for base Auto-Loading Holster.
18 supported /63 selected weapons; enhanced not implemented; no trait granted by default.

- [Data provenance](references/provenance.json)
- [Official socket/plug membership excerpts](references/socket-pools.json)
- [Timing and primary/secondary boundary](references/timing.json)
- [Design and authored policies](../../../docs/design/75_W60_자동_장전_총집.md)
- [QA](../../../docs/qa/2026-10-24/w60/README.md)

Reproduce offline: `rtk proxy python3 -B scripts/extract_holster_w60.py --verify`.
Requires exact pinned private sources under /tmp; never auto-downloads or repairs on verification.
No proprietary full inventory/articles/search responses, credentials or original source media are published here.
No model/texture/animation/audio/HUD layout changes. Real native verification remains separate.
