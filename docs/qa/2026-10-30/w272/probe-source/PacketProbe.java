package qa.mixin;
import qa.SoundProbe;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientPacketListener;
import net.minecraft.network.protocol.game.ClientboundSoundEntityPacket;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
@Mixin(ClientPacketListener.class) public class PacketProbe {
 @Inject(method="handleSoundEntityEvent",at=@At("RETURN")) private void afterPacket(ClientboundSoundEntityPacket p,CallbackInfo ci){if(!p.getSound().value().location().getNamespace().equals("destiny"))return;var mc=Minecraft.getInstance();var e=mc.level==null?null:mc.level.getEntity(p.getId());System.out.println("[W272 sound] packet event="+p.getSound().value().location()+" emitter="+p.getId()+" entity="+e);}
}