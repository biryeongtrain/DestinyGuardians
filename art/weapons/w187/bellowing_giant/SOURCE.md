# Bellowing Giant W187 source and authorship

Actual same-weapon reference: [The Silent Noob — Destiny 2 Forsaken: Black Armory Rocket Launcher Bellowing Giant curated roll](https://www.youtube.com/watch?v=DemrVvcFFjI), uploaded 2018-12-23. Inventory n600 identifies BELLOWING GIANT, capacity1, red jacket/silver stripes, graphite shoulder sleeve and open ring. Continuous reload n2940..3130 (49.049..52.218833 seconds) was inspected before motion was authored. The video is 60000/1001 fps, timebase1/60000; PTS=n*1001, confirmed by FFmpeg showinfo. Exact frames remain full-size, unaltered outside repository. Enhanced analytical crops are separate and not source originals.

Observed: launcher dips/inward rolls and turns the open front muzzle toward the camera. Support hand brings a whole dark rocket from the right, aligns and presses it along the muzzle axis. The payload progressively disappears inside the tube; palm releases, launcher rolls rapidly forward/down and settles. HUD0 becomes1 during seating. No outgoing live rocket, detachable breech band, independent bolt or latch is resolved. Combat effects and hand silhouettes obscure the precise rocket profile. A coherent16-element reload-only rocket is authored from the visible long body/tail silhouette; its nose, dimensions, face UV and exact path are approximations, not measured bone transforms.

All114 canonical W123 elements,684 face records, rotations, UV, paint atlas and displays remain exact on the carrier. Reload-only graphite payload borrows canonical stock-core face UV for material continuity without moving any stock geometry. One connected rigid assembly comprises long octagonal shell/core, two-step nose, tail neck and four shallow stabilizers. Entire seated envelope lies inside canonical Launch_chamber_heart8. It is visible only samples7..13, so there is no false extraction phase or early rocket flying outward. No scaling disappearance: constant accepted scale; graph omits the payload outside incoming/seat. Maximum assembled elements130; endpoint114; no triangle adapters.

Authoring reuses W185 generator/graph/pivot matrix transport, Python contract test patterns, actual26.3 CuboidModel parser, ItemModels codec, parsed ItemTransform/JOML checks and W123 offline rasterizer only. The14 numeric phase keys, grip pivot and rocket shape/path are individually authored for this observed reload. No W185 trajectory, extracted bones/animation, imported rig, hand mesh or IK.

Contract: destiny:weapon_reload_w187_bellowing_giant/bellowing_giant;21 samples; float[1] progress, flag[0] native/twohand; both FP contexts. Exact0/1 use original full canonical graph. Negative, ADS, inspect and nonFP preserve original. Capacity1/reload64ticks/cadence60ticks/existing timing/audio/ammo remain unchanged; source footage clock and perks do not alter gameplay. Master owns common routing/admission/lifecycle and actualGT.

comparison.png and authored storyboard panels are explicitly OFFLINE / NO HANDS / NOT NATIVE. Source panels in storyboard show actual Destiny gameplay, not Minecraft execution. Offline views use independent orthographic framing; they are not camera/bone recovery. Actual Minecraft hand contact, native framing, cancellation/lifecycle, pack loading, audio listening and10-20 display observations remain unverified and master-owned. No exhaustive all-angle/FPS gate claimed.

Generator --verify uses repository files and stdlib only, with no source media or /tmp ownership manifest access. --render requires Pillow/NumPy and the explicitly retained frames. Reports/caches/media stay at /private/tmp/w187-bellowing-report; exact94 export at /private/tmp/w187-bellowing-export.

Source MP4: `/private/tmp/w187-bellowing-report/original.mp4` SHA256 `11f99557b571d1d98435142d86d64eb8d3dfba1316c6c0e3aaa6f4bb7428d728`.

Metadata: `/private/tmp/w187-bellowing-report/original.info.json` SHA256 `593eddece0e2ec0598944ddd66d7d32996a46af9f44a1aec4b2aa5d604527490`.

| Source frame | PTS | Seconds | SHA256 | Observation |
|---|---|---|---|---|
| 600 | 600600 | 10.01000000 | d1bc9c3bf545f717d19e867c7a39b694535b08e73b4ae1a3ba0d98b3566cc20e | Inventory explicitly BELLOWING GIANT, matching red launch jacket, silver longitudinal stripes, graphite stock and open side ring. Magazine1. |
| 2940 | 2942940 | 49.04900000 | 072ebe39fcdef1efafd67deb110986d000ac6d86052ce40f14d5070231cad089 | Hip launcher after shot, HUD0; view movement and outgoing flash are gameplay, not reload geometry. |
| 2960 | 2962960 | 49.38266667 | cef7ce857494c8e3b6d622262192581a8243eab6db89001c12fe45946b37b41c | Support hand sweeps across foreground as launcher begins inward/upward presentation. |
| 2990 | 2992990 | 49.88316667 | 30616c8488fa19eaacbd2e4f0dde66fdab7812e919a9eb26aa7cc4f58b398c60 | Launcher rolls; round open muzzle rises from lower right and presents toward camera. |
| 3010 | 3013010 | 50.21683333 | 29f208bbcb994eda98a4632dcda7bcc3d219eb1519fe2227ff98cb32eb68fb28 | Muzzle front ring fully exposed at lower right; red jacket and fixed foregrip stay with tube. |
| 3020 | 3023020 | 50.38366667 | 67dc45b562aeaa97d6b2c9bc002f36b9719fb370e181aae8dc048abfbce1eee1 | Incoming dark rocket/cartridge begins entering from screen right beside open muzzle; hand partly conceals its body. |
| 3030 | 3033030 | 50.55050000 | 8c23b18ae5d516bf5dc7b02aa818be23e939616fa22f33a842347b1e8d0ebec8 | Whole incoming payload is held above/right of tube; long axis distinct from launcher, no detachable breech band. |
| 3040 | 3043040 | 50.71733333 | b2e83db75c20646d1e7305f485f4c93dd6ca41c31ae187e665346d4b9aacaacc | Payload aligns over front muzzle. Tail/hand silhouette visible right; bright combat effects obscure small surfaces. |
| 3050 | 3053050 | 50.88416667 | 4af465aa46a42295ba311fe7c90f4a9cba91f159b29e50e187edc45ef2cd44fd | Hand moves payload down into open muzzle; rocket front/neck occluded by tube. HUD becomes1. |
| 3060 | 3063060 | 51.05100000 | 680cd827ca6a07f0a24f22e64cce7cfdb12133d1dfa681dd44fb6bf0fbe9d0c0 | Support palm pushes down along muzzle axis; full rocket progressively disappears into tube. |
| 3070 | 3073070 | 51.21783333 | cf4e2c516dac271ce34e85f2c0dc635af3f3e97a6fedcdf52f7db8ee1c80b778 | Palm remains above front opening; launcher held steeply, insertion completes. |
| 3080 | 3083080 | 51.38466667 | 5895e8dc481aed17a57d8981150e5e30bf999e6f644b2f860fec8cfc3afd17f7 | Support hand releases; long fixed barrel remains intact. No independently observed bolt/latch stroke. |
| 3090 | 3093090 | 51.55150000 | 090b382dec34f38cb8110649f703a317d536420c6f0d6edd2f753d5cb8800fea | Launcher begins rapid forward/down roll; hand moves away from muzzle. |
| 3100 | 3103100 | 51.71833333 | 0c9800ff6a7974bf1e5cc7396a79b3a6135c27e857b47a8200a15b12e14f273e | Muzzle points forward again, stock returns to shoulder line. |
| 3110 | 3113110 | 51.88516667 | 52cb2a333db96e2b1bcb7169035702e9d4e9988d8f6111e94b6fc3216f5455b6 | Hip pose nearly recovered while camera pans right. |
| 3130 | 3133130 | 52.21883333 | 402044f2e594c6912ade634f6a3b0c662d390150ba2a6cc3da317db600307a70 | Recovered hip presentation; HUD1, canonical authored endpoint. |

Files: `/private/tmp/w187-bellowing-report/reference-01.png` through `reference-16.png`.
