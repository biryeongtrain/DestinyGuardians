# W325 Lionheart (rare, auto rifle Adaptive) — base gnawing_hunger (same contract as W302 Khvostov)

- The Lionheart rip is the Pariah body (identical mesh placement) with green/white camo, a long white slotted brake, a translucent white magazine with black base and a boxed optic with a round rubber eyecup. Body solids are reused from art/weapons/w325/pariah/design.py (handguard, receiver, grip, skeleton stock, magazine) at the rip proportions, without Pariah's sight, deepened rail and magazine/lower-receiver shift; new muzzle, original-depth rail and the scope are authored here.
- Elements: body 74 + magazine 2 = 76. Atlas 512x512, 16 texels/px, kit projection through the Pariah rip map; specials: shroud slots, bore, scope/eyecup inner walls, reticle.
- Fit (gnawing_hunger): moved DZ -0.44 / DY -0.2 from the Pariah frame; grip on the gnawing grip box, magazine top z 2.06..4.06 (gnawing 2.1..4.6), fore-end bottom 9.77 (gnawing 10.0), butt 15.31 (15.44); brake compressed 10% so the muzzle is -9.6 (contract -9.54).
- ADS: scope axis on y 12.785 (W151 sightCenter 12.95 - 0.165, the W302 Khvostov reticle height); real see-through tunnel (0.6 x 0.6 px aperture, 4 px long incl. eyecup); NO_OVERLAY + red emissive reticle (dot + dashes) at the objective end.
- Not verified: in-game hip/ADS (narrow scope tunnel view), reload hand/magazine contact, third person, pack load. Offline kit renders only.

## Detail + style pass (2026-11-05)
- Elements: 76 -> 148 (body 144 + magazine 4); atlas 512x512.
- W30 pixel style: painted three-colour woodland camo (green/dark green/white blobs) on the receiver and scope, white slotted brake, white stock bands, translucent-white magazine, PALETTE 16. Body solids follow the Pariah detail pass (segmented shroud/cover/stock, chamfers, fillets). Scope/eyecup elements renamed sight_scope_* / sight_eyecup_* (hollow sight frame, exempt in adscheck).
- adscheck (main kit): only hollow sight frames (elements named sight_*) exceed the base top profile; without them OK. Sight frames surround the ADS aim point.
- Contract positions (grip, trigger, magazine box/part ids, muzzle, sight line) unchanged. Not verified in game.

## Clean-geometry pass (2026-11-05)
- Elements now 124 (body 117 + magazine 7).
- Chattering-Bone pass: inherits the Pariah fixes (continuous slabs + seam grooves, axis-aligned belly/tail/mag plate, unskewed butt pad); eyecup staves sized exactly.
- Remaining rotations only on genuinely angled parts (grip, trigger hook/guard, stock strut/frame bar, cables, octagon sight/eyecup, 45-degree chamfer strips). adscheck: only sight_* frames above the base profile.

## IDENTITY LIST — Ace / Izanagi pass (2026-11-05)
- 올리브·짙은 녹색·아이보리 위장 총몸
- 하얀 두 포트 소염기와 진회색 슬리브
- 검정 개머리판의 흰 세로 띠
- 아이보리 탄창과 검정 바닥판
- 갈색 교차선 그립·은색 레버와 울
- 상자형 위장 광학장비·검정 원형 접안컵·측면 다이얼
- 진회색 핸드가드의 두 관통 창과 톱니 레일

Source: read-only rip nx/px albedo views and prior side-by-side; face paint uses original material blocks, fastener positions and panel routes. Reference geometry/UV: current Ace 87 cubes and Izanagi 79 cubes read directly; enlarged in-game/atlas reference inspected. No invented lettering was added where it was not legible in the source.

