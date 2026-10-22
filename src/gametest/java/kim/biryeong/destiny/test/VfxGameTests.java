package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.Tasks;
import kim.biryeong.destiny.fx.HunterVfx;
import kim.biryeong.destiny.fx.HunterVfx.Kind;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.Map;
import java.util.function.Consumer;

/** Real BetterModel renderers, fake owners, and normal server ticks; never clears another test's VFX. */
public final class VfxGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final Vec3 OWNER_POS = new Vec3(2.5, 1, 6.5);
    private static final Map<String, String> ANIMATIONS = Map.of(
            "destiny_vfx_arc_h13", "spawn",
            "destiny_vfx_solar_h13", "spawn",
            "destiny_vfx_vortex_h13", "loop",
            "destiny_vfx_smoke_h13", "loop");

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static ServerPlayer owner(GameTestHelper h) {
        return TestPlayers.create(h, OWNER_POS, -90, 0);
    }

    private static void cleanup(ServerPlayer owner) {
        try {
            HunterVfx.cancelOwned(owner);
        } finally {
            TestPlayers.remove(owner);
        }
    }

    private static void whenModelsLoaded(GameTestHelper h, Runnable assertions) {
        // BetterModel builds its pack asynchronously. Do not create owners or effects while waiting.
        h.startSequence().thenWaitUntil(() -> {
            for (String model : ANIMATIONS.keySet()) {
                check(h, BetterModel.model(model).isPresent(), "Waiting for BetterModel model " + model);
            }
        }).thenExecute(assertions);
    }

    private static void delayed(GameTestHelper h, ServerPlayer owner, int ticks, Runnable setup, Runnable assertions) {
        boolean scheduled = false;
        try {
            setup.run();
            // Reserve cleanup even if models became available too late for the delayed assertion.
            h.runBeforeTestEnd(() -> cleanup(owner));
            h.runAfterDelay(ticks, () -> {
                try {
                    assertions.run();
                    h.succeed();
                } finally {
                    cleanup(owner);
                }
            });
            scheduled = true;
        } finally {
            if (!scheduled) cleanup(owner);
        }
    }

    private static void play(GameTestHelper h, ServerPlayer owner, Kind kind, int duration) {
        check(h, HunterVfx.play(owner, h.getLevel(), owner.position(), kind, 2, duration),
                "Real VFX must start for " + kind);
    }

    private static ServerLevel otherLevel(GameTestHelper h) {
        ServerLevel other = h.getLevel().getServer().getLevel(
                h.getLevel().dimension().equals(Level.NETHER) ? Level.OVERWORLD : Level.NETHER);
        check(h, other != null && other != h.getLevel(), "A second dimension is required");
        return other;
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void fourModelsAndTheirAnimationsAreRegistered(GameTestHelper h) {
        whenModelsLoaded(h, () -> {
            for (var entry : ANIMATIONS.entrySet()) {
                var renderer = BetterModel.model(entry.getKey()).orElseThrow();
                var animation = renderer.animation(entry.getValue()).orElse(null);
                check(h, animation != null, entry.getKey() + " must contain " + entry.getValue());
                boolean loop = entry.getValue().equals("loop");
                check(h, animation.loop() == (loop ? AnimationIterator.Type.LOOP : AnimationIterator.Type.PLAY_ONCE),
                        entry.getKey() + " must have the expected animation mode");
                check(h, !animation.animator().isEmpty() && animation.length() > 0,
                        entry.getKey() + " must contain a nonempty animated track");
                long bones = renderer.flatten().filter(group -> !group.getItemStack().isAir()).count();
                check(h, bones > 0 && bones <= 8, entry.getKey() + " must use at most eight render bones");
                if (!loop) {
                    float seconds = entry.getKey().equals("destiny_vfx_arc_h13") ? 0.8f : 1.1f;
                    check(h, Math.abs(animation.length() - seconds) < 0.001f,
                            entry.getKey() + " must match the one-shot TTL");
                }
            }
            check(h, HunterVfx.modelName(Kind.ARC_FLASH).equals("destiny_vfx_arc_h13")
                    && HunterVfx.modelName(Kind.ARC_STRIKE).equals("destiny_vfx_arc_h13"), "Arc kinds share their model");
            check(h, HunterVfx.modelName(Kind.SOLAR_BURST).equals("destiny_vfx_solar_h13")
                    && HunterVfx.modelName(Kind.SOLAR_KNIFE).equals("destiny_vfx_solar_h13"), "Solar kinds share their model");
            check(h, HunterVfx.modelName(Kind.VOID_VORTEX).equals("destiny_vfx_vortex_h13")
                    && HunterVfx.modelName(Kind.VOID_SMOKE).equals("destiny_vfx_smoke_h13"), "Void kinds use separate models");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void everyKindCreatesARealTrackerAndCancels(GameTestHelper h) {
        whenModelsLoaded(h, () -> {
            ServerPlayer owner = owner(h);
            try {
                float health = owner.getHealth();
                Vec3 position = owner.position();
                Vec3 velocity = owner.getDeltaMovement();
                for (Kind kind : Kind.values()) {
                    play(h, owner, kind, 60);
                    check(h, HunterVfx.activeCount(owner) == 1, kind + " must retain a tracker without a real viewer");
                    HunterVfx.cancelOwned(owner);
                    HunterVfx.cancelOwned(owner);
                    check(h, HunterVfx.activeCount(owner) == 0, "Cancellation must be idempotent");
                }
                check(h, owner.getHealth() == health && owner.position().equals(position)
                        && owner.getDeltaMovement().equals(velocity), "VFX must not change owner health, position or velocity");
                h.succeed();
            } finally {
                cleanup(owner);
            }
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void expiresOnServerTicksWithoutAbilityTasks(GameTestHelper h) {
        whenModelsLoaded(h, () -> {
            ServerPlayer owner = owner(h);
            delayed(h, owner, 4, () -> {
                play(h, owner, Kind.VOID_VORTEX, 2);
                Tasks.cancelOwned(owner);
                check(h, Tasks.count(owner) == 0 && HunterVfx.activeCount(owner) == 1,
                        "Visual TTL must not be owned by the ability task scheduler");
            }, () -> check(h, HunterVfx.activeCount(owner) == 0, "Expired tracker must be removed by normal server ticks"));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1500)
    public void loopDurationIsBoundedAtTwoHundredTicks(GameTestHelper h) {
        whenModelsLoaded(h, () -> {
            ServerPlayer owner = owner(h);
            delayed(h, owner, 201, () -> {
                play(h, owner, Kind.VOID_SMOKE, Integer.MAX_VALUE);
                check(h, HunterVfx.activeCount(owner) == 1, "Overlong loop must start with a bounded TTL");
            }, () -> check(h, HunterVfx.activeCount(owner) == 0, "Even an overlong loop must expire within 200 ticks"));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void oneShotsExpireAtTheirAnimationLengths(GameTestHelper h) {
        whenModelsLoaded(h, () -> {
            ServerPlayer owner = owner(h);
            delayed(h, owner, 23, () -> {
                play(h, owner, Kind.ARC_FLASH, 200);
                play(h, owner, Kind.SOLAR_BURST, 200);
                check(h, HunterVfx.activeCount(owner) == 2, "Both one-shots must start");
                h.runAfterDelay(17, () -> {
                    try {
                        check(h, HunterVfx.activeCount(owner) == 1, "Arc must expire at 16 ticks while solar is still active");
                    } catch (RuntimeException | Error e) {
                        cleanup(owner);
                        throw e;
                    }
                });
            }, () -> check(h, HunterVfx.activeCount(owner) == 0, "Solar must expire at 22 ticks"));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void abilityCleanupCancelsOwnedVisuals(GameTestHelper h) {
        whenModelsLoaded(h, () -> {
            ServerPlayer owner = owner(h);
            ServerPlayer other = null;
            try {
                other = owner(h);
                play(h, owner, Kind.VOID_VORTEX, 60);
                play(h, other, Kind.VOID_SMOKE, 100);
                AbilityService.cleanup(owner);
                check(h, HunterVfx.activeCount(owner) == 0, "AbilityService.cleanup must cancel the owner's VFX");
                check(h, HunterVfx.activeCount(other) == 1, "Owner cleanup must preserve another owner's VFX");
                h.succeed();
            } finally {
                try {
                    cleanup(owner);
                } finally {
                    if (other != null) cleanup(other);
                }
            }
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void ownerCapEvictsOldestAndKeepsFourNewest(GameTestHelper h) {
        whenModelsLoaded(h, () -> {
            ServerPlayer owner = owner(h);
            delayed(h, owner, 5, () -> {
                // If the oldest is retained, it expires before the delayed assertion and leaves only three.
                play(h, owner, Kind.VOID_VORTEX, 2);
                for (int i = 0; i < 4; i++) {
                    play(h, owner, Kind.VOID_SMOKE, 100);
                    check(h, HunterVfx.activeCount(owner) == Math.min(i + 2, 4), "Owner may retain at most four VFX");
                }
            }, () -> check(h, HunterVfx.activeCount(owner) == 4, "The fifth VFX must evict the oldest, not a newer tracker"));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void rejectsDimensionMismatchAndInvalidNumbers(GameTestHelper h) {
        ServerPlayer owner = owner(h);
        try {
            ServerLevel level = h.getLevel();
            Vec3 position = owner.position();
            check(h, !HunterVfx.play(owner, otherLevel(h), position, Kind.ARC_FLASH, 1, 16),
                    "Owner and effect dimensions must match");
            for (double invalid : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY}) {
                for (Vec3 pos : new Vec3[]{new Vec3(invalid, 1, 1), new Vec3(1, invalid, 1), new Vec3(1, 1, invalid)}) {
                    check(h, !HunterVfx.play(owner, level, pos, Kind.ARC_FLASH, 1, 16), "Nonfinite coordinates must be rejected");
                }
            }
            for (double radius : new double[]{0, -1, Double.NaN, Double.POSITIVE_INFINITY,
                    Double.NEGATIVE_INFINITY, Double.MAX_VALUE, Double.MIN_VALUE}) {
                check(h, !HunterVfx.play(owner, level, position, Kind.ARC_FLASH, radius, 16),
                        "Invalid or unrepresentable radius must be rejected: " + radius);
            }
            for (int duration : new int[]{0, -1, Integer.MIN_VALUE}) {
                check(h, !HunterVfx.play(owner, level, position, Kind.VOID_SMOKE, 1, duration), "Nonpositive TTL must be rejected");
            }
            check(h, !HunterVfx.play(null, level, position, Kind.ARC_FLASH, 1, 16)
                    && !HunterVfx.play(owner, null, position, Kind.ARC_FLASH, 1, 16)
                    && !HunterVfx.play(owner, level, null, Kind.ARC_FLASH, 1, 16)
                    && !HunterVfx.play(owner, level, position, null, 1, 16), "Null inputs must fail safely");
            check(h, HunterVfx.activeCount(owner) == 0, "Rejected inputs must leave no active entries");
            h.succeed();
        } finally {
            cleanup(owner);
        }
    }

    private static void ownerInvalidation(GameTestHelper h, Consumer<ServerPlayer> invalidate) {
        whenModelsLoaded(h, () -> {
            ServerPlayer owner = owner(h);
            delayed(h, owner, 3, () -> {
                play(h, owner, Kind.VOID_SMOKE, 100);
                check(h, HunterVfx.activeCount(owner) == 1, "Lifecycle control must start active");
                invalidate.accept(owner);
                check(h, !HunterVfx.play(owner, h.getLevel(), owner.position(), Kind.VOID_SMOKE, 1, 100),
                        "Invalid owner must reject new VFX");
            }, () -> check(h, HunterVfx.activeCount(owner) == 0, "Invalid owner must lose existing VFX without a cleanup hook"));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void ownerDeathExpiresVisualWithoutDeathEvent(GameTestHelper h) {
        ownerInvalidation(h, owner -> owner.setHealth(0));
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void ownerRemovalExpiresVisual(GameTestHelper h) {
        ownerInvalidation(h, ServerPlayer::discard);
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void ownerDimensionChangeExpiresVisual(GameTestHelper h) {
        ownerInvalidation(h, owner -> owner.setServerLevel(otherLevel(h)));
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void ownerDisconnectExpiresVisual(GameTestHelper h) {
        ownerInvalidation(h, ServerPlayer::disconnect);
    }
}
