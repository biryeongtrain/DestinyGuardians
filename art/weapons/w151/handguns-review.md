# W151 handgun ADS sight bodies

Six ADS-only full-assembly bodies for Duke Mk.44, Austringer, Seventh Seraph
Officer Revolver, Allied Demand, Farewell and Lonesome. The manifest is
`art/weapons/w151/handguns-sights.json`, with the required top-level `weapons`
array. These bodies have no display transforms. Master owns graph/Java
integration, camera placement and native acceptance.

## Evidence actually inspected

Opened all six actual `/tmp/destiny-weapons-w31/references/<id>.jpg` default
photos. Read each current `weapon_surface_w123/<id>.json`, its W123-directory
`design.json` and `review.md`, and the W31 reference catalog. The manifest pins
the current source model, design, review and photo SHA-256 values, Bungie photo
URLs, prior source BLEND/FBX hashes and accepted source triangle counts. Allied
Demand and Farewell also have prior library-extraction provenance in their
`source-reference.json` files. No rip conversion or DCC execution was performed.

Read the weapon-art skill and `references/ace-izanagi-study.md`: retain large
meaningful volumes and existing face UVs, use real empty space for the sight,
and count the actual assembled output. Read W148 `shotgun_body` as a structural
example; the shared generator was neither executed nor edited.

These photos show iron sights on all six weapons. In particular, Austringer's
black tube is an underbarrel accessory, not an aiming optic. Its opaque lens,
32-piece optical/accessory group and hose remain unchanged below the sight line.
No generic reflex box, filled glass card, invented reticle or new texture is
added. Small rear profiles are authored interpretations of the side/oblique
photos and prior studies, not claims of an extracted first-person sight mesh.

## Per-weapon art and exact removals

| Weapon | Photo cues and ADS change | Source | Removed | Retained | Added | Assembly |
|---|---|---:|---:|---:|---:|---:|
| Duke Mk.44 | Blue long top strap, low black blade and narrow rear notch. Replace the overly wide front blade with a low foot and thin tip; keep the rear notch, loop hammer, cylinder and yoke. | 147 | 1 | 146 | 2 | 148 |
| Austringer | Pale gold shroud, black receiver and low gold top irons. Add a short front tip and two gold rear shoulder extensions. Keep the complete underbarrel accessory and all existing geometry. | 126 | 0 | 126 | 3 | 129 |
| Seventh Seraph Officer Revolver | Long toothed rail, wedge front ramp and tall broad rear block. Split the obstructing rear block into a real U notch with a low sill and two ears; extend a narrow front tip. Keep the rotated saddle, forks, forward lower hood, silver/brass trim and rail. | 121 | 1 | 120 | 4 | 124 |
| Allied Demand | Small conventional slide irons behind the long silver suppressor. Replace the center-filling front blade with a compact foot/tip and add a low rear sill between the existing ears. Green frame, patterned slide and suppressor stay intact. | 85 | 1 | 84 | 3 | 87 |
| Farewell | Angular silver front sight with a small opening and paired purple raked rear ears. Put a lower post inside a true three-piece protective hood and extend the existing rear ears into raked fins. Cables, stencil, heat sink and bayonet stay intact. | 115 | 1 | 114 | 6 | 120 |
| Lonesome | Flared rear U above the rounded breech, narrow front blade, muted bronze/steel, pierced-pattern shroud and diagonal brace. Replace the front blade with a low foot/tip; add two outward-canted rear shoulders. | 97 | 1 | 96 | 4 | 100 |

The five removed elements, and no others, are:

- Duke: `Front_sight`.
- Austringer: none.
- Seventh Seraph: `rear_sight_blade`.
- Allied Demand: `front_sight`.
- Farewell: `front_sight_post`.
- Lonesome: `front_sight_blade`.

The original assembly obstructs the sampled clearance region with exactly the
named removals; regression verifies this before checking the new bodies. Every
other source element remains byte-equivalent as a parsed JSON object, in source
order, including its geometry, rotation and every face/UV field. Texture maps
and all other top-level source metadata are preserved; only the inherited
`display` block is omitted from the new ADS body. New parts reuse faces from
their own weapon's sight UV islands, with each donor named in `sightUvDonors`.
No PNG or W148 texture changes are needed.

These are full assemblies, not extra parts to add over the existing full model.
Duke's 148 includes its unchanged cylinder/yoke, counted once. No body/magazine
representation is double-counted. Every assembly is comfortably below 1000.

## Sight plane and clearance

