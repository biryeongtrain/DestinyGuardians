package kim.biryeong.destiny.weapon;

import java.util.Map;
import java.util.HashMap;
import java.util.Optional;

/** W286 user-requested local PvP balance, in 20-HP guardian units, NOT DDC source data.
 * Damage budgets are computed once per weapon, not rebuilt for each contact.
 * Primary weapons and PvE retain their existing policies. */
public final class CruciblePowerBalance {
    public static final double HEALTH = 20;
    public record Damage(double body, double head, double melee) {}
    private static final Map<String, Damage> ALL = load();
    private CruciblePowerBalance() {}

    private static Map<String, Damage> load() {
        var result = new HashMap<String, Damage>();
        for (var entry : WeaponCatalog.all()) {
            var ammo = WeaponCharacteristics.of(entry).ammo();
            if (ammo == WeaponAmmoType.PRIMARY) continue;
            var source = CrucibleWeaponDamage.find(entry.id());
            double body = source.map(r -> r.body() * HEALTH / CrucibleDamage.GUARDIAN_HP)
                    .orElse((double) WeaponProfile.forEntry(entry).damage());
            double head = source.map(r -> r.precision() * HEALTH / CrucibleDamage.GUARDIAN_HP).orElse(body);
            Damage damage;
            if (ammo == WeaponAmmoType.HEAVY) {
                damage = entry.family().equals("machine_gun") ? new Damage(10, 12, 0)
                        : new Damage(Math.max(24, body), Math.max(24, head), 0);
            } else {
                damage = switch (entry.family()) {
                    case "shotgun" -> entry.frame().equals("pinpoint_slug")
                            ? new Damage(Math.max(16, body), Math.max(24, head), 0)
                            : new Damage(Math.max(2, body), Math.max(2, head), 0);
                    case "sniper_rifle" -> new Damage(Math.max(12, body), Math.max(24, head), 0);
                    case "fusion_rifle" -> new Damage(4, 4, 0);
                    case "grenade_launcher" -> new Damage(16, 16, 0);
                    case "glaive" -> new Damage(16, 16, 10);
                    case "trace_rifle" -> new Damage(3, 4, 0);
                    default -> null;
                };
            }
            if (damage != null) result.put(entry.id(), damage);
        }
        return Map.copyOf(result);
    }

    public static Optional<Damage> find(WeaponCatalog.Entry entry) {
        return Optional.ofNullable(ALL.get(entry.id()));
    }
}
