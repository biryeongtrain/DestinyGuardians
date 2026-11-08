package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.weapon.AmmoGeneration;

/** User-requested Minecraft PvE tuning, not original Destiny damage values.
 * 2026-11-02: primary x1.5, special x2.5, ability x3, super x10; heavy was left at x1.
 * 2026-11-08: special/heavy were weaker than primary in play. Measured over the catalog (damage per shot x pellets x burst
 * over the real cadence) heavy averaged 9-34 dps and special 28-104 dps against 23-51 for primary. Special is now x4
 * (about 2-3 times a primary's dps) and heavy x6 (about 5-8 times), so a full heavy reserve can take a boss. */
public final class PveDamageBalance {
    private PveDamageBalance() { }

    /** Game-test fixture switch: lets mechanics tests assert raw weapon damage instead of the tuning table. */
    public static volatile boolean neutralForTests;

    /** Applied once at the damage boundary, after weapon/contact modifiers; PvP stays unchanged. */
    public static float scale(float amount, AmmoGeneration.Kind kind, boolean playerTarget) {
        if (playerTarget || neutralForTests) return amount;
        return amount * switch (kind) {
            case PRIMARY -> 1.5f;
            case SPECIAL -> 4f;
            case HEAVY -> 6f;
            case ABILITY -> 3f;
            case SUPER -> 10f;
            default -> 1f;
        };
    }
}