| Weapon | sightCenter | forwardPoint | Physical front-tip top Y |
|---|---|---|---:|
| Duke | [8, 15.06, 5.04] | [8, 15.06, 3.04] | 15.005 |
| Austringer | [8, 14.03, 5.24] | [8, 14.03, 3.24] | 13.975 |
| Seventh Seraph | [8, 14.03, 6.39] | [8, 14.03, 4.39] | 13.975 |
| Allied Demand | [8, 13.42, 8.40] | [8, 13.42, 6.40] | 13.365 |
| Farewell | [8, 14.15, 7.39] | [8, 14.15, 5.39] | 14.095 |
| Lonesome | [8, 15.04, 8.71] | [8, 15.04, 6.71] | 14.985 |

All rows use `eyeSide: +Z`, `plane: XY`, `scale: 0.9` and
`eyeToSightMeters: 0.65`. The sight center is actual air, with the authored tip
centered at X=8 and ending 0.055 native units below the aiming line. A 0.05 by
0.05 native-unit square around the center is sampled on a 9 by 9 grid. Both
parallel -Z rays and common-eye rays through that square traverse the complete
assembly, including the geometry ahead of the rear sight. The eye offset in
native units is `0.65 * 16 / 0.9` along +Z. A separate common-eye ray verifies
that each tip is the nearest visible surface just below center.

The ray/box test inverse-transforms the ray into each element's local box. It
supports classic axis/angle, native 26.3 Euler `Rz * Ry * Rx`, noncentral pivots
and legacy rescale. It treats all elements as opaque, including zero-depth
cards; there is no name-based lens exemption. The regression adds an independent
forward-matrix/world-triangle oracle at off-grid aperture points, and fixtures
for rotated lenses that an unrotated AABB would miss or falsely report. This is
sampled mathematical clearance, not proof of every possible camera angle.

An in-memory CPU false-color sight-axis preview of all six assemblies was
visually inspected: source solids gray, additions blue, tips orange, and a cyan
clearance marker. It used the same full source assemblies and an independent
forward vertex transform; no preview file was written. This is geometry-only
inspection, not a textured/native screenshot or evidence of native acceptance.

## Commands and results

Run from `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w151-handguns`:

```sh
rtk proxy python3 -B scripts/generate_sight_bodies_w151_handguns.py
rtk proxy python3 -B scripts/qa/test_sight_bodies_w151_handguns.py
rtk proxy python3 -B scripts/generate_sight_bodies_w151_handguns.py --verify
rtk proxy python3 -B scripts/qa/worktree_batch.py export --worktree /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w151-handguns --output /private/tmp/w151-handguns-export
```

Targeted regression: **50 tests passed** (42 individual weapon checks plus
8 global/rotation/negative checks). Generator `--verify`: **6 weapons,
7 outputs verified**. Determinism is checked across two fresh in-memory builds
and against the saved output bytes; stale and missing outputs are rejected.
Photo/reference hashes, exact source preservation, tip visibility, rotations,
opaque lenses, zero-depth cards, texture resolution, UV donors, finite JSON,
full assembly counts and the exact seven generated paths are covered. The pure
generation test also hashes canonical/HIP/ADS/reload inputs before and after.

The intended export contains exactly these ten new owned paths:

```text
scripts/generate_sight_bodies_w151_handguns.py
scripts/qa/test_sight_bodies_w151_handguns.py
art/weapons/w151/handguns-sights.json
art/weapons/w151/handguns-review.md
src/main/resources/assets/destiny/models/weapon_sight_w151/duke_mk_44_body.json
src/main/resources/assets/destiny/models/weapon_sight_w151/austringer_body.json
src/main/resources/assets/destiny/models/weapon_sight_w151/seventh_seraph_officer_revolver_body.json
src/main/resources/assets/destiny/models/weapon_sight_w151/allied_demand_body.json
src/main/resources/assets/destiny/models/weapon_sight_w151/farewell_body.json
src/main/resources/assets/destiny/models/weapon_sight_w151/lonesome_body.json
```

## Pending master native/Vision checks

No Gradle, game, CU, Vision, dependency mutation, commit, stash, reset, clean or
push was used. Canonical HIP, third person and reload files are read-only.
Shared Java, registries, common generators and the concurrent rockets batch
are outside this worker's scope.

After master integration: native parser/pack loading and texture resolution;
ADS admission/exit and endpoint center at the requested eye distance in both
hands; actual visible tip/notch clearance during recoil; representative HIP and
third person comparison; reload and return, including Duke's cylinder/yoke;
and a brief 10–20-display observation. Farewell's guarded opening and Seraph's
rotated saddle deserve particular native close inspection. No game-tested,
shader/PBR recovery, native clipping or performance claims are made here.
