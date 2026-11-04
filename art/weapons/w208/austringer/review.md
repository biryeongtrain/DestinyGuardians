# W209 r5 rejection — preserve the free source wrist trajectory

## Decision

**r5 reload is rejected. No profile changes are justified.** Changed only this
review. Main's profile is newer (`sourceFullChain: true` and the cylinder
`gripWindow`); do not overwrite it with this worktree's older profile.
Master owns the shared common-translation correction and the next Vision.

Viewed the actual r5 images with `view_image`, before this recommendation:

- `/private/tmp/destiny-w209-r5-native/screenshots/austringer-review.png`
- `/private/tmp/destiny-w209-r5-native/screenshots/austringer-reload.png`
- `/private/tmp/destiny-w209-r5-native/frames/w209-austringer-reload-sample-04.png`
- `/private/tmp/destiny-w209-r5-native/frames/w209-austringer-reload-sample-07.png`

Hip retains two hands and the ADS sight is clear; master reports hip/ADS good.
In sample 04, the handling forearm/upper sleeve points upward above a relatively
level gun; sample 07 shows it extending diagonally through the sky above the
raised gun. The connected chain still crosses/occludes the mechanism. This is
not solved by tweaking the static cylinder palm rotation or shortening the arm.
Capture indices are not exact synchronized source progress coordinates.

## Precise source-backed diagnosis

Read current main `rig_arms_w205.py`, `build_first_person_hands_w201.py`,
`first_person_framing_w205.py`, current main profile and evaluated61 Austringer
rig. At this read, shared rig source SHA-256 was
`a84f889afbfd855f48e5bbc8a1c0640902240301c0741b85c4c3e1ca1de93cb2`;
main profile SHA-256 was
`5653b238d105755f997b7e656a41d81f834d1cc9944e21f1c180d721a009a736`.
These identify the inspected implementation, not a frozen requirement for master.

Current full-chain direction is `Rbody * C * inverse(RWt) * Ft`; the upper
orientation follows the same source bend. However, its LEFT wrist translation
is still the authored support/cylinder blend. Thus the original low, free hand
is forcibly moved onto a high cylinder. Moving the whole chain to that wrist
preserves its bend and ordinary lengths, but moves its shoulder and sleeve high
into view. A correct source orientation is insufficient when wrist translation
contradicts the source action.

The original evaluated wrist/elbow/shoulder chain is the relevant evidence:
`8C83CB67` / `897A1504` / `D1232BA2`, weapon bone `4A0810C4`. Shoulder hierarchy
was already audited from the original Blender file; no new bone-label error is
demonstrated here. The latest master finding agrees with independent trajectory
inspection. At p=.30, source wrist is about `[-.062,.247,1.147]` and weapon
origin `[.414,-.089,1.571]`: the hand is clearly away/below, not on the cylinder.

Read-only values from the current actual evaluated61 action are below. Height
is source `(leftWrist.z - weapon.z) * 32`; distance is distance to the weapon
**bone origin**, not to a recovered cylinder surface. Both are model-unit
comparisons before presentation scale. Times are the source's 4.2-second clip,
not a new gameplay duration.

