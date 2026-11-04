# W183 Patron of Lost Causes reload source

Same weapon original gameplay actually inspected before authoring motion: TheGamesEntertainer,
Destiny 2 Season of Dawn Unlock Fast Rifle Reload Mod Use on New Scout Patron of Lost Causes,
2019-12-20, https://www.youtube.com/watch?v=SLB49l1oUmA . Inventory nameplate at18.018s
shows PATRON OF LOST CAUSES and the same long upper casing, narrow scope, gold tubes,
open triangular rear stock and hanging forward hook as canonical W130. Default paint and
local original scope are preserved exactly; backlit dark gameplay is not a replacement shader.
Actual empty reload examined at211.7115-212.7125s, with context211.5113-212.9127s.
Source enhanced rifle loader/perks affect source speed; local timing remains39ticks,
magazine15, RPM200, cadence6ticks, burst1 and unchanged original reload sound.

Observed order: support hand leaves forward contact -> receiver swings muzzle nearly
vertical at the right screen edge -> exchange at bullpup rear underside -> magazine seated
(HUD0/109 ->15/94 at212.3121s) -> receiver lowers rapidly -> support hand opens and
moves forward -> small low overshoot -> hip recovery. No independently measurable
bolt/charging-handle stroke is established; canonical exposed_bolt/charging_stem/charging_knob
remain rigid with body. Camera movement, hand occlusion and backlighting prevent recovering bones.

Canonical partition: indices82 magazine_body and83 magazine_floor, rotated-8degX,
form the complete broad rear bullpup magazine behind pistol grip under the rear action.
Both move together. Body is indices0..81 and84..97 (96elements). This is semantic part
identity grounded in named canonical solids and original inventory/action location, not
arbitrary connected noise. All98 original geometry/UV/rotation/texture records and
588 face UVs are copied exactly once.0 new elements/0 triangle adapters; assembled98<=1000.
Original stock air, grip, front hook, scope, gold tube and XIV paint remain intact.
Preserving canonical geometry also preserves its simplified filled mating surfaces; no
new hollow socket or internal mechanism is invented.

Numeric poses are AUTHORED: pivot[8,7.65,8.8], rear magazine anchor[8,8.25,12.14],
peak lift82degX/-17degY/-13degZ and hidden local withdrawal[-.25,-5.8,.815].
The withdrawal approximately follows canonical-8degX slant. Exact hidden exchange path,
small seat rock, normalized knots and smooth interpolation are authored, not measured animation.
One intact magazine proxies outgoing/incoming while occluded; no duplicate/spent bullet/ejection,
scale hiding, unsupported bolt motion, hand IK, extracted animation/bones or new3P reload.
Both FP contexts and both existing grip displays use a rigid pivot/carrier;0/1 are exact
canonical displays. ADS/inspect, negative progress and nonFP use exact original item graph.

Read-only reuse of W182 Antiope generator rigid matrix algebra, graph guard and preview
layout; dedicated Patron keys, rear partition, pivot, extraction direction and chronology.
Beloved raster reads canonical XYZ cuboids. comparison.png is offline emitted-JSON reconstruction
at representative obliques and both grips/hands; storyboard.png pairs ACTUAL retained frames
with AUTHORED offline poses. Neither is native. Master owns shared routing/admission/runtime,
central tests, held framing/hand contact, full ammo/cancel lifecycle, sound listening and
a brief10-20weapon native observation. All native checks remain pending.

Source clips/metadata/raw PNGs retained outside worktree at /private/tmp/w183-patron-report.
First candidate NNPZYB6IcUM contained firing only, so it was excluded from motion evidence.
Exact decoded frames selected without seek; source frame_rate60000/1001, time_base1/60000,
frame duration1001PTS confirmed by ffmpeg showinfo. PTS=n*1001, seconds=PTS/60000.

Video SHA256 `9787ea62b2df878e8f83cd80e2fc8532611d9b97f3fe72d9a114f79fba33629e`
Metadata SHA256 `945823edc26d8e03ccf4d2cc1f289dab8e9324da8a87456a61519d18b1d6d0a4`

