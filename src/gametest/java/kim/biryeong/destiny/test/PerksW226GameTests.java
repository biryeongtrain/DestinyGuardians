package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Actual paid-damage and charge-acceptance checks; no per-stat test matrix or native-input claim. */
public final class PerksW226GameTests {
    private static void check(GameTestHelper h, boolean ok, String why) { h.assertTrue(ok, Component.literal(why)); }
    private static final class Fixture {
        final GameTestHelper h;
        final ServerPlayer p;
        final ItemStack gun;
        final WeaponCatalog.Entry entry;
        final WeaponProfile profile;
        final List<Husk> targets = new ArrayList<>();
        Fixture(GameTestHelper h, String weapon, String perk) {
            this.h = h;
            p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, 6), -90, 0,
                    "W226_" + UUID.randomUUID().toString().substring(0, 8));
            Guardians.runtime(p);
            p.setNoGravity(true); p.setOnGround(true); p.setAttached(WeaponLoadout.ENABLED, false);
            entry = WeaponCatalog.find(weapon).orElseThrow(); profile = WeaponProfile.forEntry(entry);
            gun = WeaponItems.create(entry);
            check(h, WeaponPerks.select(gun, perk), "Exact supported base socket");
            WeaponItems.save(gun, new WeaponMagazine(profile, profile.magazine(), profile.reserve()));
            int slot = WeaponCharacteristics.of(entry).slot().hotbar();
            p.getInventory().setItem(slot, gun); p.getInventory().setSelectedSlot(slot); tick();
            TestCleanup.register(h, () -> { targets.forEach(Husk::discard); WeaponRuntime.cleanup(p); TestPlayers.remove(p); });
        }
        void tick() { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); }
        void face() { p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0); }
        int rounds() { return WeaponItems.magazine(gun, profile).rounds(); }
        Husk target(double x, double y, double z) {
            var t = h.spawn(EntityTypes.HUSK, new Vec3(x, y, z)); targets.add(t);
            t.setNoAi(true); t.setNoGravity(true);
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
            t.setHealth(1000); return t;
        }
        float shot(Husk target) {
            target.setHealth(1000); target.damageCooldownTime = 0; face();
            // Reproduce a near-axis dispersion draw without altering the live accuracy cone.
            p.getRandom().setSeed(0x5DEECE66DL);
            int before = rounds();
            check(h, WeaponRuntime.beginUse(p), "Actual shot accepted"); WeaponRuntime.releaseUse(p, gun);
            check(h, rounds() == before - 1, "Exactly one paid round");
            return 1000 - target.getHealth();
        }
    }
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=120)
    public void gutshotAppliesOnlyToActualAdsBodyHitsAndLeavesPrecisionUnchanged(GameTestHelper h) {
        var f = new Fixture(h, "ammit_ar2", "gutshot_straight");
        var target = f.target(8.5, 1.8, 6);
        check(h, WeaponAiming.toggle(f.p), "Actual left-click ADS input accepted"); f.tick(); h.onEachTick(f::tick);
        // Register all three observations before GameTestInfo begins iterating callbacks.
        h.runAfterDelay(24, () -> {
            check(h, WeaponAiming.aimInput(f.p) && WeaponAiming.progress(f.p) == 1, "Accepted complete ADS");
            float adsBody = f.shot(target);
            check(h, Math.abs(adsBody - f.profile.damage() * 1.2) < .1, "Paid ADS body component is amplified");
            f.p.setShiftKeyDown(false); WeaponAiming.releasedAim(f.p);
        });
        h.runAfterDelay(48, () -> {
            float hipBody = f.shot(target);
            check(h, Math.abs(hipBody - f.profile.damage()) < .1, "Released ADS cannot retain body bonus");
            target.setPos(h.absoluteVec(new Vec3(8.5, 1, 6)));
            check(h, WeaponAiming.toggle(f.p), "Actual left-click ADS input accepted");
        });
        h.runAfterDelay(72, () -> {
            float precision = f.shot(target);
            double plain = f.profile.damage() * WeaponBallistics.of(f.entry).precision();
            check(h, Math.abs(precision - plain) < .1, "ADS precision component remains unamplified"); h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=130)
    public void corneredCannotRetimeAChargeAlreadyAcceptedBeforeEnemyEntry(GameTestHelper h) {
        var f = new Fixture(h, "dream_breaker", "cornered");
        f.target(3, 1, 11); // One actual enemy does not activate the perk.
        f.tick(); int before = f.rounds();
        check(h, !WeaponCornered.active(f.p), "Exactly one nearby enemy leaves initial charge unbuffed");
        check(h, WeaponRuntime.heartbeatUse(f.p), "Actual production trigger starts unbuffed charge");
        int duration = f.profile.chargeTicks(); int faster = Math.max(1, (int)Math.ceil(duration * .85));
        for (int i = 1; i <= duration; i++) h.runAfterDelay(i, () -> {
            f.face(); WeaponRuntime.heartbeatUse(f.p); WeaponRuntime.continueUse(f.p); f.tick();
        });
        h.runAfterDelay(2, () -> { f.target(5, 1, 11); f.tick(); });
        h.runAfterDelay(faster, () -> check(h, f.rounds() == before, "New proximity cannot shorten an accepted charge"));
        h.runAfterDelay(duration, () -> {
            f.face(); WeaponRuntime.heartbeatUse(f.p); WeaponRuntime.continueUse(f.p); f.tick();
            check(h, f.rounds() == before - 1, "Original charge deadline pays exactly once");
            WeaponRuntime.releaseUse(f.p, f.gun);
            var accepted = WeaponCornered.charge(f.p, f.entry, f.profile);
            check(h, accepted.chargeTicks() < duration, "Subsequent charge accepts the live proximity effect");
            f.p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0)); TestPlayers.drain(f.p);
            check(h, WeaponCornered.charge(f.p, f.entry, f.profile).equals(f.profile), "Actual stow invalidates the original held source");
            h.succeed();
        });
    }
}
