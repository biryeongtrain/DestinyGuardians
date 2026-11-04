# W220 Deafening Whisper — FIRST contact correction, SECOND pending

Owned files only:

- `scripts/generate_reload_w220_deafening_whisper.py`
- `art/weapons/w220/deafening_whisper/profile.json`
- `art/weapons/w220/deafening_whisper/review.md`

## Source and scope

Read the complete shared worker instructions, worktree AGENTS, global RTK,
weapon-art skill and Ace/Izanagi study. Read master's `source-review.json`,
`source-handling-evidence.json`, `source-selection-review.json`, scratch rig,
and viewed the actual `grenade_launcher_83c75a3c-80A8A136-upper-chain.png`.
Profile evidence records their SHA256 values. No independent Blender evaluation
is claimed. Master evaluated the original read-only ARMATURE in Blender5.4 Alpha.
Action `80A8A136`, OBSlot, frames1..89, 30fps, has61 evaluated upper-chain poses.
Both136 and126 were considered by master.136 is a shared class choice, not a
recovered per-weapon selector. LEFT is the loading hand; RIGHT is the carrier.
There is no source mesh, camera or finger IK.

This is a new route. There was no dedicated Deafening Whisper reload generator
or prior moving partition to preserve. Salvo was read for API/transform context;
its silhouette, pivot, geometry and phase knots were not copied. Existing sound,
gameplay timing, ammo and canonical model/item files are untouched.

## Authored mechanics

All88 canonical elements and every face UV are copied exactly into one exclusive
partition: fixed body16 and gun-attached fore-end72. Fixed: breech16..19,
receiver46/47, stock48..52, pistol56/57, trigger58/socket59, rear indicator87.
Hinged: barrel0..7, muzzle8..15, sleeves20..35, divider36..43, rail44 and rear
top plate45, foregrip53..55, complete laser/mount/cables60..70, counter/wrap
rails71..76, latch77 and complete sight78..86. The wraps, laser and tall open
sight therefore retain their relative positions throughout opening.

Hinge `[8,11.34,8.95]` uses the lower receiver height11.09..11.55 and front
fixed-breech plane8.95 of this weapon. Negative X rotation drops its -Z muzzle.
Opening reaches52 degrees at.25, holds until.50, then closes by.68. Unlock
holds0...10; recovery holds the closed mechanism.68..1. This is authored
calibration, not recovered hinge motion. Breech solids never detach and the
barrel never attaches to a palm. Existing solid breech simplification and its
intersection during the open arc require native inspection.

A reload-only short hex case plus shallow rim uses six meaningful solids and
existing neutral `front_grip_socket` face UVs. No new texture or decorative
fragment soup. It appears only samples17..28 (progress.283333...466667),
approaches along the open bore, seats by.46 and disappears inside the barrel
before closure. Its nominal case/rim radii are.72/.79, length2.76; these hidden
dimensions are authored. It is cosmetic and does not emit ammo events.

Only this `round` uses `policy=magazine`, to allow master source-left translation
attachment. Window `[.27,.30,.38,.46]` ramps on, holds, and releases completely
before the.50 close. Reload contact `[5.5,13.5,8.5]` is a virtual palm anchor
outside the case, calibrated to the actual fingerless hand volume. The initial
`[7.25,12.94,9.0]` case-surface contact put the case inside the palm volume;
the FIRST correction below addresses that concrete defect.
The right and left idle contact dictionaries are unchanged. No source-palm fit,
chain stretch, damping, support hiding or new camera offset is used. Generator
body displays stay canonical; master's full-chain replay supplies the source
weapon transform once. Full source wrist travel can expose a mismatch between
the remodeled chamber and the generic action: attachment-to-seating contact is
still subject to SECOND feedback, not claimed solved from bone sheets.

The profile was derived using current `first_person_framing_w205.load/profile`:
translation[-.65,.6,0], rotation[-1,2,0], scale.98, rightWristRoll28,
leftRotation[15,35,-35]. `sourceFullChain=true`, `keepMeshSupport=true`,
`hideSupportAtRest=false`. Master owns registering W220 in shared loaders.

## Pure generation and checks

API: `generate(root=ROOT, *, rig_path=None, profile_path=None)` returns absolute
Path-to-bytes mapping; no import/generate writes. Default rig is
`art/weapons/w220/rigs/grenade_launcher_83c75a3c.json`. Tested twice in memory
with `/private/tmp/destiny-w220-source/grenade_launcher_83c75a3c.json` override.
No generated resources were materialized in the worktree.

- PASS: write-guarded import and generate; deterministic identical bytes.
- PASS:371 exclusive output paths =370 pack JSONs +1 manifest;3 static parts,
  366 parent/display children (61poses x3parts x2grips),1 item graph.
- PASS:61 exact float32(i/60) thresholds, including exact canonical graphs at
  both endpoints; negative inactive and overshoot return canonical graphs.
- PASS: canonical ADS/inspect case precedence, nonFP graph and item extra keys
  preserved; every generated nonFP display unchanged in both carriers.
