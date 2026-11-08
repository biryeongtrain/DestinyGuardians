package kim.biryeong.destiny.combat;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import net.minecraft.world.entity.player.Player;

/** Shared combatant tier taxonomy (W322), consistent with the tagged Vorpal/Unrelenting policy.
 * Explicit local mapping: tags destiny_boss/destiny_vehicle/destiny_miniboss/destiny_elite; vanilla
 * Wither/Ender Dragon bosses; Devils' Lair kinds; shielded Fallen are elites. Health never infers rank.
 */
public enum CombatantRank {
    RANK_AND_FILE, ELITE, MINIBOSS, BOSS, VEHICLE, GUARDIAN;

    /** Elite or stronger combatant ("more powerful" in perk text). Guardians are separate. */
    public boolean powerful() { return this == ELITE || this == MINIBOSS || this == BOSS || this == VEHICLE; }

    public static CombatantRank of(LivingEntity target) {
        if (target == null) return null;
        if (target instanceof Player) return GUARDIAN;
        var tags = target.entityTags();
        if (target instanceof WitherBoss || target instanceof EnderDragon || tags.contains("destiny_boss")) return BOSS;
        if (tags.contains("destiny_vehicle")) return VEHICLE;
        if (tags.contains("destiny_miniboss")) return MINIBOSS;
        if (tags.contains("destiny_elite")) return ELITE;
        if (target instanceof StrikeCombatant combatant) return combatant.rank();
        if (target instanceof kim.biryeong.destiny.campaign.fallen.FallenMob
                && target.getAttributeBaseValue(Attributes.MAX_ABSORPTION) > 0) return ELITE;
        return target instanceof Mob ? RANK_AND_FILE : null;
    }
}
