# W229 enemy ability art — frozen handoff

Ready: **20 new resources** (6 models, 6 textures, 8 item definitions), exclusively in enemy-variants. Current installed main assets were read only; evidence/source-index.json records all 20 input hashes. Base, R2 and Nova frozen outputs are unchanged. Master owns per-viewer wiring, native QA and integration.

## IDs

| Prop | Item model ID | Emitted elements |
|---|---|---|
| hammer | `destiny:class_ability/titan/solar_super_enemy` | 221 |
| shield | `destiny:class_ability/titan/void_super_enemy` | 342 |
| sword | `destiny:class_ability/warlock/solar_super_enemy` | 211 |
| nova | `destiny:class_ability/warlock/void_super_enemy` | 38 |
| barrier | `destiny:class_ability/titan/class_ability_enemy` | 89 |
| rift | `destiny:class_ability/warlock/class_ability_enemy` | 101 |

Melee item aliases `destiny:class_ability/titan/solar_melee_enemy` and `destiny:class_ability/titan/void_melee_enemy` reference solar_super_enemy and void_super_enemy respectively. They share super geometry/textures. The captured installed list has no other Titan/Warlock ability item visuals.

**integration-manifest.json** is the canonical copy list, with absolute source, repo-relative target, bytes and SHA-256 for every resource. All `_enemy` targets were absent at handoff. No viewer logic is embedded in assets.

## Appearance and invariants

Crimson red textures retain dimensions, atlas layout, all alpha bytes and per-pixel maximum RGB byte (HSV value) exactly. Source relative luminance, saturation and chroma modulate the red/crimson/pale-red channels to preserve markings, baked shading and bright material patches. Photometric luminance is not identical after hue conversion; original brightness detail is retained through value and tone variation. Alpha holes, partial-alpha energy fields, triangle masks and gutters are unchanged.

Models differ **only in texture links**. Geometry, triangle adapter output, UV, face selection, rotations, anchors, shade, light_emission, display transforms and particle texture resolution remain identical. Geometry additions: **0**. Every model stays below1000 output elements. No raw source archives or messages are bundled. Nova/barrier/rift remain self-authored temporary VFX, not ripped original enemy effects.

## Placement

Use the same placement as friendly. Barrier bounds `[0,0,0]–[16,16,16]`, anchor `[8,8,8]`, +Z normal, NONE scale `[3,2.4,.18]`, existing Barrier.center, no old BlockDisplay corner offset. Rift XZ radius8, anchor `[8,8,8]`, NONE scale `[8,1,8]` for radius4, existing ground+.04 origin. Prop hand/display corrections are unchanged. Machine-readable contract: dimensions-anchor.json.

## Comparison evidence

Overview: [all six props](evidence/six-props-comparison.png). Each sheet has original/enemy rows with front(+Z), back(-Z), right(+X), left(-X), top(+Y), oblique:

- [hammer six views](evidence/hammer-6views-comparison.png)
- [shield six views](evidence/shield-6views-comparison.png)
- [sword six views](evidence/sword-6views-comparison.png)
- [nova six views](evidence/nova-6views-comparison.png)
- [barrier six views](evidence/barrier-6views-comparison.png)
- [rift six views](evidence/rift-6views-comparison.png)

72 individual PNG frames are included. Isolated headless Blender CPU previews use exact installed faces/UV with outward normals, backside culling, alpha/emission, and matched camera/exposure. Barrier/rift use gameplay default scales. The planar rift is naturally edge-on in four horizontal views; top/oblique show its footprint. These are **offline** previews. No live scene was opened/saved.

## Validation and remaining acceptance

Checked all20 resource files, references, six full model equivalences excluding texture links, all alpha/value bytes, element budget, source hash stability, eight item definitions and72 valid PNG frames. Previous base90, R2 30 and Nova12 SHA256SUMS entries were verified unchanged; see evidence/frozen-prior-check.json.

No game/build/Gradle/Vision/CU/commit was run. Native per-viewer red-enemy versus original-ally/owner selection, alpha behavior and combat visibility remain for master QA.

## Freeze

owned-manifest.json inventories this output only. outputs-manifest.json hashes payload/ownership files excluding itself and SHA256SUMS to avoid cyclic hashes. SHA256SUMS also hashes outputs-manifest. Do not regenerate in this frozen folder; revisions require a new delta.
