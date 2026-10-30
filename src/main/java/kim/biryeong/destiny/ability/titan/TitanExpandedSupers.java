package kim.biryeong.destiny.ability.titan;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ChunkAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.AmmoGeneration;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Brightness;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.*;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;
import org.joml.Vector3f;
import org.joml.Quaternionf;

import java.util.*;

/** W230 Titan supers. The caller owns lifecycle registration, never duplicated here. */
public final class TitanExpandedSupers {
    public static final net.minecraft.resources.Identifier THUNDERCRASH=DestinyGuardians.id("titan/thundercrash"),
            BURNING_MAUL=DestinyGuardians.id("titan/burning_maul"), WARD_OF_DAWN=DestinyGuardians.id("titan/ward_of_dawn");
    private static final Map<UUID,Session> ACTIVE=new HashMap<>();
    private static final Map<UUID,Ward> WARDS=new HashMap<>();
    private static final Map<UUID,Aftershock> AFTERSHOCKS=new HashMap<>();
    private static boolean registered;
    private TitanExpandedSupers() { }

    public static void register() {
        if(registered)return;
        AbilityRegistry.register(new Expanded("thundercrash",Element.ARC,556,"천둥충돌"));
        AbilityRegistry.register(new Expanded("burning_maul",Element.SOLAR,500,"불타는 망치"));
        AbilityRegistry.register(new Expanded("ward_of_dawn",Element.VOID,455,"새벽의 수호물"));
        registered=true;
    }

    private static final class Expanded extends Ability {
        final String kind;
        Expanded(String kind,Element element,double cooldown,String name) {
            super(DestinyGuardians.id("titan/"+kind),GuardianClass.TITAN,AbilitySlot.SUPER,element,cooldown,name);
            this.kind=kind;
        }
        @Override public boolean activate(ServerPlayer p) {
            if(!TitanAbilities.eligible(p)||AbilityService.inSuper(p)||ACTIVE.containsKey(p.getUUID())
                    ||p.isPassenger()||p.isSleeping()||p.isFallFlying()||p.isInWater()||p.isInLava())return false;
            Owner owner=new Owner(p,this);
            if(!owner.valid()||!ClassAbilityEffects.beginSuper(p,element(),id().getPath()))return false;
            Session next=switch(kind) {
                case "thundercrash"->new Crash(owner);
                case "burning_maul"->new Maul(owner);
                default->new WardCast(owner);
            };
            ACTIVE.put(p.getUUID(),next);AbilityService.startSuper(p,next);
            next.begin();return true;
        }
    }

    /** Exact object epochs, including data reload and connection replacement, not just UUID/class. */
    private static final class Owner {
        final ServerPlayer p;
        final ServerLevel level;
        final Object connection;
        final GuardianData data;
        final GuardianRuntime runtime;
        final Loadout loadout;
        final Expanded ability;
        final AbilityTuning tuning;
        boolean cancelled;
        Owner(ServerPlayer p,Expanded ability) {
            this.p=p;this.ability=ability;level=p.level();connection=p.connection;
            data=Guardians.data(p);runtime=Guardians.runtime(p);loadout=data.loadout().orElse(null);tuning=ability.tuning();
        }
        boolean valid() {
            return !cancelled&&TitanAbilities.eligible(p)&&p.level()==level&&p.connection==connection
                    &&Guardians.data(p)==data&&Guardians.runtimeIfPresent(p).orElse(null)==runtime
                    &&data.loadout().orElse(null)==loadout&&loadout!=null
                    &&ability.id().equals(loadout.get(AbilitySlot.SUPER))&&ability.tuning()==tuning;
        }
        long now() {return level.getGameTime();}
        String path() {return ability.id().getPath();}
        double value(String key,double fallback,double min,double max) {return TitanAbilities.value(ability,key,fallback,min,max);}
        int ticks(String key,int fallback,int max) {return TitanAbilities.ticks(ability,key,fallback,max);}
        int clip(String phase,int fallback) {
            // Shared helper returns source duration ONLY. These fallback contracts include start blend.
            return ClassAbilityEffects.durationTicks(path(),phase,Math.max(1,fallback-1))
                    +kim.biryeong.destiny.weapon.SwordTiming.START_TICKS;
        }
        boolean visible(Vec3 from,LivingEntity target) {
            return valid()&&target.level()==level&&TitanAbilities.enemy(p,target)
                    &&level.clip(new ClipContext(from,target.getBoundingBox().getCenter(),ClipContext.Block.COLLIDER,
                    ClipContext.Fluid.NONE,p)).getType()==HitResult.Type.MISS;
        }
        void damage(Vec3 center,double radius,float amount,Set<UUID> once) {
            if(!valid())return;
            for(LivingEntity e:Combat.enemiesNear(level,p,center,radius)) {
                if(!visible(center,e)||(once!=null&&!once.add(e.getUUID())))continue;
                Combat.damage(level,p,e,amount,ability.element(),AmmoGeneration.SUPER);
            }
        }
        void burst(Vec3 center,double radius) {
            if(valid())ClassAbilityEffects.burst(p,center,ability.element(),radius);
        }
    }

