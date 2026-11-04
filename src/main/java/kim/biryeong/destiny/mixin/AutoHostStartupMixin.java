package kim.biryeong.destiny.mixin;

import kim.biryeong.destiny.compat.pack.StartupPackCoordinator;
import net.minecraft.server.MinecraftServer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/** Do not intercept explicit operator generation commands or arbitrary builds. */
@Pseudo
@Mixin(targets = "eu.pb4.polymer.autohost.impl.AutoHost", remap = false)
public abstract class AutoHostStartupMixin {
    @Redirect(method = "init(Lnet/minecraft/server/MinecraftServer;)V", at = @At(value = "INVOKE",
            target = "Leu/pb4/polymer/autohost/impl/AutoHost;startResourcePackGeneration(Lnet/minecraft/server/MinecraftServer;)V"),
            require = 2, allow = 2)
    private static void destiny$orderStartupPack(MinecraftServer server) {
        StartupPackCoordinator.request(server);
    }
}
