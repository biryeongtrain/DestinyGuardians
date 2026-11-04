# W214 Retrofit Escapade — FIRST worker review; SECOND pending

FIRST image-backed worker decision: no product change. Generator and profile remain byte-identical to the integrated candidate. Only this review is updated. SECOND Vision and final acceptance remain pending; retain this worktree open for the master.

Master owns integration and native acceptance. Worker authored exactly the generator, profile and this review in `/private/tmp/destiny-w214-retrofit_escapade-draft/files/`; the assigned worktree was absent when work began. Main checkout remains read only. No Blender, Vision/CU, game, shared build/assets or SSD source was operated or modified by this worker.

## Source reviewed before generation

Read `/private/tmp/destiny-w214-source/source-review.json` and `machine_gun_e5b72131.json`; viewed actual `sheets/machine_gun_e5b72131-80A8A005-upper-chain.png` through image inspection. The master reports headless Blender5.4.0 Alpha evaluation of real source.blend, OBSlot, `Armature|fp_80A8A005_reload_full|Base`, frames1..180 at30fps,61 evaluated samples, old-cache maximum error0, unchanged source inputs. Worker did not independently open/evaluate Blender. The evaluated JSON names the action `Base.001`; the master report names it `Base`. Selection uses stable action80A8A005, not the suffix. Provenance hashes are recorded in profile.json.

Evidence contains only an armature/shared machine-gun family. No recovered mesh, camera or physical finger IK; family inclusion of Hammerhead and Retrofit is not a weapon-exclusive action selector. Shoulder/elbow/wrist/weapon chains are present. Source lengths at32model units/source unit are forearms8.14136 and upper arms8.7266. Start/end maximum matrix delta is0.0007364451885223389, so generated part endpoints explicitly use canonical rest rather than claiming source bit equality. The viewed XZ/YZ sheet shows substantial intermediate bending and near-return atp1; it cannot establish in-game contact.

Read main AGENTS.md, RTK.md and minecraft-weapon-art-design/SKILL.md plus its Ace/Izanagi study. The study's87/79 cubes inform semantic partitioning and UV discipline, not a required redesign or cube count. Preserve Retrofit's accepted teal/cloth/copper atlas, fork, wrap, drum, exposed linked feed and hooded optic; no new decorative solids or UV changes.

## Candidate implementation

The W210 Hammerhead template does not exist in main. Used audited W213 Steelfeather/Chattering Bone pure-generator patterns and W213 Lonesome's scalar hold-preserving PCHIP approach. Statically parsed W181 and ported only audited KEYS, GRIP, HINGE, cover/handle names and pure matrix/articulation algebra. Never imported or executed the W181 generator: its NumPy/Pillow/render/reference-media dependencies remain unused.

`generate(root=ROOT) -> dict[Path,bytes]` is pure stdlib. Import does not write; generate reads solely beneath its explicit root and returns absolute paths without materializing them. Three parent partitions,366frame/grip/part children and one item wrapper yield370pack JSON files plus one manifest=371outputs. Master owns all writes of those outputs. An exact output allowlist limits the result to the W214 Retrofit model/item namespaces and its manifest.

- Body59: all fixed housing and the independent charging handle. Handle translates locally inZ, peaks1.05 atp.80 and returns by.88.
- Magazine51: all10drum/neck,35round/link and6feed-connector solids share one rigid display and one master palm-contact shift. Nothing in this assembly separates into stray bullets.
- Cover24: upper rail/rear shoulder and complete optic articulate together about original HINGE[8,12.4,-.1]. Cover never joins the drum or charging handle; original -96degree opening and .18..58 hold remain.

All134canonical cuboids, dimensions, faces, texture bindings and UV records are preserved. Only rigid cover/handle geometry articulation and existing part display poses vary. The accepted original KEYS, extrema, .26..30 exchange hold, .50 onward seated drum and pivots remain. Weighted harmonic C1 PCHIP replaces per-segment smoothstep, with exact holds and zero slopes at endpoints/holds/extrema. Emit61poses with exact float32(i/60) thresholds; this does not certify continuous60fps rendering.

