package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.sound.EnemyHeadburstSounds;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import java.util.OptionalDouble;

/**
 * What combat, perks and sound need to know about an enemy that a strike's director owns, whichever strike it is.
 * Implemented by the strike's enemy entity; combat never names a strike's classes.
 */
public interface StrikeCombatant {
    /** Multipart enemies (a walker's legs, hull and core) credit perks, rewards and kills to one living actor. */
    default LivingEntity damageOwner() { return (LivingEntity) this; }
    /** The hit-point pool the player actually works through when it is not the entity's own health; empty otherwise. */
    default OptionalDouble damagePool() { return OptionalDouble.empty(); }
    /** Precision region test, called before the generic humanoid-head branch. No damage multiplication here. */
    boolean precisionAt(Vec3 point);
    CombatantRank rank();
    /** Shield type for matching elemental damage; null when this enemy has no combatant shield. */
    CombatantShields.Type shieldType();
    /** Headburst vocal layer, or null when none applies (multipart pieces, enemies without a family). */
    EnemyHeadburstSounds.Family headburstFamily();
}
