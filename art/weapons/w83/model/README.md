# W83 Ace of Spades model sidecar

Direct conversion of the supplied `Ace.bbmodel`: all 87 cubes, all 522 face UVs,
all 41 rotated cubes and the embedded 512x512 RGBA PNG survive. No silhouette
substitute, voxel reconstruction, palette repaint or resampling. Geometry only
receives one uniform translation: the rotated center of source element82 (main
grip) becomes [8,8,8]. Per-face 64-unit authoring UVs become native 16-unit UVs by
division by4, including reversed rectangles. PNG bytes remain identical.

The original stays external/read-only; its SHA256 and source display settings are
in manifest.json. No full bbmodel copy, author filesystem paths or embedded project
metadata are distributed. Attribution/license beyond the Bungie design was not
supplied. This is local review material, not a license grant.

From the repository root:

    rtk proxy python3 scripts/art/build_ace_w83.py
    rtk proxy python3 scripts/art/build_ace_w83.py --verify
    rtk proxy python3 scripts/art/build_ace_w83.py --source /path/to/Ace.bbmodel --verify

Python standard library only. The source SHA is pinned and mismatches fail before
writes. --verify rebuilds every output in memory, checks exact bytes and unexpected
Ace output files, and never repairs/writes. Manifest hashes cover all generated
outputs except itself; the generator is an input hash. No timestamps or absolute
machine paths enter output. The source itself is needed to reproduce the outputs.

Item identifiers:

- destiny:weapon/ace_of_spades: CMD string0 hip/ads/inspect/scope; missing/unknown
  uses hip. Scope intentionally aliases iron-sight ADS, without an optic overlay.
- destiny:weapon_aim_w70/ace_of_spades: W70 display-context wrapper and float3
  range dispatch; 21 samples at0,.05,...,1. Boolean0 selects native/twohand in
  every frame. Inspect takes priority over stale positive aim progress. Other
  display contexts use the original static pose select. Runtime/catalog belong
  to the parent task. Every model reference resolves inside these new Ace assets.

The source RH first-person scale4 and translation[25.5,-4.75,-37.75] differ from
its LH pose; source third-person rotation is absent. These displays are replaced
with authored transforms. Native first-person left-hand X translation and Y/Z
rotation reflection happens in ItemTransform, so both JSON hands store the same
pose. ADS aligns two selected source rail anchors to the idle camera center ray;
hip solves pitch/yaw for the actual barrel bore to meet that ray four blocks
ahead, retaining a lower-right resting position. Third-person [-90,180,0] inverts
the complete vanilla ItemInHandLayer Rx(-90) Ry(180), retaining both upright +Y
and forward -Z geometry, with the handle at the held-item pivot. The W30 Rx90
alone would retain muzzle direction but turn the source upside down here.
Twohand follows W30's first-person carrier inverse; its third-person rotation also
inverts the level-head primary crossbow arm Ry(-.3*sign) Rx(-pi/2+.1) from native
AnimationUtils.animateCrossbowHold. Both hands and all three basis axes are
checked. These are static mathematical poses, not runtime IK.

Native26.3 CuboidModelElement.Deserializer was inspected from the existing local
Minecraft jar via read-only javap. It accepts rotation origin + scalar x/y/z +
rescale (EulerXYZ); all source rotations are supported. Item display rotations
remain ordinary [x,y,z] EulerXYZ arrays. Source rotations are single-axis, so no
Blockbench/native multi-axis order ambiguity arises.

offline-preview.png is a deterministic software z-buffer preview with the exact
atlas: top-left side; top-right three-quarter; bottom-left hip; bottom-right ADS.
Bottom views use a70-degree square camera and idle vanilla carrier, with red
center marks. Lighting is illustrative. It does not reproduce Minecraft atlas
stitching, native bake, hands, FOV changes, bob/swing, reload, active item use,
third-person arm animation or clipping under every runtime condition.

pose-checks.json records independent geometry-vertex, UV, reference-resolution,
both-hand ADS center, twohand carrier inverse, threshold-offset and third-person
axis checks. Native codec execution, native visual testing, runtime/catalog and
gameplay verification remain the parent task's responsibility. No Gradle/game
launch, production Java/data edit or Blockbench/Blender interaction was used.
