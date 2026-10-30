package kim.biryeong.destiny.crucible;

import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import java.util.*;

/** Selected, source-tagged Shaxx Korean cues. One personal commentary channel; no overlapping banks. */
public final class CrucibleSounds {
    private static final Set<String> EVENTS = Set.of("control","start","capture_a","capture_b","capture_c",
            "lost_a","lost_b","lost_c","advantage","enemy_advantage","power_play","enemy_power_play","victory","defeat");
    private static final Map<UUID,String> PLAYING = new HashMap<>();
    private CrucibleSounds() { }
    public static void play(ServerPlayer p,String event) {
        if (!EVENTS.contains(event) || p.hasDisconnected()) return;
        stop(p);
        Identifier sound=Identifier.fromNamespaceAndPath("destiny_crucible",event);
        var at=p.getEyePosition();
        p.connection.send(new ClientboundSoundPacket(Holder.direct(SoundEvent.createFixedRangeEvent(sound,16)),
                SoundSource.VOICE,at.x,at.y,at.z,.8f,1f,p.getRandom().nextLong()));
        PLAYING.put(p.getUUID(),event);
    }
    public static void stop(ServerPlayer p) {
        String event=PLAYING.remove(p.getUUID());
        if(event!=null && !p.hasDisconnected())p.connection.send(new ClientboundStopSoundPacket(
                Identifier.fromNamespaceAndPath("destiny_crucible",event),SoundSource.VOICE));
    }
    public static void zones(ServerPlayer p,ControlMatch.Snapshot before,ControlMatch.Snapshot after) {
        String cue=zoneCue(p.getUUID(),before,after);
        if(cue!=null)play(p,cue);
    }
    /** One cue for the final ownership transition, so simultaneous captures never overlap. */
    static String zoneCue(UUID viewer,ControlMatch.Snapshot before,ControlMatch.Snapshot after) {
        var own=after.members().get(viewer);if(own==null)return null;
        var foe=own==ControlMatch.Team.ALPHA?ControlMatch.Team.BRAVO:ControlMatch.Team.ALPHA;
        int ownBefore=owned(before,own),ownAfter=owned(after,own);
        int foeBefore=owned(before,foe),foeAfter=owned(after,foe);
        if(ownAfter==3 && ownBefore!=3)return "power_play";
        if(foeAfter==3 && foeBefore!=3)return "enemy_power_play";
        if(ownAfter==2 && ownBefore<2)return "advantage";
        if(foeAfter==2 && foeBefore<2)return "enemy_advantage";
        for(String id:ControlMatch.ZONE_IDS) {
            var a=before.zones().get(id).owner();var b=after.zones().get(id).owner();
            if(a==b)continue;
            if(b==own)return "capture_"+id.toLowerCase(Locale.ROOT);
            if(a==own)return "lost_"+id.toLowerCase(Locale.ROOT);
        }
        return null;
    }
    private static int owned(ControlMatch.Snapshot snapshot,ControlMatch.Team team) {
        return (int)snapshot.zones().values().stream().filter(z->z.owner()==team).count();
    }
}
