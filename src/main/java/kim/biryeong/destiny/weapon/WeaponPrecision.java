package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

/** Explicit humanoid weakspots, not a blanket headshot rule for arbitrary Minecraft mobs. */
public final class WeaponPrecision {
    public static final TagKey<EntityType<?>> HUMANOIDS = TagKey.create(Registries.ENTITY_TYPE,
            DestinyGuardians.id("weapon_precision_humanoids"));
    private WeaponPrecision() {}
    public static boolean critical(LivingEntity target, Vec3 from, Vec3 reportedHit, double multiplier) {
        // Guardian shields/overshields are not PvE combatant shields: headshots still crit.
        boolean guardian = target instanceof net.minecraft.server.level.ServerPlayer;
        if (multiplier <= 1 || !guardian && (target.getAbsorptionAmount() > 0
                || !target.getType().builtInRegistryHolder().is(HUMANOIDS))) return false;
        Vec3 direction = reportedHit.subtract(from);
        if (direction.lengthSqr() < 1e-10) return false;
        var box = target.getBoundingBox();
        // ProjectileUtil reports an inflated box. Classify the actual body's first surface;
        // grazing only the aim-assist margin can hit, but cannot earn a precision bonus.
        if (box.contains(from)) return false;
        return box.clip(from, reportedHit.add(direction.normalize().scale(.25)))
                .filter(point -> point.y >= box.maxY - box.getYsize() * .25).isPresent();
    }
}
