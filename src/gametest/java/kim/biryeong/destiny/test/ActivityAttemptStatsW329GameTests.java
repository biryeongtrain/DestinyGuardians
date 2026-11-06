package kim.biryeong.destiny.test;

import kim.biryeong.destiny.activity.ActivityAttemptStats;
import kim.biryeong.destiny.activity.presentation.ActivityFailurePresentation;
import kim.biryeong.destiny.combat.*;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public final class ActivityAttemptStatsW329GameTests {
    private static void check(GameTestHelper h, boolean ok, String why) { h.assertTrue(ok, Component.literal(why)); }
    @GameTest(structure="destiny-test:floor", maxTicks=40, environment="destiny-test:w90_isolated")
    public void actualAppliedLossCapsOverkillAndFreezesRealTableWithSelfHighlight(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(2, 1, 2), 0, 0); UUID activity = UUID.randomUUID();
        var stats = new ActivityAttemptStats(activity); stats.reset(1, "정제소", List.of(new ActivityAttemptStats.Member(player.getUUID(), player.getScoreboardName(), ActivityAttemptStats.Presence.PRESENT)));
        var enemy = new Husk(net.minecraft.world.entity.EntityTypes.HUSK, h.getLevel()); enemy.setPos(player.position().add(2, 0, 0));
        enemy.setNoAi(true); enemy.setHealth(10);
        enemy.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_ABSORPTION).setBaseValue(4);
        enemy.setAbsorptionAmount(4); h.getLevel().addFreshEntity(enemy);
        var failure = new ActivityFailurePresentation(activity);
        var listener = CombatDamageEvents.subscribe(e -> {
            if (e.source() == player && e.recipient() == enemy)
                stats.damage(stats.token(), player.getUUID(), enemy.getUUID(), e.damage(), e.killed(), false);
        });
        TestCleanup.register(h, () -> { try { listener.close(); } catch (Exception ignored) { } failure.close(); stats.close(); enemy.discard(); TestPlayers.remove(player); });
        check(h, enemy.getHealth() == 10 && enemy.getAbsorptionAmount() == 4 && Combat.damagePool(enemy) == 14,
                "Fixture requires actual10HP+4absorption; health=" + enemy.getHealth() + " absorption=" + enemy.getAbsorptionAmount());
        Combat.damage(h.getLevel(), player, enemy, 1000, Element.KINETIC);
        var row = stats.snapshot().rows().getFirst();
        check(h, row.kills() == 1 && Math.abs(row.damage() - 14) < .001,
                "Actual HP+shield loss14 caps a1000-damage overkill; observed=" + row.damage() + " kills=" + row.kills()
                        + " remainingHealth=" + enemy.getHealth() + " remainingAbsorption=" + enemy.getAbsorptionAmount());
        var frozen = stats.freeze(stats.token());
        failure.scope(1, "RF", true); check(h, failure.beginWipe(1), "Wipe begins"); failure.results(frozen);
        for (int n = 0; n < 30; n++) { failure.tick(1, true); failure.render(List.of(player), p -> false, n, 0); }
        String prefix = "destiny:activity_failure/" + activity + "/";
        check(h, DisplayHud.getHud(player, prefix + "damage_0").getExtraData("state").toString().startsWith("14:"), "Real table shows observed loss");
        check(h, DisplayHud.getHud(player, prefix + "deaths_0").getExtraData("state").toString().startsWith("0:"), "No actual down event means zero deaths; no fabricated death statistic");
        check(h, DisplayHud.getHud(player, prefix + "self_0") != null, "Recipient sees own gold row marker");
        check(h, !stats.damage(stats.token(), player.getUUID(), UUID.randomUUID(), 100, true, true)
                && !stats.death(stats.token(), player.getUUID(), 2) && stats.snapshot().equals(frozen), "Late damage/death cannot change frozen table");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=30, environment="destiny-test:w90_isolated")
    public void observerFailureDetachesItselfWithoutBlockingDamageOrOtherObservers(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(2, 1, 2), 0, 0);
        var enemy = new Husk(net.minecraft.world.entity.EntityTypes.HUSK, h.getLevel()); enemy.setPos(player.position().add(2, 0, 0)); enemy.setNoAi(true); h.getLevel().addFreshEntity(enemy);
        var brokenCalls = new AtomicInteger(); var healthyCalls = new AtomicInteger();
        var broken = CombatDamageEvents.subscribe(e -> { if (e.source() == player) { brokenCalls.incrementAndGet(); throw new IllegalStateException("W329 observer failure fixture"); } });
        var healthy = CombatDamageEvents.subscribe(e -> { if (e.source() == player) healthyCalls.incrementAndGet(); });
        TestCleanup.register(h, () -> { try { broken.close(); healthy.close(); } catch (Exception ignored) { } enemy.discard(); TestPlayers.remove(player); });
        float before = enemy.getHealth(); Combat.damage(h.getLevel(), player, enemy, 2, Element.KINETIC); Combat.damage(h.getLevel(), player, enemy, 2, Element.KINETIC);
        check(h, enemy.getHealth() < before && brokenCalls.get() == 1 && healthyCalls.get() == 2, "Only failed observer detaches; actual damage and other observations continue");
        h.succeed();
    }
}