    private abstract static class Session implements SuperSession {
        final Owner o;
        final long start;
        final int deploy;
        final boolean airStart;
        long lastTick=Long.MIN_VALUE;
        boolean ended;
        Session(Owner o,int fallbackGround,int fallbackAir) {
            this.o=o;start=o.now();airStart=!supported(o.p);
            deploy=o.clip(airStart?"start_air":"start",airStart?fallbackAir:fallbackGround);
        }
        void begin() {
            SuperCamera.blockMovement(o.p,deploy);
            if(airStart)play(o,"start_air");
        }
        @Override public final boolean tick() {
            if(ended||!o.valid())return false;
            long now=o.now();if(now==lastTick)return alive();lastTick=now;
            ClassAbilityEffects.superTick(o.p,o.ability.element(),o.path(),(int)(now-start));
            return advance(now);
        }
        abstract boolean advance(long now);
        abstract boolean alive();
        @Override public void end() {
            if(ended)return;ended=true;ACTIVE.remove(o.p.getUUID(),this);dispose();
            finishPresentation();
        }
        void finishPresentation() {ClassAbilityEffects.endSuper(o.p,o.ability.element(),o.path());}
        void dispose() { }
        @Override public void primary() { }
        @Override public float remaining() {return ended?0:1;}
    }

