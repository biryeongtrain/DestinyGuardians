package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponReticleHud;
import kim.biryeong.destiny.hud.WeaponScopeHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.camera.api.CameraEffects;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/** Parent registers/runs centrally after its shared W91 scoped-IDLE getter integration.
 * Real crouch ticks, funded reload and Polymer packets; no forged Honed charge or clocks.
 * No client render/perspective/native-input claim is made by these server tests.
 */
public final class WeaponIzanagiScopeW162GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static WeaponCatalog.Entry entry() { return WeaponCatalog.find("izanagis_burden").orElseThrow(); }
    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }
    private static long scopeNodes(ServerPlayer p) {
        return DisplayHud.getHuds(p).keySet().stream().filter(id -> id.startsWith(WeaponScopeHud.PREFIX)).count();
    }
    private static ItemStack wire(GameTestHelper h, ServerPlayer p) {
        return PolymerItemUtils.getPolymerItemStack(p.getMainHandItem(),
                ((PacketContextProvider) (Object) p.connection).getPacketContext(), h.getLevel().registryAccess());
    }
    private static void ammo(GameTestHelper h, ItemStack stack, int loaded, int reserve, int charge) {
        var ammo = WeaponItems.magazine(stack, WeaponProfile.forEntry(entry()));
        check(h, ammo.rounds() == loaded && ammo.reserve() == reserve && ammo.overflow() == 0
                && WeaponIzanagi.charge(stack) == charge, "Exact finite ammo/Honed state preserved: " + loaded + "/" + reserve + " x" + charge);
    }
    private static void hud(GameTestHelper h, ServerPlayer p, int tint) {
        check(h, WeaponAiming.scoped(p) && scopeNodes(p) == 2, "Real owner ADS authorizes exactly two scope nodes");
        check(h, DisplayHud.getHuds(p).keySet().stream().noneMatch(id -> id.startsWith(WeaponReticleHud.PREFIX)),
                "Generic reticle absent during real scope");
        var frame = (ItemDisplayHud) DisplayHud.getHud(p, WeaponScopeHud.FRAME_ID);
        var center = (ItemDisplayHud) DisplayHud.getHud(p, WeaponScopeHud.CENTER_ID);
        check(h, !frame.isAboveHand() && frame.getLocation().z() == 0 && center.isAboveHand() && center.getLocation().z() == 6,
                "Scope frame behind vitals/ammo; center above hand");
        for (var node : List.of(frame, center)) {
            check(h, node.getAlignment() == DisplayHud.HudAlignment.CENTER && node.getLocation().x() == 960
                    && node.getLocation().y() == 540, "HUD stays on real center aim ray");
            check(h, node.getItem().get(DataComponents.CUSTOM_MODEL_DATA).colors().equals(List.of(tint)),
                    "Funded charge alone controls W162 scope tint");
        }
        check(h, Identifier.parse("destiny:gui/hud/scope_w162_izanagis_burden_frame").equals(frame.getItem().get(DataComponents.ITEM_MODEL))
                && Identifier.parse("destiny:gui/hud/scope_w162_izanagis_burden_reticle").equals(center.getItem().get(DataComponents.ITEM_MODEL)),
                "Real HUD uses both newly authored Izanagi assets");
    }

    private static final class Fixture {
        final GameTestHelper h;
        final long created;
        final List<ServerPlayer> players = new ArrayList<>();
        Fixture(GameTestHelper h) {
            this.h = h; created = h.getLevel().getServer().getTickCount();
            TestCleanup.register(h, () -> {
                for (var p : players) {
                    WeaponRuntime.cleanup(p); WeaponAiming.cleanup(p); WeaponIzanagiPresentation.cleanup(p);
                    for (var id : List.copyOf(DisplayHud.getHuds(p).keySet())) DisplayHud.removeHud(p, id);
                    CombatHud.remove(p); CameraEffects.resetFov(p); TestPlayers.remove(p);
                }
            });
            for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
        }
        ServerPlayer player(int z, WeaponModels.Grip grip, int loaded, int reserve) {
            var p = TestPlayers.create(h, new Vec3(3, 4, z), -90, 0, "W162_" + UUID.randomUUID().toString().substring(0, 8));
            players.add(p); p.setNoGravity(true); p.setOnGround(true); p.setAttached(WeaponLoadout.ENABLED, false);
            var stack = WeaponModels.withGrip(WeaponItems.create(entry()), grip).orElseThrow();
            WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry()), loaded, reserve));
            p.setItemInHand(InteractionHand.MAIN_HAND, stack);
            p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.EMERALD, 4));
            WeaponRuntime.tickPlayer(p); TestPlayers.drain(p);
            return p;
        }
        void at(int tick, Runnable action) {
            check(h, h.getLevel().getServer().getTickCount() == created, "All callbacks registered at initialization");
            h.runAfterDelay(tick, () -> {
                check(h, h.getLevel().getServer().getTickCount() - created == tick, "Observe real scheduled server tick");
                for (var p : players) { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); }
                action.run();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void unchargedBothGripsScopeOnlyAfterRealInputAndRestoreOnRelease(GameTestHelper h) {
        var f = new Fixture(h);
        for (var grip : WeaponModels.Grip.values()) ads(f.player(8 + f.players.size() * 12, grip, 2, 7), true);
        for (int tick = 1; tick <= 22; tick++) f.at(tick, () -> {
            for (var p : f.players) {
                CombatHud.update(p);
                check(h, WeaponAiming.scoped(p) == (WeaponAiming.progress(p) >= .5f), "Existing half-transition threshold");
            }
        });
        f.at(23, () -> {
            for (var p : f.players) {
                var stack = p.getMainHandItem(); var before = stack.copy();
                CombatHud.update(p); hud(h, p, 0xFFFFFF);
                var packet = wire(h, p);
                check(h, WeaponScopes.model(entry()).equals(packet.get(DataComponents.ITEM_MODEL)), "Uncharged ADS selects FP-only wrapper");
                check(h, Identifier.parse(entry().item_model()).equals(stack.get(DataComponents.ITEM_MODEL)) && ItemStack.matches(before, stack),
                        "HUD/serialization preserve actual original model, ammo, grip and every component");
                ammo(h, stack, 2, 7, 0);
                check(h, p.getOffhandItem().is(Items.EMERALD) && p.getOffhandItem().getCount() == 4, "Offhand preserved");
                ads(p, false);
            }
        });
        for (int tick = 24; tick <= 45; tick++) f.at(tick, () -> {
            for (var p : f.players) CombatHud.update(p);
        });
        f.at(46, () -> {
            for (var p : f.players) {
                check(h, !WeaponAiming.scoped(p) && WeaponAiming.progress(p) == 0 && scopeNodes(p) == 0, "Release removes scope and restores HIP");
                check(h, projected(p.getMainHandItem().get(DataComponents.ITEM_MODEL)).equals(wire(h, p).get(DataComponents.ITEM_MODEL)), "Original packet route restored");
                ammo(h, p.getMainHandItem(), 2, 7, 0);
            }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void realHonedCommitScopesChargedIdleButNeverHidesNormalOrHonedReload(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(10, WeaponModels.Grip.TWO_HAND, 1, 5);
        var normal = f.player(22, WeaponModels.Grip.TWO_HAND, 1, 5);
        var stack = p.getMainHandItem();
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.DROP_ALL_ITEMS, BlockPos.ZERO, Direction.UP));
        check(h, WeaponRuntime.reloading(p) && WeaponIzanagi.honing(p), "Real CtrlQ admits funded transaction");
        for (int tick = 1; tick <= 60; tick++) f.at(tick, () -> {
            ammo(h, stack, 1, 5, 0);
            WeaponScopeHud.update(p, WeaponRuntime.reloading(p));
            check(h, scopeNodes(p) == 0 && projected(WeaponIzanagiPresentation.model(stack)).equals(wire(h, p).get(DataComponents.ITEM_MODEL)),
                    "Actual Honed animation retains W91 route and no scope overlay until full-ready commit");
        });
        f.at(61, () -> { ammo(h, stack, 1, 2, 4); ads(p, true); ads(normal, true); });
        for (int tick = 62; tick <= 83; tick++) f.at(tick, () -> { CombatHud.update(p); CombatHud.update(normal); });
        f.at(84, () -> {
            ammo(h, stack, 1, 2, 4);
            check(h, WeaponIzanagiPresentation.active(stack) && WeaponAiming.progress(p) == 1, "Live charged IDLE and real settled ADS coexist");
            var before = stack.copy();
            CombatHud.update(p); hud(h, p, 0xFFAA8C);
            var packet = wire(h, p);
            check(h, WeaponScopes.model(entry()).equals(packet.get(DataComponents.ITEM_MODEL)),
                    "Parent shared getter: scoped charged IDLE overrides W91 FP loaded-round body");
            var context = ((PacketContextProvider) (Object) p.connection).getPacketContext();
            check(h, ItemStack.matches(before, PolymerItemUtils.getRealItemStack(packet, context, h.getLevel().registryAccess()))
                    && ItemStack.matches(before, stack), "Polymer roundtrip and HUD retain funded Honed tag, real ammo and all selectors");
            WeaponScopeHud.update(p, true);
            check(h, scopeNodes(p) == 0 && ItemStack.matches(before, stack), "HUD reload flag has no gameplay authority");
            CombatHud.update(p); hud(h, p, 0xFFAA8C);
            p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                    ServerboundPlayerActionPacket.Action.DROP_ITEM, BlockPos.ZERO, Direction.UP));
            check(h, !WeaponRuntime.reloading(p) && WeaponAiming.scoped(p), "Existing funded charge rejects ordinary reload without clearing scope");
            CombatHud.update(p);
            hud(h, p, 0xFFAA8C); hud(h, normal, 0xFFFFFF);
            normal.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                    ServerboundPlayerActionPacket.Action.DROP_ITEM, BlockPos.ZERO, Direction.UP));
            CombatHud.update(normal);
            check(h, WeaponRuntime.reloading(normal) && !WeaponIzanagi.honing(normal) && !WeaponAiming.scoped(normal) && scopeNodes(normal) == 0,
                    "Actual normal reload suspends uncharged scope and removes HUD immediately");
            check(h, projected(WeaponIzanagiPresentation.model(normal.getMainHandItem())).equals(wire(h, normal).get(DataComponents.ITEM_MODEL)),
                    "Actual RELOAD retains W91 priority over scope wrapper");
            ammo(h, stack, 1, 2, 4);
        });
        f.at(90, () -> {
            ammo(h, stack, 1, 2, 4);
            ammo(h, normal.getMainHandItem(), 1, 5, 0);
            check(h, WeaponRuntime.reloading(normal) && scopeNodes(normal) == 0, "No early ammo transfer or hidden reload while crouch held");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 35, environment = "destiny-test:w90_fov_w45")
    public void externalCameraSwapDeathAndForeignCleanupRespectScopeOwnership(GameTestHelper h) {
        var config = kim.biryeong.minigamelib.shaderfx.impl.ModConfig.getInstance();
        boolean previous = config.dynamicFovShader; config.dynamicFovShader = true;
        TestCleanup.register(h, () -> config.dynamicFovShader = previous);
        var f = new Fixture(h);
        var external = f.player(6, WeaponModels.Grip.TWO_HAND, 2, 7);
        var swap = f.player(14, WeaponModels.Grip.TWO_HAND, 2, 7);
        var dying = f.player(22, WeaponModels.Grip.TWO_HAND, 2, 7);
        for (var p : f.players) { CameraEffects.setFov(p, 80); ads(p, true); }
        for (int tick = 1; tick <= 22; tick++) f.at(tick, () -> {});
        f.at(23, () -> {
            for (var p : f.players) { CombatHud.update(p); hud(h, p, 0xFFFFFF); }
            check(h, CameraEffects.getFov(external) == 80 && WeaponAiming.progress(external) == 1,
                    "Existing sourced zoom/camera owner remains authoritative");
            var ownerNode = DisplayHud.getHud(external, WeaponScopeHud.FRAME_ID);
            WeaponScopeHud.remove(swap);
            check(h, ownerNode == DisplayHud.getHud(external, WeaponScopeHud.FRAME_ID) && !ownerNode.isRemoved(), "Foreign HUD cleanup cannot remove owner's scope");
            CameraEffects.setFov(external, 55); WeaponAiming.tick(external);
            check(h, WeaponAiming.scoped(external) && WeaponAiming.progress(external) == 1
                            && DisplayHud.getHud(external, WeaponScopeHud.FRAME_ID) == ownerNode && !ownerNode.isRemoved(),
                    "Changing only shader FOV leaves the real scope session and exact HUD owner intact");
            WeaponAiming.cleanup(external);
            check(h, CameraEffects.getFov(external) == 55, "External camera takeover survives ADS cleanup");
            swap.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(entry()));
            WeaponRuntime.tickPlayer(swap); dying.setHealth(0); WeaponRuntime.tickPlayer(dying);
            for (var p : f.players) {
                CombatHud.update(p);
                check(h, !WeaponAiming.scoped(p) && scopeNodes(p) == 0, "Explicit cleanup, exact-stack swap or death removes owned scope");
            }
            h.succeed();
        });
    }
}
