# W325 Cuboid ARu (rare, auto rifle Precision) — base ammit_ar2

- Identity kept: maroon/tan-worn Omolon-era shroud with the long see-through top slot and side knob, tan end cap, separate maroon fore-grip block with black pad, tan front sleeve + collar, perforated suppressor with a real bore, boxy reflex sight (real see-through tunnel), skeleton pistol grip with trigger-guard opening and the triangular thumb-hole frame bar, curved-rib magazine with flared base, adjustable maroon stock with sloped lower plate and dark pad.
- Elements: body 51 + magazine 2 = 53 (crossed-box pairs for the round suppressor/collar; no triangle adapters). Atlas 512x512, 16 texels/px, kit projection (OCC_TOL 0.035 m so side relief up to ~0.8 px still projects).
- Map: 23.97 px/m, shifted 1.16 px forward so the grip lands on the ammit grip box; suppressor front compressed 7% (muzzle -9.5, contract -9.04, 0.46 px longer); stock behind z 11 stretched 15% (butt 15.25, contract 15.92 -> 0.67 px short).
- Sight: rip window centre is already on the ammit ADS eye line y 13.835 at this height (no riser). Sight enlarged 1.25x about the window centre (window 0.72 x 0.56 px). The rip's sight material is missing (renders magenta); grade() maps magenta texels to dark gunmetal. NO_OVERLAY + green emissive reticle (dot + dashes) at z 7.6.
- Magazine moved 0.6 px forward (ammit mag top z 1.4..4.3, ours 2.12..4.35); the frame post behind it is widened forward to close the gap.
- Not verified: in-game hip/ADS (reticle centring relies on the derived eye line), reload hand/magazine contact, third person, pack load. Offline kit renders only.

## Detail + style pass (2026-11-05)
- Elements: 53 -> 113 (body 109 + magazine 4); atlas 512x512.
- W30 pixel style: maroon/tan/dark blocks (tan sleeve/end cap/stock strip, black pad ribs), PALETTE 16, perforation texels on the suppressor, tan wear lines, receiver vent; shroud top/mid and stock bar split into 3 stepped segments; chamfers on sleeve/shroud/receiver/magwell/pad/butt; clamp bands, dial, 4 fore-grip ribs, mag ribs. Magenta sight texture no longer used (flat gunmetal).
- adscheck (main kit): only hollow sight frames (elements named sight_*) exceed the base top profile; without them OK. Sight frames surround the ADS aim point.
- Contract positions (grip, trigger, magazine box/part ids, muzzle, sight line) unchanged. Not verified in game.

## Clean-geometry pass (2026-11-05)
- Elements now 105 (body 101 + magazine 4).
- Chattering-Bone pass: shroud/stock segments merged into continuous chamfered slabs with engraved seams; rotated receiver tail (crossed the receiver top) replaced by two axis-aligned chamfered steps; rotated butt hook replaced by an axis step.
- Remaining rotations only on genuinely angled parts (grip, trigger hook/guard, stock strut/frame bar, cables, octagon sight/eyecup, 45-degree chamfer strips). adscheck: only sight_* frames above the base profile.

## IDENTITY LIST — Ace / Izanagi pass (2026-11-05)
- 적갈색 외장과 크림색 가는 패널 테두리
- 전방 황갈색 슬리브와 적갈색 고정 밴드
- 두 줄로 뚫린 긴 검정 소음기 케이지
- 긴 상부 개방 창과 적갈색 이중 핸드가드
- 검정 골격 손잡이·하부 프레임
- 회색 리브가 있는 검정 탄창
- 총몸 원형 조절부와 크림색 피벗 디테일

Source: read-only rip nx/px albedo views and prior side-by-side; face paint uses original material blocks, fastener positions and panel routes. Reference geometry/UV: current Ace 87 cubes and Izanagi 79 cubes read directly; enlarged in-game/atlas reference inspected. No invented lettering was added where it was not legible in the source.

