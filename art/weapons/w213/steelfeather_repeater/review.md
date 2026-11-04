# W213 Steelfeather Repeater — FIRST reviewed

FIRST native evidence reviewed; no warranted product correction. SECOND Vision remains pending master. This return changes only `art/weapons/w213/steelfeather_repeater/review.md` in the assigned worktree. Generator and profile bytes remain unchanged. Source FK, rest contacts, family framing and authored magazine motion are retained.

Worker read actual FIRST hip/ADS/reload sheets and raw reload samples 01, 05, 08, 11 and 15 with view_image at original resolution. Evidence root is `/private/tmp/destiny-w213-pass1-native`. Hip keeps the central view open and shows ordinary fingerless player-skin arms. The ADS sight aperture is clear. Raw01 begins the raise; raw05 shows extraction low and partly cropped at the lower edge; raw08 shows the detached black magazine beside the handling palm and receiver; raw11 shows the low return; raw15 restores a near-ready/hip orientation. Raw15 still identifies the dense reload model in capture metadata, so visual recovery at that still is distinct from the later canonical-model/ammunition restoration.

The low handling excursion warrants documentation, not a cosmetic lift, wrist pin, hidden support arm, source-motion attenuation or arm stretch. The original source chain already makes a large left-wrist excursion during extraction/exchange. At source p≈.333, the evaluated wrist-to-weapon displacement relative to idle is approximately 14 model units downward after the existing axis mapping and authored32 conversion, before display transforms. The source .4/.6 chain sheet likewise shows the handling bend and return toward .8/1. The weapon remains readable while the handling hand partly leaves the lower frame. These stills do not prove continuous palm contact or visibility of the entire magazine exchange, and the ARMATURE-only source has no camera/mesh with which to establish a different screen-space framing target. No source/contact evidence supports changing the current rest offsets or framing.

Capture/progress comparison uses sequence observation timestamps and neighboring server timeline polls; these are approximate brackets, not exact screenshot CMD values:

| Raw sample | Client tick before/after | Neighboring server progress polls | Visible result |
|---|---|---|---|
| 01 | 854/855 | .05 → .20 | Raise begins |
| 05 | 863/864 | .20 → .36666667 | Extraction low, partly cropped |
| 08 | 870/870 | .36666667 → .53333336 | Black magazine alongside handling palm/receiver |
| 11 | 877/877 | .53333336 → .70 | Low handling return |
| 15 | 886/887 | .85 → canonical inactive -1 | Near-ready orientation; capture still uses dense model |

Worker parsed all18 presentation rows in `oracles/w213-steelfeather_repeater-reload-timeline.json`. Active server ticks1340..1370 select `destiny:weapon_reload_w213_steelfeather_repeater/steelfeather_repeater` at progress .05, .20, .36666667, .53333336, .70 and .85, consistent with float32 grid60. `reloadDuration=37` stays unchanged. Tick1376 returns `destiny:weapon/steelfeather_repeater`, floats[0,-1], reloading=false, ammo49/0; subsequent rows retain that state. `reload-finished.json` confirms it at tick1445. Sequence capture metadata identifies the hands-overlaid W213 model during the reviewed samples. Server state, capture metadata and images support separate sampled route, visual-return and ammo-return findings; no exact frame/progress synchronization or60fps interpolation certification is inferred.

`native-validation.json` reports12 native sequences across the four-weapon master batch. Worker checked their recorded released=true and all-false nativeInput fields. Steelfeather has6 firing captures,41 reload captures,19 ADS captures and finishedAmmo49/0. Its sequence records releaseACK syntheticKeysCleared=true, leaseActive=false, heldKeys=[] and neutral movement input after release. `frames/w213-steelfeather_repeater-after-reload.json` also records the canonical hands route and released neutral state; `postflight.json` records batch-neutral input. Master operated the client and reports FIRST12 passed; worker only read existing evidence and did not run Vision, Computer Use, game inputs, shared builds or generators.

Budget correction: 89 weapon solids =85 body +4 moving. The earlier 537 figure (89 + a448 four-segment arm reserve) is a narrower candidate-bank estimate, **not** the master maximum over all emitted routes including arms. The master's integrated all-emitted-route maximum for Steelfeather is **687/1000 including arms**. This is master-provided integration evidence, not an independently rerun worker route audit. This clarification supersedes the broader budget wording in the unchanged candidate profile/generator metadata. Full/static and split representations remain alternatives, never summed together.

Read main AGENTS/RTK, weapon-art skill and Ace/Izanagi reference, exact W166 generator, current canonical89-solid model, twohand display, item graph, design, W201 contacts and W205 auto-rifle framing before drafting. Preserve sweeping silver body, dark action/box magazine, restrained gold trim, open sight/stock/guard, bored muzzle and blade; geometry and face UV remain exact. Only magazine core45, side bevels46/47 and floor48 detach. Magwell49 and gold trim50 remain on85-solid body despite their design magazine-group membership.

