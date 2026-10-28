# W221 IKelos SG v1.0.1 product candidate

Draft implemented from read-only current main inputs. Assigned slot is
`/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-ikelos_sg_v1_0_1`.
Only the three owned paths are deliverables:

- `scripts/generate_insert_w221_ikelos_sg_v1_0_1.py`
- `art/weapons/w221/ikelos_sg_v1_0_1/profile.json`
- `art/weapons/w221/ikelos_sg_v1_0_1/review.md`

Worktree transfer is gated on master notification and batch status `ready`.
The slot is retained for reuse per latest user steering; do not delete it.
No shared/runtime/dependency/test/generated file was edited by this worker.
Master owns commits after accepted batch; this worker does not commit.

## Original source evidence

Durable source evidence locations assigned by master are
`docs/qa/2026-10-28/w221/source-review.json`,
`docs/qa/2026-10-28/w221/source-handling-evidence.json`,
`docs/qa/2026-10-28/w221/source-sheets/shotgun_2eb0529e-80A8A3F1-upper-chain.png`,
and `art/weapons/w221/rigs/shotgun_2eb0529e.json`.
Worker read the reports/cache and actually viewed the sheet from temporary
staging copies; master will preserve them at these repository locations.
Temporary input addresses are not durable provenance. In the viewed sheet:
six paired XZ/YZ poses show the shoulders and elbows bending, then returning
near the starting chain. Master opened/evaluated the actual source.blend in a
separate background Blender 5.4.0 Alpha; this worker did not open/evaluate
Blender. Report states original input hashes unchanged and prior-cache joint
matrix maximum absolute error 0.0.

Source action `Armature|fp_80A8A3F1_reload_full|Base`, `OBSlot`, original range
1..101; 61 evaluated samples retain original shoulder -> elbow -> wrist.
All source objects are ARMATURE only: no weapon mesh, camera, or finger IK.
No per-weapon selector recovery claimed. Left wrist weapon-local movement
10.130476 versus right 5.426285 model units supports left loading hand.
Profile records the fresh cache SHA256 plus sourceBlend/sourceMap/boneMap
hashes; generator checks provenance against its selected cache.

## Mechanical and art decisions

Read the weapon-art skill and Ace/Izanagi study, actual IKelos design/contact
records, canonical surface, item graph, twohand display and surface manifest.
Viewed the IKelos W136 comparison sheet and the existing atlas. Preserve all
111 canonical body elements, explicit UVs, mauve carbon slab, copper capacitor
banks, skeletal grip/stock, bore and sight openings. There is no detachable
magazine. Body is one rigid parent; no texture edits.

Retain W201 right carrier grip `[8,8.65,8.88]` and left support rest
`[7.8,8.98,-2.8]`. Port is derived from `lower_receiver_rear` bounds
`[7.31,10.48,4.85]..[8.69,11.6,8.22]`: midpoint X8, underside Y10.48-.32,
front Z4.85+.95, giving shell contact `[8,10.16,5.8]`. This is an authored
underside loading-port estimate on the canonical solid receiver, not a
recovered open cavity. No body/UV changes are made to carve an opening.

New shell has sixteen opaque filled cuboids: four each for longitudinal case,
head, rim and crimp, length1.72 along canonical -Z-forward axis, case diameter
.56 and rim diameter.64. Existing named UV donors are lower_receiver_rear
(graphite case), capacitor_0_-1 top face (copper head/rim, avoids side diamond),
and muzzle_roof (steel crimp); finite 20..80% donor rectangles retain material
variation, never zero-area texels. New shell mechanics and port are individual
IKelos choices, not copied FILO geometry/contact.

Authored body lift reaches a stable insertion posture by initial p=.36 and
holds throughout repeated loops. Shell travels from HOME `[-1.25,-2,1.7]`
through alignment to SEATED `[0,.52,-1.35]` relative to its port contact.
Visibility is initial [.43,.84), loop [.20,.78), return hidden; only empty
geometry hides the shell. All contact/display scales stay ordinary nonzero.
After seating, invisible shell recycling reaches HOME with zero velocity at
initial end / loop start / loop end / return start. Body and shell seam
displays are identical in both grips and FP contexts.