| Progress | Source seconds | Wrist height relative to weapon | Distance to weapon origin | Interpretation supported by the joints |
| --- | --- | --- | --- | --- |
| .00 | .00 | +.472 | 2.990 | Ready neighborhood. |
| .05 | .21 | -12.772 | 22.425 | Hand already far below/away. |
| .20 | .84 | -12.732 | 22.552 | Free lowered handling, not cylinder attachment. |
| .30 | 1.26 | -13.565 | 23.049 | Same contradiction as master's example. |
| .40 | 1.68 | -15.271 | 23.655 | Hand remains away. |
| .4333 | 1.82 | -16.561 | 23.575 | Deepest lowered interval in this sample table. |
| .4667 | 1.96 | -15.318 | 22.583 | Still below; return has not reached the gun. |
| .50 | 2.10 | +1.384 | 9.633 | Fast return/approach, not proof of surface contact. |
| .5667 | 2.38 | +.971 | 6.085 | Handling near weapon neighborhood. |
| .60 | 2.52 | -.454 | 4.775 | Near-weapon gesture. |
| .6333 | 2.66 | -.910 | 4.828 | Near-weapon gesture continues. |
| .6667 | 2.80 | +.683 | 6.309 | Beginning departure neighborhood. |
| .70 | 2.94 | -8.268 | 14.624 | Hand withdraws/down again. |
| .7333 | 3.08 | -8.465 | 19.954 | Free withdrawal. |
| .80 | 3.36 | -2.621 | 5.087 | Returning toward support. |
| .90 | 3.78 | +.472 | 2.990 | Back at ready neighborhood. |

The existing authored window reaches full cylinder attachment at .20 and holds
through .60, precisely across the original free lowered .05..47 interval.
Release-by-.76 remains a valid authored cylinder-closure safeguard, but **this
window is not an original hand-contact track**. It cannot justify pinning the
sourceFullChain wrist, even though it fixed the earlier closing-flick trap.

## Recommendation within the current scope

Master's planned common source translation is the necessary correction. Replay
the actual source wrist displacement under the same calibrated parent used by
the body and limb directions, with a fixed neutral mesh-rest calibration:

```
p_i(t) = p_meshRest_i + k * M * (w_source_i(t) - w_sourceRest_i)
```

Here M is the agreed source-parent-to-view rotation, k is the single ordinary
source-to-view distance scale, and i selects the hand. The rest sample, M,
source space and grip carrier must match the body/arm calibration. A fixed
source-to-mesh similarity may express the equivalent calibration; do not
recompute a new hand offset to hit the cylinder every frame. Apply the same
chain translation to that side's elbow and shoulder. Preserve actual source
wrist motion and source ordinary segment lengths, with no arbitrary forearm
long-axis bias. Verify the right firing contact under the selected similarity
as well; do not assume matching neutral points proves rotating grip contact.

For the sourceFullChain pair, do not reapply the legacy per-frame gripWindow
translation after source displacement. Keep its legacy behavior in other paths
unless separately audited. Do not force the hinged cylinder to follow the free
wrist; retain its authored body-relative hinge transform and the shared source-
driven body. In this source clip the hand's lowered gesture is consistent with
handling rounds/loader away from the gun, then approaching around .50..67.
The exported joints alone do **not** prove which object is held, exact fingertip
contact, or speedloader geometry. The action maps both `reload_full` and
`reload_empty`; no ammo-object inference should replace actual object evidence.

The near-weapon interval **.50..67 is a next-Vision inspection interval**, not
a proposed hard binding window or a profile change. Inspect source/mesh contact
there after free-wrist transport works; if contact fitting is later necessary,
use original mesh/prop evidence and local residuals at the real handling event,
not attachment during the lowered phase. Do not suppress the .05..47 and
.70..77 free excursions to make the contact look convenient.

The earlier r4 recommendation to translate a source-shaped chain onto each
current authored palm target was algebraically length/bend preserving, but it
failed to preserve this free wrist motion. That recommendation is superseded.
Algebra checks in the historical sections below are not visual acceptance.

## Handoff and limits

No worker Blender session or source re-export was performed; existing master
source-first61/shoulder provenance supplied original evaluated data. This pass
inspected native evidence and performed read-only trajectory arithmetic. No
profile/main/shared/runtime edit, generator, build, Gradle, CU/Vision input,
length change or hiding was performed.

Only changed path:
`/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w208-austringer/art/weapons/w208/austringer/review.md`.
Master must integrate the shared translation correction and repeat Vision of
lowered free hand, near-weapon .50..67, withdrawal, two-hand recovery and ADS.
Reload remains rejected until that review succeeds.

