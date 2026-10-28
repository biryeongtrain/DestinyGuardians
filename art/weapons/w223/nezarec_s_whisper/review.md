# W223 Nezarec’s Whisper rigid registration — FIRST reviewed, awaiting SECOND

2026-10-28. Worker scope: exactly the W222 carrier generator/profile and this W223 review in reusable `w221-pyroclastic_flow`. No generated assets materialized, shared rig helpers changed, builds, native input, commits, source Blender edits or main writes.

## Original evidence before candidate generation

Read durable `docs/qa/2026-10-28/w223/source-review.json` and `docs/qa/2026-10-28/w223/fresh-evaluation-cache.json`; viewed `docs/qa/2026-10-28/w223/source-sheets/glaive_f9784d8f-80A8A440-upper-chain.png`. Registration comparison evidence is `docs/qa/2026-10-28/w223/registration-proposal.json`. Master has saved these files in main; worker only read them. All four profile evidence hashes match the durable files; the path migration changes no evidence bytes. Master freshly evaluated the actual original `/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return/clips/glaive_f9784d8f/blender/source.blend` in isolated background Blender 5.4 Alpha with scripts disabled. This worker did **not** independently open Blender.

Evidence: ARMATURE only, no mesh/camera; `Armature|fp_80A8A440_reload_full|Base`, `OBSlot`, source frames 1..123, 61 samples; original/cache joint error 0; master reports all inputs unchanged. Worker compared the fresh evaluated actions to the actual local W222 rig: every action/frame/joint is identical. Only `w222Source61.exporterSha256` differs. Preserve the local rig and its actual hash `73e2109a902758b6a2816de4880841c1222c559e6c867525ef0fda7d0ca93b47`; fresh evidence hash is `96b5ca34b1fa41b06dfa5113776f346384892fc1060906a8b6fe6cde3a0406cd`. Original Blender hash remains `54da85c33fc8a55ff2f532c564b740de20ce10ef61e9d3453403e0b7c4202f8c`.

Read the weapon-art skill and Ace/Izanagi study. Their geometry/UV preservation and native-view requirements apply; no geometry redesign is needed for this registration defect.

## Diagnosis and derivation

Viewed actual historical W222 SECOND `nezarec_s_whisper-{review,reload}.png` under main `docs/qa/2026-10-28/w222/vision2/screenshots`. Weapon visibility improved over historical FIRST, but a huge cyan sleeve crosses rest hip/ADS and reload samples 04/09/14. Historical SECOND is visually rejected. It is not W223 FIRST.

Old Q minimized a weapon-local grip-line rotation, using `C*Wr^T*(Lw-Rw)` against the mesh shaft. That aligns a single line but selects the unconstrained shaft twist without preserving the existing world-axis convention after the accepted native body display. Complete arms consequently point camera-left/up (right) and up (left).

Use column vectors and the actual shared `xyz` convention `R=Rx*Ry*Rz`. From real idle joints and accepted semantic contacts:

```
C = existing global X-forward/Z-up -> right/up/back convention
R = accepted native firstperson_righthand rotation (currently [-77,90,0])
Wr = orthonormalized idle weapon_basis, matching the shared helper
 a = unit(C*(leftWrist-rightWrist))
 b = unit(R*(meshLeft-meshRight))
 T = shortestArc(a,b)
 B = R^T*T*C*Wr
 Q = B*C^T
```

Thus the shared `Q*C` basis is B and the ready view mapping is `R*B*Wr^T=T*C`. Among proper rotations satisfying `T*a=b`, the shortest arc minimizes rotation away from identity (equivalently maximizes trace). Adding twist around b increases that angle; there is no free angle parameter. The minimum is 18.778326470728093 degrees. Re-derivation matches the master proposal to 1.11e-16; the proposal is comparison evidence, not a hardcoded input.

```
Q = [[-0.007607548100051909, -0.9988540797145159,  0.04725095395410554],
     [-0.1960999524377253,   -0.044844595944699146,-0.9795579466619005],
     [ 0.9805544012780868,   -0.016717944019055724,-0.19553408010356774]]
O = [0.6297219058327456, 3.7929449776060404, -0.05255995275029655]
```

Pivot policy remains `O=(rightGrip-8)-32*Q*C*Wr^T*(idleRightWrist-idleWeapon)`. Shared helpers apply this same fixed Q to weapon motion, palm deltas and both complete arm chains. Generator stays a neutral carrier. `source_mesh_basis(rig, contacts, display)` now requires the actual native display; generator independently rederives Q and validates both it and `sourceRetarget`, so a profile-literal-only edit cannot pass. W222 output namespace/stage remains intentional; W223 corrects its registration.

Native rest elbow minus own wrist, including accepted uniform scale 1.25, in display right/up/back model units:

