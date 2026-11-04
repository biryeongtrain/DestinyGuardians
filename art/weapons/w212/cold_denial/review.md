# W212 Cold Denial — FIRST native feedback

Status: **FIRST native reviewed; evidence-based no-change** to generator,
framing or contacts. Profile evidence/notes and this review record the feedback.
Return unchanged presentation behavior for master SECOND Vision; final native
acceptance is still pending.

## Source findings

Read the master-provided original-Blender evaluation report
`/private/tmp/destiny-w212-source/source-review.json`, the evaluated
`pulse_rifle_b4d01502.json`, and viewed
`sheets/pulse_rifle_b4d01502-80A8A36A-upper-chain.png` using `view_image`.
This worker did not independently open/evaluate Blender.

The report records Blender 5.4.0 Alpha, Armature only (no mesh or camera),
`Armature|fp_80A8A36A_reload_full|Base`, slot `OBSlot`, source frames
1..105 at scene 30 fps, 61 evaluated samples, zero prior-cache joint error
and unchanged original inputs. Reload-full and reload-empty labels share the
action. The family cache covers Cold Denial, Bygones and other pulses; it is
not evidence of a Cold Denial-exclusive clip. Matrices are armature-object,
row-major with column vectors; no matrix_world is applied.

Reviewed evidence SHA-256:

| Input | SHA-256 |
| --- | --- |
| Original source.blend (master report) | `042a9965b8f02a7e7bfda10914e2711b31e2add9417884d8b277e11ab9668f4d` |
| Source map (master report) | `73251b2726fbb4f652eb14baf6fe0e3552a9351c1515271684525f4b95bdcb74` |
| Bone map (master report) | `411b794dbe4c8791b9bc1c82bc1ef6833aeb71d308aaa08aab7aa0a205635547` |
| source-review.json (worker read) | `a30b83e9b4babbfefe70e09ad3be2b36488b945e29b6b865656e2bce45966db5` |
| Evaluated pulse cache (worker read) | `7048f5c3143a9298879df84268225bd961563b4a6f3d5bc9bd69254d2d99ef16` |
| Source upper-chain sheet (worker viewed) | `be5cc8f75b3b1517f4b21eb50ca19400c9998a95404de62996eb72839fbb9549` |

The actual six-sample XZ/YZ sheet shows both upper/lower chains moving during
handling and returning at p=1. It cannot establish camera framing or contact
with a mesh absent from that source. Direct cache checks found exactly 61
progress samples i/60. At the inherited 32-unit conversion, left/right upper
arms remain approximately 8.72669/8.72657 model units and forearms 8.14136;
tiny per-frame differences are floating-point noise. No length override,
stretching, invented camera or attenuation of source motion is introduced.

## Mesh, partition and contacts

Read the current 100-element W138 semantic model in the W123 namespace,
its design metadata, W167 reload code and W201 Cold Denial contacts.
Viewed the actual W123 source/semantic side, front/rear oblique and detail
comparison, plus the W167 cached gameplay storyboard (4.600..6.000s,
`j1jKsnDD6Ss`). The footage shows near-upright bullpup rear-magazine
handling and recovery; occluded travel remains authored approximation.

Keep socket element 89 (`magazine_socket`) fixed in the 95-element body.
Only 90..94 detach as `moving`: core, two edges, floor, feed band. They
retain exact source solids, element rotations, face UVs and textures.
The simultaneously displayed assembly remains **95 + 5 = 100 elements**,
below the 1,000-element limit. Full mesh and split mesh are alternative
representations.

The rotated `grip_core` (82) is ahead of the rear magazine;
`lower_handguard` (24) supports the forward hand. Existing W201 right
[8,8.62,8.35], left [7.8,9.42,-1.2] and reload [7.3,8.1,12.15] target
the firing grip, handguard underside and magazine left flank. Retain these
positions/rotations and the existing magazine policy. FIRST native evidence
also supports retaining these values without a new right/left override. Keep `partHint: moving`
to match the emitted part names. Only the reload action adds `80A8A36A`.

The profile retains pulse-family translation [-0.65,0.6,0], rotation
[-1,2,0], scale .98, rightWristRoll 28 and leftRotation [15,35,-35].
It enables `sourceFullChain`, `keepMeshSupport` and visible rest support
(`hideSupportAtRest: false`). These framing values are inherited authored
calibration, not recovered camera data.