---

# Historical r4 second-Vision review — superseded by r5 wrist-trajectory finding

## Result and owned delta

**r4 is rejected. No profile changes.** Only this review is updated. Main's
newer profile and `gripWindow [.05,.20,.60,.76]` remain authoritative; do not
copy the older worktree profile over them. Master owns the coherent-source-chain
implementation and next Vision. Earlier algebra approval below established a
rotation identity, not correct source bend in the accepted camera/mesh carrier.

Inspected with `view_image` before reviewing the proposed equations:

- `/private/tmp/destiny-w209-r4-native/screenshots/austringer-review.png`
- `/private/tmp/destiny-w209-r4-native/screenshots/austringer-reload.png`

Hip/recovery still show the close two-hand cup; ADS sight is clear but separate
hand visibility remains unproven below the crop. In raised reload samples 04/09,
upper sleeves now project far upward across/above the weapon. Adding upper
segments connected the cut ends but did not correct the source-chain carrier.
Sample 14 still exposes the sleeve prominently. Cylinder palm clearance cannot
be accepted from the occluded raised poses. Do not fix this with profile angles,
extra lowering, hiding, stretching, or source-motion suppression.

Read current main shared source and shoulder provenance read-only. At inspection,
`rig_arms_w205.py` SHA-256 was
`1f474c67cb7e0abf5c670b4808294fabc23e8d5f4d02f828938663bf40cd415c`.
That version applies common-parent source delta over an authored contact frame,
then derives upper orientation as `Rforearm * (Ft^T * Ut)`. The multiplication
preserves a relative bend, but **also transports the entire bend through the
authored forearm bias**. Genuine shoulder samples do not make that arbitrary
bias a source/camera calibration. The gun also still follows its authored body
motion independently. Those facts explain why connection alone was insufficient.

## Proposed coherent-chain equations — supported, subject to calibration

Use column vectors. Wt is the evaluated source weapon transform, Ft is the
forearm basis (elbow-to-wrist +Y, elbow +Y transverse), Ut is the corresponding
upper-arm basis (shoulder-to-elbow +Y). C maps the agreed source weapon-local
axes to canonical mesh axes. B0 is the accepted neutral mesh-to-view carrier;
A is the **fixed full similarity** mapping source weapon-local coordinates to
canonical mesh coordinates, including the source-to-model scale and weapon-origin
anchor as well as C. W0 is the same evaluated neutral source sample for every
part of this calibration.

```
Bsource(t) = B0 * A * inverse(W0) * Wt * inverse(A)
Rforearm  = Rbody * C * inverse(RWt) * Ft
Rupper    = Rbody * C * inverse(RWt) * Ut
```

Since `Rbody = RB0 * C * inverse(RW0) * RWt * inverse(C)`, the two arm equations
reduce to the SAME fixed source-to-view calibration:

```
Rforearm = RB0 * C * inverse(RW0) * Ft
Rupper   = RB0 * C * inverse(RW0) * Ut
```

This cancellation is the useful coherence check. The source weapon motion now
moves the body, while the arms retain actual source directions in that same
parent frame. Do not add a per-hand rest-long-axis rotation, wrist roll, or
`sourceViewRotation` to these full-chain directions: that would rotate the
source bend again. Preserve authored mesh palm **positions**, not an arbitrary
ready forearm orientation. Skin twist, if needed, must not change the actual
longitudinal direction or the source upper/forearm bend.

### Preserve moving-part motion relative to the body

For each existing authored reload sample, extract its full relative affine:

```
Lpart(t) = inverse(Bauthored(t)) * Mauthored(t)
Mnew(t)  = Bsource(t) * Lpart(t)
```

Use the body-relative cylinder transform, including its hinge translation;
do not multiply the old authored body rotation/shift into the source body a
second time. Body and moving part must use the SAME scale, presentation and
grip carrier. The existing cylinder gripWindow still chooses the mesh palm
position and releases it by .76. Preserve its authored relative motion and
contact timing without interpreting the support palm as a permanently attached
cylinder child.

