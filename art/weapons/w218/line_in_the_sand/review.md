# W218 Line in the Sand — worker product review

Status: FIRST actual images reviewed by the same worker; product nochange justified below. Fresh master SECOND remains mandatory before visual acceptance.

## Source reviewed before authoring

Read main AGENTS.md, RTK.md, minecraft-weapon-art-design/SKILL.md and references/ace-izanagi-study.md. No CodeGraph index exists in main. The user requires existing W188 geometry and UV, so the study informs semantic part preservation rather than a new surface redesign.

Master evaluated the original `/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return/clips/fusion_rifle_04669cdb/blender/source.blend` in separate Blender5.4.0 Alpha background. Worker read the fresh report and evaluated JSON; worker did not reopen Blender. Report: ARMATURE only, `Armature|fp_80A8ADD3_reload_full|Base`, `OBSlot`, frames1..100 at30fps,61 samples, existing joint-matrix error0, all inputs unchanged. Original Blend SHA256 `cdf955feedf818492dd395a2866beb19ed11bb35944544c05c3cd4eb00eeee36`.

Fresh inputs expected at `art/weapons/w218/rigs/fusion_rifle_04669cdb.json` SHA256 `f2ecda5b6b4595443f313fda97f2536856bd85d7cbb47fa3544f0e5ab5d35929` and `docs/qa/2026-10-28/w218/source/source-review.json` SHA256 `f5a06a8373aa9ee1328f0d2b14c87dc187367edc7e28224f7bfa6287d64469d0`. The dedicated W218 rig is required; no expectation that master will overwrite W205.

Viewed actual `/private/tmp/destiny-w218-source/sheets/fusion_rifle_04669cdb-80A8ADD3-upper-chain.png` (p0,.2,.4,.6,.8,1; XZ/YZ bone-only views) and retained W188 `storyboard.png` / `comparison.png`. The former shows original shoulder/elbow/wrist movement through the exchange and recovery, without weapon mesh or camera. The latter includes16 retained actual same-weapon frames: Plasma Alchemist `hu_LOERnF6o`, n3365..3417,134.60..136.68s,25fps. Viewed inventory identification, steep rise, whole lower battery withdrawal, below-frame exchange, upward insertion/seat and lowering. The source mint shader and perk capacity9 are excluded. Original video and historical FBX were not reopened; their provenance remains historical.

## Owned product delta

Only `scripts/generate_reload_w218_line_in_the_sand.py`, `art/weapons/w218/line_in_the_sand/profile.json`, and this review are worker-owned. No shared loader/runtime/bindings/generated outputs are written by worker.

The generator is pure stdlib and importable. `generate(root=ROOT)` performs reads only and returns absolute `Path:bytes` for246 models (2 parents +244 display children),1 item graph and1 manifest:248 JSON outputs. It parses W188 constants inertly with AST and never imports/executes the old generator or rendering dependencies. Current working input hashes are pinned afresh, rather than trusting historical W188 PINS. Shared loader/config/contacts are hashed in the returned manifest without claiming worker ownership.

All13 W188 knots, grip pivot `[8,8.2,8.2]`, magazine anchor `[8,5.6,6.83]`, authored holds/seat compression and rigid native/twohand transport remain intact. C1 weighted harmonic PCHIP replaces per-segment smoothstops, using a shared derivative at every knot and zero slopes at endpoints, equal holds and extrema. Thresholds are exact `float32(i/60)` for61 poses/60 intervals. This does not claim continuous native60fps interpolation.

The body remains71 fixed elements; all8 canonical battery elements56..63 move together with the same2 small metallic contact shoes. All79 canonical elements,474 face UVs, rotations and atlas are retained exactly. No new geometry or shrinking. W188 omitted dispatch poses8..11, so normalized `[.40,.60)` is hidden: dense poses24..35. It is not an index7 cutoff on the new bank. Exact canonical graph returns at0/1 and inactive/nonFP/overshoot; original ADS/inspect cases precede reload and both grip routes remain.

Explicit profile retains effective linear-fusion family framing: translation `[-.65,.6,0]`, rotation `[-1,2,0]`, scale `.98`, rightWristRoll28, leftRotation `[15,35,-35]`. Adds `sourceFullChain=true`, `keepMeshSupport=true`, `hideSupportAtRest=false`. Rest contact positions/rotations remain unchanged. Reload explicitly selects rigAction80A8ADD3, partHint/policy magazine and gripWindow `[.10,.20,.80,.84]`: attach after reach, fade after authored upward compression, release completely by neutral seat `.84`, stay released through wrist recovery. No arm-axis/length compensation or new camera fit is introduced. Master integrates original ordinary fingerless player-skin full chains.

Reload81 +448 reserved arm elements =529. Current raw canonical253 +448 =701. Both estimates satisfy1000 and are alternatives, not summed. Master must measure every actual route including canonical/ADS/inspect and any adapter output; `assembledBudgetVerified=false` and measured routes remain null until that work. Low count alone does not establish visual or performance acceptance.

