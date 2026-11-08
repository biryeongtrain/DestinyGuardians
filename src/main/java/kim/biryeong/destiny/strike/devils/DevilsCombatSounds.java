package kim.biryeong.destiny.strike.devils;

import com.google.gson.JsonParser;
import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Full-length positional one-shots, restricted to the owning strike's listeners. */
public final class DevilsCombatSounds {
    private static final Map<DevilsPlan.Kind,Map<String,Identifier>> ROUTES=load();
    private DevilsCombatSounds() {}
    private static Map<DevilsPlan.Kind,Map<String,Identifier>> load() {
        try(var in=Objects.requireNonNull(DevilsCombatSounds.class.getResourceAsStream(
                "/destiny/devils_lair/combat-sound-routes.json"));
            var reader=new InputStreamReader(in,StandardCharsets.UTF_8)) {
            var routes=JsonParser.parseReader(reader).getAsJsonObject().getAsJsonObject("routes");
            Map<DevilsPlan.Kind,Map<String,Identifier>> result=new EnumMap<>(DevilsPlan.Kind.class);
            for(var kind:routes.entrySet()) {
                Map<String,Identifier> events=new HashMap<>();
                for(var event:kind.getValue().getAsJsonObject().entrySet())
                    events.put(event.getKey(),Identifier.parse(event.getValue().getAsString().contains(":")
                            ? event.getValue().getAsString() : "destiny_devils_sfx:" + event.getValue().getAsString()));
                result.put(DevilsPlan.Kind.valueOf(kind.getKey()),Map.copyOf(events));
            }
            return Map.copyOf(result);
        }catch(Exception error){throw new IllegalStateException("Invalid Devils combat sound catalog",error);}
    }
    static Identifier event(DevilsPlan.Kind kind, String event) { return ROUTES.getOrDefault(stand(kind),Map.of()).get(event); }
    /** Exodus Crash enemies share the sound set of the same-class Devils Lair enemy until they get their own. */
    private static DevilsPlan.Kind stand(DevilsPlan.Kind kind) {
        return switch(kind) {
            case GOBLIN -> DevilsPlan.Kind.THRALL; case HOBGOBLIN -> DevilsPlan.Kind.ACOLYTE; case HARPY -> DevilsPlan.Kind.WIZARD;
            case MINOTAUR -> DevilsPlan.Kind.KNIGHT; case CYCLOPS -> DevilsPlan.Kind.SERVITOR; case PYKIS -> DevilsPlan.Kind.CAPTAIN;
            default -> kind;
        };
    }
    public static int play(ServerLevel level,List<ServerPlayer> listeners,DevilsPlan.Kind kind,String event,Vec3 at) {
        var id=event(kind,event);
        if(id==null)return 0;
        float range=kind.boss()?64:40;
        float volume=kim.biryeong.destiny.sound.EnemySoundMix.volume(event);
        var packet=new ClientboundSoundPacket(Holder.direct(SoundEvent.createFixedRangeEvent(id,range)),
                SoundSource.HOSTILE,at.x,at.y,at.z,volume,1f,level.getRandom().nextLong());
        int sent=0;
        for(var player:listeners)if(player.level()==level&&!player.hasDisconnected()
                &&player.connection.hasClientLoaded()&&player.position().distanceToSqr(at)<=range*range){
            player.connection.send(packet);sent++;
        }
        return sent;
    }
    /** Only this strike's events; never stop all hostile audio or another activity's sounds. */
    public static void stop(ServerPlayer player) {
        ROUTES.values().stream().flatMap(events->events.values().stream()).distinct().forEach(id->
                player.connection.send(new ClientboundStopSoundPacket(id,SoundSource.HOSTILE)));
    }
}
