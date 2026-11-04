package kim.biryeong.destiny.fx;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.EntityAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.util.Brightness;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import java.util.*;

/** One cosmetic, non-colliding display per guarding player. No tasks, projectiles or damage hitboxes. */
public final class GlaiveShieldVfx {
    private record Shield(ServerPlayer owner,ElementHolder holder,ItemDisplayElement display) {}
    private static final Map<UUID,Shield> ACTIVE=new HashMap<>();
    private static final class Attachment extends EntityAttachment {
        final ServerPlayer owner;
        Attachment(ElementHolder holder,ServerPlayer owner) { super(holder,owner,false);this.owner=owner;attach(); }
        @Override public void updateCurrentlyTracking(Collection<ServerGamePacketListenerImpl> watching) {
            super.updateCurrentlyTracking(watching.stream().filter(p->p!=owner.connection).toList());
            if(!owner.isRemoved()&&!owner.hasDisconnected())holder().startWatching(owner);
        }
    }
    private GlaiveShieldVfx() {}
    public static void update(ServerPlayer player,boolean active) {
        if(!active||!player.isAlive()||player.isRemoved()||player.isSpectator()) {remove(player);return;}
        Shield s=ACTIVE.get(player.getUUID());
        if(s!=null&&s.owner()!=player){remove(player);s=null;}
        if(s==null) {
            var holder=new ElementHolder();var item=new ItemStack(Items.PAPER);
            item.set(DataComponents.ITEM_MODEL,DestinyGuardians.id("fx/glaive_shield_w41"));
            var d=new ItemDisplayElement(item);d.setItemDisplayContext(ItemDisplayContext.NONE);
            d.setBrightness(new Brightness(15,15));d.setViewRange(1);d.setTeleportDuration(1);
            d.setInterpolationDuration(1);d.setScale(new Vector3f(1.55f));holder.addElement(d);
            new Attachment(holder,player);holder.startWatching(player);
            s=new Shield(player,holder,d);ACTIVE.put(player.getUUID(),s);
        }
        Vec3 forward=player.getLookAngle().normalize();
        Vec3 center=player.getEyePosition().subtract(player.position()).add(forward.scale(.95)).add(0,-.12,0);
        s.display().setTranslation(new Vector3f((float)center.x,(float)center.y,(float)center.z));
        s.display().setLeftRotation(new Quaternionf().rotateTo(new Vector3f(0,0,1),
                new Vector3f((float)forward.x,(float)forward.y,(float)forward.z)));
        s.holder().tick();
    }
    public static int displays(ServerPlayer owner) {var s=ACTIVE.get(owner.getUUID());return s!=null&&s.owner()==owner?1:0;}
    public static void remove(ServerPlayer owner) {var s=ACTIVE.remove(owner.getUUID());if(s!=null)s.holder().destroy();}
}
