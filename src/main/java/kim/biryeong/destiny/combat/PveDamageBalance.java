package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.weapon.AmmoGeneration;

/** User-requested Minecraft PvE tuning (2026-11-02), not original Destiny damage values. */
public final class PveDamageBalance {
    private PveDamageBalance() { }

    /** Applied once at the damage boundary, after weapon/contact modifiers; PvP stays unchanged. */
    public static float scale(float amount, AmmoGeneration.Kind kind, boolean playerTarget) {
        if (playerTarget) return amount;
        return amount * switch (kind) {
            case PRIMARY -> 1.5f;
            case SPECIAL -> 2.5f;
            case SUPER -> 3f;
            default -> 1f;
        };
    }
}
