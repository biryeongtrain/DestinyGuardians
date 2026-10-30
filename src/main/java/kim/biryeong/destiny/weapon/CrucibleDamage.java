package kim.biryeong.destiny.weapon;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;

/** D2 displayed HP is normalized to the guardian health bar (230 -> maxHealth).
 * Per-target evaluation keeps a single shot's PvE and PvP contacts independent.
 * W267 explicitly documented approximations fill source gaps; unknown future rows retain local values. */
public final class CrucibleDamage {
    public static final double GUARDIAN_HP = 230;
    private CrucibleDamage() {}
    public static float base(WeaponCatalog.Entry entry, LivingEntity target, float local) {
        if (!(target instanceof ServerPlayer)) return local;
        var row = CrucibleWeaponDamage.find(entry.id());
        if (row.isEmpty()) return local;
        float original = WeaponProfile.forEntry(entry).damage();
        return (float)(local / original * row.get().body() * target.getMaxHealth() / GUARDIAN_HP);
    }
    public static double precision(WeaponCatalog.Entry entry, LivingEntity target, double local) {
        if (!(target instanceof ServerPlayer)) return local;
        return CrucibleWeaponDamage.find(entry.id()).map(r -> r.precision() / r.body()).orElse(local);
    }
    public static WeaponBallistics.Profile ballistics(WeaponCatalog.Entry entry, LivingEntity target,
                                                       WeaponBallistics.Profile original) {
        return new WeaponBallistics.Profile(original.start(), original.end(), original.floor(),
                precision(entry, target, original.precision()));
    }
    public static float melee(WeaponCatalog.Entry entry, LivingEntity target, float local) {
        if (!(target instanceof ServerPlayer)) return local;
        // Sword contacts retain their paid combo and energy-dependent heavy multipliers.
        if (entry.family().equals("sword")) return base(entry, target, local);
        var row = CrucibleWeaponDamage.find(entry.id());
        if (row.isEmpty() || row.get().melee().isEmpty()) return local;
        // Glaive's old local 7/14 combo is not a D2 double-damage third hit.
        return (float)(row.get().melee().getAsDouble() * target.getMaxHealth() / GUARDIAN_HP);
    }
    public static float payload(WeaponCatalog.Entry entry, LivingEntity target, float localBase) {
        float value = base(entry, target, localBase);
        // PvP explosive payload redistributes damage; the PvE +30% blast bonus does not apply.
        return target instanceof ServerPlayer ? value * .5f : PayloadProfile.explosion(value);
    }
}
