package kim.biryeong.destiny.test;

import com.mojang.serialization.JsonOps;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.resources.RegistryOps;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.attributes.RangedAttribute;
import net.minecraft.world.entity.monster.zombie.Zombie;

public final class MaxHealthGameTests {
    private static void check(GameTestHelper h, boolean value, String text) {
        h.assertTrue(value, Component.literal(text));
    }
    @GameTest(structure="destiny-test:floor", maxTicks=20, environment="destiny-test:w90_isolated")
    public void raisedAttributeRangeKeepsBossHealthAndSerializedValues(GameTestHelper h) {
        var max = (RangedAttribute) Attributes.MAX_HEALTH.value();
        check(h, max.getMaxValue() == (double) Float.MAX_VALUE, "Mixin lifts max_health to finite health storage range");
        check(h, max.getMinValue() == 1 && max.getDefaultValue() == 20, "Default and minimum health remain unchanged");
        check(h, ((RangedAttribute) Attributes.ARMOR.value()).getMaxValue() == 30, "Unrelated attributes retain their limits");
        var entity = new Zombie(EntityTypes.ZOMBIE, h.getLevel());
        for (double hp : new double[]{1600, 2200, 100000}) {
            entity.getAttribute(Attributes.MAX_HEALTH).setBaseValue(hp);
            entity.setHealth((float) hp);
            check(h, entity.getMaxHealth() == hp && entity.getHealth() == hp, "Real entity health is not capped at1024");
            var ops = RegistryOps.create(JsonOps.INSTANCE, h.getLevel().registryAccess());
            var encoded = AttributeInstance.Packed.CODEC.encodeStart(ops, entity.getAttribute(Attributes.MAX_HEALTH).pack()).getOrThrow();
            var restored = new Zombie(EntityTypes.ZOMBIE, h.getLevel());
            restored.getAttribute(Attributes.MAX_HEALTH).apply(AttributeInstance.Packed.CODEC.parse(ops, encoded).getOrThrow());
            check(h, restored.getMaxHealth() == hp, "Attribute codec preserves boss max health");
        }
        entity.getAttribute(Attributes.MAX_HEALTH).setBaseValue(2200);
        entity.setHealth(2200);
        entity.damageCooldownTime = 0;
        entity.hurtServer(h.getLevel(), entity.damageSources().generic(), 100);
        check(h, entity.getHealth() < 2200 && entity.getHealth() > 1024, "Real damage operates above former cap");
        entity.heal(500);
        check(h, entity.getHealth() == 2200, "Healing clamps to new actual max health");
        h.succeed();
    }
}
