package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.weapon.WeaponAce;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Observe real inventory mutations, not an unvalidated container packet or opening a screen. */
@Mixin(Inventory.class)
public abstract class InventoryAceMixin {
    @Shadow @Final public Player player;
    @Shadow public abstract int getSelectedSlot();
    @Shadow public abstract ItemStack getItem(int slot);

    @Inject(method = "setItem", at = @At("HEAD"))
    private void destiny$replacedHeldAce(int slot, ItemStack replacement, CallbackInfo ci) {
        if (slot == getSelectedSlot() && player instanceof ServerPlayer p && getItem(slot) != replacement) {
            WeaponAce.inventoryStowing(p, getItem(slot));
            kim.biryeong.destiny.weapon.WeaponRuntime.inventoryStowing(p,getItem(slot));
        }
    }

    @Inject(method = "removeItem", at = @At("HEAD"))
    private void destiny$removedHeldAce(int slot, int amount, CallbackInfoReturnable<ItemStack> cir) {
        if (amount > 0 && slot == getSelectedSlot() && player instanceof ServerPlayer p && !getItem(slot).isEmpty()) {
            WeaponAce.inventoryStowing(p, getItem(slot));
            kim.biryeong.destiny.weapon.WeaponRuntime.inventoryStowing(p,getItem(slot));
        }
    }

    @Inject(method = "removeItemNoUpdate", at = @At("HEAD"))
    private void destiny$removedWholeHeldAce(int slot, CallbackInfoReturnable<ItemStack> cir) {
        if (slot == getSelectedSlot() && player instanceof ServerPlayer p && !getItem(slot).isEmpty()) {
            WeaponAce.inventoryStowing(p, getItem(slot));
            kim.biryeong.destiny.weapon.WeaponRuntime.inventoryStowing(p,getItem(slot));
        }
    }
}
