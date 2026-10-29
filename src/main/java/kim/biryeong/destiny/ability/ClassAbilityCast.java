package kim.biryeong.destiny.ability;

import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.function.BooleanSupplier;

/** Owner-scoped preparation/contact/recovery for source-backed class abilities. */
public final class ClassAbilityCast {
    private static final Map<ServerPlayer, Cast> ACTIVE = new IdentityHashMap<>();
    private static final class Cast {
        final ServerPlayer owner; final ServerLevel level; final GuardianData data;
        final GuardianRuntime runtime; final Loadout loadout; final Identifier ability;
        final String clip; final Vec3 origin; final BooleanSupplier external; final Runnable emission;
        final ThrowTimeline timeline; boolean modeled, camera;
        Cast(ServerPlayer p, Identifier ability, String clip, int release, int duration,
             BooleanSupplier external, Runnable emission) {
            owner=p; level=p.level(); data=Guardians.data(p); runtime=Guardians.runtime(p);
            loadout=data.loadout().orElse(null); this.ability=ability; this.clip="h15_"+clip;
            origin=p.position(); this.external=external; this.emission=emission;
            timeline=new ThrowTimeline(level.getGameTime(),release,duration);
        }
        boolean valid() {
            return owner.isAlive()&&!owner.isRemoved()&&!owner.isSpectator()&&!owner.hasDisconnected()
                    &&!owner.isSleeping()&&!owner.isPassenger()&&!owner.isFallFlying()&&!owner.getAbilities().flying
                    &&owner.level()==level&&owner.getAttachedOrElse(Guardians.DATA,null)==data
                    &&Guardians.runtimeIfPresent(owner).orElse(null)==runtime&&runtime.superSession==null
                    &&data.loadout().orElse(null)==loadout
                    &&Objects.equals(AbilityService.idOf(owner,AbilitySlot.CLASS_ABILITY),ability)
                    &&owner.position().distanceToSqr(origin)<1
                    &&(!camera||SuperCamera.active(owner))&&external.getAsBoolean();
        }
    }
    private ClassAbilityCast() { }
    public static boolean begin(ServerPlayer p, Identifier ability, String clip,
                                BooleanSupplier valid, Runnable emission) {
        if(ACTIVE.containsKey(p)||GrenadeThrow.active(p)||AbilityService.inSuper(p)
                ||!Objects.equals(AbilityService.idOf(p,AbilitySlot.CLASS_ABILITY),ability)) return false;
        var timing=kim.biryeong.destiny.fx.ClassAbilityTiming.of(clip);
        int release=timing.contactTicks(),duration=timing.durationTicks();
        Cast c=new Cast(p,ability,clip,release,duration,valid,emission);
        if(!c.valid())return false;
        // A sword camera is ours to replace; foreign cinematic cameras are never adopted.
        SuperCamera.stopSword(p);
        if(SuperCamera.active(p))return false;
        ACTIVE.put(p,c);
        c.modeled=PlayerAnimations.play(p,clip);
        if(c.modeled) {
            if(!SuperCamera.startThirdPerson(p)){cleanup(p);return false;}
            c.camera=SuperCamera.active(p);
            SuperCamera.blockMovement(p,duration);
            PlayerAnimations.superEmptyHands(p);
        }
        return true;
    }
    public static void tick(MinecraftServer server) {
        for(Cast c:List.copyOf(ACTIVE.values())) {
            if(c.level.getServer()!=server)continue;
            long now=c.level.getGameTime();boolean valid=c.valid();
            try {
                if(c.timeline.release(now,valid)) c.emission.run();
            } catch(RuntimeException failure) {
                cleanup(c.owner);
                kim.biryeong.destiny.DestinyGuardians.LOGGER.warn("Class ability contact failed",failure);
                continue;
            }
            if(!valid||c.timeline.finished(now))cleanup(c.owner);
        }
    }
    public static boolean active(ServerPlayer p) {return ACTIVE.containsKey(p);}
    public static int age(ServerPlayer p) {Cast c=ACTIVE.get(p);return c==null?-1:c.timeline.age(c.level.getGameTime());}
    public static void cleanup(ServerPlayer p) {
        Cast c=ACTIVE.remove(p);if(c==null)return;
        boolean ownsClip=c.modeled&&c.clip.equals(PlayerAnimations.activeClip(p));
        if(ownsClip)PlayerAnimations.stop(p);
        if(c.camera&&!AbilityService.inSuper(p)&&(!PlayerAnimations.isPlaying(p)||ownsClip))SuperCamera.stop(p);
    }
    public static void clearAll() {for(var p:List.copyOf(ACTIVE.keySet()))cleanup(p);}
}
