# W213 Lonesome — FIRST reviewed, attachment correction

Status: **FIRST reviewed; late magazine attachment corrected in profile only.**
SECOND Vision and final native acceptance remain pending master.
This worker has not operated Blender UI, Vision, a client, or physical inputs.

Read main AGENTS.md, RTK.md, minecraft-weapon-art-design and its Ace/Izanagi
reference, exact W164 script, W212 pure-generator pattern, current canonical
native/twohand/item, W123 semantic model/design, W201 contacts, W205 framing
and rig. Master main stays read-only; draft prepared under
`/private/tmp/destiny-w213-lonesome-draft` during worktree bootstrap.

## Original-source evidence

Read master original `.blend` headless evaluation report and evaluated61 cache,
source-map and bone-map; viewed the actual
`/private/tmp/destiny-w213-source/sheets/sidearm_c0461d9d-80A8A560-upper-chain.png`
before preparing the61 bank. Profile records exact evidence hashes.
Blender5.4.0 Alpha report: ARMATURE ONLY, no mesh/camera; action80A8A560,
slot OBSlot, frames1..67 at scene30fps,61 samples, zero prior-cache joint error,
all source inputs unchanged. Report's action display name ends `|Base` while
cache metadata retains `|Base.001`; audited action tag80A8A560 is authoritative.
Source selector3EB02F1A covers Allied Demand and Lonesome. No weapon-exclusive
selector, recovered camera, magazine mesh, or original hand geometry is claimed.
The six-panel chain changes during handling and returns at1. Upper-arm lengths
at inherited32-unit conversion are8.72669/8.72657, forearms8.14136; no stretching.

## Preserved assembly and presentation

Retain exact W164 eight authored knots, per-channel holds and all values.
Weighted-harmonic PCHIP shares C1 derivatives across keys, zeros holds/extrema
and endpoints, and avoids overshoot and repeated per-key smoothstop.
Keep local translation inside original scale/idle rotation, grip pivot
[8,9.44,8.81], tilted -10deg magazine travel, and W30 inverse-crossbow algebra.
Do not substitute W212's different translation convention.

Original97 semantic elements and face UVs remain unchanged:95 body;
heel77 and heel_lower78 form moving with the exact old internal magazine
insert copied from grip72 (same bounds, rotation, faces and UVs). Grip72 stays
fixed and solid; hidden insert/grip overlap at seating remains an authored
limitation. No redesign of barrel, silhouette, textures or material detail.
Active reload candidate bank:95+3=98 elements; plus four classic112-element
forearm/upper-arm segments gives the narrower candidate bank estimate546.
This estimate is not the master all-emitted-route maximum. The integrated
master `art/weapons/w201/manifest.json` records Lonesome684 including arms
across all emitted routes, below1000. Canonical fallback native236 and split98
are alternative representations. The numerical pre-integration estimate684
happens to match the master maximum; only the integrated manifest supports
the all-route claim.

Generate61 poses with float32(i/60) thresholds, float index1 and grip flag0.
Use exact canonical graph for endpoints, negative progress and all non-FP.
ADS/inspect selection precedes reload dispatch. Endpoint children preserve
accepted native/twohand displays exactly; all non-FP display contexts persist.
No gameplay duration, audio, ammo, combat or other weapon changes.

Profile schemaVersion1 retains sidearm framing [-1,.25,0], [-1,0,0], .98,
rightWristRoll27 and current W201 rest contacts. Opt into sourceFullChain and
keepMeshSupport; explicit hideSupportAtRest=false follows the user's visible
ordinary-arm requirement. Reload rigAction80A8A560 and partHint=moving.
Keep original FK and ordinary lengths: REST mesh offsets calibrate palms;
reload.contact moves held part relative to palm, not the whole source chain.
No stretch, attenuation, camera invention, hiding, or finger IK to mask fit.

## Handoff and checks

Pure standard-library generator: import and generate(root=ROOT) never write.
Only mapping entries within new `weapon_reload_w213_lonesome/lonesome`
models/item namespace and this weapon's art manifest are allowed. Mapping:
2 static parts +244 children +1 item =247 pack files; plus manifest =248.
Manifest hashes current inputs and pack outputs, excludes its own self hash,
and records authored partition, source/shared limits and pending native status.
Master writes all mapped outputs and owns shared loader/runtime/action whitelist,
original61+shoulder cache import, ordinary fingerless player-skin arms and QA.
The isolated baseline rig has21 samples; read-only integrated MAIN now has
61 original samples with shoulders for80A8A560. Main Lonesome manifest records
currentSharedRigSamples=61. Worker did not copy or change shared cache/loader.
No invented FK resampling fills this gap.

Targeted draft checks passed against read-only current MAIN inputs with only
owned generator/profile reads overlaid from this draft in memory:

- Standard-library compile/import, with filesystem mutation methods denied.
- Two generate calls returned identical248-entry absolute-path mappings;
  none of the mapped assets or manifest were written.
- All eight W164 authored knots match exactly; representative interval bounds,
  exact held channels, nonzero transit tangent and C1 derivative spot checks pass.
- Representative authored-key local translation/pivot results match independent
  W164 algebra within0.000002 model units; native translation max error0.