Both endpoints use the complete canonical item graph and exact rest geometry/display for every partition, FP hand and native/twohand grip. The original ADS/inspect cases precede reload dispatch. Negative/inactive progress and all non-FP contexts retain the canonical graph. No gameplay, reload90tick clock, magazine77, RPM900, cadence, ammo transfer, lifecycle or audio changes are made.

## Contact, release and budget

Copied actual accepted `f.profile(data,'retrofit_escapade','machine_gun')`: translation[-.65,.6,0], rotation[-1,2,0], scale.98, rightWristRoll28, leftRotation[15,35,-35]. Added sourceFullChain:true, keepMeshSupport:true, hideSupportAtRest:false. Preserve W201 rest right[8,8.55,8.48]/[-24,0,0], left[7.8,8.85,-1.3]/[0,90,-85], and reload contact[4.5,8.45,3.92]/[0,0,-80]. Explicit reload rigAction80A8A005, partHint magazine, policy magazine. The right/left rest mesh offsets and held-part contact are distinct and must not be substituted.

Authored drum/belt seating is exactlyp=.50; cover closes .58..66; later side/charging action runs .66..88. Source left wrist relative weapon Y rises6.132->11.008 fromp.50->.55, then6.274 at.60: continuing full magazine attachment into that later motion would move the already seated feed. Proposed gripWindow[.08,.18,.42,.50] attaches by withdrawal, holds through exchange/return, then releases during the final .42..50 approach. Attachment is exactly zero at seating and throughout later source wrist lift, closure and charging. A preliminary .50..58 release was rejected during offline review because it could still drag already seated feed. FIRST images support retaining this authored window. It is not an extracted attachment event or copied Lonesome release.

The master measured the maximum over ALL materialized routes WITH arms: **677 emitted elements**, below the1000 limit with323 elements of headroom. Read `docs/qa/2026-10-28/w214/budget-pass1.json`; its Retrofit profile SHA-256 matches the unchanged owned profile. This replaces the earlier narrower reserve estimate in this review; do not use the weapon-only134 or initial arm-bank estimate as the final assembled budget. The worker read the master measurement and did not rematerialize arms or independently recount every route. Preserve normal source lengths, full FK and shoulder bends; no stretch, damping, source attenuation or support hiding.

## Bounded candidate validation

Bounded in-memory checks passed on the candidate. The source61 rig, generator and profile were supplied by an in-memory read overlay: no worktree seed or generated pack files were written. An audit hook rejected filesystem writes, mkdir/removal/rename, process launches and network connections; import and four generation calls attempted zero such actions. Four banks across three explicit/default root variants produced identical relative-path bytes and exactly371absolute Path->bytes results, including370pack outputs and a manifest. Every generate input read stayed beneath its supplied root. Virtual roots remained absent.

Validated all61x3partsx2grips child outputs; reconstructed all134canonical parent elements in original index order; compared faces/UV/material records and all non-motion properties; maximum rigid dimension roundoff3.552713678800501e-15. Exact authored KEYS/GRIP/HINGE/cover/handle names, exact knots and1407scalar hold evaluations passed. Interior scalar samples stayed within original key extrema; maximum left/right finite-difference C1 discrepancy0.0045000803083894425 at1e-7step (numerical estimate, not a formal proof). Maximum adjacent child display Euler component step4.00342484degrees; no large display flip in this bank. Both endpoint displays match canonical native/twohand for all parts/contexts; endpoint children have no geometry override. Exact float32 thresholds select their own rows.216canonical endpoint/negative/nonFP/ADS/inspect plus active FP grip branch combinations passed. Output manifest pack hashes match every returned pack byte.

