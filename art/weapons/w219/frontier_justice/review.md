# W219 Frontier Justice — prepared product delta, native review pending

Only these three paths are worker-owned:

- `scripts/generate_reload_w219_frontier_justice.py`
- `art/weapons/w219/frontier_justice/profile.json`
- `art/weapons/w219/frontier_justice/review.md`

Prepared under `/private/tmp/w219-frontier_justice-prepare` against read-only current main. The exclusive worktree `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w219-frontier_justice` has not been written: master explicit READY is still required. No generated outputs, rigs, shared code, gameplay, audio, builds, clients or servers were written/run. No reset/stash/commit/clean/push.

## Original evidence before implementation

Read main `AGENTS.md`, `/Users/qf/.codex/RTK.md`, the `minecraft-weapon-art-design` skill and `references/ace-izanagi-study.md`. Existing W218/W216/W213 dense generators informed the pure API, exact guards and rigid display composition; their weapon motion, mesh and geometry hashes were not borrowed.

The master evaluated the actual original `.blend` read-only in separate Blender 5.4.0 Alpha before this worker's implementation. Worker read `/private/tmp/destiny-w219-source/source-review.json` and fresh `/private/tmp/destiny-w219-source/scout_rifle_a3826f40.json`, and **viewed the actual image** `/private/tmp/destiny-w219-source/sheets/scout_rifle_a3826f40-80A8A345-upper-chain.png`. Worker did not independently open or evaluate Blender.

Original: `/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return/clips/scout_rifle_a3826f40/blender/source.blend`; SHA-256 `1903c0183ed2e2dd081620f442396fcfb3e2b831e5a09a9b696b70288fe8afd3`. Source map `1beb2b45ff18cc12ecfd70d417e3cc7dc295490b9a6c145e43fb860d58781e4c`; bone map `34cc654306ee835cf908f72fed910a3955868195289e1109178a45c237fcee40`. Report says all source inputs unchanged and prior cache joint absolute error 0.

Selected source action: `Armature|fp_80A8A345_reload_full|Base`, slot `OBSlot`, source frames 1..105, 30 fps, 61 uniformly evaluated poses. The shared scout source contains **three ambiguous** `reload_full`/`reload_empty` variants (`80A8A345`, `80A8A337`, `80A8A331`); master selected `80A8A345` after actual source-chain review. This is not a unique Frontier Justice selector.

Scene contains only an ARMATURE, without weapon mesh, camera or finger IK. The bone sheet shows substantial early handling-side motion and recovery. It cannot prove magazine dimensions, mesh contact, camera fit or independent charging-handle actuation.

Handling-side recheck: **LEFT** (`leftWrist` `8C83CB67`, elbow `897A1504`, shoulder `D1232BA2`). At normalized .20/.30/.40, original weapon-relative right wrist is approximately constant `[-.0857,-.0637,.0201]`, while left wrist travels `[-.6490,.3309,-.0612]`, `[-.6008,.2941,-.3122]`, `[-.1699,.0228,-.1547]`. Roles come from source names/matrices, not apparent screen mirroring. Later left motion remains source replay; no unobserved bolt event is invented.

## Implemented behavior and authored limits

Use Frontier Justice's own existing W138 surface geometry and face UVs. Its long scout silhouette, thumbhole stock, real guard/stock openings, receiver and fixed controls stay intact. This is a reload split, not a surface redesign. Ace/Izanagi's meaningful-volume and face-UV principles support retaining these solids rather than generating extra small detail or transplanting another scout mesh.

Split exactly indices **123..125** (`magazine`, `magazine_floor`, `magazine_rear_bevel`) into emitted part `magazine`; 138 remaining elements stay `body`. Charging handle 126 remains fixed with body because source evidence does not establish independent actuation. No extra shaft, mesh, triangles, fade, scale change or hidden support geometry.

The neutral body display is deliberate: the master `sourceFullChain` framing/hands builder replaces it with the selected original weapon-bone carrier and replays both original shoulder/elbow/wrist chains once. Baking that body motion again here would duplicate the shared transform. Source action and fresh W219 rig are explicit in the profile. Fresh rig default path is `art/weapons/w219/rigs/scout_rifle_a3826f40.json`; master installs it. Preparation passes `rig_path` pointing to the read-only scratch export; generator never copies or writes rigs.

