# W214 Halfdan-D — FIRST reviewed, no product change

Status: **FIRST reviewed; generator/profile unchanged; SECOND pending master.**
This feedback changes only this review.md in the assigned worktree
`/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w214-halfdan_d`.
The exact three original draft files were copied after the seed-complete signal,
with all three destinations asserted absent and all stable draft hashes verified.
The worktree stays open for master SECOND. No children, shared builds/assets,
SSD access, live Blender, Vision/CU, client, fixture or input operations by worker.
Main remains read-only. Original draft checks below are historical pre-FIRST work.

Read RTK, main AGENTS, minecraft-weapon-art-design and its Ace/Izanagi study.
This integration preserves the accepted silhouette, empty spaces, face UVs,
textures and existing part separation rather than redesigning the weapon.
The Ace/Izanagi cube counts inform the study, not a replacement geometry target.

## Original-source evidence reviewed before authoring

Master provided `/private/tmp/destiny-w214-source/source-review.json`,
`auto_rifle_943c13a2.json` and
`sheets/auto_rifle_943c13a2-80A8A395-upper-chain.png`.
Read the report and all61 evaluated matrices, and viewed the actual six-pose
XZ/YZ sheet at0,.2,.4,.6,.8,1 before generation/design. Profile records hashes.
The report attributes original source.blend evaluation to master background
Blender5.4.0 Alpha: ARMATURE only, OBSlot,
`Armature|fp_80A8A395_reload_full|Base`, range1..105 at scene30fps,
61 poses, old-cache joint maximum absolute error0 and unchanged source inputs.
Worker did not open Blender. Original blend/source-map/bone-map paths and hashes
are master-reported provenance; worker did not read those SSD files.

The supplied cache names left shoulder D1232BA2, elbow897A1504, wrist8C83CB67;
right shoulder17025F50, elbowA3781DCD, wristDE9D6BEA; weapon4A0810C4.
All61 poses contain shoulders and exact start/end matrix equality. At inherited
32-unit conversion, forearms are about8.14136, upper left8.72669/right8.72657.
Retain original evaluated bends and ordinary lengths without stretch, damping
or source excursion attenuation. Strong left handling at.4/.6 and return at1
are visible in the sheet. The auto-rifle action is shared-family bone evidence;
no recovered mesh/camera, weapon-exclusive selector, finger IK, native contact
or original magazine event track is established by these projections.

## Preserved authored assembly and motion

Read W180 generator source and AST-extracted only literal KEYS, GRIP,
MAG_ANCHOR, MAGAZINE_NAMES and the audited rigid pose_display function.
Never execute its generator, external reference loader or side-effect rendering.
W213 Steelfeather pure template exists and supplied standard-library generator,
weighted-harmonic PCHIP, absolute root override and item-graph conventions.

All11 Halfdan W180 keys remain literal-identical. GRIP[8,8.5,8.55] and
MAG_ANCHOR[8,10,3.05] remain unchanged. Preserve original rigid pivot algebra,
source-local magazine offset, translation convention, uniform scale and
native/twohand carrier. Replace per-interval smoothstop with C1 shared
weighted harmonic PCHIP tangents, zero at extrema/holds/endpoints; retain all
scalar key extrema and holds without meaningful overshoot.

Phases: shallow presentation0..10; withdrawal.10..33; magazine clear hold.33..53;
replacement/insertion.53..67; positive seating rock.67..73;
support recovery.73..90; hip return.90..1. These are authored gameplay-reference
phases retained from W180, not recovered source mesh events.
**Magazine seated progress is.67.** The first60grid sample after that is41/60;
40/60 remains just before the authored seat. No timing is retimed to a grid key.

The unchanged accepted W129 semantic source has114 elements:
110body + four whole connected Magazine_neck/body/floor/heel solids106..109.
Each original element, rotation, face, UV and field occurs exactly once.
Magwell, Charging_handle, grip, guard, straps and every other solid stay body.
No texture edit, adapter, new geometry or independently animated charging handle.
The canonical native fallback contains238 weapon elements, a separate alternative
representation retained by the original item graph.

## Presentation, contacts and attachment candidate

Copied actual `f.profile(f.load(), 'halfdan_d', 'auto_rifle')` settings:
translation[-.65,.6,0], rotation[-1,2,0], scale.98,
rightWristRoll28 and leftRotation[15,35,-35]. Add sourceFullChain=true,
keepMeshSupport=true and hideSupportAtRest=false. No additional camera offset,
visibility suppression or rest-palm correction is justified before FIRST.

