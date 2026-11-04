package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.ByteTag;
import net.minecraft.nbt.ShortTag;
import net.minecraft.nbt.IntTag;
import net.minecraft.nbt.LongTag;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** Passive base trait on the genuine held/equipped selected object. Read-only live rounds
 * at query time (including after paid save) are this port's timing adaptation: DDC239 does
 * not specify pre/post-cartridge evaluation. No sessions, tokens, timers or HUD behavior.
 */
public final class WeaponUnderPressure {
    private WeaponUnderPressure() {}

    private static WeaponCatalog.Entry source(ServerPlayer player) {
        if (player == null || !player.isAlive() || player.isRemoved() || player.isSpectator()
                || player.hasDisconnected() || AbilityService.inSuper(player)
                || !WeaponLoadout.canUse(player)) return null;
        var stack = player.getMainHandItem();
        int slot = player.getInventory().getSelectedSlot();
        if (slot < 0 || slot >= 9 || player.getInventory().getItem(slot) != stack
                || stack.getCount() != 1) return null;
        if (WeaponLoadout.enabled(player)
                && WeaponLoadout.equipped(player).stream().noneMatch(e -> e.stack() == stack)) return null;
        var entry = WeaponItems.entry(stack).orElse(null);
        if (!UnderPressureProfile.supports(entry)) return null;
        var selected = WeaponPerks.selected(stack, UnderPressureProfile.ID).orElse(null);
        return selected != null && entry.id().equals(selected.id())
                && UnderPressureProfile.rolls().contains(selected) ? entry : null;
    }

    private static int liveRounds(ItemStack stack) {
        var custom = stack.get(DataComponents.CUSTOM_DATA);
        if (custom == null) return -1;
        // The general magazine helper projects invalid/missing counts as empty. That would
        // incorrectly grant maximum stats here. Accept integral saved counts only, unchanged.
        long rounds = switch (custom.copyTag().get(WeaponItems.ROUNDS)) {
            case ByteTag value -> value.longValue();
            case ShortTag value -> value.longValue();
            case IntTag value -> value.longValue();
            case LongTag value -> value.longValue();
            case null, default -> -1L;
        };
        return rounds >= 0 && rounds <= Integer.MAX_VALUE ? (int)rounds : -1;
    }

    public static int stabilityBonus(ServerPlayer player) {
        var entry = source(player);
        return entry == null ? 0 : UnderPressureProfile.stabilityBonus(entry,
                liveRounds(player.getMainHandItem()), WeaponProfile.forEntry(entry).magazine());
    }
    public static double accuracyScalar(ServerPlayer player) {
        var entry = source(player);
        return entry == null ? 1 : UnderPressureProfile.accuracyScalar(entry,
                liveRounds(player.getMainHandItem()), WeaponProfile.forEntry(entry).magazine());
    }

    /** Optional caller-owned round snapshot; still validates current source authority.
     * For pre-paid timing, read rounds BEFORE consume/emit and pass the canonical capacity.
     * No rounds+1 reconstruction after refunds; no state is cached by this class.
     */
    public static int stabilityBonus(ServerPlayer player, int rounds, int baseCapacity) {
        var entry = source(player);
        return entry == null ? 0 : UnderPressureProfile.stabilityBonus(entry, rounds, baseCapacity);
    }
    public static double accuracyScalar(ServerPlayer player, int rounds, int baseCapacity) {
        var entry = source(player);
        return entry == null ? 1 : UnderPressureProfile.accuracyScalar(entry, rounds, baseCapacity);
    }
}