Only the magazine local path/contact is authored: reach to .10, withdrawal .10..20 by `[0,-3.8,.25]`, hold .20..32, approach/reseat .32..48, seated through recovery. C1 weighted harmonic PCHIP preserves holds and zero endpoint/extremum tangents. These normalized times and dimensions are a calibration, not extracted magazine events. `gripWindow [.04,.10,.40,.48]` attaches to LEFT before withdrawal, fades during final insertion, and releases completely at the authored .48 seat. The master attachment code moves the part toward the source palm; it does not stretch or pin the source arm to the authored contact. FIRST must assess the held fit and .40..48 handoff.

Retain current contacts exactly: right `[8,8.4,7.8]`/`[-29,0,0]`; left `[7.8,9.22,-.8]`/`[0,90,-85]`; reload `[7.45,7.45,12.4]`/`[0,0,0]`. Preserve effective scout framing translation `[-.65,.6,0]`, rotation `[-1,2,0]`, scale `.98`, right wrist roll 28 and left rotation `[15,35,-35]`; `sourceFullChain=true`, `keepMeshSupport=true`, `hideSupportAtRest=false`. Ordinary fingerless full player-skin arms only; no length stretch, axis damping or hiding hacks.

Pure stdlib `generate(root=ROOT)` returns 248 absolute `Path -> bytes` entries: 2 static part models, 244 display children (61 × 2 parts × 2 grips), 1 item graph and 1 manifest. Model/item outputs stay within `weapon_reload_w219_frontier_justice`; manifest is own `art/weapons/w219/frontier_justice/manifest.json`. No output files were materialized. Optional read-only `profile_path`/`rig_path` support preparation before installation. Shared file hashes are recorded from current consumed bytes, not pinned to old master inputs.

61 thresholds are exactly `float32(i/60)`. Native/twohand and both FP contexts preserve their accepted carrier transforms. Canonical item graph is exact at 0/1, negative inactive, overshoot and non-FP; original ADS/inspect cases precede dispatch. 61 poses do not claim native continuous 60 fps interpolation.

Stats unchanged: magazine 13, 150 RPM, cadence 8 ticks, burst 1, shared burst ammo false, reload 48 ticks; original 48-tick W63 reload sound event/asset. These inputs are read and recorded, never emitted or modified.

## Bounded verification performed

- Python syntax passed via `ast.parse`, without bytecode files.
- An audit hook rejected filesystem mutations during import and two `generate()` calls; both calls completed and returned identical byte mappings.
- Exact 248-path allowlist, absolute paths, byte values and JSON parsing passed.
- 61 exact float32 thresholds, both grips/FP contexts, exact endpoint/inactive/non-FP fallback and unchanged ADS/inspect cases passed.
- Exact original magazine elements/UVs and fixed charging handle partition passed; no arm/weapon scale animation or non-finite display values.
- Fresh source metadata includes all 61 samples and both complete shoulder chains over source range 1..105.
- Reload `138+3+448 = 589` elements. Current canonical graph alternatives resolve to at most 236 weapon elements, hence conservative canonical plus four classic arm surfaces `236+448 = 684 <= 1000`. Alternative representations are not added together. Master still measures the actual integrated generated graph.

## Pending mandatory native sequence

Master READY and installation of only these three files; master installs fresh rig and integrates shared routing/loader changes. Then FIRST actual native Vision images; this **same worker** views those actual images and corrects a concrete defect or documents an evidence-based no-change decision. Master integrates the delta and performs SECOND Vision. No native acceptance has been claimed.

FIRST should cover ready/ADS/inspect, representative dense phases especially .10/.20/.32/.40/.48/.60/.80, both hands' contact and complete arm lengths, fixed charging handle, magazine seat/release, canonical endpoints, inactive/non-FP and native/twohand/left-hand carrier behavior. Native screenshot visibility, pack loading, input lifecycle, materialized route budgets and final visual acceptance are master-owned and pending. No full hands generator, shared rebuild, full audit, client or server was run by worker.

## FIRST feedback — same-worker actual-image review, no motion change

This entry supersedes the earlier preparation/install-pending status. After explicit READY, the exact three prepared files were installed byte-identically in the exclusive worktree. Master subsequently integrated the shared source/routing and supplied FIRST native evidence. The same original worker reviewed that evidence before SECOND. This feedback changes **only this owned review.md**; generator and profile remain unchanged.

