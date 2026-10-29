package kim.biryeong.destiny.test;

import io.netty.buffer.Unpooled;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.ServerAnimationClock;
import kim.biryeong.destiny.fx.SwordPoseW146Assets;
import kim.biryeong.destiny.fx.SwordPresentation;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.weapon.*;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.tracker.TrackerModifier;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.gametest.framework.GameTestSequence;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Relative;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;

/** Real queued server packets and BetterModel clocks. Native client/render behavior remains unverified.
 * Sequence steps and teardown hooks are registered up front, never from a running callback.
 */
public final class SwordPresentationW53GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String ADAPTIVE = "abide_the_return";
    private static final List<String> SWORDS = List.of(ADAPTIVE, "goldtusk", "crown_splitter",
            "falling_guillotine", "temptation_s_hook");
    private static final double EPS = 1.0e-6;
    private static final float HP = 100;
    private record Wire(int mount, int camera) {}

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static GameTestSequence loaded(GameTestHelper h) {
        return h.startSequence().thenWaitUntil(() -> {
            check(h, SuperCamera.ENABLED && PlayerAnimations.available(), "Vanilla sword camera and real BetterModel are enabled");
            check(h, BetterModel.limb(SwordPoseW146Assets.MODEL_NAME).isPresent()
                            && BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),
                    "Waiting for separate sword and Hunter limbs");
        });
    }

    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 12);
        var original = p.level();
        p.setOnGround(true);
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.TORCH, 7));
        Guardians.runtime(p).gcbClient = false;
        Guardians.runtime(p).gcbThirdPerson = false;
        TestCleanup.register(h, () -> {
            AbilityService.cleanup(p);
            WeaponRuntime.cleanup(p);
            SwordPresentation.cleanup(p);
            SuperCamera.stop(p);
            PlayerAnimations.stop(p);
            CombatHud.remove(p);
            p.setServerLevel(original);
            if (p.getCamera() != p) foreignCameraState(p, p);
            TestPlayers.remove(p);
        });
        return p;
    }

    private static ItemStack give(ServerPlayer p, String id, int rounds) {
        var entry = WeaponCatalog.find(id).orElseThrow();
        var stack = WeaponItems.create(entry);
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry), rounds, 0));
        SwordItems.save(stack, SwordCycle.CAPACITY, 0);
        p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        return stack;
    }

    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()));
    }

    private static Husk target(GameTestHelper h, double z) {
        var e = h.spawn(EntityTypes.HUSK, new Vec3(2.9, 1, z));
        e.setNoAi(true);
        e.setNoGravity(true);
        e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP);
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        e.setHealth(HP);
        TestCleanup.register(h, e::discard);
        return e;
    }

    private static void hands(GameTestHelper h, ServerPlayer p, ItemStack sword) {
        check(h, p.getMainHandItem() == sword && p.getOffhandItem().is(Items.TORCH)
                        && p.getOffhandItem().getCount() == 7,
                "Presentation preserves exact main-hand ownership and real offhand inventory");
    }

    private static void use(GameTestHelper h, ServerPlayer p) {
        p.gameMode.useItem(p, h.getLevel(), p.getMainHandItem(), InteractionHand.MAIN_HAND);
    }

    private static int lightContact() {
        return SwordTiming.contactTicks(SwordProfile.Shape.UPPERCUT, false, 1);
    }

    private static void windup(GameTestHelper h, ServerPlayer p, Vec3 position, Husk enemy) {
        check(h, enemy.getHealth() == HP && p.position().distanceToSqr(position) < EPS * EPS,
                "Accepted sword visual precedes actual HP damage and body movement");
    }

    private static int cameraId(ClientboundSetCameraPacket packet) {
        var buf = new FriendlyByteBuf(Unpooled.buffer());
        try {
            ClientboundSetCameraPacket.STREAM_CODEC.encode(buf, packet);
            return buf.readVarInt();
        } finally { buf.release(); }
    }

    private static <T> List<T> packets(List<Packet<?>> queued, Class<T> type) {
        return queued.stream().filter(type::isInstance).map(type::cast).toList();
    }

    private static Wire entered(GameTestHelper h, ServerPlayer p, List<Packet<?>> queued) {
        var cameras = packets(queued, ClientboundSetCameraPacket.class);
        var seats = packets(queued, ClientboundSetPassengersPacket.class).stream()
                .filter(packet -> Arrays.equals(packet.getPassengers(), new int[]{p.getId()})).toList();
        check(h, cameras.size() == 1 && seats.size() == 1,
                "Equip queues one real camera selection and one virtual seat carrying only this owner");
        int camera = cameraId(cameras.getFirst());
        int mount = seats.getFirst().getVehicle();
        // BetterModel also spawns item displays; only the camera/seat packet IDs identify our markers.
        var spawned = packets(queued, ClientboundAddEntityPacket.class).stream()
                .filter(packet -> packet.getType() == EntityTypes.ITEM_DISPLAY
                        && (packet.getId() == camera || packet.getId() == mount)).toList();
        var ids = spawned.stream().map(ClientboundAddEntityPacket::getId).toList();
        check(h, spawned.size() == 2 && ids.contains(camera) && ids.contains(mount)
                        && camera != mount && camera != p.getId() && mount != p.getId(),
                "Equip spawns exactly two distinct private camera markers, excluding BetterModel displays");
        check(h, packets(queued, ClientboundSetPassengersPacket.class).stream().anyMatch(packet ->
                        packet.getVehicle() == mount && Arrays.equals(packet.getPassengers(), new int[]{p.getId()})),
                "Queued passenger graph mounts only this owner onto its private virtual seat");
        check(h, p.level().getEntity(mount) == null && p.level().getEntity(camera) == null,
                "Private camera markers are never registered as world entities");
        check(h, p.getCamera() == p && !p.isPassenger() && p.getPassengers().isEmpty() && !p.noPhysics
                        && SuperCamera.swordActive(p),
                "Server player keeps self-camera, native physics and no real mount");
        check(h, packets(queued, ClientboundPlayerPositionPacket.class).isEmpty(),
                "Entering sword view does not queue a body teleport/correction");
        return new Wire(mount, camera);
    }

    private static Wire equipCamera(GameTestHelper h, ServerPlayer p, ItemStack stack) {
        var before = stack.copy();
        var position = p.position();
        TestPlayers.drain(p);
        WeaponRuntime.tickPlayer(p);
        var wire = entered(h, p, TestPlayers.outbound(p));
        check(h, ItemStack.matches(stack, before) && p.position().distanceToSqr(position) < EPS * EPS,
                "First equip camera tick cannot mutate ammunition, energy, inventory or body position");
        hands(h, p, stack);
        return wire;
    }

    private static void removed(GameTestHelper h, List<Packet<?>> queued, Wire wire) {
        var removals = packets(queued, ClientboundRemoveEntitiesPacket.class);
        check(h, removals.stream().anyMatch(packet -> packet.entityIds().contains(wire.mount())
                        && packet.entityIds().contains(wire.camera())),
                "Real removal packet destroys the exact private mount and camera IDs");
        check(h, packets(queued, ClientboundSetPassengersPacket.class).stream().anyMatch(packet ->
                        packet.getVehicle() == wire.mount() && packet.getPassengers().length == 0),
                "Real empty passenger packet detaches this owner's virtual seat");
    }

    private static void restored(GameTestHelper h, ServerPlayer p, List<Packet<?>> queued, Wire wire) {
        removed(h, queued, wire);
        check(h, packets(queued, ClientboundSetCameraPacket.class).stream().anyMatch(packet -> cameraId(packet) == p.getId()),
                "Release queues restoration to the actual owner entity");
        var positions = packets(queued, ClientboundPlayerPositionPacket.class);
        check(h, positions.size() == 1, "Release queues one authoritative return correction");
        var correction = positions.getFirst();
        check(h, correction.change().position().distanceToSqr(p.position()) < EPS * EPS
                        && correction.change().deltaMovement().equals(Vec3.ZERO)
                        && correction.change().yRot() == 0 && correction.change().xRot() == 0
                        && correction.relatives().equals(Relative.union(Relative.DELTA, Relative.ROTATION)),
                "Return uses absolute body position with relative-zero native velocity and view correction");
    }

    private static void heartbeat(GameTestHelper h, ServerPlayer p) {
        check(h, SuperCamera.move(p, new ServerboundMovePlayerPacket.Rot(p.getYRot(), p.getXRot(), false, false)),
                "Real rotation input remains accepted during owned sword camera");
    }

    private static EntityTracker swordTracker(GameTestHelper h, ServerPlayer p) {
        check(h, PlayerAnimations.swordAttacking(p), "Accepted attack has a real sword one-shot");
        return swordPlaybackTracker(h, p);
    }

    private static EntityTracker swordPlaybackTracker(GameTestHelper h, ServerPlayer p) {
        check(h, PlayerAnimations.swordPlaying(p), "Sword attack or underlay has real playback");
        var tracker = BetterModel.limb(SwordPoseW146Assets.MODEL_NAME).orElseThrow()
                .getOrCreate(ModPlayer.of(p.connection), TrackerModifier.DEFAULT);
        check(h, !tracker.isClosed() && !tracker.bones().isEmpty()
                        && ((ServerAnimationClock) (Object) tracker).destiny$serverFrames() == PlayerAnimations.serverFrames(p),
                "Public frame telemetry comes from the live separate sword tracker with real bones");
        return tracker;
    }

    private static Display.ItemDisplay foreignMarker(ServerPlayer p) {
        var marker = new Display.ItemDisplay(EntityTypes.ITEM_DISPLAY, p.level());
        marker.setPos(p.position());
        return marker; // Private fixture, not inserted into the shared world.
    }

    /** Fault-inject server camera occupancy only. Embedded players are not in the
     * native chunk distance manager: setCamera() moves them there and crashes the
     * harness. This is not a native cinematic takeover/packet-consumption test. */
    private static void foreignCameraState(ServerPlayer p, net.minecraft.world.entity.Entity camera) {
        try {
            var field = ServerPlayer.class.getDeclaredField("camera");
            field.setAccessible(true);
            field.set(p, camera);
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }

    /** Copy the transform actually passed to BetterModel's display pipeline, not
     * worldPosition(), which rebuilds a local Euler rotation. Test-only reflection. */
    private static kr.toxicity.model.api.bone.BoneMovement sent(kr.toxicity.model.api.bone.RenderedBone bone) {
        try {
            var global = bone.getClass().getDeclaredField("globalState");
            global.setAccessible(true);
            Object handler = global.get(bone);
            var current = handler.getClass().getDeclaredField("current");
            current.setAccessible(true);
            return new kr.toxicity.model.api.bone.BoneMovement().set(
                    (kr.toxicity.model.api.bone.BoneMovement) current.get(handler));
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }

    @GameTest(structure = FLOOR, maxTicks = 600, environment = "destiny-test:w90_isolated")
    public void allEightClipsChangeActualFullBodyDisplayTransformsWithoutGameplayMutation(GameTestHelper h) {
        var p = player(h, 6.5);
        loaded(h).thenExecute(() -> {
            var stack = give(p, ADAPTIVE, 20);
            var before = stack.copy();
            var body = p.position();
            var clips = List.of("sword_light_1", "sword_light_2", "sword_light_3", "sword_uppercut",
                    "sword_dash", "sword_slam", "sword_vortex", "sword_caster");
            for (var clip : clips) {
                check(h, PlayerAnimations.swordAttack(p, clip), "Dedicated visual clip starts: " + clip);
                var tracker = swordTracker(h, p);
                var names = List.of("pri_right_item", "pc_chest", "pll_left_leg");
                var bones = names.stream().map(name -> tracker.bone(b -> b.name().rawName().equals(name))).toList();
                check(h, bones.stream().noneMatch(java.util.Objects::isNull), "Full-body sent bones are present");
                var initial = bones.stream().map(SwordPresentationW53GameTests::sent).toList();
                var changed = new boolean[names.size()];
                var clock = (ServerAnimationClock) (Object) tracker;
                long frames = clock.destiny$serverFrames();
                // Explicit authoritative clock samples, not wall-time or client-render proof.
                for (int tick = 0; tick < 6; tick++) {
                    clock.destiny$advanceServerTick();
                    for (int i = 0; i < bones.size(); i++) {
                        var value = sent(bones.get(i));
                        check(h, value.position().isFinite() && value.scale().isFinite()
                                        && value.rotation().isFinite(), "Finite display transform: " + clip + "/" + names.get(i));
                        var start = initial.get(i);
                        changed[i] |= value.position().distanceSquared(start.position()) > 1e-8
                                || Math.abs(value.rotation().dot(start.rotation())) < .99999f;
                    }
                }
                for (int i = 0; i < changed.length; i++) check(h, changed[i],
                        "Actual sent full-body transform changes: " + clip + "/" + names.get(i));
                check(h, clock.destiny$serverFrames() == frames + 12, "Exactly two real frames per server tick");
                PlayerAnimations.stopSword(p);
                check(h, tracker.isClosed(), "Visual-only sample releases its exact tracker");
            }
            check(h, ItemStack.matches(stack, before) && p.position().distanceToSqr(body) < EPS * EPS,
                    "Direct cosmetic sampling changes no gameplay ammo, energy, body or inventory");
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 600, environment = "destiny-test:w90_isolated")
    public void equipQueuesPrivateCameraAndIdleRetainsItWithoutAmmoMutation(GameTestHelper h) {
        var p = player(h, 6.5);
        ItemStack[] stack = new ItemStack[1];
        Wire[] wire = new Wire[1];
        EntityTracker[] tracker = new EntityTracker[1];
        long[] frames = new long[1];
        loaded(h).thenExecute(() -> {
            stack[0] = give(p, ADAPTIVE, 12);
            wire[0] = equipCamera(h, p, stack[0]);
            tracker[0] = swordPlaybackTracker(h, p);
            frames[0] = PlayerAnimations.serverFrames(p);
            check(h, !PlayerAnimations.swordAttacking(p) && "h15_sword_idle".equals(PlayerAnimations.swordPose(p)),
                    "Idle selection starts its persistent underlay without fabricating an attack clip");
        }).thenIdle(5).thenExecute(() -> {
            heartbeat(h, p);
            WeaponRuntime.tickPlayer(p);
            var queued = TestPlayers.outbound(p);
            check(h, SuperCamera.swordActive(p) && !PlayerAnimations.swordAttacking(p)
                            && swordPlaybackTracker(h, p) == tracker[0]
                            && PlayerAnimations.serverFrames(p) > frames[0]
                            && "h15_sword_idle".equals(PlayerAnimations.swordPose(p))
                            && ammo(stack[0]).rounds() == 12 && ammo(stack[0]).total() == 12,
                    "Selected sword retains continuous rear camera through idle without an ammo/attack grant");
            check(h, packets(queued, ClientboundSetCameraPacket.class).isEmpty()
                            && packets(queued, ClientboundAddEntityPacket.class).isEmpty()
                            && packets(queued, ClientboundEntityPositionSyncPacket.class).size() >= 2,
                    "Idle updates existing virtual marker positions instead of reallocating camera ownership");
            check(h, packets(queued, ClientboundSetPassengersPacket.class).stream().allMatch(packet ->
                            packet.getVehicle() == wire[0].mount() && Arrays.equals(packet.getPassengers(), new int[]{p.getId()})),
                    "Idle seat updates retain the same real packet IDs and owner");
            hands(h, p, stack[0]);
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 600, environment = "destiny-test:w90_isolated")
    public void acceptedLightComboAndFiveHeavyClipsAdvanceRealFramesThenKeepCamera(GameTestHelper h) {
        List<ServerPlayer> owners = new ArrayList<>();
        for (int i = 0; i < 6; i++) owners.add(player(h, 6.5));
        ItemStack[] stacks = new ItemStack[6];
        Wire[] wires = new Wire[6];
        EntityTracker[] trackers = new EntityTracker[6];
        long[] frames = new long[6];
        int cadence = WeaponProfile.forEntry(WeaponCatalog.find(ADAPTIVE).orElseThrow()).intervalTicks() + 1;
        loaded(h).thenExecute(() -> {
            var renderer = BetterModel.limb(SwordPoseW146Assets.MODEL_NAME).orElseThrow();
            for (int combo = 1; combo <= 3; combo++) {
                String clip = "h15_sword_light_" + combo;
                check(h, ("h15_" + SwordPresentation.clip(SwordProfile.Shape.UPPERCUT, false, combo)).equals(clip)
                                && renderer.animation(clip).isPresent(),
                        "Dedicated authored light mapping and real renderer clip are loaded: " + clip);
            }
            var heavyNames = List.of("uppercut", "dash", "slam", "vortex", "caster");
            for (int i = 0; i < SWORDS.size(); i++) {
                var shape = SwordProfile.of(WeaponCatalog.find(SWORDS.get(i)).orElseThrow()).shape();
                String clip = "h15_sword_" + heavyNames.get(i);
                check(h, ("h15_" + SwordPresentation.clip(shape, true, 0)).equals(clip)
                                && renderer.animation(clip).isPresent(),
                        "Dedicated authored heavy mapping and real renderer clip are loaded: " + clip);
            }
            for (int i = 0; i < owners.size(); i++) {
                var owner = owners.get(i);
                stacks[i] = give(owner, i == 0 ? ADAPTIVE : SWORDS.get(i - 1), 20);
                wires[i] = equipCamera(h, owner, stacks[i]);
                trackers[i] = swordPlaybackTracker(h, owner);
                frames[i] = PlayerAnimations.serverFrames(owner);
                if (i == 0) InputRouter.onPunch(owner); else use(h, owner);
                check(h, swordTracker(h, owner) == trackers[i]
                                && PlayerAnimations.serverFrames(owner) == frames[i],
                        "Accepted attack reuses the underlay tracker without resetting or advancing its clock");
                check(h, ammo(stacks[i]).rounds() < 20 && (i == 0 || SwordItems.energy(stacks[i]) == 0),
                        "Actual accepted light/heavy pays gameplay cost before starting its owned visual");
            }
        }).thenIdle(2).thenExecute(() -> {
            for (int i = 0; i < owners.size(); i++) {
                heartbeat(h, owners.get(i));
                check(h, !trackers[i].isClosed() && PlayerAnimations.swordAttacking(owners.get(i))
                                && PlayerAnimations.serverFrames(owners.get(i)) > frames[i],
                        "Real BetterModel sword frames advance on server ticks for light and each heavy frame");
            }
        }).thenIdle(cadence).thenExecute(() -> {
            for (var p : owners) heartbeat(h, p);
            long before = PlayerAnimations.serverFrames(owners.getFirst());
            InputRouter.onPunch(owners.getFirst());
            check(h, WeaponRuntime.swordStatus(owners.getFirst()).orElseThrow().combo() == 2,
                    "Second accepted runtime light selects the second combo visual");
            check(h, swordTracker(h, owners.getFirst()) == trackers[0]
                            && PlayerAnimations.serverFrames(owners.getFirst()) == before,
                    "Second light retains the exact tracker and monotonic clock");
            frames[0] = PlayerAnimations.serverFrames(owners.getFirst());
        }).thenIdle(2).thenExecute(() -> {
            check(h, PlayerAnimations.serverFrames(owners.getFirst()) > frames[0], "Second light clip really advances");
            for (var p : owners) heartbeat(h, p);
        }).thenIdle(cadence).thenExecute(() -> {
            for (var p : owners) heartbeat(h, p);
            long before = PlayerAnimations.serverFrames(owners.getFirst());
            InputRouter.onPunch(owners.getFirst());
            check(h, WeaponRuntime.swordStatus(owners.getFirst()).orElseThrow().combo() == 3
                            && ammo(stacks[0]).rounds() == 17,
                    "Third accepted light preserves the real three-hit combo and one ammo per light");
            check(h, swordTracker(h, owners.getFirst()) == trackers[0]
                            && PlayerAnimations.serverFrames(owners.getFirst()) == before,
                    "Third light retains the exact tracker and monotonic clock");
            frames[0] = PlayerAnimations.serverFrames(owners.getFirst());
        }).thenIdle(2).thenExecute(() -> {
            check(h, PlayerAnimations.serverFrames(owners.getFirst()) > frames[0], "Third light clip really advances");
        }).thenWaitUntil(() -> {
            for (var p : owners) heartbeat(h, p);
            check(h, owners.stream().noneMatch(PlayerAnimations::swordAttacking), "Waiting for actual sword one-shots to finish");
        }).thenExecute(() -> {
            for (int i = 0; i < owners.size(); i++) {
                var p = owners.get(i);
                check(h, swordPlaybackTracker(h, p) == trackers[i] && SuperCamera.swordActive(p)
                                && !PlayerAnimations.swordAttacking(p)
                                && PlayerAnimations.serverFrames(p) > frames[i]
                                && "h15_sword_idle".equals(PlayerAnimations.swordPose(p)),
                        "Finished attack retains its exact tracker and advancing clock and returns to idle underlay");
                var queued = TestPlayers.outbound(p);
                var wire = wires[i];
                check(h, packets(queued, ClientboundSetCameraPacket.class).isEmpty()
                                && packets(queued, ClientboundRemoveEntitiesPacket.class).stream().noneMatch(packet ->
                                    packet.entityIds().contains(wire.mount()) || packet.entityIds().contains(wire.camera())),
                        "Attack and underlay recovery retain the exact private camera and seat markers");
                hands(h, p, stacks[i]);
            }
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 600, environment = "destiny-test:w90_isolated")
    public void deniedCooldownGuardAndEmptyHeavyCannotRestartFramesOrRepeatHpCost(GameTestHelper h) {
        var p = player(h, 6.5);
        var guard = player(h, 2.5);
        Guardians.data(guard).setGuardianClass(GuardianClass.NONE); // Exercise sword guard, not crouched Guardian MELEE.
        var empty = player(h, 9.5);
        var enemy = target(h, 6.5);
        var guardEnemy = target(h, 2.5);
        var emptyEnemy = target(h, 9.5);
        ItemStack[] stacks = new ItemStack[3];
        EntityTracker[] tracker = new EntityTracker[1];
        float[] health = new float[1];
        var position = p.position();
        loaded(h).thenExecute(() -> {
            stacks[0] = give(p, ADAPTIVE, 12);
            stacks[1] = give(guard, ADAPTIVE, 12);
            stacks[2] = give(empty, ADAPTIVE, 0);
            equipCamera(h, p, stacks[0]);
            equipCamera(h, guard, stacks[1]);
            equipCamera(h, empty, stacks[2]);
            InputRouter.onPunch(p);
            tracker[0] = swordTracker(h, p);
            health[0] = enemy.getHealth();
            windup(h, p, position, enemy);
            check(h, health[0] == HP && ammo(stacks[0]).rounds() == 11,
                    "Accepted reference light pays ammo and starts its visual before actual HP contact");
            guard.setShiftKeyDown(true);
        }).thenIdle(2).thenExecute(() -> {
            heartbeat(h, p);
            heartbeat(h, guard);
            heartbeat(h, empty);
            windup(h, p, position, enemy);
            long before = PlayerAnimations.serverFrames(p);
            check(h, before > 0, "Reference clip has already advanced before rejected retrigger attempts");
            var item = stacks[0].copy();
            InputRouter.onPunch(p);
            WeaponRuntime.onPunch(p);
            use(h, p);
            check(h, !tracker[0].isClosed() && swordTracker(h, p) == tracker[0]
                            && PlayerAnimations.serverFrames(p) == before
                            && enemy.getHealth() == health[0] && ItemStack.matches(stacks[0], item),
                    "Duplicate/cooldown light and heavy denial preserve actual tracker, same-tick frames, HP and item cost");
            WeaponRuntime.tickPlayer(guard);
            check(h, WeaponRuntime.swordStatus(guard).orElseThrow().guarding(), "Guard denial fixture has active guard state");
            var guarded = stacks[1].copy();
            InputRouter.onPunch(guard);
            use(h, guard);
            use(h, empty);
            check(h, !PlayerAnimations.swordAttacking(guard) && !PlayerAnimations.swordAttacking(empty)
                            && PlayerAnimations.swordPlaying(guard) && PlayerAnimations.swordPlaying(empty)
                            && guardEnemy.getHealth() == HP && emptyEnemy.getHealth() == HP
                            && ItemStack.matches(stacks[1], guarded) && ammo(stacks[2]).total() == 0,
                    "Active guard and empty-heavy rejections create no BetterModel attack, HP loss or ammo payment");
        }).thenIdle(lightContact() - 1).thenExecute(() -> {
            heartbeat(h, p);
            heartbeat(h, guard);
            heartbeat(h, empty);
            WeaponRuntime.tickPlayer(p);
            health[0] = enemy.getHealth();
            check(h, health[0] < HP && ammo(stacks[0]).rounds() == 11
                            && guardEnemy.getHealth() == HP && emptyEnemy.getHealth() == HP,
                    "Only the accepted reference light applies actual HP damage at contact, for one ammo");
        }).thenIdle(2).thenExecute(() -> {
            heartbeat(h, p);
            WeaponRuntime.tickPlayer(p);
            check(h, enemy.getHealth() == health[0] && ammo(stacks[0]).rounds() == 11,
                    "Rejected duplicate inputs never produce another delayed HP transaction or payment");
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 600, environment = "destiny-test:w90_isolated")
    public void swappingReleasesOnlySwordViewAndUsesRelativeZeroReturnCorrection(GameTestHelper h) {
        var p = player(h, 6.5);
        var enemy = target(h, 6.5);
        var origin = p.position();
        ItemStack[] stack = new ItemStack[1];
        Wire[] wire = new Wire[1];
        EntityTracker[] tracker = new EntityTracker[1];
        loaded(h).thenExecute(() -> {
            stack[0] = give(p, ADAPTIVE, 12);
            wire[0] = equipCamera(h, p, stack[0]);
            InputRouter.onPunch(p);
            tracker[0] = swordTracker(h, p);
            windup(h, p, origin, enemy);
            check(h, ammo(stack[0]).rounds() == 11, "Accepted pre-swap light pays once");
        }).thenIdle(2).thenExecute(() -> {
            windup(h, p, origin, enemy);
            var position = p.position();
            var velocity = new Vec3(.17, -.31, .09);
            p.setDeltaMovement(velocity);
            p.setYRot(37);
            p.setXRot(-21);
            var before = stack[0].copy();
            TestPlayers.drain(p);
            p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.DIAMOND, 2));
            WeaponRuntime.tickPlayer(p);
            restored(h, p, TestPlayers.outbound(p), wire[0]);
            check(h, tracker[0].isClosed() && !PlayerAnimations.swordPlaying(p) && !SuperCamera.active(p)
                            && p.getCamera() == p && !p.isPassenger() && p.position().distanceToSqr(position) < EPS * EPS
                            && p.getDeltaMovement().distanceToSqr(velocity) < EPS * EPS && p.getYRot() == 37 && p.getXRot() == -21,
                    "Unselect closes only owned sword cosmetics while preserving native body, momentum and view");
            check(h, ItemStack.matches(stack[0], before) && p.getMainHandItem().is(Items.DIAMOND)
                            && p.getMainHandItem().getCount() == 2 && p.getOffhandItem().getCount() == 7,
                    "Release neither replaces real hands nor refills the stowed sword");
            SwordPresentation.cleanup(p);
            WeaponRuntime.cleanup(p);
            check(h, packets(TestPlayers.outbound(p), ClientboundPlayerPositionPacket.class).isEmpty(),
                    "Repeated cleanup cannot add another correction or resurrect the camera");
        }).thenIdle(lightContact() - 1).thenExecute(() -> {
            WeaponRuntime.tickPlayer(p);
            check(h, enemy.getHealth() == HP && p.position().distanceToSqr(origin) < EPS * EPS
                            && ammo(stack[0]).rounds() == 11,
                    "Pre-contact unselect and repeated cleanup cancel later HP/movement without refunding the paid light");
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 600, environment = "destiny-test:w90_isolated")
    public void skillOneShotAndArcLoopSurviveSwordAttackAndSwordOnlyCleanup(GameTestHelper h) {
        var p = player(h, 6.5);
        var enemy = target(h, 6.5);
        var origin = p.position();
        ItemStack[] stack = new ItemStack[1];
        long[] frame = new long[1];
        loaded(h).thenExecute(() -> {
            stack[0] = give(p, ADAPTIVE, 12);
            equipCamera(h, p, stack[0]);
            InputRouter.onPunch(p);
            windup(h, p, origin, enemy);
            WeaponRuntime.cancelUseForSkill(p);
            check(h, !SuperCamera.swordActive(p) && !PlayerAnimations.swordPlaying(p), "Skill handoff cancels sword-owned camera and clip");
            check(h, PlayerAnimations.play(p, "h15_roll_forward") && PlayerAnimations.foreignToSword(p),
                    "Ordinary skill starts real foreign one-shot after sword cancellation");
            check(h, !PlayerAnimations.swordAttack(p, "sword_light_1"), "Sword visual cannot steal an ordinary skill run");
            SwordPresentation.cleanup(p);
            WeaponRuntime.tickPlayer(p);
            frame[0] = PlayerAnimations.serverFrames(p);
            check(h, PlayerAnimations.foreignToSword(p) && !SuperCamera.swordActive(p),
                    "Sword-only cleanup/rebind leaves the ordinary run active and avoids camera theft");
        }).thenIdle(2).thenExecute(() -> {
            check(h, PlayerAnimations.foreignToSword(p) && PlayerAnimations.serverFrames(p) > frame[0],
                    "Ordinary skill's actual BetterModel frames continue after sword-only cleanup");
            check(h, PlayerAnimations.loop(p, "super_arc") && SuperCamera.start(p, Element.ARC),
                    "Real Arc limb loop and foreign combat camera take ownership");
            TestPlayers.drain(p);
            frame[0] = PlayerAnimations.serverFrames(p);
            SwordPresentation.cleanup(p);
            WeaponRuntime.cancelUseForSkill(p);
            WeaponRuntime.tickPlayer(p);
            check(h, !PlayerAnimations.swordAttack(p, "sword_uppercut") && PlayerAnimations.foreignToSword(p)
                            && SuperCamera.active(p) && !SuperCamera.swordActive(p),
                    "Sword cancellation never closes Arc's foreign loop or camera");
            check(h, packets(TestPlayers.outbound(p), ClientboundSetCameraPacket.class).isEmpty(),
                    "Sword-only cleanup emits no foreign-camera reset packet");
        }).thenIdle(lightContact()).thenExecute(() -> {
            heartbeat(h, p);
            check(h, PlayerAnimations.foreignToSword(p) && PlayerAnimations.serverFrames(p) > frame[0]
                            && SuperCamera.active(p) && !SuperCamera.swordActive(p),
                    "Arc loop still advances and retains its own camera after sword callbacks");
            WeaponRuntime.tickPlayer(p);
            check(h, enemy.getHealth() == HP && p.position().distanceToSqr(origin) < EPS * EPS
                            && ammo(stack[0]).rounds() == 11,
                    "Pre-contact skill cancellation leaves actual HP/movement unchanged and keeps the accepted cost");
            hands(h, p, stack[0]);
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 600, environment = "destiny-test:w90_isolated")
    public void solarSuperStaysSelfCameraAndCannotReacquireHeldSwordPresentation(GameTestHelper h) {
        var p = player(h, 6.5);
        ItemStack[] stack = new ItemStack[1];
        loaded(h).thenExecute(() -> {
            stack[0] = give(p, ADAPTIVE, 12);
            equipCamera(h, p, stack[0]);
            InputRouter.onPunch(p);
            Guardians.data(p).setSuperEnergy(1);
            check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK && AbilityService.inSuper(p),
                    "Real equipped Solar super accepts and performs sword-to-skill handoff");
            check(h, !SuperCamera.active(p) && p.getCamera() == p && !PlayerAnimations.swordPlaying(p),
                    "Solar immediately releases existing sword camera and sword-only limb");
            TestPlayers.drain(p);
        }).thenIdle(3).thenExecute(() -> {
            int rounds = ammo(stack[0]).rounds();
            AbilityService.tickPlayer(p);
            WeaponRuntime.tickPlayer(p);
            InputRouter.onPunch(p);
            use(h, p);
            check(h, AbilityService.inSuper(p) && !SuperCamera.active(p) && p.getCamera() == p
                            && !PlayerAnimations.swordAttack(p, "sword_light_1") && !PlayerAnimations.swordPlaying(p),
                    "While Solar gameplay is active, neither held sword ticks nor attack paths reacquire sword camera/limb");
            check(h, ammo(stack[0]).rounds() == rounds
                            && packets(TestPlayers.outbound(p), ClientboundSetCameraPacket.class).isEmpty(),
                    "Solar input sends no sword camera packet and spends no underlying sword ammo");
            hands(h, p, stack[0]);
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 600, environment = "destiny-test:w90_isolated")
    public void rotationTimeoutReleasesWithoutAutomaticReacquireUntilExactStackRebind(GameTestHelper h) {
        var p = player(h, 6.5);
        ItemStack[] stack = new ItemStack[1];
        Wire[] wire = new Wire[1];
        loaded(h).thenExecute(() -> {
            stack[0] = give(p, ADAPTIVE, 12);
            wire[0] = equipCamera(h, p, stack[0]);
            InputRouter.onPunch(p);
            swordTracker(h, p);
            TestPlayers.drain(p);
            // Deliberately no rotation input during the following normal server ticks.
        }).thenIdle(46).thenExecute(() -> {
            check(h, !SuperCamera.active(p) && !PlayerAnimations.swordPlaying(p),
                    "Rotation watchdog really releases idle sword camera and any owned limb");
            restored(h, p, TestPlayers.outbound(p), wire[0]);
            WeaponRuntime.tickPlayer(p);
            WeaponRuntime.tickPlayer(p);
            check(h, !PlayerAnimations.swordPlaying(p) && !SuperCamera.active(p),
                    "Same-binding ticks cannot automatically recreate the watchdog-closed underlay or camera");
            InputRouter.onPunch(p);
            check(h, !SuperCamera.active(p) && PlayerAnimations.swordAttacking(p),
                    "Same exact held-stack binding can attack visually but must not automatically reacquire timed-out camera");
            var queued = TestPlayers.outbound(p);
            check(h, packets(queued, ClientboundSetCameraPacket.class).isEmpty(),
                    "Same-binding ticks/attack queue no camera selection after watchdog release");
            var replacement = stack[0].copy();
            p.setItemInHand(InteractionHand.MAIN_HAND, replacement);
            TestPlayers.drain(p);
            WeaponRuntime.tickPlayer(p);
            var next = entered(h, p, TestPlayers.outbound(p));
            check(h, next.camera() != wire[0].camera() && next.mount() != wire[0].mount()
                            && PlayerAnimations.swordPlaying(p) && !PlayerAnimations.swordAttacking(p)
                            && "h15_sword_idle".equals(PlayerAnimations.swordPose(p))
                            && ammo(replacement).total() == ammo(stack[0]).total(),
                    "An actual ItemStack identity rebind creates fresh camera IDs and underlay without refilling ammo or retaining old swing");
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 600, environment = "destiny-test:w90_isolated")
    public void existingOrTakingOverForeignCinematicCannotBeStolenBySwordCleanup(GameTestHelper h) {
        var occupied = player(h, 2.5);
        var takeover = player(h, 9.5);
        Wire[] wire = new Wire[1];
        loaded(h).thenExecute(() -> {
            var firstForeign = foreignMarker(occupied);
            foreignCameraState(occupied, firstForeign);
            give(occupied, ADAPTIVE, 12);
            TestPlayers.drain(occupied);
            WeaponRuntime.tickPlayer(occupied);
            SwordPresentation.cleanup(occupied);
            check(h, occupied.getCamera() == firstForeign && !SuperCamera.active(occupied)
                            && !PlayerAnimations.swordPlaying(occupied)
                            && packets(TestPlayers.outbound(occupied), ClientboundSetCameraPacket.class).isEmpty(),
                    "Already foreign server camera blocks sword acquisition and is never reset by sword-only cleanup");

            var stack = give(takeover, ADAPTIVE, 12);
            wire[0] = equipCamera(h, takeover, stack);
            InputRouter.onPunch(takeover);
            swordTracker(h, takeover);
            var nextForeign = foreignMarker(takeover);
            foreignCameraState(takeover, nextForeign);
            TestPlayers.drain(takeover); // Inspect only this session's subsequent cleanup packets.
            SuperCamera.tick(h.getLevel().getServer());
            var queued = TestPlayers.outbound(takeover);
            removed(h, queued, wire[0]);
            check(h, takeover.getCamera() == nextForeign && !SuperCamera.active(takeover)
                            && !PlayerAnimations.swordPlaying(takeover)
                            && packets(queued, ClientboundSetCameraPacket.class).isEmpty()
                            && packets(queued, ClientboundPlayerPositionPacket.class).isEmpty(),
                    "Foreign takeover removes our exact private IDs without sending a self-camera or body correction over it");
            WeaponRuntime.tickPlayer(takeover);
            check(h, takeover.getCamera() == nextForeign && !SuperCamera.active(takeover)
                            && !PlayerAnimations.swordPlaying(takeover),
                    "Held sword's next runtime tick cannot steal a foreign cinematic back");
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 600, environment = "destiny-test:w90_isolated")
    public void twoPlayersKeepIndependentCameraPacketsTrackersAndInventory(GameTestHelper h) {
        var a = player(h, 2.5);
        var b = player(h, 9.5);
        var enemyA = target(h, 2.5);
        var enemyB = target(h, 9.5);
        var originA = a.position();
        var originB = b.position();
        Wire[] wire = new Wire[2];
        ItemStack[] stacks = new ItemStack[2];
        EntityTracker[] tracker = new EntityTracker[2];
        long[] frame = new long[1];
        loaded(h).thenExecute(() -> {
            stacks[0] = give(a, ADAPTIVE, 12);
            stacks[1] = give(b, ADAPTIVE, 12);
            TestPlayers.drain(b);
            wire[0] = equipCamera(h, a, stacks[0]);
            check(h, packets(TestPlayers.outbound(b), ClientboundSetCameraPacket.class).isEmpty(),
                    "A's camera selection is not queued to B");
            wire[1] = equipCamera(h, b, stacks[1]);
            check(h, Set.of(wire[0].mount(), wire[0].camera(), wire[1].mount(), wire[1].camera()).size() == 4,
                    "Independent owners receive distinct private mount/camera entity IDs");
            InputRouter.onPunch(a);
            InputRouter.onPunch(b);
            tracker[0] = swordTracker(h, a);
            tracker[1] = swordTracker(h, b);
            windup(h, a, originA, enemyA);
            windup(h, b, originB, enemyB);
            check(h, ammo(stacks[0]).rounds() == 11 && ammo(stacks[1]).rounds() == 11,
                    "Both independent accepted lights pay before either contact");
        }).thenIdle(2).thenExecute(() -> {
            windup(h, a, originA, enemyA);
            windup(h, b, originB, enemyB);
            heartbeat(h, a);
            heartbeat(h, b);
            frame[0] = PlayerAnimations.serverFrames(b);
            TestPlayers.drain(a);
            TestPlayers.drain(b);
            a.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            WeaponRuntime.tickPlayer(a);
            restored(h, a, TestPlayers.outbound(a), wire[0]);
            var other = TestPlayers.outbound(b);
            check(h, tracker[0].isClosed() && !SuperCamera.active(a) && !tracker[1].isClosed()
                            && SuperCamera.swordActive(b) && PlayerAnimations.swordAttacking(b)
                            && PlayerAnimations.serverFrames(b) == frame[0]
                            && packets(other, ClientboundSetCameraPacket.class).isEmpty()
                            && packets(other, ClientboundRemoveEntitiesPacket.class).stream().noneMatch(packet ->
                                packet.entityIds().contains(wire[1].mount()) || packet.entityIds().contains(wire[1].camera())),
                    "A's release cannot close, advance, reset or send cleanup packets to B's actual tracker/camera");
        }).thenIdle(lightContact() - 1).thenExecute(() -> {
            heartbeat(h, b);
            check(h, PlayerAnimations.serverFrames(b) > frame[0] && ammo(stacks[1]).rounds() == 11,
                    "Unaffected owner continues real BetterModel frames with its own paid ammo state");
            WeaponRuntime.tickPlayer(a);
            WeaponRuntime.tickPlayer(b);
            check(h, enemyA.getHealth() == HP && enemyB.getHealth() < HP
                            && a.position().distanceToSqr(originA) < EPS * EPS
                            && b.position().distanceToSqr(originB) < EPS * EPS && ammo(stacks[0]).rounds() == 11,
                    "A's early release cancels its HP contact without refund; B's independent contact still damages its enemy");
            hands(h, b, stacks[1]);
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 600, environment = "destiny-test:w90_isolated")
    public void deathSpectatorAndLevelChangeReleaseExactOwnedCameraAndLimb(GameTestHelper h) {
        var dead = player(h, 2.5);
        var spectator = player(h, 6.5);
        var moved = player(h, 9.5);
        var owners = List.of(dead, spectator, moved);
        var enemies = List.of(target(h, 2.5), target(h, 6.5), target(h, 9.5));
        var origins = owners.stream().map(ServerPlayer::position).toList();
        Wire[] wire = new Wire[3];
        ItemStack[] stacks = new ItemStack[3];
        EntityTracker[] tracker = new EntityTracker[3];
        loaded(h).thenExecute(() -> {
            for (int i = 0; i < owners.size(); i++) {
                var p = owners.get(i);
                stacks[i] = give(p, ADAPTIVE, 12);
                wire[i] = equipCamera(h, p, stacks[i]);
                InputRouter.onPunch(p);
                tracker[i] = swordTracker(h, p);
                windup(h, p, origins.get(i), enemies.get(i));
            }
        }).thenIdle(2).thenExecute(() -> {
            for (int i = 0; i < owners.size(); i++) {
                windup(h, owners.get(i), origins.get(i), enemies.get(i));
                TestPlayers.drain(owners.get(i));
            }
            dead.hurtServer(h.getLevel(), dead.damageSources().genericKill(), 10000);
            check(h, dead.isDeadOrDying(), "Actual server damage kills the death fixture");
            WeaponRuntime.tickPlayer(dead);
            var deathPackets = TestPlayers.outbound(dead);
            removed(h, deathPackets, wire[0]);
            check(h, packets(deathPackets, ClientboundPlayerPositionPacket.class).isEmpty(),
                    "Dead owner is not teleported by camera cleanup");

            spectator.setGameMode(GameType.SPECTATOR);
            WeaponRuntime.tickPlayer(spectator);
            removed(h, TestPlayers.outbound(spectator), wire[1]);

            ServerLevel other = null;
            for (var level : h.getLevel().getServer().getAllLevels()) {
                if (level != h.getLevel()) { other = level; break; }
            }
            check(h, other != null, "Another existing test dimension is available");
            var original = moved.level();
            moved.setServerLevel(other);
            // Embedded fixture transition plus the real Fabric event; not proof of client dimension loading.
            ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.invoker().afterChangeLevel(moved, original, other);
            var dimensionPackets = TestPlayers.outbound(moved);
            removed(h, dimensionPackets, wire[2]);
            check(h, packets(dimensionPackets, ClientboundSetCameraPacket.class).isEmpty()
                            && packets(dimensionPackets, ClientboundPlayerPositionPacket.class).isEmpty(),
                    "Old-dimension camera cleanup never sends its restore/correction into the new level");
            for (int i = 0; i < owners.size(); i++) {
                var p = owners.get(i);
                check(h, tracker[i].isClosed() && !SuperCamera.active(p) && !PlayerAnimations.swordPlaying(p)
                                && ammo(stacks[i]).rounds() == 11,
                        "Invalidation closes exact owned BetterModel tracker/private camera without ammunition refill");
            }
        }).thenIdle(lightContact() - 1).thenExecute(() -> {
            for (int i = 0; i < owners.size(); i++) {
                WeaponRuntime.tickPlayer(owners.get(i));
                check(h, enemies.get(i).getHealth() == HP && ammo(stacks[i]).rounds() == 11
                                && owners.get(i).position().distanceToSqr(origins.get(i)) < EPS * EPS,
                        "Pre-contact life/mode/dimension cancellation never applies late HP or movement and never refunds cost");
            }
        }).thenSucceed();
    }
}
