package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;
import java.util.List;

/** Real server pose and Polymer snapshot transport, not native pixels or shoulder-contact proof. */
public final class WeaponCrouchW161GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static ServerPlayer player(GameTestHelper h, String name) {
        var p = TestPlayers.create(h, new Vec3(2, 2, 2), 0, 0, name);
        p.setNoGravity(true);
        p.setAttached(WeaponLoadout.ENABLED, false);
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); TestPlayers.remove(p); });
        return p;
    }
    private static ItemStack equip(ServerPlayer p, String id) {
        var gun = WeaponItems.create(WeaponCatalog.find(id).orElseThrow());
        p.getInventory().setItem(0, gun); p.getInventory().setSelectedSlot(0);
        return gun;
    }
    private static ItemStack wire(ServerPlayer recipient, ItemStack stack) {
        var context = ((PacketContextProvider)(Object)recipient.connection).getPacketContext();
        return PolymerItemUtils.getPolymerItemStack(stack, context, recipient.registryAccess());
    }
    private static boolean flag(ItemStack stack) {
        return Boolean.TRUE.equals(stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA,
                CustomModelData.EMPTY).getBoolean(1));
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=20)
    public void actualCrouchPoseNotSneakIntentDrivesCompensation(GameTestHelper h) {
        var p = player(h, "W161_pose"); var gun = equip(p, "ammit_ar2"); var before = gun.copy();
        p.setShiftKeyDown(true); p.setPose(Pose.STANDING); WeaponRuntime.tickPlayer(p);
        check(h, !flag(gun), "Sneak intent alone cannot claim the renderer's crouch pose");
        p.setShiftKeyDown(false); p.setPose(Pose.CROUCHING); WeaponRuntime.tickPlayer(p);
        check(h, flag(gun) && flag(wire(p, gun)), "Actual crouch also works without ADS/key intent");
        p.setPose(Pose.STANDING); WeaponRuntime.tickPlayer(p);
        check(h, !flag(gun) && !flag(wire(p, gun)), "Standing clears the transported compensation");
        var entry = WeaponItems.entry(gun).orElseThrow(); var profile = WeaponProfile.forEntry(entry);
        check(h, WeaponItems.magazine(gun, profile).rounds() == WeaponItems.magazine(before, profile).rounds()
                && !p.isUsingItem() && !WeaponRuntime.reloading(p) && p.getCamera() == p,
                "Cosmetic pose does not fire, spend ammo, reload, start use or replace camera");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=25)
    public void releaseClearsCrouchWhileActualAdsModelStillLingers(GameTestHelper h) {
        var p = player(h, "W161_release"); var gun = equip(p, "ammit_ar2");
        ads(p, true); p.setShiftKeyDown(true); p.setPose(Pose.CROUCHING); WeaponRuntime.tickPlayer(p);
        h.onEachTick(() -> WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(8, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, WeaponAiming.progress(p) > .5f && flag(gun), "Real server ticks raised ADS while crouching; progress="
                    + WeaponAiming.progress(p) + ", pose=" + p.getPose() + ", flag=" + flag(gun));
            ads(p, false); p.setShiftKeyDown(false); p.setPose(Pose.STANDING); WeaponRuntime.tickPlayer(p);
            var context = ((PacketContextProvider)(Object)p.connection).getPacketContext();
            var model = WeaponCombatItem.INSTANCE.getPolymerItemModel(gun, context, p.registryAccess());
            check(h, WeaponAiming.progress(p) > 0 && model.toString().equals("destiny:weapon_sight_w151/ammit_ar2")
                            && !flag(wire(p, gun)),
                    "Lingering actual ADS route selects standing correction flag, not stale crouch");
            h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=20)
    public void equipmentSnapshotsAndOtherRecipientsKeepPoseAndUnrelatedComponents(GameTestHelper h) {
        var owner = player(h, "W161_owner"); var observer = player(h, "W161_observer");
        var gun = equip(owner, "ammit_ar2");
        gun.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(.31f, -.4f, 8f),
                List.of(true, false, true, false), List.of("hip", "foreign"), List.of(0xABCDEF)));
        var before = gun.copy();
        owner.setPose(Pose.CROUCHING); WeaponCrouchPresentation.update(owner);
        var data = gun.get(DataComponents.CUSTOM_MODEL_DATA); var previous = before.get(DataComponents.CUSTOM_MODEL_DATA);
        check(h, data.floats().equals(previous.floats()) && data.strings().equals(previous.strings())
                        && data.colors().equals(previous.colors()) && data.flags().equals(List.of(true,true,true,false))
                        && gun.get(DataComponents.CUSTOM_DATA).equals(before.get(DataComponents.CUSTOM_DATA)),
                "Only reserved flag1 changes; ammo NBT/floats/pose/colour/grip/higher flags stay unchanged");
        for (var recipient : List.of(owner, observer)) for (var source : List.of(gun, gun.copy())) {
            var encoded = wire(recipient, source);
            check(h, encoded.is(Items.CROSSBOW) && flag(encoded)
                            && Boolean.TRUE.equals(encoded.get(DataComponents.CUSTOM_MODEL_DATA).getBoolean(0)),
                    "Source and copied equipment both carry the owner's crouch, not the recipient's pose");
            var context = ((PacketContextProvider)(Object)recipient.connection).getPacketContext();
            check(h, ItemStack.matches(source, PolymerItemUtils.getRealItemStack(encoded, context, recipient.registryAccess())),
                    "Cosmetic client flags do not break Polymer's real-item roundtrip");
        }
        WeaponCrouchPresentation.cleanup(owner); WeaponCrouchPresentation.cleanup(owner);
        check(h, ItemStack.matches(before, gun), "Cleanup preserves every unrelated component and prior neutral flag1");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=20)
    public void stowAndExactObjectHandoffDoNotLeaveOrStealThePose(GameTestHelper h) {
        var a = player(h, "W161_donor"); var b = player(h, "W161_receiver"); var gun = equip(a, "ammit_ar2");
        a.setPose(Pose.CROUCHING); WeaponCrouchPresentation.update(a);
        a.getInventory().setItem(0, ItemStack.EMPTY); WeaponCrouchPresentation.update(a);
        check(h, !flag(gun), "Stowing retires the old stack even when its owner stays crouched");
        a.getInventory().setItem(0, gun); WeaponCrouchPresentation.update(a);
        a.getInventory().setItem(0, ItemStack.EMPTY); // Receiver observes this transfer before donor's next tick.
        b.getInventory().setItem(0, gun); b.setPose(Pose.CROUCHING); WeaponCrouchPresentation.update(b);
        WeaponCrouchPresentation.cleanup(a);
        check(h, flag(gun), "Late donor cleanup never neutralizes the new owner's binding");
        b.setPose(Pose.STANDING); WeaponCrouchPresentation.update(b);
        check(h, !flag(gun), "Exact-object recipient's actual standing pose replaces donor pose");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=20)
    public void nativeGripOtherGunsPreviewAndSpectatorKeepTheirExistingBehavior(GameTestHelper h) {
        var p = player(h, "W161_guards"); p.setPose(Pose.CROUCHING);
        var ammit = equip(p, "ammit_ar2"); WeaponCrouchPresentation.update(p); check(h, flag(ammit), "Positive setup");
        p.setGameMode(GameType.SPECTATOR); WeaponRuntime.tickPlayer(p);
        check(h, !flag(ammit), "Spectator lifecycle retires the cosmetic pose"); p.setGameMode(GameType.SURVIVAL);
        for (String id : List.of("ace_of_spades", "blast_furnace", "the_recluse")) {
            var gun = equip(p, id); var before = gun.copy(); WeaponCrouchPresentation.update(p);
            check(h, ItemStack.matches(before, gun) && wire(p,gun).get(DataComponents.CUSTOM_MODEL_DATA).flags().size()==1,
                    "Unrelated weapon transport retains exactly the pre-existing grip flag");
        }
        var nativeAmmit = WeaponModels.withGrip(WeaponItems.create(WeaponCatalog.find("ammit_ar2").orElseThrow()),
                WeaponModels.Grip.NATIVE).orElseThrow();
        p.getInventory().setItem(0, nativeAmmit); var beforeNative = nativeAmmit.copy(); WeaponCrouchPresentation.update(p);
        check(h, ItemStack.matches(beforeNative, nativeAmmit) && wire(p,nativeAmmit).is(Items.STICK)
                && !flag(wire(p,nativeAmmit)), "Native Ammit remains unchanged");
        var preview = WeaponModels.create(WeaponCatalog.find("ammit_ar2").orElseThrow());
        p.getInventory().setItem(0, preview); var beforePreview = preview.copy(); WeaponCrouchPresentation.update(p);
        check(h, ItemStack.matches(beforePreview, preview) && !flag(wire(p,preview)), "Inert previews do not gain live pose state");
        var dying = equip(p, "ammit_ar2"); p.setPose(Pose.CROUCHING); WeaponCrouchPresentation.update(p);
        check(h, flag(dying), "Positive pose before death cleanup");
        p.setHealth(0); WeaponRuntime.tickPlayer(p);
        check(h, !flag(dying), "Dead owners cannot retain the transient crouch selector");
        h.succeed();
    }
}
