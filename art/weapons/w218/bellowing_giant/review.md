# W218 Bellowing Giant candidate review

Status: FIRST actual images reviewed; real RIGHT-hand binding correction implemented and checked. Ready for master integration and SECOND. Corrected visual acceptance is not claimed; keep this worktree alive until SECOND.

## Owned delta and integration contract

Only `scripts/generate_reload_w218_bellowing_giant.py`, `art/weapons/w218/bellowing_giant/profile.json`, and this review are worker-owned. No changes to main/shared inputs, generated assets, runtime, bindings, tests, dependencies, commits or stash/reset/clean. Scratch work and test harness are under `/private/tmp/w218-bellowing_giant-prepare`. Python runs with `-B`; no pycache. Before installation, resolved `.git/worktree-batch.json` was verified `ready`; exact ownership and absent baseline paths checked, and all current pinned inputs matched the worker seed. Baseline SHA256 `bc362206b9f315b4ea546bf9942a06a84f830758abaff32d7fe8b1f02b1fea1d`; HEAD `bfd4b4573fd8651bf1ea850bf829622ccce5c3c2`. Only the three owned files were installed after readiness.

The stdlib generator imports inertly and `generate(root=ROOT)` reads only, returning exactly 248 absolute `Path: bytes` entries: 2 static parts, 244 display children (61 × 2 parts × 2 grips), 1 item graph, and 1 manifest. Only `models/weapon_reload_w218_bellowing_giant/bellowing_giant*.json`, the corresponding item JSON, and W218 manifest are returned. It has no writing CLI, renderer or legacy imports. Master materializes the bytes and owns every shared loader/runtime/binding route.

Master installs byte-exact fresh inputs at:

- `art/weapons/w218/rigs/rocket_launcher_ba250bec.json`: SHA256 `78d7101c57cc3a3a3d88e0dc957cbdb4982160e21ec7e11a9630e3bee5958e3d`.
- `docs/qa/2026-10-28/w218/source/source-review.json`: SHA256 `f5a06a8373aa9ee1328f0d2b14c87dc187367edc7e28224f7bfa6287d64469d0`.

The generator never expects W205 rig replacement. Current source geometry/UV/paint/display/timing/audio and W187 authored inputs were independently hashed from current main bytes; all historical W187 PINS happened to match this snapshot. Generator pins current inputs and reads old generator assignments inertly via AST.

## Original source and retained weapon evidence

Read main AGENTS.md, RTK.md, weapon-art skill and `references/ace-izanagi-study.md`. Preserve recognizable long red/silver jacket, graphite shoulder sleeve, front bore and open sight, existing UV and meaningful moving part. This is a dense animation upgrade, with no silhouette/UV redesign or count padding.

Master evaluated the original read-only `source.blend` in a separate Blender 5.4.0 Alpha background process. Worker read the fresh report and matrices and viewed the actual chain sheet; worker did not independently run Blender. ARMATURE only, action `Armature|fp_80A8A1F5_reload_full|Base`, `OBSlot`, source-map `reload_full` (also reload_special/reload_empty), original frames 1..133 at 30fps, 61 samples. Previous cache joint error is exactly 0; report confirms all original inputs unchanged. Group `rocket_launcher_ba250bec` is shared-family and includes Bellowing Giant; report representative weapon is Bad Omens. It does not establish exclusive Bellowing weapon mesh/camera/finger IK.

Original `.blend`: `/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return/clips/rocket_launcher_ba250bec/blender/source.blend`, SHA256 `814231f6f74533c758ea4527263b5b7df6e633e06d6755da60ae3b2616c53124`. Source-map SHA256 `996e8d38b351230180852056488d6a9ed57819e1df192c1cc38ae67e3081effb`; bone-map SHA256 `bef1f40549f3d698efc439d17bf5c5f07ea443c55811c29705d5f9ec4b7c5259`.

