# W221 Seventh Seraph Officer Revolver — FIRST reviewed, SECOND pending

Owned delta only:
- `scripts/generate_reload_w221_seventh_seraph_officer_revolver.py`
- `art/weapons/w221/seventh_seraph_officer_revolver/profile.json`
- `art/weapons/w221/seventh_seraph_officer_revolver/review.md`

## Original Blender evidence reviewed first

Master's source review (durable destination
`docs/qa/2026-10-28/w221/source-review.json`) records a separate
read-only Blender 5.4 Alpha evaluation of the actual original `.blend`, all inputs
unchanged and max prior-cache joint error 0. Worker reviewed temporary copies of
that report, the fresh rig and handling evidence, and viewed the actual six-pose
source chain sheet before implementation. Master will preserve the evidence at:

- `docs/qa/2026-10-28/w221/source-handling-evidence.json`
- `docs/qa/2026-10-28/w221/source-sheets/hand_cannon_5b24a8d7-80A8A53D-upper-chain.png`
- `art/weapons/w221/rigs/hand_cannon_5b24a8d7.json`

Scratch paths are temporary validation inputs, not durable provenance. Profile
and generated manifest name only the durable repository destinations above.
Correct source: `Armature|fp_80A8A53D_reload_full|Base`, OBSlot, frames 1–127 at
30 fps, 61 samples, full shoulder→elbow→wrist chains. This is group **5b24a8d7**,
not Duke **cedb29ae** despite the common action identifier. LEFT is the handling
hand: weapon-local wrist delta max 20.67985 model units, right 0.90054.
Only an ARMATURE exists; no weapon mesh, camera or finger IK is recovered.
This worker did not open/evaluate Blender, touch SSD sources, or prove a
weapon-exclusive selector. Exact fresh source/report/sheet hashes are in profile.

## Implementation and mechanism

Pure stdlib `generate(root=ROOT, *, rig_path=None, profile_path=None)` returns
absolute `Path -> bytes`; import/generate do not write. Default rig is
`art/weapons/w221/rigs/hand_cannon_5b24a8d7.json`; scratch overrides permit pure
checks before master installs the fresh rig. All other asset inputs resolve
from root; executing generator source supplies its own provenance hash. Scratch
rig/profile overrides retain canonical repository identities in inputSha256, so
temporary read locations cannot become manifest evidence paths.

248 outputs: 2 static geometry parents + 244 display children + 1 item graph +
1 manifest (247 pack assets), all restricted to the W221 Officer reload namespace
and its own manifest. One whole-reload CMD float1 bank, 61 poses/60 intervals,
exact IEEE754 float32(i/60); native/twohand and both FP contexts. CMD boolean0
retains grip choice. Canonical ADS/inspect guard precedes reload dispatch;
nonFP, negative fallback, p0 and p1 return the entire exact canonical item graph.

Preserve all **121 canonical meaningful solids and face UVs** exactly once:
**111 fixed body + 10 full cylinder**, canonical W136 geometry in W123 namespace,
long vented shroud, rear sight/hood/fork, underbarrel module, swept grip and brass
chamber trim. Cylinder indices 72–81 retain all shell/brass pieces; frame/rail,
sights and controls stay fixed. No element simplification, added mesh or adapters.
Keep W181 hinge [7.25,10.56,4.32], longitudinal Z axis, all eleven mechanical
knots, 82° open hold from2/11 through8/11, closure8/11→9/11 and closed recovery.
Weighted harmonic PCHIP is C1, zero at holds/extrema/endpoints and does not overshoot.
Only cylinder-local affine is emitted; body remains idle so master's shared
source weaponbone parent is replayed exactly once. W181's authored wholebody
pitch/roll/shift is deliberately not duplicated beside source replay.

Profile preserves the effective hand_cannon framing and original W201 right/left
idle contacts. Adds sourceFullChain, keepMeshSupport, hideSupportAtRest=false,
zero sourceViewRotation and explicit LEFT hand/rigAction/cylinder hint/policy.
Inherited reloadCameraLower1.5 remains unchanged; no new camera fitting, axis
damping, limb stretch, source-length filtering or hidden support.
LEFT gripWindow [.05,.20,6/11,7/11] releases while cylinder is still fully open,
strictly before close8/11 and seated9/11. Cylinder policy keeps the assembly on
its hinge rather than hand-translating it. Shared full-chain palms override
legacy blended palm translation: this envelope is not recovered contact IK.

