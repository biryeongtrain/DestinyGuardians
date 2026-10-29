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
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** W48 held-input acceptance through the real item, runtime and item-owned ammunition. */
public final class WeaponAutoFireW48GameTests {
    private record HeldWeapon(ServerPlayer player, ItemStack stack, WeaponProfile profile,
                              WeaponModels.Grip grip, int initialRounds) {
        private String label() {
            return WeaponItems.entry(stack).orElseThrow().id() + " / " + grip;
        }
    }

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static int rounds(HeldWeapon weapon) {
        return WeaponItems.magazine(weapon.stack(), weapon.profile()).rounds();
    }

    private static HeldWeapon equip(GameTestHelper h, String id, WeaponModels.Grip grip) {
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
        WeaponItems.save(stack, new WeaponMagazine(profile, profile.magazine(), 0));
        player.setItemInHand(InteractionHand.MAIN_HAND, stack);
        check(h, WeaponModels.twoHanded(stack) == (grip == WeaponModels.Grip.TWO_HAND),
                "Requested input protocol: " + id + " / " + grip);
        return new HeldWeapon(player, stack, profile, grip, profile.magazine());
    }

    private static void use(GameTestHelper h, HeldWeapon weapon) {
        WeaponCombatItem.INSTANCE.use(h.getLevel(), weapon.player(), InteractionHand.MAIN_HAND);
    }

    private static void nativeTick(GameTestHelper h, HeldWeapon weapon, int elapsed) {
        WeaponCombatItem.INSTANCE.onUseTick(h.getLevel(), weapon.player(), weapon.stack(), 72000 - elapsed);
        WeaponRuntime.continueUse(weapon.player());
    }

    private static void start(GameTestHelper h, HeldWeapon weapon) {
        use(h, weapon);
        int afterFirst = rounds(weapon);
        check(h, weapon.initialRounds() - afterFirst == (weapon.profile().chargeTicks() == 0 ? 1 : 0),
                "Initial press spends one round, or waits for charge: " + weapon.label());
        for (int duplicate = 0; duplicate < 3; duplicate++) {
            use(h, weapon);
            if (weapon.grip() == WeaponModels.Grip.NATIVE) nativeTick(h, weapon, 0);
            WeaponRuntime.tickPlayer(weapon.player());
            check(h, rounds(weapon) == afterFirst,
                    "Duplicate initial callbacks cannot fire twice in one server tick: " + weapon.label());
        }
        check(h, weapon.player().isUsingItem() == (weapon.grip() == WeaponModels.Grip.NATIVE),
                "Native grip owns use state; two-hand grip owns a heartbeat lease: " + weapon.label());
    }

    private static void heldTick(GameTestHelper h, HeldWeapon weapon, int elapsed) {
        boolean heartbeat = weapon.grip() == WeaponModels.Grip.TWO_HAND && elapsed % 4 == 0;
        if (heartbeat) use(h, weapon);
        if (weapon.grip() == WeaponModels.Grip.NATIVE) {
            check(h, weapon.player().isUsingItem(), "Native input remains held: " + weapon.label());
            nativeTick(h, weapon, elapsed);
        }
        // Drain legitimate queued burst bolts before measuring duplicated callbacks. Fusion/pulse
        // bolts may share a tick; they are not extra trigger cycles.
        WeaponRuntime.tickPlayer(weapon.player());
        int afterFirst = rounds(weapon);
        for (int duplicate = 0; duplicate < 3; duplicate++) {
            if (heartbeat) use(h, weapon);
            if (weapon.grip() == WeaponModels.Grip.NATIVE) nativeTick(h, weapon, elapsed);
            WeaponRuntime.tickPlayer(weapon.player());
            check(h, rounds(weapon) == afterFirst,
                    "Repeated callbacks in the same tick cannot spend extra ammo: " + weapon.label());
        }
    }

    private static void releasedTick(GameTestHelper h, HeldWeapon weapon, int elapsed) {
        // Two-hand release is loss of heartbeat, so tickPlayer must expire the lease naturally.
        WeaponRuntime.tickPlayer(weapon.player());
        int beforeDuplicates = rounds(weapon);
        if (weapon.grip() == WeaponModels.Grip.NATIVE) nativeTick(h, weapon, elapsed);
        WeaponRuntime.tickPlayer(weapon.player());
        check(h, rounds(weapon) == beforeDuplicates,
                "Duplicate runtime ticks/stale native callbacks add no shot after release: " + weapon.label());
    }

