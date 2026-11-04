# W209 r5 sourceFullChain — REJECTED; wrist translation / Recluse part contact

Latest source61 -> actual native pair -> worker correction review, before master's next integration/Vision. **No profile change.** Only this review is updated. Current MAIN profile includes sourceFullChain=true and is newer than this isolated profile; do not copy the stale worker profile over it. Main/shared code, runtime, generated assets and source Blender remain read-only.

## Actual inspection

Viewed with view_image:
- /private/tmp/destiny-w209-r5-native/screenshots/the_recluse-review.png
- /private/tmp/destiny-w209-r5-native/screenshots/the_recluse-reload.png
- /private/tmp/destiny-w209-r5-native/frames/w209-the_recluse-reload-sample-04.png

Hip retains distinct front/rear contacts; ADS aperture is readable. Reload is rejected: sample04 has a prominent pale upper sleeve rising from the lower-left elbow into the frame beside the lifted muzzle. Other selected samples frequently put much of the weapon below the viewport. Do not infer acceptance from the review sheet's later sample08, where the offending sleeve is less apparent.

Read current main sourceFullChain and source_weapon_display, not the old worker implementation. Current fullchain uses actual source forearm axes and relative upper bend; the earlier r4 arbitrary-rest-axis explanation alone no longer describes this code. The remaining conflict is translated wrist anchoring: builder still blends the left PALM toward the authored moving-magazine contact, while orientations follow evaluated source FK.

## Genuine source evidence

Read docs/qa/2026-10-28/w209/source-upper-arm.json and current SMG rig. The source-upper export documents action Armature|fp_80A8A192_reload_full|Base, slot OBSlot, source frames1..91,61 exact cached coordinates, existing-cache joint error0, armature-object coordinates and original blend SHA66480c98fd213479df5dcee83449b28eb9ef4e39329a4293e2649124f5b7ff79.

Shoulder origins are genuine direct upper-arm parents:
- left D1232BA2 -> elbow897A1504 -> wrist8C83CB67; its parent038E2D3A is clavicle-level.
- right17025F50 is explicitly b_r_upperarm -> elbowA3781DCD -> wristDE9D6BEA.
Do not substitute clavicles, display bone tails or negate the upper segment to force a desired screen direction.

Evaluated source p=.30 (source frame28), rounded armature coordinates:
- left shoulder [0.00613,0.18393,1.34657]
- left elbow [0.14365,0.33656,1.16723]
- left wrist [0.34981,0.27698,1.30391]
- weapon [0.38080,-0.08185,1.54997]

This is a genuinely lowered/outboard left hand. The ordinary source upper/forearm lengths remain ~.272709/.254418 source units. Neither hiding nor stretching is warranted.

Using the CURRENT source-weapon registration, Mrotation = C Wref^T (before accepted rest display rotation/scale), the source left-wrist displacement from idle, multiplied by32 into canonical units, is:
- p=.15: [-3.11857,-5.57763,+1.88693]
- p=.20: [-5.22097,-9.13646,+12.28336]
- p=.233333: minimum Y=-11.761124
- p=.24: [-5.64574,-11.55381,+13.43667]
- p=.30: [-9.68818,-5.59298,+2.16388]
- p=.383333: [+.92013,+2.46477,-1.72680]
- p=.40: [+1.34551,+2.79190,-2.24095]
- p=.68: [+.30346,-4.23680,+1.29379]
- p=.85: [+.32540,-.25806,+.07561]

The source trajectory descends and returns; it must not be replaced by a globally downward or85%-rest blend. Current mag pinning substantially changes where its coherent FK chain is placed.

Read-only calculation using the existing W208 magazine displacement and exact profile contact compared current FULL magazine pin with a constant-rest-calibrated source wrist. In accepted ready-body canonical coordinates (before common presentation scale/rotation), pin minus source wrist is:
- p=.20: [+5.0633,+9.7364,-9.2934], magnitude14.3806
- p=.24: [+4.9067,+11.4169,-10.6480], magnitude16.3646
- p=.30: [+7.2473,+6.2859,+1.3825], magnitude9.6927
- p=.52: [+8.7500,-4.3024,+.7066], magnitude9.7761

