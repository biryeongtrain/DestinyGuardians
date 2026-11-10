package kim.biryeong.destiny.mixin;

import net.fabricmc.fabric.impl.networking.server.ServerPlayNetworkAddon;
import net.minecraft.server.MinecraftServer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

@Mixin(value = ServerPlayNetworkAddon.class, remap = false)
public interface ServerPlayNetworkAddonAccessor {
    @Accessor(value = "server", remap = false)
    MinecraftServer destiny$server();
}
