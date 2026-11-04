# W198 Izanagi dense source animation bank

The W91 namespace and item wrapper now provide 61 samples / 60 intervals
(previously 21 / 20), resampling the identical W197 curves. Slot6 ordinary0..1 /
Honed2..3 / charged4 / idle-1 lifecycle, grip and ADS/scope/inspect routing remain.
This worker leaves runtime Java to master (60-interval quantization and collision
checks). Gameplay deadlines, charged accents and three original atlases remain.
Float32 thresholds match Java division/base addition, with generation offsets
0, .00025 and .0005 staying inside the intended bucket for both reload modes.

Ordinary samples come from evaluated80A8A140. Honed cosmetic samples use the
80A8A14D reload_special candidate; exclusivity and actual Honed trigger are NOT
confirmed. Both clips are very similar; no exaggerated authored curve is added.
The bolt stays stationary relative to the root within FBX numerical tolerance
(<0.00012deg, <4.3e-7 source units); no authored bolt cycle is added.
The compact W197 dataset contains all102 source frames for root4A0810C4,
magazine52EDE88C and bolt69768858, with rest matrices, hashes and conversion.
72997168 remains unmapped. No hands/IK/contact or source events are invented.

Source armature-object cumulative matrices are orthonormalized only for tiny
FBX numerical scale/shear, then quaternion interpolated. The outer .01/axis
matrix is recorded and never baked. Each clip frame1 calibrates to accepted W84
neutral. Root motion uses its neutral basis, parts use independently sampled
root-relative motion, with target-anchor compensation. XYZ is extracted only
after matrix composition; Euler channels are never added. Basis/scale/anchors
and retiming are explicit in the dataset. Progress maps linearly to3.366667s;
existing gameplay timing wins. Only final progress .9..1 blends to exact accepted
neutral. Native left-hand reflection and crossbow twohand inverse are preserved.

Original79 cubes/474 face UVs are partitioned body76+magazine1+bolt2. Cube26 is
magazine. Cubes25/77 form the longitudinal rear bolt sleeve behind the magazine,
adjoining receiver36 at Z16.45625 and ending near25.45625;77 is its diagonal
companion surface. This coordinate-based mechanical mapping is inferred, not
extracted skin weights (the source model groups are generic). No mesh, UV,
grip/ADS, charged95-cube geometry or scope plane redesign occurred.

Reproduce: rtk proxy python3 -B scripts/generate_izanagi_presentation_w91.py
Check: rtk proxy python3 -B scripts/generate_izanagi_presentation_w91.py --verify
Optional provenance rebuild: same generator --extract-source /absolute/path/to/
sniper_rifle_ececad46.json.gz (W196 evaluated evidence read-only). Normal generator
and verify require neither SSD nor Blender. Originalhash baseline is unchanged;
source dataset SHA and source tags are recorded separately in outputmanifest.
The W197 dataset stays byte-identical, including its historical 21-sample note;
W198 density is recorded in this handoff and outputmanifest instead.

Offline PNGs use progress .2 (source time .673333s) to show withdrawal.
Existing bbmodel frame07/14 and10/17 names keep W197 snapshot progress
.35/.70 and .50/.85 (dense indices21/42 and30/51); their bytes stay unchanged.
Offline PNGs/bbmodels bake mechanical rigid motion and use the body display.
They are software previews, not native/contact evidence. Master must check
actual1P/3P transitions, mechanical assignment/axis sign, hand contact, endpoint
settling, cancel/swap cleanup and slot6 timing in centralized native QA. This
worker ran no Blender/Blockbench/server/client/CU/Vision or Gradle.
Vanilla held-item updates remain limited to 20TPS with no per-render pose
blending; a denser bank reduces quantization and does not promise 60FPS motion.
