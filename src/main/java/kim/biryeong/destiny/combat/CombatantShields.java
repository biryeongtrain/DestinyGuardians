package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.weapon.WeaponCharacteristics;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;

/** Shared combatant energy-shield taxonomy (W322). Absorption is the shield pool.
 * Explicit local policy: an entity tag {@code destiny_shield_<arc|solar|void|stasis|strand|barrier>} wins;
 * Fallen and Devils' Lair absorption shields default to Arc (Captains), Devils' Lair Wizards to Solar.
 * Generic vanilla absorption (golden apples, effects) is never a combatant shield. Guardian shields are not modelled.
 */
public final class CombatantShields {
    public enum Type { ARC, SOLAR, VOID, STASIS, STRAND, BARRIER }
    /** Pre-damage observation; compare with {@link #points} after the hit to detect a break. */
    public record Snapshot(Type type, float points) {
        public static final Snapshot NONE = new Snapshot(null, 0);
        public boolean shielded() { return type != null && points > 0; }
        public boolean matches(WeaponCharacteristics.Damage damage) { return shielded() && CombatantShields.matches(type, damage); }
        public boolean broken(LivingEntity target) {
            return shielded() && (!target.isAlive() || CombatantShields.points(target) <= 0);
        }
    }
    private CombatantShields() {}

    public static Snapshot snapshot(LivingEntity target) {
        var type = type(target);
        float points = points(target);
        return type == null || points <= 0 ? Snapshot.NONE : new Snapshot(type, points);
    }
    public static float points(LivingEntity target) {
        return target == null ? 0 : Math.max(0, target.getAbsorptionAmount());
    }
    public static Type type(LivingEntity target) {
        if (target == null || target instanceof Player) return null;
        for (var tag : target.entityTags()) {
            if (!tag.startsWith("destiny_shield_")) continue;
            switch (tag.substring("destiny_shield_".length())) {
                case "arc": return Type.ARC;
                case "solar": return Type.SOLAR;
                case "void": return Type.VOID;
                case "stasis": return Type.STASIS;
                case "strand": return Type.STRAND;
                case "barrier": return Type.BARRIER;
                default: break;
            }
        }
        if (target instanceof StrikeCombatant combatant) return combatant.shieldType();
        if (target instanceof kim.biryeong.destiny.campaign.fallen.FallenMob
                && target.getAttributeBaseValue(Attributes.MAX_ABSORPTION) > 0) return Type.ARC;
        return null;
    }
    /** Barrier shields are elementless: nothing matches them. */
    public static boolean matches(Type type, WeaponCharacteristics.Damage damage) {
        if (type == null || damage == null) return false;
        return switch (type) {
            case ARC -> damage == WeaponCharacteristics.Damage.ARC;
            case SOLAR -> damage == WeaponCharacteristics.Damage.SOLAR;
            case VOID -> damage == WeaponCharacteristics.Damage.VOID;
            case STASIS -> damage == WeaponCharacteristics.Damage.STASIS;
            case STRAND -> damage == WeaponCharacteristics.Damage.STRAND;
            case BARRIER -> false;
        };
    }
}
