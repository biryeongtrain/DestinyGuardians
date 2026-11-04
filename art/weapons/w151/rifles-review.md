# W151 rifle ADS sight bodies

Six ADS-only candidates, authored in the fully dirty-seeded isolated CoW workspace
`/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w151-rifles`.
These are body assets and integration metadata; master owns item graph/Java
integration, runtime and Vision. No game-tested or native-accepted claim is made.

Read the workspace AGENTS.md, RTK.md, minecraft-weapon-art-design/SKILL.md and its
Ace/Izanagi study before authoring. The study's meaningful solid volumes, face UVs
and real apertures guide this small intervention. Existing W123 designs, reviews,
manifests and rip provenance were inspected for all six. The six actual default
JPGs under `/tmp/destiny-weapons-w31/references/` were opened with the image tool;
their bytes match the W31 Bungie reference hashes. No alternate shader or unrelated
weapon optic was substituted. `generate_sight_ads_w148.py::shotgun_body` was read as
a structural example, without executing or modifying that shared generator.

## Reference cues and changes

| Weapon / prior art | Actual photo cue and retained identity | W151 change | Elements: source → ADS / assembled |
|---|---|---|---|
| Halfdan-D / W129 | Ivory HAKKE rear fork on rectangular foot, inward-canted ears, low sill and long toothed rail. Original Sight_base, both rotated ears and sill retained exactly. | Narrow metal front stem at Z=-4.68 with a small pale tip; no optic added. | 114 → 116 / 116 |
| Ammit AR2 / W126 | Blue OMOLON rear peep on a short upper rail; narrow parallel posts and small bridge above the long smooth blue upper. All five existing rail/peep records retained. The supplied side-quarter photo does not establish the hidden rear face. | Slim front stem at the muzzle-top cue, Z=-8.70, aligned through the existing narrow peep. Existing body/moving-magazine partition retained. | 121 body → 123 body / 128 including 5-element magazine; 133 with a spare magazine |
| Gnawing Hunger / W128 | Short round dark reflex hood, narrow stalk, rectangular adjuster behind it and white receiver bindings. All eight rotated hood staves, base, stalk and adjuster retained exactly. | Short physical pin at Z=2.83 inside the existing hood. No glass card or filled reticle plane. | 114 → 116 / 116 |
| Steelfeather Repeater / W134 | Silver open U with straight ears, open roof and angled saddle above the swept silver receiver. Preserve its different U shape, saddle and rear rail. | Low front stem at Z=-4.93, aligned above the cooling rail, with small pale tip. | 89 → 91 / 91 |
| Frontier Justice / W138 | Pewter HAKKE GA POST on a stepped riser, chamfered cheeks and short cap over the navy receiver's long rail. Preserve the source's actual cheek/cap records, separate from Halfdan's inward-canted fork. | Front stem at Z=-4.24, above the rail, with narrow pale tip. | 141 → 143 / 143 |
| Distant Relation / W132 | Teal box scope, circular objective, silver ocular ring, two feet and low side dials. All 16 rotated rim staves, original roof, feet, dials and low barrel irons retained. | Remove four filled sight volumes; reconstruct six continuous shell slices on their original atlas to leave a through-bore, then add short pin at Z=4.30. | 88 → 92 / 92 |

The pale tips reuse the existing opaque W148 sight-atlas texel at UV
`[4.25,0.25,4.75,0.75]`; they are a simplified ADS aiming aid, not extracted D2
reticles, recovered illumination shaders or new optics. Each stem samples the
weapon's existing sight metal. Distant Relation's shell uses proportionally cropped
original housing face UVs and retains its teal material. No new texture was made.

Every source element outside the four removals is preserved as an entire JSON
record: position, dimensions, origin, rotation format/angles, face materials and UVs,
and order. Source top-level metadata is preserved except `display`, intentionally
omitted from ADS body resources so master can apply its ADS display transform.
Original texture slots remain, with only the existing W148 sight slot added.
No canonical HIP, third-person or reload asset was edited. Full-only weapons retain
their existing magazine geometry inside the full body. Ammit alone uses its existing
separate W123 body and magazine. The 1000-element assembly limit includes that
magazine and even a spare; there are no triangle adapters or alpha body cards.

## Exact ADS-only removals

Only Distant Relation has removals. Each individually intersects the selected
ADS channel in the rotation-aware finite-ray test; restoring any one makes the
clearance regression fail.

| Original name | Reason | Replacement |
|---|---|---|
| `optic_housing_core` | Solid central housing spans X=7.6112..8.3888, Y=11.23..12.53, Z=4.21..7.09 and fills the scope axis. | Four solid floor/ceiling/inner-side slices, same outer volume/material and Z depth; central air remains. |
| `optic_housing_shoulder_l` | Despite its name, this opaque cuboid spans both sides and fills the axis over X=7.46..8.54, Y=11.425..12.335, Z=4.21..7.09. | Two external side slices retain the box scope's width and continuous walls. |
| `objective_glass` | Opaque front pane at Z=4.2825..4.3175 crosses the entire aiming channel. | Real air; original objective rim remains. |
| `ocular_glass` | Opaque rear pane at Z=6.9875..7.0225 crosses the entire aiming channel. | Real air; original silver ocular rim remains. |

The other five `removedSightNames` arrays are empty. No receiver, rail, stock,
binding, shroud, barrel, magazine, grip or unrelated decorative part is removed.

## Sight coordinates and clearance

