package kim.biryeong.destiny.test;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.Tasks;
import kim.biryeong.destiny.ability.hunter.HunterDodge;
import kim.biryeong.destiny.ability.hunter.HunterGrenade;
import kim.biryeong.destiny.ability.hunter.HunterMelee;
import kim.biryeong.destiny.ability.hunter.HunterSkillCast;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

/** Normal END_SERVER_TICK scheduler; no manual ticking, sleeps, or mutation of global tuning. */
public final class HunterOrdinaryTimingGameTests {
    private static final String FLOOR = "destiny-test:floor";

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static ServerPlayer owner(GameTestHelper h, Element element) {
        ServerPlayer p = TestPlayers.hunter(h, element, new Vec3(2.5, 1, 6.5), -90, -65);
        TestCleanup.register(h, () -> TestPlayers.remove(p));
        return p;
    }

    private static HunterGrenade grenade() {
        return new HunterGrenade(kim.biryeong.destiny.ability.hunter.HunterAbilities.ARC_FLASHBANG, "H20 grenade", Element.ARC, 30);
    }

    private static HunterMelee melee(Element element) {
        return new HunterMelee(DestinyGuardians.id("h20_test_melee"), "H20 melee", element, 30);
    }

    private static void releaseTiming(GameTestHelper h, Element element, Ability ability) {
        ServerPlayer p = owner(h, element);
        int accepted = h.getLevel().getServer().getTickCount();
        check(h, ability.activate(p), "Cast accepted");
        check(h, SimProjectile.activeCount(p) == 0, "No projectile at button press");
        AtomicInteger firstRelease = new AtomicInteger(-1);
        // Registered after the contact task, so this samples the SAME END_SERVER_TICK after release.
        Tasks.run(p, h.getLevel(), age -> {
            if (SimProjectile.activeCount(p) > 0) {
                firstRelease.set(h.getLevel().getServer().getTickCount() - accepted);
                return false;
            }
            return true;
        });
        h.runAfterDelay(8, () -> {
            int contact = ability.slot() == kim.biryeong.destiny.guardian.AbilitySlot.GRENADE ? 6 : 4;
            check(h, firstRelease.get() == contact, "First projectile must appear at exactly T+" + contact + ", got " + firstRelease.get());
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void grenadeReleasesOnContact(GameTestHelper h) { releaseTiming(h, Element.ARC, grenade()); }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void solarKnifeReleasesOnContact(GameTestHelper h) { releaseTiming(h, Element.SOLAR, melee(Element.SOLAR)); }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void voidSmokeReleasesOnContact(GameTestHelper h) { releaseTiming(h, Element.VOID, melee(Element.VOID)); }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void arcDamageAppearsOnContactNotLunge(GameTestHelper h) {
        ServerPlayer p = owner(h, Element.ARC);
        p.setXRot(0);
        var target = h.spawn(EntityTypes.HUSK, new Vec3(4.5, 1, 6.5));
        target.setNoAi(true);
        TestCleanup.register(h, target::discard);
        float initial = target.getHealth();
        int accepted = h.getLevel().getServer().getTickCount();
        AtomicInteger firstHit = new AtomicInteger(-1);
        check(h, melee(Element.ARC).activate(p), "Arc cast accepted");
        check(h, target.getHealth() == initial, "No damage at button press");
        Tasks.run(p, h.getLevel(), age -> {
            if (target.getHealth() < initial) {
                firstHit.set(h.getLevel().getServer().getTickCount() - accepted);
                return false;
            }
            return true;
        });
        h.runAfterDelay(8, () -> {
            check(h, firstHit.get() == 4, "Arc damage must land at T+4, got " + firstHit.get());
            h.succeed();
        });
    }

    private static void cancelled(GameTestHelper h, Consumer<ServerPlayer> cancel) {
        ServerPlayer p = owner(h, Element.ARC);
        check(h, grenade().activate(p), "Grenade accepted");
        cancel.accept(p);
        h.runAfterDelay(8, () -> {
            check(h, SimProjectile.activeCount(p) == 0, "Cancelled windup cannot spawn a projectile");
            check(h, Tasks.count(p) == 0 && !kim.biryeong.destiny.ability.GrenadeThrow.active(p), "Cancelled throw owner and contact tasks must not linger");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void cleanupCancelsPendingRelease(GameTestHelper h) { cancelled(h, AbilityService::cleanup); }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void classChangeWithoutCleanupStillCancelsRelease(GameTestHelper h) {
        cancelled(h, p -> Guardians.data(p).setGuardianClass(GuardianClass.TITAN));
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void runtimeReplacementCancelsRelease(GameTestHelper h) { cancelled(h, Guardians::forget); }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void deadOwnerCannotRelease(GameTestHelper h) { cancelled(h, p -> p.setHealth(0)); }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void dimensionChangeWithoutCleanupCancelsRelease(GameTestHelper h) {
        cancelled(h, p -> {
            var other = h.getLevel().getServer().getLevel(
                    h.getLevel().dimension().equals(Level.NETHER) ? Level.OVERWORLD : Level.NETHER);
            check(h, other != null, "Second dimension available");
            p.setServerLevel(other);
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void newerOrdinaryCastRevokesOnlyOlderWindup(GameTestHelper h) {
        ServerPlayer p = owner(h, Element.SOLAR);
        check(h, melee(Element.SOLAR).activate(p), "First melee contact windup");
        check(h, melee(Element.SOLAR).activate(p), "Replacing windup");
        AtomicInteger maximum = new AtomicInteger();
        Tasks.run(p, h.getLevel(), age -> {
            maximum.accumulateAndGet(SimProjectile.activeCount(p), Math::max);
            return true;
        });
        h.runAfterDelay(8, () -> {
            check(h, maximum.get() == 1, "Only the newer windup may release, got " + maximum.get());
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void cancelPendingLeavesExistingProjectileAndUnrelatedTask(GameTestHelper h) {
        ServerPlayer p = owner(h, Element.SOLAR);
        AtomicInteger calls = new AtomicInteger();
        var existing = SimProjectile.launch(p, p.getEyePosition().add(0, 10, 0), Vec3.ZERO, 0, 60,
                new ItemStack(Items.SNOWBALL), .25f, Element.ARC.color(), hit -> {});
        Tasks.run(p, h.getLevel(), age -> { calls.incrementAndGet(); return true; });
        check(h, melee(Element.SOLAR).activate(p), "Melee contact windup accepted");
        HunterSkillCast.cancelPending(p);
        h.runAfterDelay(8, () -> {
            check(h, !existing.isDone() && SimProjectile.activeCount(p) == 1, "Existing projectile survives windup cancellation");
            check(h, calls.get() > 0 && Tasks.count(p) == 1, "Unrelated task is not broadly cancelled");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void dodgeKeepsImmediatePhysicsAndSixInvulnerableTicks(GameTestHelper h) {
        ServerPlayer p = owner(h, Element.ARC);
        Guardians.runtime(p).lastInput = new Input(false, true, false, false, false, false, false);
        var dodge = new HunterDodge(DestinyGuardians.id("h20_test_dodge"), "H20 dodge", HunterDodge.Variant.MARKSMAN, 12);
        check(h, dodge.activate(p), "Dodge accepted");
        check(h, p.getDeltaMovement().distanceTo(new Vec3(-1.15, .18, 0)) < 1e-5, "Backward impulse is immediate");
        check(h, Guardians.runtime(p).invulnerableTicks == 6, "Six invulnerable ticks retained");
        check(h, p.getYRot() == -90 && p.getXRot() == -65, "Dodge cannot rotate aim");
        h.runAfterDelay(5, () -> {
            check(h, Tasks.count(p) == 0, "Ground-contact task finishes, no persistent scheduler entry");
            h.succeed();
        });
    }
}