Viewed `/private/tmp/destiny-w218-source/sheets/rocket_launcher_ba250bec-80A8A1F5-upper-chain.png` (actual XZ/YZ shoulder/elbow/wrist projections at p=0,.2,.4,.6,.8,1), retained W187 `storyboard.png`, and `comparison.png`; read W187 `SOURCE.md`/manifest/source text and AST. Storyboard actual same-weapon2018 gameplay supports front muzzle presentation, whole incoming rocket from right, axial push, palm release and forward/down roll. Combat effects and hand hide exact rocket profile. Authored offline model panels have independent framing/no hands and are not Minecraft evidence. Legacy generator/render dependencies were never executed/imported.

## Product behavior

All14 W187 knots, extrema/equal-value holds, GRIP[8,8.65,7.8], payload anchor[8,12.05,.4], native/twohand rigid carrier math, left-hand conventions and canonical displays are unchanged. Replace segment smoothstops with shared-derivative C1 weighted harmonic PCHIP; endpoint, hold and extremum slopes remain zero. This avoids artificial stops at through-knots. Exactly 61 poses/60 intervals, with thresholds rounded to float32(i/60); this is not a claim of native continuous60fps interpolation.

All114 canonical elements and684 face records stay on the fixed body, including breech, lock band, sleeve, stock, foregrip, pistol, action housing and sight. The only moving assembly is the identical16-element reload-only whole rocket (core, octagonal jacket, stepped nose, tail and four shallow stabilizers). Reuse exact graphite stock UV; never move stock geometry as ammunition. Payload dimensions/hidden nose/UV/contact path remain authored approximations, not source mesh recovery.

Preserve actual old dispatch visibility: old poses7..13 occupy normalized `[.35,.70)`, now poses21..41. This preserves its seated visibility hold at .65..70 instead of misusing old indices on a61-pose grid or shrinking the rocket. The authored offset reaches exact neutral at .65 and holds through1.

The shared loader currently merges default framing for rocket_launcher: translation[0,0,0], rotation[0,0,0], scale1, rightWristRoll15, no leftRotation. All effective framing values are retained. Profile adds sourceFullChain=true, keepMeshSupport=true, hideSupportAtRest=false for ordinary fingerless player-skin arms with both original shoulder/elbow/wrist chains. No new camera offset, length scaling or axis attenuation.

Keep original mesh rest contacts and rotations (right pistol[8,8.35,7.83], left foregrip[8,8.95,2.17]) and original reload target[7,12.05,.4]/rotation[90,0,0]. Explicit reload action80A8A1F5, partHint magazine, policy magazine with explicit hand RIGHT enables the incoming whole rocket to follow the original handling wrist only during handling. Corrected gripWindow[.30,.35,.60,.65]: approach before appearance, fully attached at first visible pose .35, fade during final seat, exactly zero from .65. The seated rocket cannot be dragged by subsequent wrist recovery. No spent extraction, independent bolt/latch or moving breech is invented.

Canonical endpoint graphs and child displays are exact at0/1 for both grips/hands. Negative/inactive/overshoot and non-firstperson retain the canonical graph; original ADS/inspect cases precede reload. Capacity1/reload64ticks/cadence60ticks/burst1/sharedBurstAmmo=false/ammo/audio remain unchanged.

## Targeted checks

`rtk proxy python3 -B /private/tmp/w218-bellowing_giant-prepare/check.py` and the post-install `--worker` run both pass against a read-through in-memory overlay of the fresh rig/report and owned generator/profile over main ROOT. No shared data or generated assets are copied to the worker. Result is in scratch `checks.json`; test harness is outside owned product delta.