### Same source parent frame for positions and upper connection

For each side, let `T = Rbody * C * inverse(RWt)`, p be its selected mesh palm
position after body/moving-part/gripWindow transforms, and k the single agreed
source-to-view distance scale. Build both segment endpoints from source origins:

```
elbow   = p     + k * T * (sourceElbow - sourceWrist)
shoulder= elbow + k * T * (sourceShoulder - sourceElbow)
```

This preserves source lengths and bend without an independently rotated upper
segment. In current skin geometry the forearm wrist pivot is local Y8 and its
elbow Y1.5; the upper elbow is Y8 and shoulder Y.5. Use those endpoint offsets
and ordinary length factors (forearm /6.5, upper /7.5) exactly once.
The palm cap beyond the wrist pivot is not a recovered finger contact surface.

Anchoring an authored palm can require a per-chain **translation** relative to
the source wrist. Apply that same translation to wrist/elbow/shoulder together.
Two independently authored palm positions generally cannot simultaneously retain
a single fixed source shoulder placement. This method preserves source chain
shape; it is not a torso/shoulder IK solve. Do not claim otherwise.

## Source/carrier calibration checks before next Vision

- Use the same evaluated W0 for body, Ft and Ut; source pose data are armature-
  object coordinates, not matrix_world coordinates or scene-unit meters. Do not
  apply the exported armature world scale/rotation again.
- Validate C against source weapon-local axes and the cleaned mesh's muzzle -Z /
  +Y up. A needs the actual weapon-origin-to-mesh anchor, not an invented overall
  bounds center, palm center, or barrel tip. Rest must give Bsource=B0.
- Apply the selected native/charged-crossbow carrier exactly once to weapon,
  moving part, palms, and both segments. If Rbody already includes that carrier,
  do not apply `carrier_rotation` again in the arm equation. Its translation
  matters too. Do not apply the canonical conversion C twice.
- Use the coherent equation consistently at idle/ADS, reload entry and recovery
  for the two audited weapons, or explicitly verify the transition to their
  existing ready graph. An active-only source orientation with an unrelated
  ready orientation can snap at exact 0/1 endpoints. The new direct orientation
  is not automatically identity relative to the old authored ready forearm.
- Full-chain eligibility is ONLY the audited `austringer` and `the_recluse`, with
  evaluated shoulders for the selected idle/ADS/reload actions. Do not enable it
  family-wide based merely on a family name or a stray shoulder key. Other
  families keep their existing path.

## Independent read-only verification and provenance

Read `source-upper-arm.json` and `source-upper-integration.json`. Shoulder origins
are source upper-arm joints `D1232BA2` (left; anatomical role inferred from the
bilateral/direct-parent audit) and `17025F50` (right, explicit b_r_upperarm), not
the clavicle parents. The audited export covers only Recluse and Austringer and
records source hashes unchanged. It contains evaluated joint origins; Blender
bone display tails/lengths are not the segment-length oracle. This worker did
not re-open Blender or claim a new source export.

Using current main evaluated61 Austringer matrices, independently checked the
proposed source-body cancellation and endpoint reconstruction across all 61
reload samples x 2 chains. Maximum orientation cancellation error: 5.55e-16;
source segment length error: 4.44e-15; elbow-bend cosine error: 4.86e-16.
These are equation checks on the proposed mapping, **not** a claim that the r4
implementation or its native appearance passed. The coherent body affine still
needs the measured A calibration and native confirmation.

No main/shared/profile edit, generator, build, Gradle, CU/Vision input or Blender
operation was performed. Next Vision must verify the same raised samples, source
bend, cylinder grip/release, clear ADS, two-hand intent and return without a
0/1 snap. The prior r3/W208 sections below are historical and do not override
this r4 rejection or the current coherent-source-chain plan.