    private static final class Crash extends Session {
        final int flightTicks;
        final double maxDistance;
        Vec3 direction;
        final Vec3 previousVelocity;
        final boolean previousNoGravity;
        long flightStart=-1,recoveryUntil=Long.MAX_VALUE;
        double travelled;
        boolean physicsOwned,impacted;
        ElementHolder aura;
        ItemDisplayElement auraDisplay;
        Vec3 auraOrigin;
        Crash(Owner o) {
            super(o,17,17);flightTicks=o.ticks("flight_ticks",90,100);maxDistance=o.value("max_distance",64,4,96);
            previousVelocity=o.p.getDeltaMovement();previousNoGravity=o.p.isNoGravity();direction=o.p.getLookAngle();
        }
        @Override boolean alive() {return o.now()<recoveryUntil;}
        @Override boolean advance(long now) {
            if(impacted)return now<recoveryUntil;
            if(now<start+deploy)return true;
            if(flightStart<0) {
                flightStart=now;physicsOwned=true;o.p.setNoGravity(true);
                play(o,"air");ClassAbilityEffects.sound(o.p,Element.ARC,o.path(),"super.fire");
                startAura();
            }
            // Native rear-camera player physics gets zero residual velocity. This routine owns one
            // collision-resolved displacement per product game tick, not an unchecked teleport.
            SuperCamera.blockMovement(o.p,2);Motion.setVelocity(o.p,Vec3.ZERO);
            Vec3 desired=o.p.getLookAngle();
            if(desired.lengthSqr()>1e-8) {
                Vec3 blended=direction.scale(.6).add(desired.normalize().scale(.4));
                if(blended.lengthSqr()>1e-8)direction=blended.normalize();
            }
            double length=Math.min(o.value("flight_speed",1.0,.2,2),maxDistance-travelled);
            if(now-flightStart>=flightTicks||length<=.001) {impact(false);return true;}
            Vec3 delta=direction.scale(length),old=o.p.position();
            // Sweep the whole player volume BEFORE motion. <=0.10 block samples cannot tunnel
            // a .6-block player through any thin colliding slab. Check entities and world border too.
            int steps=Math.max(1,(int)Math.ceil(length/.1));
            Vec3 safe=Vec3.ZERO;boolean collided=false;
            for(int i=1;i<=steps;i++) {
                Vec3 candidate=delta.scale(i/(double)steps);AABB box=o.p.getBoundingBox().move(candidate);
                if(!o.level.getWorldBorder().isWithinBounds(BlockPos.containing(old.add(candidate)))
                        ||!o.level.noCollision(o.p,box)
                        ||!o.level.getEntitiesOfClass(LivingEntity.class,box,e->e!=o.p&&e.isAlive()&&!e.isSpectator()).isEmpty()) {
                    collided=true;break;
                }
                safe=candidate;
            }
            if(safe.lengthSqr()>0) {o.p.move(MoverType.SELF,safe);travelled+=o.p.position().distanceTo(old);}
            if(aura!=null) {
                auraDisplay.setOffset(o.p.position().add(0,.9,0).subtract(auraOrigin));
                auraDisplay.setLeftRotation(new Quaternionf().rotationY((float)-Math.toRadians(o.p.getYRot())));
                aura.tick();
            }
            if(collided)impact(Math.abs(direction.y)<.6);
            return true;
        }
        void impact(boolean wall) {
            if(impacted||!o.valid())return;impacted=true;restorePhysics();
            double radius=o.value("radius",4.5,1,7);
            Vec3 center=o.p.position().add(0,.7,0);
            o.damage(center,radius,(float)o.value("damage",38,0,160),null);o.burst(center,radius);
            ClassAbilityEffects.sound(o.p,Element.ARC,o.path(),"super.impact");
            Aftershock prior=AFTERSHOCKS.remove(o.p.getUUID());if(prior!=null)prior.close();
            AFTERSHOCKS.put(o.p.getUUID(),new Aftershock(o,center,radius));
            recoveryUntil=o.now()+o.clip(wall?"end_wall":"end",wall?15:18);
            play(o,wall?"end_wall":"end");SuperCamera.blockMovement(o.p,(int)(recoveryUntil-o.now()));
        }
        void restorePhysics() {
            if(aura!=null) {aura.destroy();aura=null;auraDisplay=null;}
            if(!physicsOwned)return;physicsOwned=false;
            // Only restore fields changed by this exact session. Never grant flying/noclip/invulnerability.
            if(o.p.isNoGravity())o.p.setNoGravity(previousNoGravity);
            if(o.p.level()==o.level&&o.p.isAlive())Motion.setVelocity(o.p,previousVelocity);
        }
        void startAura() {
            ElementHolder next=new ElementHolder();
            try {
                var display=new AbilityDisplayElement(o.p,ClassAbilityEffects.item(o.path()));
                display.setItemDisplayContext(ItemDisplayContext.NONE);display.setBrightness(new Brightness(15,15));
                display.setScale(new Vector3f(1.2f));display.setTeleportDuration(1);next.addElement(display);
                auraOrigin=o.p.position().add(0,.9,0);ChunkAttachment.ofTicking(next,o.level,auraOrigin);next.startWatching(o.p);
                aura=next;auraDisplay=display;
            } catch(RuntimeException ex) {
                next.destroy(); // Shared superTick still supplies the bounded Arc particle fallback.
                DestinyGuardians.LOGGER.warn("Thundercrash aura unavailable: {}",ex.toString());
            }
        }
        @Override void dispose() {restorePhysics();}
        @Override void finishPresentation() {
            // _end / _end_wall was already played at impact and allowed to finish in recovery.
            // Generic endSuper would replay it and pin the caster in a second exit animation.
            ClassAbilityEffects.sound(o.p,Element.ARC,o.path(),"super.end");
            ClassAbilityEffects.cleanup(o.p);PlayerAnimations.stop(o.p);SuperCamera.stop(o.p);
        }
        @Override public float remaining() {
            return ended?0:flightStart<0?1:Math.clamp((flightTicks-(o.now()-flightStart))/(float)flightTicks,0,1);
        }
    }

