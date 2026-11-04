# Erentil FR4 W189 — lower-grip battery/cell reload

OFFLINE / NO HANDS / NOT NATIVE. Native acceptance is pending the master batch.

## Actual same-weapon evidence

[ThatUnknown, Destiny 2: PERFECT ERENTIL!!!! | Erentil FR4 PVP Gameplay Review](https://www.youtube.com/watch?v=539XTHi69Pg), uploaded2019-07-15. Actual gameplay downloaded to `/private/tmp/w189-erentil-report/review.mp4` and decoded with PyAV. Identity frame600 explicitly reads ERENTIL FR4. Continuous action8088..8166 is269.8696..272.4722seconds,30000/1001fps, timebase1/30000. Frame index below is zero-based decode order; PTS is the original decoded timestamp, not a guessed seek time. Video SHA-256 `fc99c4d06bab6e3b51c2b8fe7ecb5fc43f0d89043e79bdf3ae08422062fb50ae`; metadata SHA-256 `dc2b573ddc4db56cec70f805c9ce1a4c1e52814623ee6ac8e890b4616de4a002`.16 unaltered decoded frames are paired above authored samples in storyboard.png.

The sequence shows a muzzle-up rise, support hand reaching the lower grip, cell withdrawal, empty-seat pause, an incoming cell/hand from below-left, upward seating at the heel, support-hand release and lowering. Fixed receiver, parallel cylinders, hoses, triangular brace and grip remain together. The source has a silver shader and alternate round optic; these demonstrate the mechanism only. Local blue Omolon paint, open reflex, UVs and all source geometry remain canonical. The source HUD refills to2 from2reserve; this is not evidence for capacity2. Source movement/ability flashes and later sprint/ADS are excluded from the authored animation.

| Decoded frame | PTS | Seconds | Actual observation | PNG SHA-256 |
|---|---|---|---|---|
| 600 | 600600 | 20.020000 | Inventory explicitly ERENTIL FR4; triangular grip frame, parallel cylinders, bottom grip cell. Alternate round optic and silver shader are mechanism evidence only. | `9582125023323cb2fac7e4ef2b51b93905959e20161a5ef408082938e554c15a` |
| 8088 | 8096088 | 269.869600 | Final hip shot and ability flash precede reload; authored zero returns exact canonical hip. | `3c60bfa39d3356fc25dfb2bc440596908972adf124f506d8dcb180e2e30e6d66` |
| 8097 | 8105097 | 270.169900 | Weapon rises and rolls muzzle-up at screen right; support hand leaves forward hold. | `8e5abbf909d6f45778a86e0198ab897e7f1ca143927f3132234a89fd615344ad` |
| 8100 | 8108100 | 270.270000 | Steep rifle with triangular grip opening exposed; support hand reaches heel cell. | `b39369e168f4a62e1c1a6a37600ef5e144bf7b2cd68979bd6a94c924d96c20f5` |
| 8106 | 8114106 | 270.470200 | Support fingers draw cell from lower grip; receiver, cylinders, hoses and triangular brace remain together. | `bf4a3f632831080342faa28eb6b68f16ec35a4ccb7768e6da9d5e42cf168ce5f` |
| 8109 | 8117109 | 270.570300 | Outgoing cell withdrawal continues along lower grip direction; fixed grip remains intact. | `625d03fadf3abe3cdf6d63b71f27c9ed1a4f701b876efb0f53c043d75c42c7ab` |
| 8112 | 8120112 | 270.670400 | Lower cell has cleared the grip seat; support hand and payload travel below-left. | `624ce92612ce468374c4b3b3473b1c2bc12b71ae3f0031b0d9b8d062819d349a` |
| 8118 | 8126118 | 270.870600 | Empty-seat dwell, steep weapon; no receiver, rail or cylinder becomes ammunition. | `fcd53ff7796a95b540b3eb52b9fac45cbe9057421b23c67c8220636f14f9dd15` |
| 8124 | 8132124 | 271.070800 | Exchange dwell; support hand begins returning from below. | `3a34278d6d3af1c08ccf58d40b650bf95870d927fe3556c0e18e56d09d779ec7` |
| 8130 | 8138130 | 271.271000 | Incoming hand/cell below-left of heel; rifle briefly relaxes its steep pitch. | `bf718d7f78aad60947e1971ca2939d5a3c9b0c137bcd7711ba4eccc1cd7b18c5` |
| 8136 | 8144136 | 271.471200 | Support hand raises replacement into lower grip, slender cell follows grip insertion axis. | `5278ed946438b3506127fe6f6d33d79c728a96c56b71c4abf60009b684124a03` |
| 8142 | 8150142 | 271.671400 | Palm seats cell upward at heel; HUD now shows2 because reserve was2, not local capacity. | `80d7f0ac0459c9bdfe822595c630bd0a47db45e19f841c562d78c6e89cdfdbd5` |
| 8148 | 8156148 | 271.871600 | Support fingers release the seated heel; rifle still muzzle-up. | `cdca9999644fc28ab581f08a1e80d11b127db8b77197d16c183f52066ede1b1f` |
| 8154 | 8162154 | 272.071800 | Support hand reaches forward while rifle lowers; no separate bolt/coil cycle. | `a4fb81ed247c4d1b3d22faba11a89494a6066dd9ee45e58c68ba8f938f05a2b1` |
| 8160 | 8168160 | 272.272000 | Return to held posture; authored endpoint restores original hip transform. | `f4c4260ff453ca3d44a82a76ba024c68cf007366e1a2dc97a4f9562e92a81921` |
| 8166 | 8174166 | 272.472200 | Reload recovery boundary. Later sprint/ADS is excluded from the authored endpoint. | `4370f624fd67c060ec719c9916d51d59abd4f8d390e0cb2e778fdcb9daf7014d` |

## Inert original rip and part mapping

The original binary FBX7500 `/tmp/destiny-weapons-w30/raw/erentil_fr4/extracted/Erentil FR4/Erentil FR4.fbx` was parsed read-only using the existing inert FBX parser in `scripts/generate_surface_w123_erentil_fr4.py`. No embedded rip script, DCC application, extracted bones or source animation was executed. External raw inspection is `/private/tmp/w189-erentil-report/rip-inspection.json` and raw/canonical inspection is `rip-preview.png` in that directory. Original SHA-256 and coordinates are retained in manifest.json.

`8D2EEB80_Group0_Index0_0_GripStock0`:328vertices/336triangles; native bounds `[7.304582,3.700629,.827771]..[8.695420,5.609437,5.470086]`. This is a separate narrow lower-grip/heel assembly with a raised insertion ridge. It is spatial evidence for the existing `Cartridge_base` index16, not a named ammunition/bone assignment recovered from the rip. Gameplay supplies the moving-part evidence. Original `Grip_heel` index14, `Triangle_lower_brace` index13 and main grip stay fixed; forward reservoirs/capacitors/rails/hoses never serve as ammunition. This mapping is intentionally more specific than choosing all parts near the cell.

Canonical source `weapon_surface_w123/erentil_fr4.json`:135cuboids/810face UVs. Body134 unchanged cuboids +original heel1 unchanged cuboid. The articulated cell adds1 rigid inner sleeve into the grip, using the original heel's existing face UVs. Sleeve width.76,length3.1,depth.64,16.970743degree X orientation. It intersects the heel, follows the grip axis, stays inside the grip when seated, and becomes visible on extraction. The raw heel has an insertion ridge, but exact concealed sleeve dimensions and appearance are independently authored. **Full hidden-payload source fidelity is not claimed.** Assembled maximum136 emitted cuboids,0triangle adapters; canonical endpoints135. Existing model/texture files are not edited.

## Sourced versus independently authored

| Supported by decoded same-weapon frames/rip | Independently authored implementation |
|---|---|
| Steep rise and lower-grip withdrawal; fixed triangle/cylinders | Pivot[8,8.15,2.88], numeric angles and grip-axis withdrawal vectors |
| Empty-seat pause and incoming hand/cell from below-left | Smoothstep phase keys, leftward transfer arc, omitted payload at samples8..10 |
| Upward cell insertion then palm seating/release | Alignment at.69, slight compression at.74, full seating by.80 |
| Return toward held posture | Exact canonical zero/one endpoints, normalized50tick duration |
| Separate raw lower-grip heel assembly | Existing canonical heel plus1 concealed sleeve; hidden profile not recovered |
| Source camera retains lower grip at screen right | Positive common FP lift and bounded camera proxy; absolute pose and native hand fit not recovered |

The13 keyframes were authored for this Erentil sequence. W188 Line in the Sand supplied only matrix composition, item graph, parser/JOML and raster scaffolding. Its trajectory, magazine indices, pivot, contacts, timings and numeric framing were not reused. Erentil is a grip-cell mechanism, not an underside receiver battery. All21 samples are shared between native/two_hand grips through the accepted carrier transform and are evaluated for both FP hands with left-hand reflection. Constant scale prevents disappearing payload through shrink tricks.

`comparison.png` shows canonical side/front/reverse/rear views,8temporal samples at one fixed camera+extent, both grips/hands at.65, and emitted whole cell beside a neutral original raw heel. Each grip/hand comparison uses an extent fixed over all21 samples. No native hands are drawn. `storyboard.png` shows16 actual decoded source frames over corresponding authored frames with PTS. Orthographic framing assists mechanism inspection and is not native viewport proof.

The manifest also has46 practical-screen anchor checks over.20..80, including lower seat and visible cell in both hands. Conventional held-camera proxy assumptions: offset(+/-.56,-.52,-.72),70degree vertical FOV,16:9; both accepted grips normalize to native before this proxy. Safety margin6percent. These prevent the prior infrastructure pattern of negative-Y lowering the exchange out of sight; they do not certify the actual server two_hand carrier or hand fit. Native viewport acceptance belongs to the master's integrated session.

## Guards, integration and unchanged numbers

Owned item `destiny:weapon_reload_w189_erentil_fr4/erentil_fr4` consumes float[1]progress,boolean[0]grip,string[0]ads/inspect.21samples per grip,84display children +2parents +1itemgraph =87pack assets. Negative/zero/exactone/overshoot fall back to original graph; nonFP contexts and ADS/inspect explicitly bypass reload. Children0/20 preserve exact canonical displays; every nonFP display and every scale is unchanged. The master owns registry admission/routing and central lifecycle tests; worker edits none of those shared files.

Actual local source remains capacity5,reload50ticks,charge20ticks,chargeMillis967,cadence11.666666666667ticks,burstSize5,burstSpacing.666666666667ticks,sharedBurstAmmo=true,shellReload=false; all audio resources and gameplay data are unchanged.21normalized visual samples at2.5tick spacing do not impose source clip duration on gameplay. The [user DDC spreadsheet](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4) remains numeric priority; basic/enhanced/PvE/PvP stay separate and `?` uncertainty is preserved. This model-only work applies no numeric delta and claims no new spreadsheet audit or inferred enhancement/PvP values.

Targeted tests: owned Python/generator verification plus five actual26.3 CuboidModel/ItemModels codec/ItemTransform+JOML JUnit methods through private copied Java25 jars, classes/logs outside source. No Gradle/dependency builds, shared outputs, server/client/CU/Vision/native input, live audio listening or performance certification. The design skill and required Ace/Izanagi study were read: semantic moving part, unchanged detailed face UV, meaningful volume,136 well below1000limit; no new surface redesign.

Master native queue: admit erentil_fr4 to this item; pack load; both grips and FP hands through21samples with close inspection at.20/.35/.55/.65/.75 for seat/cell viewport and hand contact; zero/one/negative/overshoot and ADS/inspect/nonFP; partial/empty/no reserve, completion/cancel/switch/equip/death/disconnect; verify original reload/charge/burst audio; observe10-20displays. Native success, hand IK, recovered bones/animation and third-person reload are not claimed.
