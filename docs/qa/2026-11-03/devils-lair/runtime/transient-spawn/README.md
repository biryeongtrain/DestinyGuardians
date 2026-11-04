# Transient spawn obstruction

Prior code counted all exhausted placements as hard failures. Three failures reset
an encounter even if a Guardian simply stood within12blocks of each valid shield
pad. Existing fixed-point alternatives could not distinguish this from bad map
geometry.

DevilsSpatial now separates terrain validation from transient proximity and live
entity/reservation occupancy. A terrain-valid candidate blocked by either retains
waiting status across bounded search slices; a completed wait restarts the search
on the next attempt. It neither emits a hard placement failure nor creates an actor.
The session retains the search, the director preserves the reservation and failure
count, and a10tick retry delay lets other reserved actors use the2spawn-attempt
budget. Budget-only yields still resume next tick. Successful admission clears both
wait and continuation state. Terrain, support, distance12, occupancy, route and
arena restrictions still apply; three actual exhausted failures still reset.

Validation:
-68strike JUnit tests passed, including a400tick occupied-first-slots scenario with
 other slots admitted, bounded attempt count, no checkpoint reset, later release and
 no duplicate actors.
-Actual generated NBT-world GameTest passed. Five repeated blocked-reservation
 attempts wait without failure; release succeeds; a nearby Guardian prevents spawn
 and moving away allows spawn. Injected stone at every alternate pad produces a
 hard failure. All temporary blocks restored before existing full voxel comparisons.
-Existing all-zone pack/special cohort admission remains included in that GameTest.

This is server logic and collision evidence, not a native combat/framebuffer or
speaker acceptance. Arbitrary cover-induced firing-line failures, moving32actor
performance and complete native encounter acceptance still require follow-up.

Full regression:2542 tests,16failures,0errors; exact failure case set unchanged.
Gradle jar task succeeded under --continue; combined exit1 is the test failure.
Runtime class bytes matched artifact.json. Native/client launch remains unperformed.