Evidence root, read-only: `/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-28/w219/vision1`. Worker viewed actual `screenshots/frontier_justice-review.png` and `screenshots/frontier_justice-reload.png`, then opened the underlying full-size 1708×960 PNGs individually: `frames/w219-frontier_justice-reload-sample-00.png` through `-15.png`, plus `-26.png`; `frames/w219-frontier_justice-hip.png`, `frames/w219-frontier_justice-ads-sample-06.png`, and `frames/w219-frontier_justice-after-reload.png`. That is 17 raw reload frames and 3 raw ready/ADS/return views, not just sheet thumbnails.

Worker decoded `sequences/w219-frontier_justice-reload.json` and read the presentation rows in `oracles/w219-frontier_justice-reload-timeline.json`. The sequence records 27 captures, return code 0, successful capture and cleared input on release. Samples 00..14 bracket the reload model, while 15..26 use the canonical ready model. Presentation rows advance through progress .016666668, .13333334, .26666668, .38333333, .51666665, .6333333, .76666665 and .8833333, then return to canonical floats `[0,-1]`. These are asynchronous state observations, not an exact per-PNG normalized-progress stamp; screenshot indices are **not** source pose numbers.

Image observations:

- Hip and post-reload show the same recognisable scout, exposed stock/thumbhole and guard structure, with support beneath the fore-end. Full ADS frame 06 shows the rear aperture and front post clearly against the sky; hands do not cover that aperture.
- Raw reload 00..01 shows the initial transition. In 02..05 the rifle raises near vertical, the right hand remains with its grip/stock area, and the handling hand is mostly outside the bottom of the frame. Missing offscreen contact is not scored as a failure or proof of contact.
- In raw 06 the light magazine is visible immediately beside/behind the tip of the entering LEFT hand. This supports LEFT handling, but the palm obscures part of the solid and does not prove exact fingerless-palm contact at every instant.
- In raw 07 the magazine is visibly back beside the rear stock while the LEFT hand has moved away from it. In 08..11 the rifle turns down and the LEFT arm crosses toward the receiver during the original recovery; the magazine stays body-relative where visible. No definite late magazine drag, duplicated magazine or charging-handle separation appears in the reviewed frames.
- Raw 12..13 returns toward the ready direction; 14 displays 13 rounds, and 15/26 plus the dedicated after-reload PNG show stable hip geometry/support again. This is sampled return evidence; it does not independently certify every intermediate pose or lifecycle branch.

Original-chain recheck: worker viewed the actual `scout_rifle_a3826f40-80A8A345-upper-chain.png` again and read fresh original matrices around source progress .40..50 and .60/.70/.80. The right wrist stays near weapon-relative `[-.0857,-.0637,.0201]` while LEFT moves from `[-.1699,.0228,-.1547]` at .40 through `[-.1615,.0576,-.1642]` at .45 to `[-.0615,.1411,-.0998]` at .48333, then continues its separate recovery. The original chain still supports LEFT handling and releasing the seated mesh before the later wrist excursion. The source is armature-only, so it cannot turn the authored .48 seat into a recovered event or establish a separate charging-handle actuation.

**Decision: evidence-backed no-change to generator/profile.** The reviewed full frames reveal no concrete owned defect that justifies altering the three magazine solids, current framing/contact, release window or source-chain replay. In particular, extending attachment into the later source wrist motion would risk dragging a visibly seated magazine. Preserve `gripWindow [.04,.10,.40,.48]`, exact moving indices 123..125 and fixed charging handle 126. No formal change was made merely to satisfy the feedback stage.

Remaining limit for fresh SECOND: exact .40..48 palm/part handoff is not established by these sparse, partly occluded native captures; FIRST supports the visible approach/seat/recovery sequence, not continuous contact throughout that window. Recheck that interval and the same ready/ADS/return scenario in SECOND, preserving the original full-chain source without damping, stretching or hiding. All-angle/full-arm visibility, native/twohand/left-hand coverage, inspect and uninterrupted 60 fps motion are not established by this image review. SECOND and final native acceptance remain master-owned and pending. Worker did not modify main/shared files, run native input, rebuild, regenerate resources or write any file outside the owned review path.
