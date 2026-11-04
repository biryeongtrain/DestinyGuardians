# W218 Stormchaser worker review

Status: FIRST actual images reviewed by the same worker; justified no-change to generator/profile. Review-only feedback returned for mandatory fresh SECOND. Visual acceptance remains pending SECOND.

## Owned delta

Only `scripts/generate_reload_w218_stormchaser.py`, `art/weapons/w218/stormchaser/profile.json`, and this review are worker-owned. No shared source installation, outputs, runtime, bindings, contacts, geometry/UV, gameplay, or audio edits. No commits/stash/reset/clean, Gradle or live-client runs. All commands use `rtk`; Python runs with `-B`. Preparation and tests live in `/private/tmp/w218-stormchaser-prepare`. Master confirmed seed exit0 and worker metadata `status=ready`, baseline174125 files, SHA256 `bc362206b9f315b4ea546bf9942a06a84f830758abaff32d7fe8b1f02b1fea1d`. Worker independently checked that marker before installing only the three owned files.

The new pure stdlib generator returns 248 absolute `Path:bytes` entries: two semantic parents, 244 display children (61 poses x two parts x native/twohand), one item definition and one manifest. Import and `generate(root=ROOT)` perform no writes or mkdir. No old generator or rendering dependency is imported/executed; W188 constants are read inertly using AST. Master must materialize the mapping.

## Source and authorship

Master evaluated original `/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return/clips/linear_fusion_rifle_d9d0adf4/blender/source.blend` in a separate Blender 5.4.0 Alpha background process. Worker read fresh `source-review.json` and rig bytes from `/private/tmp/destiny-w218-source`, and viewed the actual `linear_fusion_rifle_d9d0adf4-80A8ADE1-upper-chain.png`. Report: action `Armature|fp_80A8ADE1_reload_full|Base`, OBSlot, frames 1..96, 30fps, 61 evaluated samples; prior-cache joint error 0; all original inputs unchanged. Original blend SHA256 `55178575d1087e24fdc3d3e9ab2abd2e1d6451027834983ea05ef2f0dab92064`.

The report/rig are pinned at their new installation paths: `docs/qa/2026-10-28/w218/source/source-review.json` and `art/weapons/w218/rigs/linear_fusion_rifle_d9d0adf4.json`. No replacement of W205 rig bytes is expected. Source is shared-family ARMATURE motion, not exclusive Stormchaser mesh/camera/finger IK. Worker did not independently evaluate Blender.

Read main AGENTS.md, minecraft-weapon-art-design SKILL.md and references/ace-izanagi-study.md. Viewed actual retained W188 storyboard/comparison and read SOURCE.md/manifest. Ehroar n26872..27000 supports steep lift, complete grip-heel withdrawal, low exchange, long stem first insertion, neutral seat at .75 and rapid lowering. Original video was not reopened. Silver gameplay shader remains mechanism evidence; current canonical base-dye atlas is unchanged.

All 14 W188 authored knots, pivot `(8,8.26,8.015)`, battery anchor `(8,6.78,7.61)`, display rigid algebra, uniform scales, native-to-twohand carrier transport and left FP semantics remain. Canonical 95 elements/570 face UVs partition into 89 fixed elements and six original heel/crown solids80..85. Existing authored reload-only stem retains original pistol_grip76 rotation and UVs. Seven-element payload moves as one rigid assembly. No receiver/cage/loop/grip/guard boundary moves into payload. No new geometry relative to W188.

Interpolation changes only from independent segment smoothstops to shared C1 weighted harmonic PCHIP. Equal holds and extrema retain zero tangents, and exact authored knots remain exact. Translation holds `(-1.4,-1.2,-2.8)` from .22 through .75; payload offset is zero through .22 and from .75 onward. Both parts always dispatch, preserving W188; there is no inherited visibility/hide/zero-scale phase to remap. Thresholds are exact `float32(i/60)`. 61 poses/60 intervals is a return-count claim, not continuous native 60fps.

Profile retains the current effective linear-fusion family framing from the shared loader and canonical configuration, with `sourceFullChain=true`, `keepMeshSupport=true`, `hideSupportAtRest=false`. No mesh rest positions/rotations change. Reload explicitly selects action80A8ADE1, partHint/policy magazine and gripWindow `[.13,.22,.68,.75]`. Attachment fades through .68..75 and stays zero during wrist recovery after neutral seat; this avoids dragging a seated battery.

