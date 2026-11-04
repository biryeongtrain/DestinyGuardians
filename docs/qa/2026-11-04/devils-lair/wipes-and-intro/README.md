# Encounter wipes, boss-fight disconnect and the Sepiks intro soft-lock — 2026-11-04

## Wipes in the real runtime

The fireteam (one isolated client) was killed by a server `damage` fixture after protection was removed:

| Wipe | Result |
|---|---|
| RF_DEFENSE2 | Down after 0 s, `Checkpoint reset RF: 화력팀 전멸` 8 s later, back to RF_ENTRY with the same three entry packs (24/24 = 3×8), device and all three defenses replayed, then BL |
| BL_BATTLE (Walker + 2 Brigs alive) | Reset to BL_BATTLE with fresh bosses, then BL_CLEAR |
| SP_SHIELD1 (three Servitors alive) | Reset to SP_GUARD; guard, intro, both shields replayed exactly once each, then COMPLETE |

Every run continued to completion with no extra checkpoint resets, stuck phases or exceptions (`*-phases.json`). Rewards are out of scope, so reward/chest duplication was not checked.

## Disconnect just before the boss dies

At SP_DAMAGE3 the client was terminated and relaunched; it rejoined after 31 s. Sepiks kept its remaining health (`sp-damage3-after-rejoin.png`), and the run then completed exactly once (`boss-disconnect-phases.json`).

## Defect found and fixed: Sepiks intro soft-lock

In one run the client had reconnected during the briefing. Every Sepiks intro after that timed out with `Sepiks awakening did not complete`. Each timeout reset the arena to SP_GUARD, so the fight looped forever (`intro-loop-evidence.log`). The awakening gate only opened on BetterModel's play-once completion callback. BetterModel 3.5.1 stops scheduling a tracker that has no viewers (`Tracker.lambda$start$0`: `playerCount()==0` → `shutdown()`), so that callback can be lost.

`DevilsPresentation.IntroGate` now also finishes the awakening once the authored clip has fully elapsed (9.33 s = 187 ticks) plus 20 ticks of grace. That is still inside the director's 280-tick safety timeout. It logs `Sepiks intro callback missing` when it fires. A cancelled scene, a different generation or actor, or an unknown clip length still cannot finish the gate. The other `DevilsPresentationTest` checks and a new one (elapsed clip, grace boundary, unknown length, cancellation) pass, as do the 88 strike tests and the jar.

After the fix the same sequence (reconnect during the briefing, then a shield wipe) completed normally. This time the callback arrived, so the fallback did not fire in this run. The exact zero-viewer trigger has not been reproduced on demand yet, so the fallback is covered by unit tests only, not by runtime evidence.