    private static final class Aftershock {
        final Owner o;final Vec3 center;final double radius;final long first,until;
        long lastTick=Long.MIN_VALUE,next;
        boolean closed;
        Aftershock(Owner o,Vec3 center,double radius) {
            this.o=o;this.center=center;this.radius=radius;first=o.now()+15;next=first;until=first+80;
        }
        boolean tick() {
            if(closed||!o.valid()||o.now()>=until)return false;
            long now=o.now();if(lastTick==now)return true;lastTick=now;
            if(now>=next) {
                next=now+20;o.damage(center,radius,(float)o.value("aftershock_damage",6,0,40),null);o.burst(center,radius);
            }
            return true;
        }
        void close() {closed=true;}
    }

    private static final class Maul extends Session {
        final int duration;
        long until,nextAttack,pending=-1;
        boolean heavy;
        final List<Firewave> waves=new ArrayList<>();
        Maul(Owner o) {super(o,27,27);duration=o.ticks("duration_ticks",500,840);until=start+duration;nextAttack=start+deploy;}
        @Override void begin() {super.begin();PlayerAnimations.superItem(o.p,ClassAbilityEffects.item(o.path()),false);}
        @Override boolean alive() {return o.now()<until;}
        @Override boolean advance(long now) {
            if(now>=until)return false;
            if(pending>=0&&now>=pending) {
                pending=-1;
                if(heavy) {
                    if(supported(o.p)&&waves.size()<3)waves.add(new Firewave(o));
                } else {
                    Vec3 center=o.p.position().add(0,.9,0);
                    o.damage(center,o.value("spin_radius",3,1,5),(float)o.value("spin_damage",14,0,80),null);
                    o.burst(center,2);
                }
                ClassAbilityEffects.sound(o.p,Element.SOLAR,o.path(),"super.fire");
            }
            waves.removeIf(w->!w.tick());return true;
        }
        @Override public void primary() {
            long now=o.now();
            if(ended||!o.valid()||now<nextAttack||pending>=0||now>=until)return;
            boolean sneak=o.p.getLastClientInput().shift()||o.p.isShiftKeyDown();
            if(sneak&&(!supported(o.p)||waves.size()>=3))return;
            heavy=sneak;
            int full=o.clip(heavy?"attack2":"attack",heavy?21:15);
            int contact=Math.min(full-1,o.ticks(heavy?"heavy_contact_ticks":"light_contact_ticks",heavy?7:6,60));
            if(now+contact>=until)return;
            nextAttack=now+Math.max(full,heavy?full:14);pending=now+contact;
            // DDC light/heavy 4%/8% energy cost. No Sol Invictus duration extension without the aspect.
            until-=Math.round(duration*o.value(heavy?"heavy_cost":"light_cost",heavy?.08:.04,0,.3));
            if(heavy)play(o,"attack2");else ClassAbilityEffects.attack(o.p,Element.SOLAR,o.path());
            PlayerAnimations.superItem(o.p,ClassAbilityEffects.item(o.path()),false);
        }
        @Override void dispose() {pending=-1;waves.forEach(Firewave::close);waves.clear();}
        @Override public float remaining() {return ended?0:Math.clamp((until-o.now())/(float)duration,0,1);}
    }

