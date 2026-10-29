package kim.biryeong.destiny.test;

import io.netty.buffer.Unpooled;
import io.netty.channel.embedded.EmbeddedChannel;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.Connection;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.BundlePacket;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.game.ClientboundLevelChunkWithLightPacket;
import net.minecraft.server.network.ServerLoginPacketListenerImpl;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntityTypes;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Real Fabric context identities and native chunk/BE codec, NOT native client rendering or login/authentication certification. */
public final class PacketContextW87GameTests {
    private static final String FLOOR="destiny-test:w78_floor";
    private static void check(GameTestHelper h,boolean yes,String reason){h.assertTrue(yes,Component.literal(reason));}
    private static PacketContext context(Object provider){return ((PacketContextProvider)provider).getPacketContext();}

    @GameTest(structure=FLOOR,maxTicks=10, environment = "destiny-test:w90_isolated")
    public void bareEmbeddedConnectionExplainsWarningAndActualLoginConstructorAddsRegistry(GameTestHelper h) {
        var connection=new Connection(PacketFlow.SERVERBOUND);var channel=new EmbeddedChannel(connection);
        TestCleanup.register(h, channel::finishAndReleaseAll);
        var ctx=context(connection);
        check(h,ctx!=null&&ctx.get(PacketContext.CONNECTION)==connection,"Bare embedded connection already owns a real Fabric context");
        check(h,ctx.get(PacketContext.REGISTRY_ACCESS)==null&&ctx.get(PacketContext.SERVER_INSTANCE)==null,
                "Exact missing-registry condition: a nonnull context alone does NOT establish login metadata");
        check(h,PacketContext.get()==null,"No ambient scope before login-constructor observation");
        new ServerLoginPacketListenerImpl(h.getLevel().getServer(),connection,false);
        check(h,context(connection)==ctx&&ctx.get(PacketContext.REGISTRY_ACCESS)==h.getLevel().getServer().registryAccess()
                &&ctx.get(PacketContext.SERVER_INSTANCE)==h.getLevel().getServer(),"Actual native login constructor/Fabric hook populates registry and server in the SAME context");
        check(h,ctx.get(PacketContext.GAME_PROFILE)==null,"Constructor alone is not profile verification or a completed login");
        check(h,PacketContext.get()==null,"Constructor does not leak global/thread scope");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=10, environment = "destiny-test:w90_isolated")
    public void fixtureContextsMatchExactOwnersAndNestedScopesRestoreWithoutCrossConnectionMutation(GameTestHelper h) {
        var a=TestPlayers.create(h,new Vec3(8,4,8),0,0,"W87_A"+UUID.randomUUID().toString().substring(0,4));
        var b=TestPlayers.create(h,new Vec3(16,4,8),0,0,"W87_B"+UUID.randomUUID().toString().substring(0,4));
        TestCleanup.register(h, ()->{TestPlayers.remove(a);TestPlayers.remove(b);});
        var ca=context(a.connection);var cb=context(b.connection);
        check(h,ca!=cb&&ca.get(PacketContext.REGISTRY_ACCESS)==a.registryAccess()&&cb.get(PacketContext.REGISTRY_ACCESS)==b.registryAccess(),"Separate native connections share only actual server registry");
        check(h,ca.get(PacketContext.SERVER_INSTANCE)==h.getLevel().getServer()&&ca.get(PacketContext.GAME_PROFILE)==a.getGameProfile()
                &&cb.get(PacketContext.GAME_PROFILE)==b.getGameProfile()&&ca.get(PacketContext.CONNECTION)!=cb.get(PacketContext.CONNECTION),"Native server/profile/connection identities exactly match each owner");
        check(h,PacketContext.get()==null,"No ambient context before nested scopes");
        PacketContext.runWithContext((PacketContextProvider)(Object)a.connection,()->{
            check(h,PacketContext.get()==ca,"Outer scope is exact owner A");
            PacketContext.runWithContext((PacketContextProvider)(Object)b.connection,()->check(h,PacketContext.get()==cb,"Inner scope is exact owner B"));
            check(h,PacketContext.get()==ca,"Inner return restores A, not last player" );
            try {PacketContext.runWithContext((PacketContextProvider)(Object)b.connection,()->{throw new IllegalStateException("expected scope unwind");});}
            catch(IllegalStateException ex){check(h,"expected scope unwind".equals(ex.getMessage()),"Only intended exception consumed");}
            check(h,PacketContext.get()==ca,"Exceptional inner scope restores A as well");
        });
        check(h,PacketContext.get()==null&&ca.get(PacketContext.GAME_PROFILE)==a.getGameProfile()&&cb.get(PacketContext.GAME_PROFILE)==b.getGameProfile(),"No thread leak or cross-owner metadata mutation");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=12, environment = "destiny-test:w90_isolated")
    public void actualCinematicChunkSenderIncludesNativeBlockEntityAndRoundTripsOwnerPacket(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(8,4,8),0,0,"W87_C"+UUID.randomUUID().toString().substring(0,4));
        TestCleanup.register(h, ()->{CameraViews.stop(p);TestPlayers.remove(p);});
        h.setBlock(10,4,10,Blocks.CHEST);var chest=h.absolutePos(new BlockPos(10,4,10));
        var chunk=h.getLevel().getChunkAt(chest);
        check(h,chunk.getBlockEntity(chest)!=null&&chunk.getBlockEntity(chest).getType()==BlockEntityTypes.CHEST,"Positive real native chest BE in the transmitted central chunk");
        check(h,context(p.connection).get(PacketContext.REGISTRY_ACCESS)==p.registryAccess(),"Sender connection has actual login-equivalent registry before any packet construction");
        CameraViews.open(p,h.getLevel(),h.absoluteVec(new Vec3(10,6,10)),0,0);
        check(h,CameraViews.get(p)!=null,"Actual production CameraView session active");
        h.runAfterDelay(3,()->{
            var packets=new ArrayList<Packet<?>>();for(var packet:TestPlayers.outbound(p))flatten(packet,packets);
            var found=packets.stream().filter(ClientboundLevelChunkWithLightPacket.class::isInstance).map(ClientboundLevelChunkWithLightPacket.class::cast)
                    .filter(packet->packet.x()==chunk.getPos().x()&&packet.z()==chunk.getPos().z()).toList();
            check(h,!found.isEmpty(),"Actual production CameraViews.tick/PlayerChunkSender queued the chest chunk to its owner connection");
            for(var packet:found) {
                var positions=new HashSet<BlockPos>();packet.chunkData().forEachBlockEntityTag(packet.x(),packet.z(),(pos,type,tag)->{if(type==BlockEntityTypes.CHEST)positions.add(pos.immutable());});
                check(h,positions.contains(chest),"Actual native outgoing chunk contains the real chest BE coordinate/type");
                var buffer=new RegistryFriendlyByteBuf(Unpooled.buffer(),p.registryAccess());
                try {
                    ClientboundLevelChunkWithLightPacket.STREAM_CODEC.encode(buffer,packet);
                    var decoded=ClientboundLevelChunkWithLightPacket.STREAM_CODEC.decode(buffer);var after=new HashSet<BlockPos>();
                    decoded.chunkData().forEachBlockEntityTag(decoded.x(),decoded.z(),(pos,type,tag)->{if(type==BlockEntityTypes.CHEST)after.add(pos.immutable());});
                    check(h,decoded.x()==packet.x()&&decoded.z()==packet.z()&&after.contains(chest)&&buffer.readableBytes()==0,"Actual native chunk/light/BE codec round trip retains identity and consumes all bytes");
                } finally {buffer.release();}
            }
            check(h,PacketContext.get()==null,"Production chunk construction does not leak ambient context");CameraViews.stop(p);h.succeed();
        });
    }
    private static void flatten(Packet<?> packet,List<Packet<?>> out){if(packet instanceof BundlePacket<?> b)for(var child:b.subPackets())flatten(child,out);else out.add(packet);}
}
