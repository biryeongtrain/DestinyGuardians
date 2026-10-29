package kim.biryeong.destiny.test.mixin;

import net.minecraft.gametest.framework.GameTestInfo;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;
import org.spongepowered.asm.mixin.gen.Invoker;

/** Regression tests exercise native finish without a runner or a second world structure. */
@Mixin(GameTestInfo.class)
public interface GameTestInfoAccessor {
    @Invoker("finish")
    void destiny$finish();

    @Invoker("tickInternal")
    void destiny$tickInternal();

    @Accessor("started")
    void destiny$started(boolean started);

    @Accessor("tickCount")
    void destiny$tick(int tick);

    @Accessor("placedStructure")
    void destiny$placedStructure(boolean placed);

    @Accessor("chunksLoaded")
    void destiny$chunksLoaded(boolean loaded);
}