After tightening the proposed gripWindow from.50..58 release to.42..50, reran the profile/root/output checks and verified the shared handling envelope is exactly zero for every61-grid row at/after authored seatingp.50; source hand travel therefore cannot shift the seated magazine through the master magazine-follow path. Earlier geometry/curve/branch checks are unaffected by this profile-only change. During initial generation only three owned draft files were written; no emitted assets, tests, logs or cache files were created by this worker. The master subsequently materialized/integrated the candidate and supplied FIRST native evidence and the all-route arm budget below.

## Mandatory FIRST image-backed worker review — 2026-10-28

Decision: **justified no-change to generator/profile**. The two supplied actual native PNG sheets and all raw images listed below were personally viewed in this worker turn, including every capture ordinal10..20. This is the worker-feedback stage after FIRST, not final acceptance. No product, geometry, UV, contacts, phase, materialized asset or shared hook was changed, and no rebuild/test/game/input/Blender operation was run by the worker.

Observed in the exact native images:

- Hip raw shows the complete drum, linked feed and closed optic/cover, with the support arm visible. ADS raw06 has an open centered sight aperture; the arms/belt do not cover its center in this capture.
- Reload raw00 shows early low framing/closed cover; raw06 shows the raised cover/optic and feed assembly partly outside the lower-left crop. The crop does not establish deletion of the drum/belt.
- Raw10 has the complete drum against the support palm and the belt below the raised cover. Raw11/12 show the palm alongside the drum as the complete feed assembly rises: the belt retains its continuous stepped form and moves with the drum. No separate belt-only displacement, exploded links or incoherent cartridges is visible.
- Raw13..16 show the drum/belt back beside the receiver while the support palm continues up/across the raised cover. The hand overlaps/occludes the cover silhouette in this projection, especially14/15, and part of the receiver/feed in13/16. These images do not provide depth/contact-volume evidence to distinguish palm contact from actual mesh penetration; this remains an explicit SECOND contact check. They do show that the palm does not continue carrying the seated drum into the later raised-hand motion.
- Raw17 shows the cover/optic lowering independently with drum/belt still at the receiver. Raw18 shows the cover/optic closed and the support hand lowered alongside the fore-end. No isolated belt correction is supported.
- Raw19 shows the closed cover, seated drum/belt and a hand approaching the receiver side during the late weapon tilt. Raw20 shows the hand against/overlapping that side. Exact charging-handle/palm depth is partly occluded, so this establishes the late hand approach, not a recovered physical grip or finger IK. Preserve the existing handle motion independently of both cover and feed.
- Raw25 shows return/recovery with the closed cover/optic and coherent drum/belt, ammo77/73. A capture ordinal25 is not source frame25 or progress25/60.

There is no supported defect here requiring a generator/profile delta. Preserve gripWindow[.08,.18,.42,.50], independent cover/charging and the whole drum+belt transform. Do not move the belt alone, extend attachment beyond seating, attenuate source motion, hide the support arm or change ordinary limb lengths to mask the projected overlap.

### Exact source and timeline assessment

Re-read the master's evaluated source JSON: shared-family `machine_gun_e5b72131`, action80A8A005, `Base.001`, range1..180,61samples. It remains bone-only evidence. Normalized source evaluation uses `frame=1+179*p`; the original scalar part knots remain authored rather than recovered attachment/cover events. Relevant authored coordinates are:

| Event | Authored normalized p | Coordinate within evaluated source range |
|---|---:|---:|
| Full feed attachment / cover open | .18 | 33.22 |
| Begin final approach release | .42 | 76.18 |
| Drum/belt seated, attachment zero | .50 | 90.50 |
| Begin cover closure | .58 | 104.82 |
| Cover closed / side action begins | .66 | 119.14 |
| Charging-handle displacement peak | .80 | 144.20 |
| Charging handle returned | .88 | 158.52 |
| Canonical endpoint | 1 | 180 |