| Arm | Right | Up | Back |
|---|---:|---:|---:|
| Right | 5.140032 | -7.566487 | 4.460226 |
| Left | -5.885781 | -6.679691 | 4.929980 |

These match the proposal and point outward/down. They are coordinate evidence, not rendered visibility evidence.

## Lightweight checks performed

Python `-B`; no persistent test files or assets. Checks operate in memory against real input files and existing shared helper functions.

- Q determinant 1.0; orthogonality max error 2.22e-16; mesh/source grip-direction residual 5.38e-17. All 360 sampled nonzero world-axis twists increase correction angle; analytic constrained-shortest-arc argument above supplies the general result.
- Fresh original actions equal the local 61-bank exactly. Across all 61 raw samples, rigidly mapped limb-segment lengths differ by at most 1.11e-16 source units; weapon conjugation preserves source rotation angles. Fixed Q changes adjacent forearm rotation angles by at most 3.72e-13 degrees.
- Existing shared `source_weapon_display`, `source_palm_translations`, `apply`, and `upper_arm_displays` evaluated on 61 poses × native/twohand × left/right FP contexts × both arms = 488 side/context/carrier samples. All finite; Euler matrix round trips pass; ordinary forearm length rounding error <=2.92e-8 model units. Helpers were read and used, never edited.
- Pure generator returns 125 files deterministically (124 pack files + manifest), with an audit hook rejecting file writes/mutations/process launches. No assets materialized. All 122 carrier child displays are exact, body geometry/UV equals input, thresholds are exact float32(i/60), canonical endpoint/ADS/inspect/non-FP fallback graph preserved.
- Old Q is rejected by regenerated derivation validation. An in-memory accepted native-display change of +7 degrees, together with dynamically recomputed Q/provenance, regenerates successfully: no old-Q hardcode remains. This test does not change the real accepted display.
- Current body 148 elements; canonical 246; conservative four-arm reserve 448; maximum estimate 694. Actual integrated route count/visibility remains master-owned.

## Assumptions and required native sequence

C is the existing global **orientation convention**, not a recovered source camera extrinsic. Original has no weapon mesh/camera/finger IK. This is rigid mesh registration calibration under that explicit convention.

The constraint aligns grip **directions**, not distances: source wrist separation ×32 = 12.83002755 model units versus accepted mesh grips 3.3. Shared per-palm contact offsets preserve both calibrated ready contacts without rescaling source limbs or motion. This is not an exact rigid fit of an unavailable original mesh. Accepted body display, right [8,8.7,8], left [8,12,8], estimated fixed port [7.55,6.35,8], full source travel/lengths, 62-tick gameplay duration/audio/ammo, native/twohand/ADS/inspect routes all remain inputs.

Raw source bank has fast right forearm relative rotations: 103.865 degrees over p=0..1/60 and 86.600 degrees over p=.55...5667; left maximum 41.665 degrees over p=.2833...3. Raw adjacent weapon maximum is 25.172 degrees. These exist before Q and are preserved; no source attenuation is introduced. Existing shared endpoint easing/interpolation is unchanged. Native review should inspect these regions and endpoint recovery; no continuous-60fps or flip-free-render claim follows from 61 offline samples.

| Mandatory stage | Current state |
|---|---|
| Original Blender evaluation + viewed sheet | Master evaluated; worker read evidence and viewed sheet |
| 61-pose candidate | Complete in memory; source unchanged |
| W223 FIRST Vision | Master captured; same worker viewed both sheets plus raw hip/after-reload/reload07/13 |
| Same-worker FIRST feedback/correction | Complete: justified no-change product; provenance and review updated only |
| W223 SECOND Vision | Pending after feedback/integration; no final acceptance before this |

SECOND review targets: rest hip/ADS sleeve placement; native and twohand grips; right-hand port activity/left support; reload 0/.2/.4/.6/.8/1 with attention to early and .55 transitions; complete-arm contact; postreload rest/ammo return; preserved inspect/ADS routes. Master owns all native client/input. No arm hiding/stretching, new camera lift/lower/depth, free twist, or source-motion damping is an allowed correction.


## Mandatory same-worker FIRST review — no product correction

Worker inspected the actual FIRST PNGs supplied by master from `/private/tmp/destiny-w223-pass1-retry-native`, then re-viewed the durable original upper-chain sheet and compared the durable fresh cache with the actual local rig. Master performed original Blender evaluation and native client/input; worker performed evidence inspection only. No independent Blender/native execution is claimed.

