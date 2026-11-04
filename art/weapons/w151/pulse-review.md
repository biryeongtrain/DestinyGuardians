# W151 pulse/MG ADS sight bodies — offline review

All six assigned weapons are implemented in the new `weapon_sight_w151` namespace. This batch owns exactly ten new files: its generator, regression, manifest, this review and six body JSONs. It does not register or activate them. Master owns shared Java, graph integration and runtime. Canonical HIP/third-person/reload models and the W148 generator are read-only.

Read before authoring: root AGENTS.md, `/Users/qf/.codex/RTK.md`, minecraft-weapon-art-design/SKILL.md and references/ace-izanagi-study.md. No CodeGraph directory is present. Actual default photos at `/tmp/destiny-weapons-w31/references/<id>.jpg` were opened with local view_image for all six weapons. Each current W123 model, design.json, review.md and manifest.json was inspected, including original rip paths/hashes, excluded reticle provenance and default-paint limitations. W31 references.json links those photographs to the Bungie screenshot records. W148 `shotgun_body` was read as a structural example, never executed or edited. Original rip geometry was not converted or imported.

| Weapon | Actual photograph cues and ADS choice | Source / removed / added / final |
| --- | --- | --- |
| cold_denial | Tall separate swept black ramps over a toothed teal rail and bronze conduits; retain the source open-top wings and raked ramps with their patterned UVs. Add only stem and red tip between them. | 100 / 0 / 2 / **102** |
| bygones | Short green-black cylindrical optic on a narrow raised foot over walnut furniture, top band and side dial. Keep the eight-wall tube, mounts, band and dial exactly; add a pin near its forward end. | 129 / 0 / 2 / **131** |
| chattering_bone | Small violet tube with a contrasting ivory/gold rear ring over an ivory carved receiver. Retain both source rings at different depths and the violet/pale face UVs; add a forward pin. | 90 / 0 / 2 / **92** |
| blast_furnace | Photograph shows separated open iron units on the rear stock and forward breech. Remove W123's boxed optic proxy; keep rail, forward base, stock cap and original rear ears. Add two splayed upper rear ears, low notch floor, forward stem and tip on the existing bases. | 97 / 6 / 5 / **96** |
| claws_of_the_wolf | Long burgundy optic, dark mouth, brass dial and top plate above wolf studs. Retain original shell/dials/paint; replace two opaque caps with actual air, eight collar walls using corresponding existing shell face UVs, and a forward pin. | 128 / 2 / 10 / **136** |
| hammerhead | Angular reflex window with leaning side legs, short flat bridge, rear emitter and long cover mount. Retain the source hood, rotated legs, mount, cover and emitter; add a pin just forward of the window. | 149 / 0 / 2 / **151** |

Counts include every simultaneously displayed body, magazine/feed and cover element once. These are static full ADS assemblies despite the `_body` suffix; master should supply the ADS pose wrapper without adding a second magazine or cover. Full, reload and split models are alternative representations, not additive budgets. Every assembly is below 1000 elements; there are no mesh/triangle adapters or new textures. All original nonremoved element dictionaries, face UVs, rotations, order, credit and texture slots are preserved verbatim in parsed structure. Only source `display` is omitted so master can own ADS poses. No source body element is recentered, scaled, repainted, clipped or rebuilt.

## Exact ADS-only removals

`claws_of_the_wolf`: `optic_rear` is the filled rear slab at Z 7.08–7.46972291; `optic_lens` is an opaque slab at Z 4.53–4.61. Both cross the original tube center [8,12.53]. Regression verifies both original blockers and reinjects each individually to prove clearance fails. The replacement rear collar retains outer material/depth while providing a real empty center.

`blast_furnace`: `Optic_lower`, `Optic_post_-1`, `Optic_post_1`, `Optic_hood`, `Optic_sill`, `Optic_rear_adjuster`. This six-part boxed W123 proxy stands across the forward iron sight's field. Its lower/adjuster cross the selected Y 14.25 line, sill intrudes just above it, posts/roof enclose the upper field where the photographed irons are open. Replace the complete ADS sight proxy, retaining underlying `Sight_rail`, `Forward_sight_base`, original `Rear_sight_ear_-1` and `Rear_sight_ear_1` and their receiver/stock geometry. The raised upper ears and low floor form a separated rear U-notch. No removals on the other four weapons.

