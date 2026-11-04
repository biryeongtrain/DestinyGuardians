# W212 Bug-Out Bag — second candidate after FIRST Vision

FIRST Vision sheets and raw frames were received and inspected. This correction
is ready for master integration and SECOND Vision. No final native acceptance,
listening or continuous 60fps certification is claimed.

## Source review and limits

Reviewed the master's read-only evidence in
`/private/tmp/destiny-w212-source/source-review.json`,
`submachine_gun_cdf8185c.json`, and
`sheets/submachine_gun_cdf8185c-80A8A170-upper-chain.png`.
The chain sheet was inspected with view_image. It shows shoulder/elbow/wrist
motion in XZ and YZ at p=0/.2/.4/.6/.8/1, including the extended mid-reload
chain. It supplies no weapon mesh, camera, palm-clearance or native evidence.

Master evaluated the ORIGINAL source.blend in Blender 5.4.0 Alpha. The recorded
scene contains only Armature; no mesh or camera. Action
`Armature|fp_80A8A170_reload_full|Base`, slot OBSlot, spans source frames 1..91
at 30 FPS and has 61 evaluated samples. Prior cache shared-frame maximum joint
error is 0 and the source review reports all input hashes unchanged. This worker
reviewed that result and did not independently open/evaluate Blender.

The action is shared by the SMG family (including Antiope-D), not weapon-exclusive.
Source duration/range is provenance, not a change to gameplay reload duration.
The profile requests full shoulder/elbow/wrist chains at ordinary source lengths;
there are no stretch or arm-length overrides, recovered camera values, hidden
support at rest or source-motion attenuation. The evidenced reload lowering
override below is presentation calibration, not a recovered source camera.

Source provenance hashes:

- Original blend: `474d2fb3e1b97e605ed54998e6a08311a0cba7f44e826f0b98f44076302caba6`.
- Source map: `ccf84b37d2f0b48a4ffd196ab31e19e48d169ed40363e80215bad6333e57cd34`.
- Bone map: `dfb12f16b062776714efec4bda53470ae694c0ec223773e9d3b48c688c522bf9`.
- Reviewed dense JSON: `d09352a9bd907ed80efdf4a46f4436500c4ed354175538d4fcf7b832bec6043f`.
- Review JSON: `a30b83e9b4babbfefe70e09ad3be2b36488b945e29b6b865656e2bce45966db5`.
- Upper-chain sheet: `e04731565886e7c6bd52e3c860bfe1de156792f9bd815bb0553597ea334b9164`.

## Mesh, contacts and framing

Read the current W123 semantic design and canonical model, W166 authored reload,
W208 Recluse PCHIP example, W201 Bug-Out Bag contacts, W205 framing and shared
hands/rig consumers. No CodeGraph directory exists in this worktree.
Read workspace AGENTS, RTK rules and the weapon art skill plus Ace/Izanagi study.
Inspected the W123 Bug-Out Bag raw/semantic side and oblique comparison with
view_image: bronze floral shield/cage, woven cheek, separate rear black grip,
diagonal support and lower magazine remain unchanged.

The exact canonical partition is 96 body elements plus magazine indices
63/64/65/66: magazine_core, magazine_front_spine, magazine_rear_spine,
magazine_base. All 100 elements, face UVs, textures and non-element metadata
are retained. The existing `moving` name matches W201 reload.partHint and the
hands consumer's part lookup. No geometry or UV was redesigned.

The existing right palm [8,9.08,7.43] corresponds to the separate rear grip_core
(origin [8,9.12,7.42]); left [8,9.65,2.45] corresponds to the diagonal foregrip
(origin [8,9.765,2.28]); reload [7.55,6.1,7.57] corresponds to the lower magazine.
These remain authored contact estimates, not measured source-mesh contacts.
The profile overrides neither right nor left. After FIRST Vision it changes
only the reload contact to the left flank [6.0,6.1,7.57], retaining reload rotation,
`moving`, policy and `80A8A170`. This moves the held magazine relative to the
unchanged source palm; the contact is a mesh fit, not a source-bone correction.

