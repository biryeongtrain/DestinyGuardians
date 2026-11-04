# W180 Edge Transit reload source and adaptation

Reviewed 2026-10-27. Product target: original Edge Transit hash 218335759, Heavy Adaptive Grenade Launcher. Preserve the current W136 96-element solid model, face UV, green/seafoam dye, displays, textures and canonical assets. No gameplay clocks, funding, ammo, audio, hand IK or third-person reload changes. Runtime/admission belong to master.

## Original evidence and timestamps

Reload: [Quan Slow, Normal Reload / Field Prep Reload](https://www.youtube.com/watch?v=afQnPfb4ZK4), uploaded 2018-10-14, retrieved 2026-10-27, decoded 60fps at 1280x720. Original-style Edge Transit is visually identified by drum bays/rims, side cradle, long barrel, open lower frame and sight against the official model and labeled inventory. It wears a dark shader. No weapon title/API hash is visible in the action clip; exact roll and shader are unproven. This limitation is retained instead of claiming API identity telemetry.

Identity/model: [RideTube, Edge Transit Vault Cleaning](https://www.youtube.com/watch?v=AtnnHxiwWg8), uploaded 2019-09-30, labeled EDGE TRANSIT view at source frame1530, 51.051s (30000/1001fps). This proves labeled appearance only. [Bungie original screenshot](https://www.bungie.net/common/destiny2_content/screenshots/218335759.jpg), locally retained W31 SHA256 76ae0e6f799a201cc83c725e43f37dbe33eebf1fa6d0957e2d76025f1ff7a085. Existing W30 read-only FBX/default-dye research is recorded in art/weapons/w123/edge_transit/manifest.json and art/weapons/w31/references.json; no source rip is modified.

| Source time / frame | Directly observed | Local authored mapping |
|---|---|---|
| 3.000 /180 | Ready drum, barrel, sight and frame | p0 exact canonical |
| 3.800 /228 | Hand reaches and muzzle rises | p.15 presentation |
| 4.000 /240 | Sideways launcher, hand grasps drum | p.22 release |
| 4.200 /252 | Steep muzzle-up presentation | p.30 sideways clearance |
| 4.400 /264 | Hand occludes drum separation | p.36 lower drum |
| 4.800 /288 | Empty frame below barrel | p.44 drum out |
| 5.000 /300 | Empty frame; no shell-by-shell feed | p.50 hold |
| 5.200 /312 | Incoming hand/drum | p.62 return |
| 5.400 /324 | Drum seated, HUD six | p.74 seating; local magazine remains five |
| 5.600 /336 | Final securing hand action | p.84 action |
| 5.800 /348 | Lowering toward ready | p.92 release |
| 6.200 /372 | Ready restored | p1 exact canonical |

## Authored local adaptation

Action order is directly observed; numerical angles, timing normalization, grip pivot, cradle hinge, four latch/cradle solid membership, exact hidden drum path and charging-lug travel are authored interpretations. Hands hide the actual latch/bolt detail. A short travel of the existing charging lug interprets the final hand action, not directly observed bolt displacement. The drum moves sideways before lowering to clear the canonical lower rail; its exact path is authored. Same rigid drum resource proxies outgoing and incoming magazines, with no invisible teleport, duplication or shrink-to-hide. No original animation, bones or hand contacts were extracted.

This is a dedicated steep muzzle-up drum exchange, not renamed rifle animation: 28 drum solids (4 cores +8 bays +16 rims) stay rigid, four body cradle/latch solids release before departure, empty frame holds, complete drum reseats before brackets secure, then existing lug acts and carrier returns. Canonical 68 body +28 drum =96 assembled elements, zero new solids/triangle adapters/textures. Full vs split alternatives are not double-counted. Far below the 1000 cap. All cube dimensions and UV faces are preserved; exact endpoint assemblies retain original records.

Copied only established graph/matrix conventions and CPU raster utility; no other weapon keyframes or footage. Elements preserve canonical axis/angle records and use Rz Ry Rx for articulated XYZ; private preview copies normalize axis/angle before rasterization and apply native left reflection; displays use JOML Rx Ry Rz; equal .85 scale and rigid twohand carrier, native left reflection. Both FP contexts, boolean0 grips, float1 21 thresholds 0..1. Negative float1 and every non-FP/ADS/inspect fallback preserve the canonical graph. No routing files edited.

## Evidence, reproduction, native status

Private raw video, metadata, 12 exact decoded PNGs and labeled identity are retained in /private/tmp/w180-edge-transit-report. manifest.json records SHA256 and all frame indexes/timestamps. comparison.png pairs labeled original appearance with emitted geometry and compares three obliques plus drum details and both grips/hands. storyboard.png pairs actual full frames with independently reconstructed emitted display poses. These are offline authored visualizations, not native evidence or matching camera/hand performance.

Use bundled NumPy/Pillow Python: `rtk proxy <python> scripts/generate_reload_w180_edge_transit.py --render --evidence /private/tmp/w180-edge-transit-report`; `--verify` regenerates JSON and verifies retained image hashes without raw media or network. Generator output is exactly90 files; four authored support files make exact94 ownership. Focused Python regression and ReloadW180EdgeTransitTest cover partition, rigid drum, phase order, endpoints, fallback and actual26.3 parsers/codecs/transforms. Report current test results outside source in /private/tmp/w180-edge-transit-report. Historical failed commands remain in failures.log.

No native success is claimed. All master scenario rows in manifest.nativeQueue are pending: admit route/model; both hands/grips sequence/clearance/contact; ADS/inspect/non-FP fallback; partial/empty/no-reserve/full/spam and existing funding/timing; completion/cancel/switch/equip/death/disconnect cleanup; unchanged sound listening; brief10-20 displayed weapons. No shared client, server, CU or Vision touched. Master owns final session and integration.
