package kim.biryeong.destiny.fx;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ManualAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.protocol.game.ClientboundRemoveEntitiesPacket;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.*;

/** Shot-owned, non-colliding terrain ribbons. One display per live half-block lane, not per particle.
 * Polymer item displays allow each lane to stop/step independently; they do not create world entities
 * or use a second gameplay clock. All methods are server-thread-only. A rejected visual never
 * rejects a paid shot. The authored mesh/texture is an approximation, not extracted Bungie VFX.
 */
public final class WaveCrestVfx implements AutoCloseable {
    public static final int MAX_TOTAL_ELEMENTS=128, MAX_OWNER_ELEMENTS=32;
    private static final double VIEW_DISTANCE_SQUARED=48*48;
    private static final Set<WaveCrestVfx> ACTIVE=Collections.newSetFromMap(new IdentityHashMap<>());
    private final ServerPlayer owner;
    private final ServerLevel level;
    private final Vec3 origin;
    private final boolean stasis;
    private final double laneWidth;
    private final ItemDisplayElement[] lanes;
    private final Vec3[] positions;
    private final Map<UUID,ServerPlayer> viewers=new HashMap<>();
    private final List<Integer> allocatedIds=new ArrayList<>();
    private final Set<ServerGamePacketListenerImpl> pendingRemoval=Collections.newSetFromMap(new IdentityHashMap<>());
    private static boolean initialized;
    private ElementHolder holder;
    private boolean closed;
    private int reserved;
    private int refreshAt;

