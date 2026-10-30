package kim.biryeong.destiny.fx;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.EntityAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.guardian.Element;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.entity.Display;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import java.util.ArrayList;
import java.util.Collection;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import java.util.List;

/** H25 weapon-attached cosmetic energy. Six reusable vanilla displays, no damage/tasks/clock.
 * One bundle per owner, eight globally, 420t watchdog. Pose absence allocates no displays.
 */
final class SuperEnergyVfx {
    private static final int MAX_OWNERS = 8, SLOTS = 6;
    private static final List<Energy> ACTIVE = new ArrayList<>();
    private static final class Energy {
        final ServerPlayer owner;
        final ServerLevel level;
        final Element element;
        final int born;
        int expires, lastTick = Integer.MIN_VALUE, flashUntil;
        Vec3 release, direction, origin;
        int releasedAt;
        ElementHolder holder;
        final List<ItemDisplayElement> displays = new ArrayList<>();
        Energy(ServerPlayer owner, Element element) {
            this.owner=owner;this.element=element;level=owner.level();
            born=level.getServer().getTickCount();expires=born+420;
        }
        boolean valid(int tick) {
            return tick<expires && owner.level()==level && owner.isAlive() && !owner.isSpectator()
                    && !owner.isRemoved() && !owner.hasDisconnected();
        }
    }
    /** Polymer entity tracking excludes self and periodically prunes explicit watches. */
    private static final class OwnerAttachment extends EntityAttachment {
        private final ServerPlayer owner;
        OwnerAttachment(ElementHolder holder, ServerPlayer owner) {
            super(holder, owner, false);
            this.owner = owner;
            attach(); // EntityAttachment only auto-attaches its exact base class.
        }
        @Override public void updateCurrentlyTracking(Collection<ServerGamePacketListenerImpl> watching) {
            // Keep the explicit self watch out of Polymer pruning: no repeated destroy/spawn flash.
            super.updateCurrentlyTracking(watching.stream().filter(p -> p != owner.connection).toList());
            if (!owner.hasDisconnected() && !owner.isRemoved()) holder().startWatching(owner);
        }
    }
    private SuperEnergyVfx() { }