Coordinates in that table are range mappings of authored p, not recovered source events or PNG identifiers. Some knots are between61-grid samples: .42 lies between source-grid indices25(p.4166667) and26(p.4333333); .50 is grid index30/source frame90.5. Source FK atp.50/.55/.60 has left-wrist relative weaponY approximately6.132/11.008/6.274model units: allowing a seated feed to follow that later palm rise would be inappropriate. Current envelope reaches exactly zero atp.50 and remains zero afterward. Keep the source FK itself unchanged.

The PNG filenames are **capture ordinals**. `sequences/w214-retrofit_escapade-reload.json` stores54captures and before/after client-tick brackets, not a source-frame ID or CMD progress attached to each PNG. For the inspected overlap interval:

| Capture ordinal | Before client tick | After client tick |
|---|---:|---:|
| 10 | 1532 | 1534 |
| 11 | 1535 | 1537 |
| 12 | 1539 | 1541 |
| 13 | 1542 | 1544 |
| 14 | 1545 | 1547 |
| 15 | 1549 | 1551 |
| 16 | 1552 | 1554 |
| 17 | 1555 | 1557 |
| 18 | 1559 | 1561 |
| 19 | 1562 | 1564 |
| 20 | 1565 | 1567 |

The server oracle is sampled on its own clock. Read `oracles/w214-retrofit_escapade-reload-timeline.json`: server tick2031 reports p.45,2037 p.51666665,2042 p.56666666,2046 p.6166667,2051 p.6666667,2062 p.8,2070 p.8833333, and2081 p-1/reloading=false. These bracket the runtime sequence; they are not synchronized per-pixel labels for raw10..20. In particular, screenshot12 must not be called authoredp.20, source frame12 or source-grid index12. The visual closure/late hand order is consistent with the existing authored phases, but these captures do not prove the exact tick of contact/release or cover collision.

### Master checks and revised measured budget

Master reports targeted JUnit13 plus source-binding1 passed. This worker did not rerun them. Independently read `vision1/native-validation.json`:12native sequences across the four weapons, neutralAfter=true; Retrofit has4fire captures,54reload captures,13ADS captures, all released and all recorded native movement keys false. Retrofit firingPaidRounds=7; the after-shot oracle reads70/135, compared with hip77/135. The separate empty-magazine reload fixture starts0/135; reload-finished reads77/73, p-1 and reloading=false, reloadDuration90. These confirm the observed firing/reload transitions and cleanup in this master run; no stronger ammo-funding/conservation, audio or performance claim is inferred from the fixture.

`budget-pass1.json` records Retrofit **677 including arms over ALL routes**, limit1000; its profile hash is identical to the owned profile. This measured maximum supersedes earlier narrow estimates in this review. Budget file SHA-256: `1609a20a1e08d070fcd52b2205731d546d0b6a801cf30359336afdf58c4785a0`. Native-validation SHA-256: `923d1b1cfc08345795fe1414f3953149e850437ce6ce431764390aa17de3f77d`.

### Personally viewed exact PNG inventory

All paths below are relative to `/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-28/w214/vision1/`. Only these18images are claimed as personally viewed by this worker; the master's all-eight-sheet review is separately master-reported.