Profile framing sets sourceFullChain=true, keepMeshSupport=true,
hideSupportAtRest=false. It inherits the current SMG family presentation:
translation [-.65,.6,0], rotation [-1,2,0], scale .98, rightWristRoll 28,
meshArmDirections/sourceWeaponRelative true. FIRST Vision justifies overriding
reloadCameraLower from inherited 2.5 to 0, removing the extra downward offset.
Ready and full ADS presentation remain unchanged; no other framing number changes.

## Generator behavior

`generate(root=ROOT) -> dict[Path, bytes]` returns 247 W212 pack assets and the
W212 manifest (248 absolute paths total) entirely in memory. Import and generate
do not create directories or write assets. There is no materializing CLI.
The master owns writing the returned mapping, including manifest.json.

The standard-library port keeps W166's exact KEYS, GRIP and rigid-transform
algebra, checking those constants through AST rather than importing the old
Pillow/numpy script. Full body/magazine hold .34..46 and seated-magazine holds
through .10/from .66 are retained. Per-key smoothstop is replaced with the W208
weighted harmonic PCHIP rule: shared C1 derivatives, zero at endpoints,
holds and extrema, no monotone-span overshoot.

The namespace is `weapon_reload_w212_bug_out_bag/bug_out_bag`.
61 samples use normalized i/60; thresholds use float32(i/60), progressFloatIndex=1,
gripFlagIndex=0. Endpoint children retain the complete accepted native/twohand
display dictionaries exactly, and endpoint item graphs use the exact canonical
graph. Negative progress and all non-FP contexts use canonical fallback.
ADS/inspect select the canonical graph before reload dispatch. All non-FP
display dictionaries remain exact at every sample.

The returned manifest records partition, input/output hashes, action 80A8A170,
61 samples, geometry/UV unchanged, timing/mechanics/audio unchanged and native
acceptance false. Weapon/magazine motion is still W166's authored approximation;
source-chain arms do not make it recovered magazine IK. 61 bank poses are not
proof of continuous 60fps; runtime update cadence is unchanged.

## Checks performed

Read-only checks executed in memory with a Python audit hook rejecting filesystem
writes during import/generation:

- Deterministic mapping: 248 absolute Path -> bytes entries, 247 pack assets,
  all JSON parsed; no import/generate write attempts.
- Exact 96+4 partition and canonical element/UV/texture/metadata preservation.
- All61 x 2 parts x 2 grips match the verbatim W166 rigid-display algebra when
  supplied the new Hermite sampler; endpoints and all non-FP displays are exact.
- Every original authored knot is exact; full and seated holds remain exact.
  101 positions per channel per knot span showed no overshoot. Shared knot
  derivative finite-difference discrepancy was below .000873 at epsilon 1e-7.
- 288 graph states across FP/non-FP, native/twohand, hip/ADS/inspect,
  negative/end/interior progress retained routing and precedence.
- All thresholds equal float32(i/60). Invalid/nonfinite sampler progress rejects.
- All61 displays are finite; largest neighboring Euler component step is 8.420923
  degrees, with no 180-degree branch jump. Euler roundtrip matrix residual is 0.

No old generator was executed. No Gradle, full project generation, shared
hands generation, tests file, QA input, client manipulation, commit, stash,
reset or push was performed.

## Integration and remaining review

The seeded W205 SMG cache has 21 reload samples. Master's reviewed temporary
replacement has 61 and includes source shoulders. The generator reports the
actual input rig sample count honestly. Master confirms main already has the
reviewed source61 cache and shared W212 loader/actions/runtime. Integrate and
regenerate the returned mapping against main, not the stale private rig.

Master owns the W212 profile loader, action whitelist, runtime/60-interval
routing, source rig cache, hands generation, shared manifests/tests and native QA.
Only the three assigned files are supplied here; the returned manifest and asset
bytes are not materialized by this worker.

FIRST native inspection and corrections are recorded below. Master performs
SECOND Vision before final acceptance.


