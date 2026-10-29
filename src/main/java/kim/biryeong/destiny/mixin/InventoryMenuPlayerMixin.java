package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.inventory.InventoryMenuRedirect;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.MenuProvider;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import java.util.OptionalInt;

@Mixin(ServerPlayer.class)
public abstract class InventoryMenuPlayerMixin {
    @Inject(method="openMenu", at=@At("HEAD"))
    private void destiny$realRecipeBook(MenuProvider provider, CallbackInfoReturnable<OptionalInt> cir) {
        InventoryMenuRedirect.externalMenu((ServerPlayer)(Object)this);
    }
    @Inject(method="openMenu", at=@At("RETURN"))
    private void destiny$failedMenu(MenuProvider provider, CallbackInfoReturnable<OptionalInt> cir) {
        // Locked/invalid providers may return null without ever opening a screen to close.
        if (cir.getReturnValue().isEmpty()) InventoryMenuRedirect.closed((ServerPlayer)(Object)this);
    }
}