## Identity paint + geometry result (2026-11-05)
- Elements 105 → 145 (body 141 + magazine 4); T20; atlas 1024×512.
- Every visible face is explicitly painted through special(): flat source material, 1-texel bright upper edge/dark lower seam, source panel routes, screw/pivot pixels, grip checkering, tinted optic rim; no new projected grime or invented lettering.
- 512-square atlas is retained for Pariah/Lionheart. Cuboid/SUROS/Refrain need 1024×512 at T20 for near-camera receiver/rear/optic detail; the unused atlas half is cropped. PNGs are 15–22 KB each; GPU RGBA storage is 1 MiB or 2 MiB per atlas before mipmaps.
- Real geometry: Pariah/Lionheart's two shroud slots are open through the body; Cuboid has a two-row perforated suppressor cage; Lionheart's white brake has two through ports; SUROS's top rail has nine teeth. Existing real optic windows, stock holes and magazine split remain.
- Coplanar repair: inherited chamfer cap/frame overlaps are resolved with per-face micro-relief of 0.0001×(element ordinal) model px, at most 0.0145 px (under 0.3 texel). Only same-facing intersecting facets recess; opposing joining faces and unrelated boundaries are untouched. A geometric exposed-face intersection audit found 0 remaining coplanar overlaps for all five.
- Validation: kit build; unique elements, positive dimensions, UVs in 0..16, atlas/JSON dimensions; west/east/top/q/front offline renders. Raw adscheck reports the hollow sight_* frames and emissive reticle; excluding those, the solid body fits the base profile. Sampling the exact (x=8,y=eye) forward ray finds no blocking solid except the intended reticle. This is offline geometry evidence, not in-game ADS acceptance.
- Remaining: Minecraft pack load, first/third-person grip, reload/contact, 10–20 weapon display and native FPS were not run by this worker. Cuboid's missing magenta source optic material remains an explicitly reconstructed dark/green material; Refrain's pre-existing compressed hood profile remains an ADS accommodation.

## MATERIAL pass — authoritative surface version (2026-11-05)
The earlier all-face flat identity paint is superseded. Material assignment covers every element with no unmapped fallback; STYLE='material'. References inspected: Beloved/Gnawing Hunger in-game crops and atlases, their W123 source generators, plus this gun's nx/px rip projection cache.

- `maroon_paint` → paint, RGB (107, 62, 65).
- `sand_anodized` → metal, RGB (158, 143, 119).
- `steel` → steel, RGB (79, 83, 83).
- `gunmetal` → metal, RGB (49, 53, 55).
- `polymer` → polymer, RGB (36, 38, 37).
- `rubber` → rubber, RGB (26, 28, 27).
- `optic` → metal, RGB (47, 52, 53).
- `lens` → lens, RGB (58, 106, 82).
- `recess` → dark, RGB (17, 19, 20).
- `emitter` → glow, RGB (110, 235, 95).

- The kit blends source high-pass relief with controlled brushed/fine/stipple/cross/weave texture according to the assigned material. Reconstructed end caps, bevels and remapped optic faces have detail=0; top/bottom relief has reduced weight. These are static RGB cues, not runtime metallic/roughness PBR.
- special() now paints only retained identity accents (small glyphs, narrow frame/paint lines, optic glints, reticle; Lionheart/Refrain use source-derived camo masks with quiet paint grain). Whole-face flat fills and artificial generic panel-border overlays were removed.
- Geometry hash is unchanged from identity pass: 145 elements, body 141 + magazine 4; T20; atlas 1024×512.
- Rebuilt with kit; west/east/top/q/front rendered. Exposed coplanar audit remains 0. Raw adscheck saved in review/material_adscheck.txt still lists hollow optics / intended reticle; solid profile and unobstructed aim ray are unchanged by the byte-identical geometry.
- Native pack load, held views, ADS, reload, audio/FPS and 10–20 displays remain unverified. No Gradle or Minecraft run; no commit.

## MATERIAL R2 — latest (2026-11-05)
- Lower receiver/tail, bridge interiors, sight base and guard: exposed steel/gunmetal; magazine body: black pressed metal.
- Hand-authored motif: Four 1-texel magazine flute edges and fine sleeve cooling bands; narrow cream panel lines retained.
- Paint wear uses explicit substrate colours for Pariah/Cuboid/SUROS; camo paint wear is disabled to avoid reintroducing pepper noise. Source camo stencil only is median/blur cleaned then reduced to 2–3 opaque paint regions; original projection cache remains unchanged.
- Polymer/rubber base luminance delta: 35.70; rubber uses reduced rim and no plate edge.
- Geometry hash unchanged; 145 elements; T20; 1024×512 atlas unchanged. Build, JSON/UV/PNG and manifest checks PASS. Raw adscheck log: review/material_r2_adscheck.txt; only prior hollow optic / reticle exceptions remain. Native QA not run.