---

# Historical r3 first-Vision review — superseded by r4 rejection

## Decision and scope

**No new profile correction.** Keep current main contacts and two-hand intent;
fix the shared rotation transport before tuning art angles. The current main
profile includes `reload.gripWindow: [.05,.20,.60,.76]`; this older worktree
profile does not. **Integrate only this review for this pass; do not copy the
stale worktree profile over main or remove its gripWindow.** The only file
changed in this W209 pass is this `review.md`.

Latest human intent remains TWO hands for idle/ADS and recovery. Do not hide
hands, stretch forearms, suppress source motion, or mask the raised pose with
extra camera lowering. This is the requested worker review after first Vision;
master's shared fix, integration and second Vision remain required for acceptance.

## Current evidence, inspected before proposing changes

Read current main shared source, not this worktree's stale implementation:
`rig_arms_w205.py`, `build_first_person_hands_w201.py`,
`first_person_framing_w205.py`, `skin_arm_models_w204.py`, current main family
settings and Austringer profile. Main family enables `sourceWeaponRelative`,
`meshArmDirections`, `keepMeshSupport`, two hands and source lengths; it also
inherits `rightWristRoll: 27` and `reloadCameraLower: 1.5`.

Viewed actual saved first-Vision images with `view_image`:

- `/private/tmp/destiny-w209-r3-native/screenshots/austringer-review.png`
- `/private/tmp/destiny-w209-r3-native/screenshots/austringer-reload.png`
- Full-size frames `w209-austringer-hip.png`, `reload-sample-09.png`,
  `ads-sample-05.png`, and `after-reload.png` in that capture's `frames/`.
- Main `docs/qa/2026-10-28/w209/source-review/80A8A53D-contact-sheet.png`.
  This is source-bone review imagery, explicitly not a mesh/contact render.

Read main `source-blender-61.json`, source-review `review-index.json`,
`source-blender-recheck.json`, `source-axis-audit.json`,
`source-frame-continuity.json` and the current evaluated rig. Austringer reload
contains **61 directly evaluated Blender poses**, action tag `80A8A53D`, source
frames 1..127 / 4.2 seconds. Current rig SHA-256
`f359d54aac3a1ece4ecaf036de0a0834084d6774b1a925d0a6963b0fa2cc0aaf`
matches provenance. Source blend SHA-256 is
`3edb6615b69e8eb96687964de0dfabf413a309bf22ffcaa4e9524017553a60bf`.
Provenance reports source unchanged and shared-frame maximum error zero.
This worker did not open/evaluate Blender; master supplied that provenance.
The export has no camera. Cached matrices/source bones are not mesh IK fidelity.

## Visual assessment

**Hip and recovery:** the full-size hip and after-reload frames show two adjacent
skin forearms forming the close lower cup at the grip. They overlap heavily,
but support is present rather than deliberately hidden. No new idle position or
rotation is justified by these images alone.

**ADS:** centered rear sight remains clear of arms. Full ADS shows no separately
visible hands: they are below the image/behind the weapon. The false hide flag
and graph coverage do not prove visible two-hand ADS. Keep the requirement open
for second Vision, including hip-to-ADS/low ADS frames and both grip carriers.

**Reload:** hand cannon shares the raised-reload defect reported for Recluse.
Sheet samples 04 and 09 show isolated cuff/elbow ends in open air and forearms
crossing over the gun; full-size sample 09 confirms the pale cuff end above/right
of the raised cylinder area. The cylinder is swung out, but the support palm is
occluded/crossed and its surface contact cannot be accepted. Earlier/later sheet
frames show large arm swings before recovery. These screen sample numbers are
capture indices, not synchronized source progress values.

## Shared diagnosis and concrete correction

### Common weapon-frame swing, not each authored hand's rotated swing axes