- Exactly61 strictly increasing float32(i/60) thresholds; exact native/twohand
  endpoint displays, unchanged scales/non-FP contexts, no sampled Euler flip.
- Negative progress, endpoints, ADS/inspect precedence and non-FP routes
  resolve to the exact canonical graph; middle frames choose correct grip/parts.
- Body95/moving3 retain all original elements/UVs plus exact historical insert;
  namespace restriction and candidate546/pre-integration684 arithmetic pass.
  Master integrated all-emitted-route maximum684 including arms is separate.

No full generation emission, Gradle, central tests, native codec test or game
run was performed. Private worktree metadata is ready with146083 baseline files
and fingerprint10e3f4715e73ae1a18d6f367d7ae2be88ab4f3f0710f7870161da7329229fbd7;
the three owned candidate files are installed in the assigned worktree.
FIRST native evidence is now reviewed below; SECOND remains pending master.

## FIRST actual images, source and timeline assessment

Viewed the actual review/reload sheets and full raw reload samples01,05,09,
10,11,12,13,14,15,16 under `/private/tmp/destiny-w213-pass1-native`.
Hip grip and centered irons remain clear. Sample05 shows a detached magazine
at the left palm;09 shows the insertion region. Samples11..13 show the narrow
magazine following the left palm above/front of the receiver, rather than
remaining at the lower grip. Sample16 restores the ready silhouette, but HUD0
persists in that still; ammo restoration is established by later server state.

Capture numbers are ordinals, not source frame/progress IDs. Sequence metadata
records09 at client588,10 at590..591,11 at592..593,12 at594..595,
13 at597,14 at599..600,15 at601..602,16 at604. Observation wall time
for client594 is1793137246448ms. The neighboring server records are
1080/p=float32(41/60) at1793137246.380339s and
1086/p=float32(50/60) at1793137246.700233s. Thus raw12 is within the
late handling interval, not source frame12; packet/capture latency prevents
claiming an exact synchronized source frame from these sparse records.

Source action80A8A560 is original shared-family ARMATURE evidence, with no
magazine mesh/event track or weapon-exclusive selector. Its wrist/weapon
matrices show substantial late hand motion: at source normalized.75/.80/.8333
(frames50.5/53.8/56), left wrist minus weapon translation in source object
space is approximately[-.1043,.2060,-.0082],[-.2276,.3549,-.2085],
[-.2668,.2653,-.3063]. These are source-coordinate deltas, not camera positions
or exact palm contacts. Together with the native adjacent captures, this is
consistent with legitimate late rack/return motion of the hand. It does not
justify keeping the magazine attached to that hand after insertion. Original
W164 magazine travel is zero from.75 through1, and body recovery continues.

Read the actual shared attachment implementation without executing it:
`build_first_person_hands_w201.py` uses the existing per-weapon `gripWindow`,
default[.05,.20,.78,.98], to weight the detached magazine's shift toward the
source palm. The default stays fully attached until.78, then partly attached
until.98. With sourceFullChain, original wrist FK replaces palm translations
and full-chain arm rotations; the magazine alone receives `part_shift`.
The late magazine movement therefore has a concrete attachment cause beyond
a still-image overlap. Do not suppress or stretch the valid source hand action.

Smallest owned product correction: add only
`contacts.reload.gripWindow=[.05,.20,.60,.75]` in profile. Keep the same reach
and extraction attachment through.60; blend the held part back to authored
insertion over.60..75, reaching zero attachment exactly at authored seat.75.
This ends attachment before the source hand's large late motion while preserving
all generator knots/holds, geometry/UVs, rest/reload positions/rotations, source
FK, ordinary limb lengths, framing, endpoints and fallback behavior. No new
shared hook is needed. Added FIRST evidence hashes and correction notes to
profile; generator bytes remain unchanged. This is a warranted contact-window
correction; SECOND Vision must validate insertion/release continuity, especially
raw09..14 equivalent progress. No post-correction native success is claimed.

Server timeline has16 presentation records. Active records at ticks
1056/1062/1068/1074/1080/1086 use60grid indices3/12/22/31/41/50 and
duration38 throughout. Canonical model, floats[0,-1], reloading=false and
ammo12/0 appear from tick1092. Finished oracle1157 corroborates12/0.
Read native-validation: all12 FIRST sequences passed; Lonesome fire5,
reload40, ADS19 captures, released controls and neutral final state. This
corroborates lifecycle/live grid/ammo restoration, not exact per-frame contact,
continuous60fps, or SECOND visual acceptance.

## Returned delta and bounded checks

Changed only profile.json and review.md within this worker's exact3 owned files.
Generator is byte-identical:
`c395541948d5e35db53e1d43cb06690f1810307681fd244fa7c79a438160ebc7`.
Validated profile schema/policy, exact expected delta, ordered gripWindow,
attachment unchanged through.60, smooth release with zero endpoint derivative,
and zero attachment at every grid45..60 recovery pose. Reviewed integrated MAIN
source61 and master all-route budget684 read-only. Did not execute any shared
build/generator, materialize outputs, operate Vision/CU/client/Blender UI, or
modify source/rest contacts. Master materializes this profile delta and performs
SECOND Vision. FIRST reviewed; SECOND pending master.