    static void start(ServerPlayer owner, Element element) {
        if(owner==null) return;
        cancel(owner);
        if((element!=Element.ARC && element!=Element.VOID) || !owner.isAlive()
                || owner.isSpectator() || owner.isRemoved() || owner.hasDisconnected()) return;
        while(ACTIVE.size()>=MAX_OWNERS) close(ACTIVE.removeFirst());
        ACTIVE.add(new Energy(owner,element));
    }
    static void strike(ServerPlayer owner) {
        for(var e:ACTIVE) if(e.owner==owner && e.element==Element.ARC) e.flashUntil=e.level.getServer().getTickCount()+6;
    }
    static void release(ServerPlayer owner, Vec3 position, Vec3 direction) {
        if(!finite(position)||!finite(direction)||direction.lengthSqr()<1e-8) return;
        for(var e:ACTIVE) if(e.owner==owner && e.element==Element.VOID) {
            e.release=position;e.direction=direction.normalize();e.releasedAt=e.level.getServer().getTickCount();
            e.expires=e.releasedAt+8;
        }
    }
    static void end(ServerPlayer owner) {
        var it=ACTIVE.iterator();
        while(it.hasNext()) {var e=it.next();if(e.owner==owner && e.release==null){it.remove();close(e);}}
    }
    static void tick(MinecraftServer server) {
        var it=ACTIVE.iterator();
        while(it.hasNext()) {
            var e=it.next();if(e.level.getServer()!=server)continue;
            int now=server.getTickCount();
            if(!e.valid(now)){it.remove();close(e);continue;}
            if(e.lastTick==now)continue;e.lastTick=now;
            try { frame(e,now); }
            catch(RuntimeException | LinkageError failure) {
                it.remove();close(e);DestinyGuardians.LOGGER.warn("H25 energy frame failed: {}",failure.toString());
            }
        }
    }
    private static void frame(Energy e,int now) {
        boolean bow=e.element==Element.VOID;
        Vec3 origin=e.release==null?PlayerAnimations.equipmentPoint(e.owner,bow,8,8,8):e.release;
        if(!finite(origin)) { if(e.holder!=null){close(e);} return; }
        if(e.holder==null) {
            e.holder=new ElementHolder();e.origin=origin;
            for(int i=0;i<SLOTS;i++) {
                var d=new AbilityDisplayElement(e.owner,item(e.element,i==4 && bow && e.release==null));
                d.setItemDisplayContext(ItemDisplayContext.NONE);d.setBillboardMode(Display.BillboardConstraints.FIXED);
                d.setBrightness(new Brightness(15,15));d.setViewRange(.6f);d.setTeleportDuration(1);
                d.setInterpolationDuration(1);d.setScale(new Vector3f(0));
                e.holder.addElement(d);e.displays.add(d);
            }
            // Native entity tracking follows movement/chunk changes; ticking stays manager-owned.
            new OwnerAttachment(e.holder,e.owner);
            e.holder.startWatching(e.owner); // A player's own entity tracker does not include self.
        }
        // Relative to the entity's CURRENT position. Release points stay world-fixed while it moves.
        e.origin=e.owner.position();
        var strands=e.release!=null?SuperEnergyGeometry.release(now-e.releasedAt):
                bow?SuperEnergyGeometry.bow(now-e.born):SuperEnergyGeometry.arc(now-e.born);
        for(int i=0;i<SLOTS;i++) {
            var strand=strands.get(i);var d=e.displays.get(i);
            Vec3 from,to;
            if(e.release!=null) {
                from=releasePoint(e,strand.from());to=releasePoint(e,strand.to());
                if(i==4)d.setItem(item(Element.VOID,false));
            } else {
                from=point(e,bow,strand.from());to=point(e,bow,strand.to());
            }
            if(!finite(from)||!finite(to)||from.distanceToSqr(e.owner.position())>64){d.setScale(new Vector3f(0));continue;}
            d.setTranslation(new Vector3f((float)(from.x-e.origin.x),(float)(from.y-e.origin.y),(float)(from.z-e.origin.z)));
            if(strand.spark()) {
                float pulse=(float)(.65+.20*Math.sin((now-e.born)*.75));
                d.setScale(new Vector3f(pulse));d.setLeftRotation(new Quaternionf().rotateXYZ(now*.11f,now*.09f,now*.07f));
            } else {
                var delta=to.subtract(from);double length=delta.length();
                if(length<1e-5 || length>4){d.setScale(new Vector3f(0));continue;}
                float width=e.release!=null?1.35f:bow?(i<2?1.15f:.65f):now<e.flashUntil?2.2f:1.4f;
                d.setScale(new Vector3f(width,width,(float)length));
                d.setLeftRotation(SimProjectile.flightRotation(delta).rotateZ((float)(now*.71+i*1.7)));
            }
            d.startInterpolation();
        }
        e.holder.tick();
    }
    private static Vec3 point(Energy e,boolean bow,Vec3 raw) {
        return PlayerAnimations.equipmentPoint(e.owner,bow,raw.x,raw.y,raw.z);
    }
    private static Vec3 releasePoint(Energy e,Vec3 p) {
        Vec3 right=e.direction.cross(new Vec3(0,1,0));
        right=right.lengthSqr()<1e-8?new Vec3(1,0,0):right.normalize();
        Vec3 up=right.cross(e.direction).normalize();
        return e.release.add(right.scale(p.x)).add(up.scale(p.y)).add(e.direction.scale(p.z));
    }
    private static ItemStack item(Element element,boolean spark) {
        var stack=new ItemStack(Items.STICK);
        stack.set(DataComponents.ITEM_MODEL,DestinyGuardians.id("fx/"+(spark?"void_spark":element==Element.ARC?"arc_filament":"void_filament")+"_h25"));
        return stack;
    }
    static void cancel(ServerPlayer owner) {
        var it=ACTIVE.iterator();while(it.hasNext()){var e=it.next();if(e.owner==owner){it.remove();close(e);}}
    }
    static void clear() { ACTIVE.forEach(SuperEnergyVfx::close);ACTIVE.clear(); }
    private static void close(Energy e) {
        if(e.holder!=null){try{e.holder.destroy();}
            catch(RuntimeException failure){DestinyGuardians.LOGGER.warn("H25 energy cleanup failed: {}",failure.toString());}
            finally{e.holder=null;e.displays.clear();}}
    }
    static int displays(ServerPlayer owner) {return ACTIVE.stream().filter(e->e.owner==owner).mapToInt(e->e.displays.size()).sum();}
    static List<SuperVfx.EnergySnapshot> snapshots() {
        return ACTIVE.stream().map(e->new SuperVfx.EnergySnapshot(e.owner.getUUID(),e.element,e.displays.size(),
                e.release==null?"EQUIP":"RELEASE",e.expires,e.lastTick)).toList();
    }
    private static boolean finite(Vec3 p) {return p!=null && Double.isFinite(p.x)&&Double.isFinite(p.y)&&Double.isFinite(p.z);}
}
