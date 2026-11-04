package kim.biryeong.destiny.weapon;

import java.util.Objects;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Stateless paid-emission snapshot. No tick/attachment, timer, linger or enhanced handling.
 * Master captures only after payment; multiply ONLY HitDamage.precision before its combined
 * damage transaction and damage-number split. Body, abilities and splash must use Token.NONE.
 */
public final class WeaponFiringLine {
    private record Source(ServerPlayer owner, ServerLevel level, ItemStack stack,
                          WeaponCatalog.Entry entry, WeaponPerks.Roll roll, GuardianData data, GuardianRuntime runtime,
                          GuardianClass guardianClass, float multiplier) {}

    public static final class Token {
        public static final Token NONE = new Token(null);
        private final Source source;
        private Token(Source source) { this.source = source; }

        /** Ally count is frozen at emission. Revalidate the ORIGINAL source, never the new gun.
         * Stow is allowed while the original stack remains owned/equipped with the original roll.
         * No query can grant a bonus to an emission captured without two allies.
         */
        public float precisionMultiplier() {
            return source != null && valid(source) ? source.multiplier : 1f;
        }
    }

    private WeaponFiringLine() {}

    private static boolean ownerValid(ServerPlayer player) {
        return player != null && player.isAlive() && !player.isRemoved() && !player.isSpectator()
            && !player.hasDisconnected() && !AbilityService.inSuper(player);
    }

    /** Stack identity matters: a copied/replacement stack never inherits paid source authority. */
    private static boolean owns(ServerPlayer player, ItemStack stack) {
        if (stack == null || stack.isEmpty()) return false;
        boolean possessed = false;
        for (int slot = 0; slot < player.getInventory().getContainerSize(); slot++) {
            if (player.getInventory().getItem(slot) == stack) { possessed = true; break; }
        }
        return possessed && (!WeaponLoadout.enabled(player)
            || WeaponLoadout.equipped(player).stream().anyMatch(e -> e.stack() == stack));
    }

    private static boolean valid(Source source) {
        var player = source.owner;
        return ownerValid(player) && player.level() == source.level
            && player.getAttachedOrElse(Guardians.DATA,null) == source.data
            && Guardians.runtimeIfPresent(player).orElse(null) == source.runtime
            && (source.data == null ? source.guardianClass == null : source.data.guardianClass() == source.guardianClass)
            && owns(player, source.stack)
            && WeaponItems.entry(source.stack).filter(source.entry::equals).isPresent()
            && WeaponPerks.selected(source.stack, FiringLineProfile.ID).filter(source.roll::equals).isPresent();
    }

    /** Pure boundaries for focused proximity/team checks, independent of entity registries. */
    static boolean withinRadius(double squaredDistance, double radius) {
        return Double.isFinite(radius) && radius >= 0
            && Double.isFinite(squaredDistance) && squaredDistance >= 0
            && squaredDistance <= radius * radius;
    }

    static boolean sameTeam(String ownerTeam, String otherTeam) {
        return Objects.equals(ownerTeam, otherTeam); // Both unteamed also qualify.
    }

    static boolean eligibleAlly(ServerPlayer owner, ServerPlayer other) {
        if (other == null || other == owner || other.getUUID().equals(owner.getUUID())
                || !other.isAlive() || other.isRemoved() || other.isSpectator()
                || other.hasDisconnected() || other.level() != owner.level()) return false;
        var team = owner.getTeam();
        var otherTeam = other.getTeam();
        return sameTeam(team == null ? null : team.getName(), otherTeam == null ? null : otherTeam.getName())
            && withinRadius(owner.distanceToSqr(other), FiringLineProfile.radiusBlocks());
    }

    /** Iterate existing same-level players only: no entity queries, LOS, chunk loads or attachments.
     * Count saturates at the activation threshold; additional allies do not increase the bonus.
     */
    static int nearbyAllies(ServerPlayer owner) {
        int count = 0;
        for (var other : owner.level().players()) {
            if (eligibleAlly(owner, other) && ++count >= FiringLineProfile.requiredAllies()) break;
        }
        return count;
    }

    /** Caller must already have paid for this weapon emission. Never call for splash or abilities. */
    public static Token capture(ServerPlayer player) {
        if (!ownerValid(player) || !WeaponLoadout.canUse(player)) return Token.NONE;
        var stack = player.getMainHandItem();
        if (!owns(player, stack)) return Token.NONE;
        var entry = WeaponItems.entry(stack).orElse(null);
        var roll = WeaponPerks.selected(stack, FiringLineProfile.ID).orElse(null);
        if (!FiringLineProfile.supports(entry) || roll == null || !entry.id().equals(roll.id())
                || !FiringLineProfile.rolls().contains(roll)
                || nearbyAllies(player) < FiringLineProfile.requiredAllies()) return Token.NONE;
        var data=player.getAttachedOrElse(Guardians.DATA,null);
        return new Token(new Source(player, player.level(), stack, entry, roll, data,
            Guardians.runtimeIfPresent(player).orElse(null),data==null?null:data.guardianClass(),
            FiringLineProfile.precisionMultiplier()));
    }
}
