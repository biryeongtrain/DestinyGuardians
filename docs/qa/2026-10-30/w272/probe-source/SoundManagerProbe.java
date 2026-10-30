package qa.mixin;
import qa.SoundProbe;
import net.minecraft.client.sounds.SoundManager;
import net.minecraft.client.sounds.SoundEngine;
import net.minecraft.client.resources.sounds.SoundInstance;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
@Mixin(SoundManager.class) public class SoundManagerProbe {
 @Inject(method="play",at=@At("RETURN")) private void afterPlay(SoundInstance sound,CallbackInfoReturnable<SoundEngine.PlayResult> ci){SoundProbe.played(sound,ci.getReturnValue());}
}