The reviewed shared version computed `Drest^T * Dt` and postmultiplied the mesh
ready calibration. That is a local-frame relative rotation; transporting it
through each differently authored hand calibration rotates the swing axes
separately. Correct source sampling and the stable elbow-Y transverse basis do
not fix that coordinate-space choice.

Master's proposed correction is supported independently:

```
Drest = W0^T * F0
Dt    = Wt^T * Ft
Q     = Dt * Drest^T
Qmesh = C * Q * C^T
Rout  = Rbody * Qmesh * RmeshRest
```

Here F uses elbow-to-wrist longitudinal and elbow +Y transverse; W is the
orthonormal weapon basis. Q acts in the common source weapon-parent space;
C conjugates that space into the canonical mesh axes. At ready Q is identity,
so the authored ready calibration remains intact. Premultiplication preserves
the common source swing axes rather than making them depend on each grip roll.
C must continue to represent the agreed weapon-parent-to-canonical convention;
this algebra check alone does not recover camera/FOV or validate source mesh axes.

Independent read-only check across all 61 samples and both forearms (122 frames)
verified `Qmesh * (C * Drest.axis) == C * Dt.axis` for all three basis axes.
Maximum error was 4.44e-16; orthogonality error 1.11e-15; ready identity error
4.44e-16. No shared edit was duplicated. This validates basis transport only,
not native acceptance or absence of exposed elbow ends.

### Cylinder gripWindow works for position; target orientation is discarded

Current main `gripWindow [.05,.20,.60,.76]` reaches at .20, holds through .60,
returns through .76, and has zero cylinder attachment during .76..90 flick.
Read-only envelope values: .20/.40/.60 = 1, .70 = .31640625,
.76/.84 = 0. **Keep this window.** The old W208 complaint about .84 being 78.4%
attached has already been fixed in main and is historical below.

However, current `build_first_person_hands_w201.py` blends the whole left-hand
frame toward the moving cylinder and then `rig_arms_w205.apply` reconstructs
rotation from body + **ready** `config.left.rotation`, replacing the incoming
blended target orientation. A read-only reproduction changed the incoming
cylinder-target rotation from the explicit profile value to `[0,0,0]`; final
left rotations remained identical at .20, .40, .60, .70, .76 and .84. Thus the
profile's cylinder orientation has no effect during dynamic source-relative
reload. Changing that profile angle now would be ineffective.

Master should retain position and orientation as one handling frame through
composition. Account for the selected moving-part frame when deriving the
source residual, so source motion remains present and cylinder rotation is not
applied twice. Do not silently replace the target's rotation with the ready
rotation. The common-parent delta correction above fixes transport axes; by
itself it does not restore the discarded target orientation.

### Floating elbow ends are also a representation/chain issue

The skin model is only the fingerless forearm segment (local Y=1.5..9 around
contact Y=8), scaled to ordinary source forearm length. Raised source-relative
poses can bring its elbow end into the image; there is no connected upper-arm
segment. Rotating a forearm about an authored mesh palm cannot establish a
shoulder/elbow/wrist chain, especially while the support wrist follows an
authored gripWindow instead of source wrist positions.

After fixing common-parent transport and handling-frame composition, inspect
the same raised samples. If elbow ends remain exposed, continue the arm at the
same evaluated/calibrated elbow with an upper-arm segment driven by the actual
source shoulder/upper-arm chain, evaluated from the original rig. Use consistent
calibration for both segments and preserve source lengths/motion. Do not lengthen
the forearm, clamp its swing, hide it or move it offscreen as a substitute.
The six exported roles here contain elbows/wrists/weapon/utility, not a verified
shoulder chain; do not invent shoulder data or claim an IK solve.

## Handoff and verification limits

