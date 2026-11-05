# W325 Pariah (common, auto rifle Precision) — base ammit_ar2

- Identity kept: AK-style olive receiver with top-cover strip and two see-through gaps, long dark shroud with two side slots (painted recesses), slanted nose plate and toothed lower rail (10 real teeth), finned brake + collar, mag-well window plate with the silver release lever, silver trigger-guard loop, brown/black raked grip, skeleton stock with two real openings, small round reflex sight (green rim/reticle).
- Elements: body 68 + magazine 2 = 70 (no triangle adapters). Atlas 512x512 at 16 texels/px; texture = kit projection of the rip; specials: shroud slots, bore, tube inner wall, reticle.
- Map: uniform 25.06 px/m; muzzle -8.99 (contract -9.04); stock stretched 5% behind z 11 so the butt reaches 15.75..15.9 (contract 15.92); grip lands on the ammit grip box (y 8.5: 7.84..9.72 vs 7.74..9.4).
- Deliberate deviations: (1) sight enlarged (rip dia 0.78 -> 1.1 px octagon) and raised +0.855 px on a narrow riser so its centre sits on the ammit ADS eye line y 13.835 (W151 sightCenter 14.0 minus the 0.165 offset seen on W302 Khvostov / the ammit aim tip); NO_OVERLAY with green emissive reticle geometry (dot + two dashes) at z 3.0. (2) magazine moved 0.6 px forward and the lower receiver (magwell..guard) compressed 15% so the magwell front moves with it (ammit mag top z 1.4..4.3, ours 1.9..3.9). (3) lower rail deepened 0.25 px (bottom 9.72) toward the much deeper ammit fore-end.
- Known gap: ammit fore-end bottom is y 9.0, Pariah shroud/rail bottom 9.72 -> support hand may float ~0.7 px; Pariah is also far slimmer than ammit (top 12.07 vs 13.4).
- Not verified: in-game first-person/ADS (reticle centring relies on the derived 13.835 eye line), reload magazine motion/hand contact, third person, pack load. Offline kit renders only.

## Detail + style pass (2026-11-05)
- Elements: 70 -> 150 (body 146 + magazine 4); atlas 512x512.
- W30 pixel style: flat per-part colours (olive receiver, dark shroud/stock, brown grip panel, silver guard/lever/window frame), PALETTE 14; long slabs split (shroud 3, cover 3, stock top 3 segments with chamfered steps), chamfers on shroud/nose/collar/cover/stock, brake rings, window plate, grip panel, mag ribs, 5 stock-window fillets, engraved receiver lines.
- adscheck (main kit): only hollow sight frames (elements named sight_*) exceed the base top profile; without them OK. Sight frames surround the ADS aim point.
- Contract positions (grip, trigger, magazine box/part ids, muzzle, sight line) unchanged. Not verified in game.

## Clean-geometry pass (2026-11-05)
- Elements now 126 (body 119 + magazine 7).
- Chattering-Bone pass: segmented slabs now one continuous chamfered section with engraved seam grooves (no stepped/inset offset pieces); butt pad 3-degree skew removed; belly front, cover tail and magazine base plate rotated slabs replaced by axis-aligned chamfered steps; octagon sight staves sized exactly (no corner overhang).
- Remaining rotations only on genuinely angled parts (grip, trigger hook/guard, stock strut/frame bar, cables, octagon sight/eyecup, 45-degree chamfer strips). adscheck: only sight_* frames above the base profile.

## IDENTITY LIST — Ace / Izanagi pass (2026-11-05)
- 올리브색 AK형 상부 덮개와 두 열린 슬롯
- 진회색 핸드가드의 두 관통 통풍구와 하부 10개 레일 톱니
- 은색 사각 탄창우물 테두리·해제 레버·방아쇠울
- 갈색 교차선 그립 패널
- 두 빈 공간이 있는 검정 스켈레톤 개머리판
- 작은 회색 원형 반사식 조준기·녹색 조준점
- 총몸 뒤쪽 어두운 십자 표식과 은색 피벗

Source: read-only rip nx/px albedo views and prior side-by-side; face paint uses original material blocks, fastener positions and panel routes. Reference geometry/UV: current Ace 87 cubes and Izanagi 79 cubes read directly; enlarged in-game/atlas reference inspected. No invented lettering was added where it was not legible in the source.

