# Reconnecting players received no chunks — 2026-11-04

## Cause

minigame-lib's cinematic layer replaces vanilla chunk-batch acknowledgement (`ViewInputMixin.handleChunkBatchReceived` cancels vanilla) and keeps its own batch queue. That queue and the active camera views were keyed by player **UUID**. A reconnect has the same UUID, but it gets a new `ServerPlayer` and a new chunk sender. Often the old connection ("logged in from another location", a timed-out client, a crash and quick rejoin) only finishes disconnecting after the new login. Its `DISCONNECT` handler then:

- removed the new connection's pending batch records. The client's acknowledgements found nothing to match and were dropped, so the vanilla `PlayerChunkSender` waited forever for an acknowledgement and stopped sending chunks;
- or, if the old connection was inside a camera view, `CameraViews.get(newPlayer)` still found the stale view and filtered every world packet, including chunks.

That matches "only some reconnects" and "no chunks at all".

## Fix (minigame-lib `CameraViews`)

- Batch records are keyed by the exact `ServerPlayer` instance (`IdentityHashMap`), so one connection can no longer clear another's records.
- `get(player)` returns a view only when it belongs to that exact connection; stale views are closed in the tick loop and when a new view opens.
- An acknowledgement with no matching record is applied to the player's own chunk sender whenever it still has unacknowledged batches. It is never dropped.

## Verification

minigame-lib tests, the 88 strike tests, the presentation tests and the jar pass. Real-server takeovers: a second isolated client logged in with the same account while the first was still connected (the server kicks the old session). This was done in the tutorial/tower, mid BL_BATTLE, and during the Sepiks intro camera. Every new connection rendered the full world, and the strike went on to COMPLETE (`takeover-sheet.jpg`, `phases.json`, `connections.log`). I did not run a before-fix control to reproduce the blank world on demand. The cause is from reading the code; the runtime check shows the fixed behavior.