Read `build_first_person_hands_w201.py`, `rig_arms_w205.py`,
`reload_hand_w218.py`, and FILO's rejected body-only-freeze history. Profile
opts into sourceFullChain/keepMeshSupport with hideSupportAtRest false,
sourceViewRotation [0,0,0], sourceWeaponMotion true and shell-policy
sourcePalmContactFit/sourceShellPoseHold true. Effective framing starts at
W205 shotgun family values [-.65,.6,0], [-1,2,0], scale.98; no camera offset,
axis damping, support hiding or length fitting was introduced.

Master must extend the exact IKelos ID to the existing shared pose-hold route:
initial source_p=.35*smooth(p/.36), weight=smooth(p/.1); loop source_p=.35,
weight1; return source_p=.35, weight=1-smooth(p). Source weapon AND full limbs
consume the same sample. This is explicit generic source calibration at
.35/frame36, not extracted shell-loop timing or a new full reload per shell.
Existing left contact fit follows the composed shell during handling without
changing source segment lengths. Master owns implementation of those shared
routes and profile/cache loading.

## Pure checks performed

`rtk proxy python3 -B` executed the draft in memory against current read-only
main and fresh temporary staging cache, using explicit rig_path/profile_path
overrides. Generated provenance records the durable rig/profile install paths;
source cache bytes are matched to the profile hash before generation.
A Python audit hook rejected file writes, mkdir/remove/rename and subprocesses
for import and two generate calls. Generation was deterministic and all
selected input hashes were unchanged. No bytecode cache was emitted.

- Output partition: exactly737 absolute Path -> bytes outputs, only owned W221
  model/item namespace and art manifest; none materialized by worker.
- Three banks INITIAL0..1 / LOOP2..3 / RETURN4..5, CMDfloat4; 61 poses each,
  183 samples total, 732 display children, three geometry parents, one item,
  one manifest. Both native/twohand and both FP contexts.
- Every threshold and exact bin selection matched independent float32
  division-then-addition calculation; strictly increasing183 thresholds.
- Negative fallback, nonFP, ADS, inspect, initial0 and return60 preserve the
  exact canonical graph. Endpoint body displays equal accepted grip displays.
- Canonical body/UV graph exact; nonFP display dictionaries unchanged in all
  generated display children. No new textures or removable body parts.
- Held seams equal for body and shell in both grips; empty shell geometry
  selected only outside visibility windows; all scales remain accepted.
- All shell solids have positive XYZ dimensions and finite nonzero UV area.
- PCHIP knot derivative checks, zero endpoint/hold/extremum tangents and dense
  per-segment no-overshoot checks passed for body rotation/shift/shell tracks.
- Body111 + shell16 =127 maximum simultaneous weapon elements. With required
  conservative ordinary-arm reserve448, total575 <=1000. Actual assembled
  arm count remains master measurement, not claimed as worker-generated.

## Integration and outstanding native review

Master owns generated pack/hands materialization, shared IDs/parser/60-grid,
source cache installation, framing application once, Gradle, CU and Vision.
No gameplay duration, ammo, insertion timing, audio or W219 cancellable
last-shell sound changes. 61 bank poses do not establish continuous60fps.

Candidate awaits originalBlend ->61 ->FIRST feedback -> same-worker concrete
correction or justified no-change -> master SECOND Vision. Not final native
acceptance. Review both grips/FP hands, normal-length upper-arm clearance,
left palm/shell/port contact, repeated loops and hidden HOME recycling,
initial/return/canonical seams, ADS sight clearance and interrupted/partial
reload. Do not create cosmetic metadata revisions to simulate feedback work.


## FIRST Vision feedback review — justified no-change (2026-10-28)

Decision: retain generator and profile byte-exact. No concrete contact,
visibility-timing, source-pose, or seam defect was found in the reviewed
frames and pure calculations. Do not offset the shell merely to reveal it.
Only this review.md changes for FIRST feedback; no main/shared/generated
assets, gameplay, timing, audio or source inputs were edited. Fixed worktree
slot remains retained; master owns commits after accepted batch.

Actually viewed the durable evidence under `docs/qa/2026-10-28/w221/`:

- `vision1/screenshots/ikelos_sg_v1_0_1-review.png` (hip / ADS / reload).
- `vision1/screenshots/ikelos_sg_v1_0_1-reload.png` (samples01/10/19/29/38).
- `vision1/frames/w221-ikelos_sg_v1_0_1-reload-sample-03.png`, `-04.png`,
  `-05.png`, and `-10.png` (the latter names retain the same full prefix).
