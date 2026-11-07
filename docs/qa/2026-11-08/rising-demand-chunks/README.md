# Guardian Rises: demand-generated instance chunks (W341)

The W339 NBT migration still queued whole-zone warmups, view-distance margins, the next map, and an idle spare. W341 removes those production paths. Creating an instance only installs its shared NBT chunk generator; checking zone metadata requests no terrain. NBT data remains loaded asynchronously once per instance manager and shared read-only by its worlds.

An actual entry/checkpoint/zone teleport awaits one destination column through the normal asynchronous chunk pipeline. No join or synchronous map placement is used. After teleport the arrival ticket is released and vanilla player loading owns the view. Disconnect, cancellation and shutdown release the owned pending arrival. Phase lights are applied only to already-loaded chunks, including chunks loaded after their phase was reached.

## Validation

- A real Fabric server GameTest passed with Guardian Rises enabled. No automatic spare world appeared. Fresh-instance creation, checking all four zones, and idle waiting each retained zero chunk holders.
- First actual arrival explicitly requested one column; the destination neighbourhood contained **1 FULL chunk**, with **529 vanilla generation-dependency holders**. Holder count is not generated FULL chunk count. Vanilla generation dependencies and subsequent player view loading remain normal on-demand work.
- Gateway, Breach, Divide and Dock13 arrivals succeeded; each later zone's spawn chunk remained absent until it was requested. Cancellation and double-close also passed.
- The fixture disables resource-pack generation and uses the existing pixel-arms test profile because it tests server world loading only. Its AutoHost configuration was restored to the original bytes. It does not certify native client visuals, audio, FPS, or sustained production TPS.
- The first test assertion incorrectly treated `getLoadedChunksCount()` as FULL chunk count. The retained failed XML records that test mistake; the corrected check probes `getChunkNow()` without loading terrain. No product limit was relaxed to accommodate whole-map loading.
- The old W339 exhaustive geometry fixture now explicitly owns its own test-only warmup. Production `RisingZones.begin` is metadata-only. It was not run as part of this performance regression check.

Final targeted Gradle units passed: RisingMissionTest 16, RisingEncountersTest 9, ZoneTemplateTest 9 (34 total). `assemble` produced the real Gradle JAR; the W341 download is a byte-identical distribution copy. Commands, hashes and production cache validation are recorded with the adjacent evidence files.

## Matching prebuilt resource pack

The final normal JAR was also booted in the isolated production-configured server. Its changed content key generated/saved a fresh cache once (116.6 s readiness); the second boot hit that cache without pack generation (14.1 s readiness, 2028 ms cache restoration). Both servers exited 0. The client ZIP is unchanged at 188,236,924 bytes (below 250 MB); the companion cache bundle is 200,294,514 bytes. Extract the companion into the matching server root; it supplies `polymer/destiny-pack-cache/`. Configs/assets/JAR changes still invalidate the key normally. Both owned servers stopped, port 25630 is closed, and the world-only QA AutoHost config matches its original exact bytes.
