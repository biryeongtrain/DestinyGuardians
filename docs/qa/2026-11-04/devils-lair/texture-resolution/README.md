# Texture resolution reduction — 2026-11-04

User policy: default 4K→2K, close-view assets may retain 2K–4K, distant props/transports prefer 1K; whole distributed ZIP target 250 MB.

## Scope

The actual prior distributed ZIP contained one 4096² PNG: dl_skiff hull. It is now 1024². The existing 1024² emission texture is unchanged. The other 24 large PNGs were 2048² enemy/close-view ability/Ghost textures and remain 2K. No source texture larger than 2K remains in the generated pack. This does not mean runtime atlas sheets are limited to 2K.

Reusable script: scripts/assets/resize_model_texture.py. RGB uses premultiplied Lanczos; binary hull alpha uses nearest coverage to retain its cutout material. Face UVs and logical texture sizes are scaled together; normalized UVs, geometry, rig, six source clips and companion FX are unchanged. Downloads sources are untouched. Matching atlas-routing SHA was updated.

## Checks

- Six relevant JUnit tests and real Gradle jar succeeded (targeted-build.log).
- Final generated pack: 189,433,490 bytes, down from 191,795,054; 60,566,510 bytes below the 250,000,000 target. Embedded final PNG hash and dimensions verified in pack.json.
- Actual isolated Vision client loaded the server pack with resourcePacks:[] and no local overrides. native-1k.png and native-1k-far.png are real framebuffers from command-positioned debug fixtures, not native gameplay or strike-flight acceptance.
- The first Lanczos-alpha version visibly fragmented the hull (first-alpha-failure.png). It was rejected. Retaining binary alpha restored solid hull appearance. At the reference and distant views, the final 1K ship remains recognizable; fine antennas/edges are visibly coarser than 4K, accepted for the user-requested distant prop budget. The gray rectangle in the far capture is an existing test platform in front of the ship, not its texture.
- Runtime blocks atlas changed from previous 8192² to 4096×2048; items atlas remains 16384². This is not an FPS or cross-GPU certification.
- No input lease acquired. Neutral control state recorded. Debug model removed, player returned to safe platform/adventure, temporary far-view block removed. Owned server/client stopped after validation; existing bounded batch awake assertion retained across further strike work.

No whole-project gate repeated for this asset-only edit. The earlier 16 baseline failures and pending complete-strike visual/gameplay acceptance are not resolved by this batch.
