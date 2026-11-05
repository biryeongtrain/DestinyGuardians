# W325 Refrain-23 (rare, auto rifle Adaptive) — base gnawing_hunger (W302 Khvostov contract)

- Identity kept: long pale-camo hood with ochre band over a dark lower body, see-through slot along the hood top, small top rail and blue-lens reflex, long black fore-end pad panel, chinned nose with a squared muzzle (real bore), pale receiver with release button, raked dark grip, translucent pale magazine with a dark spine, angular dropped stock with dark pad.
- Elements: body 39 + magazine 2 = 41 (no triangle adapters). Atlas 512x512, 16 texels/px, kit projection (OCC_TOL 0.02 m).
- Map: 25.4 px/m with the muzzle on the contract; grip, trigger and magazine (1.96..4.6 vs gnawing 2.1..4.6) land on the gnawing boxes without moves. Deliberate: everything above y 11 (hood, rail, sight) compressed to 66% height and the gun lowered 0.25 px so the hood top is 12.55 and the sight window is on the gnawing ADS eye line y 12.785; front of z -6 compressed 7% (muzzle -9.3 vs -9.54); stock behind z 11 stretched 18% (butt 15.05 vs 15.44).
- Fore-end bottom 9.4 (gnawing 10.0) — the support hand may sit slightly inside the pad panel.
- Sight: small reflex enlarged ~1.25x (window 0.48 x 0.52 px), NO_OVERLAY + red emissive reticle at z 6.75.
- Simplified: hood side flare drawn as two thin skirts; hood curvature is a stepped roof + front slope.
- Not verified: in-game hip/ADS, reload hand/magazine contact, third person, pack load. Offline kit renders only.

## Detail + style pass (2026-11-05)
- Elements: 41 -> 119 (body 113 + magazine 6); atlas 512x512.
- ADS fix: hood compressed to 53% above y 10.6 and the stock to 92% about y 8.1 (hood top 12.12, stock top 11.42), hood stops at z 8; only the hollow sight frame (sight_*) is above the base profile. W30 pixel style: pale hood with large sage camo patches, ochre band/skirts, dark lower body, black ribbed pad panel, pale magazine/stock drop, PALETTE 14; hood roof and handguard split into stepped segments, chamfers everywhere, rail lugs, button cap, grip panel, mag window.
- adscheck (main kit): only hollow sight frames (elements named sight_*) exceed the base top profile; without them OK. Sight frames surround the ADS aim point.
- Contract positions (grip, trigger, magazine box/part ids, muzzle, sight line) unchanged. Not verified in game.

## Clean-geometry pass (2026-11-05)
- Elements now 112 (body 106 + magazine 6).
- Chattering-Bone pass: hood roof and handguard continuous with engraved seams; shallow rotated hood-nose slab replaced by an axis-aligned chamfered step; 58-degree stock drop edge and the nose chin slab replaced by axis-aligned chamfered steps.
- Remaining rotations only on genuinely angled parts (grip, trigger hook/guard, stock strut/frame bar, cables, octagon sight/eyecup, 45-degree chamfer strips). adscheck: only sight_* frames above the base profile.

## IDENTITY LIST — Ace / Izanagi pass (2026-11-05)
- 아이보리·세이지색 긴 상부 외장
- 상부 측면의 황토색 긴 띠
- 차콜색 하부 총몸·검정 리브 손받침
- 아이보리 탄창과 어두운 앞쪽 스파인
- 계단식 하강 개머리판과 검정 뒤 패드
- 푸른색 반사식 조준기 테두리
- 원형 탄창 해제 버튼과 총몸 긴 검정 홈

Source: read-only rip nx/px albedo views and prior side-by-side; face paint uses original material blocks, fastener positions and panel routes. Reference geometry/UV: current Ace 87 cubes and Izanagi 79 cubes read directly; enlarged in-game/atlas reference inspected. No invented lettering was added where it was not legible in the source.

