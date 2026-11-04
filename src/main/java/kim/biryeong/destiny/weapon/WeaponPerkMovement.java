package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import java.util.*;

/** Assassin's Blade walking/strafe mapping, separate from sprint and existing ADS slowdown.
 * This port has no Destiny Mobility stat: 0-to-100 movement is mapped to native walking x1.4.
 * That ratio is a local normalization, not a claim about current Destiny movement internals. */
public final class WeaponPerkMovement {
    public static final Identifier ID=DestinyGuardians.id("assassins_blade_movement_w195");
    private static final Map<UUID,Session> SESSIONS=new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final net.minecraft.server.level.ServerLevel level;
        final AttributeInstance speed;
        AttributeModifier owned;
        boolean yielded;
        Session(ServerPlayer p) { owner=p;level=p.level();speed=p.getAttribute(Attributes.MOVEMENT_SPEED); }
        void release() {
            if(speed!=null&&owned!=null&&speed.getModifier(ID)==owned)speed.removeModifier(ID);
            owned=null;
        }
    }
    private WeaponPerkMovement() {}
    private static boolean locomotion(ServerPlayer p) {
        return !p.isSprinting()&&!p.isPassenger()&&!p.getAbilities().flying&&!p.isFallFlying()
                &&!p.isSwimming()&&!p.isInWater()&&!p.isInLava()&&!p.onClimbable()&&!p.isVisuallyCrawling();
    }
    public static void update(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        if(s!=null&&(s.owner!=p||s.level!=p.level())) { s.release();SESSIONS.remove(p.getUUID(),s);s=null; }
        if(WeaponAssassinsBlade.remaining(p)<=0) { cleanup(p);return; }
        if(s==null) { s=new Session(p);SESSIONS.put(p.getUUID(),s); }
        if(!locomotion(p)) { s.release();return; }
        if(s.yielded)return;
        if(s.speed==null||s.speed!=p.getAttribute(Attributes.MOVEMENT_SPEED)) { s.release();s.yielded=true;return; }
        if(s.owned!=null) {
            if(s.speed.getModifier(ID)==s.owned)return;
            s.release();s.yielded=true;return;
        }
        if(s.speed.hasModifier(ID)) { s.yielded=true;return; }
        s.owned=new AttributeModifier(ID,.4,AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
        s.speed.addTransientModifier(s.owned);
    }
    public static void cleanup(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        if(s!=null&&s.owner==p) { s.release();SESSIONS.remove(p.getUUID(),s); }
    }
    public static void clear() { for(var s:SESSIONS.values())s.release();SESSIONS.clear(); }
}
