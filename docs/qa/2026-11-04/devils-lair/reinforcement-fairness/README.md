# Reinforcement placement fairness

## Latest user direction

The user explicitly deprioritized further skiff visual polish: it is invulnerable and appears briefly, so recognizable appearance without obvious problems is sufficient. Reinforcement behavior takes priority. Do not continue exhaustive surface/shader work as a gate ahead of reinforcement integration. This does not establish that a ship has already been integrated or waive combat lifecycle correctness.

## Defect and change

`DevilsDirector.tick()` previously began every bounded placement pass at the first actor. Two early reservations whose spatial searches deferred for one tick could consume both placement attempts on every tick. Later reservations with usable pads never got a chance until those searches completed. The existing blocked-pad regression used ten-tick retries and therefore missed this case.

The director now resumes after the last attempted slot, rotating across the stable actor list. Ineligible/live/terminal entries are skipped. The limit stays two attempts per tick; incarnation, spawn acceptance, telegraph duration, pack/actor caps, failure accounting and wave spacing are unchanged. Generation invalidation clears the cursor. A deferred attempt remains a deferral, never a kill or completed spawn.

## Evidence

- `before.log`: the new one-tick-deferral regression fails against the old loop because clear later pads never spawn.
- `after.log` and retained XML: all 21 director tests and 4 pause-policy tests pass. The new regression keeps slots 0–1 deferred, observes the remaining six spawn, releases the obstruction and checks all eight unique slots join without a reset or budget violation.
- The separately named telegraph filter in this targeted invocation used singular `Test` and selected no suite; it is not counted above. The final full regression includes the actual `DevilsSpawnTelegraphsTest` suite.
- Actual Fabric actor regression and final full JUnit/JAR outcomes are recorded in the adjacent report files after completion. Server tests are not native framebuffer or human difficulty acceptance.

Skiff model/projection candidates and original assets were not changed for this fix. No client was launched. Full reinforcement presentation integration (ship/actual drop association/departure) remains unfinished; this fixes a concrete scheduling stall in the gameplay path first.
