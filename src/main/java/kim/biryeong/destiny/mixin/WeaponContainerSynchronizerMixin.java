package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.weapon.WeaponOutboundPresentation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyArgs;
import org.spongepowered.asm.mixin.injection.invoke.arg.Args;

import java.util.List;

/** Only the final outbound packet arguments change. The synchronizer's menu,
 * remote matching state and server-side broadcast listeners remain authoritative.
 */
@Mixin(targets = "net.minecraft.server.level.ServerPlayer$1")
public abstract class WeaponContainerSynchronizerMixin {
    @Shadow @Final private ServerPlayer this$0;

    @ModifyArgs(method = "sendSlotChange", at = @At(value = "INVOKE", target =
            "Lnet/minecraft/network/protocol/game/ClientboundContainerSetSlotPacket;<init>(IIILnet/minecraft/world/item/ItemStack;)V"))
    private void destiny$projectSlot(Args args, AbstractContainerMenu menu, int index, ItemStack snapshot) {
        args.set(3, WeaponOutboundPresentation.projectSlot(this$0, menu, index, snapshot));
    }

    @ModifyArgs(method = "sendInitialData", at = @At(value = "INVOKE", target =
            "Lnet/minecraft/network/protocol/game/ClientboundContainerSetContentPacket;<init>(IILjava/util/List;Lnet/minecraft/world/item/ItemStack;)V"))
    private void destiny$projectContent(Args args, AbstractContainerMenu menu, List<ItemStack> snapshots,
                                       ItemStack carried, int[] data) {
        args.set(2, WeaponOutboundPresentation.projectContent(this$0, menu, snapshots));
        // Carried/cursor is not the vetted selected hand slot; never project it.
    }
}
