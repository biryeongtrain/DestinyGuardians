package kim.biryeong.destiny.mixin;

import net.minecraft.world.entity.Display;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/** One-tick interpolation for untracked empty item-display camera/seat entities. */
@Mixin(Display.class)
public interface DisplayCameraAccessor {
    @Invoker("setPosRotInterpolationDuration")
    void destiny$setCameraInterpolation(int ticks);
}
