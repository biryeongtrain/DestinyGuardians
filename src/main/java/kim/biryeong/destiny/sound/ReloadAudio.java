package kim.biryeong.destiny.sound;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponItems;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Direct positional audio using the same vanilla packet as weapon fire.
 * Bounded resource aliases isolate cancellation between concurrent same-clip reloads.
 * No server entity/world mutation, asynchronous tasks, client mods, or registry synchronization.
 * All methods run on the server thread; cosmetic sessions never transfer/authorize ammunition.
 */
public final class ReloadAudio {
    private static final int CHANNELS=32;
    private static final Map<UUID,Session> SESSIONS=new HashMap<>();
    private static final boolean QA_TRACE=Boolean.getBoolean("destiny.sound.qa");
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final String event;
        final boolean stoppable;
        final List<ServerPlayer> recipients;
        final long until;
        final boolean requiresReload;
        final Vec3 position;
        Session(ServerPlayer p,int ticks,boolean requiresReload,String baseEvent) {
            owner=p;level=p.level();stack=p.getMainHandItem();until=now(p)+ticks;
            this.requiresReload=requiresReload;
            String available=null;
            for(int channel=0;channel<CHANNELS;channel++) {
                String candidate=baseEvent+".direct_"+channel;
                if(SESSIONS.values().stream().noneMatch(s -> s.event.equals(candidate))) {
                    available=candidate;break;
                }
            }
            // Saturation still plays the authored clip, but never stops a shared base key.
            stoppable=available!=null;event=stoppable?available:baseEvent;
            position=p.getEyePosition();
            var nearby=new LinkedHashSet<ServerPlayer>();nearby.add(p);
            for(var listener:level.players())if(DestinySounds.canHear(listener,level,position)&&!listener.hasDisconnected())nearby.add(listener);
            recipients=List.copyOf(nearby);
        }
    }
    private ReloadAudio() {}
    private static long now(ServerPlayer p) {return p.level().getServer().getTickCount();}
    private static boolean connected(Session s,ServerPlayer p) {return p.level()==s.level&&!p.hasDisconnected();}
    /** Caller must first accept the real reload. False selects the existing explicit one-shot fallback. */
    public static boolean start(ServerPlayer p,WeaponCatalog.Entry entry,int ticks) {
        stop(p);
        var clip=ReloadAudioProfile.find(entry,ticks);
        if(clip.isEmpty())return false;
        return startEvent(p,entry,ticks,clip.get().event());
    }
    /** Exact intrinsic variant, separate from the same-duration ordinary reload lookup. */
    public static boolean startHoned(ServerPlayer p,WeaponCatalog.Entry entry,int ticks) {
        if(!kim.biryeong.destiny.weapon.WeaponExotics.izanagi(entry)
                ||ticks!=kim.biryeong.destiny.weapon.WeaponIzanagi.RELOAD_TICKS)return false;
        String event="weapon.reload_w84.izanagis_burden.honed."+ticks;
        if(!DestinySounds.has(event))return false;
        stop(p);return startEvent(p,entry,ticks,event);
    }
    /** Last paid shell: its short insertion/closing tail may outlive the reload flag,
     * but an accepted shot, stow or skill still retires only this owner's sound. */
    public static boolean startShotgunFinish(ServerPlayer p,WeaponCatalog.Entry entry) {
        if(!ShotgunReloadAudio.handles(entry))return false;
        stop(p);
        // W210 finish.ogg: 43200 mono samples at 32000 Hz (1.35 s).
        return startEvent(p,entry,27,"weapon.shotgun.reload_finish",false);
    }
    private static boolean startEvent(ServerPlayer p,WeaponCatalog.Entry entry,int ticks,String event) {
        return startEvent(p,entry,ticks,event,true);
    }
    private static boolean startEvent(ServerPlayer p,WeaponCatalog.Entry entry,int ticks,String event,boolean requiresReload) {
        if(!p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()
                || WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isEmpty())return false;
        var s=new Session(p,ticks,requiresReload,event);SESSIONS.put(p.getUUID(),s);
        var sound=DestinySounds.packet(s.event,s.position,SoundSource.PLAYERS,.8f,p.level().getRandom().nextLong());
        for(var listener:s.recipients)if(connected(s,listener)) {
            listener.connection.send(sound);
            if(QA_TRACE)DestinyGuardians.LOGGER.info(
                    "[Reload direct QA] receiver={} event=destiny:{}",listener.getScoreboardName(),s.event);
        }
        return true;
    }
    /** Match the gameplay deadline; positional clips are sent once, just like fire sounds. */
    public static void tick(ServerPlayer p,ItemStack stack,boolean reloading) {
        var s=SESSIONS.get(p.getUUID());if(s==null||s.owner!=p)return;
        if((s.requiresReload&&!reloading) || s.stack!=stack || stack!=p.getMainHandItem() || s.level!=p.level()
                || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected() || now(p)>=s.until) {stop(p);return;}
    }
    public static void stop(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());if(s==null||s.owner!=p)return;
        SESSIONS.remove(p.getUUID());
        if(s.stoppable) {
            var stop=new ClientboundStopSoundPacket(DestinyGuardians.id(s.event),SoundSource.PLAYERS);
            // Retire the captured sound even if a recipient has since changed dimension.
            for(var listener:s.recipients)if(!listener.hasDisconnected())listener.connection.send(stop);
        }
    }
    public static void clear() {for(var s:List.copyOf(SESSIONS.values()))stop(s.owner);}
}
