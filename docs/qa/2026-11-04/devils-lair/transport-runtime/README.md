# Shared transport runtime — 2026-11-04

## Implemented

- Shared FlightSweep/FlightTerrain, DeliveryTimeline and ModelTransport own flight geometry, pause, bounded presentation lifetime, per-connection audience and cleanup.
- DevilsPresentation observes accepted actor insertions; the model never authorizes spawns, kills or encounter completion. Generation cancellation closes its tracker.
- DevilsTransportPaths supplies activity-authored routes. The supplied dl_skiff stays in its static pose; this is authored root motion, not a claim of source skeletal-animation fidelity.
- No texture or asset resolution changes in this batch.

## Evidence

- fabric-lifecycle.xml: 16 actual Fabric GameTests passed, including two new tests for real BetterModel tracker movement/pause/departure/close and late terrain obstruction. These two use a small test hull and no client audience, so do not prove full-size route or reconnect visuals.
- nbt-route-validation.xml and log: real Fantasy instance, production NBT generator/warmup, all four maps and existing actor-admission checks passed. Every authored candidate in RY.L, BL.EXIT/L/R/H and SP.D1/D2 has at least one clear production full-size route. No test-only chunk loading or block clearing was added for flight.
- initial-route-failure.log: initial long forward route failed RY admission. Diagnostics in subsequent runs showed unloaded chunks and blocked terrain. Final candidates use 8-block horizontal ingress, 12-block egress, four headings, heights 18/30/48/64/80/96. Each admits the entire hull corridor and rechecks movement; first available route wins.

## Remaining acceptance

- Actual strike-triggered framebuffer capture of arrival, accepted spawn beam and departure is pending. Earlier static skiff screenshot is not evidence of this integration.
- Player-connection replacement and generation cancellation need integrated client acceptance; tracker lifecycle tests alone do not certify network audience behavior.
- Full RY→RF→BL→SP gameplay, wipe/reconnect, combat performance and later user-run difficulty acceptance remain open. The overall strike goal remains active.
- No completion commit yet: this integration has not passed visual acceptance.

## Final offline regression

2586 JUnit tests; 16 failures, 0 new and 0 resolved versus the previous exact-name baseline. Real Gradle jar task completed; combined command failed because existing tests remain failing. See regression.json for identities and JAR hash.