These are not tiny cap offsets. Pinning the wrist changes the derived elbow and shoulder by the same translation, despite correct relative bend. A profile rotation cannot repair that trajectory error.

Timing caveat: oracle timeline record index04 reports progress .38333333, but its polls are not atomic with screenshot sample04. Do not claim that PNG is exactly source frame35.5 without a paired render/tick record. The inspected image proves the defect; the numerical source evidence above names its own exact progress independently.

## Recommended shared correction — master owns implementation

Agree with master's proposal: sourceFullChain must use source WRIST displacement in the same constant parent M as source rotations/body, calibrated once at rest:

Pside(t) = Pside(ref) + Mlinear [wristSide(t)-wristSide(ref)]

Mlinear contains the single selected source-weapon-reference registration, source32 conversion and accepted uniform rest display scale. Add any common presentation/carrier/camera shift consistently to weapon and chain. Do not additionally rotate that displacement by the already animated current body or add the source weapon translation twice. Keep each side's mesh contact offset constant from reference rather than re-fitting every frame to the authored part.

For the source upper/forearm, retain current genuine source longitudinal axes and relative bend. Compute E/S from source-driven P using ordinary segment lengths. No upper-axis sign reversal is justified by the evidence above.

This is a wrist-anchored source FK retarget with constant rest registration. Two independently chosen rest hand offsets still need a shoulder-spacing/camera check; absent source camera is a stated limit, not grounds to suppress motion.

## Recluse-specific contact and phase advice

Retain the existing neutral model-space contact values as registration evidence:
- right firing/rest pivot [9.65,8.1,9.4] on rear/right grip-shaped volume
- left support/rest pivot [6.8,8.15,3.9] on front/left foregrip
- magazine handling contact [6.45,7.35,8.65] in the MAGAZINE model's unchanged canonical frame (pivot still[8,8,8])

The magazine contact is a part-local grasp point, not permission to overwrite the source wrist each frame. In fullchain mode, **part follows hand during attachment; hand does not chase part**. Right source chain is independent of this left-hand part attachment.

Current inherited hand gripWindow [.05,.20,.78,.98] is fully pinned from .20 through .78. It is a generic authored envelope, not a recovered61-source event track. The old W101/W208 magazine is seated through .12 and from .78, pulls out .12->.40, holds detached .40->.52, returns .52->.78. Its local offsets are:
- .12 [0,0,0]
- .24 [.3,-1.5,0]
- .40/.52 [.5,-4.2,.3]
- .68 [.2,-1.8,.1]
- .78 [0,0,0]

These old part timing/hold values are reference-authored, not evidence that source left wrist remains on that part throughout .20..78. In particular the real wrist makes its largest downward excursion near .2333 and has substantially returned by .3833; the old detached hold begins only at .40. Do not label those mismatched tracks recovered source contact.

Concrete mechanical-window BASELINE if retaining this existing part partition/timing for the next comparison:
- enter part-follow-hand transition .05->.12; be attached before the first existing extraction at .12
- follow the source hand across .12->.68, with source-based outgoing/incoming review
- blend back to the body-seated part .68->.78; fully seated at .78
- release part dependency after .78; source hand continues its own recovery to1

This proposed [.05,.12,.68,.78] is **an authored provisional part-attachment window only**, not a profile gripWindow change and not a proven source magazine event sequence. It must not drive/rest-blend/hide the hand. Source original video/part events must settle whether outgoing/incoming items or manipulation require separate attachment windows; the current bone-only export cannot prove continuous grasp. If retaining the old .40->.52 part hold is mandatory, review the source mismatch explicitly rather than flattening the real wrist to create it.