Canonical item guards keep exact native/twohand endpoints, ADS/inspect precedence, negative/inactive/overshoot and nonFP fallbacks. Current w46 timing metadata and w63 sound metadata confirm product49tick reload/5rounds/533ms charge/11charge ticks/3shot shared-ammo burst and existing49tick audio; all remain unchanged.

## Targeted checks

Command: `rtk proxy python3 -B /private/tmp/w218-stormchaser-prepare/check.py`.

Read-through in-memory overlay supplies only owned generator/profile and exact fresh W218 rig/report against main ROOT. No shared data copied into worker, no assets written to disk.

- Audit hook rejects file writes/mkdir/rename/remove during import and both generate calls: zero attempts; deterministic 248 entries, exact namespace and absolute Path/bytes types.
- Original 95 elements and all 570 face UV records preserved; exact89 fixed/six original heel/one same stem partition.
- Exact14 knots; 601 normalized samples stay inside scalar interval bounds; translation and payload holds remain exact; numerical shared derivative difference <=0.002635 at epsilon1e-7.
- All244 children checked in both FP hands/native/twohand: exact endpoints, unchanged scales/nonFP contexts, common battery/body rotation; relative rigid translation error <9.74e-10. All emitted rotations finite, no Euler representation flips; maximum adjacent component step15.71718 degrees.
- Exact61 float32 thresholds;432 resolved states across eight contexts, two grips, three modes and nine progress values confirm canonical ADS/inspect/context/fallback/endpoints and active two-part routing. Both parts stay visible; release by .75.
- Hash drift rejection for current geometry and dedicated fresh W218 rig/report; AST-identical11 W188 partition/rigid-math/stem functions.
- Reload96 +448 arm reserve =544; raw canonical245 +448 =693. These were pre-FIRST candidate estimates. Master subsequently measured all actual alternative routes including arms: Stormchaser maximum693 <=1000, fullChain=true, in `docs/qa/2026-10-28/w218/assembled-budgets.json`. Alternatives are not summed.

## FIRST actual image feedback — same-worker no-change

Master reported FIRST15/15 native sequences completed, wrappers stopped and inputs neutral. Worker read `vision1/native-validation.json`: Stormchaser fire22/reload31/ADS13 captures, released native input for each, final ammo5/20, one paid round for the shared-ammo burst, and dense server reload progress through .8833333. Runtime/mechanical validation is distinct from visual acceptance. Read `assembled-budgets.json`: actual Stormchaser all-route maximum including ordinary full-chain arms693/1000; batch maxima701/693/667/665/701. No generated manifest, profile or shared data was edited to relabel these master-owned results.

All paths below are under `/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-28/w218/`. Worker actually opened the two review sheets, all ten listed raw native PNGs, and the post-reload sheet with image viewing tools, rather than relying on the master's description. Also reopened `source/sheets/linear_fusion_rifle_d9d0adf4-80A8ADE1-upper-chain.png` and read the exact fresh source rig/report.

