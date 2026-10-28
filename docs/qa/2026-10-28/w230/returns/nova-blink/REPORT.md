# W230 Nova intermittent safe-blink revision

## Observed server evidence
Read main docs/qa/2026-10-28/w230/server-r2-report.xml/log/json. Only failure: Nova Short safe blink accepted once, test tick68, random origin(11026899,4,5616844). Previous assertions already confirm blast, LOS and one burst. Existing failure text lacks age/collision/input values, so that historical execution alone cannot distinguish gate vs geometry. Main/slot baselines matched for both files.

## Mechanism identified and reproduced
Exact26.3 GameTestHelper.onEachTick bytecode registers each callback using runAtTickTime. GameTestInfo constructor allocates Object2LongOpenHashMap; tickInternal iterates object2LongEntrySet and runs due callbacks without stable same-tick ordering. Consequently pump tick50 may run before charge setup (chargeAge51,nextAttack69), while primary tick68 may run before its pump (blinkAge68). An intended12+6 exact boundary is then one product-age tick early. This explains R1 pass / R2 fail without relaxing the product spam gate. Bytecode saved GameTestHelper-javap.txt / GameTestInfo-javap.txt.

Pure scheduling reproduction uses the actual Fastutil Object2LongOpenHashMap and the same per-gameTime-idempotent age model. It is not a server test. In1000 trials unordered original callbacks rejected266; synchronizing tick at both input callbacks rejected0. Saved SchedulerOrderProof.java and scheduler-proof.log.

## Revision, separated by ownership purpose
1. Test patch retains input ticks50/68, repeated charge requests, one burst, successful >=0.5block short blink before solid wall, full-player-bbox-clear requirement, spam rejection and cleanup. Both input callbacks call currentTickSession to advance that precise gameTime first. If onEachTick already pumped, Session.tick's existing gameTime guard makes this a no-op. No extra wait and no lowered expectation. Success now explicitly requires physical displacement as well as blinks=1.
2. Product diagnostics-only patch adds nextAttack/chargeAt/spent/lastTick to existing status output. No gameplay branches, ranges, costs, movement, collision, world/chunk checks or timing conditions changed. Separate product-diagnostics-only-manifest.json / patch.
3. Test diagnostics print testTick/gameTime/serverTick, age/windup/nextAttack/chargeAt/spent/lastTick, body/position/look/shift/native-input and each swept step's destination, full bbox, loaded-corner/world-height/world-border/collision flags. This will identify independent placement/collision failures on next run instead of attributing them to timing.

## Checks and limits
Independent javac of revised owned Java files passes using existing main compiled classes and explicit isolated TestPlayers/TestCleanup/shared helper API contracts; not central integration proof. No main/shared source/build/game/Vision/lease/commit mutation. Original collision contract preserved. Ready to integrate only after nativeR1 ends, then master targeted server verification and R1/R2 PNG review.