    /** Ground-following bounded wave; one hit per target per wave, stop at walls or unsupported ledges. */
    private static final class Firewave {
        final Owner o;final Vec3 direction,origin;final long until;
        final Set<UUID> hit=new HashSet<>();
        final ElementHolder holder=new ElementHolder();
        final ItemDisplayElement display;
        Vec3 pos;long lastTick=Long.MIN_VALUE;
        double travelled;
        boolean closed;
        Firewave(Owner o) {
            this.o=o;direction=Motion.horizontalLook(o.p);pos=o.p.position().add(0,.1,0);origin=pos;until=o.now()+80;
            display=new AbilityDisplayElement(o.p,ClassAbilityEffects.item(o.path()+"_wave"));
            display.setItemDisplayContext(ItemDisplayContext.NONE);display.setScale(new Vector3f(1));
            display.setLeftRotation(new Quaternionf().rotationTo(0,0,1,(float)direction.x,0,(float)direction.z).rotateY((float)Math.PI));
            display.setBrightness(new Brightness(15,15));display.setTeleportDuration(1);holder.addElement(display);
            ChunkAttachment.ofTicking(holder,o.level,origin);
        }
        boolean tick() {
            if(closed||!o.valid()||o.now()>=until||travelled>=o.value("wave_distance",14,2,24)) {close();return false;}
            if(lastTick==o.now())return true;lastTick=o.now();
            Vec3 candidate=pos.add(direction.scale(.5));
            HitResult obstruction=o.level.clip(new ClipContext(pos.add(0,.35,0),candidate.add(0,.35,0),
                    ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,o.p));
            if(obstruction.getType()!=HitResult.Type.MISS) {close();return false;}
            var support=o.level.clip(new ClipContext(candidate.add(0,.7,0),candidate.add(0,-.7,0),
                    ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,o.p));
            if(support.getType()!=HitResult.Type.BLOCK) {close();return false;}
            pos=support.getLocation().add(0,.12,0);travelled+=.5;
            o.damage(pos.add(0,.45,0),1.6,(float)o.value("wave_damage",28,0,120),hit);
            Fx.burst(o.p, o.level,pos,Element.SOLAR,6,.25);display.setOffset(pos.subtract(origin));holder.tick();return true;
        }
        void close() {if(closed)return;closed=true;holder.destroy();}
    }

    private static final class WardCast extends Session {
        long finish,landContact=-1;
        final long airborneDeadline;
        boolean landed,installed;
        WardCast(Owner o) {
            super(o,29,10);finish=start+deploy;airborneDeadline=finish+o.ticks("air_wait_ticks",80,120);
        }
        @Override boolean alive() {return o.now()<finish||airStart&&!landed&&o.now()<airborneDeadline;}
        @Override boolean advance(long now) {
            if(airStart&&!landed) {
                if(now<start+deploy)return true;
                if(supported(o.p)) {
                    landed=true;int length=o.clip("land",23);finish=now+length;
                    landContact=finish-2;SuperCamera.blockMovement(o.p,length);play(o,"land");
                } else {
                    SuperCamera.blockMovement(o.p,2);
                    return now<airborneDeadline;
                }
            }
            long contact=airStart?landContact:finish-2;
            if(!installed&&contact>=0&&now>=contact&&supported(o.p)) {
                Ward next=new Ward(o,o.p.position());Ward prior=WARDS.put(o.p.getUUID(),next);
                if(prior!=null)prior.close();installed=true;
                o.burst(o.p.position().add(0,.2,0),next.radius);ClassAbilityEffects.sound(o.p,Element.VOID,o.path(),"super.fire");
            }
            // Finite cast ends; the owned construct is independent of SuperSession.
            return now<finish;
        }
        @Override public float remaining() {return ended?0:Math.clamp((finish-o.now())/(float)Math.max(1,deploy),0,1);}
        @Override void dispose() {
            // Installation must release the player's cast pose/camera while the dome lives on.
            PlayerAnimations.stop(o.p);SuperCamera.stop(o.p);
        }
    }