| ID | Sight center | Forward point | Style |
|---|---|---|---|
| `halfdan_d` | [8,13.65,7.57] | [8,13.65,5.57] | `hakke_iron` |
| `ammit_ar2` | [8,14,7.54] | [8,14,5.54] | `omolon_peep` |
| `gnawing_hunger` | [8,12.95,2.91] | [8,12.95,0.91] | `round_reflex` |
| `steelfeather_repeater` | [8,13.12,5.07] | [8,13.12,3.07] | `sundial_open_u` |
| `frontier_justice` | [8,13.36,7.68] | [8,13.36,5.68] | `hakke_ga_post` |
| `distant_relation` | [8,11.88,7.25] | [8,11.88,5.25] | `gambit_box_scope` |

All use eye side +Z, aiming -Z, plane XY, scale 0.9 and eye-to-sight 0.65 metres.
The aiming tip is centered on X=8 and ends 0.085 model units below sight center.
A square of half-size 0.03 about the center remains genuinely empty, including
perspective through the front post. The tip projects just below that clear square;
no opaque geometry is allowed at the center.

The checker transforms finite ray endpoints by each element's local inverse:
`transpose(Rz*Ry*Rx)` about its actual origin, with legacy axis/angle and rescale
support. Slab intersection then tests the real local cuboid. It checks all source
and added elements, treating even named glass as opaque. It does not ignore rotations,
filter checks to new sight parts, or sample isolated Z slices. Each weapon receives
49 parallel rays and 49 perspective rays, from the eye plane to Z=-40; regression
adds 49 independently spaced perspective rays to Z=-35. Mutations prove rotated
old opaque lenses and arbitrarily thin panes are rejected. Synthetic rotated bars
cover both an intersection outside unrotated bounds and a miss within world AABB.

## Offline verification and reproducibility

Commands run from this workspace, all shell commands through RTK:

```sh
rtk proxy python3 -B scripts/generate_sight_bodies_w151_rifles.py
rtk proxy python3 -B scripts/qa/test_sight_bodies_w151_rifles.py
rtk proxy python3 -B scripts/generate_sight_bodies_w151_rifles.py --verify
rtk proxy python3 -B scripts/qa/worktree_batch.py export --worktree /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w151-rifles --output /private/tmp/w151-rifles-export
```

Targeted regression: **22 tests passed**. Coverage includes the exact six-row
contract, finite JSON, source-record preservation, removal justification, full-body
parallel/perspective clearance, physical tip position, distinct original frames,
scope depth/UVs, complete assembly budgets, native cuboid/face/texture references,
opaque W148 tip sampling, photo/prior-art/rip provenance, byte-identical deterministic
generation, missing/tampered-output comparison and read-only CLI verification.
The suite runs with the Python standard library and writes no caches or fixtures.
`--verify` compares the six body files and manifest byte-for-byte without writing.

The six actual reference JPGs and six in-memory CPU geometry previews from the
specified +Z eye were viewed. Preview observations: Halfdan's inward-canted fork,
Ammit's narrow bridged peep, Gnawing's faceted round hood, Steelfeather's roofless U,
Frontier's chamfered capped post and Distant's long hollow box scope are visibly
different. All have visible tips below an empty center. Previews used flat diagnostic
colors, without native texture filtering, lighting or rendering; no image artifact
was added outside ownership and no native screenshot is implied.

Manifest rows record source model hashes, the original photo URL/hash, prior
review/design/manifest hashes, existing rip file provenance and W148 texture hash.
The only authored delta is the ten owned paths listed below. No Gradle, game,
Computer Use, Vision, DCC application, dependency mutation or shared builder was
run. No commit, stash, reset, clean or push was performed.

## Exact export scope

```text
scripts/generate_sight_bodies_w151_rifles.py
scripts/qa/test_sight_bodies_w151_rifles.py
art/weapons/w151/rifles-sights.json
art/weapons/w151/rifles-review.md
src/main/resources/assets/destiny/models/weapon_sight_w151/halfdan_d_body.json
src/main/resources/assets/destiny/models/weapon_sight_w151/ammit_ar2_body.json
src/main/resources/assets/destiny/models/weapon_sight_w151/gnawing_hunger_body.json
src/main/resources/assets/destiny/models/weapon_sight_w151/steelfeather_repeater_body.json
src/main/resources/assets/destiny/models/weapon_sight_w151/frontier_justice_body.json
src/main/resources/assets/destiny/models/weapon_sight_w151/distant_relation_body.json
```

Export target: `/private/tmp/w151-rifles-export`. The export tool must confirm
exact owned additions, no out-of-scope edits and no main/source baseline conflict;
its external `manifest.json` is the authority for export success.

## Pending master native / Vision checks

- Integrate these bodies/rows into master's shared W151 graph and Java work; native
  26.3 pack/model parser and existing-texture resolution remain untested here.
- For **all six**: ADS entry, settled aperture/tip alignment and target visibility,
  left/right hand and twohand presentation, exit to HIP, post-fire recovery and
  contrasting bright/dark backgrounds. Check original sight frames at native FOV.
- Verify unchanged HIP/third-person appearance and reload transition. For Ammit,
  confirm the existing moving magazine, detached phase and reseating still match
  the retained body. For full-only weapons, check generic reload return.
- Inspect Distant Relation through both ends and obliquely for its retained rings,
  long teal shell, old low barrel irons and absence of opaque pane artifacts.
- Observe representative 10–20 displayed weapons for visible breaks/stutters in
  master's authorized isolated session. No performance acceptance is inferred from
  element counts or CPU previews. Runtime/game/Vision checks are pending.