No runtime, CU/Vision input, Blender, build, Gradle, generator or main mutation
was performed. Read-only checks verified evaluated61 provenance, the target
rotation overwrite, gripWindow weights and proposed common-parent algebra.
Main profile was not changed; worktree profile was not changed in this pass.
Master owns the shared implementation and second Vision: two-hand idle/ADS,
raised poses, clear sight, cylinder palm orientation/clearance, release before
flick and return to the same support cup. Current result is **not accepted**
for reload hands until that second review.

---

The following W208 notes are historical. Their source21 assumption, no-source-
motion mode and generic-envelope diagnosis do not describe current W209 main.

# Historical W208 review — superseded by W209 findings below

## Current intent supersedes the old review

The latest human explicitly requires **TWO visible hands in idle and ADS**.
This supersedes this profile's previous one-hand intent and the historical W168
footage interpretation. `hideSupportAtRest: false`, `keepMeshSupport: true` and
`meshArmDirections: true` are explicit. Recovery returns to the two-hand cup.
Source rig orientation alone is not mesh IK. These are authored contact frames,
not recovered camera, source hand/finger IK, or source pose fidelity.

This revision edits only `profile.json` and this review in the existing isolated
`/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w208-austringer` worktree.
Read worktree/main AGENTS.md, RTK.md, the minecraft-weapon-art-design skill and
its Ace/Izanagi study. Main, shared algorithms, generators, tests, manifests,
geometry, UV, gameplay timing, audio and runtime remain master-owned.

## Evidence inspected in this revision

- Saved `/private/tmp/destiny-w208-native/frames/w208-austringer-hip.png`:
  firing arm visible, support absent. This is the defective baseline, not an
  acceptance image for the revised profile.
- Saved `w208-austringer-reload-sample-00.png` in the same directory: gun low,
  hands/contact out of view. The saved sequence record reports
  `control_epoch_changed`; no complete native reload sequence was available.
- Current main `weapon_surface_w123/austringer.json`: inspected actual rotated
  Grip_palm, Grip_heel, Backstrap, guard, cylinder and band solids. Also viewed
  `art/weapons/w123/austringer/comparison.png` (default-paint reference plus
  offline solid-model comparison).
- W201 Austringer and Ace contacts, shared skin-arm W204 geometry and W205
  framing/retargeting source. Ace supplies the close lower support-cup convention,
  not proof of correct Austringer placement.
- Actual W208 body/moving transforms and W205 Austringer rig metadata. Idle
  `80A8A575`, ADS `80A8A579`, reload `80A8A53D`; no exported camera. Source idle
  forearm lengths are about 8.14136 model units on each side.

## Explicit mesh-relative contacts

All positions are neutral weapon-model units, +Y up, muzzle -Z; rotations are
Euler degrees in Rx Ry Rz order. The shared skin-arm local center `[8,8,8]`
lands at the contact; the block forearm extends toward local **-Y**. Its solid
palm cap extends beyond that center, so the contact is not a finger-surface IK
constraint. Source lengths stay unchanged in the shared retargeter.

| Role | Position | Rotation | Reason |
| --- | --- | --- | --- |
| Firing palm | `[8,9.1,7.75]` | `[-25,0,10]` | Slightly lower/back than `[8,9.25,7.58]`; sits on the palm/backstrap neighborhood below the grip neck. Elbow extends down/right/back. |
| Support cup | `[7,8.45,8.15]` | `[-25,0,-30]` | Lower and left of the firing palm, cupping the grip underside and firing hand instead of reaching to the barrel/cylinder. Elbow extends down/left/back. |
| Cylinder handling | `[6.85,12.35,4.8]` | `[-5.537566,24.41753,-106.800959]` | Retains the real moving cylinder flank; compensates its open rotation and adds a backward/outward arm approach. |

Firing/support unit elbow directions in neutral body space are approximately
`[0.173648,-0.892539,0.416198]` and `[-0.5,-0.784886,0.365998]`.
Master's `meshArmDirections` mode must preserve these contact rotations after
body/target and carrier transforms; absolute source-camera orientation must not
overwrite them. `sourceViewRotation [0,0,-3]` is retained legacy calibration,
not an additional rotation to apply to these mesh-relative directions.