| Exact image file | Visible evidence and limits |
|---|---|
| `vision1/screenshots/stormchaser-review.png` | Hip keeps the recognizable silver/red-black cage/loop and both skin arms visible. ADS has a centered visible sight line; sleeves sit below the sight in this capture. Reload panel is sample09. One ADS view does not certify every sway angle or both runtime grip variants. |
| `vision1/screenshots/stormchaser-reload.png` | Labeled samples01/05/09/13/17 show lift, steep exchange and lowering/regrip. Sheet sampling is sparse, not continuous interpolation evidence. |
| `vision1/frames/w218-stormchaser-reload-sample-01.png` | Early lift; left support at fore-end and right grip retained. Lower stock/palm partly crosses the viewport edge. |
| `vision1/frames/w218-stormchaser-reload-sample-05.png` | Steep muzzle-up presentation; muzzle and long upper cage remain inside the image. Right arm retains the carrier. Left handling arm/payload are mostly below the lower edge, so this cannot prove extraction clearance. |
| `vision1/frames/w218-stormchaser-reload-sample-09.png` | Left arm comes from lower left toward the heel/exchange area, with a narrow black battery/stem silhouette beside its palm. Right hand remains on the grip. Palm and projection conceal the exact contact surface; visible approach is not exact grasp/finger proof. |
| `vision1/frames/w218-stormchaser-reload-sample-10.png` | Left palm closes against the weapon near the battery/heel region. Both palms and dark geometry overlap; the complete battery-to-palm boundary is not exposed. No clear floating part is demonstrated. |
| `vision1/frames/w218-stormchaser-reload-sample-12.png` | Left arm is back toward the forward support position as the weapon lowers; lower heel region is partly off-screen. This is not a clean view of neutral battery seating. |
| `vision1/frames/w218-stormchaser-reload-sample-13.png` | Left palm already lies along the fore-end during recovery, rather than visibly grasping the heel. The front support position is visible; exact battery seat/contact is occluded. Do not identify this frame as an unambiguous battery approach merely from its capture number. |
| `vision1/frames/w218-stormchaser-reload-sample-14.png` | Lowering continues with left fore-end support and right grip; no clearly separated payload visible. Heel/hand overlap limits clearance judgment. |
| `vision1/frames/w218-stormchaser-reload-sample-15.png` | Later recovery with support hand at fore-end. No visible payload following that hand away from the gun; heel is partly cropped, so hidden clearance is unproven. |
| `vision1/frames/w218-stormchaser-reload-sample-16.png` | Recovery grip persists; no obvious late detached battery or wrist-driven payload trail. The obscured lower region prevents an exhaustive geometric contact claim. |
| `vision1/frames/w218-stormchaser-reload-sample-18.png` | Main canonical hand route has returned; HUD5/20 and supported weapon visible. This is sampled endpoint recovery, not proof of every earlier frame. |
| `first-post-reload-review.png` | Stormchaser panel returns to ordinary hip with two skin arms and HUD5/20; no obvious displaced loose battery. Other weapons in this combined sheet are not worker acceptance scope. |

Capture suffixes are chronological PNG indices, not `i/60` asset-pose indices. Read `vision1/sequences/w218-stormchaser-reload.json`: selected PNG before/after client ticks, relative to operation start1024, are01=3/3,05=13/13,09=22/23,10=25/26,12=30/31,13=33/33,14=35/36,15=38/40,16=41/43,18=48/50. The49tick reload and capture latency mean the pictures alone cannot label the exact .75 crossing. In particular sample13 is earlier than sample15, not pose13/60 or an asserted .75 seat. Exact release is audited separately below.

### Source handling hand is LEFT

Authoritative action remains `80A8ADE1` / `Armature|fp_80A8ADE1_reload_full|Base`, group `linear_fusion_rifle_d9d0adf4`, original range1..96. Read original bone-map.json via the pinned report source path: `DE9D6BEA` is explicitly `b_r_hand`, with right arm hierarchy22->20->17 (`b_r_upperarm`); the opposite wrist `8C83CB67` maps to leftWrist in the freshly evaluated report/rig, hierarchy21->19->15. Its raw semanticName is hashed, not a fabricated `b_l_hand` label.

Across all61 source samples, measured weapon-relative wrist position using `R_weapon^T * (wrist_translation - weapon_translation)`, compared with progress0. LEFT maximum excursion0.6519643749081154 source armature units at progress19/60; RIGHT maximum excursion0.000002969443302137062 at progress1/60. Right wrist remains weapon-fixed to source numerical tolerance while the left wrist makes the large exchange excursion. This confirms LEFT as the handling hand for this source action; no global claim about every other source group. The reopened bone-only sheet agrees with the different chain excursions. It does not expose a source battery mesh, camera or fingers.

The native frames' moving arm comes from lower left; right carrier grip stays with the weapon. Keep the existing magazine route's LEFT default. No right-hand override or source-action change is justified for Stormchaser.

### Neutral seat/release and decision

Rechecked owned generator/profile and read current master shared consumer without editing it. Profile remains gripWindow `[.13,.22,.68,.75]`. `build_first_person_hands_w201.py` computes the clamped smooth attachment envelope, and `reload_hand_w218.attached_translation_shift()` multiplies the selected palm-to-part displacement by that weight. At progress>=.75 the envelope is exactly zero. Every remaining authored battery-offset knot from .75 through1 is `(0,0,0)`; equal-channel PCHIP holds it identically zero. Thus the authored payload is body-fixed after neutral seat, and shared attachment cannot carry it along with the recovering wrist. This is code/curve evidence, not a claim that the partly hidden seat is visibly measurable in the supplied PNGs.

