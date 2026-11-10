package kim.biryeong.destiny.mixin;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import kim.biryeong.destiny.weapon.WeaponObserverEquipment;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.game.ClientboundSetEquipmentPacket;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;

/** Scope is this packet's write method, never the shared inventory/entity-data item codec. */
@Mixin(ClientboundSetEquipmentPacket.class)
public abstract class WeaponObserverEquipmentMixin {
    @Shadow public abstract int getEntity();

    @WrapOperation(method = "write", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/network/codec/StreamCodec;encode(Ljava/lang/Object;Ljava/lang/Object;)V"))
    private void destiny$observerWeapon(StreamCodec<Object, Object> codec, Object buffer, Object item,
                                        Operation<Void> original) {
        original.call(codec, buffer, WeaponObserverEquipment.project(getEntity(), (ItemStack) item,
                (RegistryFriendlyByteBuf) buffer));
    }
}
