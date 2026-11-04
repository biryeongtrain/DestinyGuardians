package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.server.level.ServerPlayer;

/** Stateless paid-shot snapshot. No timers, player maps, identity repair, or item/ammo writes. */
public final class WeaponGutshot {
    private WeaponGutshot() {}

    /** Scalar only: a paid shot stays fixed after ADS release/stow/edit. No live source references. */
    public static final class Token {
        public static final Token NONE = new Token(1);
        private final float bodyMultiplier;
        private Token(float bodyMultiplier) { this.bodyMultiplier = bodyMultiplier; }
    }

    /** Pure transaction boundary shared by the real capture and bootstrap-free policy checks.
     * eligible includes real owner/use/equipment checks; held is resolved through WeaponItems.entry.
     * Rejected/unpaid callers never invoke capture and retain NONE. */
    record Context(boolean acceptedPaidFire, boolean eligible, boolean aimInput,
                   Object hand, Object inventoryStack, int count,
                   WeaponCatalog.Entry requested, WeaponCatalog.Entry held, WeaponPerks.Roll selected) {}

    static Token snapshot(Context context) {
        if (context == null || !context.acceptedPaidFire || !context.eligible || !context.aimInput
                || context.hand == null || context.hand != context.inventoryStack || context.count != 1
                || !GutshotProfile.supports(context.requested) || !context.requested.equals(context.held)
                || context.selected == null || !GutshotProfile.rolls().contains(context.selected)
                || !context.requested.id().equals(context.selected.id())) return Token.NONE;
        return new Token(GutshotProfile.bodyMultiplier(context.requested));
    }

    /** MASTER: call exactly once AFTER accepted ammo payment, BEFORE tracing each direct emission.
     * Actual WeaponAiming.aimInput includes accepted ADS transition before completion; raw sneak,
     * cosmetic pose, completed-progress guesses and preview input never substitute for that oracle.
     * This method cannot prove payment itself: previews/rejections/unpaid splash use Token.NONE. */
    public static Token capture(ServerPlayer p, WeaponCatalog.Entry entry) {
        if (p == null || entry == null) return Token.NONE;
        if (!p.level().getServer().isSameThread())
            throw new IllegalStateException("Gutshot capture is main server thread owned");
        if (!p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return Token.NONE;
        var data = p.getAttachedOrElse(Guardians.DATA, null);
        var runtime = Guardians.runtimeIfPresent(p).orElse(null);
        if (data == null || data.guardianClass() == null || data.guardianClass() == GuardianClass.NONE
                || runtime == null || runtime.superSession != null || !WeaponLoadout.canUse(p)) return Token.NONE;
        int slot = p.getInventory().getSelectedSlot();
        if (slot < 0 || slot >= 9) return Token.NONE;
        var stack = p.getMainHandItem();
        // Real item resolution and selected-roll reads are pure; no bind, save, create or repair.
        return snapshot(new Context(true, true, WeaponAiming.aimInput(p), stack,
                p.getInventory().getItem(slot), stack.getCount(), entry,
                WeaponItems.entry(stack).orElse(null), WeaponPerks.selected(stack, GutshotProfile.ID).orElse(null)));
    }

    /** Transform ONLY hits.body before recombining a mixed direct hit. Precision is untouched.
     * MASTER damageOnly() must drop this token for perk splash. No precision transform exists. */
    public static float bodyDamage(Token token, float body) {
        if (token == null || token == Token.NONE || !Float.isFinite(body) || body <= 0) return body;
        float scaled = body * token.bodyMultiplier;
        return Float.isFinite(scaled) ? scaled : body;
    }
}