FIRST images show complete sampled lift/exchange/recovery, an on-screen muzzle at steep lift, readable hip/ADS, and no obvious post-seat payload dragging in samples15/16/18 or the post-reload panel. They do not demonstrate a wrong handling side, wrong action, Euler flip, torn component, late loose battery, or framing defect requiring an owned product correction. Left palm/heel/stem overlap and bottom-edge cropping prevent certifying exact continuous battery contact, finger clearance or all hidden stem surfaces. The original shared-family arm motion and independently authored battery path remain distinct evidence sources; their exact weapon-specific timing/contact is not recovered mesh animation.

Decision: justified no-change to generator/profile; only this review updated. Unchanged generator SHA256 `ec3e35094f348f5893a7091031f2f3b2d395a9de8b4b33a1b17e27d889a3dcfa`; unchanged profile SHA256 `bb6e80569907766d28586b8952a7e921e442c819c2d5bcb03ef95881854e926b`. No formal product revision, shared writes, generated assets, live inputs, standalone Gradle or repeated product test suite. Hash/syntax and static release checks passed; prior targeted checks remain applicable.

SECOND must be a fresh master native review before visual acceptance. Revisit heel/palm contact near .68..75 and first recovery beyond .75, compare LEFT across this source group, confirm no post-seat dragging and preserved centered ADS/hip. Supplied FIRST stills do not certify inspect, mirrored FP hand/native grip alternatives, all cancellation/equip paths, auditory quality or continuous60fps rendering. Master retains native/CU lease, integration, final acceptance and cleanup ownership. SECOND has not been performed by this worker and no final native visual acceptance is claimed.

### Viewed evidence hashes

- `vision1/screenshots/stormchaser-reload.png` SHA256 `59407f4822f96bb13f9488d2b37f5862da668c5996d3a38c2ffd9fa6da501550`
- `vision1/screenshots/stormchaser-review.png` SHA256 `a56002630ab9c9ef443cbeaf174f36c6fd8560d68663269aef6cad63068a6661`
- `vision1/frames/w218-stormchaser-reload-sample-01.png` SHA256 `43cbe8a63327c730fe89bc1f3659bfff751587e82cc0bfc14538fdb040b82c16`
- `vision1/frames/w218-stormchaser-reload-sample-05.png` SHA256 `a2d555eac2a82a9b265ec03f54ae39e9341e4dd9c91fbdc65d007ef1b8169884`
- `vision1/frames/w218-stormchaser-reload-sample-09.png` SHA256 `5eafd63d09f76873fa59c6c701a457623f781b572a3f9a9347bb00c0cde54b0e`
- `vision1/frames/w218-stormchaser-reload-sample-10.png` SHA256 `2cf134178f1377385de0866c93a7d2efdd69f8955944ef802b076d89c4f52841`
- `vision1/frames/w218-stormchaser-reload-sample-12.png` SHA256 `9f4d6731675859ee69aa699abe2fa830f8d1e6e6e1885435c5db6575b7b6753b`
- `vision1/frames/w218-stormchaser-reload-sample-13.png` SHA256 `cee5d8af8c707f5e56c010dbad58a4171c1168b3b0b41f787803c2e3b095a9bf`
- `vision1/frames/w218-stormchaser-reload-sample-14.png` SHA256 `abdfd768f18fa80f339f5bf894264990ef9cb47c0f0556e0cce3f772eea7e506`
- `vision1/frames/w218-stormchaser-reload-sample-15.png` SHA256 `976c9cbf0603bfba59313e368d75ae0ba48e02a8ec92f4a7fb7eaa49bddab648`
- `vision1/frames/w218-stormchaser-reload-sample-16.png` SHA256 `943c0ae901e8368570861e75305509dfc05275c1c75af6ba5ea231050451c9ea`
- `vision1/frames/w218-stormchaser-reload-sample-18.png` SHA256 `23386f5a11d65694b20e720e7a512962e4258136eaf3ae541e252c8ca9f12e4c`
- `first-post-reload-review.png` SHA256 `66ac853208a47161327067955b7fdc9699a09b793dca28d71aa40134cb17afcb`
