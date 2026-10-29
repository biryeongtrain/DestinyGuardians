package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.*;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.*;
import net.minecraft.world.phys.Vec3;

/** Actual vanilla packet/command/inventory/ability paths. No native rendering or input claim. */
public final class WeaponHandlingW58GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static void check(GameTestHelper h, boolean value, String message) { h.assertTrue(value, Component.literal(message)); }
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2, 1, 6), -90, 0);
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); AbilityService.cleanup(p); TestPlayers.remove(p); });
        return p;
    }
    private static ItemStack item(String id, int rounds, int reserve) {
        var e = WeaponCatalog.find(id).orElseThrow(); var s = WeaponItems.create(e);
        WeaponItems.save(s, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, reserve)); return s;
    }
    private static WeaponMagazine ammo(ItemStack s) {
        return WeaponItems.magazine(s, WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow()));
    }
    private static int ready(ItemStack s) { var p = WeaponHandlingProfile.of(WeaponItems.entry(s).orElseThrow()); return p.supported() ? p.readyTicks() : 0; }
    private static int stow(ItemStack s) { var p = WeaponHandlingProfile.of(WeaponItems.entry(s).orElseThrow()); return p.supported() ? p.stowTicks() : 0; }
    private static void initial(ServerPlayer p, ItemStack a, ItemStack b) {
        p.getInventory().setItem(0, a); p.getInventory().setItem(1, b); p.getInventory().setSelectedSlot(0);
        WeaponRuntime.tickPlayer(p);
    }
    private static void select(ServerPlayer p, int slot) { p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot)); }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void nativeSelectionPaysOutgoingStowIncomingReadyAndUpdatesActualHud(GameTestHelper h) {
        var p = player(h); var a = item("austringer", 5, 0); var b = item("beloved", 2, 5); initial(p, a, b);
        select(p, 1); int duration = stow(a) + ready(b);
        check(h, WeaponHandling.remaining(p) == duration, "Exact two weapon timing sum from validated vanilla slot mutation");
        check(h, !WeaponRuntime.beginUse(p) && !WeaponRuntime.heartbeatUse(p) && !WeaponRuntime.reload(p), "No early trigger/charge/reload");
        ads(p, true); WeaponRuntime.tickPlayer(p); CombatHud.update(p);
        check(h, WeaponAiming.progress(p) == 0 && !WeaponRuntime.reloading(p), "No ADS or fake reload while drawing");
        check(h, AmmoHud.current(p).orElseThrow().rounds() == 2 && AmmoHud.current(p).orElseThrow().reserve() == 5, "Real selected ammo HUD remains visible");
        ads(p, false);
        h.runAfterDelay(duration - 1, () -> check(h, !WeaponRuntime.beginUse(p) && ammo(b).rounds() == 2, "No early shot one tick before ready"));
        h.runAfterDelay(duration, () -> {
            check(h, !WeaponHandling.blocked(p) && WeaponRuntime.beginUse(p), "Fires exactly at ready deadline");
            check(h, ammo(b).rounds() == 1 && ammo(b).reserve() == 5 && ammo(a).rounds() == 5, "Only new actual stack paid"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 90, environment = "destiny-test:w90_isolated")
    public void sameTickAwayBackCancelsReloadAndCannotResetDeadline(GameTestHelper h) {
        var p = player(h); var a = item("beloved", 1, 10); var b = item("austringer", 5, 0); initial(p, a, b);
        check(h, WeaponRuntime.reload(p), "Real timed reload started");
        select(p, 1); select(p, 0); int duration = stow(a) + ready(a);
        check(h, WeaponHandling.remaining(p) == duration && !WeaponRuntime.reloading(p), "One retained stow plus latest target ready; old reload cancelled");
        check(h, !WeaponRuntime.beginUse(p), "Away-back is not an instant gun ready exploit");
        h.runAfterDelay(65, () -> {
            WeaponRuntime.tickPlayer(p); check(h, ammo(a).rounds() == 1 && ammo(a).reserve() == 10, "Old delayed reload never grants ammo"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void pendingPulseBurstAndHeldAutomaticInputDoNotBecomeLatentShotsAfterSwap(GameTestHelper h) {
        var p = player(h); var a = item("bygones", 10, 0); var b = item("gnawing_hunger", 10, 0); initial(p, a, b);
        check(h, WeaponRuntime.beginUse(p) && ammo(a).rounds() == 9, "First real pulse bullet paid");
        select(p, 1); check(h, !WeaponRuntime.heartbeatUse(p), "No buffered held pulse during switch");
        h.runAfterDelay(45, () -> {
            WeaponRuntime.tickPlayer(p); check(h, ammo(a).rounds() == 9 && ammo(b).rounds() == 10, "Cancelled old burst and no input means no new automatic shot");
            check(h, WeaponRuntime.heartbeatUse(p) && ammo(b).rounds() == 9, "Fresh actual input after ready works"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void drawnBowSwitchLetsDownWithoutSpawningArrow(GameTestHelper h) {
        var p = player(h); var a = item("biting_winds", 1, 0); var b = item("austringer", 5, 0); initial(p, a, b);
        check(h, WeaponRuntime.beginUse(p), "Real bow draw accepted"); p.startUsingItem(InteractionHand.MAIN_HAND);
        select(p, 1);
        check(h, !p.isUsingItem() && ammo(a).rounds() == 1 && WeaponRuntime.activeProjectiles(p) == 0, "Native stop-use callback cannot release an armed arrow");
        h.runAfterDelay(40, () -> { WeaponRuntime.tickPlayer(p); check(h, WeaponRuntime.activeProjectiles(p) == 0 && ammo(b).rounds() == 5, "No latent projectile"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void commandSelectionAndNoopHaveSameTimingAsNativeMutation(GameTestHelper h) {
        var p = player(h); var a = item("austringer", 5, 0); var b = item("beloved", 2, 5); initial(p, a, b);
        p.setAttached(WeaponLoadout.ENABLED, true);
        check(h, WeaponLoadout.select(p, WeaponSlot.ENERGY), "Real command selection accepted");
        long remaining = WeaponHandling.remaining(p);
        check(h, remaining == stow(a) + ready(b), "Command not an instant-switch bypass");
        check(h, WeaponLoadout.select(p, WeaponSlot.ENERGY) && WeaponHandling.remaining(p) == remaining, "No-op never restarts animation");
        WeaponRuntime.selectedSlotChanging(p, -1); WeaponRuntime.selectedSlotChanging(p, 9);
        check(h, WeaponHandling.remaining(p) == remaining, "Invalid slots cannot alter state"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void inventoryReplacementIsIdentityBasedAndNotAFreeEquip(GameTestHelper h) {
        var p = player(h); var a = item("austringer", 5, 0); initial(p, a, ItemStack.EMPTY);
        var replacement = a.copy(); p.getInventory().setItem(0, replacement);
        check(h, !WeaponRuntime.beginUse(p), "Equal components with different actual stack reference is a real replacement");
        check(h, WeaponHandling.remaining(p) == stow(a) + ready(replacement), "Poll/input replacement same timing path");
        check(h, ammo(a).rounds() == 5 && ammo(replacement).rounds() == 5, "No copy mutation or ammo duplication"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void buildingAndPreviewDetoursCannotBypassReadyingButAreNotBlocked(GameTestHelper h) {
        var p = player(h); var a = item("austringer", 5, 0); initial(p, a, new ItemStack(Items.STONE));
        p.getInventory().setItem(2, WeaponModels.create(WeaponCatalog.find("beloved").orElseThrow()));
        select(p, 1); check(h, !WeaponHandling.blocked(p), "Ordinary building remains usable");
        select(p, 2); check(h, !WeaponHandling.blocked(p), "Preview has no combat timing/shot state");
        select(p, 0); check(h, WeaponHandling.remaining(p) == stow(a) + ready(a), "Same-tick detours cannot erase outgoing stow");
        check(h, !WeaponRuntime.beginUse(p) && ammo(a).rounds() == 5, "No ammo mutation during transition"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void swordUnknownHandlingDoesNotInventTimingButKnownOutgoingStowStillApplies(GameTestHelper h) {
        var p = player(h); var a = item("austringer", 5, 0); var sword = item("abide_the_return", 10, 0); initial(p, a, sword);
        select(p, 1); int delay = stow(a);
        check(h, WeaponHandling.remaining(p) == delay && WeaponRuntime.onPunch(p), "Known gun stow paid; sword input consumed but not yet attacking");
        check(h, ammo(sword).rounds() == 10, "Sword not paid before outgoing gun is stowed");
        h.runAfterDelay(delay, () -> {
            WeaponRuntime.onPunch(p); check(h, ammo(sword).rounds() == 9, "Sword can attack with no invented ready curve");
            select(p, 0); check(h, WeaponHandling.remaining(p) == ready(a), "Known incoming ready even when sword stow unknown"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void skillCancelAndMarksmanInstantReloadCannotEraseTheSwitchClock(GameTestHelper h) {
        var p = player(h); Guardians.data(p).setGuardianClass(GuardianClass.HUNTER);
        Guardians.data(p).setLoadout(GuardianClass.HUNTER, kim.biryeong.destiny.ability.hunter.HunterAbilities.preset(Element.SOLAR));
        var a = item("austringer", 1, 0); var b = item("beloved", 1, 10); initial(p, a, b); p.setAttached(WeaponLoadout.ENABLED, true);
        select(p, 1); long remaining = WeaponHandling.remaining(p); WeaponRuntime.cancelUseForSkill(p);
        check(h, WeaponHandling.remaining(p) == remaining, "Skill cancel is not timing reset");
        check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.OK, "Real class ability still usable during draw");
        check(h, ammo(b).rounds() == WeaponProfile.forEntry(WeaponItems.entry(b).orElseThrow()).magazine(), "W57 instant paid reload still works");
        check(h, WeaponHandling.remaining(p) == remaining && !WeaponRuntime.beginUse(p), "Instant reload does not instantly ready weapon or create buffered shot"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void waitingDoesNotCreateInputAndOwnerClocksAreIndependent(GameTestHelper h) {
        var p = player(h); var other = player(h);
        var a = item("austringer", 5, 0); var b = item("beloved", 2, 5); initial(p, a, b);
        var otherGun = item("austringer", 5, 0); initial(other, otherGun, ItemStack.EMPTY);
        select(p, 1); check(h, WeaponRuntime.beginUse(other) && ammo(otherGun).rounds() == 4, "One player's draw never blocks another");
        h.runAfterDelay(stow(a) + ready(b) + 1, () -> {
            WeaponRuntime.tickPlayer(p); check(h, !WeaponHandling.blocked(p) && ammo(b).rounds() == 2, "Expiration alone never fires/reloads");
            WeaponRuntime.cleanup(p); check(h, WeaponHandling.remaining(p) == 0, "Lifecycle cleanup releases transient clock"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void crouchHeldDuringDrawStartsAdsOnlyAfterReadyAndOldScopeIsCleared(GameTestHelper h) {
        var p = player(h); var a = item("beloved", 2, 5); var b = item("austringer", 5, 0); initial(p, a, b);
        ads(p, true);
        int oldAds = WeaponAimProfile.of(WeaponItems.entry(a).orElseThrow()).transitionTicks();
        int switchAt = oldAds + 1, duration = stow(a) + ready(b), readyAt = switchAt + duration;
        check(h, duration >= 3 && readyAt + 1 < 80, "Authored handling and click debounce fit the test bound");
        // Register every callback before GameTestInfo starts iterating its scheduled-callback map.
        for (int i = 1; i <= oldAds; i++) h.runAfterDelay(i, () -> WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(switchAt, () -> {
            check(h, WeaponAiming.scoped(p), "Old weapon actually entered its scoped server state");
            select(p, 1); WeaponRuntime.tickPlayer(p);
            check(h, WeaponHandling.remaining(p) == duration, "Actual selection captures authored stow plus ready deadline");
            ads(p,true); check(h,!WeaponAiming.requested(p),"Click during handling is consumed without queueing ADS");
            check(h, !WeaponScopes.scoped(a) && WeaponAiming.progress(p) == 0, "Old scope restored and new weapon cannot aim while stowing");
        });
        for (int i = switchAt + 1; i < readyAt; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                WeaponRuntime.tickPlayer(p);
                check(h, WeaponHandling.remaining(p) == readyAt - elapsed && WeaponAiming.progress(p) == 0
                                && !WeaponAiming.requested(p), "Original deadline stays blocked with no queued ADS input");
            });
        }
        h.runAfterDelay(readyAt, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, !WeaponHandling.blocked(p) && WeaponAiming.progress(p) == 0 && !WeaponAiming.requested(p),
                    "Draw completion never resurrects the consumed ADS click");
            ads(p,true);
            check(h,WeaponAiming.requested(p),"New click at the real ready deadline is accepted");
            check(h, ammo(a).rounds() == 2 && ammo(b).rounds() == 5, "Aiming never creates an implicit shot");
        });
        h.runAfterDelay(readyAt + 1, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h,WeaponAiming.progress(p)>0,"Fresh accepted click advances on the next real tick");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void acceptedProjectileIsNotDeletedByWeaponSwitch(GameTestHelper h) {
        var p = player(h); var rocket = item("bad_omens", 1, 3); var gun = item("austringer", 5, 0); initial(p, rocket, gun);
        check(h, WeaponRuntime.beginUse(p) && WeaponRuntime.activeProjectiles(p) == 1 && ammo(rocket).rounds() == 0,
                "A real paid projectile was accepted before switching");
        select(p, 1);
        check(h, WeaponRuntime.activeProjectiles(p) == 1 && ammo(rocket).rounds() == 0,
                "Only pending input is cancelled; an already launched projectile is neither erased nor refunded");
        check(h, !WeaponRuntime.beginUse(p) && ammo(gun).rounds() == 5, "Incoming ready gate is still enforced"); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void firstObservationIsAlreadyEquippedButBuildingToGunPaysIncomingReady(GameTestHelper h) {
        var p = player(h); var gun = item("austringer", 5, 0);
        p.getInventory().setItem(0, new ItemStack(Items.STONE)); p.getInventory().setItem(1, gun);
        p.getInventory().setSelectedSlot(0); WeaponRuntime.tickPlayer(p);
        select(p, 1);
        check(h, WeaponHandling.remaining(p) == ready(gun), "No invented building stow duration, but actual gun has ready time");
        check(h, !WeaponRuntime.beginUse(p), "Building-to-gun is not an instant equip bypass");
        h.runAfterDelay(ready(gun), () -> {
            check(h, WeaponRuntime.beginUse(p) && ammo(gun).rounds() == 4, "Actual trigger works at incoming-ready boundary"); h.succeed();
        });
    }
}
