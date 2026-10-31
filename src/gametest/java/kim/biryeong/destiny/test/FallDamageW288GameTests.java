package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.phys.Vec3;

public final class FallDamageW288GameTests {
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.hunter(h, Element.ARC, new Vec3(2, 1, 2), 0, 0);
        TestCleanup.register(h, () -> TestPlayers.remove(p));
        return p;
    }

    private static void fall(GameTestHelper h, LivingEntity entity, double distance, float expected) {
        entity.setHealth(entity.getMaxHealth());
        entity.damageCooldownTime = 0;
        float before = entity.getHealth();
        entity.causeFallDamage(distance, 1, entity.damageSources().fall());
        float loss = before - entity.getHealth();
        h.assertTrue(Math.abs(loss - expected) < .001f,
                Component.literal(distance + " block fall: expected " + expected + ", actual " + loss));
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w288_fall")
    public void allPlayerClassesBeginTakingDamageAtTenBlocks(GameTestHelper h) {
        var p = player(h);
        for (var guardianClass : GuardianClass.values()) {
            Guardians.data(p).setGuardianClass(guardianClass);
            fall(h, p, 4, 0);
            fall(h, p, 7, 0);
            fall(h, p, 9.99, 0);
            fall(h, p, 10, 1);
            fall(h, p, 11, 2);
            fall(h, p, 15, 6);
        }
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w288_fall")
    public void nativeBonusesMultipliersAndMobThresholdArePreserved(GameTestHelper h) {
        var p = player(h);
        p.getAttribute(Attributes.SAFE_FALL_DISTANCE).setBaseValue(5);
        fall(h, p, 11, 0);
        fall(h, p, 12, 1);
        p.getAttribute(Attributes.SAFE_FALL_DISTANCE).setBaseValue(3);
        p.getAttribute(Attributes.FALL_DAMAGE_MULTIPLIER).setBaseValue(.5);
        fall(h, p, 15, 3);
        p.getAttribute(Attributes.FALL_DAMAGE_MULTIPLIER).setBaseValue(0);
        fall(h, p, 30, 0);
        var mob = h.spawn(EntityTypes.HUSK, new BlockPos(4, 1, 4));
        fall(h, mob, 3, 0);
        fall(h, mob, 4, 1);
        fall(h, mob, 10, 7);
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w288_no_fall")
    public void worldsWithFallDamageDisabledRemainSafe(GameTestHelper h) {
        fall(h, player(h), 30, 0);
        h.succeed();
    }
}