    private static final class Ward {
        final Owner o;final Vec3 center;final double radius;final long until;
        final ElementHolder holder=new ElementHolder();
        long lastTick=Long.MIN_VALUE;
        double hp;
        boolean closed;
        Ward(Owner o,Vec3 center) {
            this.o=o;this.center=center;radius=o.value("radius",4,2,6);
            hp=o.value("health",160,1,1000);until=o.now()+o.ticks("field_ticks",600,800);
            var display=new AbilityDisplayElement(o.p,ClassAbilityEffects.item(o.path()));
            display.setItemDisplayContext(ItemDisplayContext.NONE);display.setBrightness(new Brightness(15,15));
            // Art contract: item center[8,8,8], hemisphere radius8 raw units, base at centerY8.
            display.setScale(new Vector3f((float)(2*radius)));holder.addElement(display);
            try {ChunkAttachment.ofTicking(holder,o.level,center);holder.startWatching(o.p);}
            catch(RuntimeException ex) {holder.destroy();throw ex;}
        }
        boolean valid() {return !closed&&hp>0&&o.valid()&&o.now()<until;}
        boolean contains(Vec3 point) {
            Vec3 d=point.subtract(center);return d.y>=-.1&&d.lengthSqr()<radius*radius;
        }
        boolean ally(LivingEntity e) {
            return e==o.p||o.p.isAlliedTo(e)||(e instanceof TamableAnimal t&&t.isTame()&&t.isOwnedBy(o.p));
        }
        boolean crosses(Vec3 from,Vec3 to) {
            if(contains(from))return false;
            Vec3 delta=to.subtract(from);double a=delta.lengthSqr();if(a<1e-10)return false;
            Vec3 d=from.subtract(center);double b=2*d.dot(delta),c=d.lengthSqr()-radius*radius,disc=b*b-4*a*c;
            if(disc<0)return false;
            double t=(-b-Math.sqrt(disc))/(2*a);
            return t>=0&&t<=1&&from.add(delta.scale(t)).y>=center.y-.1;
        }
        void spend(double amount) {hp-=amount;if(hp<=0)removeWard(this);}
        boolean tick() {
            if(!valid())return false;if(lastTick==o.now())return true;lastTick=o.now();
            for(Projectile shot:o.level.getEntitiesOfClass(Projectile.class,AABB.ofSize(center,2*radius+16,2*radius+16,2*radius+16))) {
                if(shot.isRemoved()||shot.getOwner()==o.p||shot.getOwner()!=null&&o.p.isAlliedTo(shot.getOwner()))continue;
                Vec3 from=new Vec3(shot.xo,shot.yo,shot.zo),to=shot.position();
                if(!crosses(from,to)) {from=shot.position();to=from.add(shot.getDeltaMovement());}
                if(!crosses(from,to))continue;
                var wall=o.level.clip(new ClipContext(from,to,ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,shot));
                if(wall.getType()!=HitResult.Type.MISS)continue;
                shot.discard();spend(10);if(!valid())return false;
            }
            holder.tick();return true;
        }
        void close() {if(closed)return;closed=true;holder.destroy();}
    }

    /** Live owner/ally membership; no cached potion and no enemy benefits. */
    public static boolean inWard(ServerPlayer p) {
        if (!p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected()) return false;
        for (Ward ward : WARDS.values())
            if (ward.valid() && p.level() == ward.o.level && ward.ally(p)
                    && ward.contains(p.getBoundingBox().getCenter())) return true;
        return false;
    }

