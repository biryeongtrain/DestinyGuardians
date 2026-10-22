package kim.biryeong.destiny.mixin;

import com.llamalad7.mixinextras.injector.wrapmethod.WrapMethod;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import kim.biryeong.destiny.debug.HunterQa;
import net.minecraft.server.MinecraftServer;
import org.spongepowered.asm.mixin.Mixin;

import java.util.function.BooleanSupplier;

/** Wrap the entire invocation, including Fabric's TAIL-injected END tick listeners. */
@Mixin(MinecraftServer.class)
public abstract class MinecraftServerQaMixin {
    @WrapMethod(method = "tickServer")
    private void destiny$qaWholeTick(BooleanSupplier timeLeft, Operation<Void> original) {
        if (!HunterQa.enabled()) {
            original.call(timeLeft);
            return;
        }
        long start = System.nanoTime();
        try {
            original.call(timeLeft);
        } finally {
            HunterQa.completedTick(System.nanoTime() - start);
        }
    }
}
