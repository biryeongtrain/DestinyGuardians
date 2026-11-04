package kim.biryeong.destiny.strike.devils;

import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSoundEntityPacket;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.server.level.ServerPlayer;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public final class DevilsVoiceFixture {
    private static void check(GameTestHelper h, boolean ok, String text) { h.assertTrue(ok, Component.literal(text)); }
    private static boolean subtitle(ServerPlayer p) { return DisplayHud.getHuds(p).keySet().stream().anyMatch(k -> k.startsWith("destiny:devils_subtitle/")); }
    public static void fallback(GameTestHelper h, ServerPlayer a, ServerPlayer b, java.util.function.Function<ServerPlayer, List<net.minecraft.network.protocol.Packet<?>>> packets) {
        var audience = new ArrayList<ServerPlayer>(); audience.add(a);
        var completed = new AtomicInteger();
        try (var voice = new DevilsVoicePlayback(() -> List.copyOf(audience), token -> completed.incrementAndGet(), line -> false)) {
            packets.apply(a); packets.apply(b);
            check(h, voice.start(1,"80b59f27")==0 && voice.remaining()==60, "Unavailable clip reports fallback to director");
            check(h, subtitle(a) && !subtitle(b), "Only current audience receives fallback subtitle");
            var speaker=DisplayHud.getHud(a,"destiny:devils_subtitle/speaker");
            check(h, speaker!=null && speaker.getExtraData("shape").toString().startsWith("임무 안내:"), "Authored notice is not attributed to source character");
            check(h, packets.apply(a).stream().noneMatch(ClientboundSoundEntityPacket.class::isInstance), "Missing audio sends no sound packet");
            voice.disconnected(a); audience.clear(); audience.add(b);
            for(int i=0;i<4;i++)voice.tick();
            check(h, !subtitle(a) && subtitle(b) && voice.remaining()==56, "Replacement connection gets existing caption without resetting deadline");
            for(int i=4;i<59;i++)voice.tick();
            check(h, subtitle(b) && voice.playing(), "Caption persists through tick 59");
            voice.tick();
            check(h, !subtitle(b) && !voice.playing() && completed.get()==0, "Tick 60 removes caption; director alone owns fallback completion");
            voice.start(2,"unknown-cue");
            check(h, subtitle(b), "Unknown cue still gives generic objective guidance");
            voice.close(); voice.close();
            check(h, !subtitle(b) && completed.get()==0, "Cancellation cannot count as speech completion");
            check(h, packets.apply(b).stream().noneMatch(p -> p instanceof ClientboundSoundEntityPacket || p instanceof ClientboundStopSoundPacket), "Text-only fallback never starts or stops audio");
        }
    }
    public static void original(GameTestHelper h, ServerPlayer player, java.util.function.Function<ServerPlayer, List<net.minecraft.network.protocol.Packet<?>>> packets) {
        var completed = new AtomicInteger();
        try(var voice=new DevilsVoicePlayback(() -> List.of(player), token -> completed.incrementAndGet())) {
            packets.apply(player);
            int ticks=voice.start(3,"80b59f1e");
            check(h, ticks==DevilsVoiceCatalog.line("80b59f1e").orElseThrow().ticks(), "Original full duration retained");
            check(h, packets.apply(player).stream().filter(ClientboundSoundEntityPacket.class::isInstance).count()==1, "Available clip sends exactly one original audio packet");
            for(int i=0;i<ticks-1;i++)voice.tick();
            check(h, completed.get()==0 && subtitle(player), "Original subtitle and callback wait for full duration");
            voice.tick();voice.tick();
            check(h, completed.get()==1 && !subtitle(player), "One original completion with subtitle cleanup");
        }
    }
}