## Implementation and handoff

The standalone standard-library generator ports only W167 constants and rigid
grip-pivot/display algebra. It never imports or runs the historical generator
(which requires Pillow/NumPy and has a materializing main entry point).
All W167 KEYS, channel values, normalized phases and holds remain exact;
weighted harmonic PCHIP tangents replace per-key smoothstop. Tangents are
shared across knots and zero at endpoint/hold/extremum channels.

`generate(root=ROOT)` returns an absolute `Path -> bytes` mapping with no
writes. Its namespace is `weapon_reload_w212_cold_denial/cold_denial`.
The mapping contains 2 static parts, 244 display children (61 x 2 x 2),
1 item graph and 1 manifest: **247 pack files / 248 total returned files**.
The manifest is returned only, not created in this worker's filesystem.
Its input hashes cover the accepted asset, texture, profile, contact table,
rig cache, framing, design and source scripts; output hashes cover all pack
files, excluding the manifest's own self hash.

Thresholds are exactly float32(i/60), progressFloatIndex 1, gripFlagIndex 0.
Canonical item graphs are deep-copied at both endpoints and all fallback
branches. ADS/inspect mode selection precedes reload dispatch. Native and
twohand display children copy the accepted endpoint displays exactly and
retain all non-FP contexts and scales throughout the bank.

Shared loader/runtime/rig cache/hands generation, file materialization,
central tests and native QA belong to master. Master reports the W212 loader,
actions and runtime were added in MAIN; this worker does not alter or import
those shared changes into its baseline. No runtime, combat, ammunition,
gameplay duration, audio, full ADS or 3P change is requested. Weapon/magazine
motion remains authored W167 motion; the separately selected source chain is
not proof of extracted weapon-motion equivalence. 61 discrete poses do not
prove continuous 60fps or change server update pacing.

## Checks

Passed targeted read-only checks after private metadata reported `ready`
with baseline fingerprint
`5728d043ce9f9a3ed93855debafbff261c2cbf4801bf444a83aae5ec09b0079f`:

- Compiled and executed with standard-library imports only.
- Every W167 authored knot matches exactly. All nine channels stay within
  their interval endpoint bounds, including held channels; finite-difference
  C1 derivative mismatch was at most 0.000923 (epsilon 1e-7).
- Exactly 61 float32(i/60) thresholds, strictly increasing, indices 1/0.
- Two calls to `generate` returned identical 248-entry absolute Path/bytes
  mappings (247 pack files plus manifest). An audit hook forbade filesystem
  writes, directory creation, removals/renames and subprocess launch during
  import/generation: zero write events. No returned output exists on disk.
- Static part elements/UV/textures equal the accepted source partition;
  assembled count is 95+5=100. Both grips copy exact endpoint displays;
  every sample preserves non-FP contexts and scales.
- 216 graph scenarios verify native/twohand routing, negative progress,
  non-FP, ADS/inspect precedence and exact endpoint fallback.
- All generated numeric displays are finite. Largest adjacent Euler channel
  step across both grips/contexts/parts is 13.877868338 degrees; no Euler
  branch flip was detected in the sampled bank. This is not native visual QA.
- Manifest input hashes match current inputs; output hashes match all
  returned pack bytes. Geometry/timing preservation and no-native-acceptance
  flags are present.

Only the three assigned new files are created. The manifest/pack bank is
returned in memory only. No Gradle, full batch generation, historical
generator execution, native input, client/lease changes, commit, stash, reset
or push was performed.

## FIRST native evidence and no-change decision

This worker viewed both actual FIRST sheets with `view_image`:
`/private/tmp/destiny-w212-pass1-native/screenshots/cold_denial-review.png`
and `cold_denial-reload.png`. It also viewed the full raw reload samples
07, 09 and 27, re-viewed the original61 upper-chain sheet, rechecked the
61-sample source cache hash/ordinary limb lengths and semantic W201 contacts,
and read the Cold Denial server timeline. No native client/QA input was sent.

- Hip: forward support and rear firing-grip regions are visible; the mesh
  remains readable with distinct support/firing contacts.
- Full ADS: aperture is centered and clear of the hands in the supplied view.
  No new ADS or palm/framing offset is justified.