    /** Master wires this exactly once into ALLOW_DAMAGE. Directionless/environmental damage passes. */
    public static boolean allowDamage(LivingEntity victim,DamageSource source,float amount) {
        if(!Float.isFinite(amount)||amount<=0||source.is(DamageTypeTags.BYPASSES_INVULNERABILITY))return true;
        Entity direct=source.getDirectEntity();Vec3 from=source.getSourcePosition();
        if(from==null)return true;
        for(Ward ward:List.copyOf(WARDS.values())) {
            if(!ward.valid()) {removeWard(ward);continue;}
            if(victim.level()!=ward.o.level||!ward.ally(victim)||!ward.contains(victim.getBoundingBox().getCenter()))continue;
            if(direct!=null&&direct.level()!=ward.o.level)continue;
            Vec3 origin=from;
            if(direct instanceof Projectile projectile&&ward.contains(origin)) {
                Vec3 prior=new Vec3(projectile.xo,projectile.yo,projectile.zo);
                if(ward.crosses(prior,victim.getBoundingBox().getCenter()))origin=prior;
            }
            if(ward.contains(origin))continue; // An attacker already inside is never an external threat.
            if(ward.crosses(origin,victim.getBoundingBox().getCenter())) {ward.spend(amount);return false;}
        }
        return true;
    }

    private static boolean supported(ServerPlayer p) {
        if(!p.onGround())return false;
        var support=p.level().clip(new ClipContext(p.position().add(0,.1,0),p.position().add(0,-.25,0),
                ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,p));
        return support.getType()==HitResult.Type.BLOCK;
    }
    private static void play(Owner o,String phase) {
        String clip=ClassSuperModelAssets.prefix(o.path())+"_"+phase;
        if(ClassSuperModelAssets.hasClip(clip))PlayerAnimations.play(o.p,clip);
    }
    private static void removeWard(Ward ward) {WARDS.remove(ward.o.p.getUUID(),ward);ward.close();}
    public static void tick(MinecraftServer server) {
        for(Session session:List.copyOf(ACTIVE.values())) {
            if(session.o.level.getServer()!=server)continue;
            if(!session.tick()) {
                if(Guardians.runtimeIfPresent(session.o.p).map(r->r.superSession==session).orElse(false))AbilityService.endSuper(session.o.p);
                else session.end();
            }
        }
        for(Ward ward:List.copyOf(WARDS.values()))if(ward.o.level.getServer()==server&&!ward.tick())removeWard(ward);
        for(Aftershock field:List.copyOf(AFTERSHOCKS.values()))if(field.o.level.getServer()==server&&!field.tick()) {
            AFTERSHOCKS.remove(field.o.p.getUUID(),field);field.close();
        }
    }
    public static void cleanup(ServerPlayer p) {
        Session s=ACTIVE.get(p.getUUID());
        if(s!=null&&s.o.p==p) {
            s.o.cancelled=true;
            if(Guardians.runtimeIfPresent(p).map(r->r.superSession==s).orElse(false))AbilityService.endSuper(p);else s.end();
        }
        Ward ward=WARDS.get(p.getUUID());if(ward!=null&&ward.o.p==p) {ward.o.cancelled=true;removeWard(ward);}
        Aftershock field=AFTERSHOCKS.get(p.getUUID());if(field!=null&&field.o.p==p) {
            field.o.cancelled=true;AFTERSHOCKS.remove(p.getUUID(),field);field.close();
        }
    }
    public static void clearAll() {
        for(Session session:List.copyOf(ACTIVE.values()))cleanup(session.o.p);
        for(Ward ward:List.copyOf(WARDS.values()))cleanup(ward.o.p);
        for(Aftershock field:List.copyOf(AFTERSHOCKS.values()))cleanup(field.o.p);
    }
    public static String status(ServerPlayer p) {
        Session s=ACTIVE.get(p.getUUID());Ward w=WARDS.get(p.getUUID());Aftershock a=AFTERSHOCKS.get(p.getUUID());
        return "titanW230="+(s!=null&&s.o.p==p?s.o.ability.kind:"none")
                +",ward="+(w!=null&&w.o.p==p&&w.valid())
                +",aftershock="+(a!=null&&a.o.p==p&&!a.closed&&a.o.valid())
                +(s instanceof Crash c?",flight="+(c.flightStart>=0&&!c.impacted)+",impacted="+c.impacted+",distance="+c.travelled:"")
                +(s instanceof Maul m?",waves="+m.waves.size()+",pending="+(m.pending>=0):"");
    }
}
