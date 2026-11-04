# Covered targets must not reset a stationary-flyer encounter

`DevilsSpatial.spawn` previously treated the stationary-flyer firing-line check as a hard route failure. With every Guardian behind cover, otherwise valid authored pads exhausted the search. `DevilsSession` then reported an ordinary failure to `DevilsDirector`, whose three-failure policy can reset a checkpoint.

Stationary flyers now mark this rejection transient after terrain, support, distance and occupancy checks. The existing waiting path retains the reservation, uses a 10-tick retry delay and does not increase placement failures. Ground/mobile-flyer navigation remains unchanged. Exact warned-pad activation still requires a firing line; this fix does not permit blind spawns. Physically obstructed pads still produce a completed hard failure.

## Validation

The real NBT-world fixture uses a typed `devils_servitor` probe and the authored SP shield pads. It encloses the eligible Guardian in temporary stone cover without changing the pads, repeats admission five times, checks that a previously warned pad is rejected during cover, removes cover, and verifies admission resumes with the same Search and no failures. Existing occupancy, proximity and genuine pad obstruction assertions remain. All changed blocks are restored even on assertion failure, and the fixture continues its original full voxel comparisons.

- Before change: GameTest fails specifically at “Temporary loss of firing line waits without resetting the encounter”; preserved in `before-gametest.xml`.
- After change: generated-world GameTest 1/1 passed (`after-gametest.xml`).
- Targeted strike JUnit: 72 tests, 0 failures, 0 errors (`targeted-tests.json`).
- Full regression and artifact results are recorded separately after completion.

This tests real spatial helpers in generated maps and existing director deferred-state coverage, not a full live Session encounter or native input. No client was launched: Computer Use still reported the Mac locked. No visual acceptance or completion commit is claimed.

Full regression: 2546 tests, 16 failures, 0 errors; identical failure identities to the previous warp-pad baseline, no new failures. Gradle `jar` succeeded under `--continue`; the combined command exits 1 due to the existing test failures. Packaged DevilsSpatial.class matches compiled output; see `artifact.json`. These baseline failures remain unresolved, not waived.