    public static void init() {
        if(initialized)return;initialized=true;
        ServerTickEvents.END_SERVER_TICK.register(server->{
            for(var visual:List.copyOf(ACTIVE))if(visual.level.getServer()==server&&visual.closed)visual.retryRemoval();
        });
        ServerLifecycleEvents.SERVER_STOPPING.register(server->{
            for(var visual:List.copyOf(ACTIVE))if(visual.level.getServer()==server)visual.close();
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(server->{
            // Every client connection is now closed; there is no surviving remote entity to remove.
            ACTIVE.removeIf(visual->visual.level.getServer()==server);
        });
    }

    public WaveCrestVfx(ServerPlayer owner,Vec3 origin,Vec3 forward,boolean stasis,double laneWidth,int lanes) {
        this.owner=Objects.requireNonNull(owner);this.level=owner.level();this.origin=origin;
        this.stasis=stasis;this.laneWidth=laneWidth;
        if(lanes<1||lanes>32||!Double.isFinite(laneWidth)||laneWidth<=0||laneWidth>1
                ||!finite(origin)||!finite(forward)||Math.abs(forward.y)>1e-6
                ||Math.abs(forward.lengthSqr()-1)>.001)
            throw new IllegalArgumentException("Invalid wave crest geometry");
        this.lanes=new ItemDisplayElement[lanes];positions=new Vec3[lanes];
        if(!valid()||totalElements()+lanes>MAX_TOTAL_ELEMENTS||activeElements(owner)+lanes>MAX_OWNER_ELEMENTS) {
            closed=true;return;
        }
        try {
            holder=new ElementHolder();new ManualAttachment(holder,level,()->origin);
            for(int i=0;i<lanes;i++) {
                var stack=new ItemStack(Items.PAPER);
                stack.set(DataComponents.ITEM_MODEL,DestinyGuardians.id("fx/wave_crest_"+(stasis?"stasis":"void")+"_w79"));
                var display=new ItemDisplayElement(stack);
                display.setItemDisplayContext(ItemDisplayContext.NONE);
                display.setBrightness(new Brightness(15,15));
                // A holder remains at the impact while the wave travels up to15 blocks away.
                display.setViewRange(2);display.setInterpolationDuration(1);display.setTeleportDuration(1);
                display.setScale(new Vector3f((float)laneWidth,1,1));
                display.setLeftRotation(new Quaternionf().rotateY((float)Math.atan2(forward.x,forward.z)));
                for(int id:display.getEntityIds())allocatedIds.add(id);
                this.lanes[i]=display;holder.addElement(display);
            }
            reserved=lanes;
            ACTIVE.add(this);
        } catch(RuntimeException failure) {
            close();DestinyGuardians.LOGGER.warn("Wave crest construction failed: {}",failure.toString());
        }
    }

    /** Copies observational positions only; null lanes can never be resurrected after being removed. */
    public void update(Vec3[] tips,int age,double remainingLength) {
        if(closed)return;
        if(!valid()||tips==null||tips.length!=lanes.length||age<0||age>=100
                ||!Double.isFinite(remainingLength)||remainingLength<=0) {close();return;}
        try {
            float fade=(float)Math.clamp(Math.min((age+1)/2.0,remainingLength/.8),.05,1);
            for(int i=0;i<lanes.length;i++) {
                var display=lanes[i];if(display==null)continue;
                Vec3 tip=tips[i];
                if(!finite(tip)||tip.distanceToSqr(origin)>32*32) {
                    // removeElement sends after detaching, so retain IDs independently even on send failure.
                    holder.removeElementWithoutUpdates(display);lanes[i]=null;positions[i]=null;reserved--;
                    for(var watcher:List.copyOf(holder.getWatchingPlayers()))
                        watcher.send(new ClientboundRemoveEntitiesPacket(display.getEntityIds()));
                    continue;
                }
                positions[i]=tip;
                Vec3 relative=tip.subtract(origin);
                display.setScale(new Vector3f((float)laneWidth,fade,1));
                // NONE centres Java model y at8. The model's floor is y0, hence this lift.
                display.setTranslation(new Vector3f((float)relative.x,(float)relative.y+fade*.5f,(float)relative.z));
                display.startInterpolation();
            }
            if(elements()==0){close();return;}
            if(age>=refreshAt){refreshViewers();refreshAt=age+5;}
            holder.tick();
        } catch(RuntimeException failure) {
            close();DestinyGuardians.LOGGER.warn("Wave crest update failed: {}",failure.toString());
        }
    }

    public boolean visible() {return !closed&&elements()>0;}
    private int elements() {return reserved;}
    private boolean valid() {return level.getServer().isSameThread()&&owner.level()==level&&!owner.isRemoved()
            &&owner.isAlive()&&!owner.hasDisconnected()&&!owner.isSpectator();}
    private static boolean finite(Vec3 p) {return p!=null&&Double.isFinite(p.x)&&Double.isFinite(p.y)&&Double.isFinite(p.z);}
    private boolean nearby(ServerPlayer p) {
        if(p.connection==null||p.hasDisconnected()||p.isRemoved()||p.level()!=level)return false;
        for(var pos:positions)if(pos!=null&&p.position().distanceToSqr(pos)<=VIEW_DISTANCE_SQUARED)return true;
        return false;
    }
    private void refreshViewers() {
        Map<UUID,ServerPlayer> wanted=new HashMap<>();
        for(var p:level.getServer().getPlayerList().getPlayers())if(nearby(p))wanted.put(p.getUUID(),p);
        // Embedded GameTest owners are not necessarily in PlayerList. Actual owner connection still required.
        if(nearby(owner))wanted.put(owner.getUUID(),owner);
        for(var it=viewers.entrySet().iterator();it.hasNext();) {
            var e=it.next();if(wanted.get(e.getKey())!=e.getValue()) {
                holder.stopWatching(e.getValue());it.remove();
            }
        }
        for(var e:wanted.entrySet())if(!viewers.containsKey(e.getKey())) {
            if(holder.startWatching(e.getValue()))viewers.put(e.getKey(),e.getValue());
        }
    }
    @Override public void close() {
        if(closed){retryRemoval();return;}
        closed=true;
        if(holder!=null) {
            pendingRemoval.addAll(holder.getWatchingPlayers());
            for(var p:viewers.values())pendingRemoval.add(p.connection);
            // Retain all original IDs, including lanes already detached when a send failed.
            for(var watcher:List.copyOf(holder.getWatchingPlayers())) {
                try {holder.stopWatching(watcher);}
                catch(RuntimeException failure) {DestinyGuardians.LOGGER.warn("Wave crest viewer cleanup failed: {}",failure.toString());}
            }
            try {holder.destroy();}
            catch(RuntimeException failure) {DestinyGuardians.LOGGER.warn("Wave crest cleanup failed: {}",failure.toString());}
            finally {
                try {holder.setAttachment(null);}
                catch(RuntimeException failure) {DestinyGuardians.LOGGER.warn("Wave crest detach failed: {}",failure.toString());}
            }
            holder=null;
        }
        viewers.clear();Arrays.fill(positions,null);Arrays.fill(lanes,null);
        // A failed removal still owns its budget until retry succeeds or the connection closes.
        reserved=allocatedIds.size();retryRemoval();
    }
    private void retryRemoval() {
        var packet=new ClientboundRemoveEntitiesPacket(allocatedIds.stream().mapToInt(Integer::intValue).toArray());
        pendingRemoval.removeIf(watcher->{
            try {if(watcher.isAcceptingMessages())watcher.send(packet);return true;}
            catch(RuntimeException failure) {return false;}
        });
        if(pendingRemoval.isEmpty()){reserved=0;allocatedIds.clear();ACTIVE.remove(this);}
    }
    public record Snapshot(UUID owner,int elements,List<Vec3> positions,List<UUID> viewers,boolean stasis) {}
    public static List<Snapshot> snapshots() {return ACTIVE.stream().filter(s->!s.closed).map(s->new Snapshot(s.owner.getUUID(),s.elements(),
            Arrays.stream(s.positions).filter(Objects::nonNull).toList(),List.copyOf(s.viewers.keySet()),s.stasis)).toList();}
    public static int activeElements(ServerPlayer owner) {return ACTIVE.stream().filter(s->s.owner==owner).mapToInt(WaveCrestVfx::elements).sum();}
    public static int totalElements() {return ACTIVE.stream().mapToInt(WaveCrestVfx::elements).sum();}
    public static int pendingCleanupCount() {return (int)ACTIVE.stream().filter(s->s.closed).count();}
}
