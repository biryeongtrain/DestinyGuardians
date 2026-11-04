# Real actor boss damage integration

Filtered Gradle `runGameTest` completed successfully:6/6 server GameTests, with
normal server shutdown. Two new checks exercise actual `DevilsActors.spawn`,
BetterModel attachment and `Combat.damage` into `DevilsMob.hurtServer`.

Brig: both planned instances begin at700HP;349 damage leaves351HP and closed
armor; one more opens armor at350. Each lethal hit credits exactly one death,
stale hits cannot credit again, and killing both Brigs cannot bypass the Walker.

Sepiks: actual max/current health2200 demonstrates the attribute-limit extension
in this runtime. Guard/intro reject damage. Oversized hits clamp at1474/726HP and
enter the first/second shield respectively. Both shields reject more damage;
three real60HP Servitors must die per round, then recovery still rejects damage.
Final damage phase permits death; actual death invokes completion exactly once.

Setup boundaries: prior encounters and ordinary add deaths are scripted through
the real director; intro completion is explicitly acknowledged by the fixture.
Director clocks advance synchronously. Actors are placed in separated clear-air
locations inside the isolated floor-test world, not authored arena pads. These
checks do not prove animation timing, native weapon input, fight feel, spawn routes,
full progression, audio output or visual quality. All four previously existing
actor/model/faction/audio/Walker tests also passed in this same server run.

Product code was unchanged in this batch. Test sources and tested boss runtime
hashes are in receipt.json. Full unit regression was not repeated because only
GameTest coverage changed and the relevant actual-server suite passed.