- PASS: exhaustive canonical88 partition/UV preservation and semantic index
  coverage; no breech element in hinged or round partition.
- PASS: every sample's hinge fixed under independent displayed-point evaluation,
  both FP contexts/native/twohand; barrel length remains19.75 times scale.
- PASS: fixed body displays remain canonical for all61 samples in both grips.
- PASS: all generated active references resolve within mapping, round referenced
  only at samples17..28, and no new shared/runtime path is emitted.
- PASS: invalid/nonfinite sample progress rejected;1001 curve samples finite and
  hinge bounded[-52,0]; finite-difference C1 knot slope gap0.00694 or less with
  step1e-6. PCHIP has zero tangents at endpoints, holds and extrema.
- PASS: active maximum16+72+6=94 weapon elements; with448 ordinary arm reserve,
  542. Parent-resolved current canonical graph maximum237 (an inherited older
  alternative) is conservatively counted too, giving685 total upper estimate,
  below1000. Full and split alternatives are not double counted. Master must
  measure actual materialized route/arms; `assembledBudgetVerified=false`.

Manifest records input hashes including current canonical alternatives,
generator/profile/rig, existing timing and reload-sound data; output hashes,
actual part counts, source provenance and pending native limitations.

## Master handoff

Ready correction candidate only. No whole-hands generation, Gradle, native gameplay,
Computer Use/Vision, live DCC, source mutations, children, commits or shared
loader/runtime edits. Review open-breech clearance, left round contact through
.28...46, release before.50 closure, foregrip return, tall sight clearance,
both FP contexts/carriers, ADS/inspect and inactive/endpoints.61 sampled poses
do not establish continuous native60fps interpolation.

## FIRST observations and concrete correction

Worker viewed both Deafening Whisper sheets, full-resolution native raw03..12
(including requested03/04/05/06/07/09/11 and adjacent08/10/12), post-recovery
sheet, and original source136 bone sheet again.04/05 expose the loading hand,
but case edges are not confidently distinguishable;06/07 cover the chamber.
09..12 show recovery without an exposed stray payload or displaced fixed
breech. Tall sight and stock remain coherent. Capture indices are bracketed
samples, not exact progress coordinates. These observations alone did not
justify extending the visibility window or changing the hinge.

Master's additional palm-volume question identified a concrete error. Read the
current main builder `display_at`, source-palm override, `rig_arms.apply`,
`reload_hand.attached_translation_shift`, and `skin_arm_models_w204` geometry.
Main/worktree skin builder and attachment helper are byte-identical; rig math
is unchanged apart from master's new rig registrations/action selectors.
The forearm is a real box envelope, not a point palm: classic bounds
X/Z6.8..9.2,Y1.5..9; slim X7.1..8.9 with the same Z/Y. Contact origin is8,8,8,
one local unit below the terminal hand cap. Source rest forearm length8.141365
gives existing Yscale1.252518 relative to the weapon scale. At full attachment,
the helper aligns the configured round contact to that internal origin. Using
the case's left surface as contact was therefore wrong for these fingerless
arms. At sampled full attachment poses18..22,24..28 of48 case/rim OBB corners
were inside the classic forearm; normalized separating-axis overlap confirmed
the intersection (not merely projected PNG occlusion).

Product delta: change only the cosmetic round virtual palm anchor from
`[7.25,12.94,9.0]` to `[5.5,13.5,8.5]` in generator/profile. This moves the
attached case to the exterior of the actual hand box without moving the hand.
Normalized separating-axis checks on every case/rim cuboid against the source-
oriented classic/slim forearm bound the full-attachment clearance.81 source
samples across.30...38 have minimum separation.03226 weapon model units for
both variants; maximum nearest classic separation.35074. This is a small
surface clearance, not a claim of recovered finger grip.

No case enlargement, UV change, round geometry change, hinge/partition change,
arm translation/rotation/length change, visibility extension, camera offset,
source action/time change or audio/gameplay change. Contact affects only the
bounded attachment translation; at zero weight by.46, the exact original
authored round seat/hinge-relative path is restored. The six-solid payload is
still referenced only samples17..28 and removed before closure.50..68.
Master must regenerate the hand/framing overlay from the changed profile;
unframed weapon pose JSONs themselves remain unchanged.

Post-correction pure checks PASS: write-guarded deterministic371 outputs,
61poses, revision2, canonical88 partition/UV and six-solid round unchanged,
all366 authored part/carrier displays identical under old/new contact values,
framing/idle grips/window unchanged, exact zero correction at.46 seat and all
later samples, payload references17..28 only, active94 and conservative685
element budget. No whole-hand generator or native QA was run by worker.

Required sequence: original Blender(done) ->61poses(done) ->master FIRST PNGs
(viewed) ->same-worker round-contact correction(done) ->master SECOND(pending).
Native exposed case contact and hidden round seating are not certified; SECOND
must review the corrected exposure/transition without changing source arms.
