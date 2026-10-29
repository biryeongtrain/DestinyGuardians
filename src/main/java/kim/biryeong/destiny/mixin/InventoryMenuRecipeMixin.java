package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.inventory.InventoryMenuRedirect;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.stats.ServerRecipeBook;
import net.minecraft.world.item.crafting.RecipeHolder;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import java.util.Collection;

@Mixin(ServerRecipeBook.class)
public abstract class InventoryMenuRecipeMixin {
    @Inject(method={"addRecipes","removeRecipes"}, at=@At("TAIL"))
    private void destiny$recipeChanges(Collection<RecipeHolder<?>> recipes, ServerPlayer player, CallbackInfoReturnable<Integer> cir) {
        if (cir.getReturnValueI() > 0) InventoryMenuRedirect.refreshIfArmed(player);
    }
    @Inject(method="sendInitialRecipeBook", at=@At("TAIL"))
    private void destiny$recipeSync(ServerPlayer player, CallbackInfo ci) {
        InventoryMenuRedirect.refreshIfArmed(player);
    }
}