Original-source basis: master headlessly evaluated the original `.blend` in Blender5.4.0 Alpha. Worker read `/private/tmp/destiny-w213-source/source-review.json`, evaluated `auto_rifle_943c13a2.json`, original source/bone maps and the actual upper-chain PNG; the PNG was viewed again for FIRST review. Source contains ARMATURE only, no mesh/camera. Audited `Armature|fp_80A8A395_reload_full|Base`, OBSlot, source frames1..105 at30fps,61 evaluated poses, prior-cache joint error0; report allInputsUnchanged=true. Shared selector61CCE0D7 includes Halfdan, Ammit, Gnawing Hunger and Steelfeather, so395 remains an audited shared-family candidate rather than a weapon-exclusive selector. Source shoulders/elbows/wrists are present, ordinary forearms≈8.14136 and upper arms≈8.7266 model units at authored32 conversion; supplied action matrix endpoints match. Worker did not evaluate Blender or recover source mesh/camera.

Retain rest contacts right[8,8.22,8.25], left[7.8,8.78,-1.6], reload[7.35,7.65,3.3] and inherited rotations. Keep auto-rifle framing translation[-.65,.6,0], rotation[-1,2,0], scale.98. Profile retains sourceFullChain=true, keepMeshSupport=true, hideSupportAtRest=false, rigAction80A8A395, partHint moving and policy magazine. `source_palm_translations` transports REST mesh offsets plus original FK in the common weapon parent; reload.contact controls held-part alignment relative to that palm and is not a rest-palm correction.

Prior candidate checks remain recorded, not rerun for this documentation-only return: pure stdlib import/generate with no-write/no-external-execution audit hook; all10 W166 knots and .40..55 hold exact; geometry/UV and85+4 partition exact;61 strictly increasing float32(i/60) thresholds; native/twohand endpoints and non-FP displays exact; negative/endpoint/ADS/inspect/non-FP routes preserved; two in-memory calls byte-identical across248 absolute mapped outputs (247 pack JSONs + art manifest),247 non-self hashes checked. Representative .10 knot velocity matched left/right≈180.0018 deg/progress; maximum adjacent emitted Euler component delta4.56958 degrees. No old side-effectful generator was imported/executed. Master owns integration, source61/shoulders import, whitelist/runtime60, normal-length arm retargeting and materialization.

FIRST reviewed: retain product bytes with this evidence-based no-change record. SECOND Vision is pending master before final native acceptance. Partial lower-edge visibility remains explicitly recorded; no continuous contact, recovered camera, physical finger IK, listening or60fps claim is made.

Reviewed evidence SHA-256 (paths relative to the native evidence root unless absolute):

- `screenshots/steelfeather_repeater-review.png`: `a96895abafaff5823850da1b546a39dae1f52d3a795a934ccc851be2c8c46121`
- `screenshots/steelfeather_repeater-reload.png`: `b245af36b73e17c0ba6e7053ffdf3775cef02190867c0917d49d9c9664659341`
- `frames/w213-steelfeather_repeater-reload-sample-01.png`: `89dbda16c7ffe090cd909175837ae18aec9a99ec901acb3da09f601e1cdbbecc`
- `frames/w213-steelfeather_repeater-reload-sample-05.png`: `fdda93a210f7d2fe711833130cbce0d15bbc8527873707583b21ba4b3dceea43`
- `frames/w213-steelfeather_repeater-reload-sample-08.png`: `84b0f978b7d38c21a79ab06b4551e4e537eb4bdf6bc67335a931e90741164022`
- `frames/w213-steelfeather_repeater-reload-sample-11.png`: `09566ff8c6de200239e20c428758310a9666ed311512e0772ebbd84376360d1a`
- `frames/w213-steelfeather_repeater-reload-sample-15.png`: `707a510984a45fed8e78552b2180569b21c655f86db41da1e0701cb1fc71147e`
- `sequences/w213-steelfeather_repeater-reload.json`: `946b219090b380c8a524dd7569e2cc3cceb38bebcf77a8c62bd085935fdd2165`
- `oracles/w213-steelfeather_repeater-reload-timeline.json`: `e02ac8b332581a39c1be3936be715b276caccc21f9a8ee8f24f31df0a4806a1f`
- `oracles/w213-steelfeather_repeater-reload-finished.json`: `3edc26da96a0ca091789f33f6e8c50e3a72272444059cd602bb35eec9524b9a4`
- `frames/w213-steelfeather_repeater-after-reload.json`: `090a77b9568635e5e07eae7fe85d948efd0f3a93d927ff874b28f5c31f5ed391`
- `native-validation.json`: `e5dbafb2f51fe7b20b69a5df66584120eecab47eab915646ccc2f259049207cb`
- `postflight.json`: `979603d0f7b90265913e7ef943c1a52d4072be53599513d35becfeabbce98830`
- `/private/tmp/destiny-w213-source/source-review.json`: `cc9ef72c7c7e85936f3cf9bc1ad521a46cfac15c48e891412b1cc15685066d7f`
- `/private/tmp/destiny-w213-source/auto_rifle_943c13a2.json`: `f698e2e974a2f4a586857d8cd509f19da1603457c5c4cb5617651510288c1113`
- `/private/tmp/destiny-w213-source/sheets/auto_rifle_943c13a2-80A8A395-upper-chain.png`: `38d49d16466d5e15498ce2832f30eb80f45c7cdc393b7db2ca9871f12b28e0d3`

Preserved candidate file SHA-256:

- `scripts/generate_reload_w213_steelfeather_repeater.py`: `386e3ca5450a930ebd995451c5dc910c0f3f96043e2ac50abb7affb8998f0355`
- `art/weapons/w213/steelfeather_repeater/profile.json`: `744bc81ebe0f0d021eb8fac1a24ecea400fc5cf21a7771066bf5e6a82d4d8348`