    private static void exerciseBothGrips(GameTestHelper h, String id, boolean automatic) {
        var weapons = new HeldWeapon[] {
                equip(h, id, WeaponModels.Grip.NATIVE),
                equip(h, id, WeaponModels.Grip.TWO_HAND)
        };
        var profile = weapons[0].profile();
        for (var weapon : weapons) {
            check(h, weapon.profile().automatic() == automatic, "Current profile fire policy: " + weapon.label());
            start(h, weapon);
        }
        // Broad windows establish repetition, not an exact cadence. Real server callbacks can run
        // alongside these explicit ticks; the assertions deliberately tolerate their ordering.
        int heldTicks = Math.max(24, (int) Math.ceil(profile.chargeTicks() + 2 * profile.cadenceTicks()
                + (profile.burst() - 1) * profile.burstSpacingTicks() + 4));
        int quietStart = heldTicks + WeaponRuntime.HEARTBEAT_LEASE_TICKS + 2;
        int finish = quietStart + (int) Math.ceil(2 * profile.cadenceTicks()) + 4;
        int[] releasedRounds = {-1, -1};
        int[] quietRounds = {-1, -1};
        for (int elapsed = 1; elapsed <= finish; elapsed++) {
            int tick = elapsed;
            h.runAfterDelay(tick, () -> {
                for (int index = 0; index < weapons.length; index++) {
                    var weapon = weapons[index];
                    if (tick <= heldTicks) {
                        heldTick(h, weapon, tick);
                        if (tick == heldTicks) {
                            int spent = weapon.initialRounds() - rounds(weapon);
                            if (automatic) {
                                check(h, spent >= 3, "Maintained input fires repeated real rounds: " + weapon.label());
                            } else {
                                int oneTrigger = profile.sharedBurstAmmo() ? 1 : profile.burst();
                                check(h, spent == oneTrigger,
                                        "Maintained input fires exactly one trigger's ammo, including its burst: " + weapon.label());
                            }
                            check(h, rounds(weapon) > 0 && !WeaponRuntime.reloading(weapon.player()),
                                    "Loaded ammo remains, so a reload/empty magazine cannot mask repetition: " + weapon.label());
                        }
                    } else {
                        if (tick == heldTicks + 1 && weapon.grip() == WeaponModels.Grip.NATIVE) {
                            weapon.player().releaseUsingItem();
                            check(h, !weapon.player().isUsingItem(), "Native release clears use state: " + weapon.label());
                            releasedRounds[index] = rounds(weapon);
                        }
                        releasedTick(h, weapon, tick);
                        if (weapon.grip() == WeaponModels.Grip.NATIVE) {
                            check(h, rounds(weapon) == releasedRounds[index],
                                    "Native release immediately stops further rounds: " + weapon.label());
                        }
                        if (tick == quietStart) {
                            quietRounds[index] = rounds(weapon);
                            check(h, quietRounds[index] > 0 && !WeaponRuntime.reloading(weapon.player()),
                                    "Release leaves live ammunition available: " + weapon.label());
                        } else if (tick > quietStart) {
                            check(h, rounds(weapon) == quietRounds[index],
                                    "No later rounds after native release/heartbeat expiry: " + weapon.label());
                        }
                    }
                    check(h, WeaponItems.magazine(weapon.stack(), weapon.profile()).reserve() == 0,
                            "Held/released input cannot invent reserve ammo: " + weapon.label());
                    TestPlayers.drain(weapon.player());
                }
                if (tick == finish) h.succeed();
            });
        }
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void aishasEmbraceRepeatsWithNativeHoldAndFourTickHeartbeat(GameTestHelper h) {
        exerciseBothGrips(h, "aishas_embrace", true);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void deadManWalkingRepeatsWithNativeHoldAndFourTickHeartbeat(GameTestHelper h) {
        exerciseBothGrips(h, "dead_man_walking_xx7463", true);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void ikelosShotgunRepeatsWithNativeHoldAndFourTickHeartbeat(GameTestHelper h) {
        exerciseBothGrips(h, "ikelos_sg_v1_0_1", true);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void semiautoScoutDoesNotRepeatInEitherGrip(GameTestHelper h) {
        exerciseBothGrips(h, "long_arm", false);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void semiautoSidearmDoesNotRepeatInEitherGrip(GameTestHelper h) {
        exerciseBothGrips(h, "allied_demand", false);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void semiautoShotgunDoesNotRepeatInEitherGrip(GameTestHelper h) {
        exerciseBothGrips(h, "dust_rock_blues", false);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void rapidFirePulseCompletesOneBurstWithoutRepeatingInEitherGrip(GameTestHelper h) {
        exerciseBothGrips(h, "claws_of_the_wolf", false);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void rapidFireFusionCompletesOneChargeWithoutRepeatingInEitherGrip(GameTestHelper h) {
        exerciseBothGrips(h, "null_composure", false);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void rapidFireSniperDoesNotRepeatInEitherGrip(GameTestHelper h) {
        exerciseBothGrips(h, "apostate", false);
    }
}