| FIRST evidence | Worker observation and consequence |
|---|---|
| `screenshots/nezarec_s_whisper-review.png` | Hip/ADS center is clear of the former cyan sleeve crossing. Blade/shaft remain visible. Ready right forearm remains visually large at lower right; left chain is largely below frame. This agrees with mapped outward/down rest elbows and does not establish a wrong rest axis. |
| `frames/w223-nezarec_s_whisper-hip.png` | Raw frame confirms weapon in front of lower-right brown forearm; reticle clear. Left below-frame placement is not evidence of arm hiding: full-chain/support settings remain enabled. |
| `frames/w223-nezarec_s_whisper-after-reload.png` | Visually returns to initial blade-forward/right-forearm placement, HUD 7 rounds. Compare actual images; no pixel-exact or temporal-interpolation claim. |
| `screenshots/nezarec_s_whisper-reload.png` | Samples01/07/13/19/25 show changing weapon and complete arm placements, with center remaining clear in the sampled images. No recurrence of the historical rest/ADS center-crossing cyan sleeve defect. |
| `frames/w223-nezarec_s_whisper-reload-sample-07.png` | Large cyan upper-arm volume occupies lower-left and partly covers the lower HUD; brown forearms/shaft occupy the lower half. Reticle and central forward view remain clear. Residual lower-field occlusion is recorded, not hidden or called exact source-camera recovery. |
| `frames/w223-nezarec_s_whisper-reload-sample-13.png` | Weapon runs diagonally through lower left, brown forearm extends from below, opposite arm clipped at right edge; central view is clear. This sample supplies no evidence of a static registration inversion. |

Against source: the original sheet shows substantial shoulder/elbow/wrist reconfiguration throughout the action. The fresh 61-bank is identical to the actual replay input. The ready elbow vectors point outward/down, and the unchanged proper Q rigidly transports all source rotations/segment lengths. Large apparent arm size under the accepted native scale/perspective, or a moving upper arm entering the lower field, does not alone identify a faulty registration derivation. Source has no mesh/camera to establish exact original projected arm size or screen location.

The raw source-fast-transient caveat remains: right weapon-relative forearm steps 103.865 degrees at p=0..1/60 and 86.600 degrees at p=.55...5667 already exist in the original bank. A static PNG labelled07 is not a measured source-progress tag, and these sparse samples cannot prove that particular transient has the same timing or prove smooth playback. FIRST also does not resolve detailed finger/port contact. SECOND should retain the lower-left occlusion and fast transitions as explicit review caveats; do not suppress source motion to obtain a cleaner image.

Decision: **no evidenced derivation defect; retain the product unchanged for SECOND.** Do not modify Q, contacts, source lengths/full motion, geometry/UV, native body display or existing routes. No camera offsets, hiding, stretching or damping. This is the required same-worker feedback outcome, not final visual acceptance.

FIRST image SHA-256, in the table order above (reload sheet listed fourth):

```
fd92a7435b0f86de3ed8b681c02f6224213a101c6ae9252ed4737562f47454d1  screenshots/nezarec_s_whisper-review.png
9fea4881c05bd344e68f15301987f6a5bc6b97cfde76bbfe6129c98c2d36a298  frames/w223-nezarec_s_whisper-hip.png
29b4f7bbd22d3befba0713b1abb5dbe82588611fea6d16c5635c665dc24a5786  frames/w223-nezarec_s_whisper-after-reload.png
65fbc6aa94b0fba77a6d4371a4844d6140f2f08fcfec88cfedd92bf3a36142a4  screenshots/nezarec_s_whisper-reload.png
ee42ee4dc7312ddfd0f22a3f22d257bcbbee2ae969c7dcaf4c2b2774f273ffca  frames/w223-nezarec_s_whisper-reload-sample-07.png
f266e87969ddda057e651bdea7ce2fba52ce61d90997d7da408a4ccf37231446  frames/w223-nezarec_s_whisper-reload-sample-13.png
```

FIRST captures above identify the runtime evidence actually viewed; their archival location remains master-owned. The four original evaluation/cache/sheet/proposal references are now durable repo paths and hash-verified.

Feedback delta: only this review and profile evidence/notes changed; generator SHA-256 remains `15e486f2deda60627fd2105d5992e9c140cae23b0b590b0db0ab13fd97d0da2a`. In-memory before/after generation returns125 files, with all124 pack outputs byte-identical and only the returned art manifest changing due to profile provenance/notes/hash. No output was materialized. Master reported original rigid-source regression2/2 passing; worker did not rerun that master regression or build/native checks. SECOND remains pending.


## SECOND review — current outcome, 2026-10-28

This appended outcome supersedes the earlier FIRST-stage title/table and pending statements, which are retained as history. Worker viewed actual SECOND `screenshots/nezarec_s_whisper-review.png`, `screenshots/nezarec_s_whisper-reload.png` and raw `frames/w223-nezarec_s_whisper-after-reload.png` under `/private/tmp/destiny-w223-pass2-native`, and read `native-validation.json`. Master operated the original source evaluation and native input/client; worker inspected their evidence and made this documentation-only append.

