# W220 Salvager's Salvo — FIRST round-clearance correction, SECOND pending

Owned files only:
- `scripts/generate_reload_w220_salvager_s_salvo.py`
- `art/weapons/w220/salvager_s_salvo/profile.json`
- `art/weapons/w220/salvager_s_salvo/review.md`

## Source and review

Read the master source review, handling evidence and selection review under `/private/tmp/destiny-w220-source/`. Viewed the actual `sheets/grenade_launcher_83c75a3c-80A8A136-upper-chain.png` and W173 `storyboard.png` (actual gameplay above authored model poses), and read the W173 generator and manifest. The master evaluated the original Blender in a separate read-only Blender 5.4 Alpha process before implementation. This worker did not independently open or evaluate Blender and did not touch live DCC or game state.

Group `grenade_launcher_83c75a3c`, action `80A8A136`, source frames 1..89, 61 evaluated source samples. Both single-GL variants 136 and 126 were reviewed by master; 136 is an explicit shared selection, not a recovered per-weapon selector. Source weapon-local wrist excursion is approximately LEFT 21.19244 model units versus RIGHT 0.000222: LEFT handles the round, RIGHT carries the gun. Original files contain ARMATURE only; no original weapon mesh, camera or finger IK was recovered.

## Mechanical and contact decisions

Preserve all 12 W173 knots, normalized holds, grip `(8,8.155,8.25)`, hinge `(8,10.91,4.14)` and round center `(8,12.27,2.85)`. PCHIP changes the interpolation between knots, with shared C1 harmonic slopes and zero endpoint/hold/extremum slopes. Keep the original body carrier authoring in raw output; the existing master `source_weapon_display` replaces that carrier with source weapon motion while retaining body-relative mechanism transforms. Do not compose a second independent body motion, damp source axes, change limb lengths, hide support arms or introduce camera offsets.

Canonical geometry remains 101 elements. Barrel indices 0..31,36..57,73..75,85..100 (73) hinge together; receiver/stock/grip body has 28. Indices 32..35, named `breech_plug_0` through `breech_plug_3`, are fixed receiver faces and never detach. The barrel is always gun-attached and never receives magazine policy. Barrel angle remains -24 degrees at .20, -48 at .30 through .69, and closed by .76.

The existing six-volume cosmetic round and every face UV are unchanged, with no new texture or geometry. Local round offsets remain `(-3.2,.6,3.5)` at .40, `(-2.4,.4,3)` at .45, `(0,0,2.8)` at .53 and seated `(0,0,0)` at .65. Convert old visible samples 9..13 to new samples 27..39 (.45..65); sample 40 (.6667) and later omit the round, before closure begins at .69. This visibility is explicitly cosmetic, not ejection, ammunition or remote-detonation logic.

Keep W201 idle contacts and reload rotation. The round attachment uses a palm-origin anchor `[6.1,12.27,3.6]`, offset outside the case to account for actual fingerless hand thickness. The original candidate used case-side `[7.4,12.27,3.6]`; FIRST follow-up exposed that pinning a case surface directly to the interior palm origin buried most of the case. This correction adds 1.3 units of round-only barrel-local +X displacement at full attachment, with the existing envelope reducing it to zero by seat. This is authored mesh clearance, not recovered source glove contact. `partHint=round`, `policy=magazine`, `hand=left`, `rigAction=80A8A136`, window `[.45,.48,.56,.65]`: ramp into contact .45..48, full attachment .48..56, fade back to the authored seated trajectory .56..65, zero by seat. Only the round translation moves to the actual source palm; the full source shoulder/elbow/wrist chain remains unchanged. Native contact must be judged in FIRST Vision.

Framing copies the current effective GL profile (translation `[-.65,.6,0]`, rotation `[-1,2,0]`, scale `.98`, right wrist roll 28, left rotation `[15,35,-35]`) and adds only `sourceFullChain=true`, `keepMeshSupport=true`, `hideSupportAtRest=false`.

## Output and bounded verification

Pure stdlib API: `generate(root=ROOT, *, rig_path=None, profile_path=None) -> dict[absolute Path, bytes]`. Import and generation do not write. Used scratch override `/private/tmp/destiny-w220-source/grenade_launcher_83c75a3c.json`; the default rig is `art/weapons/w220/rigs/grenade_launcher_83c75a3c.json`, which master installs. Shared loaders, generated pack resources, source caches, QA, dependencies and runtime were not edited.

The returned mapping contains **371 files**: 3 geometry parents, 366 pose/grip/part children, 1 item, and 1 manifest. All outputs are confined to the assigned W220 Salvo model/item namespace and its manifest. Canonical item graph is exact at endpoints, inactive/negative progress, overshoot and non-FP contexts; ADS/inspect precede reload; native/twohand and both FP contexts remain supported. Thresholds are exact float32(i/60).

