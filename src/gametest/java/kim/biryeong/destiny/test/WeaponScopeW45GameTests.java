package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponReticleHud;
import kim.biryeong.destiny.hud.WeaponScopeHud;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.camera.api.CameraEffects;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** Register through the main agent's coordinated entrypoint change.
 * Vanilla DisplayHud cannot observe F5: scope graphics follow ADS in every perspective.
 * Sniper first-person branches are empty; LFR uses source-cloned 3D guns with open optics.
 * Third-person always uses original ADS models.
 * The normal-depth aperture sits behind other HUDs; only the aim center renders above the hand.
 */
public final class WeaponScopeW45GameTests {
    private static final List<String> IDS = List.of(
            "bite_of_the_fox", "beloved", "apostate", "line_in_the_sand", "stormchaser");
    // All supported profiles currently fit within 20 ticks. Use real scheduled server ticks,
    // never a same-tick loop that WeaponAimState deliberately ignores.
    private static final int SETTLE = 22;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static WeaponCatalog.Entry entry(String id) {
        return WeaponCatalog.find(id).orElseThrow();
    }

    private static ServerPlayer player(GameTestHelper h, String id) {
        var player = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), -90, 0);
        player.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(entry(id)));
        TestCleanup.register(h, () -> {
            WeaponRuntime.cleanup(player);
            WeaponScopeHud.remove(player);
            CombatHud.remove(player);
            // CombatHud also owns ammo nodes outside its own health/ability prefix.
            for (String hudId : List.copyOf(DisplayHud.getHuds(player).keySet())) {
                DisplayHud.removeHud(player, hudId);
            }
            CameraEffects.resetFov(player);
            TestPlayers.remove(player);
        });
        return player;
    }

    private static long nodes(ServerPlayer player, String prefix) {
        return DisplayHud.getHuds(player).keySet().stream().filter(id -> id.startsWith(prefix)).count();
    }

    private static String pose(ItemStack stack) {
        var data = stack.get(DataComponents.CUSTOM_MODEL_DATA);
        return data == null ? null : data.getString(0);
    }

    private static void absent(GameTestHelper h, ServerPlayer player) {
        check(h, !WeaponAiming.scoped(player), "No owner-authorized runtime scope");
        check(h, nodes(player, WeaponScopeHud.PREFIX) == 0, "Both scope HUD nodes removed");
    }

    private static void scopeHud(GameTestHelper h, ServerPlayer player) {
        check(h, WeaponAiming.scoped(player), "Live owner session authorizes scope");
        check(h, WeaponScopeHud.PREFIX.equals("destiny:scope_w45_")
                && WeaponScopeHud.FRAME_ID.equals(WeaponScopeHud.PREFIX + "frame")
                && WeaponScopeHud.CENTER_ID.equals(WeaponScopeHud.PREFIX + "center"), "Stable W45 HUD IDs");
        boolean sniper = WeaponItems.entry(player.getMainHandItem()).orElseThrow().family().equals("sniper_rifle");
        check(h, WeaponScopeHud.MAX_NODES == 2 && nodes(player, WeaponScopeHud.PREFIX) == (sniper ? 2 : 1),
                "Sniper uses two nodes; LFR keeps 3D gun and only the center node");
        var frame = DisplayHud.getHud(player, WeaponScopeHud.FRAME_ID);
        var center = DisplayHud.getHud(player, WeaponScopeHud.CENTER_ID);
        check(h, center instanceof ItemDisplayHud, "Real scope center exists");
        if (sniper) {
            check(h, frame instanceof ItemDisplayHud, "Sniper aperture exists");
            check(h, !frame.isAboveHand() && frame.getLocation().z() == 0,
                    "Aperture uses normal HUD depth zero, behind ammo/health/abilities");
        } else check(h, frame == null, "LFR has no 2D receiver/aperture replacement");
        check(h, center.isAboveHand() && center.getLocation().z() == 6,
                "Only aim center renders above hand at depth six");
        for (var hud : sniper ? List.of(frame, center) : List.of(center)) {
            check(h, hud.getAlignment() == DisplayHud.HudAlignment.CENTER
                    && hud.getLocation().x() == 960 && hud.getLocation().y() == 540,
                    "Both scope nodes remain centered at 960,540");
        }
        check(h, nodes(player, WeaponReticleHud.PREFIX) == 0, "Generic reticle is suppressed while scoped");
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void actualCrouchScopesAllFiveAtHalfTransitionAndReleaseRestoresHip(GameTestHelper h) {
        var players = new ArrayList<ServerPlayer>();
        var snapshots = new ArrayList<ItemStack>();
        for (String id : IDS) {
            var player = player(h, id);
            player.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.EMERALD, 4));
            players.add(player);
            snapshots.add(player.getMainHandItem().copy());
            CombatHud.update(player);
            absent(h, player);
            check(h, nodes(player, WeaponReticleHud.PREFIX) == 2, "Hip initially has generic reticle: " + id);
            ads(player, true);
        }
        for (int tick = 1; tick <= SETTLE; tick++) h.runAfterDelay(tick, () -> {
            for (var player : players) {
                WeaponRuntime.tickPlayer(player);
                CombatHud.update(player);
                boolean halfway = WeaponAiming.progress(player) >= .5f;
                check(h, WeaponAiming.scoped(player) == halfway, "Scope follows real input progress threshold");
                check(h, (halfway ? "scope" : "hip").equals(pose(player.getMainHandItem())),
                        "Real stack selector follows transition threshold");
                if (halfway) scopeHud(h, player); else absent(h, player);
            }
        });
        h.runAfterDelay(SETTLE + 1, () -> {
            for (var player : players) {
                check(h, WeaponAiming.progress(player) == 1, "Timed dummy ticks reach full ADS");
                scopeHud(h, player);
                var stack = player.getMainHandItem();
                var before = stack.copy();
                for (int i = 0; i < 3; i++) {
                    WeaponScopeHud.update(player, false);
                    CombatHud.update(player);
                }
                check(h, ItemStack.matches(before, stack), "Scope and combat HUDs never mutate ammo or any held components");
                WeaponScopeHud.update(player, true);
                check(h, nodes(player, WeaponScopeHud.PREFIX) == 0 && ItemStack.matches(before, stack),
                        "Cosmetic reload flag hides graphics without reloading or changing ammunition");
                check(h, !WeaponRuntime.reloading(player), "HUD reload flag cannot begin a real reload");
                CombatHud.update(player);
                scopeHud(h, player);
                ads(player, false);
            }
        });
        for (int tick = SETTLE + 2; tick <= SETTLE * 2 + 1; tick++) h.runAfterDelay(tick, () -> {
            for (var player : players) {
                WeaponRuntime.tickPlayer(player);
                CombatHud.update(player);
                check(h, WeaponAiming.scoped(player) == (WeaponAiming.progress(player) >= .5f),
                        "Release crosses the same scope threshold in reverse");
            }
        });
        h.runAfterDelay(SETTLE * 2 + 2, () -> {
            for (int i = 0; i < players.size(); i++) {
                var player = players.get(i);
                absent(h, player);
                check(h, WeaponAiming.progress(player) == 0 && "hip".equals(pose(player.getMainHandItem())),
                        "Release restores HIP pose and zero progress: " + IDS.get(i));
                check(h, nodes(player, WeaponReticleHud.PREFIX) == 2, "Generic reticle returns after release");
                check(h, ItemStack.matches(snapshots.get(i), player.getMainHandItem()),
                        "Input and HUD preserve original weapon model, ammunition and grip after release");
                check(h, player.getOffhandItem().is(Items.EMERALD) && player.getOffhandItem().getCount() == 4,
                        "Scope leaves offhand untouched");
            }
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 35, environment = "destiny-test:w90_fov_w45")
    public void reloadSwapSuspendAndExternalFovTakeoverResetOwnedScope(GameTestHelper h) {
        var config = kim.biryeong.minigamelib.shaderfx.impl.ModConfig.getInstance();
        boolean previous = config.dynamicFovShader;
        config.dynamicFovShader = true;
        TestCleanup.register(h, () -> config.dynamicFovShader = previous);
        var reload = player(h, "beloved");
        var swap = player(h, "beloved");
        var suspend = player(h, "beloved");
        var external = player(h, "beloved");
        var players = List.of(reload, swap, suspend, external);
        var profile = WeaponProfile.forEntry(entry("beloved"));
        WeaponItems.save(reload.getMainHandItem(), new WeaponMagazine(profile, 1, 2));
        for (var player : players) {
            CameraEffects.setFov(player, 80);
            ads(player, true);
        }
        for (int tick = 1; tick <= SETTLE; tick++) h.runAfterDelay(tick, () -> {
            for (var player : players) WeaponRuntime.tickPlayer(player);
        });
        var oldSwap = swap.getMainHandItem();
        h.runAfterDelay(SETTLE + 1, () -> {
            for (var player : players) {
                CombatHud.update(player);
                scopeHud(h, player);
            }
            check(h, InputRouter.onPlayerAction(reload, ServerboundPlayerActionPacket.Action.DROP_ITEM)
                    && WeaponRuntime.reloading(reload), "Real Q input starts reload and cancels scope");
            check(h, WeaponItems.magazine(reload.getMainHandItem(), profile).rounds() == 1,
                    "Reload has no early ammunition transfer");
            swap.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(entry("beloved")));
            check(h, !WeaponAiming.scoped(swap), "Same-ID replacement cannot inherit owner stack progress");
            WeaponAiming.suspend(suspend);
            CameraEffects.setFov(external, 55);
            WeaponAiming.tick(external);
            scopeHud(h, external);
            check(h,WeaponAiming.progress(external)==1 && CameraEffects.getFov(external)==55,"Shader FOV is independent of live ADS/scope");
            for (var player : List.of(reload, swap, suspend)) {
                WeaponRuntime.tickPlayer(player);
                CombatHud.update(player);
                absent(h, player);
                check(h, WeaponAiming.progress(player) == 0 && "hip".equals(pose(player.getMainHandItem())),
                        "Each reset clears scope pose and progress");
            }
            check(h, "hip".equals(pose(suspend.getMainHandItem())) && CameraEffects.getFov(suspend) == 80,
                    "Suspend restores original FOV and pose");
            WeaponAiming.cleanup(external);
            check(h, CameraEffects.getFov(external) == 55, "Cleanup preserves the external FOV owner's value");
        });
        h.runAfterDelay(SETTLE + 2, () -> {
            for (var player : List.of(reload, swap, suspend)) {
                WeaponRuntime.tickPlayer(player);
                CombatHud.update(player);
                absent(h, player);
            }
            check(h, WeaponAiming.progress(reload) == 0 && WeaponAiming.progress(suspend) == 0,
                    "Held crouch cannot bypass reload/suspend cancellation");
            check(h, WeaponAiming.progress(swap) < .5f && "hip".equals(pose(oldSwap)),
                    "Replacement starts a fresh transition and old stack returns HIP");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void bothGripsRouteOnlyWireModelAndRoundTripAllAuthoritativeComponents(GameTestHelper h) {
        var player = player(h, "beloved");
        var context = ((PacketContextProvider) (Object) player.connection).getPacketContext();
        for (String id : IDS) for (var grip : WeaponModels.Grip.values()) {
            var entry = entry(id);
            var real = WeaponModels.withGrip(WeaponItems.create(entry), grip).orElseThrow();
            WeaponItems.save(real, new WeaponMagazine(WeaponProfile.forEntry(entry), 1, 2));
            WeaponModels.setPose(real, WeaponModels.Pose.SCOPE);
            boolean two = grip == WeaponModels.Grip.TWO_HAND;
            real.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(
                    List.of(3.25f), List.of(two), List.of("scope", "retained"), List.of(0x123456)));
            real.set(DataComponents.CUSTOM_NAME, Component.literal("W45 retained " + id));
            var tag = real.get(DataComponents.CUSTOM_DATA).copyTag();
            tag.putString("w45_unrelated", "retained");
            real.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
            player.setItemInHand(InteractionHand.MAIN_HAND, real);
            var before = real.copy();
            check(h, WeaponScopes.scoped(real), "Supported live stack has scope pose");
            check(h, !WeaponAiming.scoped(player), "A cosmetic pose alone cannot create an owner aim session");
            WeaponScopeHud.update(player, false);
            absent(h, player);
            var wire = PolymerItemUtils.getPolymerItemStack(real, context, h.getLevel().registryAccess());
            check(h, WeaponScopes.model(entry).equals(wire.get(DataComponents.ITEM_MODEL)), "Only packet model routes to wrapper");
            check(h, Identifier.parse(entry.item_model()).equals(real.get(DataComponents.ITEM_MODEL)), "Real ITEM_MODEL stays original");
            check(h, wire.is(two ? Items.CROSSBOW : Items.STICK) && CrossbowItem.isCharged(wire) == two,
                    "Existing native/two-hand carrier and charge marker remain unchanged");
            var data = wire.get(DataComponents.CUSTOM_MODEL_DATA);
            check(h, Boolean.valueOf(two).equals(data.getBoolean(0))
                    && data.floats().equals(List.of(3.25f)) && data.strings().equals(List.of("scope", "retained"))
                    && data.colors().equals(List.of(0x123456)), "Packet preserves pose data and independent grip selector");
            check(h, real.get(DataComponents.CHARGED_PROJECTILES) == null && ItemStack.matches(before, real),
                    "Wire rendering never mutates the authoritative weapon");
            var roundTrip = PolymerItemUtils.getRealItemStack(wire, context, h.getLevel().registryAccess());
            check(h, ItemStack.matches(before, roundTrip), "Polymer round trip retains every authoritative component");
            WeaponModels.setPose(real, WeaponModels.Pose.HIP);
            wire = PolymerItemUtils.getPolymerItemStack(real, context, h.getLevel().registryAccess());
            check(h, projected(real.get(DataComponents.ITEM_MODEL)).equals(wire.get(DataComponents.ITEM_MODEL)), "HIP restores original packet route");
        }
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void previewLegacyAndUnsupportedScopeStringsNeverGrantRuntimeScope(GameTestHelper h) {
        var player = player(h, "beloved");
        var context = ((PacketContextProvider) (Object) player.connection).getPacketContext();
        ads(player, true);
        for (String id : IDS) for (var grip : WeaponModels.Grip.values()) {
            var entry = entry(id);
            var preview = WeaponModels.withGrip(WeaponModels.create(entry), grip).orElseThrow();
            WeaponModels.setPose(preview, WeaponModels.Pose.SCOPE);
            var legacy = preview.transmuteCopy(Items.STICK);
            for (var stack : List.of(preview, legacy)) {
                player.setItemInHand(InteractionHand.MAIN_HAND, stack);
                var before = stack.copy();
                check(h, "scope".equals(pose(stack)) && WeaponItems.entry(stack).isEmpty()
                        && !WeaponScopes.scoped(stack), "Preview scope string grants no live scope route");
                WeaponRuntime.tickPlayer(player);
                CombatHud.update(player);
                absent(h, player);
                check(h, WeaponAiming.progress(player) == 0, "Preview cannot bind runtime aiming");
                var wire = PolymerItemUtils.getPolymerItemStack(stack, context, h.getLevel().registryAccess());
                check(h, projected(stack, Identifier.parse(entry.item_model())).equals(wire.get(DataComponents.ITEM_MODEL)),
                        "Inert and legacy previews retain original packet model even with scope string");
                check(h, ItemStack.matches(before, stack), "Preview pose, metadata and grip remain unchanged");
            }
        }
        var unsupported = WeaponItems.create(entry("austringer"));
        WeaponModels.setPose(unsupported, WeaponModels.Pose.SCOPE);
        player.setItemInHand(InteractionHand.MAIN_HAND, unsupported);
        check(h, !WeaponScopes.scoped(unsupported) && !WeaponAiming.scoped(player), "Unsupported live weapon cannot scope");
        WeaponScopeHud.update(player, false);
        absent(h, player);
        var wire = PolymerItemUtils.getPolymerItemStack(unsupported, context, h.getLevel().registryAccess());
        check(h, projected(unsupported.get(DataComponents.ITEM_MODEL)).equals(wire.get(DataComponents.ITEM_MODEL)),
                "Unsupported live scope string cannot select wrapper");
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 35, environment = "destiny-test:w90_isolated")
    public void scopeSessionAndHudRemovalRemainOwnerLocal(GameTestHelper h) {
        var owner = player(h, "beloved");
        var other = player(h, "beloved");
        WeaponModels.setPose(other.getMainHandItem(), WeaponModels.Pose.SCOPE);
        ads(owner, true);
        for (int tick = 1; tick <= SETTLE; tick++) h.runAfterDelay(tick, () -> WeaponRuntime.tickPlayer(owner));
        h.runAfterDelay(SETTLE + 1, () -> {
            CombatHud.update(owner);
            scopeHud(h, owner);
            WeaponScopeHud.update(other, false);
            absent(h, other);
            var frame = DisplayHud.getHud(owner, WeaponScopeHud.FRAME_ID);
            var center = DisplayHud.getHud(owner, WeaponScopeHud.CENTER_ID);
            WeaponScopeHud.remove(other);
            WeaponScopeHud.remove(other);
            check(h, DisplayHud.getHud(owner, WeaponScopeHud.FRAME_ID) == frame && !frame.isRemoved()
                    && DisplayHud.getHud(owner, WeaponScopeHud.CENTER_ID) == center && !center.isRemoved(),
                    "Another player's idempotent cleanup cannot remove owner HUD");
            scopeHud(h, owner);
            h.succeed();
        });
    }
}
