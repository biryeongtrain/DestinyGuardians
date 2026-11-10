package kim.biryeong.destiny.test.mixin;

import com.llamalad7.mixinextras.injector.wrapmethod.WrapMethod;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import kim.biryeong.destiny.test.GameTestScaleSaveTrace;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.ProgressListener;
import org.spongepowered.asm.mixin.Mixin;

@Mixin(ServerLevel.class)
public abstract class ScaleLevelSaveTraceMixin {
    @WrapMethod(method = "save")
    private void destiny$scaleLevelSaveTiming(ProgressListener progress, boolean flush, boolean noSave,
                                             Operation<Void> original) {
        var level = (ServerLevel) (Object) this;
        var sample = GameTestScaleSaveTrace.begin(level.getServer());
        boolean returned = false;
        try {
            original.call(progress, flush, noSave);
            returned = true;
        } finally {
            GameTestScaleSaveTrace.recordLevel(level, sample, flush, noSave, returned);
        }
    }
}
