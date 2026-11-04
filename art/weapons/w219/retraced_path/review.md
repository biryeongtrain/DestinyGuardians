# W219 Retraced Path — prepared product delta, native review pending

## Ownership and state

Exactly three product files belong to this worker:

- `scripts/generate_reload_w219_retraced_path.py`
- `art/weapons/w219/retraced_path/profile.json`
- `art/weapons/w219/retraced_path/review.md`

Prepared under `/private/tmp/w219-retraced_path-prepare` while main is read-only. The eventual exclusive worktree is `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w219-retraced_path`. No worktree writes before explicit master READY. This initial review records preparation; installation status is reported separately when authorized.

Master owns shared loaders, Java routing/lifecycle, source rig installation, generated resources, builds and all Computer Use/Vision. No shared generator, client, server or full audit was run. Main was not reset, stashed, committed, cleaned or pushed. No child worker was created.

## Original Blender evidence reviewed before generation

Master evaluated the original `/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return/clips/trace_rifle_1c48cd94/blender/source.blend` read-only in a separate Blender5.4.0 Alpha background process. Worker read `/private/tmp/destiny-w219-source/source-review.json` and actually viewed `/private/tmp/destiny-w219-source/sheets/trace_rifle_1c48cd94-80A8A43C-upper-chain.png`; worker did not independently open Blender.

Report: group `trace_rifle_1c48cd94`; only `Armature`/ARMATURE; action `Armature|fp_80A8A43C_reload_full|Base`; slot `OBSlot`; source frames1..106 at30fps;61 evaluated samples; old cached joint max absolute error0; all source inputs unchanged. Original blend SHA256 `a5da0626bcfde6cb9a5c3decb694fd7e870ba7824067cab2c3dbe5191ccb5339`.

Fresh source data `/private/tmp/destiny-w219-source/trace_rifle_1c48cd94.json` contains weapon and both shoulder/elbow/wrist chains. Master installs it at `art/weapons/w219/rigs/trace_rifle_1c48cd94.json`. Generator prefers the installed rig/report, with scratch read-only fallbacks for authorized preparation. No source rig is written by this worker. Existing shared inputs are read dynamically and recorded in each generated manifest, with no old shared-file hash pin.

Viewed bone sheet shows the large support-arm excursion and return, with right wrist following weapon. Role recheck from61 fresh samples: maximum weapon-relative left-wrist displacement0.843656462985 armature units; right0.000000572547. Existing contact evidence also explicitly calls reload a LEFT-hand target. Hence profile `contacts.reload.hand="left"`; actual emitted part hint is `moving`, policy `magazine`, rig action `80A8A43C`.

Source contains no weapon mesh, camera, fingers or finger IK. Its chain projections cannot prove pack contact, camera placement, sight clearance or native success. Ordinary fingerless player-skin full arms must be attached by master without arm length stretch, axis damping or hidden support substitutions.

## Same-weapon authored geometry and motion

Read the weapon art design skill and its Ace/Izanagi study. Viewed actual retained `art/weapons/w170/retraced_path/storyboard.png` and `comparison.png`. The storyboard retains12 gameplay frames from Y8qyeBBXBgA at247.15..248.85 seconds: dip, raised side roll, left underside access, partly concealed exchange, base press and return. Video was not reopened. Original source action and this same-weapon authored pack track are distinct evidence.

Preserved all10 W170 authored knots exactly, including independent constant channel holds. The extraction vector remains `[0,-4.5,1.035714286]` throughout `.35..51`; pack remains seated from `.70` through recovery. Preserve pistol-grip pivot `[8,9.145,9.61]` and insertion anchor `[8,9.12,3.55]`. Complete four-element pack indices78..81 retains `magazine_well`, `magazine_foot`, `magazine_blue_edge_-1`, `magazine_blue_edge_1`. All95 other elements, fixed casing/rails/housing and24 circular-disc solids retain their geometry and face UV. Pack stays visible at constant scale throughout; no duplicate, shell, fusion geometry or fusion animation is borrowed.

Only interpolation changes:61 samples/60 intervals with exact float32(i/60) dispatch thresholds, C1 weighted harmonic PCHIP and shared derivatives; zero endpoint, hold and extremum tangents. Preserve rigid local part math, native/twohand carriers and both first-person hand contexts. This is a discrete pose bank, not evidence of native continuous60fps interpolation.

Profile preserves effective trace-rifle offsets: translation `[-.65,.6,0]`, rotation `[-1,2,0]`, scale `.98`, right wrist roll28, left rotation `[15,35,-35]`. It enables `sourceFullChain:true`, `keepMeshSupport:true`, `hideSupportAtRest:false`. Existing right/left contact points and rotations, reload contact `[7.25,6.9,4]` and rotation `[13,0,0]` are retained.

Grip window `[.09,.23,.76,.84]` is authored: reach while raising `.09..23`, handle through extraction/exchange/insertion and the base-press peak `.23..76`, release `.76..84` before recovery begins. It follows existing W170 phases and visible left-hand access, not recovered finger contact or source event timing. FIRST native review may require correction.

## Output contract and bounded checks

`generate(root=ROOT)` uses only stdlib, returns absolute `Path -> bytes`, and never writes. In-memory output consists only of `src/main/resources/assets/destiny/models/weapon_reload_w219_retraced_path/`, `src/main/resources/assets/destiny/items/weapon_reload_w219_retraced_path/retraced_path.json`, and `art/weapons/w219/retraced_path/manifest.json`. There are248 returned files:2 static part models,244 parent/display children,1 item and1 manifest;247 pack files. Worker has not materialized any generated output.

