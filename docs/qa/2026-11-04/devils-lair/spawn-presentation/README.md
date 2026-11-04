# Strike spawn presentation integration boundary

The session now forwards director incoming notifications to its owned presentation, retaining the existing spawn-warning deadlines. A generation/running check rejects stale requests, and an incoming presentation exception cannot prevent reservation progression.

`DevilsActors.Environment.spawned` reports the immutable spawn request and actual selected world position only after entity insertion, model attachment, and any Walker parts succeed. `DevilsSession` forwards it to `DevilsLair.Presentation.spawned` only for its active generation. This is a synchronous presentation observation before the host spawn call returns to the director; it is not authorization to advance encounters or claim a kill. A presentation exception is logged without rejecting the already accepted actor, preventing erroneous retries/duplicates.

These hooks prepare the skiff integration. The current presentation's default incoming/spawned methods remain no-ops: **no visible skiff has been added by this change**. Selected spawn-pad warnings already use the existing spawnTelegraph path. Full skiff routes, source model/material integration, lifecycle playback and native acceptance remain unfinished.

## Validation

- Actual Fabric actor suite: 13/13 GameTests passed, including real entity/model insertion with deliberately throwing presentation callback.
- New test checks deferred selection emits no success, accepted callback receives actual inserted actor position, callback failure preserves acceptance, duplicate spawn does not replay, block-obstructed insertion emits no success, and a closed runtime emits no stale success.
- The fixture deliberately uses clear air and an explicit block obstruction; it does not prove authored map spawn-pad routing or flight collision.
- The initial test mistakenly assumed `noCollision` would reject a second overlapping mob in this fixture. It also placed assertions inside the deliberately caught presentation callback. The final test uses an explicit stone obstruction and asserts recorded callback observations outside the exception boundary. `initial-failed.log` preserves the first failure.
- Full JUnit: 2550 tests, 16 failures, 0 errors. All failure identities match `warp-pads/full-failures.json`; they remain unresolved and are not waived.
- `jar` executed successfully in the real Gradle `test jar --continue` run; combined exit was 1 because tests failed. Exact JAR hash is in `build-receipt.json`.
- No native client launched; no visual/audio/FPS acceptance or completion commit.

## Source fidelity for next integration

The plan names original skiff variants `80C3EE92` and `80CC0740`. Both FBX sources and manifests are present in the user-provided Downloads asset folder, read only. `skiff-source-inputs.json` records their files and hashes. Their primary source models declare 10 bones; child models declare 10/2/2 bones. The existing 54-element `rg_skiff` compiled-motion investigation does not certify either original model, rig, or material fidelity. Inspect and integrate those originals before claiming the planned final skiff asset is complete.
