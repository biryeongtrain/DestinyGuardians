package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.guardian.Loadout;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.Map;

/**
 * Server damage-path/lifecycle coverage, not a resistance-table test.
 * PvP uses direct playerAttack -> hurtServer: no Combat.damage/canFight or match fixture.
 * Requires W265's default SuperSession.damageResistanceActive() when integrated.
 */
public final class SuperResistanceW265GameTests {
    private static final float HIT = 10f, EPS = 0.001f;

    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }

    private static void same(GameTestHelper h, float actual, float expected, String message) {
        check(h, Math.abs(actual - expected) < EPS, message + ": actual=" + actual + " expected=" + expected);
    }

    private static ServerPlayer player(GameTestHelper h, String name, double x) {
        var p = TestPlayers.hunter(h, Element.ARC, new Vec3(x, 1, 6.5), -90, 0, name);
        TestCleanup.register(h, () -> TestPlayers.remove(p));
        p.getAttribute(Attributes.MAX_HEALTH).setBaseValue(100);
        p.getAttribute(Attributes.MAX_ABSORPTION).setBaseValue(20);
        p.getAttribute(Attributes.ARMOR).setBaseValue(0);
        p.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        p.setHealth(p.getMaxHealth());
        p.setOnGround(true);
        return p;
    }

    private static Husk mob(GameTestHelper h) {
        var mob = EntityTypes.HUSK.create(h.getLevel(), net.minecraft.world.entity.EntitySpawnReason.COMMAND);
        check(h, mob != null, "Control mob created");
        mob.setPos(h.absoluteVec(new Vec3(6.5, 1, 6.5)));
        check(h, h.getLevel().addFreshEntity(mob), "Control mob added to actual world");
        TestCleanup.register(h, mob::discard);
        mob.setNoAi(true);
        mob.setNoGravity(true);
        mob.getAttribute(Attributes.ARMOR).setBaseValue(0);
        return mob;
    }

    /** Reset native immunity between independent hits; always measure real HP + absorption. */
    private static float hit(GameTestHelper h, LivingEntity target, DamageSource source, float absorption) {
        target.setHealth(target.getMaxHealth());
        target.setAbsorptionAmount(absorption);
        target.damageCooldownTime = 0;
        float before = target.getHealth() + target.getAbsorptionAmount();
        target.hurtServer((net.minecraft.server.level.ServerLevel) target.level(), source, HIT);
        float loss = before - target.getHealth() - target.getAbsorptionAmount();
        check(h, loss > 0, "Control hit must reach native health/absorption: " + source);
        return loss;
    }

    private static void equip(ServerPlayer p, Element element) {
        Guardians.data(p).setLoadout(GuardianClass.HUNTER, HunterAbilities.preset(element));
    }

    private static final class Session implements SuperSession {
        boolean active = true;
        @Override public boolean tick() { return true; }
        @Override public void primary() { }
        @Override public void end() { active = false; }
        @Override public float remaining() { return 1; }
        @Override public boolean damageResistanceActive() { return active; }
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated", maxTicks = 20)
    public void snapshotIdentityActivityAndWorldGateActualPlayerDamage(GameTestHelper h) {
        var p = player(h, "W265Snapshot", 2.5);
        var attacker = player(h, "W265Attacker", 4.5);
        var source = p.damageSources().playerAttack(attacker);
        float plain = hit(h, p, source, 0);
        var first = new Session();
        AbilityService.startSuper(p, first);
        float arc = hit(h, p, source, 0);
        // One representative native hit detects missing/doubled reduction; no profile helper oracle.
        same(h, arc, plain * .47f, "Arc PvP reduction is applied exactly once by hurtServer");
        equip(p, Element.SOLAR);
        same(h, hit(h, p, source, 0), arc, "Changing equipped SUPER preserves the accepted Arc snapshot");
        var replacement = new Session();
        AbilityService.startSuper(p, replacement);
        same(h, hit(h, p, source, 0), plain, "Replacement snapshots Golden Gun with no PvP resistance");

        equip(p, Element.ARC);
        var active = new Session();
        AbilityService.startSuper(p, active);
        same(h, hit(h, p, source, 0), arc, "Fresh start replaces the prior snapshot");
        active.active = false;
        same(h, hit(h, p, source, 0), plain, "Inactive session immediately stops resistance");
        active.active = true;
        same(h, hit(h, p, source, 0), arc, "Same live session can enter its protected phase");
        Guardians.runtime(p).superSession = new Session();
        same(h, hit(h, p, source, 0), plain, "Unbound session identity cannot inherit resistance");
        AbilityService.startSuper(p, new Session());
        Guardians.runtime(p).superSession = null;
        same(h, hit(h, p, source, 0), plain, "Direct runtime null turns resistance off without a tick");
        AbilityService.startSuper(p, new Session());
        AbilityService.endSuper(p);
        same(h, hit(h, p, source, 0), plain, "Explicit end restores native damage immediately");

        Guardians.data(p).setLoadout(GuardianClass.HUNTER, new Loadout(Map.of()));
        AbilityService.startSuper(p, new Session());
        same(h, hit(h, p, source, 0), plain, "No equipped SUPER cannot inherit the previous profile");
        AbilityService.endSuper(p);
        equip(p, Element.ARC);
        var bound = new Session();
        AbilityService.startSuper(p, bound);
        var original = p.level();
        var other = original.getServer().getLevel(original.dimension().equals(Level.NETHER)
                ? Level.OVERWORLD : Level.NETHER);
        check(h, other != null && other != original, "Fixture requires a distinct server level");
        // Unregistered TestPlayers: change level directly to isolate the stale binding guard,
        // deliberately retaining the session. This does not claim teleport-event coverage.
        try {
            p.setServerLevel(other);
            attacker.setServerLevel(other);
            check(h, Guardians.runtime(p).superSession == bound, "World guard is tested with the stale session retained");
            same(h, hit(h, p, p.damageSources().playerAttack(attacker), 0), plain,
                    "Old-world snapshot cannot protect a player in another level");
        } finally {
            p.setServerLevel(original);
            attacker.setServerLevel(original);
            AbilityService.endSuper(p);
        }
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w258_camera_clock", maxTicks = 1200)
    public void acceptedHunterProtectsHpAndAbsorptionButNotBypassOrFailedCast(GameTestHelper h) {
        h.startSequence().thenWaitUntil(() -> check(h, BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),
                "Waiting for the actual Hunter activation limb")).thenExecute(() -> {
            var p = player(h, "W265Hunter", 2.5);
            var attacker = mob(h);
            var attack = p.damageSources().mobAttack(attacker);
            var environment = p.damageSources().generic();
            var self = p.damageSources().playerAttack(p);
            var voidDamage = p.damageSources().fellOutOfWorld();
            var kill = p.damageSources().genericKill();
            float plain = hit(h, p, attack, 0);
            float ambient = hit(h, p, environment, 0), selfLoss = hit(h, p, self, 0);
            float voidLoss = hit(h, p, voidDamage, 0), killLoss = hit(h, p, kill, 0);
            float mobLoss = hit(h, attacker, attacker.damageSources().playerAttack(p), 0);
            Guardians.data(p).setSuperEnergy(1);
            check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK,
                    "One real equipped Hunter Arc activation is accepted");
            check(h, AbilityService.inSuper(p), "Accepted activation installs a real SuperSession");
            float protectedLoss = hit(h, p, attack, 0);
            same(h, protectedLoss, plain * .10f, "Native mob damage takes one PvE reduction");
            float absorption = protectedLoss / 2;
            same(h, hit(h, p, attack, absorption), protectedLoss, "Absorption and HP share one reduced hit");
            same(h, p.getAbsorptionAmount(), 0, "Reduced hit consumes the available absorption first");
            same(h, p.getMaxHealth() - p.getHealth(), protectedLoss - absorption,
                    "Only the reduced remainder reaches HP");
            same(h, hit(h, p, environment, 0), ambient, "Environmental damage is unchanged during super");
            same(h, hit(h, p, self, 0), selfLoss, "Self-attributed damage is unchanged during super");
            same(h, hit(h, p, voidDamage, 0), voidLoss, "Nonlethal vanilla void source bypasses resistance");
            same(h, hit(h, p, kill, 0), killLoss, "Nonlethal vanilla kill source bypasses resistance");
            same(h, hit(h, attacker, attacker.damageSources().playerAttack(p), 0), mobLoss,
                    "Caster's super never reduces damage to a mob target");
            AbilityService.endSuper(p);
            same(h, hit(h, p, attack, 0), plain, "Ending the actual Hunter session restores full mob damage");
            Guardians.data(p).setSuperEnergy(1);
            p.getAbilities().flying = true;
            try {
                check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.FAILED,
                        "Unsupported flying state rejects actual Hunter activation");
            } finally {
                p.getAbilities().flying = false;
            }
            check(h, !AbilityService.inSuper(p), "Failed activation leaves no super session");
            same(h, hit(h, p, attack, 0), plain, "Failed activation cannot retain resistance");
            h.succeed();
        });
    }
}
