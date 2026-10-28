package kim.biryeong.destiny.ability.titan;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Bounded lift impulse train; never grants flight or changes gravity flags. */
public final class TitanJump extends Ability {
    private record Lift(TitanAbilities.Context context,long until,double acceleration,double ceiling,long[] last) {}
    private static final Map<UUID,Lift> ACTIVE=new HashMap<>();
    public TitanJump() {super(TitanAbilities.JUMP,GuardianClass.TITAN,AbilitySlot.JUMP,Element.KINETIC,0,"리프트");}
    @Override public boolean activate(ServerPlayer p) {
        if(!TitanAbilities.eligible(p)||p.onGround()||p.isInWater()||p.isInLava()||p.isPassenger()||p.isFallFlying()
                ||Guardians.runtime(p).airJumpsUsed>=1||ACTIVE.containsKey(p.getUUID()))return false;
        var c=TitanAbilities.context(p);if(!c.valid())return false;
        Guardians.runtime(p).airJumpsUsed++;
        double ceiling=TitanAbilities.value(this,"max_up_speed",.5,.1,.8);
        Motion.setVelocity(p,new Vec3(p.getDeltaMovement().x,Math.max(p.getDeltaMovement().y,ceiling),p.getDeltaMovement().z));
        p.resetFallDistance();
        ACTIVE.put(p.getUUID(),new Lift(c,c.level.getGameTime()+TitanAbilities.ticks(this,"duration_ticks",16,40),
                TitanAbilities.value(this,"acceleration",.095,.01,.15),ceiling,new long[]{Long.MIN_VALUE}));
        ClassAbilityEffects.sound(p,Element.ARC,"jump");return true;
    }
    static void tick(MinecraftServer server) {
        for(var entry:List.copyOf(ACTIVE.entrySet())) {
            Lift l=entry.getValue();if(l.context.level.getServer()!=server)continue;
            ServerPlayer p=l.context.owner;long now=l.context.level.getGameTime();
            if(!l.context.valid()||p.onGround()||p.isInWater()||p.isInLava()||p.isPassenger()||p.isFallFlying()||now>=l.until) {
                ACTIVE.remove(entry.getKey());continue;
            }
            if(l.last[0]==now)continue;l.last[0]=now;
            Vec3 v=p.getDeltaMovement();Motion.setVelocity(p,new Vec3(v.x,Math.min(l.ceiling,v.y+l.acceleration),v.z));
            p.resetFallDistance();if(now%3==0)Fx.burst(p.level(),p.position(),Element.ARC,3,.15);
        }
    }
    public static boolean active(ServerPlayer p) {var l=ACTIVE.get(p.getUUID());return l!=null&&l.context.owner==p;}
    static void cleanup(ServerPlayer p) {ACTIVE.remove(p.getUUID());}
    static void clearAll() {ACTIVE.clear();}
}
