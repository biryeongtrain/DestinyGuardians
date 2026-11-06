# Owner weapon display distance — 2026-11-06

Owner-only weapon, grenade and four arm displays now have a small vanilla `view_range`. Ordinary front/back third-person cameras stop rendering the foreground weapon while native held equipment remains visible. This is a bounded improvement, **not complete third-person detection**: wall-compressed cameras can still render the foreground weapon (reproduced in `high-wall.png`).

## Implementation

Minecraft 26.3 local bytecode (`Display.shouldRenderAtSqrDistance`, `LevelExtractor`, `Options.getEffectiveRenderDistance`) establishes the distance rule: radius = view_range × 64 × clamp(effective chunks / 8, 1, 2.5) × entity-distance slider. `DisplayViewRange.nearCamera` compensates for the client/server chunk cap. A base radius of 0.64 yields 0.32–3.2 blocks across the vanilla 50–500% entity slider, below the ordinary four-block third-person camera distance. The slider itself is not reported to the server.

Initial metadata is set before spawn; active displays refresh only when the computed range changes. Existing GCB camera suppression remains. No shader, geometry, animation, damage, ammo or observer-equipment code changed. No new client mod is required. QA used the existing Vision instrumentation client without GCB, not a separately launched completely unmodified client.

## Validation

- Targeted Gradle tests: DisplayViewRangeTest (2), ProfileArmAssetsTest (3), all passed. Numerical tests cover client/server chunk combinations, slider extrema and invalid radius inputs; they do not prove camera collision behavior.
- Full `./gradlew test build --no-daemon`: **failed**, 2,682 tests / 18 failures. The failure test-name set matches the preceding memory-optimization gate exactly. Compilation and jar tasks completed; this is not a successful full build. Failure names are in `full-test-failures.json`.
- Actual PNG review with HUD visible, isolated server 25610 / Vision 8102: 100% first/front/back transitions, crouch/run/jump, ADS and fire-to-empty automatic reload passed. `low-fire-2/15/28.png` are **100%**, despite their early filename prefix: graphics preset Fancy reset the attempted option edit. These show aim, empty-magazine reload and restored ammo respectively.
- Corrected setting trials used `graphicsPreset:"custom"`; persisted options were checked after loading. At 50%, native crouch/run/jump retained gun/hands (`min-move-2/9.png`), and back third-person hid them (`min-back.png`). At 500%, first person retained them and ordinary front/back views hid them (`high-first/front/back.png`). Client render distance 16, server cap 10; other chunk combinations were checked numerically only.
- At 500%, a temporary wall behind the player compressed the camera and foreground gun/hands returned (`high-wall.png`). This residual is inherent to using distance as a proxy for F5. No claim of wall-safe or all-camera-mode acceptance is made.
- Native sequences completed and released; final state had no lease, held keys, pending steps or native movement input. Screenshots are bracketed observations, not every rendered frame or FPS certification. No speaker/audio QA.

## Cleanup and evidence

The wall occupied nine previously scanned air blocks in destiny:tower, x69–71/y75–77/z-18. Both placement and removal reported nine changed blocks. Player returned to tower spawn and first person. Dedicated QA options were restored byte-for-byte; owned client, server and bounded keep-awake coordinator stopped; ports closed. User profiles and unrelated loot work were preserved.

Original PNG hashes are in `screenshots.json`. Raw native sequence results, min/high option snapshots and runtime evidence remain in `/tmp/destiny-thirdperson-qa-20261106/`; server log is in `/tmp/destiny-devils-qa-20261103/server.log`. No runtime secrets are copied into this report.