## Identity paint + geometry result (2026-11-05)
- Elements 126 → 130 (body 123 + magazine 7); T20; atlas 512×512.
- Every visible face is explicitly painted through special(): flat source material, 1-texel bright upper edge/dark lower seam, source panel routes, screw/pivot pixels, grip checkering, tinted optic rim; no new projected grime or invented lettering.
- 512-square atlas is retained for Pariah/Lionheart. Cuboid/SUROS/Refrain need 1024×512 at T20 for near-camera receiver/rear/optic detail; the unused atlas half is cropped. PNGs are 15–22 KB each; GPU RGBA storage is 1 MiB or 2 MiB per atlas before mipmaps.
- Real geometry: Pariah/Lionheart's two shroud slots are open through the body; Cuboid has a two-row perforated suppressor cage; Lionheart's white brake has two through ports; SUROS's top rail has nine teeth. Existing real optic windows, stock holes and magazine split remain.
- Coplanar repair: inherited chamfer cap/frame overlaps are resolved with per-face micro-relief of 0.0001×(element ordinal) model px, at most 0.0145 px (under 0.3 texel). Only same-facing intersecting facets recess; opposing joining faces and unrelated boundaries are untouched. A geometric exposed-face intersection audit found 0 remaining coplanar overlaps for all five.
- Validation: kit build; unique elements, positive dimensions, UVs in 0..16, atlas/JSON dimensions; west/east/top/q/front offline renders. Raw adscheck reports the hollow sight_* frames and emissive reticle; excluding those, the solid body fits the base profile. Sampling the exact (x=8,y=eye) forward ray finds no blocking solid except the intended reticle. This is offline geometry evidence, not in-game ADS acceptance.
- Remaining: Minecraft pack load, first/third-person grip, reload/contact, 10–20 weapon display and native FPS were not run by this worker. Cuboid's missing magenta source optic material remains an explicitly reconstructed dark/green material; Refrain's pre-existing compressed hood profile remains an ADS accommodation.

## MATERIAL pass — authoritative surface version (2026-11-05)
The earlier all-face flat identity paint is superseded. Material assignment covers every element with no unmapped fallback; STYLE='material'. References inspected: Beloved/Gnawing Hunger in-game crops and atlases, their W123 source generators, plus this gun's nx/px rip projection cache.

- `olive_paint` → paint, RGB (88, 89, 48).
- `blued_steel` → steel, RGB (58, 61, 64).
- `satin_aluminium` → metal, RGB (157, 160, 156).
- `handguard_polymer` → polymer, RGB (43, 44, 43).
- `grip_brown_wrap` → cloth, RGB (85, 49, 34).
- `butt_rubber` → rubber, RGB (28, 30, 29).
- `optic_grey` → metal, RGB (104, 109, 108).
- `optic_green` → lens, RGB (62, 116, 75).
- `recess` → dark, RGB (17, 20, 20).
- `emitter` → glow, RGB (110, 235, 95).

- The kit blends source high-pass relief with controlled brushed/fine/stipple/cross/weave texture according to the assigned material. Reconstructed end caps, bevels and remapped optic faces have detail=0; top/bottom relief has reduced weight. These are static RGB cues, not runtime metallic/roughness PBR.
- special() now paints only retained identity accents (small glyphs, narrow frame/paint lines, optic glints, reticle; Lionheart/Refrain use source-derived camo masks with quiet paint grain). Whole-face flat fills and artificial generic panel-border overlays were removed.
- Geometry hash is unchanged from identity pass: 130 elements, body 123 + magazine 7; T20; atlas 512×512.
- Rebuilt with kit; west/east/top/q/front rendered. Exposed coplanar audit remains 0. Raw adscheck saved in review/material_adscheck.txt still lists hollow optics / intended reticle; solid profile and unobstructed aim ray are unchanged by the byte-identical geometry.
- Native pack load, held views, ADS, reload, audio/FPS and 10–20 displays remain unverified. No Gradle or Minecraft run; no commit.

## MATERIAL R2 — latest (2026-11-05)
- Lower receiver, magwell rear and receiver post: paint to blued steel; shroud: polymer to dark metal.
- Hand-authored motif: Brown grip wrap has a sparse 1-texel diagonal seam motif. Cross glyph and narrow magwell frame retained.
- Paint wear uses explicit substrate colours for Pariah/Cuboid/SUROS; camo paint wear is disabled to avoid reintroducing pepper noise. Source camo stencil only is median/blur cleaned then reduced to 2–3 opaque paint regions; original projection cache remains unchanged.
- Polymer/rubber base luminance delta: 35.70; rubber uses reduced rim and no plate edge.
- Geometry hash unchanged; 130 elements; T20; 512×512 atlas unchanged. Build, JSON/UV/PNG and manifest checks PASS. Raw adscheck log: review/material_r2_adscheck.txt; only prior hollow optic / reticle exceptions remain. Native QA not run.
