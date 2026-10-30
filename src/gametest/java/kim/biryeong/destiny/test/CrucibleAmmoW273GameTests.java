package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.crucible.*;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** Manual, sequential tests in the master's empty tower-enabled Control server.
 * Reuses W263's real login/packet-ack/cleanup fixture; deaths and replacement objects
 * come from Combat and normal Runtime hooks, never synthetic match state or global ticks.
 * Direct magazine consumption/position changes below are explicit fixture preparation.
 */
public final class CrucibleAmmoW273GameTests {
    private static final String SNIPER = "bite_of_the_fox", TRACE = "retraced_path", HEAVY = "hammerhead";

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static int slot(String id) { return WeaponCharacteristics.of(entry(id)).slot().hotbar(); }
    private static WeaponMagazine ammo(ServerPlayer p, String id) {
        return WeaponItems.magazine(p.getInventory().getItem(slot(id)), WeaponProfile.forEntry(entry(id)));
    }
    private static void totals(GameTestHelper h, ServerPlayer p, long sniper, long trace) {
        check(h, ammo(p, SNIPER).total() == sniper && ammo(p, TRACE).total() == trace,
                "Independent equipped pools: expected " + sniper + "/" + trace + ", got "
                        + ammo(p, SNIPER).total() + "/" + ammo(p, TRACE).total());
    }
    private static void spend(ServerPlayer p, String id) {
        var ammo = ammo(p, id);
        while (ammo.total() > 0) {
            if (ammo.rounds() == 0 && ammo.reload() == 0) throw new AssertionError("Cannot spend fixture ammo");
            if (!ammo.consume(ammo.rounds())) throw new AssertionError("Fixture consumption failed");
        }
        WeaponItems.save(p.getInventory().getItem(slot(id)), ammo);
    }
    private static void move(GameTestHelper h, ServerPlayer p, Vec3 at) {
        CrucibleW263GameTests.moveFixture(h, p, at);
        p.setNoGravity(true);
    }
    private static void kill(GameTestHelper h, ServerPlayer attacker, ServerPlayer victim) {
        check(h, CrucibleRuntime.canFight(attacker, victim), "Current opponents are outside respawn protection");
        check(h, Combat.damage(attacker, victim, 10000, Element.ARC) && victim.isDeadOrDying(),
                "Actual lethal Combat transaction reaches Runtime death hook");
    }

