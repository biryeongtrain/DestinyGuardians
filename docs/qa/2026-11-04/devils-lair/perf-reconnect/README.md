# Peak-load server tick and mid-encounter reconnect — 2026-11-04

## Server tick at peak BL load

The fixture stopped killing enemies for 150 s after BL_BATTLE began, so the Walker, both Brigs and the ordinary packs stayed alive. Status reported 27/32 occupied actors for the whole hold. Five vanilla `/tick query` samples (100 ticks each) during the hold:

| Sample | Avg | P50 | P95 | P99 |
|---|---:|---:|---:|---:|
| idle tower before start | 1.8 ms | 1.3 | 5.0 | 14.0 |
| BL hold +0 s | 1.9 ms | 1.8 | 4.0 | 5.9 |
| +30 s | 1.8 ms | 1.8 | 2.9 | 3.7 |
| +60 s | 2.1 ms | 1.6 | 4.9 | 8.8 |
| +90 s | 2.2 ms | 2.0 | 4.1 | 6.1 |
| +120 s | 2.0 ms | 1.8 | 4.3 | 5.8 |

The plan's server target is tick P95 ≤ 45 ms at 3 players / 32 actors for 10 minutes. This sample is one connected player, 27 actors, 2.5 minutes on an M-series Mac with a 4 GB heap; it is well inside the target but is not the full 3-player, 32-actor, 10-minute acceptance run. Client FPS was not measured: the background-mode client snapshot (`client-snapshot.json`) reports the vanilla counter while unfocused and is not a frame-rate measurement.

## Reconnect during BL_BATTLE

The isolated client was terminated at 08:27:49 and relaunched; it logged back in at 08:28:38 (49 s, inside the 120 s reconnect window) directly into the same strike world at its previous position. The session paused while the whole fireteam was offline and resumed on rejoin. After reconnect the objective tracker, Walker and both Brig health bars were restored with their previous values (`after-reconnect.png`), music resumed at the same section, and the run continued to COMPLETE (`after-reconnect-phases.json`).

The actor count fell from 27 to 3 just before the disconnect. That was the fixture's final damage round as the hold ended (27 logged `Applied 400.0 damage` lines at 08:25:42), not a reconnect loss; the Brigs' half-health bars come from the same round.

Kills, zone exits and survival are server fixtures as in `../full-progression/`. The 3-player variant (one member leaving while others continue) and the 120 s expiry path were not exercised here.
