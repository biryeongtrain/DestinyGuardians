# W181 Seventh Seraph Officer Revolver FP reload

Preserve the canonical W136 Officer's long black vented shroud, silver muzzle/latches,
narrow brass chamber rim, raised rail/hood and swept perforated grip. The official
[Bungie default art, item 3037520408](https://www.bungie.net/common/destiny2_content/screenshots/3037520408.jpg)
was opened visually and checked against W31 SHA-256
`386a6d3061bda47461fc85650e8c9d8bcb013c53af7379ec2ac0f28fc7332d46`.
The accepted W136 clean model and atlas remain exact: 121 opaque cubes, 726 explicit
face UVs, zero triangle adapters, no additional geometry, no new texture or dye.

## Same-weapon motion evidence

[madmaxdrj Gaming: Seventh Seraph Officer Revolver with Timed Payload](https://www.youtube.com/watch?v=CT0EUpyTweM),
published 2022-01-05, 1280x720/60fps. The long vented shroud, hood/rail, rear fork,
rectangular brass-trimmed cylinder, underbarrel module and swept grip visually identify
the same Officer against the official art. Its alternate red/green shader is motion
evidence only; its paint, perks, player hand mesh and HUD timing are not transferred.
Original gameplay frames were decoded sequentially from the video, using frame n/60
as source time; final selection does not depend on approximate input seeking.

The 18.50-20.3333s **completed empty reload** shows presentation and cylinder swing,
steep muzzle-up open hold, lowering to support-hand/loader contact, closing flick,
and post-close hip recovery. The HUD changes 0 to 11 at loader contact. This is
an observation in uncontrolled footage, not a local ammo-credit or clock calibration.
The earlier 14.33-14.83s opening attempt is interrupted by dodge and was excluded
from the completion reference. Support-hand occlusion prevents measurement of the
exact hinge linkage, cylinder internals and loader stroke.

[comparison.png](comparison.png) pairs official default art with the canonical model,
then shows three oblique cameras with common framing for ready/open/loader/end,
the intact cylinder, and all four FP hand/grip combinations. [storyboard.png](storyboard.png)
pairs each real gameplay frame with the nearest authored sample. The render reads
emitted parent/display JSON and independently reconstructs Rx Ry Rz with NumPy;
it does not call the generator's pose or sampling routines. Face UV triangulation
and CPU rasterization are reused from the existing W123 Hammerhead helper only.
These are offline diagnostic images, with no hand mesh or native success claim.

## Product and mechanical boundaries

The two static parents are **111 fixed body + 10 cylinder cubes = 121 assembled**.
`magazine` is only the established composite suffix. It contains all canonical
`rear_chamber`, two bevels, underside, and six brass rim solids (source 72..81),
with every original field/UV preserved once. The whole cylinder rotates rigidly
about a longitudinal left-lower hinge. Rear frame, chamber bottom rail, shroud,
latches, underbarrel, sight and grip remain fixed to the receiver. There are no
pseudo shards, detached flat box replacements, scale fades, new cases or rounds.
The canonical solid cylinder does not have new chamber bores or a crane link.

Numeric 82-degree opening, pivot [7.25,10.56,4.32], grip origin [8,8.09,8.765],
body angles, smooth phase interpolation and 21 normalized samples are authored
adaptations of the observed action order. The open cylinder stays beside the frame
through the loader interval and closes before the final recovery. Constant uniform
scale and exact canonical endpoints apply to native/twohand in both FP hands.
The actual 26.3 ItemTransform left reflection is checked separately by JOML tests.

W168 Austringer and W169 Duke were studied for attached cylinder hinge algebra;
W180 Halfdan-D and Edge Transit supplied ownership, graph guard and independent
render conventions. No prior weapon's motion keys or reference sequence were used
as Officer evidence. The weapon-art skill and Ace/Izanagi study guided preservation
of clean semantic volumes, meaningful apertures and explicit UV detail.

The 87 pack files are two geometry parents, 84 parent/display children, and one
FP item graph. String0 ADS/inspect takes precedence, float1 chooses normalized
reload progress, boolean0 chooses twohand. Negative progress and every non-FP
context use the exact canonical item graph. Canonical ADS, inspect, ammo (11),
base reload (52 ticks), RPM (180), cadence, reload sound bytes and all mechanics
remain unchanged. Master owns routing/admission and shared runtime; this worker
adds neither a route nor a registry entry. Asset tests assert this owned graph
without requiring the shared route addition.

## Reproduction and pending native work

`python scripts/generate_reload_w181_seventh_seraph_officer_revolver.py --verify`
checks deterministic core assets and retained comparison/storyboard hashes without
raw-video availability. Add `--render --verify --evidence /private/tmp/w181-officer-report`
to regenerate and compare both images from retained real frames and official art.
Targeted Python unittest and `ReloadW181OfficerTest` cover graph/fallbacks, exact
partition/UV/paint, source hashes, rigid hinge motion and actual 26.3 cuboid/codec/
ItemTransform acceptance. Gradle configuration/evidence belongs outside source.

Pending master: route admission; native pack bake and both hands x both grips;
open/loader/close visibility, frame/rail clearance, near plane and real hand contact;
ADS/inspect and canonical non-FP observer checks; complete/cancel/swap/equip/death/
disconnect cleanup; partial/empty/full/no-reserve ammo credit and 52-tick base clock;
actual sound listening; short observation with 10-20 displayed weapons. No hand IK,
extracted bones, new third-person reload or native performance acceptance is claimed.
Raw video, original frames, intermediate scout sheets, logs and failures stay in
`/private/tmp/w181-officer-report`, outside product. Only the manifest's 94 paths
are owned; no central docs, shared runtime, routing, registry or HUD was edited.

## Frame provenance

Video SHA-256: `29642397a6df638fcf6b02bc732f131c3598dbeff98e976fa83aabc6374308c5`.
Metadata SHA-256: `3f5ceb515f469e7811c6cf28df00c10c298380865b016934b8b06311e74e01d4`.

| Frame | Source seconds | SHA-256 | Observation |
|---|---:|---|---|
| 1110 | 18.500000 | `9448b48bb5d28df1a93c506a4de5883acbd5581d83750b210671483fd34d010b` | Ready after emptying; Officer long shroud, raised rear sight, swept grip; source HUD 0. |
| 1120 | 18.666667 | `5cb7f97794122edb51de8756cac7f951d4c30060e5c953eb9750022338d715a8` | Initial roll and presentation before cylinder opening. |
| 1130 | 18.833333 | `18e0e45d957410c7bea2fd1acd2d3d918572e95675caccb7b0b52054e8da7804` | Complete cylinder swung to screen-left; circular rear face and chambers visible. |
| 1140 | 19.000000 | `74a6e877665b755de0055df023591b2adf15af47451738adbc17097eced6986b` | Muzzle rises with cylinder held open beside frame. |
| 1150 | 19.166667 | `66066565f693536d11b5f47cfd1e603e506bc33d10d146f0863ce0654fb22f4b` | Steep upright open-cylinder presentation, long shroud overhead. |
| 1160 | 19.333333 | `d640bf642368c52dbdffd1e47a6aa80a328fd7658fd934ec361613ebaca6db64` | Upright open hold; chamber and frame remain distinct. |
| 1170 | 19.500000 | `ae14ac2f7f62d2e104e9781ae0606bd4472c49bcd95d9863d77888a3112ffd03` | Lowering toward loader; open cylinder rear face visible. |
| 1180 | 19.666667 | `1c32b9140617745ab5f06937f50e2b10dab8c310ceab1131180d2c718755da8d` | Support hand and loader approach open cylinder rear face. |
| 1190 | 19.833333 | `2298829aac776cd0d91c8107d2c1ce41ffbc54ca4b5a91216d105096b3450d24` | Loader/hand contact obscures rear; source counter 0 to 11, not a local timing rule. |
| 1200 | 20.000000 | `4954a877f8af8906a77c9023c3be720f3fe426f851353150c348a3db3d64e6d9` | Closing wrist flick and recovery begin; cylinder reseated. |
| 1210 | 20.166667 | `f10e49e6f1d3f340d62b52740f9562b7d7c6eea9191ef77953a5a0dae52af539` | Brief post-close raised recovery with support hand leaving. |
| 1220 | 20.333333 | `5fcf841615fd98a36c131360e034763e81e9ca36f3ecff858f9583c4623e6653` | Ready hip restored after complete reload. |
