# W330 Spectral Blades source motion candidate

User-supplied `Destiny-Light-Abilities-2026-10-28` source, directly evaluated in a separately owned headless Blender process. Original source files were read only. `blend-inspection.json` records 72 source bones, all 13 actions, action slots, source rest matrices, and the outer FBX transform. The exported nine actions use their original 30 fps action duration; original live Destiny gameplay speed has not been independently measured.

Run from the worker repository:

```sh
rtk proxy /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup /Users/qf/Downloads/Destiny-Light-Abilities-2026-10-28/Destiny-Light-Abilities-2026-10-28/animations/hunter_spectral_blades/source.blend --python scripts/art/w330_spectral_blades.py
rtk proxy qlmanage -t -s 2400 -o /tmp/w330-super-motion art/animation/w330/spectral_blades/source-target-review.svg
```

`spectral_blades_w330.animation.json` is an integration payload for `/destiny/animation/spectral_blades_w330.animation.json`; it does not edit the shared W230 file. Target clip names retain the `w230_hunter_spectral_blades_` prefix. Runtime/SourceAnimationGrid integration is owned by the runtime worker and master.

| Phase | Original action | Duration | Provisional contact |
| --- | --- | ---: | ---: |
| start | 80A8AAC4 | 1.566667 s | no damage contact |
| start_air | 80A8AAD0 | 1.600000 s | no damage contact |
| attack | 80A8AAC8 | 1.466667 s | 0.300 s |
| attack2 | 80A8AAC7 | 1.466667 s | 0.225 s |
| attack3 | 80A8AAC5 | 1.733333 s | 0.150 s |
| attack_air | 80A8AAF8 | 0.833333 s | 0.300 s |
| attack3_air | 80A8AAE5 | 0.966667 s | 0.150 s |
| heavy | 80A8B4F5 | 1.000000 s | 0.075 s |
| heavy_air | 80A8B55A | 0.900000 s | 0.075 s |

Contact candidates are the first 90%-of-peak source wrist speed within the first 72% of the action. These identify acceleration/sweep beats for native tuning; they are **not decoded original damage events**. `clips.json` events contain unidentified/audio tags, so the payload explicitly marks contacts provisional. Recovery retains the complete source follow-through. Cast metadata has an inert wrist-speed candidate but runtime must not treat cast as a damage clip.

The new idle and air loops hold the corresponding original cast's exact final guard. The move loop combines that source upper guard with existing authored root/pelvis/leg/cape locomotion, resampled to 40 Hz; it is a mixed-source adaptation, not an extracted Destiny locomotion clip. No idle breathing was invented.

The existing segmented player geometry, group bind rotations, and item pivots are preserved. Torso/head use independent rest-relative source rotations; two-link arm IK adapts limb lengths, then each wrist's original rest-relative orientation controls its own knife attachment. Leg flex comes from the anatomical knee plane. Source horizontal locomotion is omitted because runtime owns entity travel. Ground root height fits the target skin support plus source foot lift; air height is a bounded pelvis offset. These are retarget adaptations, not a claim of an identical Destiny skeleton.

All exported rotations have continuous equivalent Euler representations and hemisphere-continuous quaternion metadata in target Blockbench `Rz * Ry * Rx` convention. Source keys already had coherent quaternion signs (zero source sign corrections); some source acrobatic motions genuinely rotate quickly. The exporter preserves those motions rather than smoothing them into an invented swing. The runtime worker applies quaternion interpolation before the shared 40 Hz compilation path.

First native baseline reviewed: `baseline-spectral-clean-03.png` showed wrists/arms packed into the center during cast; `baseline-spectral-clean-14.png` showed folded torso/short apparent follow-through. This candidate separates hip/waist/chest and restores both wrist orientations, retains the full source recovery, and provides distinct ground/air actions. `source-target-review.png` is a static orthographic diagram from directly evaluated source and target poses, not a native render. It cannot certify final knife grip, skin-cube overlap, or visual smoothness. Master second Vision remains required; no live client, server, or shared fixture was operated by this worker.

## Source-detail revision after W332 native review

The user's later correction requests more detailed motion per bone, with original speed retained. The baseline exported rotation only for torso/arms: measured source parent-local waist displacement reached1.6465 model units, chest0.0799, left/right clavicle-plus-shoulder2.2390/2.2481. Those source translations now have actual position channels on the existing pivots. Arm IK uses the translated shoulder and keeps the previously accepted wrist/knife world position and orientation as hard constraints; reach-limited frames reduce shoulder displacement rather than stretching a disconnected limb. Maximum reach correction is1.7283 units.

The source lower-arm axial roll is measured relative to its transported anatomical bend plane and applied independently to the existing forearm. Equipment position and local rotation counteract that roll. The supplied source has little additional axial roll (left approximately-0.3163..0.1703 degrees, right-0.0500..0.0475); it is not amplified to invent motion. The main recovered detail is spine/clavicle translation and the resulting elbow trajectory. FK wrist/knife residuals are at most4.1e-15 model units and1.71e-6 degrees; the equipment point remains inside the existing broad hand cross-section. These are static geometric checks, not native visual acceptance.

The pelvis root-relative displacement reaches24.484 units and includes whole-body leap/travel already represented by the current root/entity movement policy; it remains excluded. All12 clip lengths, original40Hz timestamps, root channels, item scales, and contact/recovery/entry/exit metadata compare unchanged against current main. Audio and geometry are untouched. `detail-review.png` compares four representative actions before/after. The historical `evaluated-source.json` stays unchanged; the current raw evaluated cache is only `/tmp/w332-super-review/spectral-detail-evaluated-source.json` and is excluded from the returned delta/commit. Master ground/light/heavy/air native recheck remains pending.
