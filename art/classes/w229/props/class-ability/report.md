# W229 class ability R2 art delta — frozen handoff

Six integration assets are ready in this delta only. `integration-manifest.json` gives exact source paths, target paths, byte sizes and SHA-256. Frozen base three props (9 files) were verified unchanged; Nova and R1 review are separate. No repository code or existing asset was written.

## Placement contract

Use `ItemDisplayContext.NONE` and the centered ItemDisplay coordinate system. Both anchors are model `[8,8,8]`.

- Barrier: canonical bounds `[0,0,0]` to `[16,16,16]`, XY field, normal +Z. Apply scale `[width,height,thickness]` = **[3,2.4,0.18]**. Place at existing center `p + normal*1.35 + (0,1.2,0)` and rotate +Z onto normal. Do not retain the old BlockDisplay corner translation.
- Rift: XZ radius **8 model units** (0.5 block), +Y normal. Scale **[2*radius,1,2*radius]** = **[8,1,8]** for radius4. Place anchor at existing ground+.04 origin. Field plane Y8.018; thin uplift maximum Y8.57, which is .035625 block above anchor at Yscale1. Square plane support X/Z0..16 is clipped to a circle by alpha. Uniform scale8 would incorrectly enlarge height.

The machine-readable contract is `dimensions-anchor.json`. Master owns Java attachment, orientation, scale, collision and damage; these files change art only.

## Design and budget

Barrier: **89 native cube/plane elements**, no triangle adapter. Blue permeable energy plane with bright geometric perimeter, scanning ribs, vertical conduits and base emitters. Rift: **101 native cube/plane elements**, no triangle adapter. White ground field, three segmented flow rings and fine lift traces. Each is below the 1000 cap. Counts are actual exported counts.

No barrier/rift source mesh or source UV was available in this task: both are **self-authored temporary primitive VFX**, not original ripped effects. Textures are authored 2048 RGBA atlases, 2px gutters; the main planes are two-sided. All face UVs are within 0..16. Light emission15 and shadefalse are included. The barrier intentionally contains true zero-alpha apertures as well as partial-alpha pixels; smooth translucency is renderer dependent. Rift markings are static, no flow animation is claimed.

## Validation and preview limits

Assets passed JSON/reference/UV/bounds/element-budget/two-sided-plane checks. Export used the unchanged compile function from installed Blockbench 5.1.4 in an isolated Node context, with native output snapshots and codec hash recorded. This is not a Minecraft parser or game acceptance test. Offline six-view contact sheet uses exact exported faces/UV, actual gameplay scales, alpha and emission in separate headless Blender processes with `--disable-autoexec`. Checker support is preview-only. No live Blender scene or source blend was opened or saved.

`evidence/vfx-3way-contact.png` and per-model PNGs are offline previews, not native screenshots. Native R2 must confirm alpha/cutout/depth behavior, visibility from both sides, local +Z normal and exact center/ground placement. No Gradle/game/Vision/CU/commit was run here. Send native R2 PNG feedback for a new delta if adjustment is necessary.

## Frozen files

`owned-manifest.json` lists this delta ownership. `outputs-manifest.json` hashes all payload and ownership files except itself and SHA256SUMS; `SHA256SUMS` additionally hashes outputs-manifest. Self-reference exclusions avoid cyclic hashes. Do not rerun generation in this frozen folder; later changes must use a new delta directory.
