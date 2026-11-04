# W100 Recluse reload assets

87 assets reuse all 217 original elements: 193 body + 24 lower-cartridge proxy.
The source component's physical magazine identity is approximate. The generic
static rip has no named magazine/bones, and the supplied gameplay hides the exact
boundary. Master reviewed the geometry audit; this limitation remains material
to visual acceptance.

## Original source and geometric partition

- Archive: W30 `The Recluse.rar`, Drive `1LRTAvTc70Sq8QLSLHqdYf7uX6MD_l72j`.
- Local: `/tmp/destiny-weapons-w30/raw/the_recluse/source.archive` and
  `extracted/Recluse.fbx`, `extracted/Recluse.blend`. Exact pins are in the manifest.
- The inert binary FBX 7400 parser checks the common export carrier, reproduces
  all 13 meshes / 20,369 triangles and the recorded W30 bounds, and applies the
  original `(-Y, Z, -X) * scale + anchor` mapping. No source scripts or applications run.
- Selected proxy: welded connected component 1 of `Mesh_0007.rip`, 352 triangles.
  Source polygon indices and all other component inventories are in the audit.
- Cubes: `2, 3, 4, 44, 56, 62, 63, 65, 72, 77, 78, 81, 83, 84, 141, 144,
  156, 161, 162, 163, 167, 173, 178, 183`.
- Selection uses strict majority of actual triangle area clipped against all six
  cube planes. Bounding boxes only reject impossible intersections. No centroid
  or bounding-box inclusion is used as positive classification evidence.
- Every original element appears exactly once, in original relative order, with
  unchanged faces, UV, texture bindings and metadata. No closure faces, textures,
  new cubes or UV rebake. Composite count stays 217, below 256.
- Mixed selected cubes: `44, 56, 62, 83`. The selection captures 81.4104% of the
  candidate's source area clipped inside the original cubes, or 70.4610% of its
  complete raw component area, and carries 1.896499 model-square-units of other
  component surface. Minority surfaces retained by the body are listed in the
  audit. This is a whole-cube approximation of an already reconstructed model.

## Reference observations and authored motion

Read `reference-notes.md` and `references/gameplay-provenance.json`; directly
inspected the supplied 37.30, 37.40, 37.50 and 37.60 PNGs. The footage establishes
the raised/rolled body, small lower-right ejection, approaching underside hand,
and insert/return. It does not establish exact local transforms or source part
membership. No further reference research was performed.

The generator authors 21 normalized samples: short raise/roll, lower-right
withdrawal, held separation, reseat, short settle, exact original HIP. Numeric
transforms, normalized key placement and cartridge trajectory are authored.
Both rigid parts share body rotation and scale; the magazine offset is rotated
by the native ItemTransform rotation and scaled before display translation.
Native left-hand signs are applied by Minecraft, without an extra manual mirror.

Historical Feeding Frenzy seconds are not copied. The generator changes no
duration, ammo, perks, audio, HUD, registration or runtime logic. It supplies no
hands/IK, separate bolt motion, recovered animation or third-person reload.

## Asset and verification contract

- Item: `destiny:weapon_reload_w100/the_recluse`.
- Geometry parents: `the_recluse_body`, `the_recluse_magazine`.
- Poses: `the_recluse_{00..20}_{body|magazine}_{native|twohand}`.
- First-person right/left only, progress float 1, grip flag 0, 21 ordered thresholds.
- Every inactive and other-context fallback is the exact original full item graph.
- Phase 0 and 1 use exact original native/twohand display objects for both parts,
  including numeric precision. Other contexts retain the corresponding accepted
  display values. The W30 inverse carrier supplies intermediate twohand poses.
- Generator and `--verify` check pins, 87 assets, conservation, endpoints,
  fallback graph, ordered references, finite values and native transform limits.
- A separate read-only 4x4 matrix check compared 84 compensated transforms using
  signed left/right semantics; maximum element error was `3.3797268126495306e-08`
  against tolerance `3e-6`.