To preserve local grasp pose without a snap, register once at attachment:
K = HsourceHand(attach)^-1 HmagAuthored(attach)
HmagTracked(t) = HsourceHand(t) K

Use an explicitly registered actual source wrist frame for this part grip, not an arbitrary upper/forearm frame; forearm roll and wrist articulation are different. K preserves the selected authored grasp offset/orientation. The blend to seated/body part must use compatible transforms at the same progress. Do not add the old .12->.78 magazine pull a second time on top of the tracked path.

If authored magazine orientation must remain exact, an alternative translation-only contact target is:
tMag(t) = PsourceHand(t) - RmagAuthored(t) Smag [contact-[8,8,8]]
with a constant calibrated hand/contact offset if required. This preserves that orientation while moving its local contact to the source-driven grasp point. This is an authored hand-following proxy, not recovered original magazine animation.

Utility80E9F09E is a root-level utility (parent1A5C68E5), not an audited magazine bone; weapon4A0810C4 is a weapon child of right-wrist hierarchy. Do not silently treat utility as a detachable-magazine trajectory. Rear black firing-grip-shaped geometry is still inside the moving magazine partition; the earlier fixed-grip/topology limitation remains and cannot be solved by hand IK or this review.

## Return scope

No profile/phase keys changed: the needed dynamic translation and hand-driven part routing are master-owned shared changes, and current MAIN already has newer sourceFullChain. This worker did not duplicate implementation or run build/generation/Blender/runtime. Only read-only matrix/source calculations and actual PNG inspection were performed. Next Vision must include source excursion .20/.2333/.30, return near .3833/.40, reseat .68/.78, sample04 equivalent with paired progress, hip/ADS and final return. r5 remains rejected.

Current main read snapshot hashes:
- scripts/rig_arms_w205.py: 1cec6da0364243c7387748f1054c604187b4a39eca12b6ffb09a77cd56369a69
- scripts/build_first_person_hands_w201.py: 4937b236087a4f75499b83379b2d5bc33f3e54fb01122cd4b1b84856e55ddea3
- scripts/generate_reload_w208_the_recluse.py: b632d3d51ac1f13274b76d876847db0714a520e95b9d3eafc8b5f02f7aec00b4
- art/weapons/w208/the_recluse/profile.json: 7094c820ac72b9555435a2b3685568f6301b7695ef88c495c5aa80be02a94ff2
- art/weapons/w205/rigs/submachine_gun_dc16526f.json: 246fc5a37789cdddecbb7effd861b3ad79a458e9540c314da913a4197efc4778
- docs/qa/2026-10-28/w209/source-upper-arm.json: b9a4f45f7ae97bdcad35a0fe2490629e857ff711ae5538fc16acc4a32e6fb493

---

Older r4/r3/W208 reviews follow; their accepted algebra is not acceptance of r5's dynamic translation or part attachment.

# W209 SECOND Vision r4 — REJECTED; source fullchain review

Latest review-only return, before the next master Vision. **profile.json is unchanged** (SHA-256 333af8aeefc3a7af9a7610032285ed27193aa69f9a856a6c0ac467ff2fe37d91). This section supersedes earlier acceptance status and the delta-only recommendation for fullchain orientation. No CU/Vision interaction, build/generation, Blender evaluation, shared/main mutation or runtime intervention.

## Actual r4 inspection

Viewed via view_image:
- /private/tmp/destiny-w209-r4-native/screenshots/the_recluse-review.png: rear/forward hip contact roles remain distinct. The ADS optic aperture remains identifiable, but upper-arm geometry rises into the left foreground and another segment enters at lower right; the overall ADS/frame is rejected. Raised reload shows a connected elbow with an upper arm pointing nearly vertically upward.
- /private/tmp/destiny-w209-r4-native/screenshots/the_recluse-reload.png: actual labels sample01/05/08/11/15. sample01 already exposes an upturned upper segment; sample05 and sample08 make the disconnected-axis appearance clear even though the elbow joint is connected. sample11 has further upper-arm intrusion, and sample15 still shows an upper segment across the lower foreground. Merely connecting elbow vertices did not produce a coherent anatomical/source chain.

