# W221 Pyroclastic Flow candidate

Status: READY baseline marker and expected baseline hash verified; exact three normalized draft files transferred into assigned worktree. In-memory pure validation passed there; no generated assets materialized. FIRST native evidence reviewed by the same worker; justified no-change returned. SECOND Vision and batch acceptance remain pending. Retain this worktree as a fixed reusable slot per latest user instruction.

Owned paths (only):
- `scripts/generate_reload_w221_pyroclastic_flow.py`
- `art/weapons/w221/pyroclastic_flow/profile.json`
- `art/weapons/w221/pyroclastic_flow/review.md`

## Original source and retained geometry

Master evaluated original `rocket_launcher_1a221f25/source.blend` read-only in separate Blender 5.4 Alpha: action `Armature|fp_80A8A1A2_reload_full|Base`, OBSlot, frames1..113 at30fps,61 samples, prior-cache joint error0, all inputs unchanged. Worker read full source-review and handling evidence and viewed the actual six-pose XZ/YZ upper-chain sheet. Worker did not independently evaluate Blender. Durable master evidence: `docs/qa/2026-10-28/w221/source-review.json`, `docs/qa/2026-10-28/w221/source-handling-evidence.json`, and `docs/qa/2026-10-28/w221/source-sheets/rocket_launcher_1a221f25-80A8A1A2-upper-chain.png`. Fresh rig: `art/weapons/w221/rigs/rocket_launcher_1a221f25.json`. Scratch source files used for draft checks are temporary inputs, not durable evidence locations. Source is ARMATURE only: no weapon mesh, camera, finger IK, or recovered weapon-exclusive selector claim.

The W150 effective canonical model contains106 meaningful solids. Preserve all original geometry and face UV exactly across103 fixed elements, two socket-closure elements and one latch. `launch_tube_0..7`, the complete `receiver_core`, `receiver_cradle`, cowling, armor and optics remain together. Source weapon-bone replay belongs to master; the generator authors no body sweep or camera correction.

There is no named detachable rocket in the actual canonical element list. Rather than moving a receiver/tube and calling it a projectile, add eight reload-only connected solids: two intersecting shaft prisms, two nose prisms, two collar prisms and two fins. Existing opaque material face UVs from launch tube, optic bracket, receiver band and barrel fins are retained as templates. The narrower nose leads along model -Z, matching the launch tube. This is an authored approximation, not recovered rocket geometry or original texture mapping.

## Mechanical behavior

Four separately parented parts: body103, magazine8, cradle2, lever1. `rear_socket_floor`/`rear_socket_lip` rotate42 degrees about existing `rear_hinge` center[8,9.4,16.43]; `rear_latch` unlocks24 degrees about[8,9.55,16.9]. The actual receiver remains intact. Authored latch unlock.00..08, socket opening.08..18, handling.18..66, axial seat.66..72, projectile hidden after seating.72..76, closure.76..84 and latch lock.84..89. These mechanical times are inferred from geometry/source phase, not extracted event tracks.

Profile selects LEFT source handling hand, explicit action80A8A1A2, `policy=magazine`, `partHint=magazine`, gripWindow[.18,.28,.56,.66]. Shared selected-hand attachment translates only projectile toward unchanged source palm. Full release by.66 precedes neutral seat.72 and closure.76, preventing wrist recovery from dragging the seated assembly. Preserve existing W201 idle right/left contacts. Reload-only contact[8,11.7,14.8] is the projectile anchor, replacing the old approximate static loading-port target.

Use current effective default framing translation/rotation0, scale1, rightWristRoll15; add sourceFullChain=true, keepMeshSupport=true, hideSupportAtRest=false and sourceViewRotation[0,0,0]. No limb shortening, axis attenuation, source palm fitting or camera shift. Ordinary arm geometry/length and actual assembled count remain master integration responsibilities.

## Pure checks performed

Stdlib generator import and two `generate(root, rig_path=..., profile_path=...)` calls ran with Path.write_bytes/write_text/mkdir rejected; deterministic494 absolute Path->bytes outputs returned only in exact weapon-specific model/item namespace plus its art manifest. No generated asset files written. Original Blender61 cache used via rig_path for draft validation. Worktree validation used the temporary original source61 cache override; durable rig installation remains with master.

-61 poses/60 intervals, native/twohand banks, both first-person contexts.
-Exact float32(i/60) threshold encoding and every grid boundary selected expected entry.
-Canonical item graph retained for nonFP, inactive fallback, endpoints0/1, ADS and inspect; ADS/inspect guard precedes reload dispatch. Overshoot clamps to canonical final entry.
-Canonical106-element geometry/UV partition equality; fixed body display unchanged at every pose/grip; nonFP displays unchanged in every child.
-Dense PCHIP channel sampling stayed in knot bounds; endpoint/hold/extremum tangents zero. Shared derivatives give C1; numerical one-sided derivative mismatch at epsilon1e-7 at most0.002880 in highest-speed degree channel.
-Explicit attachment release.66 before neutral seat.72, no projectile visibility after.76.

494 returned files comprise4 static geometry parents,488 pose/grip/part display children,1 item graph and1 manifest. Reload114+448 conservative ordinary-arm reserve=562. Raw legacy canonical228+448=676; selected W150 canonical106+448=554. These are conservative estimates, not actual assembled counts; master must measure all routes including ADS/inspect under1000.

