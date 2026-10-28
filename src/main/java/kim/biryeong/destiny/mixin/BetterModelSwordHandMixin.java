package kim.biryeong.destiny.mixin;

import com.llamalad7.mixinextras.injector.wrapmethod.WrapMethod;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import kim.biryeong.destiny.fx.SwordHandPackets;
import net.minecraft.network.protocol.Packet;
import net.minecraft.server.network.ServerPlayerConnection;
import org.spongepowered.asm.mixin.*;

/** BM 3.5.1 owner-only logical hand repair; world equipment hiding is unchanged. */
@Pseudo
@Mixin(targets = "kr.toxicity.model.impl.fabric.entity.PlayerChannelHandlerImpl", remap = false)
public abstract class BetterModelSwordHandMixin {
    @Shadow @Final private ServerPlayerConnection connection;

    @WrapMethod(method = "handle(Lnet/minecraft/network/protocol/Packet;)Lnet/minecraft/network/protocol/Packet;")
    private Packet<?> destiny$keepUsableSword(Packet<?> packet, Operation<Packet<?>> original) {
        return SwordHandPackets.around(connection, packet, p -> original.call(p));
    }
}