## Identity paint + geometry result (2026-11-05)
- Elements 124 → 132 (body 125 + magazine 7); T20; atlas 512×512.
- Every visible face is explicitly painted through special(): flat source material, 1-texel bright upper edge/dark lower seam, source panel routes, screw/pivot pixels, grip checkering, tinted optic rim; no new projected grime or invented lettering.
- 512-square atlas is retained for Pariah/Lionheart. Cuboid/SUROS/Refrain need 1024×512 at T20 for near-camera receiver/rear/optic detail; the unused atlas half is cropped. PNGs are 15–22 KB each; GPU RGBA storage is 1 MiB or 2 MiB per atlas before mipmaps.
- Real geometry: Pariah/Lionheart's two shroud slots are open through the body; Cuboid has a two-row perforated suppressor cage; Lionheart's white brake has two through ports; SUROS's top rail has nine teeth. Existing real optic windows, stock holes and magazine split remain.
- Coplanar repair: inherited chamfer cap/frame overlaps are resolved with per-face micro-relief of 0.0001×(element ordinal) model px, at most 0.0145 px (under 0.3 texel). Only same-facing intersecting facets recess; opposing joining faces and unrelated boundaries are untouched. A geometric exposed-face intersection audit found 0 remaining coplanar overlaps for all five.
- Validation: kit build; unique elements, positive dimensions, UVs in 0..16, atlas/JSON dimensions; west/east/top/q/front offline renders. Raw adscheck reports the hollow sight_* frames and emissive reticle; excluding those, the solid body fits the base profile. Sampling the exact (x=8,y=eye) forward ray finds no blocking solid except the intended reticle. This is offline geometry evidence, not in-game ADS acceptance.
- Remaining: Minecraft pack load, first/third-person grip, reload/contact, 10–20 weapon display and native FPS were not run by this worker. Cuboid's missing magenta source optic material remains an explicitly reconstructed dark/green material; Refrain's pre-existing compressed hood profile remains an ADS accommodation.

## MATERIAL pass — authoritative surface version (2026-11-05)
The earlier all-face flat identity paint is superseded. Material assignment covers every element with no unmapped fallback; STYLE='material'. References inspected: Beloved/Gnawing Hunger in-game crops and atlases, their W123 source generators, plus this gun's nx/px rip projection cache.

- `green_camo_paint` → paint, RGB (65, 78, 43).
- `ivory_ceramic` → paint, RGB (210, 204, 190).
- `gunmetal` → steel, RGB (57, 61, 60).
- `silver` → metal, RGB (166, 168, 160).
- `polymer` → polymer, RGB (43, 45, 42).
- `grip_brown_wrap` → cloth, RGB (85, 49, 34).
- `rubber` → rubber, RGB (26, 28, 27).
- `ivory_magazine` → polymer, RGB (196, 189, 175).
- `lens` → lens, RGB (53, 101, 119).
- `recess` → dark, RGB (16, 18, 18).
- `emitter` → glow, RGB (225, 52, 40).

- The kit blends source high-pass relief with controlled brushed/fine/stipple/cross/weave texture according to the assigned material. Reconstructed end caps, bevels and remapped optic faces have detail=0; top/bottom relief has reduced weight. These are static RGB cues, not runtime metallic/roughness PBR.
- special() now paints only retained identity accents (small glyphs, narrow frame/paint lines, optic glints, reticle; Lionheart/Refrain use source-derived camo masks with quiet paint grain). Whole-face flat fills and artificial generic panel-border overlays were removed.
- Geometry hash is unchanged from identity pass: 132 elements, body 125 + magazine 7; T20; atlas 512×512.
- Rebuilt with kit; west/east/top/q/front rendered. Exposed coplanar audit remains 0. Raw adscheck saved in review/material_adscheck.txt still lists hollow optics / intended reticle; solid profile and unobstructed aim ray are unchanged by the byte-identical geometry.
- Native pack load, held views, ADS, reload, audio/FPS and 10–20 displays remain unverified. No Gradle or Minecraft run; no commit.

## MATERIAL R2 — latest (2026-11-05)
- Lower receiver/post/well rear: gunmetal; scope mount: silver; barrel: silver; white brake: steel; shroud: dark metal.
- Hand-authored motif: Scope dial tick marks and diagonal brown grip-wrap seams; original 3-colour camo reduced to large regions.
- Paint wear uses explicit substrate colours for Pariah/Cuboid/SUROS; camo paint wear is disabled to avoid reintroducing pepper noise. Source camo stencil only is median/blur cleaned then reduced to 2–3 opaque paint regions; original projection cache remains unchanged.
- Polymer/rubber base luminance delta: 35.70; rubber uses reduced rim and no plate edge.
- Geometry hash unchanged; 132 elements; T20; 512×512 atlas unchanged. Build, JSON/UV/PNG and manifest checks PASS. Raw adscheck log: review/material_r2_adscheck.txt; only prior hollow optic / reticle exceptions remain. Native QA not run.
