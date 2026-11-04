# W69 — Original Ammit AR2 source audit

Verified 2026-10-24T06:32:31.173434+00:00 on `feat/hunter`. Both cached originals match the user pins and W30 manifest. **Neither file contains a usable ripped reload animation.** The `.blend` does contain a frame-driven fluid shader and rig remnants, detailed below.

## Identity and inspection

Drive: [10O1xjObGAvW5x6uESPax0G-U1qA7Vh7f](https://drive.google.com/file/d/10O1xjObGAvW5x6uESPax0G-U1qA7Vh7f/view), `Ammit AR2.7z Compressed archive`. Local source folder: `/tmp/destiny-weapons-w30/raw/ammit_ar2/extracted/Ammit AR2/`.

| Original | Bytes | Current SHA-256; equals before and expected |
|---|---:|---|
| `Ammit AR2.blend` | 11,987,537 | `4898634c120d335b15465d61b9e3fa4979e78ef1e57bb87f4a43eef92ba4921d` |
| `Ammit AR2.fbx` | 1,075,116 | `45d3b95b8e875957f480f2ae97193b4aa2b01ea760583751d8633261b17c0b07` |

The source lineage was traced through `scripts/build_weapons_w30.py`, `art/weapons/w30/manifest.json`, the catalog and `ammit_ar2.bbmodel`. `scripts/art/reconstruct_weapons_w30.py` locates `raw/<id>/extracted`; cached inspections are incomplete for animation because FBX was imported with `use_anim=False`. Fresh inspection used separate Blender 5.4.0 Alpha processes (`7a8f04b3bb5a`), `--background --factory-startup --disable-autoexec --threads 1`; `.blend` opened with `load_ui=False,use_scripts=False`, FBX imported with **`use_anim=True`**. The original blend was saved by Blender **3.3.6**. Bundled FBX parsing also inspected raw FBX 7400 Objects records, independently of animation import. Source shader scripts/text blocks were never executed.

## Actual data

| Verified quantity | BLEND | FBX |
|---|---:|---:|
| Objects, all MESH | 13 | 13 |
| Mesh datablocks | 13 | 13 |
| Vertices | 16,560 | 16,560 |
| Polygons / triangles (all triangulated) | 20,250 | 20,250 |
| Armatures | 0 | 0 |
| Bones | 0 | 0 |
| Actions / action curves / keyframes | 0 | 0 |
| NLA tracks / strips | 0 | 0 |
| Shape key datablocks | 0 | 0 |
| Armature modifiers | 13 | 0 |
| Drivers | 1 | 0 |
| Material datablocks | 12 | 11 |

Armature, bone, action and NLA name lists are empty in both formats. All objects are unparented, have no object animation data or constraints, and share origin `[0,0,0]`. In the blend each transform is identity. The scene range `1–250` at 24 fps (saved frame 50) is scene metadata, not evidence of a clip. Raw FBX has exactly **13 Geometry + 13 Model (Mesh) + 11 Material** records, with **0 AnimationStack, AnimationLayer, AnimationCurveNode, AnimationCurve, Deformer or Pose**. Imported FBX contains no vertex groups or modifiers.

**Rig remnants:** every blend mesh has one `Armature` modifier whose armature target is **null**, plus the same **80** named vertex groups, including `Pedestal`, `Pelvis`, `Utility`, `Grip.L`, `Grip.R`, limb/finger and material-slot groups. The JSON contains the full 80-name set and every nonempty group with assignment counts and weights. `Magazine` has all 180 vertices assigned to `Pelvis` at weight 1; `Middle` has 102 assigned to `Utility` at weight 1 and 9,293 to `Pedestal`. No corresponding armature/bones or motion tracks exist. These are usable labels/weights for inspection, not a functioning reload rig.

**Shader exception:** material `Fluid` has one scripted driver, `frame/-100`, on `nodes["Mapping.001"].inputs[1].default_value`, array index **1** (Location Y). Its Mapping Vector feeds `Image Texture.001` (`886eef80.png`), then the color/emission graph. This is frame-dependent texture-coordinate motion, not weapon/hand geometry animation. The expression and graph were read as data with autoexec disabled; playback was not evaluated.

## Named components

Both formats contain the following exact object names and matching vertex/triangle counts. Full per-format mesh names, bounds, transforms, material slots, UV layers, weights and modifiers are in the JSON.

| Object | Mesh datablock | Vertices | Triangles | Material |
|---|---|---:|---:|---|
| `Barrel Tube` | `Ammit-AR2.00.001` | 24 | 20 | `Barrel Tube` |
| `Fluid` | `Ammit-AR2.02.001` | 268 | 476 | `Fluid` |
| `Fluid Glass` | `Ammit-AR2.02.002` | 268 | 476 | `Fluid Glass` |
| `Inner Omolon Logo` | `Ammit-AR2.01.002` | 8 | 4 | `Inner Omolon Logo` |
| `Inner Structure` | `Ammit-AR2.03.000` | 2,834 | 3,700 | `Inner Structure` |
| `Magazine` | `Ammit-AR2.05.000` | 180 | 164 | `Magazine` |
| `Main - Body` | `Ammit-AR2.00.002` | 2,352 | 2,556 | `Main` |
| `Main - Omolon Logo` | `Ammit-AR2.00.003` | 484 | 584 | `Main` |
| `Main - Spot` | `Ammit-AR2.00.000` | 4 | 2 | `Main` |
| `Middle` | `Ammit-AR2.02.000` | 9,395 | 11,417 | `Middle` |
| `Reticle` | `Ammit-AR2.14.000` | 27 | 25 | `Reticle` |
| `Sights` | `Ammit-AR2.06.000` | 532 | 606 | `Sights` |
| `Stock` | `Ammit-AR2.04.000` | 184 | 220 | `Stock` |

`Magazine` is already an independent mesh (180 vertices, 164 triangles); no mesh split is needed to identify the source magazine. Its source bounds (XYZ) are `[-0.016909, -0.240151, -0.081982]` to `[0.016909, -0.125463, 0.022458]`. Its origin remains world zero, so the source does not demonstrate a local magazine/socket pivot or removal path. `Middle`/`Main - Body`/`Inner Structure` are separately named source meshes. No object is named bolt or charging handle; the 102-vertex `Middle` → `Utility` subset is only a candidate for further inspection and is not identified here as either part.

W30 excludes `Reticle` (27 vertices, 25 triangles). Thus its 12 included components have **16,533 vertices and 20,225 triangles**, exactly reconciling with the manifest’s 20,225 source triangles. The original total is 20,250. W30’s historical 19,253 textured-triangle count is a generation record, not a fresh texture-availability assertion. The current W30 cuboid derivative has 199 cubes and is distinct from these original component meshes. Small FBX import rounding differences in bounds are preserved in the JSON.

## Materials and reload handoff

The blend has 11 materials assigned to the meshes and an additional unassigned `Dots Stroke` material. Its source groups include `Ammit AR2`, `D2 PlayerGear Shader 3.0.8`, `DyeSlot Converter 2`, and `Reticle Shader`. Main/Middle/Magazine/Stock/Sights/Inner Structure/Inner Omolon Logo use Diffuse/Normal/GStack images and dye/playergear graphs; Fluid, Fluid Glass and Barrel Tube have distinct graphs. Every mesh has UV layers `uv0`, `uv1`, `slot`. The FBX retains 11 material names but imports with no connected image texture nodes or source node groups; use the blend graph for richer material evidence.

**Result:** the inspected originals provide a separated static weapon assembly and legacy weight labels, with a fluid shader driver. They provide **no reusable ripped reload clip, bone rig, hand motion, reload timing, magazine trajectory, or bolt motion track**. Gameplay reference interpretation, component partitioning, pivots, animation authoring, generator/runtime work and visual review remain with main. This audit does not infer absence of hidden geometry from object names.

## Preservation and bounded execution

All **49** files in the private Ammit cache package retained their SHA-256, size and modification time across all inspections. Both model hashes were checked again before writing this report. Protected Blender **58116** and Blockbench **48104** remained running; neither was contacted or modified. Own headless processes 50787, 50820, 51198 completed with exit code 0 in 3.667s, 0.609s, 1.296s, each under a 90-second bound. No termination signals were needed.

Only repository outputs:

- `art/weapons/w69/references/original-model-audit.json`
- `art/weapons/w69/references/original-model-audit.md`

Private inspection scripts, raw JSON, logs and execution snapshots remain in `/tmp/destiny-w69-source-inspect/`. No original model or GUI scene was saved; no video research, client launch, normal QA, reset of a running app, code change, or commit was performed.
