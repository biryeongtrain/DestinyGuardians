package kim.biryeong.destiny.mixin;

import com.llamalad7.mixinextras.injector.wrapmethod.WrapMethod;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import kim.biryeong.destiny.fx.ServerPoseSampling;
import kr.toxicity.model.api.animation.AnimationProgress;
import kr.toxicity.model.api.animation.AnimationStateHandler;
import kr.toxicity.model.api.bone.BoneMovement;
import kr.toxicity.model.api.bone.RenderedBone;
import kr.toxicity.model.api.nms.DisplayTransformer;
import kr.toxicity.model.api.nms.AnimationBundler;
import org.joml.Vector3f;
import org.joml.Quaternionf;
import kim.biryeong.destiny.fx.EquipmentDisplaySamples;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;

/** Sample LOCAL animation channels before BetterModel composes the hierarchy.
 * Sending future keyframe endpoints, even on a server clock, lets a lagging client's
 * interpolation arrive at contact before the server. Only send the reached snapshot.
 */
@Pseudo
@Mixin(targets = "kr.toxicity.model.api.bone.RenderedBone$BoneStateHandler", remap = false)
public abstract class BetterModelPoseMixin {
    @Shadow @Final private RenderedBone this$0;
    @Shadow @Final private AnimationStateHandler<AnimationProgress> state;
    @Shadow private boolean firstTick;
    @Shadow private boolean skipInterpolation;
    @Unique private boolean destiny$sampled;
    @Unique private final BoneMovement destiny$previous = new BoneMovement();
    @Unique private final BoneMovement destiny$next = new BoneMovement();

    @WrapMethod(method = "tick()Z")
    private boolean destiny$sampleEveryFrame(Operation<Boolean> original) {
        if (ServerPoseSampling.active()) {
            firstTick = true; // Use BM's own dirty and cache invalidation path.
            destiny$sampled = true;
        }
        return original.call();
    }

    @WrapOperation(method = "after", at = @At(value = "INVOKE", target =
            "Lkr/toxicity/model/api/animation/AnimationProgress;animate(Lkr/toxicity/model/api/bone/BoneMovement;Lkr/toxicity/model/api/bone/BoneMovement;)Lkr/toxicity/model/api/bone/BoneMovement;"))
    private BoneMovement destiny$sampleLocal(AnimationProgress next, BoneMovement bind, BoneMovement destination,
                                             Operation<BoneMovement> original) {
        if (!ServerPoseSampling.active()) return original.call(next, bind, destination);
        if (skipInterpolation) return original.call(next, bind, destination);
        state.beforeKeyframe(AnimationProgress.EMPTY).animate(bind, destiny$previous);
        next.animate(bind, destiny$next);
        return destiny$previous.lerp(destiny$next, 1f - state.progress(), destination);
    }

    @WrapMethod(method = "sendTransformation")
    private void destiny$publishFinalTickPose(AnimationBundler bundler, Operation<Void> original) {
        // Both evaluated snapshots previously went down the wire back-to-back.
        // Each packet contains start_interpolation=0, so that restarted a one-tick
        // blend twice in the same client tick. Keep both simulation steps, send
        // only their final reached pose. Unclaimed trackers keep native behavior.
        if (!ServerPoseSampling.active() || ServerPoseSampling.publishing()) original.call(bundler);
    }

    @WrapOperation(method = "sendTransformation", at = @At(value = "INVOKE", target =
            "Lkr/toxicity/model/api/nms/DisplayTransformer;transform(ILorg/joml/Vector3f;Lorg/joml/Vector3f;Lorg/joml/Quaternionf;Lkr/toxicity/model/api/nms/AnimationBundler;)V"))
    private void destiny$copyEquipmentTransform(DisplayTransformer display, int duration, Vector3f position,
            Vector3f scale, Quaternionf rotation, AnimationBundler bundler, Operation<Void> original) {
        original.call(display, duration, position, scale, rotation, bundler);
        EquipmentDisplaySamples.record(this$0, position, scale, rotation);
    }

    @WrapMethod(method = "interpolationDuration")
    private int destiny$oneTickSmoothing(Operation<Integer> original) {
        return destiny$sampled ? (skipInterpolation ? 0 : 1) : original.call();
    }

    @WrapMethod(method = "progress")
    private float destiny$noDoubleInterpolation(Operation<Float> original) {
        return destiny$sampled ? 1 : original.call();
    }
}