## FIRST native evidence and exact correction

Inspected with view_image:

- `/private/tmp/destiny-w212-pass1-native/screenshots/bug_out_bag-review.png`.
- `/private/tmp/destiny-w212-pass1-native/screenshots/bug_out_bag-reload.png`.
- Raw frames `frames/w212-bug_out_bag-reload-sample-00.png`, 07, 08, 09, 10,
  and 11 under that same FIRST native directory.
- Original source61 upper-chain sheet again before deciding on contact.

The hip view has distinct rear/right and forward/left contacts, and the ADS sight
aperture is readable. Preserve those rest contacts and full ADS. The raw entry
sample00 shows only a small weapon portion above the bottom; sample11 return is
also low. The inherited SMG reloadCameraLower=2.5 adds a downward shift to this
actual source path. Set it to 0. At full lowering-envelope weight this raises the
whole weapon/arm assembly 2.5 display units relative to FIRST, with zero rotation
or scale change. The envelope vanishes at endpoints. The earliest source dip can
remain because the envelope is still rising there; SECOND must check it honestly.

Raw08 has a bare-looking block palm with only a small gray sliver at its cap;
raw10 has the hand crossing as source FK returns. The server timeline and raw
file wall times place raw08 around p=.50..55; this is a bracket, not exact render
synchronization. The magazine handling weight is 1 there, and release only starts
at .78. It is therefore not legitimate scheduled release. The source contains no
magazine mesh/camera, so it cannot independently prove near-plane clipping.

Read-only calculation used CURRENT main source_weapon_display,
source_palm_translations and sourceFullChain direction/ordinary forearm length,
the original61 JSON and exact canonical four magazine solids. At p=32/60,
magazine bounds in left-forearm local coordinates with the FIRST contact are:
X[6.73084,9.66366], Y[7.66012,8.87110], Z[6.81565,9.45548]. The classic solid
hand has width/depth2.4 (X/Z6.8..9.2) and cap Y9. Most magazine volume is inside
the hand, with the entire Y bound below its cap. This supports palm occlusion,
not a source-action error. Do not claim measured near-plane exclusion.

Set reload.contact to [6.0,6.1,7.57] from [7.55,6.1,7.57]. This is a left-flank
mesh fit: the four magazine solids have X7.48..8.52 overall; the palm target is
1.48 units outside that flank, allowing the solid hand cross-section room.
The existing shared part_shift moves the magazine, not the source wrist. At
p=32/60, the corrected magazine Y bounds are [8.86050,10.07148]: the magazine
protrudes past capY9 with some contact overlap. At p=.50 corrected Y bounds are
[8.94032,10.03369], and at p=41/60 [8.70837,10.09447]. These are geometric
clearance checks, not post-change native proof. Source wrist positions, arm
rotations/lengths and release window remain unchanged. No generator edit.

Read timeline `oracles/w212-bug_out_bag-reload-timeline.json`: runtime dense values
include .06666667/.2/.36666667/.55/.68333334/.8333333, reloadDuration38;
canonical return has progress -1 and ammo36. Master reports all12 actual native
sequences passed, all neutral, JUnit13. Those broad checks are master-reported;
this worker read the Bug-Out Bag timeline and images only. No listening or
continuous60fps certification. SECOND Vision still needs entry/return crop,
visible held magazine at raw08/10 equivalents, reseat and rest recovery.


Correction checks: profile JSON parses; generator SHA remains
`0967d6d435f5e6c8d500db450dc3d0acc8271d4ccd1d262d83abfff74452c31f`;
original61 SHA remains unchanged. Across all61 right-FP samples, the flank-contact
change leaves source palm translation/rotation/ordinary scale exactly unchanged.
Removing lowering changes body, palm and magazine by the same Y offset (maximum
+2.5 versus FIRST), with no X/Z, rotation or scale change. Profile has no right/left
rest-contact override. No generated output, shared code, main or QA file written.
Post-correction native appearance remains unverified until master SECOND Vision.