| Actual image | SHA-256 |
|---|---|
| `screenshots/retrofit_escapade-review.png` | `218d2b0bbf86efce72e1f94003beaed695d91384e2196dac501e2dd01ad89e48` |
| `screenshots/retrofit_escapade-reload.png` | `c9bd468b7ccb51f1cf2add841d75448045eab634abe60edf8f2a4ec7d30da20e` |
| `frames/w214-retrofit_escapade-hip.png` | `3ab38e5278c81d56816c0156277fd4a1adbef98c14ef438dbcb048027c933c52` |
| `frames/w214-retrofit_escapade-ads-sample-06.png` | `a9cd17f8082f74f5a3ccac9d991d9dbc2b78ce747c032a1cc669d14d07c2f0df` |
| `frames/w214-retrofit_escapade-reload-sample-00.png` | `5e4ff5a85fe467f7697e36a666928439e1d924fd83302c7f02f4cb60dc14ab93` |
| `frames/w214-retrofit_escapade-reload-sample-06.png` | `a94b03197d5c224154f283d03e81d33f766bc00c210f52f097ceb6a1658b9768` |
| `frames/w214-retrofit_escapade-reload-sample-10.png` | `57c9e0007b455a56914497053369b2f95c68afc09629d725a7d15fd44de937ce` |
| `frames/w214-retrofit_escapade-reload-sample-11.png` | `7fe666481e65547e47734c24d63556d4fa5855319db79bce9aa295acd5a2b47a` |
| `frames/w214-retrofit_escapade-reload-sample-12.png` | `8bcb547a9499bf434e6fd8a7988dd60ed8a509a35ab76e282dc9fff402df758b` |
| `frames/w214-retrofit_escapade-reload-sample-13.png` | `b61bd2032da171a7381b4a4a55b3cfb05f218d7a9e32e46c617bfb3e975414ef` |
| `frames/w214-retrofit_escapade-reload-sample-14.png` | `f2bb89e94b2df6c3c54dc84eec81354ccf0f4d015540ba0c2f5f2bd5a94bd7b0` |
| `frames/w214-retrofit_escapade-reload-sample-15.png` | `5664a25a785d993f0833d6b41d953dbac9762c628d2edf6de0881bab98815161` |
| `frames/w214-retrofit_escapade-reload-sample-16.png` | `59864661eba3231a18f85f852f66804e82443b967840e7cfcc7eb649c7b87356` |
| `frames/w214-retrofit_escapade-reload-sample-17.png` | `cce06b46cb610fcd912543268c1f3b99fa28a01de7dffb08e894b78579801737` |
| `frames/w214-retrofit_escapade-reload-sample-18.png` | `3d9a53b5f79302c3fcbb290b6ffea52f2ab18d08437f93e301c009d1e062d456` |
| `frames/w214-retrofit_escapade-reload-sample-19.png` | `b88568f514adc3bdaaf3e1e17cd50daba5fdd0ac57eb5dda27ffe8954240b554` |
| `frames/w214-retrofit_escapade-reload-sample-20.png` | `14eefdba247a2032709fd16c474934e97e571872acbd1d0de87d218805763122` |
| `frames/w214-retrofit_escapade-reload-sample-25.png` | `f52f8b5434bf2587fc69c41a5640a35c4c990dedb1f81d58f9792173c7f5137e` |

### No-change hashes and SECOND handoff

- `scripts/generate_reload_w214_retrofit_escapade.py`: `93eb7a421906b9f63ffbc507c1ee485f8470c33839ac599f9a006779ac23e7fc` (unchanged).
- `art/weapons/w214/retrofit_escapade/profile.json`: `e68b2586c14cfc164ade93ac0e236cd68cf862f924e6f4b6a578c9e402170e37` (unchanged).
- Only `art/weapons/w214/retrofit_escapade/review.md` changes in this feedback turn. No generated outputs are returned or rematerialized.

Sequence status: master real original.blend evaluation ->61candidate -> FIRST Vision -> this image-backed justified no-change review are complete for this worker handoff. **SECOND Vision remains pending and final acceptance is not claimed.** Keep the existing worktree open. Master should carry the same product bytes into SECOND and inspect the hand/cover projected overlap in the13..16 FIRST bracket and the partly occluded charging-handle contact in19/20, plus return and ADS visibility. An additional synchronized angle/depth view would resolve contact better than adjusting source FK from a single screenshot. Mirrored/native grip coverage, all motion-between-capture clearance, sound and10..20display performance are not newly certified by this worker review. No source camera/mesh, weapon-exclusive selector, physical finger IK or continuous60fps interpolation is claimed.