Profile adds explicit reload.rigAction80A8A395 and partHint=magazine, retaining
magazine policy. Current inherited W201 right position[8,8.55,8.55],
rotation[-16,0,0]; left position[7.8,9.72,-1.8], rotation[0,90,-85];
reload.contact[7.4,7.65,3.12], rotation[-3,0,0] remain unchanged.
REST right/left mesh offsets locate source palms. reload.contact locates the
held part relative to the source palm, not a whole-chain rest correction.

Read existing build_first_person_hands_w201 gripWindow/part_shift algebra.
Its default[.05,.20,.78,.98] keeps a magazine following the source palm long
after Halfdan's authored seat.67. Supplied source object-space left-wrist minus
weapon translation at p=.666667/.733333/.8 is approximately
[-.21876,.15539,-.02055]/[-.09187,.19247,.01016]/[.27389,.04905,.01394].
Substantial valid post-seat hand travel must remain, while the magazine seats.
These coordinates establish hand travel, not an independently recovered rack event.

Candidate reload.gripWindow **[.05,.20,.53,.67]** preserves the existing reach
and full extraction/clear-hold attachment through.53, then smoothly releases
the held part over Halfdan's own authored insertion.53..67, reaching zero at
seat.67. It is deliberately different from Lonesome's.60..75 correction.
The window does not modify original FK, limb lengths, authored magazine keys,
rest/reload positions/rotations, geometry or framing. Native smooth insertion
is unverified; FIRST must check the blend before accepting this candidate.

## Pure output contract and bounded checks

`generate(root=ROOT) -> dict[Path, bytes]` is standard-library only. Import and
generate perform no writes, spawn no process and execute no old generator.
Every input uses root; no temporary evidence path is read by the generator.
Profile provenance contains absolute evidence strings but no external dependency.
Outputs are restricted to new `weapon_reload_w214_halfdan_d/halfdan_d`
model/item namespace plus this weapon's art manifest:
2static parts +244display children +1item =247pack, plus manifest =248.
Manifest records input/pack hashes without a circular manifest self-hash.

61 strictly increasing thresholds are exact float32(i/60), float index1 and
grip flag0. Native/twohand endpoint children retain canonical display exactly.
Endpoint item routes resolve the canonical graph, as do negative inactive and
non-FP routes. ADS/inspect precedence, all non-FP displays and wrapper flags
remain intact. No gameplay, reload duration, ammo, timing or audio changes.
Master owns admission, runtime60, loader, action whitelist and final assets.

Bounded verification ran entirely in memory against read-only MAIN inputs,
overlaying only owned generator/profile bytes from draft. A Python audit hook
rejected filesystem writes/mutations or subprocess spawning during checks.

- Compile/import and three generate calls passed with zero attempted writes.
  Two identical calls and a second independent virtual root returned identical
  root-relative bytes;248 absolute mapping entries,12 rooted inputs per call.
- Namespace,247pack hashes, manifest counts and source input hash stability passed.
- All114 original element/UV dictionaries reassembled exactly from110+4;
  magazine indices106..109 and fixed-body separation verified.
- All11 literal keys/constants and the complete rigid pose_display AST match W180.
  Interval scalar bounds, constant channels, clear hold and seated offsets passed.
  Finite-difference C1 spot maximum discrepancy0.001374 at epsilon1e-7;
  bound roundoff at most3.56e-15; a transit tangent remains nonzero.
- Independent direct matrix/pivot reconstruction at every authored key,
  both parts/grips/hands: maximum translation error4.98e-10 model units,
  rotation-matrix error1.11e-11. Maximum sampled Euler step5.544degrees;
  all61 endpoint/scales/non-FP-display checks passed without sampled flips.
- Item graph checks cover both grips, eight display contexts, ADS/inspect,
  negative/endpoint states, every active threshold and its preceding float32.
- Actual accepted framing and inherited right/left/reload contact coordinates
  match; explicit ordered window gives full attachment through.53 and zero
  from seat.67, including every grid41..60 recovery pose.

