# Selected-pad spawn telegraphs (2026-11-03/04)

The old presentation warned at the lane's base anchor before live placement chose
an alternative. Its timed effect could expire while placement was deferred, then an
actor could appear at a different point with no fresh local warning.

The live session now selects and reserves an exact world-space pad first. Its
per-slot warning begins there, retains its body reservation across ticks, and only
activates after the full requested lead on the director clock. Pausing the director
freezes the countdown. Presentation has no independent expiry: activation,
invalidation, retirement, generation reset or close removes the warning. A reroute
needs a new full lead. Failed presentation dispatch cannot arm the countdown.

Activation rechecks the exact warned point against live distance, world bounds,
terrain, support, entity/reservation occupancy and route. Failed recheck cancels
that point, then uses the normal bounded search/defer rules for another point.
Other spawns and Sepiks warp selection include pending footprints; own commit
excludes its own pending footprint. A live host opts out of the old reservation
countdown so the selected-pad warning does not add a second redundant delay.
Reservation counts and the two-attempt-per-tick cap remain director-owned.

Verification:
-78 targeted strike/presentation JUnit tests passed, including late selection,
 rerouting lead, stale-generation/retired cleanup, pending footprint ownership,
 live-host reservation timing and paused director clock.
-The generated NBT world GameTest passed. Exact selected-pad revalidation accepts
 unchanged geometry, rejects later reservations, and rejects a Guardian approaching
 during the warning. Existing full map/pack/boss admission checks remain included.
-A final source review moved countdown arming after successful presentation dispatch;
 final full suite recompiles that change. The real-world fixture tests spatial
 helpers, not the entire live Session-to-presentation wiring.
-Computer Use preflight at the end still reports a locked Mac. No Vision launch,
 actual PNG, native fight, speaker or runtime particle-load acceptance is claimed.

Remaining: full live session verification of warning visibility, actual placement,
 cancellation, sound overlap and particle load, plus broader model/music/native
 encounter acceptance. No acceptance commit while that review remains open.

Full regression:2546 tests,16failures,0errors, exact failure identities unchanged.
Gradle jar task succeeded; combined exit1 reflects test failures. Runtime class
bytes match the packaged artifact. No runtime process left owned by this batch.
