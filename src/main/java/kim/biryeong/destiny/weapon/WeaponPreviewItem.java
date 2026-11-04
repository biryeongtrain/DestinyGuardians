package kim.biryeong.destiny.weapon;

import eu.pb4.polymer.core.api.item.PolymerItem;
import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.*;
import net.minecraft.world.item.component.ChargedProjectiles;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.Level;

import java.util.List;

/** Inert server item. Only its Polymer wire copy borrows the vanilla charged-crossbow pose. */
public final class WeaponPreviewItem extends Item implements PolymerItem {
    public static final WeaponPreviewItem INSTANCE = register();

    private static WeaponPreviewItem register() {
        var id = DestinyGuardians.id("weapon_preview");
        return Registry.register(BuiltInRegistries.ITEM, id, new WeaponPreviewItem(
                new Properties().setId(ResourceKey.create(Registries.ITEM, id)).stacksTo(1)));
    }

    private WeaponPreviewItem(Properties properties) { super(properties); }
    public static void init() { /* Register while registries are mutable, not on first equip. */ }

    @Override public Item getPolymerItem(ItemStack stack, PacketContext context) {
        return WeaponModels.twoHanded(stack) ? Items.CROSSBOW : Items.STICK;
    }

    @Override public Identifier getPolymerItemModel(ItemStack stack, PacketContext context, HolderLookup.Provider lookup) {
        return WeaponModels.entry(stack).isPresent() ? WeaponSkins.route(stack, stack.get(DataComponents.ITEM_MODEL))
                : Identifier.withDefaultNamespace("stick");
    }

    /** Apply player-skin arms after the normal Polymer representation and live-route selection. */
    @Override public ItemStack getPolymerItemStack(ItemStack stack, TooltipFlag tooltip,
            PacketContext context, HolderLookup.Provider lookup) {
        return WeaponFirstPersonHands.project(PolymerItem.super.getPolymerItemStack(stack, tooltip, context, lookup), context);
    }

    @Override public void modifyBasePolymerItemStack(ItemStack out, ItemStack original,
                                                    PacketContext context, HolderLookup.Provider lookup) {
        boolean twoHanded = WeaponModels.twoHanded(original);
        var data = original.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        out.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(data.floats(), List.of(twoHanded),
                data.strings(), data.colors()));
        // Never charge the real server stack. The arrow is a pose marker in the wire copy only.
        if (twoHanded) out.set(DataComponents.CHARGED_PROJECTILES,
                ChargedProjectiles.of(new ItemStackTemplate(Items.ARROW)));
        else out.remove(DataComponents.CHARGED_PROJECTILES);
    }

    @Override public InteractionResult use(Level level, Player player, InteractionHand hand) {
        // No startUsingItem, ammo lookup, projectile, durability, consumption, or swing.
        return InteractionResult.CONSUME;
    }

    @Override public boolean isPolymerItemInteraction(ServerPlayer player, InteractionHand hand,
            ItemStack stack, ServerLevel level, InteractionResult result) { return true; }
}