    private static final class Fixture {
        final GameTestHelper h;
        final List<CrucibleW263GameTests.Login> logins = new ArrayList<>();
        Fixture(GameTestHelper h) {
            this.h = h;
            check(h, CrucibleRuntime.snapshot().members().isEmpty(), "Exclusive empty Control session required");
            TowerSpawnWorld.open(h.getLevel().getServer());
            h.onEachTick(() -> logins.forEach(l -> CrucibleW263GameTests.tickLogin(h.getLevel().getServer(), l)));
        }
        ServerPlayer join(String name) {
            var p = CrucibleW263GameTests.login(h, logins, name, Element.ARC);
            check(h, TowerSpawnWorld.teleport(p), "Fixture starts in Tower");
            for (String id : List.of(SNIPER, TRACE, HEAVY))
                p.getInventory().setItem(slot(id), WeaponItems.create(entry(id)));
            check(h, slot(SNIPER) != slot(TRACE), "Two Special fixtures occupy distinct canonical slots");
            p.getInventory().setSelectedSlot(slot(SNIPER));
            check(h, WeaponLoadout.equipHeld(p) == null && CrucibleRuntime.join(p), "Actual equipped login joins Control");
            totals(h, p, 2, 30);
            check(h, ammo(p, HEAVY).total() == 0, "Heavy starts empty");
            return p;
        }
        ServerPlayer current(ServerPlayer original) {
            var p = h.getLevel().getServer().getPlayerList().getPlayer(original.getUUID());
            check(h, p != null && p.isAlive() && CrucibleRuntime.currentParticipant(p), "Current living Runtime member exists");
            return p;
        }
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated", maxTicks = 830, manualOnly = true)
    public void everyLifeGetsTwoAndThirtyOnceWhileStaleCallbacksSwapsAndRejoinCannotRefill(GameTestHelper h) {
        var f = new Fixture(h);
        var original = f.join("W273Life");
        var enemy = f.join("W273Opponent");
        spend(original, SNIPER); spend(original, TRACE);
        CrucibleAmmo.arrive(original, true); CrucibleAmmo.arrive(original, false);
        totals(h, original, 0, 0);
        ServerPlayer[] second = new ServerPlayer[1];
        h.runAfterDelay(450, () -> {
            totals(h, original, 0, 0); // INTRO/PLAYING arrivals must not pay twice.
            kill(h, enemy, original);
            check(h, CrucibleAmmo.sharedPositions(enemy).isEmpty(), "Empty Special death drops nothing");
        });
        h.runAfterDelay(570, () -> {
            second[0] = f.current(original);
            check(h, second[0] != original, "Native respawn created a replacement object");
            totals(h, second[0], 2, 30);
            CrucibleAmmo.arrive(original, true); CrucibleAmmo.died(original); CrucibleAmmo.leave(original);
            CrucibleAmmo.arrive(second[0], true); CrucibleAmmo.arrive(second[0], false);
            totals(h, second[0], 2, 30);
            check(h, CrucibleAmmo.sharedPositions(enemy).isEmpty(), "Late old-object callbacks cannot invent death drops");
        });
        h.runAfterDelay(620, () -> {
            kill(h, enemy, second[0]);
            totals(h, second[0], 0, 0);
            check(h, CrucibleAmmo.sharedPositions(enemy).size() == 1, "Two armed Special weapons still drop one brick");
            CrucibleAmmo.died(second[0]); CrucibleAmmo.arrive(second[0], false);
            check(h, CrucibleAmmo.sharedPositions(enemy).size() == 1, "Duplicate death/dead arrival cannot multiply bricks");
            move(h, enemy, CrucibleAmmo.sharedPositions(enemy).getFirst());
            CrucibleAmmo.tick(enemy);
            check(h, CrucibleAmmo.sharedPositions(enemy).isEmpty(), "Consumed death brick does not reach the next life");
        });
        h.runAfterDelay(750, () -> {
            var third = f.current(original);
            check(h, third != second[0], "Second native death produces another replacement");
            totals(h, third, 2, 30);
            check(h, ammo(third, HEAVY).total() == 0, "Heavy remains empty on respawn");
            var removed = third.getInventory().getItem(slot(SNIPER));
            third.getInventory().setItem(slot(SNIPER), WeaponItems.create(entry(SNIPER)));
            third.getInventory().setSelectedSlot(slot(SNIPER));
            check(h, WeaponLoadout.equipHeld(third) == null, "Real replacement equipment mutation accepted");
            totals(h, third, 0, 0);
            check(h, WeaponItems.magazine(removed, WeaponProfile.forEntry(entry(SNIPER))).total() == 0,
                    "Removed equipment cannot bank finite ammo");
            CrucibleAmmo.arrive(third, true); CrucibleAmmo.arrive(third, false);
            totals(h, third, 0, 0);
            check(h, CrucibleRuntime.leave(third, true) && CrucibleRuntime.join(third), "Same-round exit/rejoin accepted");
            totals(h, third, 0, 0);
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated", maxTicks = 750, manualOnly = true)
    public void sharedDeathBrickPaysEitherTeamOnceAndRejectsSpectatorOutsiderAndFullPools(GameTestHelper h) {
        var f = new Fixture(h);
        var donor = f.join("W273Donor");
        var enemy = f.join("W273Enemy");
        var ally = f.join("W273Ally");
        check(h, CrucibleRuntime.team(donor) == CrucibleRuntime.team(ally)
                        && CrucibleRuntime.team(donor) != CrucibleRuntime.team(enemy), "Fixture covers both teams");
        h.runAfterDelay(450, () -> {
            // Hold recipients above the floor so automatic pickup cannot race the assertions.
            move(h, enemy, donor.position().add(0, 5, 0));
            move(h, ally, donor.position().add(0, 7, 0));
            kill(h, enemy, donor);
            var at = CrucibleAmmo.sharedPositions(enemy).getFirst();
            check(h, CrucibleAmmo.sharedPositions(enemy).size() == 1
                            && AmmoEconomy.safePosition(enemy.level(), at).isPresent(), "One shared brick on verified safe field support");
            enemy.setGameMode(GameType.SPECTATOR);
            move(h, enemy, at); CrucibleAmmo.tick(enemy);
            totals(h, enemy, 2, 30);
            check(h, CrucibleAmmo.sharedPositions(ally).size() == 1, "Participating spectator cannot consume");
            var outsider = TestPlayers.create(h, Vec3.ZERO, 0, 0, "W273Outsider");
            TestCleanup.register(h, () -> TestPlayers.remove(outsider));
            outsider.setServerLevel(enemy.level()); outsider.setPos(at);
            outsider.getInventory().setItem(slot(SNIPER), WeaponItems.create(entry(SNIPER)));
            long outsideBefore = ammo(outsider, SNIPER).total();
            CrucibleAmmo.tick(outsider);
            check(h, ammo(outsider, SNIPER).total() == outsideBefore && CrucibleAmmo.sharedPositions(ally).size() == 1,
                    "Nearby living outsider cannot consume or receive Special");
            enemy.setGameMode(GameType.ADVENTURE);
            for (String id : List.of(SNIPER, TRACE)) {
                var profile = WeaponProfile.forEntry(entry(id));
                WeaponItems.save(enemy.getInventory().getItem(slot(id)), new WeaponMagazine(profile, profile.magazine(), profile.reserve()));
            }
            CrucibleAmmo.tick(enemy);
            check(h, CrucibleAmmo.sharedPositions(ally).size() == 1, "Full reserve pools leave the shared brick for another player");
            spend(enemy, SNIPER); spend(enemy, TRACE);
            CrucibleAmmo.tick(enemy);
            totals(h, enemy, 2, 30);
            check(h, ammo(enemy, SNIPER).rounds() == 0 && ammo(enemy, TRACE).rounds() == 0,
                    "Pickup pays reserves without silently reloading either magazine");
            move(h, ally, at); CrucibleAmmo.tick(ally);
            totals(h, ally, 2, 30);
            check(h, CrucibleAmmo.sharedPositions(ally).isEmpty(), "Same brick cannot pay a second nearby player");
        });
        h.runAfterDelay(630, () -> {
            var nextDonor = f.current(donor);
            totals(h, nextDonor, 2, 30);
            move(h, enemy, nextDonor.position().add(0, 5, 0));
            move(h, ally, nextDonor.position().add(0, 7, 0));
            kill(h, enemy, nextDonor);
            var at = CrucibleAmmo.sharedPositions(ally).getFirst();
            check(h, CrucibleRuntime.leave(nextDonor, false), "Dead donor exits without owning the shared pickup");
            check(h, CrucibleAmmo.sharedPositions(ally).size() == 1, "Donor exit does not remove a public death brick");
            move(h, ally, at); CrucibleAmmo.tick(ally);
            totals(h, ally, 4, 60);
            move(h, enemy, at); CrucibleAmmo.tick(enemy);
            totals(h, enemy, 2, 30);
            check(h, CrucibleAmmo.sharedPositions(ally).isEmpty(), "Ally collects once; enemy cannot collect it again");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated", maxTicks = 2350, manualOnly = true)
    public void disabledSpecialCratesDoNotChangeTheExistingPersonalHeavyWave(GameTestHelper h) {
        var f = new Fixture(h);
        var owner = f.join("W273HeavyA");
        var other = f.join("W273HeavyB");
        h.runAfterDelay(1050, () -> {
            check(h, CrucibleRuntime.snapshot().phaseTicks() >= 600 && CrucibleAmmo.bricks(owner) == 0
                            && CrucibleAmmo.bricks(other) == 0, "No Special crates at the old thirty-second wave");
            totals(h, owner, 2, 30);
        });
        h.runAfterDelay(2250, () -> {
            check(h, CrucibleRuntime.snapshot().phaseTicks() >= CrucibleAmmoRules.HEAVY_FIRST_TICKS,
                    "Real match clock reached the unchanged Heavy first-wave deadline");
            check(h, CrucibleAmmo.sharedPositions(owner).isEmpty() && CrucibleAmmo.bricks(owner) == 1
                            && CrucibleAmmo.bricks(other) == 1, "Only one personal Heavy crate per participant");
            var at = AmmoEconomy.safePosition(owner.level(), owner.position().add(-2, 0, 0)).orElseThrow();
            move(h, other, at); CrucibleAmmo.tick(other);
            check(h, ammo(other, HEAVY).total() == 0 && CrucibleAmmo.bricks(owner) == 1,
                    "Other team cannot collect the owner's personal Heavy crate");
            move(h, owner, at); CrucibleAmmo.tick(owner);
            check(h, ammo(owner, HEAVY).total() == CrucibleAmmoRules.heavyBrick("machine_gun")
                            && CrucibleAmmo.bricks(owner) == 0, "Unchanged personal Heavy pickup grants 22 MG rounds");
            totals(h, owner, 2, 30);
            h.succeed();
        });
    }
}