No final native acceptance. Do not conceal this with arm hiding, extra camera lowering, stretching, clipping or source-motion suppression.

## Current main diagnosis

Read current MAIN rig_arms_w205.py, build_first_person_hands_w201.py and skin_arm_models_w204.py. The source61 rig now includes leftShoulder D1232BA2 and rightShoulder 17025F50, beside the earlier elbow/wrist and weapon bones. The read snapshot still uses authored mesh contact orientation plus transported source change for forearms, then upper_arm_displays computes:

bend = Fsource(t)^T Usource(t)
Rupper = RrenderedForearm bend

That relative bend is valid **only if RrenderedForearm and Fsource share the same calibrated local axes**. A forearm obtained by applying a source delta to an arbitrary authored rest contact need not satisfy this. A connected elbow is a positional condition, not proof of axis compatibility. The problem exists at rest as well as during dynamic reload: the current upper_arm_displays path applies the bend for idle and ADS too.

Agree with master's coherent-source direction: use the source weapon rest-relative rigid pose for body, a source-calibrated forearm frame throughout fullchain, then the actual source relative upper bend. Retain current mesh palm positions and ordinary segment lengths. Do not use profile's manual right/left/reload approach rotations as the fullchain source rest axes.

## Calibration equation and coordinate domains

Use column vectors and proper orthonormal rotations:
- Wt: source weapon orientation in armature space; W0: selected source reference weapon orientation.
- Ft: source forearm frame in armature space, +Y elbow -> wrist, transverse from elbow +Y.
- Ut: source upper-arm frame in armature space, +Y shoulder -> elbow, transverse from shoulder +Y.
- A: one explicit source-weapon-local -> canonical-mesh rotation registration.
- Bt: rendered body rotation, including the same presentation/carrier transform used for its palm positions.

Then coherent source frames are:

Df(t) = Wt^T Ft
Du(t) = Wt^T Ut
Rforearm(t) = Bt A Df(t)
Rupper(t) = Rforearm(t) (Ft^T Ut) = Bt A Du(t)

At source reference, Rforearm(0) must equal B0 A W0^T F0. It generally does NOT equal the profile's arbitrary authored mesh rest rotation. This is the source rest calibration required before applying the bend. If a source-to-render basis adapter is used for a different skin segment frame, its inverse must also be included on the matching side of the relative bend; avoid an undocumented one-sided axis correction.

For source-driven BODY rotation, use the matching registration:

Bt = B0 A (W0^T Wt) A^T

This cancels the weapon-relative arm conversion coherently:
Rforearm(t) = B0 A W0^T Ft
Rupper(t) = B0 A W0^T Ut

Thus the same source reference maps both weapon and limbs. Do not combine source BODY motion with a second copy of the old W101/W208 body swing or apply the source weapon delta again to these fullchain arm orientations.

For body translation/pivot, use the corresponding homogeneous rigid transform rather than adding armature-space translation directly in camera/canonical axes:

Ht = H0 Ahat (T0^-1 Tt) Ahat^-1

Here T is the source weapon rigid pose; Ahat is explicit weapon-to-centered-mesh registration including the source-unit conversion and pivot offset. This guarantees Ht(reference)=H0 and handles rotation around an off-origin weapon bone. Use one uniform source-unit scale; remove exported scale/shear from rotations. Presentation/carrier transforms must affect body, current mesh palm anchors and both limb frames consistently.

**Flag C's domain:** existing C maps source armature XYZ to canonical axes. It can be chosen as A only if that weapon-local registration is explicit and consistent with the body construction. If preserving the old absolute armature mapping C at reference is intended, A = C W0; then the common world calibration is B0 C. Using A=C in one path and A=C W0 in another changes the rest orientation. Do not mix C Ft with C Wt^T Ft without the reference-weapon registration.

