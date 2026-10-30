package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.ability.warlock.WarlockExpandedSupers;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.weapon.AmmoGeneration;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import net.minecraft.world.entity.player.Player;

/** No timed potion or permanent attribute: reduction belongs to the exact accepted session/field. */
public final class SuperDamageResistance {
    public record Binding(SuperSession session, Identifier ability, ServerLevel level) { }
    private SuperDamageResistance() { }

    public static float modifyIncoming(ServerPlayer player, DamageSource source, float amount) {
        if (!Float.isFinite(amount) || amount <= 0 || !player.isAlive() || player.isRemoved()
                || player.isSpectator() || player.hasDisconnected()
                || source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)
                || !(source.getEntity() instanceof LivingEntity attacker) || attacker == player) return amount;
        boolean pvp = attacker instanceof Player;
        double cast = 0;
        var runtime = Guardians.runtimeIfPresent(player).orElse(null);
        if (runtime != null) {
            var binding = runtime.superResistance;
            if (binding != null && binding.ability() != null && runtime.superSession != null && binding.level() == player.level()
                    && runtime.superSession == binding.session() && binding.session().damageResistanceActive())
                cast = SuperResistanceProfile.cast(binding.ability().getPath(), pvp);
        }
        double field = 0;
        if (WarlockExpandedSupers.inWell(player)) {
            boolean primary = source instanceof GuardianDamageSource shot && shot.kind() == AmmoGeneration.Kind.PRIMARY;
            boolean boss = attacker instanceof WitherBoss || attacker instanceof EnderDragon
                    || attacker.entityTags().contains("destiny_boss");
            field = SuperResistanceProfile.well(pvp, primary, boss);
        }
        // Independent sources stack multiplicatively; overlapping Wells only contribute once.
        return (float)(amount * (1 - cast) * (1 - field));
    }
}