- Import and both generate calls run under a Python audit hook that rejects filesystem writes/mkdir/rename/remove/link/chmod and subprocess execution: no attempts. Legacy execution/import absent. Two generated mappings are byte-identical; all248 outputs parse and match the exact absolute allowlist; manifest input/output digests verified.
- 61 strictly increasing thresholds equal exact float32(i/60); 244 display children, both parts/grips/hands, 2 static models, 247 pack files, 248 returned files.
- Fixed body equals the entire source model; rocket equals W187 reload-only elements/UV. Partition114+16, no additional geometry/triangle adapters. All14 knots exact; 101 points per segment check scalar monotonicity, extrema and exact equal holds. Finite-difference C1 checks pass at every interior knot. Invalid/nonfinite progress rejected; neutral rocket offset holds from .65 through1.
- Independent graph selection checks native/twohand, both firstperson hands, GUI/ground/thirdperson, ADS/inspect, negative/0/1/overshoot. All canonical guards/fallbacks and endpoint graphs/displays preserved. Visibility is exactly dense21..41.
- Independent Rx*Ry*Rz point transforms verify body/rocket, every pose/grip/hand, pivot and extremal payload points. Maximum error5.834666083615048e-10. NonFP display dictionaries and uniform scale remain exact. Largest consecutive rigid rotation12.23722974083266 degrees; no matrix flip or singularity jump. Euler scalar representations are not physical flip evidence.
- Fresh full source chains have finite matrices and unchanged ordinary32-unit limb lengths. Left upper8.72668545..8.72669209; left fore8.14136145..8.14136634; right upper8.72656688..8.72657467; right fore8.14135734..8.14136587.
- Candidate simultaneous reload130+448 reserved arm elements=578. Raw canonical217+448=665. These are alternative routes, never summed. Both below1000; actual all-route composed count remains master-owned and unverified in candidate manifest, including canonical/ADS/inspect. No whole Gradle or live client run.

## FIRST feedback / same-worker response / SECOND

Viewed the actual native FIRST reload sheet, hip/ADS/reload sheet, post-reload sheet and all10 requested raw PNGs. Master reports15/15 native/runtime sequences and budget counts701/693/667/665/701 passed; wrappers stopped and inputs neutral. This does not accept visual handling. Worker independently read native-validation.json: Bellowing finished1/6, fire/reload/ADS released and neutralAfter=true. Worker did not operate a client or listen to audio.

Specific viewed raw frames, under main `docs/qa/2026-10-28/w218/vision1/frames/`:

| Raw sample suffix | Actual observation |
|---|---|
| 01 | Ready/early lift with launcher and both arms. No incoming rocket expected/readable yet. |
| 05 | Raised launcher and approaching right forearm; no distinct held rocket visible. |
| 09 | Empty RIGHT hand clearly separated to the right of the steep launcher; this is the real handling defect. |
| 10 | Right palm returns toward the tube; no independently readable canister. |
| 12 | Right hand crosses against the tube; a distinct rocket is still visually unestablished. |
| 13,14 | Raised launcher/late handling and reseat; no separate right-held round is readable. |
| 15 | Forward/down recovery begins; missing handling payload remains unacceptable. |
| 16 | Arm crosses upper launcher during recovery; SECOND must inspect release and clearance. |
| 18 | Near ready recovery; post-reload sheet confirms recovered hip presentation and HUD1/reserve6. |

Names are `w218-bellowing_giant-reload-sample-NN.png`; these actual raw files and both sheets, plus `../first-post-reload-review.png`, were viewed read-only and their SHA256/observations are recorded in profile.evidence. Sample suffixes are capture identities, not assumed exact normalized timestamps. Hip/ADS sheet shows existing large close tube/open sight; no geometry/framing change is made as part of the hand correction.

The original shared-family action80A8A1F5 uses RIGHT as the handling wrist and LEFT to stabilize the weapon. Master found the shared builder previously blended/followed LEFT unconditionally. User-supplied source delta32 at p.4 is left[1.046,.895,3.717] versus right[-4.725,6.838,-13.176]. Worker also calculated source weapon-relative right wrist travel from its p0 pose: p.35[-2.6664,12.7812,-18.4250], p.40[-4.7252,6.8382,-13.1767], p.433333[-6.8920,3.9849,-5.4476]. The large incoming reach is already present by .35 and substantially returning at .43. The previous attachment ramp .35..43 therefore missed early grasp. Bounded correction moves only the approach to .30..35, fully attached when the original payload first appears; full carry through .60 and release .60..65 remain. Original source matrices/timing and all authored model knots are untouched.

