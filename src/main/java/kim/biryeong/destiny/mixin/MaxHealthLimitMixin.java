package kim.biryeong.destiny.mixin;

import net.minecraft.world.entity.ai.attributes.Attributes;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyArgs;
import org.spongepowered.asm.mixin.injection.invoke.arg.Args;

/** Lift only max_health's vanilla 1024 cap. Health storage remains a finite float. */
@Mixin(Attributes.class)
public abstract class MaxHealthLimitMixin {
    @ModifyArgs(method = "<clinit>", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/world/entity/ai/attributes/RangedAttribute;<init>(Ljava/lang/String;DDD)V"))
    private static void destiny$maxHealthRange(Args args) {
        if ("attribute.name.max_health".equals(args.get(0))) args.set(3, (double) Float.MAX_VALUE);
    }
}
