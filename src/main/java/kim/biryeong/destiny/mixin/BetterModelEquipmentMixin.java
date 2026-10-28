package kim.biryeong.destiny.mixin;

import com.llamalad7.mixinextras.injector.wrapmethod.WrapMethod;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import kim.biryeong.destiny.fx.ServerEquipmentMapping;
import kr.toxicity.model.api.bone.BoneItemMapper;
import kr.toxicity.model.api.bone.BoneRenderContext;
import kr.toxicity.model.api.bone.RenderedBone;
import kr.toxicity.model.api.util.TransformedItemStack;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import java.util.function.Predicate;
import java.util.function.Supplier;

/** BM3.5.1 evaluates its mapper BEFORE itemLock. A late context/packet refresh can
 * otherwise commit a real hand after our prop, or an old prop after clear.
 * Resolve owned hands again at the native commit boundary under the SAME lock.
 * Do not change original mapper/transform, unrelated bones, inventory or clocks.
 */
@Pseudo
@Mixin(targets="kr.toxicity.model.api.bone.RenderedBone",remap=false)
public abstract class BetterModelEquipmentMixin implements ServerEquipmentMapping {
    @Shadow @Final private Object itemLock;
    @Shadow private volatile BoneRenderContext renderContext;
    @Shadow private BoneItemMapper itemMapper;
    @Shadow private volatile TransformedItemStack itemStack;
    @Unique private Supplier<TransformedItemStack> destiny$equipment;

    @Override
    public void destiny$bindEquipment(Supplier<TransformedItemStack> selection) {
        synchronized(itemLock) {
            if(destiny$equipment!=null) throw new IllegalStateException("Equipment bone already owned");
            destiny$equipment=java.util.Objects.requireNonNull(selection);
        }
    }

    @WrapMethod(method="itemStack(Ljava/util/function/Predicate;Lkr/toxicity/model/api/util/TransformedItemStack;)Z")
    private boolean destiny$currentEquipmentAtCommit(Predicate<RenderedBone> predicate, TransformedItemStack incoming,
                                                     Operation<Boolean> original) {
        // Even the unowned path takes this native lock: an evaluation already in flight
        // before bind must serialize with bind rather than bypass ownership after it.
        synchronized(itemLock) {
            if(destiny$equipment!=null) {
                var forced=destiny$equipment.get();
                incoming=forced!=null?forced:itemMapper.apply(renderContext,itemStack);
            }
            return original.call(predicate,incoming);
        }
    }
}
