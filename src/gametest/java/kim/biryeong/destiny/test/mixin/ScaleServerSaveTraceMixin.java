package kim.biryeong.destiny.test.mixin;

import com.llamalad7.mixinextras.injector.wrapmethod.WrapMethod;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import kim.biryeong.destiny.test.GameTestScaleSaveTrace;
import net.minecraft.server.MinecraftServer;
import org.spongepowered.asm.mixin.Mixin;

@Mixin(MinecraftServer.class)
public abstract class ScaleServerSaveTraceMixin {
    @WrapMethod(method = "saveEverything")
    private boolean destiny$scaleSaveTiming(boolean silent, boolean flush, boolean force, Operation<Boolean> original) {
        var server = (MinecraftServer) (Object) this;
        var sample = GameTestScaleSaveTrace.begin(server);
        boolean returned = false;
        boolean result = false;
        try {
            result = original.call(silent, flush, force);
            returned = true;
            return result;
        } finally {
            GameTestScaleSaveTrace.recordServer(server, sample, silent, flush, force, returned, result);
        }
    }
}
