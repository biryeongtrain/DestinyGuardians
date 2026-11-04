package kim.biryeong.destiny.weapon;

import eu.pb4.polymer.core.api.item.PolymerItem;
import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.Holder;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.item.component.Consumable;
import net.minecraft.world.item.component.UseEffects;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.*;
import net.minecraft.world.item.component.ChargedProjectiles;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import java.util.List;

/** Separate live item: vanilla carriers supply rendering only; every shot is server simulated. */
public final class WeaponCombatItem extends Item implements PolymerItem {
    public static final WeaponCombatItem INSTANCE = register();
    private static WeaponCombatItem register() {
        var id = DestinyGuardians.id("weapon_combat");
        return Registry.register(BuiltInRegistries.ITEM, id, new WeaponCombatItem(
                new Properties().setId(ResourceKey.create(Registries.ITEM, id)).stacksTo(1)));
    }
    private WeaponCombatItem(Properties properties) { super(properties); }
    public static void init() {}
    @Override public Item getPolymerItem(ItemStack stack, PacketContext context) {
        return WeaponModels.twoHanded(stack) ? Items.CROSSBOW : Items.STICK;
    }
    @Override public Identifier getPolymerItemModel(ItemStack stack, PacketContext context, HolderLookup.Provider lookup) {
        return WeaponSkins.route(stack, baseItemModel(stack));
    }
    private Identifier baseItemModel(ItemStack stack) {
        if (WeaponSwapPresentation.active(stack)) return WeaponSwapPresentation.model(stack);
        if (WeaponInsertPresentation.active(stack)) return WeaponInsertPresentation.model(WeaponItems.entry(stack).orElseThrow());
        if (WeaponIzanagiPresentation.active(stack)) return WeaponIzanagiPresentation.scopedIdle(stack)
                ? WeaponScopes.model(WeaponItems.entry(stack).orElseThrow()) : WeaponIzanagiPresentation.model(stack);
        if (WeaponReloadPresentation.active(stack)) return WeaponReloadPresentation.model(WeaponItems.entry(stack).orElseThrow());
        // Snipers retain the opaque W45 scope route at .5; LFRs keep moving their 3D scope model.
        if (WeaponAimPresentation.active(stack) && !(WeaponScopes.scoped(stack)
                && WeaponItems.entry(stack).filter(e -> e.family().equals("sniper_rifle")).isPresent()))
            return WeaponAimPresentation.model(stack);
        if (WeaponBowPresentation.active(stack)) return WeaponBowPresentation.model(WeaponItems.entry(stack).orElseThrow());
        if (WeaponScopes.scoped(stack)) return WeaponScopes.model(WeaponItems.entry(stack).orElseThrow());
        return WeaponModels.entry(stack).isPresent() ? stack.get(DataComponents.ITEM_MODEL) : Identifier.withDefaultNamespace("stick");
    }
    /** Apply player-skin arms after the normal Polymer representation and live-route selection. */
    @Override public ItemStack getPolymerItemStack(ItemStack stack, TooltipFlag tooltip,
            PacketContext context, HolderLookup.Provider lookup) {
        var out = WeaponFirstPersonHands.project(PolymerItem.super.getPolymerItemStack(stack, tooltip, context, lookup), context);
        var connection = context.get(PacketContext.CONNECTION);
        if (connection != null && connection.getPacketListener() instanceof net.minecraft.server.network.ServerGamePacketListenerImpl listener
                && kim.biryeong.destiny.input.ClientControls.gcb(listener.getPlayer()) && !SwordItems.isSword(stack)) {
            var lore = out.get(DataComponents.LORE);
            if (lore != null) {
                var lines = new java.util.ArrayList<>(lore.lines());
                if (lines.size() > 2) lines.set(2, net.minecraft.network.chat.Component.literal(GlaiveItems.isGlaive(stack)
                        ? "좌클릭 발사 / 우클릭 근접 / 웅크리기 방패 / Q 재장전"
                        : "좌클릭 발사·유지 / 우클릭 홀드 정조준 / Q 재장전"));
                if (lines.size() > 4) lines.set(4, net.minecraft.network.chat.Component.literal("궁극기·스킬 입력 우선"));
                out.set(DataComponents.LORE, new net.minecraft.world.item.component.ItemLore(lines));
            }
        }
        return out;
    }

    @Override public void modifyBasePolymerItemStack(ItemStack out, ItemStack original, PacketContext context, HolderLookup.Provider lookup) {
        boolean two = WeaponModels.twoHanded(original);
        var data = original.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        var flags = WeaponCrouchPresentation.supports(original)
                ? List.of(two, WeaponCrouchPresentation.crouched(original)) : List.of(two);
        out.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(data.floats(), flags, data.strings(), data.colors()));
        out.set(DataComponents.USE_EFFECTS, new UseEffects(true, false, 1f));
        out.remove(DataComponents.FOOD);
        if (two) {
            // Charged crossbow repeats client use packets every four ticks, never native use/release.
            out.set(DataComponents.CHARGED_PROJECTILES, ChargedProjectiles.of(new ItemStackTemplate(Items.ARROW)));
            out.remove(DataComponents.CONSUMABLE);
        } else {
            out.remove(DataComponents.CHARGED_PROJECTILES);
            out.set(DataComponents.CONSUMABLE, Consumable.builder().consumeSeconds(3600)
                    .animation(ItemUseAnimation.NONE).hasConsumeParticles(false)
                    .sound(Holder.direct(SoundEvent.createVariableRangeEvent(Identifier.withDefaultNamespace("intentionally_empty"))))
                    .build());
        }
    }
    @Override public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (player instanceof ServerPlayer serverPlayer && hand == InteractionHand.MAIN_HAND) {
            if (GcbWeaponInput.remapped(serverPlayer)) return InteractionResult.CONSUME;
            if (WeaponModels.twoHanded(player.getMainHandItem())) WeaponRuntime.heartbeatUse(serverPlayer);
            else if (WeaponRuntime.beginUse(serverPlayer)) player.startUsingItem(hand);
        }
        return InteractionResult.CONSUME;
    }
    @Override public InteractionResult useOn(UseOnContext context) {
        return context.getPlayer() == null ? InteractionResult.CONSUME : use(context.getLevel(), context.getPlayer(), context.getHand());
    }
    @Override public void onUseTick(Level level, LivingEntity entity, ItemStack stack, int remaining) {
        if (entity instanceof ServerPlayer player && !GcbWeaponInput.remapped(player)) WeaponRuntime.continueUse(player);
    }
    @Override public boolean releaseUsing(ItemStack stack, Level level, LivingEntity entity, int remaining) {
        if (entity instanceof ServerPlayer player && !GcbWeaponInput.remapped(player)) WeaponRuntime.releaseUse(player, stack);
        return true;
    }
    @Override public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) { return stack; }
    @Override public int getUseDuration(ItemStack stack, LivingEntity entity) { return 72000; }
    @Override public ItemUseAnimation getUseAnimation(ItemStack stack) { return ItemUseAnimation.NONE; }
    @Override public boolean isPolymerItemInteraction(ServerPlayer player, InteractionHand hand,
            ItemStack stack, ServerLevel level, InteractionResult result) { return true; }
}