## Identity paint + geometry result (2026-11-05)
- Elements 112 → 112 (body 106 + magazine 6); T20; atlas 1024×512.
- Every visible face is explicitly painted through special(): flat source material, 1-texel bright upper edge/dark lower seam, source panel routes, screw/pivot pixels, grip checkering, tinted optic rim; no new projected grime or invented lettering.
- 512-square atlas is retained for Pariah/Lionheart. Cuboid/SUROS/Refrain need 1024×512 at T20 for near-camera receiver/rear/optic detail; the unused atlas half is cropped. PNGs are 15–22 KB each; GPU RGBA storage is 1 MiB or 2 MiB per atlas before mipmaps.
- Real geometry: Pariah/Lionheart's two shroud slots are open through the body; Cuboid has a two-row perforated suppressor cage; Lionheart's white brake has two through ports; SUROS's top rail has nine teeth. Existing real optic windows, stock holes and magazine split remain.
- Coplanar repair: inherited chamfer cap/frame overlaps are resolved with per-face micro-relief of 0.0001×(element ordinal) model px, at most 0.0145 px (under 0.3 texel). Only same-facing intersecting facets recess; opposing joining faces and unrelated boundaries are untouched. A geometric exposed-face intersection audit found 0 remaining coplanar overlaps for all five.
- Validation: kit build; unique elements, positive dimensions, UVs in 0..16, atlas/JSON dimensions; west/east/top/q/front offline renders. Raw adscheck reports the hollow sight_* frames and emissive reticle; excluding those, the solid body fits the base profile. Sampling the exact (x=8,y=eye) forward ray finds no blocking solid except the intended reticle. This is offline geometry evidence, not in-game ADS acceptance.
- Remaining: Minecraft pack load, first/third-person grip, reload/contact, 10–20 weapon display and native FPS were not run by this worker. Cuboid's missing magenta source optic material remains an explicitly reconstructed dark/green material; Refrain's pre-existing compressed hood profile remains an ADS accommodation.

## MATERIAL pass — authoritative surface version (2026-11-05)
The earlier all-face flat identity paint is superseded. Material assignment covers every element with no unmapped fallback; STYLE='material'. References inspected: Beloved/Gnawing Hunger in-game crops and atlases, their W123 source generators, plus this gun's nx/px rip projection cache.

- `ivory_paint` → paint, RGB (226, 210, 196).
- `ochre_paint` → paint, RGB (154, 145, 71).
- `lower_metal` → metal, RGB (75, 74, 65).
- `well_alloy` → metal, RGB (121, 117, 97).
- `polymer` → polymer, RGB (39, 41, 37).
- `rubber` → rubber, RGB (25, 28, 26).
- `ivory_magazine` → polymer, RGB (218, 206, 192).
- `steel` → steel, RGB (160, 162, 150).
- `lens` → lens, RGB (45, 73, 130).
- `recess` → dark, RGB (15, 19, 17).
- `emitter` → glow, RGB (225, 52, 40).

- The kit blends source high-pass relief with controlled brushed/fine/stipple/cross/weave texture according to the assigned material. Reconstructed end caps, bevels and remapped optic faces have detail=0; top/bottom relief has reduced weight. These are static RGB cues, not runtime metallic/roughness PBR.
- special() now paints only retained identity accents (small glyphs, narrow frame/paint lines, optic glints, reticle; Lionheart/Refrain use source-derived camo masks with quiet paint grain). Whole-face flat fills and artificial generic panel-border overlays were removed.
- Geometry hash is unchanged from identity pass: 112 elements, body 106 + magazine 6; T20; atlas 1024×512.
- Rebuilt with kit; west/east/top/q/front rendered. Exposed coplanar audit remains 0. Raw adscheck saved in review/material_adscheck.txt still lists hollow optics / intended reticle; solid profile and unobstructed aim ray are unchanged by the byte-identical geometry.
- Native pack load, held views, ADS, reload, audio/FPS and 10–20 displays remain unverified. No Gradle or Minecraft run; no commit.

## MATERIAL R2 — latest (2026-11-05)
- Top rail and rail lugs: brighter steel; lower receiver and well alloy separated in luminance. Original pale/ochre painted exterior retained.
- Hand-authored motif: Eight 1-texel forepad groove edges and a 1-texel release-button ring; original 2-colour hood camo reduced to large regions.
- Paint wear uses explicit substrate colours for Pariah/Cuboid/SUROS; camo paint wear is disabled to avoid reintroducing pepper noise. Source camo stencil only is median/blur cleaned then reduced to 2–3 opaque paint regions; original projection cache remains unchanged.
- Polymer/rubber base luminance delta: 35.70; rubber uses reduced rim and no plate edge.
- Geometry hash unchanged; 112 elements; T20; 1024×512 atlas unchanged. Build, JSON/UV/PNG and manifest checks PASS. Raw adscheck log: review/material_r2_adscheck.txt; only prior hollow optic / reticle exceptions remain. Native QA not run.
