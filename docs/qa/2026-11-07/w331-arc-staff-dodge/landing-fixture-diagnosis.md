W331 Spectral accepted-air fixture follow-up

Only MeleeAreaW329GameTests.arcStaffAndSpectralTargetlessAirContactsTravelFiveAndStaleSessionCannotMove changes. No production changes, no standalone actual GameTest run.

26.3 bytecode evidence in Entity.bytecode.txt / GameTestInfo.bytecode.txt / GameTestHelper.bytecode.txt:
- GameTestHelper.onEachTick registers per-tick callback wrappers through GameTestInfo.setRunAtTickTime, just like runAfterDelay.
- GameTestInfo.tickInternal iterates its Object2LongMap callbacks without ordering same-tick entries, then ticks sequences (offsets 257..267).
- Entity.move sets verticalCollision from requested Y != resolved Y (offsets 473..491), verticalCollisionBelow from that plus negative Y, then setOnGroundWithMovement.
- The old +0.2 height / -0.2 velocity can reach the plane without a clipped vertical delta on its first frame; floor-height-dependent floating-point rounding makes exact ties variable. A +2 tick assertion that runs before its second native frame can therefore see onGround=false.

Fix: make acceptance, +2 landing assertion and final contact assertion a sequence, which runs after the native onEachTick callback map. All existing deadlines/velocity/displacement/HP/session/5-block assertions are retained. Add real supporting-floor, airborne source clip, and exact original floor-Y assertions with useful failure coordinates. No timeout/tolerance widening.

Residual: actual cause cannot be reconstructed from old log positions (old assertion omitted them); this removes the proven callback-order dependency and exact-contact exposure. Master will run the single failed test.
