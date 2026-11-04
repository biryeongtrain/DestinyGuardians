# W212 Bygones candidate review

FIRST native review complete: evidence-based no product change. Final native acceptance
remains pending master SECOND Vision.
This worker owns exactly the new generator, profile and this review. The master
owns output materialization, the new manifest, shared loader/runtime/rig cache,
hands generation, tests and native QA. No additional workers were instantiated.

## Source inspected

- Read master's original-Blender evaluation report at
  /private/tmp/destiny-w212-source/source-review.json. It reports Blender 5.4.0
  Alpha, OBSlot action Armature|fp_80A8A36A_reload_full|Base, source frames 1..105
  at 30fps, 61 evaluated samples, prior-cache joint error 0 and
  allInputsUnchanged=true. Source blend SHA-256:
  042a9965b8f02a7e7bfda10914e2711b31e2add9417884d8b277e11ab9668f4d.
  The worker did not independently open/evaluate the .blend.
- Read the supplied pulse_rifle_b4d01502.json and viewed
  sheets/pulse_rifle_b4d01502-80A8A36A-upper-chain.png with view_image.
  All61 samples include shoulders, elbows, wrists and weapon, uniformly
  distributed across normalized progress. The six-pose XZ/YZ sheet shows
  changing upper/forearm bends during exchange and a close return to idle.
  Matrix start/end max absolute difference is 1.2844815501011908e-5, not exact
  equality. Cache and report both name Armature|fp_80A8A36A_reload_full|Base.
  The earlier Base.001 note was a worker documentation error, corrected during
  FIRST review; action selection and generator were unaffected.
- The original scene has Armature only: no mesh, hands surface or camera.
  Matrices are armature-object space, row-major with column vectors; no
  matrix_world application. This evidence establishes source bone motion,
  not original mesh fit, camera/FOV, finger IK or native clearance.
- Read the original non-fallback source-map.json. Cold Denial is the
  representative; selector 7B4E9613 is shared with Bygones, Chattering Bone,
  Blast Furnace and Claws of the Wolf. 80A8A366/368/36A each carry reload_full
  and reload_empty labels. 80A8A36A is the requested candidate, not a proved
  weapon-exclusive action.
- At the existing authored 32 model-units/source-unit calibration, source
  forearms are about 8.14136 and upper arms 8.7266 model units. Retain these
  ordinary lengths; no stretching or camera invention is proposed.

## Mesh, contacts and motion

Viewed the actual W134 comparison sheet with view_image and read the current
design, canonical model, accepted twohand display and w201 contact evidence.
The recognizable walnut stock/grip/forewood, green receiver, open trigger bow
and optic channel remain untouched. The canonical model contains 129 opaque
cuboids and unchanged face UVs.

The exact W168 semantic partition is retained: body 124 plus moving 5.
Moving indices 106..110 are magazine, magazine_shoulder_-1,
magazine_shoulder_1, magazine_front_spine and magazine_floorplate.
receiver_keel 82, stock_belly_join 98 and stock_toe 99 stay body; there is no
explicit magazine_socket solid. Retain the existing contact partHint moving.

Right [8,8.55,8.45] is the walnut firing grip, left [7.8,9.12,-1.9] supports
the forewood, and reload [7.35,7.65,12.2] approaches the slanted rear magazine.
The profile inherits these palm positions and rotations. No new explicit
right/left contact overrides are warranted after the supplied FIRST native views.
Right stays body-relative while left follows moving only during handling.

The profile enables sourceFullChain=true, keepMeshSupport=true and
hideSupportAtRest=false. Existing pulse-rifle translation [-0.65,0.6,0],
rotation [-1,2,0] and scale 0.98 are copied; inherited rightWristRoll 28 and
leftRotation [15,35,-35] are retained. This framing is authored calibration,
not recovered source camera data. Weapon and source wrists must use one
parent frame; shared retargeting and upper-arm emission belong to master.

The generator ports W168's rigid pivot/carrier algebra using only the standard
library, retaining all12 authored keys and every hold. W208 weighted harmonic
PCHIP replaces per-key smoothstop: shared C1 tangent at ordinary knots and zero
tangents at holds, extrema and endpoints. The body holds .22..57, detached
magazine .30..48, magazine seated through .065 and again from .68. Phase
boundaries and gameplay duration are unchanged; intermediate velocities change
intentionally. Authored part motion is not a recovered source magazine path.

The only pack namespace returned is weapon_reload_w212_bygones/bygones.
generate(root=ROOT) returns absolute Path:bytes without writes, including the
master-owned manifest as bytes only. It emits61 float32(i/60) thresholds,
progress float index1 and grip flag index0; ADS/inspect precede reload dispatch,
negative/non-FP fallback and both endpoint graphs remain canonical.
Endpoint leaf displays are exact native/twohand copies. All non-FP leaf
contexts remain accepted values. No historical generator is executed.

## Checks

