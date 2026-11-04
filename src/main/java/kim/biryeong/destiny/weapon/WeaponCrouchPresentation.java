package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

/** Ammit's charged-crossbow third-person crouch compensation, independent of ADS easing.
 * CMD flag1 is reserved cosmetic pose transport, never aim/fire/ability authority. It is
 * written to the real stack so ordinary equipment snapshots carry the same owner pose to
 * every viewer. Flag0 remains the existing client-only grip selector. No native input,
 * body pose, camera, ammunition, reload or movement is modified here.
 */
public final class WeaponCrouchPresentation {
    public static final int FLAG_INDEX = 1;
    private record Binding(ServerPlayer owner, ServerLevel level, int previousSize) { }
    private static final Map<ItemStack, Binding> ACTIVE = new IdentityHashMap<>();

    private WeaponCrouchPresentation() { }

    public static boolean supports(ItemStack stack) {
        return stack != null && WeaponModels.twoHanded(stack)
                && WeaponItems.entry(stack).filter(e -> e.id().equals("ammit_ar2")).isPresent();
    }

    /** Snapshot-safe read for Polymer: flags are cosmetic data, not session admission. */
    public static boolean crouched(ItemStack stack) {
        return supports(stack) && Boolean.TRUE.equals(stack.getOrDefault(
                DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY).getBoolean(FLAG_INDEX));
    }

    private static boolean eligible(ServerPlayer player) {
        return player.isAlive() && !player.isRemoved() && !player.hasDisconnected()
                && !player.isSpectator() && !AbilityService.inSuper(player)
                && WeaponLoadout.canUse(player) && supports(player.getMainHandItem());
    }

    /** Same entity pose query used by 26.3 HumanoidMobRenderer; not sneak-key intent. */
    public static void update(ServerPlayer owner) {
        ItemStack held = owner.getMainHandItem();
        boolean eligible = eligible(owner);
        for (var stack : List.copyOf(ACTIVE.keySet())) {
            var binding = ACTIVE.get(stack);
            if (binding.owner == owner && (!eligible || stack != held
                    || binding.level != owner.level())) release(stack, binding);
        }
        if (!eligible) return;
        var binding = ACTIVE.get(held);
        if (binding == null || binding.owner != owner || binding.level != owner.level()) {
            // Transfer the exact object only after retiring the donor's cosmetic slot.
            if (binding != null) release(held, binding);
            int previousSize = held.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY).flags().size();
            binding = new Binding(owner, owner.level(), previousSize);
            ACTIVE.put(held, binding);
        }
        write(held, flags(held.getOrDefault(DataComponents.CUSTOM_MODEL_DATA,
                CustomModelData.EMPTY).flags(), owner.isCrouching()));
    }

    /** Avoid adding absent false slots; preserve every unrelated flag at its original index. */
    static List<Boolean> flags(List<Boolean> current, boolean crouched) {
        if (!crouched && current.size() <= FLAG_INDEX) return current;
        var values = new ArrayList<>(current);
        while (values.size() <= FLAG_INDEX) values.add(false);
        values.set(FLAG_INDEX, crouched);
        return List.copyOf(values);
    }

    /** Our reserved flag is neutralized, not restored from possibly stale saved pose data.
     * Remove only our appended tail/padding; live higher slots and grip0 remain in place.
     */
    static List<Boolean> retiredFlags(List<Boolean> current, int previousSize) {
        var values = new ArrayList<>(flags(current, false));
        if (previousSize <= FLAG_INDEX && values.size() == FLAG_INDEX + 1) {
            values.remove(FLAG_INDEX);
            if (previousSize == 0 && values.size() == 1 && !values.getFirst()) values.clear();
        }
        return List.copyOf(values);
    }

    private static void write(ItemStack stack, List<Boolean> flags) {
        var data = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        if (!data.flags().equals(flags)) stack.set(DataComponents.CUSTOM_MODEL_DATA,
                new CustomModelData(data.floats(), flags, data.strings(), data.colors()));
    }

    private static void release(ItemStack stack, Binding binding) {
        if (!ACTIVE.remove(stack, binding)) return;
        var data = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        write(stack, retiredFlags(data.flags(), binding.previousSize));
    }

    public static void cleanup(ServerPlayer owner) {
        for (var stack : List.copyOf(ACTIVE.keySet())) {
            var binding = ACTIVE.get(stack);
            if (binding.owner == owner) release(stack, binding);
        }
    }

    public static void clearAll() {
        for (var stack : List.copyOf(ACTIVE.keySet())) release(stack, ACTIVE.get(stack));
    }
}