## Endpoint and scale checks for master

Let P be the retained mesh palm pivot, lf/lu the fixed ordinary source segment lengths after the shared uniform display scale, and ey=(0,1,0):

E = P - lf Rforearm ey
S = E - lu Rupper ey

Current forearm elbow geometry is local Y1.5 relative to palm pivot Y8 (span6.5); current upper elbow is Y8 and shoulder Y0.5 (span7.5). Therefore forearm Y scale must encode lf/6.5 and upper Y scale lu/7.5, applying display scale exactly once. The upper segment's +Y direction is shoulder->elbow; its local -Y extends from attached elbow toward shoulder. No sign flip or global 180-degree patch is needed if the basis definitions match these signs.

Current main's upper elbow offset and upper length span are consistent with those geometry definitions. The likely failure is frame calibration, not simply reversing an upper segment. The block hand cap ends at Y9, one local unit beyond the palm pivot; check that visible cap separately without confusing it with the wrist joint.

Keeping both mesh palms fixed while taking source orientation/length produces two independently wrist-anchored FK chains, not guaranteed source shoulder positions or a shared torso fit. Any source-wrist-to-mesh discrepancy translates its entire derived shoulder. Report that limitation and inspect shoulders/caps against the source; do not invent shoulder IK, stretch, or move palms to force a hidden endpoint. Left handling target translation and the source weapon/magazine path must remain phase-consistent; do not reapply the previous manual handling orientation inside the fullchain source frame.

Idle/ADS/reload and both endpoints must use the same source-rest calibration. Changing from manual ready axes to source axes only when dynamic becomes true can create a seam at reload start/end. Check ADS reference selection, endpoint blending, native/twohand carrier compensation and both hand contexts without discontinuous calibration switches.

## Read-only algebra result and scope

An inline Python matrix calculation on CURRENT main's61 shoulder/elbow/wrist/weapon samples checked the coherent equations for both arms. With an explicit example registration A=C W0 and B0=identity, the maximum error in Rforearm=C Ft and Rupper=C Ut, including the relative-bend factorization, was 1.5543122344752192e-15. This verifies algebra under that stated registration; it is not native acceptance, a new source Blender evaluation or a recommendation to guess A.

Snapshot hashes:
- scripts/rig_arms_w205.py: 1f474c67cb7e0abf5c670b4808294fabc23e8d5f4d02f828938663bf40cd415c
- scripts/build_first_person_hands_w201.py: 4dd28d46cabef3c251549990de12ce7b59babd69f2cca5fcf975ef74eace48fa
- scripts/skin_arm_models_w204.py: 5ee8a0d196b144e67c510cb3a9f8e34a81b21254298aca8721c75f55097c1d2b
- art/weapons/w205/rigs/submachine_gun_dc16526f.json: 246fc5a37789cdddecbb7effd861b3ad79a458e9540c314da913a4197efc4778
- Original SMG source blend SHA remains 66480c98fd213479df5dcee83449b28eb9ef4e39329a4293e2649124f5b7ff79.

Master is implementing sourceWeaponPose/fullchain separately; that in-progress implementation was not present in this read snapshot and is not claimed reviewed. Next Vision must recheck idle, ADS obstruction, sample01/05/08/11/15, both limb segments, left magazine handling and return. All shared edits/build/native validation remain master-owned.

---

Historical r3 and W208 reviews follow; neither establishes acceptance of r4 or the proposed coherent-source implementation.

# W209 FIRST source61 native review — returned before SECOND Vision

**Scoped profile delta: framing.rightWristRoll = 0 only.** All contact positions/rotations, framing translation/rotation/scale, sourceViewRotation, keepMeshSupport, meshArmDirections and visibility flags are retained. Evidence/notes updated. No main/shared edits, CU/Vision interaction, Blender evaluation, build, generation or runtime intervention.

## Observed result and provenance

