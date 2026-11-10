package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.world.DestinyWorldDistances;
import net.minecraft.server.level.ServerChunkCache;
import net.minecraft.server.level.ServerLevel;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyVariable;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Preserve owned per-level limits when vanilla reapplies PlayerList's global settings to every level. */
@Mixin(ServerChunkCache.class)
public abstract class ServerChunkCacheDistanceMixin {
    @Shadow @Final private ServerLevel level;

    @ModifyVariable(method="setViewDistance", at=@At("HEAD"), argsOnly=true)
    private int destiny$viewDistance(int distance) {
        return DestinyWorldDistances.viewDistance(level, distance);
    }

    @ModifyVariable(method="setSimulationDistance", at=@At("HEAD"), argsOnly=true)
    private int destiny$simulationDistance(int distance) {
        return DestinyWorldDistances.simulationDistance(level, distance);
    }

    @Inject(method="setViewDistance", at=@At("TAIL"))
    private void destiny$viewDistanceChanged(int distance, CallbackInfo ci) {
        DestinyWorldDistances.viewDistanceChanged(level, distance);
    }

    @Inject(method="setSimulationDistance", at=@At("TAIL"))
    private void destiny$simulationDistanceChanged(int distance, CallbackInfo ci) {
        DestinyWorldDistances.simulationDistanceChanged(level, distance);
    }
}