Exact product correction: profile.contacts.reload.hand=`right`, gripWindow `[.30,.35,.60,.65]`; explicit action80A8A1F5/partHint magazine/policy magazine unchanged. Generator strictly expects right hand/new window and records manifest.reloadHand=`right`. Reject missing/left/invalid weapon profile hand. No mesh contact change is justified: existing reload point[7,12.05,.4] is one unit beside the rigid payload anchor[8,12.05,.4], beside the unchanged .46-unit minimum lateral surface gap; moving it without SECOND would be speculative. Existing right/left rest contacts, reload rotation, framing, payload visibility `[.35,.70)`/dense21..41, rocket anchor and geometry/UV remain exact. Source hand/canister dimensions are approximate; a glove may still obscure a narrow payload, so actual SECOND silhouettes/contact must be checked.

Master owns the shared generic reload.hand selector/validation/default-left preservation and selected-hand moving-payload attachment. Worker has not edited the shared builder, bindings, installed rig/report, generated assets, runtime or gameplay/audio. All247 models and item graphs are byte-identical to the FIRST worker candidate; only the returned manifest metadata changes, while the profile changes which arm the master attaches to the existing moving payload.

Post-correction tests:

- `rtk proxy python3 -B /private/tmp/w218-bellowing_giant-prepare/check.py --worker`: PASS. Exact-worker no-write import/generate,248 deterministic output bytes, float32 thresholds, all knots/holds/C1, UV/geometry/rigid math, endpoints/native/twohand/ADS/inspect/fallbacks and budgets remain valid.
- `rtk proxy python3 -B /private/tmp/w218-bellowing_giant-prepare/first_feedback_checks.py`: PASS. First/corrected W218 modules evaluated under no-write audit and read-through overlay (neither imports legacy187). All247 models/item graphs byte-identical; only manifest changed. Manifest right/window recorded. Missing/left/RIGHT/invalid profile hand rejected. Weight is1 for dense21..36 and0 from39 onward; payload remains visible21..41, with exact neutral offset from39. No disk-generated assets.
- Python AST/compile and profile JSON syntax pass with `-B`, no pycache. Review changes are documentation of actual FIRST evidence and correction. No whole Gradle, live client or shared out-of-scope scan was run by worker.

SECOND acceptance is a visible actual round/canister carried by RIGHT during .35..60, progressive reseat/release .60..65 and original seated hold .65..70, followed by unforced source wrist recovery. LEFT must continue stabilizing. Check ready/ADS clearance and final return after the generic shared binding fix. Native runtime or element-budget success alone cannot close this defect. Worker remains available; keep worktree alive until SECOND. No corrected-native visibility, audio or final acceptance claimed.

Post-install readiness: ready marker/baseline hash and exact three-file ownership verified. Worker bytes equal prepared scratch; generator Python AST/compile and profile JSON syntax pass. Exact worker generator/profile passed the no-write read-through overlay checks again. Current corrected generator SHA256 `6577cacf34845dae5b9248a78a29c5726e8ff4f8e7cafcaa00f6fd31754e43a6`; profile SHA256 `7f9456b420533c2812a1df9ae66667fe9ba93153841a6c12c0a9ce18ccd9bdee`. FIRST images reviewed and correction returned; available for master SECOND. No shared/output assets or standalone Gradle run.

Master follow-up: generic selectable reload helper and four regressions are ready, with profile.reload.hand=right selecting the source RIGHT palm for payload. Source and all requested FIRST PNG reviews are complete. This same-worker correction is returned for master integration/SECOND; keep worker alive. No shared files were edited.