Checks passed with no generated resource writes:
- Import/generate under blocked Path write/mkdir APIs; repeated generation is byte-identical, including explicit profile override.
- All three geometry parents equal the actual prior W173 emitted models, including round UVs; correct 28/73/6 partition and fixed breech plugs.
- All 12 knots exact, constant hinge holds, dense finite/bounded curve sampling, and shared derivative continuity around interior knots.
- Rigid hinge-point alignment and round-local bore/approach offsets for all 61 poses, both grips and both FP contexts.
- Exact float32 thresholds, ADS/inspect precedence, canonical fallbacks/endpoints, and round inclusion only in samples 27..39.
- No bank Euler flip: maximum adjacent Euler-component change about 15.950643 degrees.

Actual active weapon count is **28+73+6=107**; plus 448 classic arm surface reserve gives **555**. The current canonical graph's largest parent-resolved weapon alternative has **220** elements, so the maximum known canonical/reload route plus reserve is **668**, below 1000. Alternatives are not added together. This is a bounded worker estimate; final materialized route/arm counts belong to master.

Original gameplay duration, ammunition, remote detonation, audio and timing remain unchanged. Their current inputs are hashed, not modified. Manifest also hashes current generator/profile, rig, geometry, canonical routes, texture, contact/framing, W173 source/manifest/storyboard/reference and emitted output bytes.

## FIRST review and concrete correction

Viewed actual native hip/ADS/reload sheets, raw frames03,04,05,06,07,08,09,10,11,12 and the shared post-reload sheet. Ladder sight remains clear, the barrel opens with the receiver seam intact, no fixed breech plug detachment is visible, and the weapon returns to normal hip placement with the displayed round restored. Frames04/05 partly obscure cartridge contact;06 shows the dark case beside the receiver,07 leaves a small dark sliver over the hand, and08 onward shows no obvious loose cartridge. Capture indices bracket time and are not exact generator progress; these images cannot independently prove the .65 seat.

Master's additional case-occlusion feedback prompted a check of actual current builder geometry rather than an assumed glove size. `skin_arm_models_w204.common_model/pixel_layout` gives classic forearm bounds `[6.8,1.5,6.8]..[9.2,9,9.2]` (2.4 width/depth), slim bounds `[7.1,1.5,6.8]..[8.9,9,9.2]` (1.8 width/2.4 depth). `display_at` maps local origin `[8,8,8]` to the contact; it is inside the hand, one localY unit before its Y9 end. `rig_arms.apply` retains the full source forearm rotation and multiplies Y scale by1.2525177286296538 for this rig. Thus case radius alone is insufficient clearance. Current main and worker arm geometry/builder/attachment code are identical; current main rig helper only adds W220 rig/action routing.

At source p=.48,.50,.53,.55,.56, an interior/component grid of the unchanged six case/rim boxes places roughly78-83% of diagnostic points inside the classic hand when the old case-side anchor is pinned to its palm center. This is a concrete placement issue, not a claim that PNGs prove every concealed contact. New palm-origin anchor `[6.1,12.27,3.6]` leaves only a shallow intersection with the hand surface: over81 source samples from.48 through.56, roughly4.4-13.5% of the same diagnostic points remain inside classic,3.7-6.3% inside slim. These are sampled component-point fractions, not exact union-volume percentages or native visibility measurements. Source arm pose and palm translation are not altered. Geometry, UVs, knots, pivots, attachment/visibility window and seat remain exact.

Post-correction checks passed: pure/deterministic371-file generation under blocked filesystem-write APIs; all370 raw pack bytes match the master FIRST candidate; the actual full-chain forearm and upper-arm display results are identical before/after contact correction at all61 samples. Attachment-helper differences equal only the expected envelope-weighted1.3-unit round-local displacement (maximum1.105 display units at the current raw scale); both old/new attachment shifts are zero at/after.65. Fixed plug partition, seat and pre-closure round omission remain exact.

Correction is confined to the owned generator constant and profile contact, with this review/provenance describing the actual product change. No new camera offset, source damping, limb stretching, support hiding, timing/audio/ammunition/remote-detonation change or Vision run. The generator retains the same371 outputs and107 active weapon elements; raw geometry and pose-model bytes remain unchanged. Master source-chain attachment applies the new contact when materializing hands.

Ready for master's SECOND Vision: compare case exposure/hand contact around the central open phase, fade into the original.65 seat, omission from sample40 before.69 closure, fixed plug and hinge seam, and restored hip/ADS. Source forearm/body occlusion may still hide part of insertion. No revised native visibility success or exact-progress seat proof is claimed.
