# W218 Bad Omens worker review

FIRST image feedback correction returned; SECOND visual acceptance pending. Only three owned files are delivered: this review,
`profile.json`, and `scripts/generate_reload_w218_bad_omens.py`. No shared inputs,
generated assets, registry/runtime, gameplay or audio files are modified.

## Original source and visual evidence

Master evaluated the unchanged original source.blend in separate Blender5.4.0 Alpha.
Worker read `/private/tmp/destiny-w218-source/source-review.json`, fresh rig bytes
`rocket_launcher_ba250bec.json`, and viewed actual upper-chain sheet
`sheets/rocket_launcher_ba250bec-80A8A1F5-upper-chain.png`. Authoritative shared
rocket-family group `rocket_launcher_ba250bec`, OBSlot action
`Armature|fp_80A8A1F5_reload_full|Base`, source frames1..133 at30fps,61 evaluated
samples; previous-cache joint error0 and `allInputsUnchanged=true`.
Measured original61-sample32-unit source lengths: upper8.72669/8.72657,
forearms8.14136, with only floating-point variation across poses.
Only ARMATURE exists. This is not an independent worker Blender evaluation or
weapon-exclusive mesh/camera/finger-IK recovery. Master installs exact fresh bytes
at `art/weapons/w218/rigs/rocket_launcher_ba250bec.json` and report under
`docs/qa/2026-10-28/w218/source/source-review.json`; old W205 rig is not used.

Worker viewed retained W177 comparison.png and storyboard.png, including actual
Mudcat fLyWxsBImP8 frames28.8..31.4s. Bad Omens teal tube, silver rings, wood grips
and raised top sight remain recognizable; two lifts bracket rear-mouth loading.
Hand-occluded rocket internals, dimensions, centerline and exact display angles
remain authored. W177 source is read as inert AST only; no import/execution of its
PIL/numpy/runpy/render dependencies. W217/W215/W216 supplied pure-stdlib/PCHIP
patterns only, never this weapon's motion.

## Product

- Exact11 W177 body/shift/payload keys, both anchors, all holds/extrema and rigid
  display math retained. PCHIP uses weighted harmonic shared knot derivatives,
  with zero endpoint, equal-hold and extremum tangents.61 poses/60 intervals;
  no native continuous60fps claim.
- 117 canonical body solids and12 existing connected reload-only rocket solids,
  face UVs and textures preserved. Original bore, wood grips, collars and aft tube
  remain on body; no removable cap or body split invented. Current inputs are
  pinned from working main, independent of stale W177 PINS.
- Visibility evaluates normalized progress: zero through.20, linear reveal to.25,
  full through.66, linear hide to.72, then zero. Scale remains about MAG_ANCHOR.
  Exact float32(i/60) thresholds match master grid60.
- Original native/twohand carrier compensation, canonical endpoint displays,
  canonical graph at0/1/inactive/nonFP, ADS/inspect precedence retained. Existing
  gameplay duration/ammo/perk speed/audio remain unchanged; no source frame-time
  conversion into gameplay time.
- Current shared loader falls back to default for absent rocket_launcher family:
  translation[0,0,0],rotation[0,0,0],scale1,rightWristRoll15. Preserve these values;
  add sourceFullChain=true,keepMeshSupport=true,hideSupportAtRest=false. Original
  ordinary shoulder/elbow/wrist arms, no limb scaling/axis attenuation/camera fit.
- Right/left mesh rest and reload contact position/rotation unchanged. Explicit
  rigAction80A8A1F5,partHint=magazine,policy=magazine; gripWindow[.20,.25,.58,.64]
  engages during reveal/approach and releases by authored neutral seat.64.
  Payload is body-fixed from.64; later source wrist recovery cannot drag it.

## Targeted checks

Read-through in-memory overlay of fresh W218 rig/report and owned generator/profile
against main ROOT; no asset materialization or shared-data copy. Scratch harness:
`/private/tmp/w218-bad_omens-prepare/check.py`; results beside it in `checks.json`.

Passed: actual new-module import and generate with filesystem write auditing;
repeat byte determinism; exact output namespace/absolute Path:bytes mapping;
248 returned files =247 pack JSON +1 manifest,244 pose children,2 static parts;
61 thresholds exact float32 grid; all authored knots/equal holds/extrema and no
channel overshoot; C1 numerical derivatives; full normalized visibility;
independent rigid-contact reconstruction in both FP contexts and both grips;
canonical endpoints, payload zero-scales and unchanged nonFP display; graph
routing for ADS/inspect/native/twohand/nonFP/inactive and exact float32 boundaries.
Maximum adjacent matrix rotation17.330703 degrees, no flips. Maximum numerical
left/right derivative difference0.000256 at epsilon1e-8. No write audit events.

Budget estimates reserve448 ordinary-arm elements: reload129+448=577;
raw canonical253+448=701. Alternative representations are not summed. These
are candidate estimates; master measures actual simultaneous assemblies across
all routes, including canonical/ADS/inspect, below1000. No all-route pass claimed.

