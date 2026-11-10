package kim.biryeong.destiny.test.mixin;

import com.llamalad7.mixinextras.injector.wrapmethod.WrapMethod;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import net.minecraft.gametest.framework.GameTestServer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.concurrent.locks.LockSupport;
import java.util.function.BooleanSupplier;

/** Native headless tests normally accelerate. Only explicit load tests use real20Hz wall-clock pacing. */
@Mixin(GameTestServer.class)
public abstract class GameTestScalePacingMixin {
    @org.spongepowered.asm.mixin.Unique private long destiny$nextScaleTick;
    @WrapMethod(method="tickServer")
    private void destiny$scalePacing(BooleanSupplier haveTime, Operation<Void> original) {
        if (!Boolean.getBoolean("destiny.gametest.scale.enabled")) { original.call(haveTime); return; }
        long started = System.nanoTime();
        if (destiny$nextScaleTick == 0 || started - destiny$nextScaleTick > 500_000_000L) destiny$nextScaleTick = started;
        destiny$nextScaleTick += 50_000_000L;
        long deadline = destiny$nextScaleTick;
        // The accelerated GameTest clock is not our wall-clock budget. Native chunk
        // unload callbacks must receive the same spare time as this20Hz wrapper.
        original.call((BooleanSupplier) () -> System.nanoTime() < deadline);
        long remaining;
        while ((remaining = destiny$nextScaleTick - System.nanoTime()) > 0 && !Thread.currentThread().isInterrupted())
            LockSupport.parkNanos(remaining); // Packet delivery can unpark the server; honor the whole deadline.
    }

    @Inject(method="getMaxPlayers", at=@At("HEAD"), cancellable=true)
    private void destiny$scaleCapacity(CallbackInfoReturnable<Integer> result) {
        if (Boolean.getBoolean("destiny.gametest.scale.enabled")) result.setReturnValue(64);
    }
}
