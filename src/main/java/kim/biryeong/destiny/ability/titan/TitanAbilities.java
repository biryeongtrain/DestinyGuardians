package kim.biryeong.destiny.ability.titan;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.ClassAbilityEffects;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;
import java.util.*;
import java.util.function.Consumer;

/** Titan owns these runtimes only. Shared lifecycle/input/visual wiring belongs to the integrator. */
public final class TitanAbilities {
    public static final Identifier JUMP=id("jump"), CLASS_ABILITY=id("class_ability");
    public static final Identifier ARC_GRENADE=id("arc_grenade"), SOLAR_GRENADE=id("solar_grenade"), VOID_GRENADE=id("void_grenade");
    public static final Identifier ARC_MELEE=id("arc_melee"), SOLAR_MELEE=id("solar_melee"), VOID_MELEE=id("void_melee");
    public static final Identifier ARC_SUPER=id("arc_super"), SOLAR_SUPER=id("solar_super"), VOID_SUPER=id("void_super");
    private static final Map<UUID, Context> OWNERS=new HashMap<>();
    private static boolean registered;
    private TitanAbilities() {}
    private static Identifier id(String path) { return DestinyGuardians.id("titan/"+path); }
    public static void register() {
        if (registered) return;
        AbilityRegistry.register(new TitanClassAbility());
        for (Element e:List.of(Element.ARC,Element.SOLAR,Element.VOID)) {
            AbilityRegistry.register(new TitanGrenade(e));
            AbilityRegistry.register(new TitanMelee(e));
            AbilityRegistry.register(new TitanSuper(e));
        }
        TitanExpandedSupers.register();
        TitanClassAbility.init();
        registered=true;
    }
    public static Loadout preset(Element element) {
        String prefix=switch(element) {case SOLAR->"solar";case VOID->"void";default->"arc";};
        return new Loadout(Map.of(AbilitySlot.JUMP,JUMP,AbilitySlot.CLASS_ABILITY,CLASS_ABILITY,
                AbilitySlot.GRENADE,id(prefix+"_grenade"),AbilitySlot.MELEE,id(prefix+"_melee"),AbilitySlot.SUPER,id(prefix+"_super")));
    }
    static String path(Element e,String suffix) {return "titan/"+e.name().toLowerCase(Locale.ROOT)+"_"+suffix;}
    static Identifier abilityId(Element e,String suffix) {return DestinyGuardians.id(path(e,suffix));}
    static boolean eligible(ServerPlayer p) {
        return p.isAlive()&&!p.isRemoved()&&!p.hasDisconnected()&&!p.isSpectator()
                &&Guardians.data(p).guardianClass()==GuardianClass.TITAN;
    }
    static Context context(ServerPlayer p) {
        Context c=OWNERS.get(p.getUUID());
        if(c!=null&&!c.valid()) {cleanup(c.owner);c=null;}
        if(c==null) {c=new Context(p);OWNERS.put(p.getUUID(),c);}
        return c;
    }
    static final class Context {
        final ServerPlayer owner;
        final ServerLevel level;
        final Loadout loadout;
        final List<SimProjectile> shots=new ArrayList<>();
        boolean cancelled;
        Context(ServerPlayer p) {owner=p;level=p.level();loadout=Guardians.data(p).loadout().orElse(null);}
        boolean valid() {return !cancelled&&eligible(owner)&&owner.level()==level
                &&Guardians.data(owner).loadout().orElse(null)==loadout;}
        boolean room() {shots.removeIf(SimProjectile::isDone);return shots.size()<8;}
        boolean launch(Vec3 origin,Vec3 velocity,double gravity,int life,Element e,String path,Consumer<HitResult> impact) {
            return launchFlight(origin,velocity,gravity,life,e,path,impact)!=null;
        }
        SimProjectile launchFlight(Vec3 origin,Vec3 velocity,double gravity,int life,Element e,String path,Consumer<HitResult> impact) {
            if(!valid()||!room())return null;
            SimProjectile flight=SimProjectile.launch(owner,origin,velocity,gravity,life,ClassAbilityEffects.item(path),.65f,e.color(),
                    hit->{if(valid())impact.accept(hit);});
            shots.add(flight);
            return flight;
        }
    }
    static double value(Ability a,String key,double fallback,double min,double max) {
        double v=a.param(key,fallback);return Double.isFinite(v)?Math.clamp(v,min,max):fallback;
    }
    static int ticks(Ability a,String key,int fallback,int max) {return (int)value(a,key,fallback,1,max);}
    static boolean enemy(ServerPlayer p,LivingEntity e) {
        return Combat.isEnemy(p,e)&&!p.isAlliedTo(e)&&!(e instanceof TamableAnimal t&&t.isTame());
    }
    static boolean visible(Context c,Vec3 from,LivingEntity e) {
        return c.valid()&&e.level()==c.level&&enemy(c.owner,e)
                &&c.level.clip(new ClipContext(from,e.getBoundingBox().getCenter(),ClipContext.Block.COLLIDER,
                ClipContext.Fluid.NONE,c.owner)).getType()==HitResult.Type.MISS;
    }
    static List<LivingEntity> targets(Context c,Vec3 from,double radius) {
        return Combat.enemiesNear(c.level,c.owner,from,radius).stream().filter(e->visible(c,from,e)).toList();
    }
    /** Keep an impact on the incoming face of a wall, rather than damaging through its far face. */
    static Vec3 impactPosition(HitResult hit) {
        if(hit instanceof BlockHitResult b)return hit.getLocation().add(new Vec3(b.getDirection().getStepX(),b.getDirection().getStepY(),b.getDirection().getStepZ()).scale(.08));
        return hit.getLocation();
    }
    public static void tick(MinecraftServer server) {
        for(Context c:List.copyOf(OWNERS.values())) {
            if(c.level.getServer()!=server)continue;
            if(!c.valid())cleanup(c.owner);
            else c.shots.removeIf(SimProjectile::isDone);
        }
        TitanJump.tick(server);TitanClassAbility.tick(server);TitanGrenade.tick(server);TitanSuper.tick(server);
        OWNERS.values().removeIf(c->c.shots.isEmpty()&&!TitanJump.active(c.owner)&&!TitanClassAbility.active(c.owner)
                &&!TitanGrenade.active(c.owner)&&!TitanSuper.active(c.owner)&&!kim.biryeong.destiny.ability.GrenadeThrow.active(c.owner));
    }
    public static void cleanup(ServerPlayer p) {
        Context c=OWNERS.get(p.getUUID());
        if(c!=null&&c.owner!=p)return;
        if(c!=null) {c.cancelled=true;OWNERS.remove(p.getUUID());}
        TitanJump.cleanup(p);TitanClassAbility.cleanup(p);TitanGrenade.cleanup(p);TitanSuper.cleanup(p);
        // Cancel exactly the Titan handles accepted by this context, never another feature's flights.
        if(c!=null) {for(SimProjectile flight:List.copyOf(c.shots))flight.cancel();c.shots.clear();}
    }
    public static void clearAll() {
        for(Context c:List.copyOf(OWNERS.values()))cleanup(c.owner);
        TitanJump.clearAll();TitanClassAbility.clearAll();TitanGrenade.clearAll();TitanSuper.clearAll();
    }
}
