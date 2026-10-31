package kim.biryeong.destiny.weapon;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;

/** D2 displayed HP is normalized to the guardian health bar (230 -> maxHealth).
 * W286 user-authored special/heavy budgets override source rows in 20-HP units.
 * Per-target evaluation keeps a single shot's PvE and PvP contacts independent.
 * W267 explicitly documented approximations fill source gaps; unknown future rows retain local values. */
public final class CrucibleDamage {
    public static final double GUARDIAN_HP = 230;
    private CrucibleDamage() {}
    public static float base(WeaponCatalog.Entry entry, LivingEntity target, float local) {
        if (!(target instanceof ServerPlayer)) return local;
        var balance = CruciblePowerBalance.find(entry);
        if (balance.isPresent()) return (float)(local / WeaponProfile.forEntry(entry).damage()
                * balance.get().body() * target.getMaxHealth() / CruciblePowerBalance.HEALTH);
        var row = CrucibleWeaponDamage.find(entry.id());
        if (row.isEmpty()) return local;
        float original = WeaponProfile.forEntry(entry).damage();
        return (float)(local / original * row.get().body() * target.getMaxHealth() / GUARDIAN_HP);
    }
    public static double precision(WeaponCatalog.Entry entry, LivingEntity target, double local) {
        if (!(target instanceof ServerPlayer)) return local;
        var balance = CruciblePowerBalance.find(entry);
        if (balance.isPresent()) return balance.get().head() / balance.get().body();
        return CrucibleWeaponDamage.find(entry.id()).map(r -> r.precision() / r.body()).orElse(local);
    }
    public static WeaponBallistics.Profile ballistics(WeaponCatalog.Entry entry, LivingEntity target,
                                                       WeaponBallistics.Profile original) {
        // A complete pellet pattern remains lethal through five blocks, including low-range frames.
        double start = original.start(), end = original.end();
        if (target instanceof ServerPlayer && entry.family().equals("shotgun")
                && !entry.frame().equals("pinpoint_slug") && start < 5) {
            end += 5 - start;
            start = 5;
        }
        return new WeaponBallistics.Profile(start, end, original.floor(),
                precision(entry, target, original.precision()));
    }
    public static float melee(WeaponCatalog.Entry entry, LivingEntity target, float local) {
        if (!(target instanceof ServerPlayer)) return local;
        // Sword contacts retain their paid combo and energy-dependent heavy multipliers.
        if (entry.family().equals("sword")) return base(entry, target, local);
        var balance = CruciblePowerBalance.find(entry);
        if (balance.isPresent() && balance.get().melee() > 0)
            return (float)(balance.get().melee() * target.getMaxHealth() / CruciblePowerBalance.HEALTH);
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
    /** A direct PvP explosive contact receives its full budget; nearby targets still get radial falloff. */
    public static float blast(WeaponCatalog.Entry entry, LivingEntity target, float local, boolean direct, float falloff) {
        return base(entry, target, local) * (direct && target instanceof ServerPlayer ? 1 : falloff);
    }
    /** Wave and physical contact each use the PvP projectile budget; runtime deduplicates the same victim. */
    public static float wave(WeaponCatalog.Entry entry, LivingEntity target, float local, float multiplier) {
        return base(entry, target, local) * (target instanceof ServerPlayer ? 1 : multiplier);
    }
}
