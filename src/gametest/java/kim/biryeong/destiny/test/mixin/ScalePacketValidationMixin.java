package kim.biryeong.destiny.test.mixin;

import com.llamalad7.mixinextras.injector.wrapmethod.WrapMethod;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import org.spongepowered.asm.mixin.Mixin;

/** Diagnostic only: never changes vanilla validation or excuses invalid benchmark input. */
@Mixin(ServerGamePacketListenerImpl.class)
public abstract class ScalePacketValidationMixin {
    @WrapMethod(method="containsInvalidValues")
    private static boolean destiny$scaleInvalidValues(double x, double y, double z, float yaw, float pitch, Operation<Boolean> original) {
        boolean invalid = original.call(x, y, z, yaw, pitch);
        if (invalid && Boolean.getBoolean("destiny.gametest.scale.enabled"))
            org.slf4j.LoggerFactory.getLogger("DestinyScale").warn("Invalid native movement: xyz={},{},{} yaw={} pitch={} caller={}",
                    x, y, z, yaw, pitch, StackWalker.getInstance().walk(s -> s.limit(7).toList()));
        return invalid;
    }
}