- Waited for private Git worktree-batch.json status ready before creating any
  owned file. Baseline fingerprint:
  5728d043ce9f9a3ed93855debafbff261c2cbf4801bf444a83aae5ec09b0079f.
  All three owned files were new and absent from the baseline. Reviewed source,
  W168/W208 generators, contacts and family framing matched seed baseline hashes.
- Executed import-equivalent compilation and targeted Bygones generate(root)
  twice with write-mode open and Path mutation operations forbidden. Both runs
  returned identical248 absolute Path:bytes entries:247 pack assets plus the
  master-owned manifest bytes. No returned path was materialized. Input/output
  SHA-256 tables matched actual input bytes and output mapping bytes.
- Verified every original authored key/partition/pivot constant via AST without
  importing the old generator or its heavy dependencies. All61 new displays
  matched selectively evaluated W168 algebra with the new sampler substituted.
- Verified exact124+5 canonical element/face-UV partition, textures, both
  native/twohand endpoint displays and all non-FP leaf displays. Euler matrix
  round trips stayed below1e-10 residual; maximum adjacent Euler component
  change was16.289245405 degrees, with no branch flip in the61-pose bank.
- Checked101 samples per authored span: no channel overshoot, all authored
  knots exact, holds preserved; finite-difference left/right derivative gap at
  1e-7 distance from knots was at most0.0012664713722188026. Invalid/non-finite
  sampler progress was rejected. This checks the analytic curve, not native
  continuous interpolation.
- Verified61 strictly increasing float32(i/60) thresholds, progress index1,
  grip index0, canonical endpoint/negative/non-FP fallback graphs, ADS/inspect
  precedence, and retained hand_animation_on_swap metadata.
- Verified profile schema/weapon, sourceFullChain, keepMeshSupport,
  hideSupportAtRest=false, requested action80A8A36A and partHint moving.
- No Gradle, complete pack pipeline, native QA input, output materialization,
  commit, stash, reset or push. Shared W212 loader/runtime/cache changes remain
  master-owned; this worktree intentionally retains its seed shared files.

## FIRST native review returned to master

Decision: no product correction. The generator SHA-256 remains
5567b64438a56a51f38703471c2b584574543f99d1ef35708550033c280e8331.
Framing and contacts are semantically unchanged; only profile evidence/notes and
this review were updated. No main/shared/QA files were written.

Viewed with view_image:

- /private/tmp/destiny-w212-pass1-native/screenshots/bygones-review.png:
  hip central view is clear and the ADS optic aperture stays centered and open.
- /private/tmp/destiny-w212-pass1-native/screenshots/bygones-reload.png, plus
  raw frames/w212-bygones-reload-sample-03.png, -05.png, -08.png and -10.png
  under that same evidence root. Sample03 presents the rear magazine and left
  handling palm. At sample05 the stock/rear handling region stays in frame,
  with left handling geometry partly occluded. Sample08 shows the detached
  rear magazine beside the visible left palm during release/return; sample10
  returns to lowered ready/hip orientation. Do not label sample10 ammo-complete
  from its HUD: the timeline separately establishes the later ammo return.
- Re-viewed the actual source61 upper-chain sheet and checked all61 source
  samples. Shoulder/elbow/wrist posture changes strongly through the exchange;
  source weapon Z translation rises from1.44745 at rest to1.71647 at p=.4,
  then returns near rest. Bone-only source has no camera or original mesh.

The native muzzle extends above the top edge during the source-driven raised
phase, while receiver/stock/rear handling remains visible. This is documented
framing behavior, not grounds to add a camera offset, reduce source motion,
stretch arms or alter preserved authored holds. Selected stills establish visible
handling and recovery but cannot certify every intervening palm contact or
finger fit. The partially occluded sample05 does not justify a speculative
contact correction. Keep existing moving partition, action80A8A36A,
sourceFullChain and family framing for SECOND Vision.

Read and parsed
/private/tmp/destiny-w212-pass1-native/oracles/w212-bygones-reload-timeline.json:
18 presentation rows; active ticks2348..2384 select W212 Bygones with progress
0,.15,.3,.45,.6,.76666665,.9166667. These are consistent with float32 grid60
sampling, not proof that every60th pose was rendered. reloadDuration stays39.
At tick2391 canonical weapon/bygones returns with progress-1,
reloading=false and ammo38/0; later rows retain that neutral state.

Master reports all12 actual native sequences passed, ammo returned, all neutral,
and13 JUnit tests passed. The worker independently inspected only the Bygones
images/source/timeline named here; no suite, game input or listening was run.
No60fps certification, continuous-contact guarantee, recovered source camera
or weapon-exclusive source action is claimed.

## Required SECOND Vision

Master integrates these evidence-only updates and performs SECOND Vision of the
unchanged product. Recheck clear hip/ADS aperture, source-raised rear handling,
left-hand release/reseat and recovery; preserve exact non-FP/inspect routing.
Final native acceptance remains pending that review. Worker remains available
for exact screenshot/progress-based corrections within the same three files.
