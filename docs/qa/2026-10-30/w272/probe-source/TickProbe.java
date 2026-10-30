package qa.mixin;
import qa.SoundProbe;
import net.minecraft.client.Minecraft;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
@Mixin(Minecraft.class) public class TickProbe {
 @Inject(method="tick",at=@At("TAIL")) private void afterTick(CallbackInfo ci){SoundProbe.tickProbe();}
}