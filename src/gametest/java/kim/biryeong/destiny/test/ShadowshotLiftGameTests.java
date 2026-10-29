package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.ShadowshotTiming;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.input.GuardianAction;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.function.IntConsumer;

/**
 * Real equipped Shadowshot sessions and collision-resolved native physics; no synthetic pose tokens,
 * manual global task/projectile/animation ticks, sleeps, or player-list registration.
 * While remotely owned, connection.tick() includes doTick's before/afterPhysics mixins AND the
 * connection's position-rewind wrapper. After ownership ends, direct doTick is intentional: these
 * embedded players have no vanilla client supplying the position packets required by that wrapper.
 * These tests do not establish client pixels or the exact delivery time of the restore-camera packet.
 */
public final class ShadowshotLiftGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final double EPS = 1.0e-5;
    private static final Input IDLE = new Input(false, false, false, false, false, false, false);

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static void loaded(GameTestHelper h, Runnable action) {
        h.startSequence().thenWaitUntil(() -> check(h,
                BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(), "Waiting for H21 hunter limb"))
                .thenExecute(() -> {
                    check(h, SuperCamera.ENABLED, "Lift tests require the vanilla server-side camera");
                    // Own the actual landing pad; older floor fixtures exposed air at relative y=0.
                    for (int x = 1; x <= 9; x++) {
                        for (int z = 1; z <= 9; z++) h.setBlock(x, 0, z, Blocks.STONE);
                    }
                    action.run();
                });
    }

    /** Snapshot at the native-physics -> ability boundary isolates writes made by the lift itself. */
    private record Frame(Vec3 position, Vec3 velocity, double fallDistance, boolean noGravity,
                         boolean flying, boolean invulnerable, Pose pose, float width, float height) {
        static Frame of(ServerPlayer p) {
            return new Frame(p.position(), p.getDeltaMovement(), p.fallDistance, p.isNoGravity(),
                    p.getAbilities().flying, p.isInvulnerable(), p.getPose(), p.getBbWidth(), p.getBbHeight());
        }
    }

    private static final class Fixture {
        final GameTestHelper h;
        final ServerPlayer player;
        final ServerLevel originalLevel;
        final Vec3 origin;
        final double targetY;
        final float yaw, pitch;
        final Pose pose;
        final float width, height;
        Frame beforeAbility;

        Fixture(GameTestHelper h, Element element, Vec3 relative, boolean ground, Vec3 velocity) {
            this.h = h;
            originalLevel = h.getLevel();
            player = TestPlayers.hunter(h, element, relative, 35, -18);
            TestCleanup.register(h, () -> {
                // setServerLevel below is an embedded-fixture transition, not a registered entity teleport.
                player.setServerLevel(originalLevel);
                TestPlayers.remove(player);
            });
            check(h, !originalLevel.getServer().getPlayerList().getPlayers().contains(player),
                    "Embedded owner must not receive a second natural player-list ability tick");
            Guardians.runtime(player).gcbClient = false;
            Guardians.runtime(player).gcbThirdPerson = false;
            player.setSpeed((float) player.getAttributeValue(Attributes.MOVEMENT_SPEED));
            player.setLastClientInput(IDLE);
            player.setOnGround(ground);
            player.setDeltaMovement(velocity);
            origin = player.position();
            targetY = origin.y + (ground ? .60 : .15);
            yaw = player.getYRot();
            pitch = player.getXRot();
            pose = player.getPose();
            width = player.getBbWidth();
            height = player.getBbHeight();
        }

        void cast() {
            Guardians.data(player).setSuperEnergy(1);
            check(h, AbilityService.use(player, AbilitySlot.SUPER) == AbilityService.Result.OK,
                    "Actual equipped super accepted");
            check(h, AbilityService.inSuper(player) && PlayerAnimations.isPlaying(player),
                    "Actual gameplay session and versioned limb are present");
            check(h, SimProjectile.activeCount(player) == 0, "Automatic windup must not release an immediate arrow");
        }

        void step() {
            if (SuperCamera.active(player)) {
                check(h, SuperCamera.move(player, new ServerboundMovePlayerPacket.Rot(yaw, pitch, false, false)),
                        "Native rotation heartbeat accepted");
                player.connection.tick(); // Exactly one native doTick through the real rewind wrapper.
            } else {
                player.doTick(); // Exactly one native step; no real vanilla position-packet producer exists.
            }
            beforeAbility = Frame.of(player);
            AbilityService.tickPlayer(player); // Exactly once per actual server tick, after native physics.
            invariants();
            TestPlayers.drain(player);
        }

        void invariants() {
            Frame b = beforeAbility;
            check(h, player.position().distanceToSqr(b.position) < EPS * EPS,
                    "Lift must set velocity, never teleport the actual body");
            Vec3 after = player.getDeltaMovement();
            check(h, Math.abs(after.x - b.velocity.x) < EPS && Math.abs(after.z - b.velocity.z) < EPS,
                    "Lift must preserve native horizontal momentum, including drag");
            check(h, player.fallDistance == b.fallDistance, "Ability tick must not reset accumulated native fall distance");
            check(h, player.isNoGravity() == b.noGravity && player.getAbilities().flying == b.flying
                            && !player.isNoGravity() && !player.getAbilities().flying,
                    "No noGravity or flying permission/state is granted");
            check(h, player.isInvulnerable() == b.invulnerable && !player.isInvulnerable()
                            && Guardians.runtime(player).invulnerableTicks == 0,
                    "Lift never grants vanilla or Guardian invulnerability");
            check(h, player.getPose() == b.pose
                            && player.getBbWidth() == b.width && player.getBbHeight() == b.height,
                    "Ability tick must not mutate the native pose or collision dimensions");
            if (player.isAlive()) check(h, player.getPose() == pose
                            && player.getBbWidth() == width && player.getBbHeight() == height,
                    "Crouch is visual only: living owner's collision dimensions stay unchanged");
            check(h, !player.noPhysics && !player.isPassenger() && player.getCamera() == player,
                    "No noclip, real mount, or foreign server camera");
            check(h, Math.abs(player.getYRot() - yaw) < EPS && Math.abs(player.getXRot() - pitch) < EPS,
                    "Hop preserves gameplay aim yaw and pitch");
        }

        void noVerticalWrite(String phase) {
            check(h, Math.abs(player.getDeltaMovement().y - beforeAbility.velocity.y) < EPS,
                    phase + ": no extra vertical write; native=" + beforeAbility.velocity
                            + ", after=" + player.getDeltaMovement());
        }

        void liftAt(int elapsed) {
            if (elapsed >= 2 && elapsed < ShadowshotTiming.RELEASE_TICKS) {
                double expected = Math.clamp(targetY - player.getY(), -.06, .22);
                check(h, Math.abs(player.getDeltaMovement().y - expected) < EPS,
                        "T+" + elapsed + " bounded vertical target: expected=" + expected
                                + ", actual=" + player.getDeltaMovement().y + ", y=" + player.getY());
            } else noVerticalWrite("Preparation/release/post-release T+" + elapsed);
        }

        void arrowAt(int elapsed) {
            if (elapsed > ShadowshotTiming.RELEASE_TICKS) return;
            check(h, SimProjectile.activeCount(player) == (elapsed == ShadowshotTiming.RELEASE_TICKS ? 1 : 0),
                    "Exactly one actual arrow at T+7, none earlier: T+" + elapsed);
            check(h, AbilityService.inSuper(player) == (elapsed < ShadowshotTiming.RELEASE_TICKS),
                    "Session ends at the actual T+7 release");
            if (elapsed == ShadowshotTiming.RELEASE_TICKS) checkRelease(h, player);
        }

        void cancelled() {
            check(h, !AbilityService.inSuper(player) && !SuperCamera.active(player)
                            && !PlayerAnimations.isPlaying(player), "Cancelled session, camera and limb stay absent");
            check(h, SimProjectile.activeCount(player) == 0, "No delayed cancelled arrow");
        }

        void restored() {
            check(h, !AbilityService.inSuper(player) && !SuperCamera.active(player)
                            && !PlayerAnimations.isPlaying(player) && !PlayerAnimations.ownerSeesLimb(player),
                    "Natural recovery releases session, limb and rear camera");
            check(h, SuperCamera.cameraPosition(player).distanceToSqr(player.getEyePosition()) < EPS * EPS,
                    "Released camera falls back to the actual owner's eye");
        }
    }

    /** Read-only observation, not a projectile tick or a substituted launch/pose token. */
    private static void checkRelease(GameTestHelper h, ServerPlayer player) {
        try {
            var active = SimProjectile.class.getDeclaredField("ACTIVE");
            var owner = SimProjectile.class.getDeclaredField("owner");
            var velocity = SimProjectile.class.getDeclaredField("velocity");
            active.setAccessible(true);
            owner.setAccessible(true);
            velocity.setAccessible(true);
            SimProjectile arrow = null;
            for (Object value : (List<?>) active.get(null)) {
                if (owner.get(value) == player && !((SimProjectile) value).isDone()) {
                    check(h, arrow == null, "Only one owned release projectile exists");
                    arrow = (SimProjectile) value;
                }
            }
            check(h, arrow != null, "Actual launched Shadowshot arrow is observable at T+7");
            // Explicit H21 pose contract. The separate unit gate ties RELEASE_DROP to the JSON root delta.
            Vec3 expectedOrigin = player.getEyePosition().add(0, -.2098875, 0);
            check(h, arrow.position().distanceToSqr(expectedOrigin) < EPS * EPS,
                    "Real T+7 arrow starts at H21's lowered nock, eyeY - .2098875m");
            check(h, ((Vec3) velocity.get(arrow)).distanceToSqr(player.getLookAngle().scale(2.6)) < EPS * EPS,
                    "Lowering the nock changes origin only, never the gameplay look direction/speed");
        } catch (ReflectiveOperationException e) {
            throw new AssertionError("Cannot observe actual Shadowshot release projectile", e);
        }
    }

    /** Unique callbacks, once per real server tick; assertions never run inside swallowed Tasks callbacks. */
    private static void ticks(GameTestHelper h, List<Fixture> fixtures, int total, IntConsumer afterTick) {
        int start = h.getLevel().getServer().getTickCount();
        // Pre-register the whole sequence; never insert callbacks while fastutil is iterating.
        var sequence = h.startSequence();
        for (int elapsed = 1; elapsed <= total; elapsed++) {
            final int age = elapsed;
            sequence.thenExecuteAfter(1, () -> {
                check(h, h.getLevel().getServer().getTickCount() - start == age,
                        "Exactly one physics and ability step per real server tick: T+" + age);
                fixtures.forEach(Fixture::step);
                afterTick.accept(age);
                if (age == total) h.succeed();
            });
        }
    }

    private static int landingDeadline() {
        double seconds = BetterModel.limb(HunterModelAssets.MODEL_NAME).orElseThrow()
                .animation("h15_super_void_attack").orElseThrow().length();
        return Math.max(60, (int) Math.ceil(seconds * 20) + 20);
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void groundedHopUsesConnectedPhysicsCapsAtPointSixAndReleasesOnlyOnSeven(GameTestHelper h) {
        loaded(h, () -> {
            Fixture f = new Fixture(h, Element.VOID, new Vec3(4.5, 1, 4.5), true, new Vec3(.04, 0, .025));
            f.cast();
            check(h, SuperCamera.active(f.player), "Ground hop uses the actual rear-camera path");
            double[] maximum = {f.origin.y};
            boolean[] landed = {false};
            int deadline = landingDeadline();
            ticks(h, List.of(f), deadline, elapsed -> {
                f.liftAt(elapsed);
                f.arrowAt(elapsed);
                maximum[0] = Math.max(maximum[0], f.player.getY());
                check(h, maximum[0] <= f.origin.y + .61, "Actual connected body must not overshoot the .60m hop");
                if (elapsed == 1) check(h, Math.abs(f.player.getY() - f.origin.y) < EPS,
                        "T+1 is a grounded preparation tick, not an immediate jump");
                if (elapsed == 4) check(h, f.player.getY() > f.origin.y + .3,
                        "Native connection wrapper must retain the actual hop instead of rewinding it");
                if (elapsed > 7 && f.player.onGround()) landed[0] = true;
                if (elapsed == deadline) {
                    check(h, maximum[0] >= f.origin.y + .5 && landed[0]
                                    && Math.abs(f.player.getY() - f.origin.y) < EPS,
                            "Visible-sized small hop returns to the actual collision floor");
                    f.restored();
                }
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void fallingCastBrieflyAssistsWithoutFlightImmunityOrFallDistanceReset(GameTestHelper h) {
        loaded(h, () -> {
            Fixture f = new Fixture(h, Element.VOID, new Vec3(4.5, 5, 4.5), false, new Vec3(.025, -.30, .015));
            f.player.fallDistance = 2.75; // Existing fall, not a reset or a lift granted by the fixture.
            f.cast();
            double[] previousY = {f.origin.y}, releaseY = {Double.NaN};
            boolean[] assistedRise = {false}, landed = {false};
            int deadline = landingDeadline();
            ticks(h, List.of(f), deadline, elapsed -> {
                f.liftAt(elapsed);
                f.arrowAt(elapsed);
                check(h, f.player.getY() <= f.origin.y + .16, "Air target is only origin + .15m, not ground + .60m");
                if (elapsed == 1) check(h, f.player.getY() < f.origin.y && f.player.fallDistance >= 2.75,
                        "Cast begins in a real accumulated native fall");
                if (elapsed >= 3 && elapsed <= 7 && f.player.getY() > previousY[0] + EPS) assistedRise[0] = true;
                previousY[0] = f.player.getY();
                if (elapsed == 3) {
                    float health = f.player.getHealth();
                    check(h, f.player.hurtServer(f.player.level(), f.player.damageSources().generic(), 1),
                            "A mid-draw native damage call is not blocked by cosmetic lift");
                    check(h, f.player.getHealth() < health, "Midair Shadowshot grants no damage immunity");
                }
                if (elapsed == 7) releaseY[0] = f.player.getY();
                if (elapsed == 10) check(h, f.player.getY() < releaseY[0] - .1
                                && f.player.getDeltaMovement().y < 0,
                        "Native gravity resumes descending after T+7; no constant hover/free flight");
                if (elapsed > 7 && f.player.onGround()) landed[0] = true;
                if (elapsed == deadline) {
                    check(h, assistedRise[0] && landed[0] && f.player.isAlive(), "Brief actual air assist, then native landing");
                    f.restored();
                }
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void lowCeilingAbandonsHopWithoutNoclipButStillReleasesOnSeven(GameTestHelper h) {
        loaded(h, () -> {
            for (int x = 3; x <= 5; x++) for (int z = 3; z <= 5; z++) h.setBlock(x, 3, z, Blocks.STONE);
            Fixture f = new Fixture(h, Element.VOID, new Vec3(4.5, 1, 4.5), true, Vec3.ZERO);
            check(h, f.player.level().noCollision(f.player, f.player.getBoundingBox())
                            && !f.player.level().noCollision(f.player, f.player.getBoundingBox().move(0, .25, 0)),
                    "Fixture fits the unchanged hitbox, but its .25m upward probe hits the ceiling");
            f.cast();
            ticks(h, List.of(f), 12, elapsed -> {
                f.noVerticalWrite("Low ceiling abandons the assist permanently");
                f.arrowAt(elapsed);
                check(h, Math.abs(f.player.getY() - f.origin.y) < EPS
                                && f.player.getBoundingBox().maxY < h.absoluteVec(new Vec3(4, 3, 4)).y,
                        "Real collision body stays below the low ceiling");
                if (elapsed == 3) {
                    // Clearing the obstacle after rejection must not resurrect this draw's lift.
                    for (int x = 3; x <= 5; x++) for (int z = 3; z <= 5; z++) h.setBlock(x, 3, z, Blocks.AIR);
                }
            });
        });
    }

    private static void cancelAt(GameTestHelper h, int cancelTick) {
        loaded(h, () -> {
            Fixture f = new Fixture(h, Element.VOID, new Vec3(4.5, 1, 4.5), true, Vec3.ZERO);
            f.cast();
            double[] cancelY = {Double.NaN};
            ticks(h, List.of(f), 24, elapsed -> {
                if (elapsed <= cancelTick) f.liftAt(elapsed);
                else f.noVerticalWrite("No late lift write after explicit cancellation at T+" + cancelTick);
                if (elapsed == cancelTick) {
                    cancelY[0] = f.player.getY();
                    AbilityService.endSuper(f.player);
                }
                if (elapsed >= cancelTick) {
                    f.cancelled();
                    // Existing upward momentum at T+4 is legitimate vanilla inertia, not a late write.
                    check(h, f.player.getY() <= cancelY[0] + (cancelTick == 1 ? EPS : .45),
                            "Cancellation allows only the short residual ballistic arc, never renewed hover");
                }
                if (elapsed == 24) check(h, f.player.onGround() && Math.abs(f.player.getY() - f.origin.y) < EPS,
                        "Cancelled hop ultimately lands under normal gravity");
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void cancellingPreparationAtOneCannotStartLateLiftOrArrow(GameTestHelper h) { cancelAt(h, 1); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void cancellingMidHopAtFourKeepsOnlyVanillaInertiaAndNoDelayedArrow(GameTestHelper h) { cancelAt(h, 4); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void deathAndDimensionCleanupRevokePendingAssistAndArrow(GameTestHelper h) {
        loaded(h, () -> {
            Fixture dead = new Fixture(h, Element.VOID, new Vec3(3.5, 5, 4.5), false, new Vec3(0, -.1, 0));
            Fixture moved = new Fixture(h, Element.VOID, new Vec3(7.5, 5, 4.5), false, new Vec3(0, -.1, 0));
            ServerLevel other = h.getLevel().getServer().getLevel(
                    h.getLevel().dimension().equals(Level.NETHER) ? Level.OVERWORLD : Level.NETHER);
            check(h, other != null, "A second server dimension is available");
            dead.cast();
            moved.cast();
            ticks(h, List.of(dead, moved), 14, elapsed -> {
                for (Fixture f : List.of(dead, moved)) {
                    if (elapsed <= 3) f.liftAt(elapsed);
                    else {
                        f.noVerticalWrite("No assist write after death/dimension cleanup");
                        f.cancelled();
                    }
                }
                if (elapsed == 3) {
                    dead.player.setHealth(0); // tickPlayer's real dead-owner branch must clean this one up.
                    moved.player.setServerLevel(other);
                    // setServerLevel is not an actual Fabric teleport event for an unregistered player.
                    // Invoke the same cleanup hook used by AFTER_PLAYER_CHANGE_LEVEL, not a fake event claim.
                    AbilityService.cleanup(moved.player);
                    moved.cancelled();
                }
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void arcAndSolarPrimaryNeverAcquireShadowshotVerticalAssist(GameTestHelper h) {
        loaded(h, () -> {
            Fixture arc = new Fixture(h, Element.ARC, new Vec3(3.5, 1, 4.5), true, Vec3.ZERO);
            Fixture solar = new Fixture(h, Element.SOLAR, new Vec3(7.5, 1, 4.5), true, Vec3.ZERO);
            arc.cast();
            solar.cast();
            check(h, SuperCamera.active(arc.player) && !SuperCamera.active(solar.player),
                    "Arc retains rear camera; Solar remains native first person");
            ticks(h, List.of(arc, solar), 24, elapsed -> {
                for (Fixture f : List.of(arc, solar)) {
                    f.noVerticalWrite("Non-Void deploy, queued primary, contact and recovery T+" + elapsed);
                    check(h, Math.abs(f.player.getY() - f.origin.y) < EPS
                                    && SimProjectile.activeCount(f.player) == 0,
                            "Non-Void cast never hops or spawns a Shadowshot arrow");
                }
                check(h, !SuperCamera.active(solar.player), "Solar stays first person after every native tick");
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void strongExternalImpulseAndRealAirJumpRelinquishRatherThanClampMomentum(GameTestHelper h) {
        loaded(h, () -> {
            Fixture impulse = new Fixture(h, Element.VOID, new Vec3(3.5, 1, 4.5), true, Vec3.ZERO);
            Fixture jump = new Fixture(h, Element.VOID, new Vec3(7.5, 1, 4.5), true, Vec3.ZERO);
            impulse.cast();
            jump.cast();
            ticks(h, List.of(impulse, jump), 12, elapsed -> {
                for (Fixture f : List.of(impulse, jump)) {
                    if (elapsed <= 3) f.liftAt(elapsed);
                    else f.noVerticalWrite("Deliberate jump/strong external impulse permanently wins");
                    f.arrowAt(elapsed);
                }
                if (elapsed == 3) {
                    impulse.player.setDeltaMovement(new Vec3(.12, .8, -.07));
                    // No direct position change: next connection.tick resolves this external velocity natively.
                    check(h, AbilityService.use(jump.player, AbilitySlot.JUMP) == AbilityService.Result.OK,
                            "Real equipped Hunter air jump is allowed during the pending super");
                    check(h, jump.player.getDeltaMovement().y > .4, "Fixture jump actually supplies a strong upward impulse");
                }
                if (elapsed == 4) {
                    for (Fixture f : List.of(impulse, jump)) check(h, f.beforeAbility.velocity.y > .4,
                            "Strong upward momentum is still present at the actual lift boundary");
                }
            });
        });
    }
}
