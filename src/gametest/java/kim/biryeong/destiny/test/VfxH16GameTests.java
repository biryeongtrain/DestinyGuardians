package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.fx.HunterVfx;
import kim.biryeong.destiny.fx.SuperVfx;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/** H16 step 4: embedded owners and real backend allocations, not real network/render performance. */
public final class VfxH16GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final Vec3 ORIGIN = new Vec3(2.5, 1, 6.5);

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    /** No fixtures are allocated while waiting for pack loading and other tests' effects to finish. */
    private static void start(GameTestHelper h, Consumer<Owners> scenario) {
        h.startSequence().thenWaitUntil(() -> {
            for (var kind : List.of(HunterVfx.Kind.VOID_VORTEX, HunterVfx.Kind.VOID_ANCHOR)) {
                check(h, BetterModel.model(kind.modelName()).isPresent(), "Waiting for " + kind.modelName());
            }
            check(h, HunterVfx.activeCount() == 0 && SuperVfx.activeCount() == 0,
                    "Wait for idle pools; never clear or evict another test's effects");
        }).thenExecute(() -> {
            Owners owners = new Owners(h);
            owners.guarded(() -> scenario.accept(owners));
        });
    }

    private static final class Owners implements AutoCloseable {
        final GameTestHelper h;
        final List<ServerPlayer> players = new ArrayList<>();
        boolean closed;

        Owners(GameTestHelper h) {
            this.h = h;
            h.runBeforeTestEnd(this::close);
        }

        ServerPlayer create() {
            ServerPlayer player = TestPlayers.create(h, ORIGIN, -90, 0);
            players.add(player);
            check(h, h.getLevel().getServer().getPlayerList().getPlayer(player.getUUID()) == null,
                    "Embedded fixture must remain outside PlayerList; it is not a real viewer");
            return player;
        }

        void guarded(Runnable action) {
            try {
                action.run();
            } catch (RuntimeException | Error failure) {
                try { close(); }
                catch (RuntimeException | Error cleanup) { failure.addSuppressed(cleanup); }
                throw failure;
            }
        }

        void after(int ticks, Runnable action) {
            h.runAfterDelay(ticks, () -> guarded(action));
        }

        void done(Runnable assertions) {
            try { assertions.run(); }
            finally { close(); }
            h.succeed();
        }

        @Override
        public void close() {
            if (closed) return;
            closed = true;
            RuntimeException failure = null;
            for (ServerPlayer player : players) {
                try {
                    // TestPlayers.remove delegates to AbilityService.cleanup for both pools.
                    TestPlayers.remove(player);
                } catch (RuntimeException cleanup) {
                    if (failure == null) failure = cleanup;
                    else failure.addSuppressed(cleanup);
                }
            }
            if (failure != null) throw failure;
        }
    }

    private static void counts(GameTestHelper h, ServerPlayer owner, int trackers, int beams) {
        check(h, HunterVfx.activeCount(owner) == trackers,
                "Expected " + trackers + " owned BetterModel trackers, got " + HunterVfx.activeCount(owner));
        check(h, SuperVfx.activeCount(owner) == beams,
                "Expected " + beams + " owned beam holders, got " + SuperVfx.activeCount(owner));
    }

    private static void tracker(GameTestHelper h, ServerPlayer owner, HunterVfx.Kind kind, int ticks) {
        check(h, HunterVfx.play(owner, owner.level(), owner.position(), kind, 1, ticks),
                "Allocate real BetterModel tracker for " + kind);
    }

    private static void beam(GameTestHelper h, ServerPlayer owner, int index, int ticks) {
        Vec3 start = owner.position().add(0, 1, 0);
        check(h, SuperVfx.trail(owner, start, start.add(2 + index, 0, 0), ticks),
                "Allocate a bounded real Polymer holder");
    }

    private static void pair(GameTestHelper h, ServerPlayer owner, int ticks) {
        tracker(h, owner, HunterVfx.Kind.VOID_ANCHOR, ticks);
        beam(h, owner, 0, ticks);
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void sevenOwnersExerciseIndependentGlobalCapsAndOldestEviction(GameTestHelper h) {
        start(h, owners -> {
            List<ServerPlayer> players = new ArrayList<>();
            for (int i = 0; i < 7; i++) players.add(owners.create());
            // Entire cap test, including cleanup, stays in this one callback: no other test can
            // allocate between the idle gate and our saturation/eviction assertions.
            for (int ownerIndex = 0; ownerIndex < 6; ownerIndex++) {
                ServerPlayer player = players.get(ownerIndex);
                for (int slot = 0; slot < 4; slot++) {
                    tracker(h, player, slot % 2 == 0 ? HunterVfx.Kind.VOID_VORTEX : HunterVfx.Kind.VOID_ANCHOR, 60);
                    beam(h, player, slot, 10);
                    check(h, HunterVfx.activeCount() <= 24 && SuperVfx.activeCount() <= 24,
                            "Neither pool may exceed its own 24-slot global bound");
                }
                counts(h, player, 4, 4);
            }
            check(h, HunterVfx.activeCount() == 24 && SuperVfx.activeCount() == 24,
                    "Combined capacity must be 24 trackers + 24 holders = 48, not 24");
            ServerPlayer newest = players.get(6);
            for (int slot = 0; slot < 4; slot++) {
                tracker(h, newest, HunterVfx.Kind.VOID_ANCHOR, 60);
                counts(h, players.getFirst(), 3 - slot, 4 - slot);
                beam(h, newest, slot, 10);
                counts(h, players.getFirst(), 3 - slot, 3 - slot);
                counts(h, newest, slot + 1, slot + 1);
                check(h, HunterVfx.activeCount() == 24 && SuperVfx.activeCount() == 24,
                        "Newest owner replaces the globally oldest owner independently in each pool");
            }
            for (int i = 1; i < 6; i++) counts(h, players.get(i), 4, 4);
            HunterVfx.cancelOwned(newest);
            counts(h, newest, 0, 4);
            check(h, HunterVfx.activeCount() == 20 && SuperVfx.activeCount() == 24,
                    "Tracker cancellation must leave the beam pool full");
            SuperVfx.cancelOwned(newest);
            check(h, HunterVfx.activeCount() == 20 && SuperVfx.activeCount() == 20,
                    "Beam cancellation must remove only its four holders");
            owners.close();
            check(h, HunterVfx.activeCount() == 0 && SuperVfx.activeCount() == 0,
                    "All fixture allocations must be released without global clearAll");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void ownerCapsAndCleanupPreserveOtherOwnerAndOtherPool(GameTestHelper h) {
        start(h, owners -> {
            ServerPlayer a = owners.create(), b = owners.create();
            pair(h, b, 10);
            for (int i = 0; i < 8; i++) {
                tracker(h, a, HunterVfx.Kind.VOID_ANCHOR, 60);
                beam(h, a, i, 10);
                counts(h, a, Math.min(4, i + 1), Math.min(4, i + 1));
                counts(h, b, 1, 1);
            }
            HunterVfx.cancelOwned(a);
            HunterVfx.cancelOwned(a);
            counts(h, a, 0, 4);
            counts(h, b, 1, 1);
            AbilityService.cleanup(a);
            owners.done(() -> {
                counts(h, a, 0, 0);
                counts(h, b, 1, 1);
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void normalTickExpiryIsIndependentForTwoOwnersAndBothPools(GameTestHelper h) {
        start(h, owners -> {
            ServerPlayer shortLived = owners.create(), longLived = owners.create();
            pair(h, shortLived, 2);
            pair(h, longLived, 10);
            counts(h, shortLived, 1, 1);
            counts(h, longLived, 1, 1);
            owners.after(1, () -> {
                counts(h, shortLived, 1, 1);
                counts(h, longLived, 1, 1);
            });
            owners.after(3, () -> {
                counts(h, shortLived, 0, 0);
                counts(h, longLived, 1, 1);
            });
            owners.after(11, () -> owners.done(() -> {
                counts(h, shortLived, 0, 0);
                counts(h, longLived, 0, 0);
            }));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void invalidOwnerGuardsDropBothPoolsWithoutDroppingHealthyOwner(GameTestHelper h) {
        start(h, owners -> {
            ServerPlayer dead = owners.create(), removed = owners.create(), moved = owners.create();
            ServerPlayer disconnected = owners.create(), healthy = owners.create();
            List<ServerPlayer> invalid = List.of(dead, removed, moved, disconnected);
            for (ServerPlayer player : List.of(dead, removed, moved, disconnected, healthy)) {
                pair(h, player, 10);
                counts(h, player, 1, 1);
            }
            ServerLevel other = h.getLevel().getServer().getLevel(
                    h.getLevel().dimension().equals(Level.NETHER) ? Level.OVERWORLD : Level.NETHER);
            check(h, other != null && other != h.getLevel(), "Second dimension required");
            dead.setHealth(0);
            removed.discard();
            moved.setServerLevel(other);
            disconnected.disconnect();
            // No cleanup calls or synthetic manager ticks before the assertion.
            owners.after(2, () -> owners.done(() -> {
                for (ServerPlayer player : invalid) counts(h, player, 0, 0);
                counts(h, healthy, 1, 1);
                for (ServerPlayer player : List.of(dead, removed, disconnected)) {
                    check(h, !HunterVfx.play(player, player.level(), player.position(),
                                    HunterVfx.Kind.VOID_ANCHOR, 1, 10), "Invalid owner must reject tracker creation");
                    Vec3 from = player.position();
                    check(h, !SuperVfx.trail(player, from, from.add(2, 0, 0), 10),
                            "Invalid owner must reject holder creation");
                    counts(h, player, 0, 0);
                }
            }));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void targetRadiusBoundaryRefreshAndExitAreOwnerIsolated(GameTestHelper h) {
        start(h, owners -> {
            ServerPlayer a = owners.create(), b = owners.create();
            ServerPlayer targetA = owners.create(), targetB = owners.create();
            Vec3 anchor = a.position();
            targetA.setPos(anchor.add(7, 0, 0));
            targetB.setPos(anchor.add(6.99, 0, 0));
            check(h, SuperVfx.link(a, anchor, targetA, 7, 12), "Exact radius boundary is inclusive");
            check(h, SuperVfx.link(b, anchor, targetB, 7, 12), "Inside-radius control link");
            for (int i = 0; i < 16; i++) {
                check(h, SuperVfx.link(a, anchor, targetA, 7, 12), "Refresh at boundary must succeed");
                counts(h, a, 0, 1);
                counts(h, b, 0, 1);
            }
            targetA.setPos(anchor.add(7.01, 0, 0));
            check(h, !SuperVfx.link(a, anchor, targetA, 7, 12), "Just outside radius cannot refresh");
            owners.after(2, () -> owners.done(() -> {
                counts(h, a, 0, 0);
                counts(h, b, 0, 1);
                targetA.setPos(anchor.add(7, 0, 0));
                check(h, SuperVfx.link(a, anchor, targetA, 7, 12), "Re-entry permits a new link");
                counts(h, a, 0, 1);
                counts(h, b, 0, 1);
            }));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void maximumBeamLengthAndRejectedGeometryPreserveBothOwners(GameTestHelper h) {
        start(h, owners -> {
            ServerPlayer a = owners.create(), b = owners.create();
            Vec3 from = a.position();
            beam(h, b, 0, 10);
            check(h, SuperVfx.trail(a, from, from.add(96, 0, 0), 10), "Exact 96-block maximum is inclusive");
            for (Vec3 end : List.of(from.add(96.001, 0, 0), from,
                    from.add(Double.NaN, 0, 0), from.add(Double.POSITIVE_INFINITY, 0, 0))) {
                check(h, !SuperVfx.trail(a, from, end, 10), "Reject invalid or overlong geometry");
                counts(h, a, 0, 1);
                counts(h, b, 0, 1);
            }
            owners.done(() -> {
                counts(h, a, 0, 1);
                counts(h, b, 0, 1);
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void cancelOneAnchorPreservesOtherAnchorTrailAndOtherOwner(GameTestHelper h) {
        start(h, owners -> {
            ServerPlayer a = owners.create(), b = owners.create(), target = owners.create();
            Vec3 anchor = a.position(), secondAnchor = anchor.add(0, 0, 1);
            target.setPos(anchor.add(3, 0, 0));
            check(h, SuperVfx.link(a, anchor, target, 7, 12), "First anchor");
            check(h, SuperVfx.link(a, secondAnchor, target, 7, 12), "Same target at a different anchor");
            check(h, SuperVfx.link(b, anchor, target, 7, 12), "Same anchor with a different owner");
            beam(h, a, 0, 10);
            counts(h, a, 0, 3);
            counts(h, b, 0, 1);
            SuperVfx.cancelLinks(a, anchor);
            SuperVfx.cancelLinks(a, anchor);
            counts(h, a, 0, 2);
            counts(h, b, 0, 1);
            owners.done(() -> {
                SuperVfx.cancelLinks(a, secondAnchor);
                counts(h, a, 0, 1); // The unrelated flame trail remains.
                counts(h, b, 0, 1);
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void twoOwnersSelectThreeNearestTargetsAndObserveSharedTargetDeath(GameTestHelper h) {
        start(h, owners -> {
            ServerPlayer a = owners.create(), b = owners.create();
            Vec3 anchor = a.position();
            List<ServerPlayer> targets = new ArrayList<>();
            for (int i = 1; i <= 5; i++) {
                ServerPlayer target = owners.create();
                target.setPos(anchor.add(i, 0, 0));
                targets.add(target);
            }
            // Reverse ordering ensures the cosmetic selection must sort by distance.
            List<net.minecraft.world.entity.LivingEntity> candidates = new ArrayList<>(targets.reversed());
            SuperVfx.tether(a, anchor, 7, candidates);
            SuperVfx.tether(b, anchor, 7, candidates);
            counts(h, a, 0, 3);
            counts(h, b, 0, 3);
            targets.getLast().setHealth(0); // Farthest target must not have a retained link.
            owners.after(2, () -> {
                counts(h, a, 0, 3);
                counts(h, b, 0, 3);
                targets.getFirst().setHealth(0); // Nearest target is shared by both owners.
            });
            owners.after(4, () -> owners.done(() -> {
                counts(h, a, 0, 2);
                counts(h, b, 0, 2);
                SuperVfx.cancelOwned(a);
                counts(h, a, 0, 0);
                counts(h, b, 0, 2);
            }));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void distantOwnerDoesNotCancelWorldAnchoredEffects(GameTestHelper h) {
        start(h, owners -> {
            ServerPlayer moving = owners.create(), control = owners.create();
            pair(h, moving, 10);
            pair(h, control, 10);
            Vec3 origin = moving.position();
            // This is owner validity, NOT a 48-block viewer spawn/despawn test: neither fixture is
            // in PlayerList. Real viewer distance, packets and rendering require separate clients.
            moving.setPos(origin.add(48.01, 0, 0));
            owners.after(2, () -> {
                counts(h, moving, 1, 1);
                counts(h, control, 1, 1);
                moving.setPos(origin.add(47.99, 0, 0));
            });
            owners.after(4, () -> owners.done(() -> {
                counts(h, moving, 1, 1);
                counts(h, control, 1, 1);
                check(h, moving.getHealth() == control.getHealth(), "Cosmetic movement test does not damage owners");
            }));
        });
    }
}
