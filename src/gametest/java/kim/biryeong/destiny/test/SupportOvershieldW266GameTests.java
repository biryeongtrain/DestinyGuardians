package kim.biryeong.destiny.test;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.titan.TitanAbilities;
import kim.biryeong.destiny.ability.titan.TitanExpandedSupers;
import kim.biryeong.destiny.ability.warlock.WarlockAbilities;
import kim.biryeong.destiny.ability.warlock.WarlockExpandedSupers;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.combat.SupportOvershield;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/** Real casts and native absorption lifecycle. Well's shield is the custom W266 extension.
 * No separate Void-shield PvE DR or visual/HUD assertions; registration belongs to master.
 */
public final class SupportOvershieldW266GameTests {
    private static final Identifier SUPPORT = DestinyGuardians.id("support_overshield");
    private static final Identifier FOREIGN = DestinyGuardians.id("w266_foreign_absorption");
    private static final Vec3 OUTSIDE = new Vec3(14.5, 1, 12.5);

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static void near(GameTestHelper h, float actual, float expected, String message) {
        check(h, Math.abs(actual - expected) < .001f,
                message + ": actual=" + actual + " expected=" + expected);
    }

    private static float cap(ServerPlayer p) { return p.getMaxHealth() * 45f / 230f; }
    private static float charge(ServerPlayer p, int ticks) { return p.getMaxHealth() * 15f / 230f / 20f * ticks; }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated",
            maxTicks = 400, skyAccess = true, manualOnly = true)
    public void actualWellsAndWardShareChargeCapAndRechargeAfterAbsorbedDamage(GameTestHelper h) {
        var f = new Fixture(h);
        f.after(48, () -> {
            f.assertFieldsAfterCast();
            f.enter();
            f.after(20, () -> {
                for (ServerPlayer p : f.recipients()) {
                    near(h, p.getAbsorptionAmount(), charge(p, 20),
                            "Well-only, Ward-only and overlapping fields charge at one 15 Destiny HP/s rate");
                    float before = p.getAbsorptionAmount();
                    AbilityService.tickPlayer(p);
                    AbilityService.tickPlayer(p);
                    near(h, p.getAbsorptionAmount(), before, "Duplicate player ticks in one world tick cannot recharge");
                }
                near(h, f.enemy.getAbsorptionAmount(), 0, "Enemy inside overlapping fields receives no shield");
            });
            f.after(70, () -> {
                for (ServerPlayer p : f.recipients()) {
                    near(h, p.getAbsorptionAmount(), cap(p), "Overlapping fields retain one 45 Destiny HP cap");
                }
                float before = f.overlap.getAbsorptionAmount();
                float health = f.overlap.getHealth();
                f.overlap.damageCooldownTime = 0;
                f.overlap.hurtServer(h.getLevel(), f.overlap.damageSources().generic(), before / 2);
                float damaged = f.overlap.getAbsorptionAmount();
                check(h, damaged > 0 && damaged < before, "Actual native damage consumes part of the support shield");
                near(h, f.overlap.getHealth(), health, "Absorbed hit leaves native health intact");
                f.after(10, () -> near(h, f.overlap.getAbsorptionAmount(),
                        Math.min(cap(f.overlap), damaged + charge(f.overlap, 10)),
                        "Damaged pool recharges at the shared rate while still inside"));
                f.after(40, () -> {
                    near(h, f.overlap.getAbsorptionAmount(), cap(f.overlap), "Recharged pool stops at the same cap");
                    near(h, f.enemy.getAbsorptionAmount(), 0, "Enemy remains excluded throughout charging");
                    h.succeed();
                });
            });
        });
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated",
            maxTicks = 400, skyAccess = true, manualOnly = true)
    public void leavingStopsChargeExpiresAt200TicksAndCleanupPreservesForeignAbsorption(GameTestHelper h) {
        var f = new Fixture(h);
        for (ServerPlayer p : f.recipients()) {
            p.getAttribute(Attributes.MAX_ABSORPTION).addTransientModifier(new AttributeModifier(
                    FOREIGN, 8, AttributeModifier.Operation.ADD_VALUE));
            p.setAbsorptionAmount(2);
        }
        f.after(48, () -> {
            f.assertFieldsAfterCast();
            for (ServerPlayer p : f.recipients()) {
                near(h, p.getAbsorptionAmount(), 2, "Outside players keep only their foreign absorption");
            }
            f.enter();
            f.after(20, () -> {
                for (ServerPlayer p : f.recipients()) {
                    near(h, p.getAbsorptionAmount(), 2 + charge(p, 20), "Support charge is added above foreign absorption");
                    f.move(p, OUTSIDE);
                    check(h, !WarlockExpandedSupers.inWell(p) && !TitanExpandedSupers.inWard(p),
                            "Leaving revokes live membership immediately, before another field tick");
                }
                // This callback runs after tickPlayer: now is the last in-field refresh, not the next outside tick.
                long lastRefresh = h.getLevel().getGameTime();
                float wellHeld = f.wellOnly.getAbsorptionAmount();
                float wardHeld = f.wardOnly.getAbsorptionAmount();
                // Exercise the death/disconnect cleanup helper without killing the fake player.
                f.overlap.damageCooldownTime = 0;
                float before = f.overlap.getAbsorptionAmount();
                f.overlap.hurtServer(h.getLevel(), f.overlap.damageSources().generic(), charge(f.overlap, 10));
                check(h, f.overlap.getAbsorptionAmount() < before && f.overlap.getAbsorptionAmount() > 2,
                        "Native damage precedes cleanup without an intervening reconciliation tick");
                SupportOvershield.cleanup(f.overlap);
                assertForeignOnly(h, f.overlap, 2);
                SupportOvershield.cleanup(f.overlap);
                assertForeignOnly(h, f.overlap, 2);
                f.after(20, () -> {
                    near(h, f.wellOnly.getAbsorptionAmount(), wellHeld, "Leaving Well stops a partially filled pool");
                    near(h, f.wardOnly.getAbsorptionAmount(), wardHeld, "Leaving Ward stops a partially filled pool");
                    // Unrelated absorption arriving after departure must also survive support expiration.
                    f.wellOnly.setAbsorptionAmount(wellHeld + 1);
                });
                f.after(199, () -> {
                    check(h, h.getLevel().getGameTime() - lastRefresh == 199, "199 real world ticks elapsed");
                    near(h, f.wellOnly.getAbsorptionAmount(), wellHeld + 1, "Well shield remains through tick 199");
                    near(h, f.wardOnly.getAbsorptionAmount(), wardHeld, "Ward shield remains through tick 199");
                    f.assertFieldsAfterCast();
                });
                f.after(200, () -> {
                    check(h, h.getLevel().getGameTime() - lastRefresh == 200, "200 real world ticks elapsed");
                    assertForeignOnly(h, f.wellOnly, 3);
                    assertForeignOnly(h, f.wardOnly, 2);
                    assertForeignOnly(h, f.overlap, 2);
                    AbilityService.cleanup(f.wellOnly);
                    assertForeignOnly(h, f.wellOnly, 3);
                    h.succeed();
                });
            });
        });
    }

    private static void assertForeignOnly(GameTestHelper h, ServerPlayer p, float amount) {
        near(h, p.getAbsorptionAmount(), amount, "Cleanup/expiry removes only support-owned absorption");
        var attribute = p.getAttribute(Attributes.MAX_ABSORPTION);
        check(h, !attribute.hasModifier(SUPPORT) && attribute.hasModifier(FOREIGN),
                "Support capacity is removed and the unrelated capacity modifier survives");
    }

    /** Fake players are not in PlayerList: drive player ticks even after their cast ends. */
    private static final class Fixture {
        private record Task(long due, Runnable action) { }
        final GameTestHelper h;
        final List<ServerPlayer> players = new ArrayList<>();
        final List<Task> tasks = new ArrayList<>();
        final ServerPlayer wellA, wellB, ward, wellOnly, wardOnly, overlap, enemy;

        Fixture(GameTestHelper h) {
            this.h = h;
            TestCleanup.register(h, tasks::clear);
            for (int x = 0; x < 16; x++) for (int z = 0; z < 14; z++) h.setBlock(x, 0, z, Blocks.STONE);
            var board = h.getLevel().getScoreboard();
            var team = board.addPlayerTeam("w266" + UUID.randomUUID().toString().substring(0, 8));
            TestCleanup.register(h, () -> board.removePlayerTeam(team));
            wellA = player(new Vec3(3.5, 1, 6.5));
            wellB = player(new Vec3(4.5, 1, 6.5));
            ward = player(new Vec3(9.5, 1, 6.5));
            wellOnly = player(OUTSIDE);
            wardOnly = player(OUTSIDE);
            overlap = player(OUTSIDE);
            enemy = player(new Vec3(6.5, 1, 7.5));
            for (ServerPlayer p : players) if (p != enemy) board.addPlayerToTeam(p.getScoreboardName(), team);
            // A second maximum-health scale catches accidentally hard-coded Minecraft HP conversion.
            overlap.getAttribute(Attributes.MAX_HEALTH).setBaseValue(40);
            overlap.setHealth(overlap.getMaxHealth());
            for (ServerPlayer p : List.of(wellA, wellB)) {
                Guardians.data(p).setGuardianClass(GuardianClass.WARLOCK);
                Guardians.data(p).setLoadout(GuardianClass.WARLOCK, WarlockAbilities.preset(Element.SOLAR)
                        .with(AbilitySlot.SUPER, WarlockExpandedSupers.WELL_OF_RADIANCE));
            }
            Guardians.data(ward).setGuardianClass(GuardianClass.TITAN);
            Guardians.data(ward).setLoadout(GuardianClass.TITAN, TitanAbilities.preset(Element.VOID)
                    .with(AbilitySlot.SUPER, TitanExpandedSupers.WARD_OF_DAWN));
            for (ServerPlayer p : List.of(wellA, wellB, ward)) {
                Guardians.runtime(p);
                Guardians.data(p).setSuperEnergy(1);
                check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK,
                        "Actual equipped Well/Ward cast accepted");
            }
            h.onEachTick(this::tick);
        }

        ServerPlayer player(Vec3 position) {
            ServerPlayer p = TestPlayers.create(h, position, -90, 0,
                    "W266" + UUID.randomUUID().toString().substring(0, 8));
            players.add(p);
            TestCleanup.register(h, () -> {
                SupportOvershield.cleanup(p);
                TestPlayers.remove(p);
                p.getAttribute(Attributes.MAX_ABSORPTION).removeModifier(FOREIGN);
            });
            p.setNoGravity(true);
            p.setOnGround(true);
            return p;
        }

        List<ServerPlayer> recipients() { return List.of(wellOnly, wardOnly, overlap); }
        void move(ServerPlayer p, Vec3 position) { p.setPos(h.absoluteVec(position)); }
        void after(int ticks, Runnable action) { tasks.add(new Task(h.getLevel().getGameTime() + ticks, action)); }

        void assertFieldsAfterCast() {
            for (ServerPlayer p : List.of(wellA, wellB, ward)) {
                check(h, !AbilityService.inSuper(p) && !SuperCamera.active(p)
                                && Guardians.runtime(p).superSession == null,
                        "Cast session and camera have ended while support remains usable");
                check(h, p.getAbsorptionAmount() > 0, "Caster receives support absorption after the real cast");
            }
            check(h, WarlockExpandedSupers.status(wellA).contains("well=true")
                            && WarlockExpandedSupers.status(wellB).contains("well=true")
                            && TitanExpandedSupers.status(ward).contains("ward=true"),
                    "Both independent Wells and Ward remain alive within their 600-tick field lifetime");
            check(h, !WarlockExpandedSupers.inWell(enemy) && !TitanExpandedSupers.inWard(enemy),
                    "Enemy standing in the overlapping fields is not a member");
        }

        void enter() {
            move(wellOnly, new Vec3(3.5, 1, 7.5));
            move(wardOnly, new Vec3(10.5, 1, 6.5));
            move(overlap, new Vec3(6.5, 1, 6.5));
            check(h, WarlockExpandedSupers.inWell(wellOnly) && !TitanExpandedSupers.inWard(wellOnly),
                    "Well-only recipient is inside Wells but outside Ward");
            check(h, TitanExpandedSupers.inWard(wardOnly) && !WarlockExpandedSupers.inWell(wardOnly),
                    "Ward-only recipient is inside Ward but outside Wells");
            check(h, WarlockExpandedSupers.inWell(overlap) && TitanExpandedSupers.inWard(overlap),
                    "Mixed recipient is inside both kinds of live field");
        }

        void tick() {
            for (ServerPlayer p : players) {
                if (SuperCamera.active(p)) {
                    int rotations = SuperCamera.rotations(p);
                    p.connection.handleMovePlayer(new ServerboundMovePlayerPacket.Rot(
                            p.getYRot(), p.getXRot(), p.onGround(), false));
                    check(h, SuperCamera.rotations(p) == rotations + 1, "Native rotation heartbeat refreshes cast camera");
                }
                AbilityService.tickPlayer(p);
            }
            TitanExpandedSupers.tick(h.getLevel().getServer());
            WarlockExpandedSupers.tick(h.getLevel().getServer());
            players.forEach(TestPlayers::drain);
            for (Task task : List.copyOf(tasks)) if (h.getLevel().getGameTime() >= task.due()) {
                tasks.remove(task);
                check(h, h.getLevel().getGameTime() == task.due(), "Callback reached its real world-clock deadline");
                task.action().run();
            }
        }
    }
}
