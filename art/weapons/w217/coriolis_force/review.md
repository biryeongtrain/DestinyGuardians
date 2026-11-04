# W217 Coriolis Force — FIRST reviewed, SECOND pending

Only the W217 generator, profile and this review are worker-owned. Master owns shared binding, runtime, generated assets, arms, build and native QA. FIRST has now been reviewed by the same worker; the justified nochange response is below. SECOND remains pending.

The port preserves W189's 104 textured elements: 102 body elements and only cartridge_solid60/cartridge_upper61 as the rigid moving cell. All13 knots and five vector channels, geometry/UV, grip pivot[8,10.5,7.05], cell anchor[8,10.95,-.52], original cell rotation and twohand framing correction remain exact. Red surround/floor/toe, receiver, triggerguard, rear grip, stock and U clamp remain fixed. No whole-grip displacement is justified by a lower cell intersection.

The W215/216 interpolation template supplies C1 weighted harmonic PCHIP over unchanged nonuniform authored knots. Endpoints, extrema and actual flat channels have zero tangents; ordinary monotone knots share nonzero derivatives. The pure stdlib generate(root=ROOT) returns248 absolute Path-to-bytes outputs (247pack assets plus manifest), without import/generate writes. Sixty-one poses span60intervals; this does not establish native continuous60fps interpolation.

Master's fresh Blender5.4.0 Alpha report evaluates Armature|fp_80A8A43C_reload_full|Base, OBSlot, source1..106 at30fps. Old matrix error0 and allInputsUnchanged true. The rig contains only ARMATURE; weapon-relative shoulder/elbow/wrist chains are real source evidence, while weapon mesh, camera and IK were not recovered. Worker read the report/fresh matrices and viewed the actual six-pose XZ/YZ upper-chain sheet. ADCA is iron_sight_idle, not reload. No weapon-exclusive source is invented.

Fresh required rig SHA256: ed8727287afffb9ff4ca1f5d87bae9a83e8b92c269bd05a704b41d089f8c5fd5. Required report SHA256: d8edb0d97be1b4cc1446363216ac271fb6bbb1a91f3b52f1fa0b3dc48388fd6a. Master installs exact source bytes at art/weapons/w205/rigs/fusion_rifle_9ab6be45.json and docs/qa/2026-10-28/w217/source/source-review.json. Worker does not copy shared files into the baseline.

The viewed retained W189 storyboard contains same-weapon footage n772..856, Ironworker Gaming 67wv69MomYQ: grasp central dark cell, withdraw downward from fixed red opening, replace from below-left, seat, recover. Cell/socket boundary and hidden path remain authored. Source perks and7-round footage do not alter local6round/45tick reload,667ms charge/14charge ticks,7bolt shared-ammo volley or audio.

The profile retains effective fusion framing translation[-.65,.6,0], rotation[-1,2,0], scale.98, rightWristRoll28 and leftRotation[15,35,-35]. Full source chains, mesh support and visible resting support are explicit. Ordinary-length fingerless skin arms remain master-owned. Existing rest/reload contact positions and rotations remain unchanged. contacts.reload explicitly selects80A8A43C, partHint=magazine, policy=magazine, gripWindow[.05,.18,.65,.74]. Attachment releases fully by the same-weapon neutral cell seat.74; cell local translation/rotation stay neutral through1 while the body lowers.

Exact canonical endpoint item graphs, accepted native/twohand displays, nonFP displays, ADS/inspect precedence and inactive/negative/overshoot fallbacks are retained. All legacy geometry/display/timing/audio pins remain enforced.

Budget estimate:104weapon+448arm reserve=552reload; canonical241+448=689. No elements added. Master must measure all actually assembled routes, including ADS/inspect, under1000.

Focused validation passed after READY. Compiled/imported the candidate and called generate(root=worker) twice under a filesystem-mutation audit hook:248 deterministic absolute Path-to-bytes outputs,247pack assets, zero write attempts. Overrode only the stale baseline rig and missing W217 report reads in memory with exact current MAIN bytes; those matched the reviewed /private/tmp exports. Baseline rig remained untouched.

Geometry/UV/rotation reconstruction equals all104 canonical elements, including102fixed+2moving. AST literal audit confirms13keys/fivechannels/anchors/names/PINS remain exact without old-generator import or execution. Dense segment samples stayed within authored bounds and preserved flat channels exactly. Finite differences at interior knots matched shared C1 tangents (maximum left/right derivative mismatch0.0006473);63monotone channel knots retained nonzero slopes. Invalid/nonfinite progress was rejected.

All244display children were checked for accepted native/twohand endpoints and unchanged nonFP displays. All61pose rotations/translations were finite, max adjacent Euler component step7.209500204degrees, minimum absolute cos(EulerY)0.9087852334: no sampled flip or near singularity. Seated cell has no independent translation/rotation from.74..1. A focused item-graph evaluator verified canonical negative/inactive0/end1/overshoot, nonFP and ADS/inspect precedence, with both native/twohand reload composites on active hip progress.

