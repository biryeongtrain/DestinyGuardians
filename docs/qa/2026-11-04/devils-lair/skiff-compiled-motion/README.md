# Skiff compiled-motion investigation

This is server-side planning evidence, not a shipped strike skiff or client visual acceptance.

## Execution

Ran the existing four-map NBT GameTest with `DevilsSkiffSurvey` additionally reading the loaded BetterModel `rg_skiff` renderer's compiled animation tracks. The final Gradle run exited 0; the NBT GameTest passed (1/1). `gametest.xml` and `gametest.log` retain the results. Product sources and the product JAR were not changed by this investigation.

`compiled-motion.json` contains all six animated tracks for arrive/drop/depart (125 compiled entries): local position, scale, quaternion, raw rotation, raw time, and interpolation flags. The test requires finite nonnegative time values and finite position/quaternion values. `inputs.json` pins the model, diagnostic source, map manifest, and API dependency.

## Findings that change route planning

- Arrive hull: 25 entries, position Y reaches -1.1539997 blocks and local Z reaches +6.2679996 after starting at -87.5. The source position keyframes alone do not capture this overshoot.
- Depart hull: 26 entries, Y reaches -1.3641357 and local Z reaches -9.197388 before ending at +112.5.
- Drop hull: 16 entries, Y reaches -0.38276628.
- Compiled local Z and pitch signs differ from the raw Blockbench data. A route must include the actual tracker/world orientation transform before making world-space collision claims.
- Raw time values are not monotonic; for each track their sum equals clip length (4, 2.6, or 4 seconds). Do not treat each raw time as an absolute timestamp.

The first attempt incorrectly asserted monotonically increasing raw times and failed. `initial-failed.log` preserves that diagnostic error. The final extractor retains raw values and checks their valid numeric range without that assumption. No product animation was changed to satisfy the test.

## Remaining integration

The earlier sparse, upright `skiff-survey` results are feasibility evidence only. They do not certify safe routes. Use the compiled transforms, actual bone hierarchy, ship geometry, tracker yaw convention, and between-frame display interpolation to construct a swept envelope. Include clamp rotation and engine scaling, as well as any simultaneously played idle animation. Validate the selected enemy pads and full corridor against actual NBT collision shapes; precompute expensive work before combat, own corridor chunk tickets, and tie presentation cleanup to session generation. Do not alter enemy spawn timing or relocate existing enemies to hide a route failure.

Actual ship playback, late-viewer behavior, native framebuffer, audio, and performance acceptance remain pending. The strike still has no integrated skiff presentation.
