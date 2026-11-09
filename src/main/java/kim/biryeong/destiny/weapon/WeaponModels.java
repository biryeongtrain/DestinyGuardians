package kim.biryeong.destiny.weapon;

import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.CustomModelData;
import java.util.List;
import java.util.Optional;

/** Vanilla-compatible inventory/held models. No DisplayHud or client registry required. */
public final class WeaponModels {
    public static final String TAG = "destiny_weapon_preview";
    public static final String GRIP_TAG = "destiny_weapon_grip";
    public enum Pose { HIP, ADS, INSPECT, SCOPE }
    public enum Grip { NATIVE, TWO_HAND }
    private WeaponModels() {}

    public static ItemStack create(WeaponCatalog.Entry entry) {
        ItemStack stack = new ItemStack(WeaponPreviewItem.INSTANCE);
        stack.set(DataComponents.ITEM_MODEL, Identifier.parse(entry.item_model()));
        stack.set(DataComponents.ITEM_NAME, Component.literal(WeaponExotics.displayName(entry)));
        stack.set(DataComponents.MAX_STACK_SIZE, 1);
        CompoundTag tag = new CompoundTag();
        tag.putString(TAG, entry.id());
        tag.putString(GRIP_TAG, defaultGrip(entry).name());
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        setPose(stack, Pose.HIP);
        return stack;
    }
    public static Optional<WeaponCatalog.Entry> entry(ItemStack stack) {
        // W30/W31 saved stick previews remain recognizable; grip conversion is explicit.
        if (!stack.is(Items.STICK) && !stack.is(WeaponPreviewItem.INSTANCE) && !stack.is(WeaponCombatItem.INSTANCE)) return Optional.empty();
        var data = stack.get(DataComponents.CUSTOM_DATA);
        if (data == null) return Optional.empty();
        return data.copyTag().getString(TAG).flatMap(WeaponCatalog::find)
                .filter(e -> Identifier.parse(e.item_model()).equals(stack.get(DataComponents.ITEM_MODEL)));
    }
    public static boolean supportsTwoHand(WeaponCatalog.Entry entry) {
        return !List.of("bow", "sword").contains(entry.family());
    }
    public static Grip defaultGrip(WeaponCatalog.Entry entry) {
        return supportsTwoHand(entry) && !List.of("hand_cannon", "sidearm").contains(entry.family())
                ? Grip.TWO_HAND : Grip.NATIVE;
    }
    public static boolean twoHanded(ItemStack stack) {
        if (!stack.is(WeaponPreviewItem.INSTANCE) && !stack.is(WeaponCombatItem.INSTANCE)) return false;
        return entry(stack).filter(WeaponModels::supportsTwoHand).isPresent()
                && stack.get(DataComponents.CUSTOM_DATA).copyTag().getString(GRIP_TAG)
                .filter(Grip.TWO_HAND.name()::equals).isPresent();
    }
    /** Returns a copy so a legacy stick can safely migrate without losing its components. */
    public static Optional<ItemStack> withGrip(ItemStack stack, Grip grip) {
        var entry = entry(stack);
        if (entry.isEmpty() || grip == Grip.TWO_HAND && !supportsTwoHand(entry.get())) return Optional.empty();
        var out = stack.transmuteCopy(stack.is(WeaponCombatItem.INSTANCE) ? WeaponCombatItem.INSTANCE : WeaponPreviewItem.INSTANCE);
        var tag = out.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putString(GRIP_TAG, grip.name());
        out.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        return Optional.of(out);
    }
    public static boolean setPose(ItemStack stack, Pose pose) {
        if (entry(stack).isEmpty()) return false;
        var data = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        var strings = new java.util.ArrayList<>(data.strings());
        if (strings.isEmpty()) strings.add("");
        strings.set(0, pose.name().toLowerCase(java.util.Locale.ROOT));
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(data.floats(), data.flags(),
                strings, data.colors()));
        return true;
    }
}