Fresh source hash/action/range/full-chain validation and552reload/689canonical arm-reserve estimates passed. No generated bytes were materialized. No build, Java, central/full gate, game, audio listening, Vision or CU was run by worker. FIRST/SECOND and actual composed-route measurements remain master-owned.

FIRST sampled visibility observations and the same-worker nochange decision are documented below. SECOND remains required. Source bone-only projections and offline checks alone cannot establish native contact, hidden clearance, continuous interpolation, audio listening or final all-route budget.

## FIRST same-worker response — justified no product change

Worker reviewed the actual sealed FIRST PNGs at /Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-28/w217/vision1: both screenshots/coriolis_force-review.png and screenshots/coriolis_force-reload.png, raw frames/w217-coriolis_force-reload-sample-03.png, -06.png, -09.png and frames/w217-coriolis_force-after-reload.png. All six image SHA256 values match evidence-sha256.json. The source report/action, authored phase timing, native reload sequence, server progress timeline and Coriolis validation row were also read. Worker did not operate the game or write sealed evidence.

Observed: sample03 shows the dark cell down beside the support palm, visibly separated from the central red bay. Sample06 shows the wider diagonal43C handling pose with the red frame retained. Sample09 shows recovery toward the forward hold. The after-reload PNG shows the canonical held weapon and HUD6/30. The review sheet shows preserved resting framing and the open central ADS sight. These are sampled visible observations, not a continuous contact or hidden-clearance certification. No hard visible defect was identified that supports changing carrier motion, geometry, UV, rest or ADS.

Progress evidence: native-validation.json records28reload captures, neutral release and finishedAmmo6/30; the server timeline reports45tick duration and progress .016666668,.15,.28333333,.41666666,.55,.7,.81666666,.95, then inactive-1 with6/30. Raw03 is bracketed by client ticks2017..2019, raw06 by2027..2029, raw09 by2037..2039. Capture indices are not generator pose indices, and client screenshot brackets are not exact server-progress timestamps. In particular raw09 does not prove the precise.74 release instant. Original Blender reload_full80A8A43C is1..106 at30fps; the source evidence remains full-chain ARMATURE only. Authored W189 insertion ends.74, followed by the.74..80 seat hold and lowering. Source range and footage/perk timing do not retime the45tick product reload.

Targeted post-FIRST check re-read the actual shared build_first_person_hands_w201.py rule: magazine part_shift multiplies source-palm displacement by reload_grip_weight, using the profile gripWindow. With[.05,.18,.65,.74], attachment weight is1 at.65, .4170096022 at.70, .0156480211 at44/60, and exactly0 at.74 and45/60 through1. A read-only candidate evaluation confirmed cell-local translation/rotation remain exactly zero throughout.74..1. Thus the configured source-palm attachment cannot continue dragging the cell after its authored seat; the sampled PNGs do not independently establish the exact physical seating instant.

The bay/grip junction and cell socket interior are partly occluded by the hand and red frame. FIRST therefore leaves hidden penetration depth, lower-cell/grip overlap and full continuous palm clearance unresolved. The images supply no basis for moving the entire rear grip, receiver or triggerguard, shortening arms, suppressing the support chain or changing the cell partition. Preserve all104 geometry/UV elements and all13knots/fivechannels because the evidence does not support a clearance change.

Decision: no generator or profile change. Their exact pre-FIRST hashes remain:

- scripts/generate_reload_w217_coriolis_force.py: 5e76b9ef04be14d68735e71e051eea8810430af45306a96391434631e9a9ee91
- art/weapons/w217/coriolis_force/profile.json: 99135603e2edd41fa0c3c9ef47cfd73d09312df3c7e2365d4e852afeba3e941b

Only this owned review.md changes in the FIRST response. No generated/shared/main/QA files changed; canonical rest/ADS, geometry/UV, gameplay and audio remain intact. FIRST -> same-worker justified nochange is now documented. Master SECOND of the same scenario is still required before final acceptance. No fresh full gate or native input was run by worker; continuous60fps, microphone listening, hidden geometry fidelity and all-route native clearance are not certified.

Viewed FIRST evidence SHA256:

- screenshots/coriolis_force-review.png: 7749d28805b8fd529b002d215a587789c3968bc1418177e61df4e233add6f70a
- screenshots/coriolis_force-reload.png: 3f815ec1c1c84d5e6540a3c335a3bac2b49d15f7425149eeb44ce07baf6ed261
- frames/w217-coriolis_force-reload-sample-03.png: cc2ca444fe6635adbcf13787b6cbe1418e035d5fcd805851ba46075e7bc052f2
- frames/w217-coriolis_force-reload-sample-06.png: 6374e2ef3d3fb271e7941132e0e0aa813f93f9a1b476bbb7bd42a417cac66be1
- frames/w217-coriolis_force-reload-sample-09.png: bbf02af40baf53cdd66819d073600461e0f041924663e70e2ed8a35bd4780b41
- frames/w217-coriolis_force-after-reload.png: 5563404d4fe06e2465d150732b3c1d1cc994c8433a928071e8a0c597699ade44
