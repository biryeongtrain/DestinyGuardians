# Skiff flight corridor foundation

Implements a previously missing prerequisite for the planned nonattacking, generation-owned skiff. **No strike ship is spawned by this change.** Source rig/animation adaptation, model acceptance, route selection, corridor chunk ownership and presentation lifecycle integration remain open.

`DevilsFlightSweep` accepts evaluated local hull bounds plus rigid world-space pose endpoints. It encloses continuous shortest-arc quaternion interpolation and linear translation using endpoint box union plus rotational sagitta. Bounds include the offset of the hull from its rotation origin, avoiding nose/tail tunneling between clear endpoint poses. Mutable JOML inputs/accessors are copied; invalid geometry and unbounded pose lists are rejected.

This contract does not cover arbitrary cubic source-key interpolation or local skeletal motion that escapes the supplied envelope. The future source adapter must use actual compiled interpolation endpoints and a certified full animated local envelope, including hierarchy/scale. Earlier `rg_skiff` compiled-motion evidence already proves raw keys miss overshoot; these helpers do not replace that work or authorize the old tutorial ship as the strike asset.

`DevilsFlightTerrain` performs a fresh server-thread check of one swept interval: world border/height, a bounded collision-cell budget, loaded chunks including the collision iterator's neighboring blocks, then actual block collision shapes. It never acquires chunks or caches an acceptance. A future coordinator must own/release its corridor leases, budget route preflight before combat and recheck the next movement interval. Conservative false rejections are possible; they must not be hidden by moving enemy pads or skipping combat.

## Validation

- Real Gradle targeted JUnit: 9 tests pass. Coverage includes a turning nose hitting a midpath obstacle, 80 deterministic compound-rotation/translation cases with 101 interpolation points and all eight corners, quaternion sign equivalence, half-turn and stationary flight, immutable pose data, invalid inputs, missing neighboring chunks before shape reads, negative chunk coordinates, bounded world queries and fresh obstruction checks.
- A new Fabric test in `DevilsWalkerGameTests` checks an actual lower slab (upper flight clear/lower flight blocked), a full-block obstruction between endpoints, and obstacle removal. **1/1 passed**; real Gradle `runGameTest` exited 0 and its server shut down normally. `gametest.xml`/`gametest.log` retain the evidence. This fixture is not an authored Devils' Lair flight route.
- The first targeted GameTest selector used a dot instead of the registered underscore; it selected zero tests and failed. `initial-filter-miss.log` preserves this. The corrected selector matches exactly one test; a zero-test run is not counted as validation.
- No native client, full-route test, FPS, flight animation or model-quality acceptance in this batch. Product JAR not rebuilt; source compilation and targeted tests do not update the previously delivered artifact. No completion commit.