Gameplay/ammo/audio are unchanged: existing capacity5,49tick reload,11tick charge,19tick cadence,burst1/sharedBurstAmmo. Pinned timing/audio inputs and no gameplay outputs support this preservation; actual audio listening remains master QA.

## Worker checks

Ran `rtk proxy python3 -B /private/tmp/w218-line_in_the_sand-prepare/check.py` using read-through in-memory overlay of the fresh W218 rig/report and owned script/profile against main ROOT. No generated assets were written. Scratch test and exact check results remain in `/private/tmp/w218-line_in_the_sand-prepare/check.py` and `checks.json`.

30 checks passed, including mutation-audited import/generate (no write/mkdir/process attempt), deterministic repeated output mapping, exact namespace/count/types, semantic parent equality with actual retained W188 outputs, all13 exact knots,54 nonzero monotone knot tangents,30 equal scalar hold segments, bounds/extrema, shared finite-difference C1 derivatives, float32 grid, hidden dispatch interval, both grips/hands/scales/nonFP/endpoints, original ADS/inspect/fallback graph and seat release. Maximum adjacent Euler component step11.346894degrees; maximum rigid battery-offset error9.77e-10; maximum left/right derivative difference9.60e-5 with epsilon1e-8. These are offline numerical checks, not native visual claims.

No whole Gradle, live client/server, Vision input, original generator execution, commits/stash/reset/clean, shared asset writes or child workers.

## Initial integration and image-feedback checklist (FIRST update below)

Install exact fresh W218 rig/report bytes, load W218 profile and source-rig routing in shared loader, materialize returned assets and bind runtime grid60 while preserving gameplay timing. Measure every assembled route. Run FIRST with actual inputs/PNGs for rest support, both hands/grips, battery withdrawal/disappearance/re-entry/seat, wrist release/recovery, ADS/inspect visibility and native return. Route/lifecycle checks include partial/empty/no reserve/cancel/switch/equip/death/disconnect; audio listening and10–20display observation remain master-owned.

Same worker must receive and VIEW FIRST actual images with exact segment/problem/source basis. A satisfactory FIRST still requires documented same-worker feedback; no cosmetic motion change merely to create a delta. After feedback, change this review only unless an actual product correction is justified, then master integrates and performs SECOND. Pending FIRST/feedback/SECOND, native hand contact, framing, ADS obstruction, pack loading/audio and performance remain unverified. Shared-family armature evidence does not establish exclusive Line in the Sand mesh/camera/finger IK or exact source hand fit.

Recommended FIRST samples: p0,.10,.20,.30,.3833,.40,.5833,.60,.76,.80,.84,.92,1. Compare visibility at.40/.60 and payload attachment through.80/.84; inspect both mirrored FP hands and native/twohand routes. Exact seat recovery should leave magazine display equal to body display from.84 onward.


## FIRST actual native image feedback — 2026-10-28

Worker directly VIEWED the following existing native PNGs read-only under main `docs/qa/2026-10-28/w218/`; no screenshots were regenerated and no live client/input was used:

- `vision1/screenshots/line_in_the_sand-reload.png`
- `vision1/screenshots/line_in_the_sand-review.png`
- `first-post-reload-review.png` (Line in the Sand upper-left panel)
- `vision1/frames/w218-line_in_the_sand-after-reload.png` (full-resolution completed return)

Also directly VIEWED each of these raw files in `vision1/frames/` (these are native capture sequence indices, not the61-model bank indices):

| Exact raw PNG filename | Visible evidence and limit |
|---|---|
| `w218-line_in_the_sand-reload-sample-01.png` | Initial forward weapon posture, receiver/coil/sight readable and arms below center. HUD0/20. |
| `w218-line_in_the_sand-reload-sample-05.png` | Steep lift, right-side supporting grip remains against gun; no gross body/arm separation. Lower handling region partly below image. |
| `w218-line_in_the_sand-reload-sample-09.png` | Raised receiver, lower handling region near bottom edge. Does not reveal concealed battery contact. |
| `w218-line_in_the_sand-reload-sample-10.png` | Left support palm is visibly separated from weapon at lower-left; no cell is visible in its gap. Gun stays with right grip. This falls in the intentional hidden-cell exchange interval; it is not evidence of a visible battery floating away from a gripping palm. |
| `w218-line_in_the_sand-reload-sample-12.png` | Empty support palm remains displaced lower-left while raised gun remains in right hand. Still no visible cell/palm contact to certify. |
| `w218-line_in_the_sand-reload-sample-13.png` | Complete dark battery with silver border/contact tips visibly re-enters next to left palm, distinctly separate from fixed receiver/coils. |
| `w218-line_in_the_sand-reload-sample-14.png` | Left palm and battery approach underside opening. Palm covers much of the junction; flush seating cannot be measured in this view. |
| `w218-line_in_the_sand-reload-sample-15.png` | Incoming dark/silver-edged battery is raised beside left palm close to lower receiver. There is readable reinsertion, but hand/weapon overlap hides the final mating surfaces; this single PNG does not prove a fully seated payload. |
| `w218-line_in_the_sand-reload-sample-16.png` | Cell remains visible beside handling palm during transition toward recovery. Do not call this already fully seated from the image alone or infer exact authored progress from sample index. |
| `w218-line_in_the_sand-reload-sample-18.png` | Weapon has returned near forward posture, no extra detached cell visible. HUD still0/20 here, so this frame alone is not ammo-completion evidence. |

