# Guardian Rises NBT generation

Guardian Rises previously opened an empty Fantasy world and placed zone blocks through `ZoneTemplate.Build` on the server thread. The production path now loads four pre-exported Nucleoid section-NBT templates asynchronously once per instance manager and uses the same shared chunk generator and bounded chunk warmup as Devil’s Lair. The authoring grids and markers remain unchanged.

- Source non-air blocks: Gateway 966400, Breach 334233, Divide 1540290, Dock13 515233 (3356156 total). NBT files total 2062688 bytes.
- Origins remain `(2048 + zoneOrdinal*4096, 64, 2048)`. Palette properties, geometry, light blocks, markers, and checkpoint coordinates are preserved.
- Each warmup requests at most eight columns per step. Both entry and background build request budgets are now 2ms; chunk generation runs through Minecraft's chunk pipeline without ServerLevel block placement or neighbour updates.
- Preparation does not block on NBT IO. Empty Fantasy worlds tick during preparation, and READY disables unconditional empty ticking. Warmups retain only their own tickets and release them on cancellation/cleanup.
- Adoption now transfers completed warmup cleanup ownership as well as in-flight work; resuming at another checkpoint releases the unused Gateway warmup. Failed asynchronous loads are handled by session failure / spare retry handling.
- Generator and warmup code were extracted without algorithm changes; Devil’s Lair retains compatibility adapters. The lossless Python exporter is also shared.

## Validation

- Shared converter: all eight Guardian Rises / Devil's Lair templates reproduce byte-identically; authored geometry/marker inputs are unchanged.
- Actual Fabric/Fantasy server: Guardian Rises four-zone sample checks (651504 voxel positions, comparing both loaded NBT and generated world), generated heightmaps, actual empty-world ticking, completed-spare adoption, cancellation/idempotence/retry, independent player copies, and cleanup PASS. Existing Devil's Lair NBT generation/spatial tests also PASS.
- The broad `*nbt*` filter also selected seven unrelated tests: five passed; two existing reload presentation assertions failed (Recluse W100 / Magazine W114 expected 0.083333336 vs live 0.06666667). Overall runGameTest exited2, not a full-suite pass. No reload source or expectations were changed.
- Initial attempt stopped before fixture allocation at the existing120s asset setup deadline. Retry kept the same profile-graph readiness condition and used its existing360s timeout option; setup completed at135914ms. Logs retain both attempts.
- Native client QA and before/after TPS/FPS benchmarks were not performed. This change does not establish client frame rate or a before/after TPS benchmark.

- Final real Gradle targeted unit tests: 32 passed, no failures; assemble SUCCESSFUL. JAR and bundled NBT/classes verified in `build-validation.json`.