**Source discrepancy to master:** the authoritative prompt mentions existing
axial cartridges/ejector, but the current read-only W181 script, manifest and
canonical121 geometry explicitly have no separate rounds/ejector/loader/crane.
The candidate preserves the actual full-cylinder partition and introduces no
floating or severed cartridges. Recheck the finalized worktree baseline before
transfer; if master has a newer axial partition, it needs an explicit re-audit.

## Lightweight checks performed in draft

Python3 -B import plus two pure generations under a write-rejecting audit hook:
zero writes; deterministic248 absolute outputs; exact namespace/path set;
full reassembly matches every original element and face UV; 61 distinct exact
float32 thresholds and corresponding range dispatch selection; canonical
ADS/inspect/nonFP/fallback/endpoints; every W181 mechanical knot retained;
finite progress validation; bounded C1 curve with zero one-sided derivatives
at all knots and no overshoot; hinge remains attached at every pose/carrier/
FP context within1e-7; constant scales; body and nonFP displays exact.
Max adjacent authored display Euler step22.24098°, no 180°/360° representation
flip. These checks describe generated JSON, not native visual acceptance.

Conservative assembled bound: reload121+448 ordinary arm surfaces = **569**;
raw canonical fallback234+448 = **682**, below1000. Master must measure actual
materialized routes including all arms; profile/manifest do not mark this as
native budget certification. Gameplay duration, ammo/counters and audio untouched.
No generated pack assets, shared loaders/runtime, dependencies, tests or other
source files were edited. No fullhands generation, Gradle, native client, Vision
or live DCC was run. The original temporary draft was transferred byte-for-byte into the assigned
ready worktree after master notification. Worktree-only pure validation returned
248 outputs in memory with zero generated/materialized writes, using the fresh
scratch rig override because binding that shared rig is master-owned.

## Pending sequence and retained slot

Transfer and pure worktree validation completed after ready notification;
baseline195709 files, hash20d131fe19cf2c58851434a6948223e71292498af598146204c6cb39d66031d4. Master handles shared rig
binding, profile loading, routing, arm materialization and consolidated QA.
FIRST screenshots/intervals returned to this same worker and were reviewed
below; master still performs SECOND Vision after this justified no-change decision.
No final acceptance before that sequence; 61 discrete poses do not prove
continuous60fps animation, actual sound playback or native performance.
Retain this worktree as the fixed reusable slot; never delete/archive it. User
authorizes commits only after accepted batch; master owns those commits and
workers do not commit.


## FIRST Vision feedback review — justified no-change

Master reported FIRST18/18 native sequences passed, authoritative paid-shotgun
interrupt events, and neutral cleanup. Worker read the preserved
`docs/qa/2026-10-28/w221/vision1/native-validation.json`: Officer reload28 captures,
ADS12 and fire4; finished ammo11/0; input released. This is master's execution
and the worker's evidence review, not a worker-operated game session.

Worker actually opened/viewed the Officer hip/ADS/reload sheet, reload timeline,
raw reload-sample-08 and whole-batch post-reload sheet, plus reopened the durable
original61 upper-chain sheet for comparison. Reviewed framebuffer evidence:

- `docs/qa/2026-10-28/w221/vision1/screenshots/seventh_seraph_officer_revolver-review.png` — SHA256 `e0c9d61c3146ee1896e1f546929bb52ef14f45c09a97f0245ebcd5071867d719`
- `docs/qa/2026-10-28/w221/vision1/screenshots/seventh_seraph_officer_revolver-reload.png` — SHA256 `7b37959f0e9669f665ec944d915ed37d7d9919a0096876602bd3f5ebb84d0a67`
- `docs/qa/2026-10-28/w221/vision1/frames/w221-seventh_seraph_officer_revolver-reload-sample-08.png` — SHA256 `8748532fb6bd011801810cd9130a6e93967624ab94c4a9aed7a0d8f0ce8b682c`
- `docs/qa/2026-10-28/w221/first-post-reload-review.png` — SHA256 `77107b1e8a5e6a8567494282dfcdd760805e16de8e5ba327383128eee478f97f`