## FIRST feedback review — no implementation change

Same worker actually viewed the Pyroclastic hip/ADS/reload review sheet, reload contact sheet, raw reload samples12/14/16/18, the batch post-reload sheet, and the original six-pose upper-chain sheet. Read the durable source-review again: OBSlot action80A8A1A2, original1..113,61 samples, error0, ARMATURE only, inputs unchanged. Installed main W221 rig SHA matches the fresh source61 hash pinned by this profile. This remains master's original Blender evaluation, not an independent worker Blender run.

Observed in raw12: visible gold/purple projectile cap at the LEFT palm and the rear closure open, with the main launcher/receiver intact. The projectile is partly obscured by the fingerless palm; the visible overlap does not establish exact grasp or a recovered carry orientation. Raw14 shows the empty left hand separated while a dark/gold projectile section remains toward the rear opening; raw16 retains an open/closing socket while that hand recovers. Raw18 lowers the launcher near the frame edge, so it cannot prove the entire final closure. No sampled image establishes a duplicated receiver, detached closure pivot, reversed insertion axis, or seated part following the returning wrist. Post-reload Pyroclastic panel shows the launcher returned to the hip presentation, HUD1/6, with no separate rocket left at the hand. The ADS ring is centered with a visible aperture; the large body occupies the left screen. No camera correction is justified by that canonical composition.

Pure mechanical recheck of all61 poses, both grips and both FP contexts: finite displays and orthonormal rotations; projectile authored offset is Z-only and nose leads -Z along tube. At.56 attachment weight1; at.60=.648 and.64=.104; attachment is0 from.66 onward. At.66 the axial offset is3 with zero tilt; it reaches0 at.72 and remains0. Projectile visibility is1 through.72, .5 at.74 and0 at.76. Socket stays42deg open through.76, closes to21deg at.80 and0 at.84; latch locks to0 by.89. These PCHIP holds and release ordering support keeping the existing code. Shared attachment moves only the projectile to the selected source palm and does not justify moving the original hand or introducing a camera fit. Source bone sheet confirms substantial left-chain excursion and late recovery, without mesh/finger/camera evidence for an exact carry plane.

Decision: justified no-change to generator/profile. Existing -8..0deg projectile carry tilt and closure pivots remain authored approximations; the samples do not support a specific replacement value. Only this review.md changed in response to FIRST. Master reports18/18 native sequences, authoritative paid shotgun interrupts and neutral cleanup. Read native-validation.json: Pyroclastic fire/reload/ADS released input, finished ammo1/6, one paid firing round, neutralAfter=true. These runtime results are distinct from mechanical visual acceptance.

Viewed evidence (durable main paths, recorded here without editing main):

- `docs/qa/2026-10-28/w221/vision1/screenshots/pyroclastic_flow-review.png` — SHA256 `8c05164303c4ffcff1713ca9b94ed009def3124adf51a7fef905d22c2ad0b09f`
- `docs/qa/2026-10-28/w221/vision1/screenshots/pyroclastic_flow-reload.png` — SHA256 `0896c5f89b0166b31576a88f0d5a996fb1607a061adf6aa099b49765c5a37067`
- `docs/qa/2026-10-28/w221/vision1/frames/w221-pyroclastic_flow-reload-sample-12.png` — SHA256 `7500b06b0659e7e51b4dd6aa9525fcb942a8d794db113a0284b10c8bdf9329f2`
- `docs/qa/2026-10-28/w221/vision1/frames/w221-pyroclastic_flow-reload-sample-14.png` — SHA256 `c953bdbb289a7cf168ec7974ccfc04b11d3890b07dff6df3d106fa7f4278c755`
- `docs/qa/2026-10-28/w221/vision1/frames/w221-pyroclastic_flow-reload-sample-16.png` — SHA256 `6918a8e761806a8f47a0e03c0b8b301464179f3fb01b1489931b3cef91107753`
- `docs/qa/2026-10-28/w221/vision1/frames/w221-pyroclastic_flow-reload-sample-18.png` — SHA256 `13f22386a647e0708b17cac424399ae43847ce0969f9384a56e3b718b3363a06`
- `docs/qa/2026-10-28/w221/first-post-reload-review.png` — SHA256 `77107b1e8a5e6a8567494282dfcdd760805e16de8e5ba327383128eee478f97f`
- `docs/qa/2026-10-28/w221/source-sheets/rocket_launcher_1a221f25-80A8A1A2-upper-chain.png` — SHA256 `5c050f9b1fc0d2fe80fe71b5aa7c384cd8212d6bcbcae9020b4f59e337adfae0`

## Remaining validation

SECOND master Vision remains pending. Inspect the LEFT-hand carry/release/seat and socket closure across.56..89, including intervals between the sampled frames; retain source hand motion and canonical camera. Exact mesh contact, carry-plane alignment, projectile/socket clearance and continuous seat/closure are not certified by the available samples. Near-frame-edge recovery limits closure visibility; the post-reload sheet establishes returned hip/HUD state, not continuous trajectory correctness. No recovered fingers/IK/camera or continuous60fps claim. The worktree's shared/generated inputs remain its seeded baseline; master owns integration, actual assembled counts, materialization, game operation and final acceptance. No fullhands generation, Gradle, game control, generated/shared/main edits or commits performed by worker. Retain this fixed worktree slot; master owns any commit after accepted batch.
