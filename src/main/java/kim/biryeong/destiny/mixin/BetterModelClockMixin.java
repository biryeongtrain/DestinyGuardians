package kim.biryeong.destiny.mixin;

import com.llamalad7.mixinextras.injector.wrapmethod.WrapMethod;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import kim.biryeong.destiny.fx.ServerAnimationClock;
import kim.biryeong.destiny.fx.ServerPoseSampling;
import kr.toxicity.model.api.tracker.Tracker;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;

/** BetterModel 3.5.1 normally advances a frame every 25ms, independently of server TPS.
 * Transfer only our player limbs to two frames per server tick, including per-viewer
 * animation and packet bundlers. Do not just pause the global pipeline: per-player
 * caches have their own clocks. All entry paths share this monitor, so claiming a
 * tracker waits out an already-running scheduled frame and prevents double stepping.
 */
@Pseudo
@Mixin(targets = "kr.toxicity.model.api.tracker.Tracker", remap = false)
public abstract class BetterModelClockMixin implements ServerAnimationClock {
    @Shadow private long frame;
    @Shadow private void tick() { throw new AssertionError(); }
    @Shadow private void animationTick() { throw new AssertionError(); }
    @Shadow public abstract boolean isClosed();
    @Unique private boolean destiny$serverOwned;
    @Unique private boolean destiny$advancing;
    @Unique private boolean destiny$animationPermit;
    @Unique private long destiny$frames;

    @Override
    public synchronized void destiny$claimServerClock() {
        destiny$serverOwned = true;
    }

    @Override
    public synchronized void destiny$advanceServerTick() {
        if (!destiny$serverOwned || isClosed()) return;
        destiny$advancing = true;
        try {
            for (int i = 0; i < 2; i++) {
                ++frame;
                ServerPoseSampling.run(i == 1, this::tick);
                ++destiny$frames;
            }
        } finally {
            destiny$advancing = false;
        }
    }

    @Override
    public synchronized void destiny$primeAnimation() {
        if (!destiny$serverOwned || isClosed()) return;
        destiny$advancing = true;
        destiny$animationPermit = true;
        try { ServerPoseSampling.run(this::animationTick); }
        finally { destiny$animationPermit = false; destiny$advancing = false; }
    }

    @Override
    public synchronized long destiny$serverFrames() { return destiny$frames; }

    @WrapMethod(method = "lambda$start$0")
    private void destiny$scheduledFrame(Operation<Void> original) {
        synchronized (this) {
            if (!destiny$serverOwned) original.call();
        }
    }

    @WrapMethod(method = "tick()V")
    private void destiny$frame(Operation<Void> original) {
        synchronized (this) {
            // start() also calls tick directly: it must not advance an owned clock.
            if (!destiny$serverOwned || destiny$advancing) original.call();
        }
    }

    @WrapMethod(method = "animationTick")
    private void destiny$noImplicitAdvance(Operation<Void> original) {
        synchronized (this) {
            if (!destiny$serverOwned) original.call();
            else if (destiny$animationPermit) {
                destiny$animationPermit = false; // Consume before callbacks can re-enter animate().
                original.call();
            }
        }
    }

    @WrapOperation(method = "lambda$new$5", at = @At(value = "INVOKE", target =
            "Lkr/toxicity/model/api/tracker/Tracker;animationTick()V"))
    private void destiny$scheduledAnimationOnly(Tracker tracker, Operation<Void> original) {
        destiny$animationPermit = destiny$serverOwned && destiny$advancing;
        try { original.call(tracker); }
        finally { destiny$animationPermit = false; }
    }
}