Observed: ADS center sight is clear in the provided view; reload turns the whole
gun through the source presentation; the full cylinder remains attached beside
the frame and right grip stays attached. Raw08 resolves the gun/cylinder/right
hand more clearly than the montage. LEFT is low/partly below frame in many
samples and appears at the lower edge later. Post-reload Officer is back at hip
with HUD11. These samples do not establish continuous contact throughout reload.
No separate cartridge, loader/ejector or finger motion is evidenced or claimed.

**Source/calibration check:** durable source/report/sheet/handling hashes match
profile provenance. Original action80A8A53D/group5b24a8d7 still has61 complete
shoulder–elbow–wrist matrices; master report prior-cache error0. Across these61,
LEFT forearm length32 ranges8.14136196–8.14136797 and upper arm
8.72668719–8.72669267, only exported float drift. The active shared retargeter
uses fixed idle source segment lengths, not changing projected/chord lengths.
Read-only inspection of the actual materialized Officer hands graph, selecting
hip/native or hip/twohand, confirms both forearms and both upper arms are present
in all122 routes (61 poses×2 grips). Classic-model segment display scales are
constant across every such route and both FP contexts:

- LEFT forearm [0.833,1.04334723,0.833].
- RIGHT forearm [0.833,1.04334628,0.833].
- LEFT upper arm [0.833,0.96924438,0.833].
- RIGHT upper arm [0.833,0.96923083,0.833].

The longitudinal factors convert ordinary source lengths into the forearm6.5 /
upper-arm7.5 model segments; they do not animate or stretch to reach a target.
Read-only pure replay of the current main rig/framing functions gives LEFT palm
FP-right display Y -10.4653 atp.2 and -9.5413 atp.4, compared with0.0658 atrest;
atp.6 it returns to -1.5251. Atp.2 the source weapon-local LEFT wrist delta32 is
[-12.8338,-8.2552,12.9782]. Source hand travel, source weapon rotation and existing
mesh calibration explain the low presentation. The inherited common reload
camera lowering is1.5 during these phases; no extra offset was added. The active
profile has sourceFullChain=true, keepMeshSupport=true, hideSupportAtRest=false,
sourceViewRotation=[0,0,0]; no sourcePalmContactFit or LEFT-only concealment.
Shared full-chain palm translations use actual source wrist travel; cylinder
policy bypasses detached-magazine part shifting. Low visibility therefore is
consistent with source full-chain replay under the existing calibration, not a
hidden/stretching hand defect. Original ARMATURE-only evidence has no camera
or hand mesh, so it cannot certify the source camera framing or ideal hand-to-
cylinder contact in every view.

**Release/curve check:** pure W181-preserving PCHIP remains82° through8/11;
LEFT grip weight reaches0 at7/11 (0.63636), before close8/11 (0.72727) and
seated9/11 (0.81818). On the exact float32(i/60) bank the first fully released
sample is39/60; the first closing-cylinder sample is44/60. Weight stays0 through
closure/recovery. This verifies the authored release envelope, not recovered
source contact IK: full-chain palms deliberately replay source travel instead
of being pinned to that legacy cylinder target.

**Decision:** no generator/profile correction is justified by FIRST evidence.
Moving the hand into frame would change established source/mesh calibration
without recovered camera/IK evidence; the reported low visibility remains an
explicit visual limitation. Generator and profile hashes remain unchanged from
transfer. Only this owned review.md changed for FIRST. No shared/main/generated
assets, live DCC, client or dependencies were modified; no fullhands regeneration,
Gradle, export scan or worker commit was performed.

Master's preserved assembled-budgets.json reports actual route maximum682
including arms, within1000. This worker read that result, did not rerun the shared
materialization/budget batch. FIRST validates sampled frames and the stated
native scenarios; it does not prove continuous60fps, all-view visibility, exact
LEFT cylinder contact or microphone/audio acceptance. Master SECOND Vision and
final acceptance remain pending. Keep the fixed reusable worktree open and
retained for SECOND/acceptance; master owns any post-acceptance batch commit.