Viewed actual master PNGs with view_image:
- /private/tmp/destiny-w209-r3-native/screenshots/the_recluse-review.png: hip now has rear firing/right and forward support/left contacts; ADS aperture is readable.
- /private/tmp/destiny-w209-r3-native/screenshots/the_recluse-reload.png: raised samples04/08 have sideways forearms and elbow ends fully visible inside the framebuffer. Right cap/posture remains awkward; not accepted. sample15 returns toward hip.

Read current MAIN shared source and source-blender-61.json, source-blender-recheck.json, source-axis-audit.json, source-frame-continuity.json, source-review/review-index.json, plus viewed source-review/80A8A192-contact-sheet.png. Source provenance records Blender action 80A8A192, 61 directly evaluated samples, shared-frame error0, unchanged blend SHA66480c98fd213479df5dcee83449b28eb9ef4e39329a4293e2649124f5b7ff79, current rig SHA72e3ad99e749300bebcbf0fe3a70763c3bc02f5210ea55856a9a1ad7fb998c30. The 3-pose Blender recheck reports matrix error0 and restored user scene. This worker reviewed those records and source bone sheet; did not independently open/evaluate the blend. Bone-only armature views do not establish original camera/framing or mesh grip clearance.

Current source basis uses elbow-to-wrist longitudinal and projected elbow+Y transverse; audit minimum projection exceeds0.9999997. The prior wrist-axis roll singularity is therefore not the supported explanation for this pass's splay.

## Concrete profile correction

Main SMG family supplies rightWristRoll28; framing.contact adds it to profile right.rotation Z35, making effective [-30,0,63]. This double rest calibration was absent from the prior profile's stated explicit-arm contract and its static OBB check. Override rightWristRoll0 restores the complete authored [-30,0,35], preserving the source delta, ordinary arm length and rear palm pivot. No lowering/hiding/stretching or animation attenuation is introduced. This changes right rest orientation, so SECOND native must recheck its cap, hip and ADS as well as raised reload.

## Shared parent-space diagnosis — master owns implementation

Agree with master's proposed column-vector equation:

Drest = Wref^T Fref; Dt = Wt^T Ft
Q = Dt Drest^T
Qcanonical = C Q C^T
Rout = Rbody Qcanonical RmeshRest

C is current ((0,-1,0),(0,0,1),(-1,0,0)): source X-forward/Z-up -> canonical -Z/+Y. Q is the spatial change in the common source weapon-parent axes. Current main instead uses Rbody RmeshRest (Drest^T Dt), expressing that change in each source rest-forearm frame and applying it in an arbitrary authored contact's local axes. Although both are proper rotations and identity at rest, those are different retargeting calibrations; global-armature-invariance alone cannot establish that the authored contact receives the intended parent-space axes.

Read-only inline Python calculations against CURRENT main matrices (no generation/test suite):
- Across all61 source frames and both arms, Qcanonical (C Drest) = C Dt has max matrix residual 8.881784197001252e-16. At rest Qcanonical is identity; axis conjugation preserves rotation angle and source timing. This supports the proposed transport, not native aesthetic acceptance.
- At progress .20, right weapon-frame palm-to-elbow direction with inherited +28 roll: current [+.9931,+.1166,-.0141], proposed parent [+.7127,-.0940,+.6952].
- With this profile's explicit zero extra roll, proposed right direction at .20 is [+.3710,-.4068,+.8348], versus current local-delta [+.9275,-.2981,+.2253]. Source motion is retained, not flattened.
- Proposed left direction is still [-.9410,-.2714,-.2024] at .20 and [-.8657,-.0303,-.4996] at .60. A source-preserving parent transport does not guarantee elbows leave the framebuffer. Do not force them offscreen by hiding, scaling or suppressing source poses.