## Native sequence still required

Master supplied FIRST actual PNG/input evidence; same worker viewed and corrected
right-hand binding below. Master owns shared builder integration and SECOND Vision. No live client, Vision/CU input, whole Gradle or native audio
verification was run by this worker. Remaining risks: actual source-arm/mesh
contact fit, hidden rocket approach/seat, bore occlusion, ADS clearance, native
smoothness and return in both grip modes, live lifecycle restoration and measured
all-route arm budgets. The same-worker FIRST review below records exact images and the justified
three-file correction. Further native acceptance requires actual SECOND images.
Do not mark the batch complete before master SECOND.


## FIRST actual images and justified correction

Viewed actual read-only native evidence under main
`docs/qa/2026-10-28/w218/`: `vision1/screenshots/bad_omens-reload.png`,
`vision1/screenshots/bad_omens-review.png`, `first-post-reload-review.png`, and
all ten supplied raw `vision1/frames/w218-bad_omens-reload-sample-` PNGs:
01,05,09,10,12,13,14,15,16,18. The profile records each viewed PNG SHA256.

Raw01 shows initial movement.05 and especially09 show the visibly empty right
hand separated from the launcher; no round/canister can be identified with that
handling hand.10/12 bring the right hand alongside the steep tube without an
identifiable payload.13 separates it again;14/15/16 are lowering/recovery and
cannot validate earlier grasp/reseat.18 and the post-reload panel show restored
hip pose and HUD1/6. The review sheet's centered ADS optic is visible, but this
and successful ammo return do not establish a successful loading gesture.

Master's fresh source diagnosis for original action80A8A1F5 identifies RIGHT as
handling hand, LEFT as stabilizer: weapon-relative delta32 atp.4 is
left[1.046,.895,3.717],right[-4.725,6.838,-13.176]. The shared builder had always
blended/followed LEFT, including moving-part attachment. This is a real binding
error; FIRST visuals are not accepted. The earlier ambiguous source-sheet
support-wrist wording in profile evidence is corrected accordingly.

Exact owned delta:
- Profile adds `contacts.reload.hand=right`, retains explicit action80A8A1F5,
  magazine hint/policy, and gripWindow[.20,.25,.58,.64]. It records FIRST image
  evidence, reported runtime/budget pass, defect and explicit SECOND criteria.
- Generator explicitly requires hand=right in its complete reload-profile dict,
  and records reloadHand=right/stabilizingHand=left plus FIRST correction metadata
  in the returned manifest. No authored pose/scale/geometry/UV data changes.
- This review records actual frame findings, rationale, checks and pending gate.

Mesh reload contact[7.1,12.2,17],rotation[90,0,0] remains unchanged: no new original
geometry evidence justifies moving that authored side-of-rocket target. Window
remains bounded to the authored visibility and seat: attach through reveal.20..25,
fully attached.25..58, release.58..64, exactly zero at neutral seat.64. Rocket is
full-scale.25..66, hides.66..72 and is zero afterward. The wrong-hand FIRST pass
cannot establish a different grasp/release interval. Retiming source or expanding
attachment into recovery would hide the binding error and risk dragging the
already seated round; source action and all original timings remain unchanged.

Targeted correction checks passed with the owned files over main read-through
inputs, fresh W218 rig/report overlay and filesystem writes denied during actual
new-module import/generate. The247 pack JSON blobs are byte-identical to the
pre-feedback candidate; only returned manifest metadata changes. Profile changes
are consumed by master's corrected shared builder, which was not edited here.
Checks additionally reject left/missing/invalid hand, retain exact contact/window,
validate full visibility during attachment/reseat, and zero attachment by.64.
The61 poses, C1/holds/thresholds, endpoints/ADS/inspect/grips, rigid math, output
namespace, determinism and no-write checks still pass. Harness/result:
`/private/tmp/w218-bad_omens-prepare/check-first-feedback.py` and
`checks-first-feedback.json`. No generated assets or shared files were written.

Master reports FIRST15/15 native/runtime sequences, neutral inputs/stopped wrappers
and five-weapon maximum budgets701/693/667/665/701 (Bad Omens701). Worker read
`vision1/native-validation.json`: Bad Omens fire/reload/ADS released, paid1 round,
finished1/6, neutralAfter=true. These pass reports do not accept the corrected
appearance or certify continuous60fps/audio listening. Shared hand-selection
implementation, export and out-of-scope scans remain master-owned.

SECOND must show an actual recognizable rocket/canister with the RIGHT handling
hand through approach/handling/reseat, not an empty palm; LEFT should stabilize
the launcher. Check full-chain clearances, original visibility through seating,
release by.64 without dragging the seated payload, recovery and ADS. If wrong-hand
routing alone still leaves the canister hidden, inspect the actual corrected PNGs
and contact/visibility mapping before any bounded further correction. No SECOND
visual acceptance is claimed. Keep this exact worktree alive for that review.
