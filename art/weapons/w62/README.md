# W62 — Outlaw precision-kill reload acceleration

- [Official socket proofs](references/socket-pools.json):13 exact selected weapons,12 randomized+fixed Halfdan-D. Fake reusable650 is not randomized evidence.
- [Mechanics/source boundaries](references/mechanics.json), [effective stat/curve calculations](references/reload-timings.json), [provenance](references/provenance.json).
- `rtk proxy python3 scripts/extract_outlaw_w62.py --verify` is offline/read-only. Full caches/articles/search captures stay private under `/tmp`.
- [Design and authored policies](../../../docs/design/77_W62_무법자_재장전_가속.md), [QA](../../../docs/qa/2026-10-24/w62/README.md).
- [Original HUD sprite composite](../../hud/w62-outlaw/offline-preview.png) is offline art, not a framebuffer. No weapon model/audio changes.
- `implementation.json` records the final current source/JAR snapshot. Historical stage manifests are not rewritten.