Master measured the integrated **all-route maximum including arms at686**, below
1000, in `docs/qa/2026-10-28/w214/budget-pass1.json`. Its recorded Halfdan profile
hash matches this worker's unchanged profile. This replaces the narrower pre-FIRST
562 reload-bank estimate as the current assembled budget evidence.114 reload-bank
weapon elements and238 canonical native fallback weapon elements are alternative
representations; the master measured all-route686 includes the arm overlays.
The generator/profile retain their historical estimate metadata byte-for-byte;
this documentation reports the later integrated measurement without a rebuild.

## FIRST image-backed feedback and justified no-change

Reviewed the two actual attached sheets (full paths below):

- `/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-28/w214/vision1/screenshots/halfdan_d-review.png`
- `/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-28/w214/vision1/screenshots/halfdan_d-reload.png`

The review sheet shows a supported hip silhouette, open centered iron sights
in ADS, ordinary skin arms and a raised receiver during handling. The reload
sheet samples01/05/09/13/17 show initial lift, presentation, magazine handling,
late hand travel and return. Those numbers are capture ordinals, not source
frames, progress values or normalized source sample indices.

Additionally viewed every full raw image
`vision1/frames/w214-halfdan_d-reload-sample-08.png` through
`w214-halfdan_d-reload-sample-15.png`, inclusive, plus
`w214-halfdan_d-ads-sample-08.png` and `w214-halfdan_d-after-reload.png`.
Raw08 exposes the lower receiver/well area;09/10 show the support palm beside
silver magazine geometry while the receiver stays raised.11..13 lower the
receiver as the left hand passes along/below it; palm/receiver overlap partially
occludes the well.14 shows the left hand separated toward the lower left with
no obvious silver magazine riding that hand;15 brings the support hand forward.
The settled after-reload image shows the whole magazine seated beneath the
receiver, support at the handguard, restored hip silhouette and HUD33.
Raw ADS08 has open centered irons with arms below the aiming view.

No visible late magazine dragging, detached seated magazine, blocked ADS,
sampled rotation flip or disconnected gross arm contact is established by these
reviewed images. The existing release window is consistent with this sequence.
**No generator/profile correction is warranted by FIRST evidence.** Preserve
source hand travel and the existing [.05,.20,.53,.67] magazine attachment window;
do not change correct product bytes just to produce a delta.

Remaining contact limits: the magazine/well is partly occluded in11..13, and
sparse stills cannot prove exact palm-surface clearance, every insertion instant
or uninterrupted motion between captures. No fingers or finger IK are present.
No identified actionable contact defect remains in the reviewed captures;
SECOND must still review insertion/release and late-hand independence.
This is a justified no-change FIRST review, not final native acceptance.

## Exact source / timeline assessment

Re-read the supplied evaluated original61 action80A8A395 under
`/private/tmp/destiny-w214-source/auto_rifle_943c13a2.json`. Source remains shared
family ARMATURE evidence, no magazine mesh/events/camera. Authored magazine
clear hold.33..53 and seat.67 remain unchanged. The source range1..105 means
source frame1+104*p; this is independent of framebuffer capture numbering.
Original source left-wrist minus weapon translation in object space:

| Source progress | Original frame | Wrist minus weapon XYZ |
| --- | --- | --- |
| .5833333333 | 61.6666666667 | [-.10168159,.10869239,.04220557] |
| .6666666667 | 70.3333333333 | [-.21876457,.15539367,-.02055490] |
| .6833333333 | 72.0666666667 | [-.19766252,.16225949,-.02204156] |
| .7000000000 | 73.8000000000 | [-.17137653,.16819786,-.00942624] |
| .7333333333 | 77.2666666667 | [-.09187441,.19246994,.01015615] |
| .7833333333 | 82.4666666667 | [.24170488,.08447136,.02967215] |
| .8000000000 | 84.2000000000 | [.27389255,.04905134,.01393640] |

This confirms substantial legitimate hand travel after authored magazine seating;
it is not a recovered rack event or camera/contact measurement. Existing smooth
gripWindow release begins.53, reaches zero at.67, and is zero for all grid41..60.
Thus the magazine follows its authored seated carrier during late source travel,
while source wrists/arms continue. No damping, stretching, hiding or retiming.

Read `vision1/sequences/w214-halfdan_d-reload.json` and
`vision1/oracles/w214-halfdan_d-reload-timeline.json` directly. Sequence capture
brackets are client ticks before/after the framebuffer acquisition:

