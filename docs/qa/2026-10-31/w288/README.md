# W288 — Player fall damage starts at ten blocks

## Change

Server-only `LivingEntityMixin` adds six blocks to the native player safe-fall-distance calculation. Minecraft 26.3 uses `floor((distance + 1e-6 - safeDistance) * multiplier)`, with default safe distance 3. The adjusted default therefore deals 0 damage below 10 blocks, 1 at 10, 2 at 11, and 6 at 15. Health damage units are half-hearts.

The adjustment applies to server players of every class and to both GCB and vanilla connections. It preserves the existing native safe-distance bonuses, damage multiplier, downstream damage protections and fall-damage world rules. Mobs retain their native threshold. No per-tick scan, network messages, client changes or fall-distance resets are added.

## Validation

- Targeted Fabric GameTests: 3/3 passed through native `causeFallDamage` and actual health loss.
- Every guardian class: 4, 7 and 9.99 block falls are harmless; 10/11/15 deal 1/2/6 damage.
- Native safe-distance bonus and half/zero damage multipliers preserved; husk 4/10 block falls still deal 1/7.
- Fall-damage-disabled environment: 30 block player fall remains harmless.
- These are server damage-path tests. This batch did not run a client or physically perform class jumps with native input.
- Full gate and artifact details are recorded in the accompanying JSON files.

## Commands

Java 25; `./gradlew runGameTest -I /tmp/destiny-w288-targeted.gradle --console=plain` (filter `destiny-test:*w288*`), then `./gradlew build --console=plain`.

The source inspection used the actual Loom 26.3 merged Minecraft JAR (`LivingEntity.calculateFallPower` and `calculateFallDamage`), rather than older-version fall-damage rounding assumptions.

Full gate: 101 required failures, exactly the same failure IDs as W287; no new failures. The three W288 cases passed. `build` exits 1 because of those existing failures, while the JAR task completes. The artifact class bytes match the current compiled mixin. Existing unrelated working-tree changes are included in the local build and remain outside this scoped commit.
