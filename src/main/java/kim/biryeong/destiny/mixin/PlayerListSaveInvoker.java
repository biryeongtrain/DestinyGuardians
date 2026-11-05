package kim.biryeong.destiny.mixin;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.players.PlayerList;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/** Lets the economy save a player's inventory right after an item moves into or out of the ledger. */
@Mixin(PlayerList.class)
public interface PlayerListSaveInvoker {
    @Invoker("save") void destiny$save(ServerPlayer player);
}
