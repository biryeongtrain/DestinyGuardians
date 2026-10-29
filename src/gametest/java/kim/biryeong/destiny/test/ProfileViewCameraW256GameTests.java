package kim.biryeong.destiny.test;

import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.compat.pack.ProfileArmAssets;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.weapon.ProfileWeaponView;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponCombatItem;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

/** Actual owner HUD registry regressions; client rendering remains a separate Vision check. */
public final class ProfileViewCameraW256GameTests {
    private static final String PREFIX = "destiny:profile_view_";
    private static final Set<String> PARTS = Set.of("gun", "grenade", "arm_0", "arm_1", "arm_2", "arm_3");

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static ServerPlayer player(GameTestHelper h, Element element) {
        check(h, SuperCamera.ENABLED && ProfileWeaponView.enabled(), "Camera and profile view must be enabled");
        var p = TestPlayers.hunter(h, element, new Vec3(3.5, 1, 3.5), 0, 0, "W256_" + element);
        // Separate LIFO callbacks still release the player if an earlier cleanup fails.
        TestCleanup.register(h, () -> TestPlayers.remove(p));
        TestCleanup.register(h, () -> view(p, "remove"));
        TestCleanup.register(h, () -> SuperCamera.stop(p));
        p.setNoGravity(true);
        p.setOnGround(true);
        Guardians.runtime(p).gcbClient = false;
        Guardians.runtime(p).gcbThirdPerson = false;
        return p;
    }

    private static ItemStack weapon(String id) {
        return WeaponItems.create(WeaponCatalog.find(id).orElseThrow());
    }

    private static void view(ServerPlayer p, String operation) {
        // TestPlayers are not PlayerList members, so invoke the real private updater explicitly.
        try {
            var method = ProfileWeaponView.class.getDeclaredMethod(operation, ServerPlayer.class);
            method.setAccessible(true);
            method.invoke(null, p);
        } catch (ReflectiveOperationException error) {
            throw new AssertionError("ProfileWeaponView." + operation, error);
        }
    }

    private static Map<String, DisplayHud> profileHuds(ServerPlayer p) {
        var result = new HashMap<String, DisplayHud>();
        DisplayHud.getHuds(p).forEach((id, hud) -> {
            if (id.startsWith(PREFIX)) result.put(id.substring(PREFIX.length()), hud);
        });
        return result;
    }

    private static Map<String, DisplayHud> completeView(GameTestHelper h, ServerPlayer p, ItemStack held) {
        var huds = profileHuds(p);
        check(h, huds.keySet().equals(PARTS), "Exactly gun, grenade and four arm HUDs must exist: " + huds.keySet());
        check(h, huds.values().stream().allMatch(ItemDisplayHud.class::isInstance), "All six parts are real item HUDs");
        var route = WeaponCombatItem.INSTANCE.getPolymerItemModel(held, null, p.level().registryAccess());
        check(h, route != null && ProfileArmAssets.graph(route) != null, "Current weapon profile graph is loaded");
        var shown = ((ItemDisplayHud) huds.get("gun")).getItem();
        check(h, ProfileArmAssets.view(route).equals(shown.get(DataComponents.ITEM_MODEL)),
                "Actual HUD selects current weapon view graph: " + route);
        check(h, ((ItemDisplayHud) huds.get("grenade")).getItem().isEmpty(), "Idle grenade display is empty");
        return huds;
    }

    private static void inventory(GameTestHelper h, ServerPlayer p, ItemStack held, ItemStack snapshot) {
        check(h, p.getMainHandItem() == held, "Real held stack identity is preserved");
        check(h, ItemStack.matches(held, snapshot), "Camera/HUD leaves real weapon contents unchanged");
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated", maxTicks = 40)
    public void rearCameraRemovesAllPartsImmediatelyAndRestoresCurrentWeapon(GameTestHelper h) {
        var p = player(h, Element.ARC);
        var original = weapon("ace_of_spades");
        p.setItemInHand(InteractionHand.MAIN_HAND, original);
        var originalSnapshot = original.copy();
        view(p, "update");
        var initial = completeView(h, p, original);
        var originalModel = ((ItemDisplayHud) initial.get("gun")).getItem().get(DataComponents.ITEM_MODEL);
        inventory(h, p, original, originalSnapshot);

        check(h, SuperCamera.startThirdPerson(p) && SuperCamera.active(p), "Rear camera takes ownership");
        check(h, p.getCamera() == p, "Packet-only rear camera leaves server camera equal to player");
        // No update between start and this assertion: a next-tick-only fix is insufficient.
        check(h, profileHuds(p).isEmpty(), "Camera start synchronously removes all six profile HUDs");
        inventory(h, p, original, originalSnapshot);
        // Keep this synchronous: a bare camera has no ability/animation keeping it alive on server ticks.
        for (int i = 0; i < 4; i++) {
            view(p, "update");
            check(h, SuperCamera.active(p) && p.getCamera() == p, "Fake rear camera still owns the player");
            check(h, profileHuds(p).isEmpty(), "Owned update " + i + " cannot recreate any profile HUD");
            inventory(h, p, original, originalSnapshot);
        }

        var current = weapon("blast_furnace");
        p.setItemInHand(InteractionHand.MAIN_HAND, current);
        var currentSnapshot = current.copy();
        view(p, "update");
        check(h, profileHuds(p).isEmpty(), "Changing held weapon during ownership cannot recreate the HUD");
        inventory(h, p, current, currentSnapshot);
        SuperCamera.stop(p);
        check(h, !SuperCamera.active(p) && p.getCamera() == p, "Camera released before first-person update");
        inventory(h, p, current, currentSnapshot);
        view(p, "update");
        var restored = completeView(h, p, current);
        var shown = ((ItemDisplayHud) restored.get("gun")).getItem();
        check(h, !originalModel.equals(shown.get(DataComponents.ITEM_MODEL)), "Restoration cannot reuse the old weapon graph");
        var flags = shown.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY).flags();
        check(h, !flags.isEmpty() && flags.getFirst(), "Restored pulse rifle uses the current two-handed grip selector");
        for (var part : PARTS) {
            check(h, restored.get(part) != initial.get(part), "Retired " + part + " HUD is replaced on recovery");
        }
        inventory(h, p, current, currentSnapshot);
        check(h, ItemStack.matches(original, originalSnapshot), "Retired real weapon was never rewritten");
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated", maxTicks = 40)
    public void goldenGunSolarNoOpKeepsExistingFirstPersonView(GameTestHelper h) {
        var p = player(h, Element.SOLAR);
        var held = weapon("ace_of_spades");
        p.setItemInHand(InteractionHand.MAIN_HAND, held);
        var snapshot = held.copy();
        view(p, "update");
        var initial = completeView(h, p, held);

        check(h, SuperCamera.start(p, Element.SOLAR), "Golden Gun Solar start accepts without a rear camera");
        check(h, !SuperCamera.active(p) && p.getCamera() == p, "Solar retains first-person ownership");
        for (int i = 0; i <= 4; i++) {
            // Iteration zero verifies that start itself did not remove/recreate the view.
            if (i > 0) view(p, "update");
            var current = completeView(h, p, held);
            for (var part : PARTS) {
                check(h, current.get(part) == initial.get(part), "Solar keeps the same " + part + " HUD at update " + i);
            }
            inventory(h, p, held, snapshot);
        }
        h.succeed();
    }
}
