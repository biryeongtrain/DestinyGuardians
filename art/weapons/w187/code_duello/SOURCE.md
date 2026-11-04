# Code Duello W187 — source-led first-person reload

Actual same-weapon source: [Marcusbgaming — How to get Code Duello Rocket Launcher and God Roll opinions](https://www.youtube.com/watch?v=tXfSro7b6y0), uploaded 2021-02-18. Original gameplay was researched and the actual frames inspected before motion authoring. n900 inventory identifies CODE DUELLO; n774..858 is a continuous empty-to-one reload. Source uses blue shader; original canonical W123 teal/gold paint and atlas remain unchanged.

Observed sequence: right-edge near-vertical rise; support hand around long ribbed canister; whole canister lifts axially from rear socket, exposing brass connector; offscreen exchange; connector-first replacement into same socket; hand releases and launcher lowers. The complete canonical forward canister is56 solids: indices0..25,35..45,53..63,71..78. Static rear socket/teal collar, rear tube, side rails/fins, grip, optic and trigger remain in161-solid body. A breech band alone is not ammunition. The full rigid canister includes long tube, heart, mouth/throat/lip, both ridge rows and gold connector band.

Two added reload-only intersecting prisms represent the short rear brass connector visible n802 and n826, using existing gold-band face UV and atlas. Dimensions0.64x0.64x1.30, seat/pivot, normalized phases and all numeric poses are individually authored; no bone or animation extraction. Connector sits entirely inside canonical Rear_solid_heart. Canonical217 solids/1302 faces, element rotations, UVs, paint, display scales, ADS/inspect and source files are byte-preserved. Active assembly161+58=219<=1000; endpoint original graph217. One assembly represents outgoing/incoming canister; no separately animated rocket inside it is claimed. No additional independent part was established from inspected footage.

Limitations: support hand and frame edge obscure parts of exchange; exact hidden connector profile, native hand contact, and true open socket interior are unverified. Canonical Rear_solid_heart stays filled, so an exact hollow chamber is not reconstructed. The model is an individually authored approximation of the observed same-weapon canister mechanism. Body global presentation moves; its161 fixed solids do not articulate relative to one another.

API: destiny:weapon_reload_w187_code_duello/code_duello; float[1] progress0..1, flag[0] native/twohand;21 samples every3.35ticks; both first-person hands. Exact0/1 uses complete original canonical item graph; negative/nonFP/ADS/inspect fallback also original. Product67ticks,1rocket,15RPM/cadence80, audio and ammo untouched. Master owns common routing/admission/lifecycle, actual GT, pack/native/CU/Vision and10-20weapon gate. API readiness is also outside repo at /private/tmp/w187-code-report/API-readiness.json.

W185 generator, Python tests, actual26.3 CuboidModel parser/ItemModels codec/ItemTransform/JOML test infrastructure and W123 offline rasterizer are reused. The motion, pivot, axis, phases and connector dimensions are independently authored for Code Duello. `python -B scripts/generate_reload_w187_code_duello.py --verify` reads retained output PNG hashes and canonical/source files only: no external media and no /tmp ownership-manifest requirement. `--render --evidence /private/tmp/w187-code-report` deliberately requires original16 source PNGs and checks their hashes.

comparison.png and storyboard.png are explicitly OFFLINE / NO HANDS / NOT NATIVE. Storyboard includes actual source images above separately framed offline no-hands renders; image labels distinguish both. These images do not demonstrate native hand fit, runtime route, audio, server success or performance. Offline test results and export report remain outside repo.

Exact original source video: /private/tmp/w187-code-report/original.mp4
Metadata: /private/tmp/w187-code-report/original.info.json
Video SHA256: 72d345e7589331fe1559e5ab009f6992ad1ca18e303f614b2c9de3b7eccbd7d9
Metadata SHA256: e8f688f15078fc9bd7e2744bd49fec65aa415318d339b265e9eeecd44ad9ceab
Actual CFR30000/1001fps, original timebase1/30000. PTS=n*1001; exact timestamp seconds=PTS/30000.16 representative full-resolution unscaled/unannotated extracted PNGs outside repo; SHA256 below. Contact sheets are separate derivatives.

| Frame n | PTS | Seconds | External PNG | SHA256 | Observation |
|---|---|---|---|---|---|
| 774 | 774774 | 25.825800000 | /private/tmp/w187-code-report/action-01.png | b8a01fac09184e3cf03b72635afb96ec29471b715bf4f794039b417fa980e9d2 | Empty hip hold after shot; reload begins. |
| 780 | 780780 | 26.026000000 | /private/tmp/w187-code-report/action-02.png | 18710e0373c2ba8d03a4dd6b389fc38d42cb4fd5df71dd03ec7a228f2531b410 | Launcher dips before right-edge rise. |
| 786 | 786786 | 26.226200000 | /private/tmp/w187-code-report/action-03.png | d8f05d94d31b5b8444d23f0d3f25198072caab714c43f82daa5bb30221d69f2c | Long ribbed canister rises nearly vertical; hand encloses it. |
| 792 | 792792 | 26.426400000 | /private/tmp/w187-code-report/action-04.png | d07a9d5701bbd1040babdde3f095ac634eb133c040c4e592c0b3b41d8fc7a9ad | Support grip stays on complete ribbed canister. |
| 798 | 798798 | 26.626600000 | /private/tmp/w187-code-report/action-05.png | d9e87d311293fa6a579ea6e47a5397739909335152ac4ae84bf4df48ab6f1f98 | Canister begins axial lift from rear socket. |
| 802 | 802802 | 26.760066667 | /private/tmp/w187-code-report/action-06.png | 8d8e64f6598305d51395f7051fed2abd7d8a2fc48758fa1e69432952968a46a2 | Brass connector exposed between canister and socket. |
| 806 | 806806 | 26.893533333 | /private/tmp/w187-code-report/action-07.png | 735584d0bace814e7a8e3c8e25510d4cd4d613cbd17a1ee94feee73cf5765157 | Whole canister clears socket, moving upward beyond screen. |
| 814 | 814814 | 27.160466667 | /private/tmp/w187-code-report/action-08.png | b974e72520f3b490c6aef208a8635fbaf05827859b7b6f4d247487cb2c03fef0 | Rear circular socket remains with long side rail fixed. |
| 822 | 822822 | 27.427400000 | /private/tmp/w187-code-report/action-09.png | ba34c307c6d80a8dba529dd8d38a7ece95d42a998bc2eec947d987409d0dd2eb | Empty socket at low right; incoming canister is above screen. |
| 826 | 826826 | 27.560866667 | /private/tmp/w187-code-report/action-10.png | 12f68dfb54f779316bf2f912d7d4732522a7c688ba33d582269eff96d0bbb2a3 | Incoming complete canister connector enters at upper right. |
| 830 | 830830 | 27.694333333 | /private/tmp/w187-code-report/action-11.png | f9f7e45cd52f2b17394ff3c3d63485b7136d3888680b572973e96d458b8435ba | Long ribbed canister aligns with socket, hand supports its length. |
| 834 | 834834 | 27.827800000 | /private/tmp/w187-code-report/action-12.png | d4e3c56cd97e689161f86c333a04e53c87d526a9f208a63ba7ac5c97e8719bc0 | Canister seated; source HUD updates0->1. |
| 840 | 840840 | 28.028000000 | /private/tmp/w187-code-report/action-13.png | 5191fcde93541b3f810aa90538df5a24a641d5ba0525916cb65816f95b7ad46c | Support hand releases seated canister. |
| 850 | 850850 | 28.361666667 | /private/tmp/w187-code-report/action-14.png | 1ec6ae722c0cedeed7d460bf960ab63660ff8f70c3070e7e0d252077ded943fb | Launcher lowering toward hip. |
| 858 | 858858 | 28.628600000 | /private/tmp/w187-code-report/action-15.png | 0f4c76a5f2dc250956ec37b5d2a73d615d5770a145cf10ca0e2e06e2c4d4af0b | Return near hip orientation. |
| 900 | 900900 | 30.030000000 | /private/tmp/w187-code-report/action-16.png | 86eb5796ac788be29b636d501f4e736674c50ff6ac71ccedeed03c69c22726ec | Inventory overlay explicitly identifies CODE DUELLO. |

Rejected reference: Utepers cNzGk3TNCi0 (2021-01-24) shows other weapons and predates Code Duello; excluded from motion/provenance. Only Marcusbgaming same-weapon frames support this work.

## Revision2 — raised socket framing correction (offline pending native retest)

Master-supplied initial native images were inspected before this correction: /private/tmp/destiny-w187-native/reviews/rocket-native-sheet-initial.png; native sample05/14 and two_hand sample14. Source n806/814 retains the socket lower-right, while initial native high-pitch body/socket goes offscreen. Initial94 files were verified byte-identical to integrated initial export and their exact BEFORE hashes saved at /private/tmp/w187-code-correction/before94.json before editing.

Only the common display-space shift is corrected, by an authored high-phase delta[-2,-3.5,-6.5] with smoothstep entry/exit weights[0,.18,1,1,1,1,1,1,1,1,1,.45,.05,0] at the existing key times. This is a first authored native-defect response, not a measured source pose or confirmed native calibration. Both body and canister receive the same correction, carried into the accepted twohand transform; extraction axis, mechanism, rotations, pivot, relative canister motion, geometry/UV/paint, scale, timing/ammo/audio, and exact original0/1/nonFP/ADS/inspect graphs stay unchanged.

Corrected comparison adds a representative p=.45 BEFORE/CORRECTED row using a fixed orthographic camera and shared extent to avoid auto-framing away the translation difference. Storyboard is regenerated from corrected transforms and original16 hashed source frames. These remain OFFLINE/no-hands, and cannot establish native socket visibility. Master owns actual calibration/retest. Manual correction delta with BEFORE/AFTER SHA256 is under /private/tmp/w187-code-correction; the initial export is preserved.
