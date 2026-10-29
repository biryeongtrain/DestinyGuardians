package kim.biryeong.destiny.ability;

import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;
import java.util.function.BooleanSupplier;

/** Accepted throw windup and recovery shared by all three classes. Inventory is never replaced. */
public final class GrenadeThrow {
    public static final int RELEASE_TICKS = 6, DURATION_TICKS = 20;
    private static final Map<ServerPlayer, Cast> ACTIVE = new IdentityHashMap<>();
    private static final class Cast {
        final ServerPlayer owner; final ServerLevel level; final GuardianData data;
        final GuardianRuntime runtime; final Loadout loadout; final GuardianClass cls;
        final BooleanSupplier external; final Runnable emission; final ItemStack prop;
        final ThrowTimeline timeline; boolean modeled;
        Cast(ServerPlayer p, ItemStack prop, BooleanSupplier external, Runnable emission) {
            owner=p; level=p.level(); data=Guardians.data(p); runtime=Guardians.runtime(p);
            loadout=data.loadout().orElse(null); cls=data.guardianClass();
            this.prop=prop.copy(); this.external=external; this.emission=emission;
            timeline=new ThrowTimeline(level.getGameTime(),RELEASE_TICKS,DURATION_TICKS);
        }
        boolean valid() {
            return owner.isAlive()&&!owner.isRemoved()&&!owner.isSpectator()&&!owner.hasDisconnected()
                    &&owner.level()==level&&owner.getAttachedOrElse(Guardians.DATA,null)==data
                    &&Guardians.runtimeIfPresent(owner).orElse(null)==runtime&&runtime.superSession==null
                    &&data.guardianClass()==cls&&data.loadout().orElse(null)==loadout&&external.getAsBoolean();
        }
    }
    private GrenadeThrow() {}
    public static boolean begin(ServerPlayer p, Identifier ability, ItemStack prop, BooleanSupplier valid, Runnable emission) {
        if(ACTIVE.containsKey(p)||AbilityService.inSuper(p)||!Objects.equals(AbilityService.idOf(p,AbilitySlot.GRENADE),ability))return false;
        Cast c=new Cast(p,prop,valid,emission);if(!c.valid())return false;
        ACTIVE.put(p,c);
        c.modeled=PlayerAnimations.play(p,"grenade");
        if(c.modeled) PlayerAnimations.superItems(p,ItemStack.EMPTY,prop);
        return true;
    }
    public static void tick(MinecraftServer server) {
        for(Cast c:List.copyOf(ACTIVE.values())) {
            if(c.level.getServer()!=server)continue;
            long now=c.level.getGameTime();boolean valid=c.valid();
            if(c.timeline.release(now,valid)) {
                if(c.modeled)PlayerAnimations.superEmptyHands(c.owner);
                c.emission.run();
            }
            if(!valid||c.timeline.finished(now)) cleanup(c.owner);
        }
    }
    public static net.minecraft.world.phys.Vec3 origin(ServerPlayer p) {
        var eye=p.getEyePosition();var look=p.getLookAngle();
        var side=look.cross(new net.minecraft.world.phys.Vec3(0,1,0)).normalize();
        double hand=p.getMainArm()==net.minecraft.world.entity.HumanoidArm.LEFT?.22:-.22;
        var from=eye.add(look.scale(.3)).add(side.scale(hand)).add(0,-.18,0);
        var hit=p.level().clip(new net.minecraft.world.level.ClipContext(eye,from,
                net.minecraft.world.level.ClipContext.Block.COLLIDER,net.minecraft.world.level.ClipContext.Fluid.NONE,p));
        return hit.getType()==net.minecraft.world.phys.HitResult.Type.MISS?from:eye;
    }
    public static boolean active(ServerPlayer p) {Cast c=ACTIVE.get(p);return c!=null&&c.valid();}
    public static int age(ServerPlayer p) {Cast c=ACTIVE.get(p);return c==null?DURATION_TICKS:c.timeline.age(c.level.getGameTime());}
    public static ItemStack prop(ServerPlayer p) {Cast c=ACTIVE.get(p);return c==null||c.timeline.emitted()?ItemStack.EMPTY:c.prop.copy();}
    public static void cleanup(ServerPlayer p) {Cast c=ACTIVE.remove(p);if(c!=null&&c.modeled&&"h15_grenade".equals(PlayerAnimations.activeClip(p)))PlayerAnimations.stop(p);}
    public static void clearAll() {for(var p:List.copyOf(ACTIVE.keySet()))cleanup(p);}
}