Separate remaining shared issue: build_first_person_hands_w201.py computes the left moving-magazine target including reload.rotation and gripWindow, then blends that display. Current rig.apply sourceWeaponRelative branch rebuilds its orientation from body_display and config.left, discarding that blended handling rotation while retaining its translation. Parent-space transport alone does not address this loss. Master should explicitly decide the phase-appropriate rest/handling calibration and apply source transport once in the common parent frame. Do not blindly postmultiply the full source delta onto an already animated part frame; that can duplicate motion. Right must remain body-relative.

The emitted weapon still uses authored W101/W208 body motion, while arm changes are relative to the original source weapon bone. This hybrid retargeting and the absent original camera mean source pose fidelity does not prove screen framing. Compare derived elbow/cap positions against source-relative direction before changing framing; the old rear-grip/moving-magazine topology limitation remains separate.

## Return and SECOND native acceptance

Profile functional change is exactly one key; JSON parsed and contacts/other framing fields compared with pre-edit bytes. Native, build and shared regression checks remain master-owned. SECOND capture should compare samples04/08 and source-equivalent progress, rear right cap, left handling orientation/return, both carrier/hand contexts, classic/slim and retained ADS aperture. No final reload acceptance is claimed.

Read snapshot hashes:
- scripts/rig_arms_w205.py: 47ece11c0ce270b60b5a4a4a6c29fab46d3f078d995a73f802620cfcddd1fbd1
- scripts/build_first_person_hands_w201.py: 941d444d34fd49a9085226d35531963e48a0af34b57d418fa6ee1f226f329f5a
- scripts/first_person_framing_w205.py: 0eb38f274945ad91345076c935bf3f236d8b2cf117781b026ccc9a826ee16ab8
- art/weapons/w205/first-person-framing.json: 783fdde584ed580ab6c828238f6e95b3053cf4347db1a6c33983dc572d44bd90

---

The following W208 review is historical. Its static explicit-right-rotation checks now align with the zero-extra-roll profile; they are not W209 animated acceptance.

# W208 The Recluse: separated mesh contacts, 2026-10-28

Only `profile.json` and this review are edited in the existing isolated worktree. Main is read-only. Read worktree AGENTS.md, RTK.md, the weapon-art-design skill and its Ace/Izanagi study. No CU, Vision interaction, Gradle, generator execution, geometry/UV, ADS graph, audio or shared-code edit.

## Actual evidence and topology

Inspected via view_image:
- `/private/tmp/destiny-w208-native/frames/w208-the_recluse-hip.png`: a prominent arm reaches the forward black grip, matching the user's grip complaint. Pixels alone do not prove the rendered arm's right/left identity.
- `/private/tmp/destiny-w208-native/screenshots/the_recluse-reload.png`: the raised middle sample has long block arms and awkward alignment; endpoint samples return to the same forward-grip pose. These are pre-correction captures.
- Main `art/weapons/w123/the_recluse/comparison.png`: raw-source and semantic side/oblique views show forward support, open trigger and rear black grip as distinct regions.

Main canonical design SHA-256: `42fd43633d0168bf72e6bf4dbe439819a88bb6be63dd6e77f055ce32d4ef25d4`. The isolated design and canonical full/body/magazine files match current main byte for byte. Muzzle direction is **-Z**, rear is **+Z**. Element rotations must be applied before interpreting their long unrotated bounding boxes.

| Canonical element | Rotated long-axis endpoints / origin | Meaning |
| --- | --- | --- |
| foregrip/core | [8,6.22,4.65] -> [8,10.18,3.10], origin [8,8.2,3.875], X=-111.376077 degrees | Forward ribbed support grip |
| foregrip/backstrap | [8,6.20,5.28] -> [8,9.83,4.10] | Back of same forward grip |
| trigger/upper, trigger/hook | origins [8,9.725,7.325], [8,9.17,7.275] | Open trigger between the grips |
| magazine/core | [8,6.72,8.35] -> [8,9.47,9.29], origin [8,8.095,8.82], X=-71.128639 degrees | Rear black firing-grip-shaped volume, behind trigger |
| magazine/front-round | [8,6.78,7.85] -> [8,9.25,8.71] | Front rounding of that rear volume |

