package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.ShadowshotTiming;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.input.GuardianAction;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerInputPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/** Server-side camera ownership/physics regressions; not proof of vanilla client rendering or hardware input. */
public final class SuperCameraGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final double EPS = 1.0e-5;
    private static final Input IDLE = new Input(false, false, false, false, false, false, false);
    private static final Input FORWARD = new Input(true, false, false, false, false, false, false);

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static void loaded(GameTestHelper h, Runnable action) {
        h.startSequence().thenWaitUntil(() -> check(h, BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),
                "Waiting for camera test player limb")).thenExecute(action);
    }

    private static ServerPlayer owner(GameTestHelper h, Element element, Vec3 relative) {
        ServerPlayer p = TestPlayers.hunter(h, element, relative, -90, 0);
        TestCleanup.register(h, () -> TestPlayers.remove(p));
        Guardians.runtime(p).gcbClient = false;
        Guardians.runtime(p).gcbThirdPerson = false;
        return p;
    }

    private static ServerPlayer owner(GameTestHelper h) {
        return owner(h, Element.ARC, new Vec3(2.5, 1, 6.5));
    }

    private static void ready(GameTestHelper h, ServerPlayer p, Element element) {
        check(h, SuperCamera.ENABLED, "Camera tests require destiny.superCamera=true");
        check(h, PlayerAnimations.loop(p, "super_" + element.getSerializedName()), "Real ready loop starts");
        check(h, SuperCamera.start(p, element), "Camera starts");
        check(h, SuperCamera.active(p), "Camera owns player");
    }

    private static void actualBody(GameTestHelper h, ServerPlayer p) {
        check(h, p.getCamera() == p, "Server camera remains the actual player");
        check(h, !p.isPassenger() && p.getPassengers().isEmpty(), "Fake mount is not a server passenger graph");
    }

    private static void unchanged(GameTestHelper h, ServerPlayer p, Vec3 before) {
        check(h, p.position().distanceToSqr(before) < EPS * EPS, "Packets/camera must not translate actual body");
        actualBody(h, p);
    }

    private static void heartbeat(GameTestHelper h, ServerPlayer p) {
        check(h, SuperCamera.move(p, new ServerboundMovePlayerPacket.Rot(p.getYRot(), p.getXRot(), false, false)),
                "Owned Rot packet consumed");
        PlayerAnimations.tick(h.getLevel().getServer());
        SuperCamera.tick(h.getLevel().getServer());
        check(h, SuperCamera.active(p), "Ready animation and rotation heartbeat retain camera");
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w258_camera_clock")
    public void solarIsStrictNoOp(GameTestHelper h) {
        ServerPlayer p = owner(h, Element.SOLAR, new Vec3(2.5, 1, 6.5));
        Vec3 before = p.position();
        int count = SuperCamera.activeCount();
        check(h, SuperCamera.start(p, Element.SOLAR), "Solar accepts without camera ownership");
        check(h, !SuperCamera.active(p) && SuperCamera.activeCount() == count, "Solar adds no session");
        check(h, !PlayerAnimations.ownerSeesLimb(p), "Vanilla Solar owner visibility unchanged");
        check(h, !SuperCamera.move(p, new ServerboundMovePlayerPacket.Rot(30, 10, true, false)),
                "Unowned packets remain vanilla");
        unchanged(h, p, before);
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w258_camera_clock")
    public void arcVanillaOwnerSeesLimbWithoutRealMount(GameTestHelper h) {
        loaded(h, () -> {
            ServerPlayer p = owner(h);
            Vec3 before = p.position();
            ready(h, p, Element.ARC);
            check(h, !Guardians.runtime(p).gcbClient && !Guardians.runtime(p).gcbThirdPerson,
                    "Fixture has no GCB camera capability");
            check(h, PlayerAnimations.ownerSeesLimb(p), "Camera ownership makes vanilla owner see limb");
            Vec3 camera = SuperCamera.cameraPosition(p);
            check(h, Double.isFinite(camera.x) && Double.isFinite(camera.y) && Double.isFinite(camera.z),
                    "Camera position finite");
            check(h, camera.distanceToSqr(p.getEyePosition()) > .1, "Camera offset from actual eye");
            heartbeat(h, p);
            unchanged(h, p, before);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w258_camera_clock")
    public void rotationWrapsClampsAndRejectsNonfinitePairs(GameTestHelper h) {
        loaded(h, () -> {
            ServerPlayer p = owner(h);
            ready(h, p, Element.ARC);
            Vec3 before = p.position();
            check(h, SuperCamera.move(p, new ServerboundMovePlayerPacket.Rot(450, 120, true, true)), "Rot consumed");
            check(h, p.getYRot() == 90 && p.getXRot() == 90 && p.getYHeadRot() == 90, "Wrap yaw and clamp pitch");
            check(h, SuperCamera.move(p, new ServerboundMovePlayerPacket.Rot(-450, -120, false, false)), "Second Rot consumed");
            check(h, p.getYRot() == -90 && p.getXRot() == -90, "Negative yaw and pitch bounded");
            int accepted = SuperCamera.rotations(p);
            check(h, accepted == 2, "Count only accepted rotation pairs");
            float[][] invalid = {{Float.NaN, 0}, {0, Float.NaN}, {Float.POSITIVE_INFINITY, 0},
                    {0, Float.NEGATIVE_INFINITY}};
            for (float[] pair : invalid) {
                check(h, SuperCamera.move(p, new ServerboundMovePlayerPacket.Rot(pair[0], pair[1], true, true)),
                        "Malformed owned packet still consumed");
                check(h, SuperCamera.rotations(p) == accepted && p.getYRot() == -90 && p.getXRot() == -90,
                        "Nonfinite pair changes neither aim nor accepted count");
            }
            unchanged(h, p, before);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w258_camera_clock")
    public void positionGroundAndCollisionClaimsAreIgnored(GameTestHelper h) {
        loaded(h, () -> {
            ServerPlayer p = owner(h);
            ready(h, p, Element.ARC);
            p.setOnGround(true);
            p.horizontalCollision = false;
            Vec3 before = p.position(), velocity = p.getDeltaMovement();
            ServerboundMovePlayerPacket[] packets = {
                    new ServerboundMovePlayerPacket.Pos(before.x + 1000, before.y + 1000, before.z, false, true),
                    new ServerboundMovePlayerPacket.Pos(Double.NaN, Double.POSITIVE_INFINITY, Double.NaN, false, true),
                    new ServerboundMovePlayerPacket.PosRot(Double.NaN, before.y - 1000, before.z + 1000,
                            35, 20, false, true)};
            for (ServerboundMovePlayerPacket packet : packets) {
                check(h, SuperCamera.move(p, packet), "Every owned position packet consumed");
                unchanged(h, p, before);
                check(h, p.onGround() && !p.horizontalCollision, "Packet ground/collision claims ignored");
                check(h, p.getDeltaMovement().distanceToSqr(velocity) < EPS * EPS, "Packet cannot set velocity");
            }
            check(h, p.getYRot() == 35 && p.getXRot() == 20 && SuperCamera.rotations(p) == 1,
                    "PosRot accepts only its finite angles");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w258_camera_clock")
    public void stopIsIdempotentAndOwnerLocal(GameTestHelper h) {
        loaded(h, () -> {
            ServerPlayer p = owner(h), other = owner(h);
            ready(h, p, Element.ARC);
            ready(h, other, Element.ARC);
            Vec3 before = p.position();
            int count = SuperCamera.activeCount();
            p.setLastClientInput(FORWARD);
            SuperCamera.beforePhysics(p);
            check(h, p.zza > 0, "Fixture has live movement input");
            SuperCamera.stop(p);
            SuperCamera.stop(p);
            check(h, !SuperCamera.active(p) && SuperCamera.activeCount() == count - 1, "Repeated stop removes only one session");
            check(h, p.xxa == 0 && p.zza == 0, "Stop clears movement axes");
            check(h, SuperCamera.cameraPosition(p).distanceToSqr(p.getEyePosition()) < EPS * EPS,
                    "Inactive camera falls back to real eye");
            check(h, !PlayerAnimations.ownerSeesLimb(p), "Vanilla owner view restored");
            check(h, !SuperCamera.move(p, new ServerboundMovePlayerPacket.Rot(70, 20, true, false)), "Stop returns packet control");
            heartbeat(h, other);
            check(h, PlayerAnimations.isPlaying(other), "Other owner animation unaffected");
            unchanged(h, p, before);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w258_camera_clock")
    public void flyingRejectsSuperWithoutSpendingEnergy(GameTestHelper h) {
        ServerPlayer p = owner(h);
        Guardians.data(p).setSuperEnergy(1f);
        p.getAbilities().flying = true;
        Vec3 before = p.position();
        check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.FAILED, "Unsupported flying state rejects actual ability");
        check(h, Guardians.data(p).superEnergy() == 1f, "Rejected camera spends no super energy");
        check(h, !SuperCamera.active(p) && !AbilityService.inSuper(p), "Rejection creates no camera/gameplay session");
        unchanged(h, p, before);
        h.succeed();
    }

    private static void atRest(ServerPlayer p) {
        // Fresh TestPlayers have not had Player.aiStep initialize speed from the native attribute yet.
        // Initialize that normal fixture state, never momentum or a direct travel/move call.
        p.setSpeed((float) p.getAttributeValue(Attributes.MOVEMENT_SPEED));
        p.setOnGround(true);
        p.setDeltaMovement(Vec3.ZERO);
        p.setLastClientInput(IDLE);
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w258_camera_clock")
    public void nativeSingleTickConsumesKeysFromRestAndCollides(GameTestHelper h) {
        loaded(h, () -> {
            h.setBlock(3, 1, 6, Blocks.STONE);
            h.setBlock(3, 2, 6, Blocks.STONE);
            ServerPlayer forward = owner(h, Element.ARC, new Vec3(2.5, 1, 3.5));
            ServerPlayer strafe = owner(h, Element.ARC, new Vec3(6.5, 1, 6.5));
            ServerPlayer blocked = owner(h, Element.ARC, new Vec3(2.69, 1, 6.5));
            for (ServerPlayer p : new ServerPlayer[]{forward, strafe, blocked}) {
                ready(h, p, Element.ARC);
                atRest(p);
            }
            // The native last-client-input, not the separate Guardian input cache, drives physics.
            Guardians.runtime(forward).lastInput = new Input(false, true, false, false, false, false, false);
            forward.setLastClientInput(new Input(true, false, true, false, true, true, true));
            SuperCamera.beforePhysics(forward);
            check(h, Math.abs(forward.xxa - .3 / Math.sqrt(2)) < EPS
                    && Math.abs(forward.zza - .3 / Math.sqrt(2)) < EPS, "Native diagonal/crouch axes normalized");
            check(h, forward.isShiftKeyDown() && !forward.isSprinting(), "Crouch excludes sprint");
            atRest(forward);
            forward.setLastClientInput(FORWARD);
            strafe.setLastClientInput(new Input(false, false, true, false, false, false, false));
            blocked.setLastClientInput(FORWARD);
            Vec3 a = forward.position(), b = strafe.position(), c = blocked.position();
            // Exercise the real connection wrapper: vanilla tickPlayer rewinds doTick's result
            // to firstGoodXYZ. Calling doTick directly missed the H18 connected-player freeze.
            // One connection tick must retain exactly one collision-resolved native step.
            forward.connection.tick();
            strafe.connection.tick();
            blocked.connection.tick();
            double distance = forward.getX() - a.x;
            check(h, distance > .02 && distance < .3, "Forward key must move actual body from zero velocity: dx=" + distance);
            check(h, Math.abs(forward.getZ() - a.z) < EPS, "Forward at yaw -90 stays on X axis");
            check(h, b.z - strafe.getZ() > .02 && Math.abs(strafe.getX() - b.x) < EPS,
                    "Left strafe at yaw -90 must move actual body along -Z from rest");
            double wall = h.absoluteVec(new Vec3(3, 1, 6)).x;
            double capped = blocked.getX() - c.x;
            check(h, capped >= 0 && capped < distance && blocked.getBoundingBox().maxX <= wall + EPS,
                    "Native collision caps movement before wall: dx=" + capped);
            check(h, blocked.horizontalCollision, "Native tick reports horizontal wall collision");
            for (ServerPlayer p : new ServerPlayer[]{forward, strafe, blocked}) actualBody(h, p);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w258_camera_clock")
    public void connectedSprintAccumulatesExactlyOneNativeStepForArcAndVoid(GameTestHelper h) {
        loaded(h, () -> {
            for (int x = 1; x <= 8; x++) {
                for (int z = 1; z <= 8; z++) h.setBlock(x, 0, z, Blocks.STONE);
            }
            ServerPlayer[] connected = new ServerPlayer[2], direct = new ServerPlayer[2];
            Vec3[] starts = new Vec3[2];
            Input sprint = new Input(true, false, false, false, false, false, true);
            Element[] elements = {Element.ARC, Element.VOID};
            for (int i = 0; i < elements.length; i++) {
                Vec3 pos = new Vec3(2.5, 1, 2.5 + i * 3);
                connected[i] = owner(h, elements[i], pos);
                direct[i] = owner(h, elements[i], pos);
                for (ServerPlayer p : new ServerPlayer[]{connected[i], direct[i]}) {
                    // Let vanilla initialize speed before ownership; no fixture setSpeed/velocity impulse.
                    p.connection.tick();
                    p.setDeltaMovement(Vec3.ZERO);
                    p.setOnGround(true);
                    ready(h, p, elements[i]);
                    p.connection.handlePlayerInput(new ServerboundPlayerInputPacket(sprint));
                    check(h, p.getLastClientInput().equals(sprint), "Real input handler retains forward/sprint keys");
                }
                starts[i] = connected[i].position();
            }
            for (int delay = 1; delay <= 8; delay++) {
                final int nativeTick = delay;
                h.runAfterDelay(delay, () -> {
                    for (int i = 0; i < elements.length; i++) {
                        ServerPlayer p = connected[i], reference = direct[i];
                        for (ServerPlayer player : new ServerPlayer[]{p, reference}) {
                            player.connection.handleMovePlayer(new ServerboundMovePlayerPacket.Rot(-90, 0, false, false));
                            heartbeat(h, player);
                        }
                        Vec3 before = p.position();
                        p.connection.tick();
                        reference.doTick(); // Oracle: one native step, never a replacement movement implementation.
                        check(h, p.position().distanceToSqr(reference.position()) < EPS * EPS,
                                elements[i] + " connected tick equals exactly one native step at tick " + nativeTick);
                        check(h, p.getX() > before.x + .02 && p.isSprinting(),
                                elements[i] + " retains forward/sprint displacement after the connection wrapper");
                        check(h, Math.abs(p.getZ() - starts[i].z) < EPS, "Yaw -90 retains forward axis");
                        actualBody(h, p);
                        TestPlayers.drain(p);
                        TestPlayers.drain(reference);
                    }
                    if (nativeTick == 8) {
                        for (int i = 0; i < elements.length; i++) {
                            check(h, connected[i].getX() - starts[i].x > 1,
                                    elements[i] + " movement accumulates across connection ticks instead of rewinding");
                        }
                        h.succeed();
                    }
                });
            }
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w258_camera_clock")
    public void unownedConnectionRetainsVanillaPositionRewind(GameTestHelper h) {
        ServerPlayer p = owner(h, Element.SOLAR, new Vec3(2.5, 1, 6.5));
        atRest(p);
        Vec3 before = p.position();
        // A real native step would move this body, but vanilla's unowned connection restores
        // its packet-authoritative baseline. This also guards the camera-only injection scope.
        p.xxa = 0;
        p.zza = 1;
        p.connection.tick();
        unchanged(h, p, before);
        check(h, p.getDeltaMovement().horizontalDistanceSqr() > 0,
                "Native travel ran even though unowned vanilla connection rewound the position");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w258_camera_clock")
    public void nativeDropDamagesDespiteSpoofedGroundPackets(GameTestHelper h) {
        loaded(h, () -> {
            // Source floor.snbt declares stone at relative y=0, but the running 26.3 fixture
            // exposed air there and a barrier one block below. Own the landing surface explicitly.
            for (int x = 5; x <= 7; x++) {
                for (int z = 5; z <= 7; z++) h.setBlock(x, 0, z, Blocks.STONE);
            }
            check(h, h.getLevel().getBlockState(h.absolutePos(new BlockPos(6, 0, 6))).is(Blocks.STONE),
                    "Explicit full-block stone landing pad is present at relative y=0");
            ServerPlayer p = owner(h, Element.ARC, new Vec3(6.5, 7, 6.5));
            ready(h, p, Element.ARC);
            atRest(p);
            p.setOnGround(false);
            p.resetFallDistance();
            float health = p.getHealth();
            double floor = h.absoluteVec(new Vec3(6.5, 1, 6.5)).y;
            double startY = p.getY();
            boolean[] landed = {false};
            // Pre-schedule distinct callbacks. GameTestInfo removes a Runnable's map entry AFTER
            // calling it; re-enqueuing the same Runnable from run() loses its next invocation.
            for (int i = 1; i <= 60; i++) {
                final int nativeTick = i;
                h.runAfterDelay(i, () -> {
                    if (landed[0]) return;
                    heartbeat(h, p);
                    check(h, SuperCamera.move(p, new ServerboundMovePlayerPacket.Pos(p.getX(), p.getY(), p.getZ(), true, true)),
                            "Spoofed ground packet consumed before physics");
                    p.connection.tick(); // Include tickPlayer's post-physics baseline rewind (H18 regression).
                    actualBody(h, p);
                    check(h, nativeTick < 3 || p.getY() < startY - EPS,
                            "Native gravity must lower actual body from rest: tick=" + nativeTick + ", y=" + p.getY());
                    if (p.onGround()) {
                        landed[0] = true;
                        check(h, Math.abs(p.getY() - floor) < EPS, "Native collision lands on structure floor: actual=" + p.position()
                                + ", expectedY=" + floor + ", startY=" + startY
                                + ", below=" + p.level().getBlockState(BlockPos.containing(p.position().add(0, -.01, 0)))
                                + ", fixtureFloor=" + p.level().getBlockState(h.absolutePos(new BlockPos(6, 0, 6))));
                        check(h, p.getHealth() < health, "Six-block native drop must damage player; TAIL fall bookkeeping is required"
                                + ": tick=" + nativeTick + ", health=" + p.getHealth());
                        check(h, p.isAlive(), "Drop is damaging, not lethal");
                        h.succeed();
                    } else {
                        check(h, nativeTick < 60, "Drop must land within 60 native ticks: y=" + p.getY()
                                + ", velocity=" + p.getDeltaMovement());
                    }
                });
            }
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w258_camera_clock")
    public void voidCameraRetainsFinalRecoveryThenRestores(GameTestHelper h) {
        loaded(h, () -> {
            ServerPlayer p = owner(h, Element.VOID, new Vec3(2.5, 1, 6.5));
            Vec3 before = p.position();
            Guardians.data(p).setSuperEnergy(1f);
            check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK, "Actual Void super starts");
            check(h, SuperCamera.active(p) && AbilityService.inSuper(p), "Void owns camera and gameplay");
            check(h, AbilityService.inSuper(p), "Accepted bow draw retains gameplay until arrow contact");
            for (int delay = 1; delay <= ShadowshotTiming.RELEASE_TICKS; delay++) {
                final int drawTick = delay;
                h.runAfterDelay(delay, () -> {
                    AbilityService.tickPlayer(p); // Fake player is not in the natural player-list tick.
                    check(h, AbilityService.inSuper(p) == (drawTick < ShadowshotTiming.RELEASE_TICKS),
                            "Gameplay remains through bow draw and ends at arrow contact: tick=" + drawTick);
                    heartbeat(h, p);
                    check(h, PlayerAnimations.isPlaying(p) && PlayerAnimations.ownerSeesLimb(p),
                            "Camera and owner limb survive draw/contact and gameplay end");
                    unchanged(h, p, before);
                });
            }
            heartbeat(h, p);
            h.runAfterDelay(ShadowshotTiming.RELEASE_TICKS + 2, () -> {
                heartbeat(h, p);
                check(h, PlayerAnimations.isPlaying(p) && PlayerAnimations.ownerSeesLimb(p),
                        "Final release and owner limb are not truncated on the next ticks");
                unchanged(h, p, before);
            });
            // Use the installed attack clip's length, including its start transition and callback
            // grace, instead of the old fixed 25-tick deadline. Clip time starts at activation.
            int clipTicks = (int) Math.ceil(BetterModel.limb(HunterModelAssets.MODEL_NAME).orElseThrow()
                    .animation("h15_super_void_attack").orElseThrow().length() * 20);
            int recoveryDeadline = Math.max(ShadowshotTiming.RELEASE_TICKS + 3, clipTicks + 1 + 6 + 1);
            h.runAfterDelay(recoveryDeadline, () -> {
                PlayerAnimations.tick(h.getLevel().getServer());
                SuperCamera.tick(h.getLevel().getServer());
                check(h, !PlayerAnimations.isPlaying(p) && !SuperCamera.active(p),
                        "Final recovery completion releases animation and camera");
                check(h, !PlayerAnimations.ownerSeesLimb(p), "Vanilla owner visibility restored after final recovery");
                check(h, SuperCamera.cameraPosition(p).distanceToSqr(p.getEyePosition()) < EPS * EPS,
                        "Released camera position falls back to real eye");
                unchanged(h, p, before);
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w258_camera_clock")
    public void rotationHeartbeatRetainsSuperThenWatchdogReleases(GameTestHelper h) {
        loaded(h, () -> {
            ServerPlayer p = owner(h);
            Vec3 before = p.position();
            Guardians.data(p).setSuperEnergy(1f);
            check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK, "Actual Arc super starts");
            check(h, PlayerAnimations.isPlaying(p), "Actual ready animation starts");
            int start = h.getLevel().getServer().getTickCount();
            heartbeat(h, p);
            for (int delay = 10; delay <= 50; delay += 10) {
                h.runAfterDelay(delay, () -> heartbeat(h, p));
            }
            h.runAfterDelay(52, () -> {
                heartbeat(h, p); // Last valid rotation; stop sending after this point.
                check(h, h.getLevel().getServer().getTickCount() - start == 52,
                        "Heartbeat survival measured over real server ticks beyond watchdog duration");
                check(h, AbilityService.inSuper(p) && PlayerAnimations.isPlaying(p),
                        "Valid rotations keep actual super and ready animation alive");
                p.setLastClientInput(FORWARD);
                SuperCamera.beforePhysics(p);
                check(h, p.zza > 0, "Watchdog has movement input to clear");
            });
            h.runAfterDelay(92, () -> {
                SuperCamera.tick(h.getLevel().getServer());
                check(h, SuperCamera.active(p), "Exactly 40 ticks since last rotation is still within grace");
            });
            h.runAfterDelay(94, () -> {
                SuperCamera.tick(h.getLevel().getServer());
                check(h, !SuperCamera.active(p) && !AbilityService.inSuper(p),
                        "Missing rotations beyond 40 ticks release camera and actual gameplay session");
                check(h, !PlayerAnimations.isPlaying(p) && !PlayerAnimations.ownerSeesLimb(p),
                        "Watchdog stops ready animation and restores vanilla owner visibility");
                check(h, p.xxa == 0 && p.zza == 0, "Watchdog clears movement axes");
                check(h, !SuperCamera.move(p, new ServerboundMovePlayerPacket.Rot(0, 0, true, false)),
                        "Watchdog returns movement packet ownership");
                unchanged(h, p, before);
                h.succeed();
            });
        });
    }

}