- `first-post-reload-review.png`, inspecting its IKelos postreload panel.
- `source-sheets/shotgun_2eb0529e-80A8A3F1-upper-chain.png` again, comparing
  the original evaluated source chain with the explicit held-pose policy.

Observed hip has distinct support/carrier arms; ADS sight aperture is clear
in its supplied view. Reload samples show a stable held receiver, ordinary
arm shape, and the left handling hand reaching beneath the receiver. No
obvious receiver/source-arm sweep or seam pop appears in these sampled
views. Postreload panel matches the pictured hip posture with ammo7/25;
no lingering shell is separately visible. This is a sampled-frame finding,
not a claim to have watched every intervening frame or measured performance.

Near-seat inspection used raw04 and raw10, plus raw03/05 around first insert.
Read `vision1/sequences/w221-ikelos_sg_v1_0_1-reload.json` and
`vision1/oracles/w221-ikelos_sg_v1_0_1-reload-timeline.json`. Raw04 spans
client ticks757..758; nearest monitor tick757 maps approximately to server
presentation tick1364, CMD4=.8333333 (initial near-seat), with40ms between
monitor/server record times. Raw10 tick772 maps approximately to server
tick1376, CMD4=2.7666667 (loop near-seat), with123ms separation. These are
nearest observations, not exact PNG/render synchronization. Raw03 itself
cannot be assigned an exact phase from the sparse nearest-server record.

Visibility limit: receiver and left palm heavily occlude the shell in raw04,
raw10 and the reload sheet. They do not independently resolve its full
cartridge contour, exact insertion depth, disappearance instant or contact
through every pose. Absence of a visible cartridge here is not evidence of
premature geometry hiding. No camera, scale, support, or contact offset was
changed to make it conspicuous. Canonical solid receiver still has an
approximate underside port, not an extracted/cut open chamber.

Targeted pure verification after FIRST feedback (in memory, writes rejected
by Python audit hook; no full hands generation):

- Worktree generator produced737 outputs against the installed durable
  `art/weapons/w221/rigs/shotgun_2eb0529e.json` in read-only main, with its
  bytes matching the existing profile provenance. No outputs materialized.
- Rechecked all183 samples, both native/twohand grips and both FP contexts:
  the generated shell-anchor transform equals its authored rigid port-path
  transform to maximum coordinate error5.151896687e-10 display units.
- Profile selects hand LEFT and sourcePalmContactFit. Read current shared
  `build_first_person_hands_w201.py`: its shell-only source contact fitter
  blends the LEFT palm translation toward the composed reload_target, with
  initial handling fully attached by p=.36 and loop weight1. This confirms
  implementation attachment; occluded PNGs cannot alone prove every contact.
- Initial last visible grid sample50/60 has offset
  [0,.516561920,-1.334744727]; first hidden51/60 is exactly SEATED
  [0,.52,-1.35]. Loop last visible46/60 has
  [0,.514810388,-1.326318567]; first hidden47/60 is exactly SEATED.
  Thus geometry switches to empty only once seating is complete; hidden
  recycle follows afterward, with ordinary nonzero contact/display scale.
- Body AND shell display seams are exact at initial1 / loop0 / loop1 /
  return0 for both grips. Read/executed the current shared source sampler
  only: original weapon/shoulder/elbow/wrist joint samples match exactly at
  those four seams; return1 is exact rest with dynamic=false.
- Re-read durable source-review.json: action80A8A3F1, OBSlot, frames1..101,
  original61 samples, prior-cache joint error0 and allInputsUnchanged true.
  Source handling evidence again identifies LEFT. Shared source sampling
  holds .35/frame36 and blends to rest as specified. This remains authored
  generic-source phase calibration, not recovered shell events/full playback.
- Existing PCHIP C1/zero extrema/holds and canonical endpoint/fallback checks
  remain applicable: generator/profile hashes are unchanged from transfer.

Master's FIRST result is18/18 native sequences passed, authoritative paid
shotgun interrupt events and neutral cleanup. Read native-validation.json
confirming18 sequences and IKelos released interrupt with reloading=false,
a paid runtime event, and completed ammo7/25. Worker did not operate game,
CU/Vision controls, server or lease, and does not expand this to new native
coverage beyond supplied evidence.

Remaining: master SECOND Vision/acceptance is pending. Keep near-seat
occlusion and sparse capture-to-phase synchronization as documented limits;
review the same loop/return/interrupt scenario without cosmetic revisions.
No final acceptance is claimed before SECOND. Worker remains available.