**Previous W201/W208 hand assignment was wrong:** right [8,8.2,3.88] and left [7.3,7.65,3.72] both cup the *forward* grip, only 0.904489 units apart. There is no separately named fixed pistol_grip element. The rear firing-grip-shaped volume belongs to the four-element moving magazine partition. Calling the rear geometry magazine does not make the forward support a suitable firing grip.

## Authored contacts

Coordinates are canonical model units; rotations are the existing helper's XYZ degrees, before body/part display transforms.

| Role | New palm pivot | Rotation | Direction of local -Y, palm toward elbow |
| --- | --- | --- | --- |
| Right firing hand | [9.65,8.1,9.4] | [-30,0,35] | [+0.573576,-0.709406,+0.409576] |
| Left forward support | [6.8,8.15,3.9] | [-32,0,-38] | [-0.615661,-0.668271,+0.417582] |
| Left reload handling | [6.45,7.35,8.65] | [-25,0,-35] | [-0.573576,-0.742404,+0.346189] |

New idle pivot separation is **6.194756 units**. Right is on the rear/right flank behind the trigger; left is on the forward/left flank. Both forearms leave down, rearward and outward, avoiding a diagonal arm across the trigger. Reload approaches the existing rear proxy from left/below, then uses the existing moving-target blend and release.

The block skin has pivot [8,8,8], hand end Y9, open elbow end Y1.5, classic width/depth 2.4; it is not the old curled glove. Thus a skin-arm pivot at the grip center would bury a solid block in the grip. These flank offsets allow the hand-end volume to meet the actual grip. At the ordinary source Y scale ~1.252518, hand-end cap centers are right [8.931585,8.988544,8.886999], support [7.571127,8.987021,3.376971], reload [7.168415,8.279874,8.216393]. They are mesh-based block-palm approximations, not recovered finger IK.

## Shared retargeting contract for master

Added **framing.meshArmDirections: true**; retained keepMeshSupport true and hideSupportAtRest false. Other framing fields, including sourceViewRotation [0,0,-3], are unchanged.

Master's shared mode must preserve right/left rotations already composed with BODY display and the left reload rotation already composed/blended with its actual moving-part target. Do not replace them with absolute source-camera elbow/wrist orientation or add source twist/carrier rotation a second time. Retain ordinary source arm lengths (~8.141364 units), with no stretch or source-wrist-separation override.

**Right remains body-relative during reload.** Only left follows the moving magazine while handling it. The neutral rear contact uses the rear black volume as evidence; it is not an instruction to attach right to that moving part.

Structural limitation: the rear firing-grip-shaped geometry itself detaches with the existing magazine proxy. Contact-only edits cannot provide a separately fixed pistol grip. A future geometry/partition audit, owned separately by master, should distinguish fixed grip shell from actual removable insert; do not relabel/swap those parts or stretch arms to hide the problem in this patch. The screenshot and existing partition do not establish the exact physical magazine boundary.

## Checks and limits

Executed a read-only, inline Python oriented-box SAT check with current canonical rotations, classic 2.4 x 2.4 arm envelope and ordinary source length. Right whole envelope intersects only magazine/core and magazine/front-round; left whole envelope only foregrip/core and foregrip/backstrap. Neither idle envelope intersects trigger or guard. Forearm sections below local Y7 clear every neutral canonical element for all three contacts. Reload palm-end envelope intersects the lower brace as well as the intended magazine/core, front-round and floorplate; exact extraction/reseat clearance is pending master native review. This is static envelope evidence, not animated/native clearance acceptance.

JSON parsing/finite values, intended contact coordinates, unchanged pre-existing framing fields and reload policy/action are checked after writing. The earlier generator/test delivery is unchanged; historical test counts are not rerun or claimed for this correction. Master owns regeneration/build/tests and native hip, both carriers/hands, classic/slim, ADS clearance, detached-magazine handling and return. No post-change native success is claimed.
