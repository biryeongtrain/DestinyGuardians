package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.fx.HunterVfx;
import kim.biryeong.destiny.fx.WeaponDamageNumbers;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.sound.DestinySounds;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import java.util.Comparator;

/** Ace's precision-final-blow solar blast, not recursive weapon damage or Memento kill credit.
 * Radius/full-damage core sourced; 15 Minecraft HP is authored PvE policy; linear falloff to the sourced .2 PvE endpoint is local.
 */
public final class WeaponFirefly {
    public static final double RADIUS = 7.5, CORE = 3.75;
    public static final float DAMAGE = 15;
    public static final int MAX_TARGETS = 128;
    private WeaponFirefly() {}
    public static float damageAt(double distance) {
        if (!Double.isFinite(distance) || distance < 0 || distance > RADIUS) return 0;
        return DAMAGE * (float)(distance <= CORE ? 1 : 1 - .8 * (distance - CORE) / (RADIUS - CORE));
    }
    static void explode(ServerPlayer owner, LivingEntity corpse) {
        var level = owner.level(); var center = corpse.getBoundingBox().getCenter();
        if (!level.hasChunkAt(BlockPos.containing(center))) return;
        int admitted = 0;
        for (var target : level.getEntitiesOfClass(LivingEntity.class, AABB.ofSize(center, RADIUS * 2 + 1e-6, RADIUS * 2 + 1e-6, RADIUS * 2 + 1e-6),
                e -> Combat.isEnemy(owner, e) && e.getBoundingBox().getCenter().distanceToSqr(center) <= RADIUS * RADIUS)
                .stream().sorted(Comparator.comparingDouble(e -> e.getBoundingBox().getCenter().distanceToSqr(center))).toList()) {
            if (target == corpse || owner.isAlliedTo(target) || target instanceof TamableAnimal tame && tame.isTame()) continue;
            var point = target.getBoundingBox().getCenter();
            if (!level.hasChunkAt(BlockPos.containing(point)) || !WeaponWavefront.loadedSegment(level,center,point)) continue;
            var wall = level.clip(new ClipContext(center, point, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, owner));
            if (wall.getType() != HitResult.Type.MISS && center.distanceToSqr(wall.getLocation()) + 1e-6 < center.distanceToSqr(point)) continue;
            if (admitted++ >= MAX_TARGETS) break;
            float before = target.getHealth() + target.getAbsorptionAmount();
            boolean killed = Combat.damage(level, owner, target, damageAt(center.distanceTo(point)), Element.SOLAR,
                    AmmoGeneration.weapon(WeaponCatalog.find("ace_of_spades").orElseThrow()));
            float actual = before - target.getHealth() - target.getAbsorptionAmount();
            if (Float.isFinite(actual) && actual > 0) {
                kim.biryeong.destiny.hud.WeaponHitHud.confirm(owner, actual, killed);
                WeaponDamageNumbers.confirm(owner, level, point, actual, false);
            }
        }
        Fx.burst(level, center, Element.SOLAR, 28, .4);
        Fx.ring(level, center, RADIUS * .55, 0xF79254, 32);
        HunterVfx.play(owner, level, center, HunterVfx.Kind.SOLAR_BURST, 1.5, 12);
        // Documented supplied-archive surrogate, not a falsely named exact Firefly recording.
        DestinySounds.at(level, center, "hunter.solar.grenade.impact", .65f);
    }
}