| Capture ordinal | Client tick bracket | Nearby observation wall ms |
| --- | --- | --- |
| 08 | 651..651 | 1793139527269 |
| 09 | 653..654 | 1793139527387 |
| 10 | 656..656 | 1793139527506 |
| 11 | 658..659 | 1793139527628 |
| 12 | 661..661 | 1793139527755 |
| 13 | 663..664 | 1793139527878 |
| 14 | 666..666 | 1793139528006 |
| 15 | 668..669 | 1793139528128 |
| 17 | 673..674 | 1793139528378 |

Observation times are neighboring state polls; the capture record itself has
before/after states, not an exact synchronized render timestamp or source pose.
Server timeline rows record tick1151/p=.5833333 at1793139527.587036s,
tick1156/p=.7 at1793139527.852902s and tick1160/p=.78333336 at
1793139528.063497s. Raw11..15 therefore bracket insertion and late hand motion
in wall time, with13 near the.7 record and14/15 near the.78333336 record.
Packet/render/query latency and sparse logs prevent assigning an exact source
frame or progress to any screenshot. Capture13 is not source frame13.

Timeline has21 presentation rows. Nine active records are ticks
1127/1133/1138/1142/1146/1151/1156/1160/1164, with60grid indices
2/10/17/23/28/35/42/47/53, W214 model and duration44 throughout.
From tick1169 onward it returns to canonical weapon model, floats[0,-1],
reloading=false and ammo33/0. Finished oracle tick1227 corroborates33/0.
The after-shot oracle tick1088 has31/0; FIRST validation records two paid fire
rounds from33. An explicit empty-magazine fixture precedes the reload, so the
reload's0/0 start is not the result of those two fired rounds alone.
Sheet17 still shows HUD0 during visual return; later settled PNG and server
state, rather than that still alone, establish ammo restoration.

Read master build-pass1.json:13 targeted JUnit tests, zero failures/errors.
Master reports one additional source-binding check; worker did not rerun it.
Read native-validation.json:12 sequences total, Halfdan fire4/reload38/ADS16
captures, two paid rounds, finished33/0, released controls and neutralAfter=true.
The sequence released record clears held keys and pending steps; master batch
final-neutral-before-stop.json has leaseActive=false and all native inputs false.
These support live lifecycle/grid/ammo/cleanup findings, not continuous60fps,
exact contact at every frame, microphone listening or SECOND acceptance.

## Feedback delta, evidence and held worktree

Changed only `art/weapons/w214/halfdan_d/review.md` in the assigned worktree.
Generator and profile retain exactly the copied candidate hashes:

- generator: `a3eb58394e8b2a5f6191a084702abdf55f289dd156a07a97b34144b8bcd6d907`
- profile: `bfacc72eea633f48bab4c2e68d1af1d0a016f78c40636ef66eb9ef9e4304c10d`

Evidence SHA256 (paths relative to docs/qa/2026-10-28/w214):

- budget-pass1.json:1609a20a1e08d070fcd52b2205731d546d0b6a801cf30359336afdf58c4785a0
- build-pass1.json:6d1ccf66ddab750d632b3a6d2f3bf25dc519d4b04a330364321c7a59b31bd854
- vision1/native-validation.json:923d1b1cfc08345795fe1414f3953149e850437ce6ce431764390aa17de3f77d
- vision1/sequences/w214-halfdan_d-reload.json:d7037eb0aacbab9e0c88b5d9515c0073b6fb125cc0f94cd674fb0c79dfb8809c
- vision1/oracles/w214-halfdan_d-reload-timeline.json:5ff2a23dd5240ea49c2f2e6c10d6d34905dce8e50f29844bbf649452cbe752cb
- vision1/screenshots/halfdan_d-review.png:71d507329902d1f5b3a97ba02631d690f726fd523f2b6cef62c79997a6b01537
- vision1/screenshots/halfdan_d-reload.png:1860562b1c6911e8315ca873235fec7092f150b02fa9c210a3db0e0acfaf50cf

Worker checks this feedback turn: evidence reads, exact image inspection,
source/timeline comparison and unchanged product hash assertions only.
No builds, generator execution, output materialization, pycache writes, shared
files, game inputs, new workers or SSD/Blender modifications. Master owns SECOND
and any materialization. Keep this worktree open for SECOND; no final acceptance.