### Hidden-cell gap: deliberate phase, no demonstrated product defect

The W188 same-weapon storyboard shows outgoing battery/hand withdrawing below frame and replacement arriving from below-left, with no requirement that the support palm stay on the fixed receiver throughout exchange. W218 deliberately preserves the old dispatch omission at `[.40,.60)` and restores the complete payload afterward. The observed sample10 palm/body gap is consistent with the intentionally detached handling interval. It is not a seated-cell grip defect demonstrated by these images.

Be precise about the word release: sample10 is NOT the profile's final grip-weight release. The handling weight stays attached during this interval; `build_first_person_hands_w201.py` uses body display as the target when the moving cell leaf is omitted. Thus a hidden cell is not rendered and the image cannot certify an invisible palm/cell contact. The explicit final handling fade remains `.80..84`, zero after neutral seat`.84`. Changing the grip window to close an empty exchange gap would alter preserved authored handling without showing a visible-cell contact failure. No such edit is justified from FIRST.

The visible incoming battery in13..16 and the unobstructed completed return support retaining the authored trajectory. Concealed seating surfaces, exact transient palm clearance, every unsampled pose and a future SECOND image remain separate checks. There is no claim of recovered finger IK, a literal open-hand release gesture or exact source-camera hand fit.

### Source handling hand is LEFT

Re-read the read-only original `clips/fusion_rifle_04669cdb/bone-map.json`; SHA256 `a439c489fb5ab1de893beb8cfe682958641d1c2682059f849932a25db27d3fd4` matches the fresh source report/rig. Source wrist `DE9D6BEA` is explicitly `b_r_hand`, its shoulder `17025F50` explicitly `b_r_upperarm`. Weapon chain is `4A0810C4 -> 19AB4BEF -> DE9D6BEA`, so the weapon is parented beneath the RIGHT hand. The opposite handling chain is `D1232BA2 -> 897A1504 -> 8C83CB67`, at positive-Y rest positions versus the explicitly right chain's negative-Y positions. Its wrist has a hashed semantic string rather than an explicit `b_l_hand` label; the LEFT assignment is established by the paired anatomy/hierarchy and motion, not by inventing a missing source label or by screen-left alone.

Across all61 fresh evaluated frames of80A8ADD3, maximum wrist translation relative to the weapon's own rotating frame from the first sample is0.792435887 source units for `8C83CB67` (p.283333333), versus0.000013535 for the explicitly right `DE9D6BEA`. This confirms the LEFT chain performs the handling excursion while the RIGHT hand retains the weapon. These values measure source joint motion, not native contact error. Retain LEFT reload policy. Shared-family source does not establish exclusive Line in the Sand mesh/finger/camera recovery or authorize changing other groups.

### Completed return, ADS, runtime and remaining SECOND

`line_in_the_sand-review.png` shows the hip gun and arms below a clear center, and a centered ADS sight aperture with no arm crossing its opening in that sampled view. This is evidence for those actual shots, not all ADS transitions, inspect or the mirrored/native alternative route. `w218-line_in_the_sand-after-reload.png` and the Line in the Sand panel of `first-post-reload-review.png` show the restored hip hold with HUD5/20 and no separate battery held away from the gun. The full-resolution post PNG is stronger completion evidence than sample18's still-zero HUD.

Read master `vision1/native-validation.json`:15/15 sequences, Line in the Sand37 reload captures/17 ADS captures, native inputs neutral/released, completed ammo5/20, dense server progress through.95. Read `assembled-budgets.json`: actual Line in the Sand all-route maximum including full-chain arms701/1000 (batch maxima701/693/667/665/701). These are master runtime/budget evidence; worker did not rerun native QA. The initial candidate manifest remains an estimate and master owns acceptance records.

Decision: NO CHANGE to generator or profile. Only this review changed after viewing exact FIRST images. Keep current geometry/UV/holds/knots, LEFT handling policy, hidden interval and final seat-release window. The product hashes remain generator `140f263b633eb0c8ec2ec50115111f4f50a096a97ddb795cff52070e9d767ca8`, profile `afef82ad93095adb4e51d8aa67f3c026a141dccbb57e26b528e8a5d8f8deb766`.

Fresh SECOND native review remains MANDATORY before visual acceptance, with particular attention to left-palm/cell re-entry13..16, obscured seating/hand release, completed hip return and centered ADS. FIRST static images do not certify continuous60fps, exact finger contact, all lifecycle alternatives, audio listening or10–20display performance. Worker remains available for exact SECOND feedback; no formal product edit was made merely to create a delta.
