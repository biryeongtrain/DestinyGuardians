package kim.biryeong.destiny.test;

import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.WeaponAccessibility;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponCombatItem;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponMagazine;
import kim.biryeong.destiny.weapon.WeaponModels;
import kim.biryeong.destiny.weapon.WeaponProfile;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** W49 server integration only; these simulated callbacks are not native-client evidence. */
public final class WeaponEmptyReloadW49GameTests {
    private record Weapon(ServerPlayer player, ItemStack stack, WeaponProfile profile, WeaponModels.Grip grip) {
        private WeaponMagazine ammo() { return WeaponItems.magazine(stack, profile); }
        private String label() { return WeaponItems.entry(stack).orElseThrow().id() + " / " + grip; }
    }

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static Weapon equip(GameTestHelper h, String id, WeaponModels.Grip grip, int rounds, int reserve) {
        var player = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), -90, 0);
        // Exercise the weapon base trigger policy independently of the default-on accessibility option.
        WeaponAccessibility.setEnabled(player, false);
        TestCleanup.register(h, () -> {
            WeaponRuntime.cleanup(player);
            CombatHud.remove(player);
            TestPlayers.remove(player);
        });
        var entry = WeaponCatalog.find(id).orElseThrow();
        var profile = WeaponProfile.forEntry(entry);
        var stack = WeaponModels.withGrip(WeaponItems.create(entry), grip).orElseThrow();
        WeaponItems.save(stack, new WeaponMagazine(profile, rounds, reserve));
        player.setItemInHand(InteractionHand.MAIN_HAND, stack);
        check(h, WeaponModels.twoHanded(stack) == (grip == WeaponModels.Grip.TWO_HAND),
                "Explicit input protocol: " + id + " / " + grip);
        check(h, !profile.infiniteReserve() && stack.is(WeaponCombatItem.INSTANCE),
                "Live finite-ammo fixture: " + id);
        check(h, WeaponItems.magazine(stack, profile).rounds() == rounds
                        && WeaponItems.magazine(stack, profile).reserve() == reserve,
                "Fixture ammo is not silently clamped: " + id);
        return new Weapon(player, stack, profile, grip);
    }

    private static WeaponProfile profile(String id) {
        return WeaponProfile.forEntry(WeaponCatalog.find(id).orElseThrow());
    }

    private static void use(GameTestHelper h, Weapon weapon) {
        WeaponCombatItem.INSTANCE.use(h.getLevel(), weapon.player(), InteractionHand.MAIN_HAND);
    }

    private static void nativeTick(GameTestHelper h, Weapon weapon, int tick) {
        WeaponCombatItem.INSTANCE.onUseTick(h.getLevel(), weapon.player(), weapon.stack(), 72000 - tick);
    }

    private static void heldTick(GameTestHelper h, Weapon weapon, int tick) {
        if (weapon.grip() == WeaponModels.Grip.NATIVE) {
            check(h, weapon.player().isUsingItem(), "Real native use state remains held: " + weapon.label());
            nativeTick(h, weapon, tick);
        } else if (tick % 4 == 0) {
            use(h, weapon);
        }
        WeaponRuntime.tickPlayer(weapon.player());
    }

    private static void release(Weapon weapon) {
        if (weapon.grip() == WeaponModels.Grip.NATIVE) {
            weapon.player().releaseUsingItem();
        }
        // Two-hand release is represented by ceasing heartbeat packets, not a native release.
    }

    private static void quietTick(GameTestHelper h, Weapon weapon, int tick) {
        WeaponRuntime.tickPlayer(weapon.player());
        if (weapon.grip() == WeaponModels.Grip.NATIVE) nativeTick(h, weapon, tick);
        WeaponRuntime.tickPlayer(weapon.player());
        TestPlayers.drain(weapon.player());
    }

    private static void bounded(GameTestHelper h, Weapon weapon, long maximumTotal) {
        var ammo = weapon.ammo();
        check(h, ammo.rounds() >= 0 && ammo.rounds() <= weapon.profile().magazine()
                        && ammo.reserve() >= 0 && ammo.reserve() <= weapon.profile().reserve()
                        && ammo.overflow() == 0 && ammo.total() <= maximumTotal,
                "Finite item-owned ammo remains bounded: " + weapon.label());
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 240, environment = "destiny-test:w90_isolated")
    public void belovedLastBulletReloadsAfterReleaseWithoutFurtherInputAndConservesFiniteReserve(GameTestHelper h) {
        var weapon = equip(h, "beloved", WeaponModels.Grip.NATIVE, 1, 7);
        var p = weapon.profile();
        check(h, !p.automatic() && !p.shellReload() && p.magazine() < 7,
                "Whole-magazine semiauto has more reserve than one reload can transfer");
        use(h, weapon);
        check(h, weapon.ammo().rounds() == 0 && weapon.ammo().reserve() == 7,
                "Successful last shot spends only its loaded bullet");
        release(weapon);
        boolean[] sawReload = {WeaponRuntime.reloading(weapon.player())};
        int finish = 2 * p.reloadTicks() + 24;
        for (int delay = 1; delay <= finish; delay++) {
            int tick = delay;
            h.runAfterDelay(delay, () -> {
                // No item-use callback or renewed input is needed to start or finish the reload.
                WeaponRuntime.tickPlayer(weapon.player());
                sawReload[0] |= WeaponRuntime.reloading(weapon.player());
                check(h, weapon.ammo().total() == 7, "Reload transfers ammo without another shot or free grant");
                bounded(h, weapon, 7);
                TestPlayers.drain(weapon.player());
                if (tick == finish) {
                    check(h, sawReload[0] && !WeaponRuntime.reloading(weapon.player()),
                            "Shot-caused reload starts and completes with released input");
                    check(h, weapon.ammo().rounds() == p.magazine()
                                    && weapon.ammo().reserve() == 7 - p.magazine(),
                            "Transfer is capped by magazine space and preserves excess finite reserve");
                    h.succeed();
                }
            });
        }
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 240, environment = "destiny-test:w90_isolated")
    public void heldSemiautoCannotFireReloadedMagazineUntilFreshInputInEitherGrip(GameTestHelper h) {
        var weapons = new Weapon[] {
                equip(h, "beloved", WeaponModels.Grip.NATIVE, 1, 3),
                equip(h, "beloved", WeaponModels.Grip.TWO_HAND, 1, 3)
        };
        for (var weapon : weapons) use(h, weapon);
        int heldUntil = 2 * weapons[0].profile().reloadTicks() + 12;
        int freshAt = heldUntil + WeaponRuntime.HEARTBEAT_LEASE_TICKS + 3;
        for (int delay = 1; delay <= freshAt; delay++) {
            int tick = delay;
            h.runAfterDelay(delay, () -> {
                for (var weapon : weapons) {
                    // Semiauto reload may stop native consumption. A stale continuation must
                    // still never substitute for a new native press; crossbow packets stay held.
                    if (tick <= heldUntil) {
                        if (weapon.grip() == WeaponModels.Grip.NATIVE) nativeTick(h, weapon, tick);
                        else if (tick % 4 == 0) use(h, weapon);
                        WeaponRuntime.tickPlayer(weapon.player());
                    } else quietTick(h, weapon, tick);
                    check(h, weapon.ammo().total() == 3,
                            "Held semiauto never spends the reloaded ammo: " + weapon.label());
                    if (tick == heldUntil) {
                        check(h, weapon.ammo().rounds() == 3 && !WeaponRuntime.reloading(weapon.player()),
                                "Loaded ammo remains available throughout the held-input quiet window");
                        release(weapon);
                    }
                    if (tick == freshAt) {
                        use(h, weapon);
                        check(h, weapon.ammo().rounds() == 2 && weapon.ammo().reserve() == 0,
                                "A fresh press fires exactly one loaded round: " + weapon.label());
                        use(h, weapon);
                        check(h, weapon.ammo().rounds() == 2, "Duplicate press cannot add a same-tick shot");
                    }
                    TestPlayers.drain(weapon.player());
                }
                if (tick == freshAt) h.succeed();
            });
        }
    }

    private static Husk target(GameTestHelper h) {
        var target = h.spawn(EntityTypes.HUSK, new Vec3(7.5, 1.8, 6.5));
        target.setNoAi(true);
        target.setNoGravity(true);
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
        target.getAttribute(Attributes.ARMOR).setBaseValue(0);
        target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        target.setHealth(1000);
        TestCleanup.register(h, target::discard);
        return target;
    }

    private static void hits(GameTestHelper h, Husk target, Weapon weapon, int count, String message) {
        check(h, Math.abs((1000 - target.getHealth()) - count * weapon.profile().damage()) < .01,
                message);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 240, environment = "destiny-test:w90_isolated")
    public void stormchaserLastSharedRoundDeliversThreeBoltsBeforeAutomaticReloadStarts(GameTestHelper h) {
        var weapon = equip(h, "stormchaser", WeaponModels.Grip.TWO_HAND, 1, 2);
        var target = target(h);
        var p = weapon.profile();
        check(h, p.sharedBurstAmmo() && p.burst() == 3 && !p.automatic() && !p.shellReload(),
                "One shared-ammo charge owns three queued bolts and a whole-magazine reload");
        use(h, weapon);
        boolean[] spent = {false};
        boolean[] sawReload = {false};
        int finish = p.chargeTicks() + (int) Math.ceil(2 * p.burstSpacingTicks()) + 2 * p.reloadTicks() + 24;
        for (int delay = 1; delay <= finish; delay++) {
            int tick = delay;
            h.runAfterDelay(delay, () -> {
                if (!spent[0]) heldTick(h, weapon, tick);
                else WeaponRuntime.tickPlayer(weapon.player());
                spent[0] |= weapon.ammo().total() == 2;
                if (WeaponRuntime.reloading(weapon.player())) {
                    sawReload[0] = true;
                    hits(h, target, weapon, 3, "All three real body hits precede the first reload timer");
                    check(h, weapon.ammo().rounds() == 0 && weapon.ammo().reserve() == 2,
                            "No reload transfer while queued bolts or the reload deadline remain");
                }
                check(h, weapon.ammo().total() == (spent[0] ? 2 : 3),
                        "Shared burst spends exactly one unit and reload conserves the remaining two");
                bounded(h, weapon, 3);
                TestPlayers.drain(weapon.player());
                if (tick == finish) {
                    check(h, spent[0] && sawReload[0] && !WeaponRuntime.reloading(weapon.player()),
                            "Released shared burst finishes, then reloads without another press");
                    hits(h, target, weapon, 3, "No missing queued bolt or latent fourth bolt after reload");
                    check(h, weapon.ammo().rounds() == 2 && weapon.ammo().reserve() == 0,
                            "Only the two real reserve units transfer");
                    h.succeed();
                }
            });
        }
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 240, environment = "destiny-test:w90_isolated")
    public void automaticTraceResumesOnlyWithMaintainedNativeUseOrRenewedHeartbeat(GameTestHelper h) {
        var p = profile("retraced_path");
        int reserve = p.magazine() + 11;
        var weapons = new Weapon[] {
                equip(h, "retraced_path", WeaponModels.Grip.NATIVE, 1, reserve),
                equip(h, "retraced_path", WeaponModels.Grip.TWO_HAND, 1, reserve)
        };
        check(h, p.automatic() && !p.shellReload(), "Whole-magazine automatic trace fixture");
        boolean[] sawReload = new boolean[2];
        int[] releasedAt = {-1, -1};
        int[] quietRounds = {-1, -1};
        for (int index = 0; index < weapons.length; index++) {
            use(h, weapons[index]);
            check(h, weapons[index].ammo().rounds() == 0, "Initial automatic shot empties magazine");
            sawReload[index] = WeaponRuntime.reloading(weapons[index].player());
        }
        int finish = 2 * p.reloadTicks() + 48;
        for (int delay = 1; delay <= finish; delay++) {
            int tick = delay;
            h.runAfterDelay(delay, () -> {
                for (int index = 0; index < weapons.length; index++) {
                    var weapon = weapons[index];
                    if (releasedAt[index] < 0) {
                        heldTick(h, weapon, tick);
                        sawReload[index] |= WeaponRuntime.reloading(weapon.player());
                        if (weapon.ammo().reserve() == 11 && reserve - weapon.ammo().total() >= 3) {
                            check(h, sawReload[index] && !WeaponRuntime.reloading(weapon.player()),
                                    "Maintained real input resumes several shots after reload: " + weapon.label());
                            check(h, weapon.ammo().rounds() > p.magazine() / 2,
                                    "Release before ammunition exhaustion can mask a stuck automatic trigger");
                            releasedAt[index] = tick;
                            release(weapon);
                        }
                    } else {
                        quietTick(h, weapon, tick);
                        if (tick >= releasedAt[index] + WeaponRuntime.HEARTBEAT_LEASE_TICKS + 2) {
                            if (quietRounds[index] < 0) quietRounds[index] = weapon.ammo().rounds();
                            check(h, weapon.ammo().rounds() == quietRounds[index]
                                            && weapon.ammo().rounds() > 0 && weapon.ammo().reserve() == 11
                                            && !WeaponRuntime.reloading(weapon.player()),
                                    "Release/expired lease stops resumed fire with live ammo remaining: " + weapon.label());
                        }
                    }
                    bounded(h, weapon, reserve);
                    TestPlayers.drain(weapon.player());
                }
                if (tick == finish) {
                    for (int index = 0; index < weapons.length; index++) {
                        check(h, releasedAt[index] >= 0 && quietRounds[index] > 0
                                        && tick - releasedAt[index] > WeaponRuntime.HEARTBEAT_LEASE_TICKS + 12,
                                "Each grip demonstrates both resume and a sustained released-input quiet window");
                    }
                    h.succeed();
                }
            });
        }
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 240, environment = "destiny-test:w90_isolated")
    public void releasedNativeAndExpiredHeartbeatCannotResumeWhenAutomaticReloadCompletes(GameTestHelper h) {
        var p = profile("retraced_path");
        int reserve = p.magazine() + 11;
        var weapons = new Weapon[] {
                equip(h, "retraced_path", WeaponModels.Grip.NATIVE, 1, reserve),
                equip(h, "retraced_path", WeaponModels.Grip.TWO_HAND, 1, reserve)
        };
        boolean[] sawReload = new boolean[2];
        for (int index = 0; index < weapons.length; index++) {
            var weapon = weapons[index];
            use(h, weapon);
            sawReload[index] = WeaponRuntime.reloading(weapon.player());
            release(weapon);
        }
        int finish = 2 * p.reloadTicks() + 24;
        for (int delay = 1; delay <= finish; delay++) {
            int tick = delay;
            h.runAfterDelay(delay, () -> {
                for (int index = 0; index < weapons.length; index++) {
                    var weapon = weapons[index];
                    quietTick(h, weapon, tick);
                    sawReload[index] |= WeaponRuntime.reloading(weapon.player());
                    check(h, weapon.ammo().total() == reserve,
                            "Lost input cannot fire a round before, during or after automatic reload: " + weapon.label());
                    bounded(h, weapon, reserve);
                    if (tick == finish) {
                        check(h, sawReload[index] && !WeaponRuntime.reloading(weapon.player())
                                        && weapon.ammo().rounds() == p.magazine() && weapon.ammo().reserve() == 11,
                                "Reload still completes without input; no latent resumed shot: " + weapon.label());
                    }
                }
                if (tick == finish) h.succeed();
            });
        }
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 240, environment = "destiny-test:w90_isolated")
    public void noSpareAmmoCreatesNeitherReloadNorRetryAfterLaterReservePickup(GameTestHelper h) {
        var weapons = new Weapon[] {
                equip(h, "retraced_path", WeaponModels.Grip.NATIVE, 1, 0),
                equip(h, "retraced_path", WeaponModels.Grip.TWO_HAND, 1, 0)
        };
        for (var weapon : weapons) {
            use(h, weapon);
            release(weapon);
            check(h, weapon.ammo().total() == 0, "Last shot spends the only finite round");
        }
        int pickupAt = WeaponRuntime.HEARTBEAT_LEASE_TICKS + 12;
        int finish = pickupAt + 2 * weapons[0].profile().reloadTicks() + 24;
        for (int delay = 1; delay <= finish; delay++) {
            int tick = delay;
            h.runAfterDelay(delay, () -> {
                for (var weapon : weapons) {
                    quietTick(h, weapon, tick);
                    if (tick == pickupAt) {
                        var ammo = weapon.ammo();
                        check(h, ammo.addReserve(3) == 3, "Later real pickup supplies only reserve");
                        WeaponItems.save(weapon.stack(), ammo);
                    }
                    check(h, !WeaponRuntime.reloading(weapon.player()) && weapon.ammo().rounds() == 0
                                    && weapon.ammo().reserve() == (tick >= pickupAt ? 3 : 0),
                            "Failed auto reload does not leave a timer, free ammo or a persistent retry: " + weapon.label());
                }
                if (tick == finish) h.succeed();
            });
        }
    }

    private static void cancelPendingBurst(GameTestHelper h, boolean skill) {
        var weapon = equip(h, "stormchaser", WeaponModels.Grip.TWO_HAND, 1, 2);
        var target = target(h);
        var p = weapon.profile();
        check(h, p.sharedBurstAmmo() && p.burst() == 3 && p.burstSpacingTicks() > 1,
                "First spent unit leaves a genuine queued-burst cancellation window");
        use(h, weapon);
        int[] cancelledAt = {-1};
        int finish = p.chargeTicks() + (int) Math.ceil(2 * p.burstSpacingTicks()) + 2 * p.reloadTicks() + 24;
        for (int delay = 1; delay <= finish; delay++) {
            int tick = delay;
            h.runAfterDelay(delay, () -> {
                if (cancelledAt[0] < 0) {
                    heldTick(h, weapon, tick);
                    if (weapon.ammo().rounds() == 0) {
                        check(h, !WeaponRuntime.reloading(weapon.player()),
                                "Cancel the queued candidate before any reload timer starts");
                        hits(h, target, weapon, 1, "Cancel after the first actual bolt, while two remain queued");
                        cancelledAt[0] = tick;
                        if (skill) WeaponRuntime.cancelUseForSkill(weapon.player());
                        else {
                            weapon.player().setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
                            WeaponRuntime.tickPlayer(weapon.player());
                        }
                    }
                } else {
                    if (!skill && tick == cancelledAt[0] + 1) {
                        weapon.player().setItemInHand(InteractionHand.MAIN_HAND, weapon.stack());
                    }
                    quietTick(h, weapon, tick);
                }
                if (cancelledAt[0] >= 0) {
                    check(h, weapon.ammo().rounds() == 0 && weapon.ammo().reserve() == 2
                                    && !WeaponRuntime.reloading(weapon.player()),
                            "Cancelled pending reload never restarts, transfers or refunds ammo");
                    hits(h, target, weapon, 1, "Cancellation prevents every unexecuted later bolt");
                }
                TestPlayers.drain(weapon.player());
                if (tick == finish) {
                    check(h, cancelledAt[0] >= 0 && weapon.player().getMainHandItem() == weapon.stack(),
                            "Observe a real pending cancellation and re-equip the same saved empty stack");
                    h.succeed();
                }
            });
        }
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 240, environment = "destiny-test:w90_isolated")
    public void swapAndReequipCancelQueuedEmptyReloadBeforeItBegins(GameTestHelper h) {
        cancelPendingBurst(h, false);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 240, environment = "destiny-test:w90_isolated")
    public void skillCancelsQueuedEmptyReloadBeforeItBegins(GameTestHelper h) {
        cancelPendingBurst(h, true);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 240, environment = "destiny-test:w90_isolated")
    public void manualAndEmptyTriggerReloadsStillCannotQueueAutomaticFireInEitherGrip(GameTestHelper h) {
        var p = profile("retraced_path");
        var weapons = new Weapon[] {
                equip(h, "retraced_path", WeaponModels.Grip.NATIVE, 1, p.magazine() + 10),
                equip(h, "retraced_path", WeaponModels.Grip.TWO_HAND, 1, p.magazine() + 10),
                equip(h, "retraced_path", WeaponModels.Grip.NATIVE, 0, p.magazine() + 11),
                equip(h, "retraced_path", WeaponModels.Grip.TWO_HAND, 0, p.magazine() + 11)
        };
        for (int index = 0; index < weapons.length; index++) {
            if (index < 2) check(h, WeaponRuntime.reload(weapons[index].player()), "Manual reload starts");
            else use(h, weapons[index]);
            check(h, WeaponRuntime.reloading(weapons[index].player()), "Existing reload entry point starts its timer");
        }
        int finish = 2 * p.reloadTicks() + 24;
        for (int delay = 1; delay <= finish; delay++) {
            int tick = delay;
            h.runAfterDelay(delay, () -> {
                for (var weapon : weapons) {
                    // Offer real callbacks only while the timer owns input. A post-completion
                    // fresh item.use would be a valid new press and is intentionally not sent.
                    if (WeaponRuntime.reloading(weapon.player()) && tick % 4 == 0) use(h, weapon);
                    quietTick(h, weapon, tick);
                    check(h, weapon.ammo().total() == p.magazine() + 11,
                            "Manual/empty-trigger reload does not inherit shot-caused automatic hold permission");
                    if (tick == finish) {
                        check(h, !WeaponRuntime.reloading(weapon.player()) && weapon.ammo().rounds() == p.magazine()
                                        && weapon.ammo().reserve() == 11,
                                "Original timer completes and loaded ammo remains unfired: " + weapon.label());
                    }
                }
                if (tick == finish) h.succeed();
            });
        }
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 240, environment = "destiny-test:w90_isolated")
    public void lastSwordSwingIsExcludedFromRangedEmptyReload(GameTestHelper h) {
        var weapon = equip(h, "abide_the_return", WeaponModels.Grip.NATIVE, 1, 0);
        check(h, weapon.profile().mode() == WeaponProfile.Mode.MELEE, "Sword uses the melee path");
        check(h, WeaponRuntime.onPunch(weapon.player()), "Sword swing consumes the real weapon attack");
        check(h, weapon.ammo().rounds() == 0, "Last sword swing spends its loaded unit");
        int finish = 2 * weapon.profile().reloadTicks() + 24;
        for (int delay = 1; delay <= finish; delay++) {
            int tick = delay;
            h.runAfterDelay(delay, () -> {
                quietTick(h, weapon, tick);
                check(h, weapon.ammo().rounds() == 0 && weapon.ammo().reserve() == 0
                                && !WeaponRuntime.reloading(weapon.player()),
                        "A melee last hit cannot queue ranged reload or grant ammo");
                if (tick == finish) h.succeed();
            });
        }
    }
}