### Why the reload rotation is not simply a smaller Z roll

The W208 cylinder opens **+78 degrees about Z** around `[7.3,11.06,4.34]`.
The old target `[0,0,-80]` almost canceled that opening; at full opening its
forearm direction was `[-0.034899,-0.999391,0]`, nearly straight down with no
backward approach. Simply replacing -80 with -20 would rotate the forearm back
across the moving part.

The new local rotation is calculated as
`Rz(-78) * Rx(-25) * Rz(-30)`. After the cylinder's +78-degree rotation, the
forearm points `[-0.5,-0.78488557,0.36599815]` before body/carrier framing:
down, left, and back toward the player. The neutral flank target becomes about
`[5.94463,10.88804,4.8]` when open, beneath the swung-out cylinder. Do not store
that opened coordinate as the neutral target or apply the hinge twice.
`partHint: moving`, `policy: cylinder`, `rigAction: 80A8A53D` remain explicit.

## Shared faults for master

1. The old retargeter overwrote the correctly transformed palm rotation with
   absolute source-camera FK rotation. This discarded body/cylinder orientation
   while retaining mesh anchor positions. Master is implementing the
   `meshArmDirections` correction; this profile opts in. It is mesh-relative
   authoring with source lengths, not a shoulder/wrist IK solve.
2. The current generic reach/return envelope reaches full target at .20,
   holds through .78 and returns by .98. Austringer's flick-close starts at
   **.76**, so the hand is still about **78.4% attached at .84**, after the
   cylinder has already rotated from 78 to 12 degrees. This can swing the
   whole forearm through the frame. Release cylinder contact before .76;
   restore the lower support cup during recovery. A constant contact rotation
   cannot repair that timing error. W168's loader-contact interval is .50..76;
   the generic early reach is also an authored approximation, not source IK.
3. W204 skin-arm geometry spans local Y=1.5..9 around contact Y=8. W205 scales
   Y by sourceLength/6.5. Therefore the solid palm cap's offset from the
   contact center changes with source length (about 1.2525 units here).
   This center/cap distinction needs consideration during shared clearance
   review; neither a source wrist position nor a grip pivot proves surface
   contact. No arm geometry or length compensation is changed here.
4. Master must regenerate hand overlays and refresh the manifest's profile
   input hash. `test_motion_w208_austringer.py::test_10` still asserts
   `hideSupportAtRest` is true, the superseded one-hand requirement. Update it
   in master's scope to expect two hands and mesh-relative directions.

## Preserved assembly and verification limits

W123 retains 126 opaque cuboids / 756 explicit UV faces, split into 114 body and
12 moving cylinder/band elements (indices 32..43). Fixed lower/breech/top frame
44..47 stays fixed. No new loader, cartridge, crane, texture or mesh is added.
Framing stays `[-0.85,0.4,0.85]` translation, `[-2,0,-1]` rotation, scale `.98`.
The existing 61-pose C1 W208 generator and W168 normalized phase keys are intact.

Current revision: 10 existing read-only generator tests passed in 0.101s.
Excluded only test_10 because it asserts the obsolete one-hand flag. Separate
in-memory checks using current main shared code passed 64 arm/context cases
across both carriers: contact merge, preserved mesh-relative rotation and
translation, ordinary source lengths, and the open-cylinder direction equation.
No generated output was written. Main profile/review hashes still match the
pre-edit baseline; master must import only these two worktree files.
Historical prior-generator checks do not establish acceptance of this revision.
No CU/Vision input, native client, runtime, Gradle, build, fixture, audio or DCC
operation was performed. Master owns regeneration/build and native acceptance:
both grip carriers, classic/slim arms, idle/ADS two-hand visibility, palm/guard
clearance, open-cylinder handling, release-before-flick and two-hand recovery.
