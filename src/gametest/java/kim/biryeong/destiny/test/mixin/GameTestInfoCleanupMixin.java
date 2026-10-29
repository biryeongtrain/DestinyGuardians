package kim.biryeong.destiny.test.mixin;

import com.llamalad7.mixinextras.injector.wrapmethod.WrapMethod;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import kim.biryeong.destiny.test.TestCleanup;
import net.minecraft.gametest.framework.GameTestInfo;
import net.minecraft.gametest.framework.GameTestRunner;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(GameTestInfo.class)
public abstract class GameTestInfoCleanupMixin implements TestCleanup.Owner {
    @Unique
    private final TestCleanup.Scope destiny$cleanup = new TestCleanup.Scope();

    @Unique
    private boolean destiny$ticking;

    @Unique
    private boolean destiny$cleanupPending;

    @Override
    public TestCleanup.Scope destiny$cleanup() {
        return destiny$cleanup;
    }

    @Inject(method = "finish()V", at = @At("HEAD"), cancellable = true)
    private void destiny$finishCleanup(CallbackInfo ci) {
        // Do not let a callback's recursive finish publish done while teardown is running.
        if (destiny$cleanup.isDraining()) {
            ci.cancel();
            return;
        }
        var info = (GameTestInfo) (Object) this;
        if (!info.isDone()) {
            if (destiny$ticking) destiny$cleanupPending = true;
            else TestCleanup.finish(info, destiny$cleanup);
        }
    }

    @WrapMethod(method = "tick")
    private void destiny$trackTerminalTick(GameTestRunner runner, Operation<Void> original) {
        boolean alreadyTicking = destiny$ticking;
        destiny$ticking = true;
        try {
            original.call(runner);
        } finally {
            destiny$ticking = alreadyTicking;
            // Normally drained at the injection below. Also release if native ticking throws.
            if (!alreadyTicking) destiny$drainPendingCleanup();
        }
    }

    @Inject(method = "tick", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/gametest/framework/GameTestInfo;tickInternal()V",
            shift = At.Shift.AFTER))
    private void destiny$cleanupBeforeReporting(GameTestRunner runner, CallbackInfo ci) {
        // Native tickInternal can run more scheduled callbacks after succeed(). Preserve them,
        // then clean once before tick() chooses its pass/fail listener branch.
        destiny$drainPendingCleanup();
    }

    @Unique
    private void destiny$drainPendingCleanup() {
        if (!destiny$cleanupPending) return;
        destiny$cleanupPending = false;
        TestCleanup.finish((GameTestInfo) (Object) this, destiny$cleanup);
    }
}
