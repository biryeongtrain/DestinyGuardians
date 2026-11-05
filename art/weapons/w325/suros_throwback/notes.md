# W325 SUROS Throwback (uncommon, auto rifle Precision) — base ammit_ar2

- Identity kept: teal SUROS shroud with sloped nose, long upper top rail, open slots into the shroud, side skirts (the flared "ears" seen from the front), grey padded under-handguard, forked flash hider over a separate under-tube, green-lit box reflex (real see-through tunnel), black side cables bowing out to the stock (top-view signature), Omolon-style skeleton grip with trigger opening and thumb-hole frame bar, angular stock with dark top rail, sloped strut and pad.
- Elements: body 56 + magazine 2 = 58 (crossed-box pairs for the round under-tube; yaw-rotated cable segments). Atlas 512x512, 16 texels/px, kit projection (OCC_TOL 0.02 m); specials: sight tunnel inner walls, cables, reticle.
- Map: 25.7 px/m, shifted 0.9 px forward so the grip lands on the ammit grip box; front compressed 7% (muzzle -9.3 vs contract -9.04); stock behind z 11 stretched 18% (butt 15.5, contract 15.92).
- Sight: green frame centre on the ammit ADS eye line y 13.835 (gun lowered 0.74 px; fore-end pads reach y 9.2 vs ammit 9.0, mag bottom 5.6). Sight enlarged 1.2x (window 0.68 x 0.48 px). NO_OVERLAY + green emissive reticle at z 7.2.
- Magazine moved 0.6 px forward (ours 2.0..4.35, ammit 1.4..4.3); frame post widened forward to close the gap.
- Simplified: side skirts are flat plates (rip: curved arcs); internal mechanism seen through the rip's shroud opening is not modelled (open slots instead).
- Not verified: in-game hip/ADS/reload, third person, pack load. Offline kit renders only.

## Detail + style pass (2026-11-05)
- Elements: 58 -> 121 (body 116 + magazine 5); atlas 512x512.
- W30 pixel style: teal/dark/grey blocks, light 1-texel SUROS panel lines, magazine diagonal lines, green-lit sight interior, PALETTE 14; shroud top/mid split into 3 stepped segments, side skirts into 3 plates; chamfers on shroud/nose/handguard/receiver/stock/butt/mag; barrel rings, 3 slanted nose vents, 4 grey handguard pads, ejection-port frame, 3 dark stock windows.
- adscheck (main kit): only hollow sight frames (elements named sight_*) exceed the base top profile; without them OK. Sight frames surround the ADS aim point.
- Contract positions (grip, trigger, magazine box/part ids, muzzle, sight line) unchanged. Not verified in game.

## Clean-geometry pass (2026-11-05)
- Elements now 114 (body 109 + magazine 5).
- Chattering-Bone pass: shroud top/mid continuous with engraved seams; rotated receiver tail replaced by an axis-aligned chamfered step. Skirt plates kept as flush separate plates (shared planes).
- Remaining rotations only on genuinely angled parts (grip, trigger hook/guard, stock strut/frame bar, cables, octagon sight/eyecup, 45-degree chamfer strips). adscheck: only sight_* frames above the base profile.

## IDENTITY LIST — Ace / Izanagi pass (2026-11-05)
- 청록색 SUROS 외장과 은회색 패널 경계
- 두 개로 갈라진 포구와 독립 하부 튜브
- 총몸 양쪽으로 돌아가는 검정 케이블
- 전방 세 사선 통풍선
- 탄창의 밝은 두 평행 사선
- 세 개의 검정 개머리판 홈과 열린 하부 프레임
- 회색 하부 손받침 패드·상부 톱니 레일

Source: read-only rip nx/px albedo views and prior side-by-side; face paint uses original material blocks, fastener positions and panel routes. Reference geometry/UV: current Ace 87 cubes and Izanagi 79 cubes read directly; enlarged in-game/atlas reference inspected. No invented lettering was added where it was not legible in the source.

