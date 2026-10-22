# H16 step 4 test handoff

Scope: multiplayer/server resource bounds, geometric distance and lifecycle only. No step 5 work.

Changed paths from this test task:
- src/gametest/java/kim/biryeong/destiny/test/VfxH16GameTests.java (new, 9 tests)
- src/gametest/resources/fabric.mod.json (one added fabric-gametest entrypoint; existing entries preserved)
- /tmp/h16-test-notes.md (this handoff)

Coverage:
- Seven embedded owners saturate 24 shared H14/H15 BetterModel trackers + 24 Polymer beam holders = combined 48. Per-pool oldest-owner eviction and independent cancellation are checked synchronously, including fixture cleanup.
- Owner caps of 4 trackers + 4 holders, isolation from a second owner, idempotent cancellation and AbilityService.cleanup.
- Normal-tick expiry of both pools for two owners; death, removal, dimension change and disconnect guards preserve a healthy owner.
- Inclusive 7-block target radius, rejection at 7.01, repeated link reuse, exit and re-entry; inclusive 96-block beam length, invalid geometry rejection.
- Anchor-specific cleanup preserves another anchor, unrelated trail and another owner. Two owners select three nearest targets from reversed input and react only to linked target death.
- Moving the owner past 48 blocks and back preserves world-anchored effects; this is explicitly NOT viewer distance culling coverage.

Bounds/isolation:
- At most 7 embedded players in any test; global allocation peaks at 24 trackers + 24 holders.
- maxTicks=1200 bounds async model-load/idle waiting. No allocations before required models exist and both pools are idle.
- Global saturation/eviction/cleanup finishes inside one callback, so another test cannot allocate between those steps.
- Normal lifecycle/expiry assertions wait for actual server ticks, never invoke manager ticks manually. Cleanup is owner-scoped; no clearAll or PlayerList mutation.

Evidence limits:
- These tests use live EmbeddedChannel-backed fake ServerPlayers outside PlayerList and actual BetterModel/Polymer allocation paths.
- They do not prove real client viewer eligibility at 48 blocks, spawn/despawn packets over a real connection, client rendering, network entity counts, FPS, TPS/MSPT under load, night/cave appearance or client resource-pack acceptance.
- Real multiple-client/distance/render/performance observations remain separate main-task work.

Results:
- Main reported runGameTest/build at 15:32:59 with 80/80 GameTests passing. This task did not independently run that build or inspect its runtime report.
- Static review confirms all 9 new annotated tests are registered exactly once, all prior entrypoints preserved, and git diff --check passed.
- No test edits were made after main's 80/80 report; only final read-only checks and this /tmp handoff were performed.
- No builds, server launch, main-source/doc/build edits or commits from this task. Other concurrent main-task changes were left untouched.

Current H16 test source SHA-256: fa3b90e80f87cbfa4fa7e286d23c476575eec00eb8353979538f437f950fed5c
