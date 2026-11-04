package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.weapon.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Server-only sword camera, stance loops and accepted-attack visuals.
 * No ammo, damage, input, movement or inventory mutation. */
public final class SwordPresentation {
    private static final Map<UUID,Binding> BOUND=new HashMap<>();
    private static final class Binding {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        boolean attempted;
        boolean stanceAttempted;
        Binding(ServerPlayer p) {owner=p;level=p.level();stack=p.getMainHandItem();}
    }
    private SwordPresentation() {}

    public static String clip(SwordProfile.Shape shape,boolean heavy,int combo) {
        if(!heavy)return "sword_light_"+Math.clamp(combo,1,3);
        return "sword_"+switch(shape) {
            case UPPERCUT -> "uppercut";
            case DASH -> "dash";
            case SLAM -> "slam";
            case VORTEX -> "vortex";
            case CASTER -> "caster";
        };
    }

    private static boolean eligible(ServerPlayer p) {
        return SwordItems.isSword(p.getMainHandItem())&&p.isAlive()&&!p.isRemoved()&&!p.isSpectator()
                &&!p.hasDisconnected()&&!AbilityService.inSuper(p)&&WeaponLoadout.canUse(p);
    }
    public static void tick(ServerPlayer p) {
        if(!eligible(p)) {
            cleanup(p);return;
        }
        Binding b=BOUND.get(p.getUUID());
        if(b==null||b.owner!=p||b.level!=p.level()||b.stack!=p.getMainHandItem()) {
            cleanup(p);b=new Binding(p);BOUND.put(p.getUUID(),b);
        }
        // Do not steal an ability's final recovery or a foreign cinematic. Only one
        // camera attempt per binding; a failed rotation watchdog must not loop-reacquire.
        if(!b.attempted&&!PlayerAnimations.foreignToSword(p)&&!SuperCamera.active(p)) {
            b.attempted=true;
            SuperCamera.startSword(p);
        }
        // One attempt per exact binding. A missing/closed cosmetic or camera
        // watchdog must not be recreated and re-hide the player every tick.
        if(!b.stanceAttempted&&!PlayerAnimations.foreignToSword(p)&&SuperCamera.swordActive(p)) {
            b.stanceAttempted=true;
            PlayerAnimations.swordPose(p,SwordStance.select(
                    WeaponRuntime.swordStatus(p).map(WeaponRuntime.SwordStatus::guarding).orElse(false),p.onGround(),0));
        }
    }

    /** Call only after the authoritative attack has passed every gameplay gate. */
    public static boolean attack(ServerPlayer p,SwordProfile.Shape shape,boolean heavy,int combo) {
        if(!eligible(p))return false;
        tick(p);
        return PlayerAnimations.swordAttack(p,clip(shape,heavy,combo));
    }

    public static void cleanup(ServerPlayer p) {
        Binding b=BOUND.get(p.getUUID());
        if(b!=null&&b.owner==p)BOUND.remove(p.getUUID());
        PlayerAnimations.stopSword(p);
        SuperCamera.stopSword(p);
    }
    public static void clearAll() {
        for(var b:java.util.List.copyOf(BOUND.values()))cleanup(b.owner);
        BOUND.clear();
    }
}
