package kim.biryeong.destiny.strike.devils;

import com.google.gson.*;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.minigamelib.MinigameLib;
import kim.biryeong.minigamelib.Playback;
import kim.biryeong.minigamelib.music.MusicPacks;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Session-owned bank-derived music. No category-wide stop and no filenames-as-playlists. */
final class DevilsMusic implements AutoCloseable {
    private static final JsonObject DATA=load();
    private final Map<ServerPlayer,Listener> listeners=new IdentityHashMap<>();
    private final long seed=new Random().nextLong();
    private static final class Listener {
        final DevilsMusicTimeline timeline;
        Playback playback;
        Listener(long seed){timeline=new DevilsMusicTimeline(DATA,seed);}
        void stop(){if(playback!=null)playback.stop();playback=null;}
    }
    private static JsonObject load() {
        try(var reader=new InputStreamReader(Objects.requireNonNull(DevilsMusic.class.getResourceAsStream(
                "/destiny/devils_lair/music.json")),StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader).getAsJsonObject();
        }catch(Exception e){throw new IllegalStateException("Invalid Devils music catalog",e);}
    }
    static int section(DevilsDirector.Phase phase) {
        return switch(phase) {
            case READY,BRIEFING,CLOSED -> -1;
            case RY_APPROACH,RY_CLEAR,RF_ENTRY -> 0;
            case RF_DEVICE -> 1;
            case RF_HACK,RF_DEFENSE1 -> 2;
            case RF_INTERMISSION1,RF_DEFENSE2 -> 3;
            case RF_INTERMISSION2,RF_DEFENSE3 -> 4;
            case RF_CLEAR,BL_BATTLE -> 5;
            case BL_CLEAR,SP_GUARD,SP_INTRO -> 6;
            case SP_DAMAGE1,SP_SHIELD1,SP_RECOVER1,SP_DAMAGE2,SP_SHIELD2,SP_RECOVER2,SP_DAMAGE3 -> 7;
            case COMPLETE -> 9;
        };
    }
    void tick(DevilsDirector.Phase phase,List<ServerPlayer> audience,long now) {
        int desired=section(phase);
        if(desired<0){close();return;}
        var ready=audience.stream().filter(p->!p.hasDisconnected()&&p.connection.hasClientLoaded()&&MusicPacks.ready(p)).toList();
        for(var p:List.copyOf(listeners.keySet()))if(!ready.contains(p))remove(p);
        for(var p:ready) {
            // Each listener joins the CURRENT phase immediately. Reconnect/pack readiness cannot reset teammates.
            var listener=listeners.computeIfAbsent(p,k->new Listener(seed));
            var change=listener.timeline.update(desired,now);
            if(change.stop())listener.stop();
            if(change.segment()==null)continue;
            var clip=DATA.getAsJsonObject("segments").getAsJsonObject(change.segment().toString());
            var event=Identifier.fromNamespaceAndPath("destiny_music",clip.get("event").getAsString());
            listener.playback=MinigameLib.get(p.level().getServer()).music().playSound(
                    event,clip.get("seconds").getAsDouble(),1f,List.of(p),true,SoundSource.RECORDS);
            DestinyGuardians.LOGGER.info("[Devils music] player={} section={} segment={} transition={}",
                    p.getScoreboardName(),listener.timeline.section(),change.segment(),change.transition());
        }
    }
    void remove(ServerPlayer p){var listener=listeners.remove(p);if(listener!=null)listener.stop();}
    @Override public void close(){listeners.values().forEach(Listener::stop);listeners.clear();}
}
