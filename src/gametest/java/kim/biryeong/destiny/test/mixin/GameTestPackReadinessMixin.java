package kim.biryeong.destiny.test.mixin;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.compat.pack.ProfileArmAssets;
import kim.biryeong.destiny.weapon.ProfileWeaponView;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.gametest.framework.GameTestServer;
import net.minecraft.gametest.framework.MultipleTestTracker;
import net.minecraft.resources.Identifier;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.function.BooleanSupplier;

/** Headless ticks run faster than real time; finish async asset setup before test deadlines begin. */
@Mixin(GameTestServer.class)
public abstract class GameTestPackReadinessMixin {
    @Shadow private MultipleTestTracker testTracker;
    @Unique private long destiny$packWaitStarted;

    @Inject(method = "tickServer", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/gametest/framework/GameTestServer;haveTestsStarted()Z"), cancellable = true)
    private void destiny$awaitProfileGraphs(BooleanSupplier haveTime, CallbackInfo ci) {
        if (testTracker != null || !ProfileWeaponView.enabled()
                || !FabricLoader.getInstance().isModLoaded("polymer-autohost")) return;
        if (ProfileArmAssets.graph(Identifier.parse("destiny:weapon/ace_of_spades")) != null) {
            if (destiny$packWaitStarted != 0) {
                DestinyGuardians.LOGGER.info("GameTest asset setup ready after {} ms; starting test clocks",
                        (System.nanoTime() - destiny$packWaitStarted) / 1_000_000);
            }
            return;
        }
        long now = System.nanoTime();
        if (destiny$packWaitStarted == 0) {
            destiny$packWaitStarted = now;
            DestinyGuardians.LOGGER.info("GameTest waits for real profile-graph publication before allocating test fixtures");
        } else if (now - destiny$packWaitStarted > 120_000_000_000L) {
            throw new IllegalStateException("GameTest asset setup failed: profile graph not published within 120 seconds; inspect Polymer startup errors");
        }
        // The MinecraftServer superclass tick has already run: workers and queued server tasks
        // keep progressing. Only fixture allocation / test clocks wait, with no blocking sleep.
        ci.cancel();
    }
}