## Sight contract and checks

Every manifest row has `id`, real `family`, `body`, `sightCenter`, `forwardPoint` at Z−2, individual `style`, `eyeSide:+Z`, `plane:XY`, `scale:0.9`, `eyeToSightMeters:0.65`, `removedSightNames`, `elementCount`, repository-relative W123 `source`, `sourceSha256` and concrete reference notes. Additional fields record added names, aiming tip, radius, source counts, photo/review/design/rip and W148 texture hashes. The top-level object is exactly `{"weapons":[...]}`. JSON serialization rejects NaN/infinity.

The center ray points along −Z through literal air. The physical tip is centered in X just below Y, with a projected gap of 0.055 model units at the rear sight plane for the declared eye; its actual Y gap accounts for rear/front depth. This matters most for Blast Furnace's separated irons. A 0.04-radius aperture stays clear around center. No filled lens, reticle card or opaque center dot is used. Pins are a physical aiming approximation; glass/refraction and original floating reticles are not reconstructed.

The regression inverse-transforms ray segment endpoints into each element's local coordinates before the slab intersection. It supports legacy axis/angle, rescale, and 26.3 X/Y/Z rotations using inverse Rz*Ry*Rx order. It tests every retained and new element, not a sight-name filter or unrotated XY/AABB shortcut. For each weapon it samples 197 points in the clear disk, both parallel and through the declared eye (**2364 body/aperture rays**), plus centered-tip visibility. Synthetic rotated opaque slabs test missed intersections and false positives; compound angles, nonzero origins, rescale and zero-depth cards are covered.

A transient CPU perspective geometry preview was inspected in assignment order (Cold Denial, Bygones, Chattering Bone, Blast Furnace, Claws, Hammerhead). It shows distinct open ramps, short tube, pale-rim tube, separated U irons, longer collar tube and angular reflex window, with clear centers above the tips. The diagnostic uses flat placeholder material colors, proper near-plane clipping and no native renderer; it is not texture/native appearance evidence and creates no extra workspace artifact. System Python lacks Pillow; the first optional preview attempt failed before any file writes, then a standard-library raster diagnostic was used. The six actual original photos, rather than those placeholder colors, establish the material and shape cues.

Commands executed from `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w151-pulse` (all shell commands begin with rtk):

```sh
rtk proxy python3 -B scripts/generate_sight_bodies_w151_pulse.py
rtk proxy python3 -B scripts/generate_sight_bodies_w151_pulse.py --verify
rtk proxy python3 -B scripts/qa/test_sight_bodies_w151_pulse.py
rtk proxy python3 -B scripts/qa/worktree_batch.py export --worktree /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w151-pulse --output /private/tmp/w151-pulse-export
```

Targeted regression result: **12 tests passed**, covering all six rows, complete source/UV preservation except exact named removals, assembly budget/schema/texture resolution, rotated body/aperture tests, aiming tip visibility, original opaque lens detection and reinjection, photo/design/review/rip provenance, deterministic seven generated outputs, successful CLI verification and mismatch rejection without writes. Export manifest is the authoritative scope/main-baseline audit. No commit, stash, reset, clean or push; no Gradle, game, Computer Use, Vision or dependency operations.

## Pending master native checks

Master still needs to integrate the new body IDs/anchors into ADS wrappers and verify resource-pack parsing and 26.3 rotations, unobstructed native −Z aiming at targets, tip readability, HIP→ADS transition/return, offhand/twohand holding, third-person preservation, and reload return without duplicate magazine/cover or sight clipping. Check Hammerhead's cover/feed detach/reseat and Blast Furnace magazine insertion using their existing runtime graphs. Representative 10–20 simultaneous displays and visible stutter remain unmeasured. No game-tested, native acceptance or performance claim is made.


## W152 user correction — Blast Furnace (2026-10-26)

Previous separated-iron/stock-rear ADS was not visually usable despite a clear central ray. Restore all six original W123 Optic elements/UV, replace the added rear-stock notch with the original upper open sight, anchor (8,14.73,8.065), eye relief0.32m, aligned two-element front pin. Stock geometry retained, 99 cubes. Other five pulse/MG designs unchanged. Actual native PNG, ADS burst36→32 and HIP return accepted in docs/qa/2026-10-26/w152/README.md; Python21/JUnit5 pass. Original worker report above is historical, not the current Blast specification.
