package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerPlayer;

/** Read-only paid-cartridge snapshot. Master calls AFTER successful paid emission/save,
 * passing TRUE pre-consumption rounds and canonical base capacity. Shared fusion/LFR bolts reuse
 * one token; ordinary burst bullets capture separately after each paid consume.
 * Abilities, glaive melee and perk-generated splash MUST pass NONE. No lifecycle sessions.
 */
public final class WeaponHighImpactReserves {
    private record Source(WeaponCatalog.Entry entry, WeaponPerks.Roll roll,
                          int roundsBefore, int baseCapacity, float multiplier) {}

    public static final class Token {
        public static final Token NONE = new Token(null);
        private final Source source;
        private Token(Source source) { this.source = source; }

        /** Frozen scalar; survives source stow/edit/refund. No current-round or source rechecks. */
        public float multiplier() { return source == null ? 1f : source.multiplier; }
    }

    private WeaponHighImpactReserves() {}

    /** Current genuine owned/equipped, alive connected notSuper source only.
     * Caller owns successful payment authority. This API never consumes or refunds ammunition.
     */
    public static Token capture(ServerPlayer player, int roundsBefore, int baseCapacity) {
        if (player == null || !player.isAlive() || player.isRemoved() || player.isSpectator()
                || player.hasDisconnected() || AbilityService.inSuper(player)
                || !WeaponLoadout.canUse(player)) return Token.NONE;
        var stack = player.getMainHandItem();
        boolean possessed = false;
        for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
            if (player.getInventory().getItem(i) == stack) { possessed = true; break; }
        }
        if (!possessed || WeaponLoadout.enabled(player)
                && WeaponLoadout.equipped(player).stream().noneMatch(e -> e.stack() == stack)) return Token.NONE;
        var entry = WeaponItems.entry(stack);
        var selection = WeaponPerks.selected(stack, HighImpactReservesProfile.ID);
        if (entry.isEmpty() || selection.isEmpty()) return Token.NONE;
        return snapshotSource(entry.get(), selection.get(), roundsBefore, baseCapacity);
    }

    /** Pure source/value validation after production authority checks; offline tests need no entity.
     * Invalid arguments fail closed. Above-half valid sources are neutral and allocate no token.
     */
    static Token snapshotSource(WeaponCatalog.Entry entry, WeaponPerks.Roll selection,
                                int roundsBefore, int baseCapacity) {
        if (!HighImpactReservesProfile.supports(entry) || selection == null
                || !entry.id().equals(selection.id())
                || !HighImpactReservesProfile.rolls().contains(selection)) return Token.NONE;
        final float scalar;
        try { scalar = HighImpactReservesProfile.multiplier(entry, roundsBefore, baseCapacity); }
        catch (IllegalArgumentException invalid) { return Token.NONE; }
        if (!Float.isFinite(scalar) || scalar <= 1f) return Token.NONE;
        return new Token(new Source(entry, selection, roundsBefore, baseCapacity, scalar));
    }
}
