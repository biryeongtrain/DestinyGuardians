package kim.biryeong.destiny.test;

import com.mojang.authlib.GameProfile;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.network.Connection;
import net.minecraft.server.MinecraftServer;

/** Embedded PLAY fixtures bypass Fabric's login constructor/profile verification.
 * Supply exactly the metadata those native login hooks normally store, not a global
 * context, a fake registry or a production fallback. Only disposable test connections.
 */
final class TestPacketContexts {
    private TestPacketContexts() {}
    static void initialize(Connection connection, MinecraftServer server, GameProfile profile) {
        var context=((PacketContextProvider)(Object)connection).getPacketContext();
        put(context,PacketContext.SERVER_INSTANCE,server);
        put(context,PacketContext.REGISTRY_ACCESS,server.registryAccess());
        put(context,PacketContext.GAME_PROFILE,profile);
        if(context.get(PacketContext.CONNECTION)!=connection)throw new IllegalStateException("Fixture context belongs to another connection");
    }
    private static <T> void put(PacketContext context,PacketContext.ReadKey<T> key,T value) {
        // Fabric exposes native keys read-only to consumers, but their actual identity is
        // a Key (confirmed in exact 6.3.10 bytecode). Emulate login only in this fixture.
        if(!(key instanceof PacketContext.Key<?>))throw new IllegalStateException("Fabric native key is no longer writable; update fixture login setup");
        @SuppressWarnings("unchecked") var writable=(PacketContext.Key<T>)key;
        var existing=context.get(key);
        if(existing!=null&&existing!=value)throw new IllegalStateException("Refuse to overwrite another fixture identity");
        context.set(writable,value);
    }
}