## Identity paint + geometry result (2026-11-05)
- Elements 114 → 123 (body 118 + magazine 5); T20; atlas 1024×512.
- Every visible face is explicitly painted through special(): flat source material, 1-texel bright upper edge/dark lower seam, source panel routes, screw/pivot pixels, grip checkering, tinted optic rim; no new projected grime or invented lettering.
- 512-square atlas is retained for Pariah/Lionheart. Cuboid/SUROS/Refrain need 1024×512 at T20 for near-camera receiver/rear/optic detail; the unused atlas half is cropped. PNGs are 15–22 KB each; GPU RGBA storage is 1 MiB or 2 MiB per atlas before mipmaps.
- Real geometry: Pariah/Lionheart's two shroud slots are open through the body; Cuboid has a two-row perforated suppressor cage; Lionheart's white brake has two through ports; SUROS's top rail has nine teeth. Existing real optic windows, stock holes and magazine split remain.
- Coplanar repair: inherited chamfer cap/frame overlaps are resolved with per-face micro-relief of 0.0001×(element ordinal) model px, at most 0.0145 px (under 0.3 texel). Only same-facing intersecting facets recess; opposing joining faces and unrelated boundaries are untouched. A geometric exposed-face intersection audit found 0 remaining coplanar overlaps for all five.
- Validation: kit build; unique elements, positive dimensions, UVs in 0..16, atlas/JSON dimensions; west/east/top/q/front offline renders. Raw adscheck reports the hollow sight_* frames and emissive reticle; excluding those, the solid body fits the base profile. Sampling the exact (x=8,y=eye) forward ray finds no blocking solid except the intended reticle. This is offline geometry evidence, not in-game ADS acceptance.
- Remaining: Minecraft pack load, first/third-person grip, reload/contact, 10–20 weapon display and native FPS were not run by this worker. Cuboid's missing magenta source optic material remains an explicitly reconstructed dark/green material; Refrain's pre-existing compressed hood profile remains an ADS accommodation.

## MATERIAL pass — authoritative surface version (2026-11-05)
The earlier all-face flat identity paint is superseded. Material assignment covers every element with no unmapped fallback; STYLE='material'. References inspected: Beloved/Gnawing Hunger in-game crops and atlases, their W123 source generators, plus this gun's nx/px rip projection cache.

- `suros_teal` → paint, RGB (51, 77, 72).
- `steel` → steel, RGB (94, 101, 100).
- `gunmetal` → metal, RGB (53, 58, 58).
- `polymer` → polymer, RGB (34, 38, 37).
- `rubber` → rubber, RGB (27, 29, 29).
- `cable_rubber` → rubber, RGB (34, 38, 37).
- `lens` → lens, RGB (49, 105, 63).
- `recess` → dark, RGB (16, 20, 19).
- `emitter` → glow, RGB (110, 235, 95).

- The kit blends source high-pass relief with controlled brushed/fine/stipple/cross/weave texture according to the assigned material. Reconstructed end caps, bevels and remapped optic faces have detail=0; top/bottom relief has reduced weight. These are static RGB cues, not runtime metallic/roughness PBR.
- special() now paints only retained identity accents (small glyphs, narrow frame/paint lines, optic glints, reticle; Lionheart/Refrain use source-derived camo masks with quiet paint grain). Whole-face flat fills and artificial generic panel-border overlays were removed.
- Geometry hash is unchanged from identity pass: 123 elements, body 118 + magazine 5; T20; atlas 1024×512.
- Rebuilt with kit; west/east/top/q/front rendered. Exposed coplanar audit remains 0. Raw adscheck saved in review/material_adscheck.txt still lists hollow optics / intended reticle; solid profile and unobstructed aim ray are unchanged by the byte-identical geometry.
- Native pack load, held views, ADS, reload, audio/FPS and 10–20 displays remain unverified. No Gradle or Minecraft run; no commit.

## MATERIAL R2 — latest (2026-11-05)
- Mid shroud/bridges and stock strut: exposed gunmetal; sight base/guard: steel; magazine body: black pressed metal.
- Hand-authored motif: Sparse receiver fastener row; two crisp parallel magazine slashes retained.
- Paint wear uses explicit substrate colours for Pariah/Cuboid/SUROS; camo paint wear is disabled to avoid reintroducing pepper noise. Source camo stencil only is median/blur cleaned then reduced to 2–3 opaque paint regions; original projection cache remains unchanged.
- Polymer/rubber base luminance delta: 35.70; rubber uses reduced rim and no plate edge.
- Geometry hash unchanged; 123 elements; T20; 1024×512 atlas unchanged. Build, JSON/UV/PNG and manifest checks PASS. Raw adscheck log: review/material_r2_adscheck.txt; only prior hollow optic / reticle exceptions remain. Native QA not run.
