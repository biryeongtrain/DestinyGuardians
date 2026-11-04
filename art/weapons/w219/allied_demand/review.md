# W219 Allied Demand worker review

Status: three prepared files installed byte-for-byte after explicit READY. SAME-worker FIRST image review complete: justified implementation no-change; only this review is revised. Main/shared/generated resources and native/build operations remain untouched by this worker. SECOND and final native acceptance remain pending.

Owned delta is exactly:

- `scripts/generate_reload_w219_allied_demand.py`
- `art/weapons/w219/allied_demand/profile.json`
- `art/weapons/w219/allied_demand/review.md`

Preparation root: `/private/tmp/w219-allied_demand-prepare`. Exclusive worktree: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w219-allied_demand`. READY received after all five181099-file dirty seeds completed; common baseline SHA256 `0bd717b7a1a4e69ecc68be8d9ffea8908d94a66ae9c9f198e7395718827e9f01`. Exactly the three prepared paths were installed, with syntax/no-write/determinism/endpoint/part checks passing; no full inventory export or rig installation by this worker.

## Original evidence read before generation

Read main `AGENTS.md`, `/Users/qf/.codex/RTK.md`, `minecraft-weapon-art-design/SKILL.md` and its `references/ace-izanagi-study.md`. Preserve meaningful volumes and existing face UVs; do not add surface fragments to approach the1000 cap.

Read `/private/tmp/destiny-w219-source/source-review.json`, group `sidearm_c0461d9d`. Master evaluated original `/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return/clips/sidearm_c0461d9d/blender/source.blend` read-only in separately owned Blender5.4.0 Alpha. `allInputsUnchanged=true`; prior cached joint maximum error0. Action `Armature|fp_80A8A560_reload_full|Base`, slot `OBSlot`, original frames1..67 at30fps,61 evaluated poses. Worker did not independently open or run Blender.

Source blend SHA256: `16335951a2bd664aa4aba5ad9373de56be318d24f1795e3dd655fd5f1b172fb7`. It contains ARMATURE ONLY: no weapon mesh, camera, magazine event track or finger IK. Family provenance is shared with Lonesome; no weapon-exclusive action-selector claim.

Worker VIEWED actual `/private/tmp/destiny-w219-source/sheets/sidearm_c0461d9d-80A8A560-upper-chain.png` at p0,.2,.4,.6,.8,1 before generation. Bone-only XZ/YZ chains show reach, large handling excursion, later handling and recovery. This is not a native weapon/contact image.

Read fresh `/private/tmp/destiny-w219-source/sidearm_c0461d9d.json`. Left chain `D1232BA2 -> 897A1504 -> 8C83CB67` is the magazine hand; right `17025F50 -> A3781DCD -> DE9D6BEA` remains near weapon `4A0810C4`. After existing source-to-canonical conversion and32-unit scaling, left wrist-relative Y reaches about-17.112 at.35, returns near-2.144 at.50, then rises to+3.409 at.60 and+6.421 at.75. Right wrist-relative travel remains around.23. This supports explicit `hand:left` and a magazine release before the later hand lift, without claiming recovered contact/events.

## Product change and authorship

NEW reload route for Allied Demand. Own canonical `models/weapon_surface_w123/allied_demand.json` has85 elements. Move only `magazine_lower`63 and `magazine_floor`64. Keep83 body elements including green grip57, grip panels58/59, straps60/61 and heel62 fixed. Original elements, rotations, textures and UVs remain exact in the partition. No canonical edits or new texture files.

The exposed magazine is a lower section. Add one small `authored_internal_magazine_shaft` to its moving part: local from[7.64,8.20,8.50] to[8.36,10.35,9.30], same original magazine63 rotation origin/axis/angle and cloned face UVs. It overlaps the lower section and fits wholly inside the fixed grip while seated. This is explicitly a hidden-detail interpretation, not recovered source mesh. The initial shaft candidate protruded beyond the grip's front interior; the bounded corner-fit check caught this and its Z bounds were corrected before delivery.

Lonesome W213 was read only for matrix/graph infrastructure. No Lonesome geometry, pivot, motion knots or internal insert were copied. Body bank uses the fresh own source61 weapon FK. Translation32/source unit and source X-forward/Z-up -> canonical -Z-forward/Y-up match existing infrastructure. Shortest-arc rotation avoids Euler interpolation flips. The existing shared .1 normalized endpoint transition is mirrored as a whole rigid transition; no new per-axis attenuation, length override or camera compensation.

Magazine motion derives from this source's LEFT wrist-relative excursion, with authored reach/seat envelope. `gripWindow=[.05,.10,.45,.55]`: reach .05..10, hold during withdrawal/return, release .45..55. The part is exactly body-relative/seated from pose33(.55) through60. The original source continues later hand handling; it cannot carry the seated magazine during that phase. This remains an authored contact/seat choice; FIRST image-backed assessment below supports retaining it, with SECOND pending. Master uses existing magazine-to-source-palm translation fit; the source chain itself is not relocated to an authored magazine path.

Preserve effective sidearm framing translation[-1,.25,0],rotation[-1,0,0],scale.98,rightWristRoll27. No earlier weapon-specific Allied Demand profile was found. Set `sourceFullChain=true`, `keepMeshSupport=true`, `hideSupportAtRest=false` explicitly; the family previously hid support at rest. Preserve own right rest[8,9.15,8.88],left rest[7.25,8.75,9.16],reload contact[7.35,7.35,8.85] and their existing rotations. Contacts are authored approximate mesh landmarks, not recovered IK.

Ordinary fingerless player-skin full arms remain master-owned. No arm length stretching, per-axis damping, offscreen hiding tricks, new textures, stat/cadence/ammo/reload-clock/lifecycle/audio changes.

## Generator contract and bounded verification

Pure stdlib, inert import, `generate(root=ROOT) -> dict[absolute Path, bytes]`. No output writes. Reads current shared inputs dynamically and records hashes; does not pin shared files to old hashes. Rig is read first from `art/weapons/w219/rigs/sidearm_c0461d9d.json`, with scratch evaluated rig allowed only while the installed file is absent. Worker never writes/install rigs.

Returns exactly248 files in memory:246 own models (2 geometries+61*2parts*2grips display children), `items/weapon_reload_w219_allied_demand/allied_demand.json`, and `art/weapons/w219/allied_demand/manifest.json`. No other namespace. Native/twohand and both first-person hand contexts retain current carrier compensation derived dynamically from accepted displays. Exact canonical graph at0/1, inactive negative/overshoot and nonFP; canonical ADS/inspect cases precede reload dispatch. Thresholds are float32(i/60),61 poses/60 intervals. This does not certify native60fps continuous interpolation.

Bounded checks PASS: syntax; audited no-write import/generate; repeated in-memory deterministic bytes; exact output paths;61 float32 thresholds; exact endpoint displays and canonical fallback/ADS-inspect/nonFP; native/twohand and left-context scales; canonical fixed/moving partition and face UV identity; shaft rotated-corner containment inside grip; exact seated hold33..60. Adjacent body orientation maximum19.046163 degrees across both contexts/carriers, using matrix relative rotation; no180-degree flip. This is source action motion, not an arbitrary smoothness/performance guarantee.

Current counts:83body+3magazine=86 reload elements. Four classic arm surfaces reserve448 gives534. Maximum across actual read canonical item alternatives242 and split86, plus448, is690<=1000. Alternative representations are never added together. Master's integrated generated graph count remains pending; worker does not claim an all-route materialized measurement.

Preparation check mapping SHA256 (current dynamic inputs): `f2fa456dd089b38cc7d11ec5f8d2c5e0d76b7f4c32b7aa8b95e38622e25ef46b`. Expected to change when master installs the canonical rig path or shared inputs change; no pin gate.

## FIRST actual image review: justified no-change

Decision: keep generator/profile and the .45..55 release unchanged. No concrete contact/seat defect in the inspected FIRST images warrants a product correction. This is a bounded image-backed decision, not final acceptance.

Worker independently VIEWED the actual `allied_demand-review.png` and `allied_demand-reload.png` sheets, plus full raw reload samples08,09,10,11,12,13,14,15,16, raw hip, and ADS sample09 under `/private/tmp/destiny-w219-pass1-native`. Re-viewed the original bone-chain sheet and compared original61 source wrist positions around .45..95. No client/lease/fixture was operated.

Hip shows visible ordinary arms/support beside the grip, without an isolated hand floating away from it. ADS sample09 retains the upper iron sight over the receiver, with palms below it; these views provide no reason to refit rest contacts/framing or hide support.

Reload raw08 shows the dark detached magazine at the left palm, below the pistol, while fixed green grip/heel stay on the body. The magazine and palm visibly meet; no floating gap or isolated shaft is apparent at this view. Raw09 brings the left hand to the lower grip area; the dark magazine is no longer separately visible. It is partly occluded by the hands, so this is consistent with seating rather than proof of exact internal alignment. Raw10 shows the left hand rising toward the receiver without a separately carried magazine. Raw11 brings the empty hand over the receiver/slide area, obscuring that area transiently; raw12 lowers it and raw13..15 recover. No dark magazine follows the raised hand over the receiver. This is the desired distinction between insertion and later handling. Raw15 shows the ready silhouette while HUD still reads0; raw16 shows ready support and15 rounds. Do not equate visual recovery at15 with ammo completion.

The original source supports this late handling: left wrist-relative Y is-8.725 at .45,-2.144 at .50,-1.649 at .55, then+3.409 at .60,+5.860 at .65 and+6.421 at .75; it returns near rest by .95. Right wrist remains near its weapon-relative contact. `gripWindow` weight is1 at .45,.5 at .50,0 at .55 and remains0 during the upper-receiver hand lift. Retaining that separation avoids dragging the seated magazine with late source FK. The source contains bones only: call this later receiver-area handling, not recovered finger/slide contact or an independently animated slide mechanic. No new arm length, axis, camera, hiding or timing adjustment is justified.

Read the FIRST capture sequence and server presentation timeline. Sequence capture ordinals are not source pose indices. Raw08 brackets client685 (observation1793152874793ms), raw09 client687 (4902ms), raw10 client689 (5011ms), raw11 client691..692 (5120ms), raw12 client693..694 (5235ms), raw15 client700..701 (5585ms), raw16 client703 (5702ms). Absolute timestamps share the179315287 prefix shown for08. Server snapshots report native reload progress .41666666 at tick1276, .55 at1281, .71666664 at1287 and .9166667 at1294, then canonical inactive floats[0,-1] and15/0 ammo at1299; duration36 is unchanged. These sparse, independently bracketed server/client observations do not assign an exact source pose to a PNG or prove every .45..55 pose/contact. The observed detached-to-seated transition followed by empty-hand lift is consistent with the intended release window.

SECOND should repeat extraction/reseat/late handling/ready and ADS under the same scenario, retaining special attention to the partially occluded .45..55 insertion. Twohand/left-hand display contexts, interruption/nonFP and every intermediate contact are not established by these selected native-grip images. FIRST coordinator is still completing other weapons; no batch-completion or SECOND result is inferred.

## Required remaining native sequence

Original master Blender evaluation/report+viewed source-chain PNG -> candidate61 is complete. Master owns original rig installation, shared loader/action whitelist and routing, generated resources/full-arm graph, targeted/integrated checks, builds and all CU/Vision/client/server operations.

FIRST Allied Demand feedback was received and actual PNGs were reviewed by this SAME worker. Return delta for FIRST is review.md only: justified generator/profile no-change. Master integrates this decision and runs SECOND with the same scenarios; retain insertion-window visibility and remaining carrier/context/interruption checks as above. No generated resources or shared integration are changed by the worker.

No final native acceptance, performance certification, continuous60fps or recovered camera/finger-IK claim.

## FIRST evidence SHA256

Paths below are relative to `/private/tmp/destiny-w219-pass1-native` except the absolute source evidence path. They record inspected files, not hash gates on master shared inputs.

| Evidence | SHA256 |
|---|---|
| `screenshots/allied_demand-review.png` | `e532ce3a2a1a52f20cba9893e1f4066afe394639c522224379e1a9e44e3495a4` |
| `screenshots/allied_demand-reload.png` | `c708f816bc9e7d29ee2512e6aa08ad73e9698a150d4958a0ba4fa2ecc4984cea` |
| `frames/w219-allied_demand-hip.png` | `2a4c7913650c92cd3df2384ffe67f20d577abe73318d2b5329f0cee4a013bddb` |
| `frames/w219-allied_demand-ads-sample-09.png` | `96b84cdbcff2280ce0356bb877c69d640ad5466fad0a15433869d91adb539e1d` |
| `frames/w219-allied_demand-reload-sample-08.png` | `cb40abeaf5745fe055404ab4563f6216524cf647c1cb1a115f3cd3c40ad95553` |
| `frames/w219-allied_demand-reload-sample-09.png` | `dfb40403d6deb112d855ec04f7bd7955dbc5ed014cbfed19f84671e8689e9dd1` |
| `frames/w219-allied_demand-reload-sample-10.png` | `2a0a5371f2dc4c835a742b10da1c2aa106643773eb26fa369f5d2d2b773e8b20` |
| `frames/w219-allied_demand-reload-sample-11.png` | `70c5b61d95ea19a5ff292226110ae82f2bfce86ce8ac540f1e1db3fc83dcc9a0` |
| `frames/w219-allied_demand-reload-sample-12.png` | `5125bcc6c0a4de946f310b6b4e8dbeaf7a23d65c03c9e96e3611c062f59fa6d9` |
| `frames/w219-allied_demand-reload-sample-13.png` | `5cf1536938afd9c85e6f01ec988d8af94fea5ae1ae27b6302c2d03b7ae25bbb3` |
| `frames/w219-allied_demand-reload-sample-14.png` | `d731cd0a0b95c1f5308047b4b922f607b131a031fd0f831feca1a483b189f58e` |
| `frames/w219-allied_demand-reload-sample-15.png` | `f7657c9e38877b63cf7c742afcddd3d32f57ee05a1e3bc2c507a20d0d4a099ba` |
| `frames/w219-allied_demand-reload-sample-16.png` | `3d394e4ce980ed334e400b5c764d4ad860cdd4c1f73b25fe9877781dc48a4574` |
| `sequences/w219-allied_demand-reload.json` | `595d37afdbbd903c4a913e7475e18d0164148caf30d639c7b827d33b48e357da` |
| `oracles/w219-allied_demand-reload-timeline.json` | `8915d2fb78dc9f66c45c16a9454277b976834bec349ed87c31f66a94d9cd89f6` |
| `/private/tmp/destiny-w219-source/source-handling-evidence.json` | `3b33ce169007525991bb43dbadf00967ec2b129b46e0171a216e6b8cb06be22a` |
