# W61 — Kill Clip evidence and integration

- Exact selected item hashes only: 12 randomized sockets and Antiope-D's fixed initial socket; 13/63 weapons.
- [Official socket evidence](references/socket-pools.json), [timing and policy boundaries](references/mechanics.json), [private-source hashes](references/provenance.json).
- `rtk proxy python3 scripts/extract_kill_clip_w61.py --verify` reproduces pinned outputs without networking/writes. Full source caches are private under `/tmp`, not redistributed.
- [Runtime/HUD design](../../../docs/design/76_W61_살상_탄창_버프_HUD.md), [QA](../../../docs/qa/2026-10-24/w61/README.md).
- No new sounds or weapon models. HUD sprites are original; [offline preview](../../hud/w61-perks/offline-preview.png) is **not a framebuffer**.
- `implementation.json` records the finalized source snapshot and JAR; previous stage manifests remain historical.