- Raised reload: the muzzle is cropped at the top. The firing grip, rear
  magazine and handling area remain on screen. This is a documented framing
  limitation, not a reason to invent camera data, shorten/stretch source arms,
  attenuate the source action or change accepted framing without a visible
  handling defect.
- Raw sample07: detached rear magazine sits beside the left palm. The firing
  hand stays at the grip/body; the fixed socket is distinct from the detached
  assembly. This supports `partHint: moving` and the inherited magazine flank
  contact rather than a new partition or contact correction.
- Raw sample09: magazine approaches the rear socket while the handling hand
  remains beside it; the sampled view supports reseating rather than an
  incorrect hand-role swap. It does not prove exact contact at every instant.
- Raw sample27: hip presentation is restored with HUD28. The source sheet also
  returns its chains at p=1. Capture sample ordinals are not source pose indices
  or precisely synchronized progress measurements.

Decision: retain `80A8A36A`, sourceFullChain, visible mesh support, original
limb lengths, W201 contacts, family framing and the W167/PCHIP weapon bank.
There is no image-backed correction warranted in the owned generator or
presentation settings. The ORIGINAL source is bone-only and shared-family;
these native images do not establish a recovered source camera or exact
source mesh/finger contact. The generator remains byte-identical SHA-256
`c7813127dd0e864214563f555627d9f2bca0ec2b4afea9b99b9c37a498882192`.

FIRST evidence SHA-256 (all read/viewed by this worker):

| Relative to `/private/tmp/destiny-w212-pass1-native` | SHA-256 |
| --- | --- |
| `screenshots/cold_denial-review.png` | `b291193944f58423c07ba73bcaaf17793992336efd6c5dc6a029dfe904cff607` |
| `screenshots/cold_denial-reload.png` | `2a14bfbd6b338a128db29d805955eb3e6b3b8837a80cde3d73daf202c3be1a02` |
| `frames/w212-cold_denial-reload-sample-07.png` | `ad1f2c25224ac3b518016d9327f6c55d1a4275417c245c8eb49e1755a004904b` |
| `frames/w212-cold_denial-reload-sample-09.png` | `c4a46e1a865b205774b0874143cd6e29e15db6914e3073f61d4079fed14e5e89` |
| `frames/w212-cold_denial-reload-sample-27.png` | `1f7ac101d2ce694d3dfc405bec2478e2c62c9e62eafaf109f243d3208b198343` |
| `oracles/w212-cold_denial-reload-timeline.json` | `3e2e2e63bdd0d5412014855d7da4a5a4706d6b0b5eca62dd3db06edd91b11e8a` |

The Cold Denial oracle contains 18 presentation snapshots. Eight active
reload snapshots select the W212 namespace with normalized float values
corresponding to float32 grid60 indices 0,8,16,24,32,40,50,57. This independently
corroborates sampled routing, not delivery/rendering of all 61 poses.
`reloadDuration=44` remains constant. At tick2096 and subsequent terminal
records the canonical model returns with floats [0,-1], reloading=false,
ammo28/0, swap=none and handling=NONE:0. Final raw sample27 agrees with the
restored HUD ammunition and hip presentation.

Master separately reports all 12 actual native sequences passed, grid60
runtime server values, ammunition return/neutral cleanup and JUnit13. Those
batch-wide outcomes are attributed to master; this worker independently
inspected only the supplied Cold Denial images/oracle and source evidence.
Neither listening nor continuous 60fps certification is claimed.

Feedback edit checks: profile JSON parses; schema/weapon/framing/contacts are
unchanged, generator hash is unchanged, and modified profile/review have no
trailing whitespace. Only evidence/notes/documentation changed in the owned
profile/review. The profile input hash changes; master owns refreshing its
manifest provenance during integration. No pack materialization or full
regression rerun is needed for this documentation-only feedback delta.

## SECOND native review pending

Return this documented no-change candidate for master SECOND Vision using
the same hip, ADS and rear-magazine extraction/reseat/recovery scenario.
Recheck that the handling area remains visible despite the raised muzzle crop
and that the terminal pose restores hip. Retain the documented limitations;
SECOND Vision/final batch acceptance has not been reviewed by this worker.
The worker remains available for exact image-backed corrections.
