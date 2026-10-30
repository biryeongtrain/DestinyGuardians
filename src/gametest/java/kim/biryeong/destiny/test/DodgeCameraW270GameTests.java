package kim.biryeong.destiny.test;

import io.netty.buffer.Unpooled;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.ability.hunter.HunterSkillTiming;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.tracker.EntityTracker;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetCameraPacket;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.Map;

/** Real limb/camera packets on normal server animation ticks; native visual QA remains separate. */
public final class DodgeCameraW270GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static void profileReady(GameTestHelper h, Runnable action) {
        check(h, SuperCamera.ENABLED && ProfileWeaponView.enabled()
                && net.fabricmc.loader.api.FabricLoader.getInstance().isModLoaded("polymer-autohost"),
                "Requires production rear camera, profile view and startup pack generation");
        h.startSequence().thenWaitUntil(() -> {
            check(h, BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(), "Await authored Hunter limb");
            var gun = WeaponItems.create(WeaponCatalog.find("ace_of_spades").orElseThrow());
            var route = WeaponCombatItem.INSTANCE.getPolymerItemModel(gun, null, h.getLevel().registryAccess());
            check(h, kim.biryeong.destiny.compat.pack.ProfileArmAssets.graph(route) != null,
                    "Await successful profile graph publication");
        }).thenExecute(action);
    }

    private static ServerPlayer player(GameTestHelper h, boolean marksman, int index) {
        int x = 3 + index * 6;
        for (int dx = -2; dx <= 2; dx++) for (int z = 1; z <= 7; z++) h.setBlock(x + dx, 0, z, Blocks.STONE);
        var p = TestPlayers.hunter(h, Element.ARC, new Vec3(x + .5, 1, 4.5), 0, 0, "W270Dodge" + index);
        TestCleanup.register(h, () -> { CameraViews.stop(p); TestPlayers.remove(p); });
        p.setNoGravity(true);
        p.setOnGround(true);
        check(h, CharacterLoadouts.selectAbility(p, AbilitySlot.CLASS_ABILITY,
                marksman ? HunterAbilities.MARKSMANS_DODGE : HunterAbilities.GAMBLERS_DODGE) == null,
                "Equip registered dodge variant");
        p.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(WeaponCatalog.find("ace_of_spades").orElseThrow()));
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.TORCH));
        Guardians.runtime(p).lastInput = new Input(true, false, false, false, false, false, false);
        // Embedded players are not in PlayerList. Advance their lifecycle, never duplicate global animation/camera ticks.
        h.onEachTick(() -> {
            if (SuperCamera.active(p)) p.connection.handleMovePlayer(
                    new ServerboundMovePlayerPacket.Rot(p.getYRot(), p.getXRot(), true, false));
            AbilityService.tickPlayer(p);
        });
        return p;
    }

    private static List<Integer> cameraIds(ServerPlayer p) {
        return TestPlayers.outbound(p).stream().filter(ClientboundSetCameraPacket.class::isInstance)
                .map(ClientboundSetCameraPacket.class::cast).map(packet -> {
                    var buf = new FriendlyByteBuf(Unpooled.buffer());
                    try { ClientboundSetCameraPacket.STREAM_CODEC.encode(buf, packet); return buf.readVarInt(); }
                    finally { buf.release(); }
                }).toList();
    }

    private static Object field(Class<?> type, Object object, String name) {
        try { var f = type.getDeclaredField(name); f.setAccessible(true); return f.get(object); }
        catch (ReflectiveOperationException e) { throw new AssertionError("Inspect actual limb " + name, e); }
    }

    private static EntityTracker tracker(ServerPlayer p) {
        var playback = ((Map<?, ?>) field(PlayerAnimations.class, null, "ACTIVE")).get(p.getUUID());
        if (playback == null) throw new AssertionError("Accepted dodge has no actual playback");
        return (EntityTracker) field(playback.getClass(), playback, "tracker");
    }

    private static void emptyHands(GameTestHelper h, ServerPlayer p) {
        for (String name : List.of("pli_left_item", "pri_right_item")) {
            var bone = tracker(p).bone(b -> b.name().rawName().equals(name));
            check(h, bone != null && bone.getDisplay() != null, "Actual hand display exists: " + name);
            var display = bone.getDisplay();
            var entity = (Display.ItemDisplay) field(display.getClass(), display, "display");
            check(h, entity.getItemStack().isEmpty(), "Dodge keeps actual visual hand empty: " + name);
        }
    }

    private static void start(GameTestHelper h, ServerPlayer p, boolean marksman) {
        TestPlayers.drain(p);
        check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.OK, "Dodge accepted");
        var ids = cameraIds(p);
        check(h, ids.size() == 1 && ids.getFirst() != p.getId() && SuperCamera.active(p),
                "Acceptance sends exactly one real non-self SetCamera packet");
        check(h, PlayerAnimations.isPlaying(p) && PlayerAnimations.activeClip(p).equals(
                marksman ? "h15_dodge_marksman_forward" : "h15_roll_forward"), "Actual variant source clip playing");
        check(h, SuperCamera.cameraPosition(p).subtract(p.getEyePosition()).dot(p.getLookAngle()) < 0,
                "Camera is behind authoritative player aim");
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated", maxTicks = 1200)
    public void bothDodgesKeepRearCameraThroughContactAndNaturallyRestoreSelf(GameTestHelper h) {
        profileReady(h, () -> {
            var players = List.of(player(h, false, 0), player(h, true, 1));
            var guns = players.stream().map(ServerPlayer::getMainHandItem).toList();
            var offhands = players.stream().map(ServerPlayer::getOffhandItem).toList();
            int longest = 0;
            for (int i = 0; i < players.size(); i++) {
                var p = players.get(i);
                start(h, p, i == 1);
                check(h, p.getMainHandItem() == guns.get(i) && p.getOffhandItem() == offhands.get(i),
                        "Activation preserves authoritative hand objects");
                int sourceTicks = (int) Math.ceil(tracker(p).renderer().animation(PlayerAnimations.activeClip(p))
                        .orElseThrow().length() * 20);
                longest = Math.max(longest, sourceTicks);
                h.runAfterDelay(sourceTicks - 1, () -> check(h,
                        SuperCamera.active(p) && PlayerAnimations.isPlaying(p), "Do not retire before source clip finishes"));
            }
            h.runAfterDelay(HunterSkillTiming.DODGE_CONTACT_TICKS + 1, () -> {
                for (int i = 0; i < players.size(); i++) {
                    var p = players.get(i);
                    check(h, SuperCamera.active(p) && PlayerAnimations.isPlaying(p) && cameraIds(p).isEmpty(),
                            "Contact does not restore camera or truncate source motion");
                    emptyHands(h, p);
                    check(h, p.getMainHandItem() == guns.get(i) && p.getOffhandItem() == offhands.get(i),
                            "Contact changes visual hands only");
                    // Restoration must preserve the current selection, not overwrite it with the accepted gun.
                    p.getInventory().setItem(1, new ItemStack(Items.DIAMOND, 3));
                    p.getInventory().setSelectedSlot(1);
                }
            });
            // Source duration plus the existing start tick, six callback-grace ticks and one observation tick.
            h.runAfterDelay(longest + 8, () -> {
                for (var p : players) {
                    check(h, !SuperCamera.active(p) && !PlayerAnimations.isPlaying(p) && p.getCamera() == p,
                            "Normal server ticks naturally retire model and camera");
                    check(h, cameraIds(p).equals(List.of(p.getId())), "Natural retirement sends one self-camera packet");
                    check(h, p.getMainHandItem().is(Items.DIAMOND) && p.getMainHandItem().getCount() == 3
                            && p.getInventory().getSelectedSlot() == 1, "Current authoritative hand survives restoration");
                }
                h.succeed();
            });
        });
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated", maxTicks = 1200)
    public void subclassAndDeathCancelBothVariantsWithoutLateResurrection(GameTestHelper h) {
        profileReady(h, () -> {
            var players = List.of(player(h, false, 0), player(h, true, 1), player(h, false, 2), player(h, true, 3));
            for (int i = 0; i < players.size(); i++) start(h, players.get(i), i % 2 == 1);
            // Cancel before the two-tick contact; dead embedded players use the real per-player lifecycle below.
            for (int i = 0; i < players.size(); i++) {
                var p = players.get(i);
                if (i < 2) check(h, CharacterLoadouts.selectSubclass(p, Element.SOLAR) == null, "Subclass change accepted");
                else { p.setHealth(0); AbilityService.tickPlayer(p); }
                check(h, !SuperCamera.active(p) && !PlayerAnimations.isPlaying(p), "Cancellation immediately retires owned presentation");
                check(h, cameraIds(p).equals(List.of(p.getId())), "Cancellation restores self once");
            }
            h.runAfterDelay(35, () -> {
                for (var p : players) check(h, !SuperCamera.active(p) && !PlayerAnimations.isPlaying(p)
                        && cameraIds(p).isEmpty(), "Pending contact/callback cannot resurrect cancelled camera or model");
                h.succeed();
            });
        });
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated", maxTicks = 1200)
    public void foreignCameraViewsRejectBothDodgesWithoutStealingView(GameTestHelper h) {
        profileReady(h, () -> {
            for (int i = 0; i < 2; i++) {
                var p = player(h, i == 1, i);
                CameraViews.open(p, h.getLevel(), p.getEyePosition().add(0, 2, -3), 0, 0);
                var foreign = CameraViews.get(p);
                check(h, foreign != null, "Actual external cinematic owns view");
                var hand = p.getMainHandItem();
                var velocity = p.getDeltaMovement();
                TestPlayers.drain(p);
                check(h, !AbilityService.equipped(p, AbilitySlot.CLASS_ABILITY).orElseThrow().activate(p),
                        "Concrete dodge rejects foreign camera before acceptance");
                check(h, CameraViews.get(p) == foreign && !SuperCamera.active(p) && !PlayerAnimations.isPlaying(p)
                        && cameraIds(p).isEmpty(), "Rejected dodge never replaces or restores foreign camera");
                check(h, p.getMainHandItem() == hand && p.getDeltaMovement().equals(velocity)
                        && Guardians.runtime(p).invulnerableTicks == 0, "Rejected dodge has no inventory/motion/protection effects");
            }
            h.succeed();
        });
    }
}
