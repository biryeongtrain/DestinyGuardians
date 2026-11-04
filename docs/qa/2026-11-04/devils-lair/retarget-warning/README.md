# Faction target replacement must restart the attack warning

## Defect and change

`DevilsMob` previously canceled an unfinished attack only when focusing a player. When its enemy-faction target disappeared, assigning another faction target preserved the previous windup/burst/aim. A replacement standing in melee range could take damage immediately, without its own warning.

All target changes, including loss of a target, now use the same cancellation path. Primary and secondary windups/bursts and their aim/reservation are released. Player priority memory still uses the existing focus path. Already launched projectiles are retained.

## Evidence

`before-real.xml` fails specifically because the replacement takes damage on the first AI step after the old target is retired. `after-real.xml` passes all 9 actor GameTests. The new regression uses actual director-owned refinery slots, model attachment and real damage in a Minecraft server. AI is manually stepped with movement isolated: original warning nearly completes, old target retires, replacement receives a new charge, stays undamaged for 11 more steps, then takes 3 damage at the twelfth step.

The early `before.xml`/`before.log` fixture only proved absent charge; its fabricated slot IDs were not registered with the director, so damage was rejected. That fixture was corrected before the authoritative before/after runs. It is not evidence of valid damage behavior.

Existing 8 server cases also pass, including live-server-tick Sepiks warp success/cancellation and boss phase damage. Native client visuals/listening remain unverified because Computer Use still reports a locked Mac. No completed visual acceptance or completion commit is claimed.

Full JUnit: 2546 tests, 16 failures, 0 errors; failure identities match the pre-existing baseline: True. These failures remain unresolved, not waived. Gradle continued to the JAR task; combined command exits 1 because tests failed. JAR SHA256: `5653b31982f636bb100b27ce1db1c40ae88f6f3476cdc5cb27a888a5c25e43b3`.
