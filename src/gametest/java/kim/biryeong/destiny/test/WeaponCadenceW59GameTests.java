package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** Actual paid shots, native slot mutations, and paid dodge reload. No native-client proof. */
public final class WeaponCadenceW59GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static void check(GameTestHelper h, boolean ok, String text) { h.assertTrue(ok, Component.literal(text)); }
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2, 1, 6), -90, 0);
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); AbilityService.cleanup(p); TestPlayers.remove(p); }); return p;
    }
    private static ItemStack item(String id, int rounds, int reserve) {
        var e = WeaponCatalog.find(id).orElseThrow(); var s = WeaponItems.create(e);
        WeaponItems.save(s, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, reserve)); return s;
    }
    private static WeaponMagazine ammo(ItemStack s) { return WeaponItems.magazine(s, WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow())); }
    private static void slots(ServerPlayer p, ItemStack a, ItemStack b) {
        p.getInventory().setItem(0, a); p.getInventory().setItem(1, b); p.getInventory().setSelectedSlot(0); WeaponRuntime.tickPlayer(p);
    }
    private static void select(ServerPlayer p, int slot) { p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot)); }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void rocketRpmDoesNotDelayAReadiedHandCannon(GameTestHelper h) {
        var p = player(h); var rocket = item("bad_omens", 1, 3); var gun = item("austringer", 5, 0); slots(p, rocket, gun);
        check(h, WeaponRuntime.beginUse(p) && ammo(rocket).rounds() == 0, "Real rocket paid its first shot"); select(p, 1);
        int delay = (int)WeaponHandling.remaining(p);
        check(h, delay < WeaponProfile.forEntry(WeaponItems.entry(rocket).orElseThrow()).cadenceTicks(), "New ready finishes before old rocket cadence");
        check(h, !WeaponRuntime.beginUse(p), "Independent RPM does not bypass Handling");
        h.runAfterDelay(delay, () -> {
            check(h, WeaponRuntime.beginUse(p) && ammo(gun).rounds() == 4, "New gun fires at its ready boundary, not old rocket's 48-tick deadline");
            check(h, ammo(rocket).rounds() == 0 && ammo(rocket).reserve() == 3, "No implicit stowed reload/refund"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 90, environment = "destiny-test:w90_isolated")
    public void returningToOriginalRocketKeepsItsDeadlineEvenAfterMarksmanReload(GameTestHelper h) {
        var p = player(h); var rocket = item("bad_omens", 1, 3); var gun = item("austringer", 5, 0); slots(p, rocket, gun);
        int originalDeadline = (int)Math.ceil(WeaponProfile.forEntry(WeaponItems.entry(rocket).orElseThrow()).cadenceTicks());
        check(h, WeaponRuntime.beginUse(p), "Original rocket shot accepted"); select(p, 1);
        int firstReady = (int)WeaponHandling.remaining(p);
        h.runAfterDelay(firstReady, () -> {
            check(h, WeaponRuntime.beginUse(p) && ammo(gun).rounds() == 4, "Other gun independently fired"); select(p, 0);
            int backReady = (int)WeaponHandling.remaining(p);
            check(h, firstReady + backReady < originalDeadline, "Return ready occurs while original projectile weapon still recovers");
            h.runAfterDelay(backReady, () -> {
                check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.OK, "Real Marksman reload activation");
                check(h, ammo(rocket).rounds() == 1 && ammo(rocket).reserve() == 2, "Actual finite reserve paid the reload");
                check(h, !WeaponRuntime.beginUse(p), "Reload and distinct-gun shot cannot reset original item clock");
            });
        });
        h.runAfterDelay(originalDeadline - 1, () -> check(h, !WeaponRuntime.beginUse(p) && ammo(rocket).rounds() == 1, "No early shot at original deadline minus one"));
        h.runAfterDelay(originalDeadline, () -> {
            check(h, WeaponRuntime.beginUse(p) && ammo(rocket).rounds() == 0 && ammo(rocket).reserve() == 2, "Same original stack fires exactly when its own recovery ends"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void sameCatalogDifferentActualStackHasItsOwnCadence(GameTestHelper h) {
        var p = player(h); var first = item("bad_omens", 1, 0); var second = item("bad_omens", 1, 0); slots(p, first, second);
        check(h, WeaponRuntime.beginUse(p), "First actual rocket fired"); select(p, 1); int delay = (int)WeaponHandling.remaining(p);
        h.runAfterDelay(delay, () -> {
            check(h, WeaponRuntime.beginUse(p) && ammo(second).rounds() == 0 && ammo(first).rounds() == 0,
                    "Clock belongs to actual stack, not family/id or all owner weapons"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void realReadyThenEmptyTriggerStartsNewWeaponReloadWithoutWaitingForOldRpm(GameTestHelper h) {
        var p = player(h); var rocket = item("bad_omens", 1, 3); var sniper = item("beloved", 0, 4); slots(p, rocket, sniper);
        WeaponRuntime.beginUse(p); select(p, 1); int delay = (int)WeaponHandling.remaining(p);
        h.runAfterDelay(delay, () -> {
            check(h, !WeaponRuntime.beginUse(p) && WeaponRuntime.reloading(p), "Empty new weapon trigger starts its actual reload once ready");
            check(h, ammo(sniper).rounds() == 0 && ammo(sniper).reserve() == 4, "Reload still has no early reserve transfer"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void skillAndNoopSelectionNeverResetSameItemRpm(GameTestHelper h) {
        var p = player(h); var rocket = item("bad_omens", 1, 3); slots(p, rocket, ItemStack.EMPTY);
        WeaponRuntime.beginUse(p);
        WeaponRuntime.cancelUseForSkill(p); select(p, 0);
        check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.OK, "Actual paid instant reload");
        check(h, ammo(rocket).rounds() == 1 && ammo(rocket).reserve() == 2 && !WeaponRuntime.beginUse(p), "Skill cancellation plus no-op do not clear firing recovery");
        h.runAfterDelay(47, () -> check(h, !WeaponRuntime.beginUse(p), "Original same-item cadence still active"));
        h.runAfterDelay(48, () -> { check(h, WeaponRuntime.beginUse(p) && ammo(rocket).rounds() == 0, "Original cadence expires normally"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void anotherOwnerAndSharedCleanupDoNotInheritWeaponClocksOrGrantAmmo(GameTestHelper h) {
        var p = player(h); var other = player(h); var a = item("bad_omens", 1, 0); var b = item("bad_omens", 1, 3);
        slots(p, a, ItemStack.EMPTY); slots(other, b, ItemStack.EMPTY);
        check(h, WeaponRuntime.beginUse(p) && WeaponRuntime.beginUse(other), "Identical catalog across owners has no shared RPM lockout");
        WeaponRuntime.cleanup(p);
        check(h, ammo(a).rounds() == 0 && ammo(b).rounds() == 0, "Lifecycle teardown cannot refund either shot");
        check(h, AbilityService.use(other, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.OK, "Other owner actually cancels hold and pays reserve to reload");
        check(h, ammo(b).rounds() == 1 && ammo(b).reserve() == 2 && !WeaponRuntime.beginUse(other),
                "One owner cleanup does not reset the other's loaded weapon recovery"); h.succeed();
    }
}
