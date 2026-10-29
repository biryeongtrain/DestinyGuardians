package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.SuperAttackTiming;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.input.GuardianAction;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.phys.Vec3;

import java.util.function.IntConsumer;

/**
 * Actual Arc activation and server-tick deployment boundary. Input is injected into the native
 * last-client-input state and observed at beforePhysics, not supplied by a native keyboard/client.
 * These hook assertions establish input gating and unchanged momentum/gravity flags, not travel
 * integration or the rendered activation pose. Global animation/camera ticks remain server-owned.
 */
public final class ArcDeployGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final double EPS = 1.0e-6;
    private static final float HEALTH = 400;
    private static final Input MOVE_JUMP = new Input(true, false, true, false, true, false, false);

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static void loaded(GameTestHelper h, Runnable test) {
        h.startSequence().thenWaitUntil(() -> check(h,
                BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(), "Waiting for hunter limb"))
                .thenExecute(() -> {
                    check(h, SuperCamera.ENABLED, "Arc deploy tests require the server-side camera");
                    check(h, SuperAttackTiming.ARC_DEPLOY > 1, "Deployment must have a pre-deadline tick");
                    test.run();
                });
    }

    private static final class Fixture {
        final GameTestHelper h;
        final ServerPlayer player;
        final int start;

        Fixture(GameTestHelper h) {
            this.h = h;
            player = TestPlayers.hunter(h, Element.ARC, new Vec3(2.5, 1, 6.5), -90, 0);
            TestCleanup.register(h, () -> TestPlayers.remove(player));
            check(h, !h.getLevel().getServer().getPlayerList().getPlayers().contains(player),
                    "Embedded owner must not receive a second natural PlayerList ability tick");
            Guardians.runtime(player).gcbClient = false;
            Guardians.runtime(player).gcbThirdPerson = false;
            player.setLastClientInput(MOVE_JUMP);
            player.setDeltaMovement(new Vec3(.08, -.12, .03));
            Vec3 velocity = player.getDeltaMovement();
            Guardians.data(player).setSuperEnergy(1);
            start = h.getLevel().getServer().getTickCount();
            check(h, AbilityService.use(player, AbilitySlot.SUPER) == AbilityService.Result.OK,
                    "Equipped Arc super actually activates");
            check(h, AbilityService.inSuper(player) && Guardians.data(player).superEnergy() == 0,
                    "Activation creates the gameplay session and consumes super energy");
            check(h, SuperCamera.active(player) && PlayerAnimations.isPlaying(player)
                            && PlayerAnimations.ownerSeesLimb(player),
                    "Activated Arc owns the camera and exposes its real limb to a vanilla owner");
            check(h, player.getDeltaMovement().equals(velocity), "Activation preserves existing momentum");
            gate(true);
        }

        int elapsed() {
            return h.getLevel().getServer().getTickCount() - start;
        }

        void heartbeat() {
            check(h, SuperCamera.move(player,
                            new ServerboundMovePlayerPacket.Rot(player.getYRot(), player.getXRot(), false, false)),
                    "Active camera consumes a rotation heartbeat");
        }

        void gate(boolean blocked) {
            check(h, SuperCamera.movementBlocked(player) == blocked,
                    "Movement deadline at actual server T+" + elapsed() + ": blocked=" + blocked);
            Vec3 position = player.position(), velocity = player.getDeltaMovement();
            double fallDistance = player.fallDistance;
            player.setLastClientInput(MOVE_JUMP);
            // Seed stale values too: the hook must clear existing movement/jump while blocked.
            player.xxa = -.75f;
            player.zza = -.5f;
            player.setJumping(true);
            SuperCamera.beforePhysics(player);
            if (blocked) {
                check(h, player.xxa == 0 && player.zza == 0 && !player.isJumping(),
                        "Deployment clears horizontal axes and jump at beforePhysics");
            } else {
                double diagonal = 1 / Math.sqrt(2);
                check(h, Math.abs(player.xxa - diagonal) < EPS
                                && Math.abs(player.zza - diagonal) < EPS && player.isJumping(),
                        "At/after deadline the same stored input reaches horizontal axes and jump");
            }
            check(h, player.getLastClientInput().equals(MOVE_JUMP), "Gate preserves stored input for roaming");
            check(h, player.position().equals(position) && player.getDeltaMovement().equals(velocity),
                    "beforePhysics gates input without teleporting or clearing horizontal/vertical momentum");
            check(h, !player.isNoGravity() && !player.getAbilities().flying
                            && player.fallDistance == fallDistance,
                    "Gate grants no gravity/flight override and does not reset fall distance");
        }

        void primary() {
            check(h, AbilityService.perform(player, GuardianAction.PRIMARY), "Actual Arc session accepts PRIMARY");
        }

        void cancelled() {
            check(h, !AbilityService.inSuper(player) && !SuperCamera.active(player)
                            && !SuperCamera.movementBlocked(player) && !PlayerAnimations.isPlaying(player),
                    "Cancellation/death releases gameplay session, camera, movement gate and animation");
            check(h, player.xxa == 0 && player.zza == 0 && !player.isJumping(),
                    "Release clears owned movement/jump values");
            // Once ownership is gone this hook must not retain a hidden deployment gate.
            player.xxa = .25f;
            player.zza = -.5f;
            player.setJumping(true);
            SuperCamera.beforePhysics(player);
            check(h, player.xxa == .25f && player.zza == -.5f && player.isJumping(),
                    "Unowned beforePhysics leaves caller movement values alone");
            player.xxa = player.zza = 0;
            player.setJumping(false);
        }
    }

    /** Unique callbacks use real server ticks; tickPlayer never stands in for a server clock. */
    private static void ticks(Fixture f, int next, int total, IntConsumer atTick) {
        f.h.runAfterDelay(1, () -> {
            check(f.h, f.elapsed() == next, "Callback runs exactly once at actual server T+" + next);
            atTick.accept(next);
            TestPlayers.drain(f.player);
            if (next == total) f.h.succeed();
            else ticks(f, next + 1, total, atTick);
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void actualArcBlocksUntilExactServerDeadlineThenRoamsWithCamera(GameTestHelper h) {
        loaded(h, () -> {
            Fixture f = new Fixture(h);
            ticks(f, 1, SuperAttackTiming.ARC_DEPLOY + 2, elapsed -> {
                f.heartbeat();
                // Observe the boundary BEFORE advancing the embedded owner's ability age.
                f.gate(elapsed < SuperAttackTiming.ARC_DEPLOY);
                AbilityService.tickPlayer(f.player);
                check(h, AbilityService.inSuper(f.player) && SuperCamera.active(f.player),
                        "Unlock keeps the roaming Arc session and combat camera active");
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void movementDeadlineExpiresEvenWhenEmbeddedAbilityAgeIsNotAdvanced(GameTestHelper h) {
        loaded(h, () -> {
            Fixture f = new Fixture(h);
            float remaining = Guardians.runtime(f.player).superSession.remaining();
            ticks(f, 1, SuperAttackTiming.ARC_DEPLOY, elapsed -> {
                f.heartbeat();
                // Deliberately do not call tickPlayer: deadline must use server time, not session age.
                check(h, Guardians.runtime(f.player).superSession.remaining() == remaining,
                        "Embedded ability age remains unchanged while the actual server clock advances");
                f.gate(elapsed < SuperAttackTiming.ARC_DEPLOY);
                check(h, SuperCamera.active(f.player), "Clock-only expiry retains camera ownership");
            });
        });
    }

    private static Husk target(Fixture f) {
        Husk target = f.h.spawn(EntityTypes.HUSK, new Vec3(5.5, 1, 6.5));
        TestCleanup.register(f.h, () -> { Statuses.forget(target); target.discard(); });
        target.setNoAi(true);
        target.setNoGravity(true);
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HEALTH);
        target.getAttribute(Attributes.ARMOR).setBaseValue(0);
        target.setHealth(HEALTH);
        return target;
    }

    private static void health(GameTestHelper h, Husk target, float expected, int elapsed) {
        check(h, Math.abs(target.getHealth() - expected) < .01f,
                "Arc damage at server T+" + elapsed + ": expected health=" + expected + ", got=" + target.getHealth());
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void earlyPrimaryCoalescesWithoutDamageDuringDeployOrContactWindup(GameTestHelper h) {
        loaded(h, () -> {
            Fixture f = new Fixture(h);
            Husk target = target(f);
            float damage = (float) AbilityService.equipped(f.player, AbilitySlot.SUPER).orElseThrow().param("damage", 16);
            for (int i = 0; i < 6; i++) f.primary();
            health(h, target, HEALTH, 0);
            int hitAt = SuperAttackTiming.ARC_DEPLOY + SuperAttackTiming.ARC_CONTACT;
            ticks(f, 1, hitAt + 2, elapsed -> {
                f.heartbeat();
                f.gate(elapsed < SuperAttackTiming.ARC_DEPLOY);
                AbilityService.tickPlayer(f.player);
                health(h, target, elapsed < hitAt ? HEALTH : HEALTH - damage, elapsed);
                if (elapsed < SuperAttackTiming.ARC_DEPLOY) f.primary();
            });
        });
    }

    private static void cancellation(GameTestHelper h, int mode) {
        loaded(h, () -> {
            Fixture f = new Fixture(h);
            Husk target = target(f);
            f.primary();
            int cancelAt = SuperAttackTiming.ARC_DEPLOY - 1;
            ticks(f, 1, SuperAttackTiming.ARC_DEPLOY + SuperAttackTiming.ARC_CONTACT + 3, elapsed -> {
                if (elapsed <= cancelAt) {
                    f.heartbeat();
                    f.gate(true);
                }
                if (elapsed == cancelAt) {
                    if (mode == 0) AbilityService.endSuper(f.player);
                    else if (mode == 1) AbilityService.cleanup(f.player);
                    else f.player.setHealth(0); // tickPlayer must detect death; no manual death cleanup.
                    if (mode != 2) f.cancelled();
                }
                AbilityService.tickPlayer(f.player);
                if (elapsed >= cancelAt) f.cancelled();
                health(h, target, HEALTH, elapsed);
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void explicitEndDuringDeployReleasesGateAndDropsQueuedDamage(GameTestHelper h) {
        cancellation(h, 0);
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void cleanupDuringDeployReleasesGateAndDropsQueuedDamage(GameTestHelper h) {
        cancellation(h, 1);
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void deathDuringDeployReleasesGateAndDropsQueuedDamage(GameTestHelper h) {
        cancellation(h, 2);
    }
}