Pass: syntax compilation; audit-hook rejection of writes during import and two generation calls; deterministic byte equality; exact output ownership/count; all61 float32 thresholds; canonical graph equality at0/1, negative inactive, overshoot and non-FP; ADS/inspect branches preserved; both hand contexts and native/twohand carriers; exact authored knots/holds, finite transforms, constant scales, unchanged geometry/UV and endpoint displays; bounded C1 derivative check across interior knots.

Budget measured from current canonical graph with inherited model elements and alternative selection: reload95+4=99; canonical maximum222; four classic arm surfaces reserve448. Reload with arms547; maximum alternative with arms670 <=1000. Full versus split representations are not summed. Final master-generated composed route measurement remains pending; no native performance certification.

No ammo, capacity, damage, cadence, reload clock, speed effect, perk or sound file is edited. Their current values remain unchanged. No new gameplay duration is inferred from source frames or the gameplay reference window.

## Mandatory remaining review

1. Master integrates only these three paths, installs original rig/action and shared loader/routing support, materializes generated output, and captures FIRST native images.
2. Return those actual images and exact problematic phases to this same worker. Worker views images and makes a justified correction or records evidence-backed no-change; no cosmetic change merely to satisfy a loop.
3. Master integrates the reviewed delta and captures SECOND using the same scenario. Only then may master evaluate final native acceptance.

Pending native checks: ordinary full-arm lengths/skin surfaces and original-action loading; left palm vs whole pack contact through extraction/reseat/release; fixed disc/housing integrity; both first-person hands and native/twohand; rest/ADS/inspect visibility; canonical inactive/non-FP/endpoints; reload cancel/complete/equip restore; final route budget and brief10..20 display observation. FIRST images have not yet been provided, FIRST has not been reviewed, SECOND is unverified, and this return is not final native acceptance.


## FIRST same-worker review — concrete pack-seating correction

This section supersedes the initial pending-FIRST status and initial `.76..84` grip-release rationale above. Worker viewed both actual FIRST sheets `docs/qa/2026-10-28/w219/vision1/screenshots/retraced_path-review.png` and `retraced_path-reload.png`, and the28 underlying `frames/w219-retraced_path-reload-sample-00.png` through `27.png`. Focused inspection used06..11 around return/insertion/recovery;13..27 show stable completed HIP. Read the corresponding reload sequence, server reload timeline and native-validation row. No new native inputs or client run were performed.

Observed intact housing, rails and fixed discs; clear rectangular sight in the ADS sheet; dark complete pack follows left hand in the detached interval; no obvious arm-stretch or extra-cell mesh in the reviewed frames. Fine seating clearance is partly occluded. Selected screenshots alone do not establish an unambiguous second pull-out, so this correction is grounded in the actual emitted transforms as well as the reviewed images, not an invented visible pop.

Concrete defect: the final assembled FIRST graph still applies source-left-palm attachment after the W170 seated knot `.70`. Own generator's moving offset is exactly zero from `.70` onward, but shared `attached_translation_shift` adds `(sourcePalm - reloadContactTarget) * gripWeight` to the whole pack. Existing window `[.09,.23,.76,.84]` keeps full weight through `.76`. Resolving the actual generated body's and moving pack's final display translations gives separation magnitudes4.753539 at grid42/p~.70,4.740136 at45/.75,2.369864 at48/.80 and0.093259 at50/~.8333, reaching0 at51/.85. Both FP hand contexts and both grip branches agree. These are display-translation units; there is no claimed world-space or screen-pixel measurement. Rotation/scale match the body at the seat, so the nonzero translations are unwanted cell displacement, not its authored insertion offset.

Owned functional correction: change only `GRIP_WINDOW` and the matching profile window to `[.09,.23,.62,.70]`, updating its explanatory limitation. Reach/contact before `.62` stays identical. Existing smooth release now spans final insertion `.62..70`; source-hand movement cannot drag the seated pack after `.70`. The exact W17010 knots/holds, geometry/UV, whole4-element pack, anchors, source action/full-arm chain, rest/ADS framing, clocks, ammunition and audio remain unchanged. No metadata-only generator/profile acceptance fields were edited.

Bounded local checks passed: syntax, write-rejecting import/generate,248 returned outputs, all247 own pack outputs byte-identical to FIRST, and unchanged keys/pivots/partition. Exercised the current shared attachment helper read-only with the new weight at `.70`, float32(.70),`.75`,`.80`,`.8333`,`.85` and1: pack shift is zero to emitted8-decimal precision; pre-release handling samples remain identical. No shared generation, generated output materialization, Gradle or native run. Only the same three owned worktree files changed.

FIRST server record:42-tick reload, dense progress includes `.70` and`.85`, then canonical inactive `-1`; actual ammo transitions0/150 to94/56. This is supporting master-owned FIRST evidence, not a changed runtime policy.

Master must integrate the three owned paths, regenerate the affected arm/weapon composition, and perform fresh SECOND. Check the seat/handoff at `.62..70`, stable pack-to-housing seam throughout `.70..84`, and source left-hand return without a new snap or floating pack. SECOND and final native acceptance remain pending.
