package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.player.Player;

/** Stateless, target-conditional passive. Capture ONLY at the runtime's paid weapon boundary.
 * Abilities and glaive melee pass NONE; paid sword attacks and glaive projectiles may capture.
 * No selection, HUD read, target check, tick, stow or edit creates new source credit.
 */
public final class WeaponVorpal {
    /** Immutable value objects only: never retain the player, level, stack or mutable session. */
    private record Source(WeaponCatalog.Entry entry, WeaponPerks.Roll roll, float multiplier) {}

    public static final class Token {
        public static final Token NONE = new Token(null);
        private final Source source;
        private Token(Source source) { this.source = source; }

        /** The target's CURRENT classification matters; the source's paid-emission scalar is frozen.
         * Already-launched damage survives source stow/edit. This never rechecks the shooter's new gun.
         */
        public float multiplier(LivingEntity target) {
            return multiplierForTarget(eligibleTarget(target));
        }

        // Pure scalar boundary for offline tests without bootstrapping Minecraft entity registries.
        float multiplierForTarget(boolean eligible) {
            return source != null && eligible ? source.multiplier : 1f;
        }
    }

    private WeaponVorpal() {}

    /** Explicit local mapping of Clarity's miniboss/boss/vehicle categories.
     * PvP is excluded by project combat; nonliving vehicles are outside LivingEntity damage.
     * Health, display name, boss-bar presence and unrelated tags never infer this classification.
     */
    static boolean eligibleTarget(LivingEntity target) {
        if (target == null || target instanceof Player || target instanceof ArmorStand
                || !target.isAlive() || target.isRemoved() || target.isSpectator()) return false;
        return target instanceof WitherBoss || target instanceof EnderDragon
                || target instanceof Mob && (target.entityTags().contains("destiny_boss")
                || target.entityTags().contains("destiny_vehicle"));
    }

    /** Valid CURRENT held/equipped source only; the caller must already have paid for the emission. */
    public static Token capture(ServerPlayer player) {
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
        var selection = WeaponPerks.selected(stack, VorpalProfile.ID);
        if (entry.isEmpty() || selection.isEmpty()) return Token.NONE;
        return snapshotSource(entry.get(), selection.get());
    }

    /** After source authority checks, freeze exact catalog/roll values. No shared registry required
     * for this pure boundary; production selection remains exclusively WeaponPerks.selected.
     */
    static Token snapshotSource(WeaponCatalog.Entry entry, WeaponPerks.Roll selection) {
        if (!VorpalProfile.supports(entry) || selection == null
                || !entry.id().equals(selection.id()) || !VorpalProfile.rolls().contains(selection)) return Token.NONE;
        return new Token(new Source(entry, selection, VorpalProfile.multiplier(entry)));
    }

    public static float multiplier(Token token, LivingEntity target) {
        return token == null ? 1f : token.multiplier(target);
    }
}