SECOND observations: rest hip and ADS retain a clear central reticle/forward view; the previous center-crossing cyan sleeve does not recur in the reviewed sheets. The right ready forearm remains large at lower right. Reload sample07 again shows substantial cyan upper-arm volume at lower-left, partly occluding the lower HUD; sample18 also has cyan arm volume entering from the lower-left/bottom edge. Central view stays clear in these selected images. Samples13/24 retain visible weapon/arm motion. The raw postreload capture recovers the blade-forward ready placement and HUD **7/30**. These are bounded observations of actual PNGs, not exact source projection or continuous-motion certification.

The validation record contains seven native sequences, no partial interrupts, and `neutralAfter=true`; all three listed Nezarec fire/reload/ADS sequences have `released=true` and all native movement inputs false. It records final ammo7/30 and thirteen distinct server progress samples from0.016666668 through0.95. Those thirteen samples demonstrate intermediate source-bank progression, not full temporal coverage of all61 poses or continuous60fps. Master reports all seven sequences completed neutrally and owned server/client stopped with exit0; process cleanup was performed by master, not by this worker.

Master additionally reports the full hands125377-output digests identical and tested jar unchanged between FIRST and SECOND. The product was retained after FIRST; feedback changed only provenance/notes and review. The worker's prior in-memory comparison separately established all124 neutral carrier pack outputs unchanged, only its returned art manifest affected by profile provenance. This SECOND append changes neither profile nor generator and materializes nothing; no unnecessary product change or rebuild is introduced.

| Mandatory stage | Current outcome after SECOND |
|---|---|
| Original Blender evaluation + viewed source sheet | Complete: master evaluated actual original read-only; worker inspected evidence/sheet, no independent Blender-opening claim |
| 61-pose source candidate | Complete: original action preserved, fixed proper registration, source lengths/full motion retained |
| FIRST Vision | Complete: master native execution/captures, same worker inspected sheets and raw evidence |
| Same-worker FIRST feedback/correction | Complete: no evidenced derivation defect; justified unchanged product, durable provenance references/notes only |
| SECOND Vision | Complete: master native replay, same worker viewed both sheets and raw recovery; bounded center-obstruction fix accepted |

**Acceptance is limited to the rest/ADS central-obstruction correction and observed postreload recovery in these reviewed scenarios.** It does not accept every arm projection, handling contact, view route, temporal artifact or performance condition. Lower-left upper-arm/HUD occlusion around samples07/18 remains an explicit limitation. No cosmetic suppression was applied.

The source-fast-transient caveat from FIRST remains: original right forearm relative steps103.865degrees at p0..1/60 and86.600degrees at p.55...5667 are preserved by fixed Q. PNG sample numbers are not exact source-progress tags. Sparse captures and thirteen server samples cannot certify smooth/flip-free interpolation, continuous60fps or precise alignment of those fast events. Existing source easing/interpolation remains unchanged.

C remains an existing global orientation convention used for mesh rigid registration, not recovered source camera extrinsics. Original has no mesh/camera/finger IK; source/mesh grip-distance mismatch and separate accepted contact offsets remain documented. No claim of exact original projected anatomy, finger/port contact, recovered detachable-part events, microphone/audio-listening verification, exhaustive twohand/inspect/third-person coverage or performance certification follows from this review. No camera offsets, arm hiding/stretching, free twist or source attenuation were added.

SECOND evidence SHA-256 (runtime archive relocation remains master-owned):

```
f815c34aa0bf903bd1b7d01c21d3e3e14acdd6db2ddf885a58a4aab526337aee  native-validation.json
ca80bd9acb5d8689152c67ff683aac7e87ba1f979655ae80417e9410f17fc9b9  screenshots/nezarec_s_whisper-review.png
691cab0f357adb60416ade8bd9c2e5394396a50f2a0b8bdb956251cca6b35ffa  screenshots/nezarec_s_whisper-reload.png
3c51c84a9aa67e4c7c9b0c0da00b33d34c7840c24e0a2404a395a9dabb959ef8  frames/w223-nezarec_s_whisper-after-reload.png
```

Final worker delta for this step: append this section only. Generator remains SHA-256 `15e486f2deda60627fd2105d5992e9c140cae23b0b590b0db0ab13fd97d0da2a`; profile remains SHA-256 `f52c7947f81f21bd89aed26f9de6f0c0c4b70c15cf51f4faadc0a27e0b1b8fa4`. No build, materialization, native input, commit, main/source edit or worktree removal. Reusable worktree retained for master closure.