- Native 26.3 `ItemModels.CODEC` / `CuboidModel.fromStream` execution is pending
  Master/L2. This L1 has no child-agent tools; no child was created and there is
  no child ID. Master must assign the sole test author for
  `src/test/java/kim/biryeong/destiny/fx/RecluseReloadW100Test.java`; L1 review is
  still required when that test returns. No Gradle/build/server/client/app/CU ran.

Regenerate with `rtk proxy python3 scripts/generate_reload_models_w100.py`;
read-only verification adds `--verify`. Regeneration requires the pinned local
source cache and supplied reference files. Reference bytes are pinned to force
a review if Master changes the contract. The generator writes only its W100
manifest/audit and W100 model/item namespaces; it does not write the reference
files, any original asset, shared code or W99.

## L1 first review — Master-assisted L2, 2026-10-25

Outcome: accepted for Master's central gates; no blocking source-review findings.
This is a read-only code/API review, not a claim that JUnit/native parsing or
gameplay was executed or passed by L1/L2.

- Author: Master-assisted L2 Nietzsche,
  `01a17065-6063-7b10-b99e-faec52335a8b`. Master assigned this peer because L1
  has no child-agent tools. It is not a descendant delegation/tool tree. Master
  owns closing that L2 after this review; the earlier pending-assignment/review
  statements above describe the pre-review state and are superseded here.
- Reviewed test: `src/test/java/kim/biryeong/destiny/fx/RecluseReloadW100Test.java`,
  11 `@Test` methods, frozen source SHA256
  `90c4df2588948b66c20d0f77b8d66969444339a963284fa44099f4ed2d346558`.
- Compared against generator SHA256
  `aef69a0be0a2b4f84c87ff33ce4ca56faf637dcb24b34806293b34b4ea21e97c`
  and manifest SHA256
  `f4ddf971ef78211072931a73448e6ec3fd3f2431075d07743685dbaa62b19713`.
  Read-only comparisons confirmed the test's 11 literal original pins, literal
  partition and authored motion match the accepted contract, and all 87 asset
  hashes match. Method identities are the Java method names followed by `()`.
- Coverage reviewed: 87-file inventory/hash checks; one native item codec and 86
  native cuboid parsers with malformed-context/vector negative controls; exact
  217-element/UV conservation and 256-cube budget; both exact native/twohand
  endpoints; 21 ordered float-1 frames/flag-0 grips; original full-graph fallback
  for inactive and every other context; finite transforms; independent authored
  motion; signed left/right carrier compensation; native apply versus independent
  double matrices; rigid magazine displacement at every proxy cube corner;
  reference/audit pins and explicit proxy-identification limitation.
- Exact local 26.3 API evidence was inspected with `javap` against
  `.gradle/loom-cache/minecraftMaven/net/minecraft/minecraft-merged-09aa076130/26.3/minecraft-merged-09aa076130-26.3.jar`.
  Confirmed `CuboidModel.fromStream(Reader)`, `transforms().getTransform(context)`,
  `ItemTransform.apply(boolean, PoseStack.Pose)`, codec/bootstrap APIs and the
  malformed-vector exception. Native bytecode negates translation X and rotation
  Y/Z for the left hand, applies XYZ quaternion rotation and scale, then translates
  by `(-0.5,-0.5,-0.5)`; the test's oracle accounts for these exact semantics.
  The displacement oracle reflects local X once, consistently with that native
  sign convention; endpoint assertions compare complete original display objects.
- No JUnit, builds, Gradle, server/client or app/CU actions were run for review.
  Master must run central gates. This review does not independently verify the
  proposed 829-GT/715-JUnit integration totals and does not resolve the accepted
  provisional proxy's physical magazine identity/visual fidelity.
- Write scope for this review: append this outcome to `model-notes.md` only.
  JUnit, generator, manifest and all asset/reference files were left unchanged.
