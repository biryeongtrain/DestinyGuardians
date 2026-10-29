# W245 runtime worker

Status: slot4 ready received; four owned files installed after matching the source baseline. First isolated compile blocked only by master-owned isFinished() not yet propagated into slot4.

## Implementation

- New TowerBakedMaterialPass validates schema 1, compressed voxel SHA 55425ec1d14bc970ba05e90338e10a34468498d8a655d49ebc014d633996098d and compressed W243 SHA a0ecb154be54569b4bb183fdbc33dd03b750da6c97a4024f0fd7e79b5ad429f4 before any driver/ledger creation.
- Entire gzip/JSON decode, palette parsing, prior material decode and exposed-source geometry validation runs in CompletableFuture preparation. Limits: 32 MiB decompressed JSON, 200000 unique coordinates, 4096 palette strings. Full collision/outline vanilla cubes only; no air/fluid/block entities.
- Each expected string must equal the pinned W243 replacement for that position or the original voxel string otherwise. Five integers per cell, bounds and source exposure checked.
- Reuses TowerDetailPass driver, per-cell expected guard, 128 operations per tick, dedicated destiny:tower_courtyard_baked_w245 ledger. Existing trees/user edits are skipped and consumed; old ledgers remain untouched.
- TowerSpawnWorld owns/closes baked state; ticks only after materials.isFinished(). Master owns adding that method with successful completion semantics.

## Targeted verification

- Prepared new TowerBakedMaterialW245GameTests with two manual tests and a server-free main entrypoint. Master owns fabric-gametest entrypoint registration.
- Checks declared/actual prior hash, actual source hash, duplicate positions, W243/source expected mismatch, partial cube and invalid source target.
- Exercises shared live write function plus ledger codec round trip: matching writes, existing log and gold blocks, consumed skips, user removal/revert and independent older ledgers.
- Optional main argument validates master-owned shipped baked gzip through the same decoder.
- Read-only source/W243 hash checks passed against main. Test sample discovery is limited to one source chunk.
- Isolated compile authorized after ready. Actual runtime fixture execution is assigned to master and will not be run by this worker. No game, ports, live Blender or full GameTest gate run.

## Scope

Only four assigned worktree files will be changed after ready. No commits/index/reset/clean, resource/assets/shader/master document writes, main checkout mutations, shared dependencies or server/client execution.

## Master handoff commands

Compile uses the isolated composite dependency path:

```sh
rtk proxy ./gradlew --offline --no-daemon -Pgcb_server_dir=/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-pyroclastic_flow/libs/gcb-server compileJava compileGametestJava
```

Two manual GameTests are in `kim.biryeong.destiny.test.TowerBakedMaterialW245GameTests`; master must register that entrypoint if using GameTest discovery. A small temporary Gradle init script also exposes the same fixtures as `w245TargetedRuntime` without starting a server. Master may run this after integrating the master-owned isFinished() method and data:

```sh
rtk proxy ./gradlew --offline --no-daemon -Pgcb_server_dir=/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-pyroclastic_flow/libs/gcb-server -I /private/tmp/destiny-w245/runtime-worker/targeted.gradle -Pw245BakedResource=/Users/qf/IdeaProjects/DestinyGuardians/src/main/resources/data/destiny/tower/courtyard-baked-w245.json.gz w245TargetedRuntime
```

The optional resource argument validates the final master-owned gzip with the production decoder. It does not perform a live world save/reopen or visual QA. Restart fixture round-trips the exact shared ledger codec and invokes the exact shared conditional write function against a three-cell in-memory world.

## Compile result (worker)

- First isolated `compileJava compileGametestJava`: **FAILED**, exit 1, 104.8 seconds.
- Exactly one javac error: TowerSpawnWorld.java:216 cannot find TowerMaterialPass.isFinished(). Main has that master-owned addition; slot4 did not at compile time. Worker did not modify TowerMaterialPass.
- compileGametestJava was not reached. Other runtime/targeted tests were not executed by this worker; actual runtime tests remain master-owned.
- Full compiler output: `/private/tmp/destiny-w245/runtime-worker/compile.log`.
- Owned-path `git diff --check` passed.
