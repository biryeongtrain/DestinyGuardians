package kim.biryeong.destiny.hud;

import kim.biryeong.minigamelib.cinematic.CameraViews;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import java.util.*;

/** Owner-only received-damage feedback, shared with non-Guardians because the health HUD is shared.
 * Uses real post-mitigation loss and immutable impact origins; never damage requests, nearby mobs or aim assist. */
public final class IncomingDamageHud {
    public static final String PREFIX="destiny:hud_incoming_w86_";
    private static final Map<UUID,Session> SESSIONS=new HashMap<>();
    private static boolean initialized;
    private static final class Session {
        final ServerPlayer owner;final ServerLevel level;
        final IncomingDamageState state=new IncomingDamageState();
        Session(ServerPlayer p){owner=p;level=p.level();}
    }
    private IncomingDamageHud() {}
    public static void init() {
        if(initialized)return;initialized=true;
        CriticalHudShader.init();
        ServerPlayConnectionEvents.DISCONNECT.register((handler,server)->cleanup(handler.getPlayer()));
        ServerLivingEntityEvents.AFTER_DEATH.register((entity,source)->{if(entity instanceof ServerPlayer p)cleanup(p);});
        ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((p,from,to)->cleanup(p));
        ServerLifecycleEvents.SERVER_STOPPING.register(server->clear());
    }
    private static boolean eligible(ServerPlayer p) {
        // Our own SuperCamera still shows combat HUD; foreign cinematic/native cameras do not.
        return p.isAlive()&&!p.isRemoved()&&!p.isSpectator()&&!p.hasDisconnected()
                &&p.getCamera()==p&&CameraViews.get(p)==null;
    }
    private static Session session(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        if(s!=null&&(s.owner!=p||s.level!=p.level())) {remove(s);s=null;}
        if(s==null){s=new Session(p);SESSIONS.put(p.getUUID(),s);}
        return s;
    }
    /** Called once for exclusive actual HP+absorption loss, after native Player.actuallyHurt. */
    public static void damaged(ServerPlayer p,DamageSource source,float actualLoss) {
        if(!Float.isFinite(actualLoss)||actualLoss<=0||!eligible(p))return;
        var direct=source.getDirectEntity();var owner=source.getEntity();
        boolean sameLevel=(direct==null||direct.level()==p.level())&&(owner==null||owner.level()==p.level());
        // A projectile can already be at the victim when damage is resolved. Prefer a known
        // responsible attacker, otherwise retain the explicit/direct source position (e.g. blast).
        // Snapshot once; the later HUD must not follow an attacker moving behind a wall.
        var origin=!sameLevel?null:owner!=null&&owner!=p?owner.position():source.getSourcePosition();
        if(origin!=null && Double.isFinite(origin.x)&&Double.isFinite(origin.y)&&Double.isFinite(origin.z)) {
            session(p).state.hit(p.level().getServer().getTickCount(),p.getX(),p.getZ(),origin.x,origin.z);
        }
        update(p);
    }
    public static void update(ServerPlayer p) {
        if(!eligible(p)){cleanup(p);return;}
        long now=p.level().getServer().getTickCount();
        int critical=IncomingDamageState.criticalFrame(now,CombatHud.healthFraction(p));
        var s=SESSIONS.get(p.getUUID());
        if(s!=null&&(s.owner!=p||s.level!=p.level())){remove(s);s=null;}
        if(s==null&&critical<0)return;
        if(s==null)s=session(p);
        var cues=s.state.cues(now);
        if(cues.isEmpty()&&critical<0){remove(s);return;}
        boolean[] visible=new boolean[IncomingDamageState.CAPACITY];
        for(var cue:cues) {
            float angle=IncomingDamageState.bearing(cue.x()-p.getX(),cue.z()-p.getZ(),p.getYRot());
            if(!Float.isFinite(angle))continue;
            visible[cue.slot()]=true;
            String id=PREFIX+"arc_"+cue.slot();
            CombatHud.sprite(p,id,"incoming_w86_arc_"+IncomingDamageState.fadeFrame(now,cue),
                    960,540,320,320,7,0xF25C50,DisplayHud.HudAlignment.CENTER);
            var hud=(ItemDisplayHud)DisplayHud.getHud(p,id);
            // 2-degree steps bound metadata without snapping to only four cardinal directions.
            // displayhud_clip mirrors world X into screen X. Positive Z rotation is clockwise
            // on this HUD; negating the bearing mirrors left/right in the actual framebuffer.
            float rotation=Math.round(angle/2)*2;
            if(!Objects.equals(hud.getExtraData("incomingRotation"),rotation)) {
                // DisplayHud vecToQuat passes arguments to rotateZYX: its FIRST component is Z.
                hud.setExtraData("incomingRotation",rotation);hud.setRightRotation(rotation,0,0);
            }
        }
        for(int i=0;i<visible.length;i++)if(!visible[i])DisplayHud.removeHud(p,PREFIX+"arc_"+i);
        if(critical>=0) {
            CombatHud.sprite(p,PREFIX+"critical","incoming_w89_critical_"+critical,
                    960,540,1920,1080,0,0xB52B25,DisplayHud.HudAlignment.CENTER);
            // Layer0 keeps the critical wash behind ordinary ammo/ability layers1..3 (W99 reversible native proof).
            // Only this owner-local plane opts into subcutoff alpha. Other HUDs keep native cutout.
            // Brightness is not lighting for DisplayHud; 2/3 is distinct from above-hand 1/2.
            var wash = DisplayHud.getHud(p, PREFIX+"critical");
            if(wash.getBrightnessBlock()!=2 || wash.getBrightnessSky()!=3)wash.setBrightness(2,3);
        } else DisplayHud.removeHud(p,PREFIX+"critical");
    }
    public static void cleanup(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        if(s!=null&&s.owner==p)remove(s);
    }
    private static void remove(Session s) {
        for(int i=0;i<IncomingDamageState.CAPACITY;i++)DisplayHud.removeHud(s.owner,PREFIX+"arc_"+i);
        DisplayHud.removeHud(s.owner,PREFIX+"critical");
        SESSIONS.remove(s.owner.getUUID(),s);
    }
    public static void clear() {for(var s:List.copyOf(SESSIONS.values()))remove(s);}
}
