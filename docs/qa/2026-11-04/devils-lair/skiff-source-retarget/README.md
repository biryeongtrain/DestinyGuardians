# Native skiff skeletal motion → normalized Drive display rig

Converted six source-tagged clips into the current shader-baked candidate with `scripts/strikes/retarget_skiff_motion.py`. Production models/JAR remain unchanged. `validation.json` pins the candidate and scripts; `retarget.json` records all inputs, original source FBX identity, sample counts, errors and auxiliary-bone policy. The converter rechecks the original motion FBX SHA256 before writing and refuses an input overwrite or a model already containing animation.

## Coordinate correction

The earlier raw Drive/native inspection required Z180 alignment. **The shader bake cache is already normalized into native source coordinates.** Applying Z180 again produced 10–17 unit head errors. Direct comparison of the actual bake cache and native motion rest pivots yields a maximum error of 0.000002055 source units. Do not carry the raw-scene alignment into this normalized converter.

Imported bone rolls differ. The conversion therefore uses world-space skin deformation `pose * inverse(rest)`, applies that deformation to each normalized Drive pivot, converts to Minecraft axes/16 model pixels per source unit, and derives parent-relative display motion. It does not copy native local Euler values onto a different bone basis. Nonrigid deformation beyond float tolerance is rejected rather than silently stripping meaningful scale/shear.

Every original Drive bone's hierarchy and bind origin are checked, including the ten additional bones. Additional bones and generated glow children retain their authored parent-relative bind transform and inherit their parent motion; no source keys or guessed hash mappings are invented for them. The unweighted independent `pedestal_001` root stays independent.

## Source limits and validation

- Four imported clips contain one constant sampled pose despite longer frame-count metadata. They are emitted as explicit holds spanning `(manifestFrames-1)/30`; this uses the existing sample-span convention and does not reconstruct absent keys. Two changing clips contain 81 and 121 samples at 30 FPS.
- Only mapped bones `unk_2671741570` and `unk_2681882356` show substantive rotation in the changing clips. Their serialized component spans are approximately 22–26 degrees. No extracted flight translation exists in these sources.
- Source tags remain `source_80a8a4e2`, `source_80a8a51d`, `source_80a8a51e`, `source_80a8a51f`, `source_80a8a520`, `source_80a8a521`. No unsupported arrive/drop/depart aliases were assigned. Future root flight paths must be labeled authored separately.
- Reconstructed hierarchy after five-decimal key serialization: maximum position error about 0.0000161 model pixels and maximum rotation-matrix component error about 1.26e-7 over every source sample. Geometry, textures, hierarchy and non-animation model fields compare equal to the input candidate.
- Five focused Python tests pass: rest-roll independence, rejection of nonrigid deformation, continuous Euler branch reconstruction, auxiliary hierarchy/input preservation and constant hold timing, and rejection of altered auxiliary parenting.
- `motion-comparison.png` shows actual **offline Blender** renders at start and midpoint of 80A8A51E from matching cameras. The side components change orientation and the attached lights remain with them. This is not a Minecraft framebuffer or a claim of smooth native playback. Hull stippling remains visible and unaccepted.

Remaining: native BetterModel compilation/playback, continuous intermediate-pose checks (including engine Euler/quaternion conventions), source-derived animated hull envelope, authored root trajectories using the sweep/terrain helpers, bounded chunk ownership, one-ship-per-zone generation lifecycle, actual spawn-pad association, departure and cleanup. No visible strike skiff has been activated by this batch. No completion commit or full-goal acceptance.