- reference-01.png: n=1080, PTS=1081080, t=18.0180s; SHA256 `e796c5d1ac1531212e6d2e73e74e0486b882879d4ea2098c1e8b4fe11a41d189`. Inventory PATRON OF LOST CAUSES nameplate, long silver casing, narrow optic, gold barrel/internal tube, black open triangular stock and forward underside hook. Identity only.
- reference-02.png: n=12678, PTS=12690678, t=211.5113s; SHA256 `6a90b084fb64e7d1df3a1b61b726a8a5877248c4947105948e9b8e84fc0cf29e`. Empty HUD0 after firing; receiver near hip before reload.
- reference-03.png: n=12684, PTS=12696684, t=211.6114s; SHA256 `f08b499bb3740524fb1985d8a6424d033b6e4f9f44593f5c15be535c96cc19d3`. Empty HUD0, support hand still forward; pre-lift.
- reference-04.png: n=12690, PTS=12702690, t=211.7115s; SHA256 `22cb1aa4115079ae7b9a47a85589b40398a3b7271903170162a5b4f64e63b7bf`. Reload onset: support hand leaves forward contact toward rear magazine.
- reference-05.png: n=12696, PTS=12708696, t=211.8116s; SHA256 `280d208459f5373b9a9a798631e00b943c7b9147cc07a83922465108fd13abb3`. Support hand reaches toward bullpup rear underside as receiver begins rising.
- reference-06.png: n=12702, PTS=12714702, t=211.9117s; SHA256 `ff8276c766e9e76124f4e9c7f0e9e2ac91e9829347f2671da9c68d0d2ab0966c`. Steep muzzle-up lift at right edge; rear stock and rear magazine region presented.
- reference-07.png: n=12708, PTS=12720708, t=212.0118s; SHA256 `4cd5b608f6e445c847bd602180541dddfb34bf439444b112acded9123447538e`. Near-vertical receiver hold; hand/screen edge occludes outgoing magazine exchange.
- reference-08.png: n=12714, PTS=12726714, t=212.1119s; SHA256 `dbf8402c564b9f13c06e1039f7308704472f2214027ff586ec3307b472fd8313`. Steep hold continues; support hand returning beneath rear magazine socket.
- reference-09.png: n=12720, PTS=12732720, t=212.2120s; SHA256 `ea40db67c0b6f7fc290b63c2a9e03d9c1b9461659d5bb7921c311310ce24b0d7`. Replacement approach at rear underside; hand partly covers magazine body.
- reference-10.png: n=12726, PTS=12738726, t=212.3121s; SHA256 `545e8d5a75e2fb57a4ed9406ed84615dc795b082a9343fc31ef56bdf6364fc10`. Magazine seated: HUD15/reserve94; support hand begins opening under stock.
- reference-11.png: n=12732, PTS=12744732, t=212.4122s; SHA256 `ee9ddaf9c06ac74b1f5c48ed6e6710340d640cc8502b0c5b80233d36886149e0`. Receiver lowers sharply; support hand moves forward along body. No isolated bolt stroke measurable.
- reference-12.png: n=12738, PTS=12750738, t=212.5123s; SHA256 `f1f0a56cae76a3fce5ced77a208347eea1cf0669ec0576a7e50b290ee4c2f6ef`. Receiver near hip; support palm continues forward recovery.
- reference-13.png: n=12744, PTS=12756744, t=212.6124s; SHA256 `9dc1e95c2f098480b509d1c0ac7e5204eea6aba1c4bbba105f59715c6b6261d6`. Small low overshoot after rapid lowering; magazine seated.
- reference-14.png: n=12750, PTS=12762750, t=212.7125s; SHA256 `97c41c456b1b5a505deed980ce859964631792b946cde22e0432ad3b3a7d6daf`. Hip recovery with open support fingers leaving sight line.
- reference-15.png: n=12756, PTS=12768756, t=212.8126s; SHA256 `aefbdf5c0d094476e01dfdd245c379f3250db7d8734d2543b68bdfbcf12c0a41`. Ready hip silhouette recovered, complete magazine seated.
- reference-16.png: n=12762, PTS=12774762, t=212.9127s; SHA256 `9f9024473ee720b4e63f92581145b647b1e351503477a741149930d87f563532`. Post-reload ready hip; same scope and receiver.
