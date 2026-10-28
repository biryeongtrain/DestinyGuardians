package kim.biryeong.destiny.ability.titan;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.AmmoGeneration;
import kim.biryeong.destiny.weapon.SwordTiming;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.*;
import java.util.*;

/** Source-length roaming supers. Contact candidates are provisional, never decoded damage events. */
public final class TitanSuper extends Ability {
    private static final Map<UUID,Session> ACTIVE=new HashMap<>();
    public TitanSuper(Element e) {super(TitanAbilities.abilityId(e,"super"),GuardianClass.TITAN,AbilitySlot.SUPER,e,556,
            switch(e){case ARC->"대혼란의 주먹";case SOLAR->"태양의 망치";default->"파수병 방패";});}
    @Override public boolean activate(ServerPlayer p) {
        if(!TitanAbilities.eligible(p)||AbilityService.inSuper(p)||ACTIVE.containsKey(p.getUUID()))return false;
        var c=TitanAbilities.context(p);if(!c.valid())return false;
        if(!ClassAbilityEffects.beginSuper(p,element(),id().getPath()))return false;
        var session=new Session(c,this);ACTIVE.put(p.getUUID(),session);AbilityService.startSuper(p,session);
        SuperCamera.blockMovement(p,session.deployTicks);
        if(session.airStart&&ClassSuperModelAssets.hasClip("w229_titan_arc_start_air"))
            PlayerAnimations.play(p,"w229_titan_arc_start_air");
        return true;
    }
    private static final class Session implements SuperSession {
        final TitanAbilities.Context c;
        final TitanSuper ability;
        final long start,until;
        final int duration,deployTicks,contactTicks,intervalTicks;
        final boolean airStart;
        final Object connection;
        final GuardianData data;
        final GuardianRuntime runtime;
        final AbilityTuning tuning;
        final List<SimProjectile> flights=new ArrayList<>();
        long lastVisual=Long.MIN_VALUE,nextAttack,slamUntil,pendingRelease=-1;
        long landFinish=-1,startupContact=-1;
        int attacks;
        boolean ended,pendingSlam,pendingAirAttack,startupDone,startupImpacted;
        Session(TitanAbilities.Context c,TitanSuper ability) {
            this.c=c;this.ability=ability;start=c.level.getGameTime();
            connection=c.owner.connection;data=Guardians.data(c.owner);runtime=Guardians.runtime(c.owner);tuning=ability.tuning();
            airStart=ability.element()==Element.ARC&&!supported(c.owner);
            duration=TitanAbilities.ticks(ability,"duration_ticks",
                    ability.element()==Element.ARC?500:ability.element()==Element.SOLAR?420:340,600);until=start+duration;
            // Manifest 2026-10-28: Solar cast26/attack32, Void cast28/attack27.
            // PlayerAnimations.play adds SwordTiming.START_TICKS (currently1).
            // Fists source 80A8AD9A ground30, AD9B air14, AD9C landing18, plus one start blend.
            // There is still no identified independent light-attack source: its fast timing is authored.
            int blend=SwordTiming.START_TICKS;
            int cast=ability.element()==Element.SOLAR?26:ability.element()==Element.VOID?28:airStart?14:30;
            int full=ability.element()==Element.SOLAR?32:ability.element()==Element.VOID?27:12;
            deployTicks=ability.element()==Element.ARC
                    ?ClassAbilityEffects.durationTicks(ability.id().getPath(),airStart?"start_air":"start",cast)+blend
                    :Math.max(cast,TitanAbilities.ticks(ability,"deploy_ticks",cast,100))+blend;
            contactTicks=TitanAbilities.ticks(ability,"attack_contact_ticks",ability.element()==Element.ARC?4:6,60)+blend;
            intervalTicks=Math.max(contactTicks+1,Math.max(full,
                    TitanAbilities.ticks(ability,"attack_interval_ticks",full,100))+blend);
            nextAttack=start+deployTicks;
            startupDone=ability.element()!=Element.ARC;
        }
        boolean valid() {return !ended&&c.valid()&&c.level.getGameTime()<until&&c.owner.connection==connection
                &&Guardians.data(c.owner)==data&&Guardians.runtimeIfPresent(c.owner).orElse(null)==runtime&&ability.tuning()==tuning;}
        @Override public boolean tick() {
            if(!valid())return false;
            long now=c.level.getGameTime();
            if(lastVisual!=now) {
                flights.removeIf(SimProjectile::isDone);
                lastVisual=now;ClassAbilityEffects.superTick(c.owner,ability.element(),ability.id().getPath(),(int)(now-start));
                if(!startupDone)startup(now);
                if(pendingRelease>=0&&now>=pendingRelease) {pendingRelease=-1;release();}
                if(pendingSlam) {
                    if(supported(c.owner)) {pendingSlam=false;landAttackPose();strike(true);}
                    else if(now>=slamUntil)pendingSlam=false;
                }
            }
            return true;
        }
        void startup(long now) {
            if(!airStart) {
                // Provisional near-end contact candidate, NOT a decoded Destiny damage event.
                if(!startupImpacted&&now>=start+deployTicks-3&&supported(c.owner)) {
                    startupImpacted=true;strike(true);
                }
                if(startupImpacted&&now>=start+deployTicks)startupDone=true;
            } else if(now>=start+deployTicks) {
                if(landFinish<0&&supported(c.owner)) {
                    int land=ClassAbilityEffects.durationTicks(ability.id().getPath(),"land",18)+SwordTiming.START_TICKS;
                    landFinish=now+land;startupContact=landFinish-3;nextAttack=landFinish;
                    SuperCamera.blockMovement(c.owner,land);
                    if(ClassSuperModelAssets.hasClip("w229_titan_arc_land"))PlayerAnimations.play(c.owner,"w229_titan_arc_land");
                }
                if(landFinish>=0) {
                    if(!startupImpacted&&now>=startupContact&&supported(c.owner)) {startupImpacted=true;strike(true);}
                    if(now>=landFinish)startupDone=true;
                }
            }
            if(!startupDone&&landFinish<0&&now>=start+deployTicks+60) {
                // No imaginary mid-air impact. Bound the wait and release ordinary roaming controls.
                startupDone=true;nextAttack=now;
            }
            if(!startupDone&&now>=start+deployTicks&&landFinish<0)SuperCamera.blockMovement(c.owner,2);
        }
        static boolean supported(ServerPlayer p) {
            if(!p.onGround())return false;
            return p.level().clip(new net.minecraft.world.level.ClipContext(p.position().add(0,.1,0),p.position().add(0,-.25,0),
                    net.minecraft.world.level.ClipContext.Block.COLLIDER,net.minecraft.world.level.ClipContext.Fluid.NONE,p)).getType()==HitResult.Type.BLOCK;
        }
        @Override public void primary() {
            long now=c.level.getGameTime();
            if(!valid()||!startupDone||now<nextAttack||pendingSlam||pendingRelease>=0||now+contactTicks>=until
                    ||attacks>=TitanAbilities.ticks(ability,"max_attacks",16,30))return;
            if(ability.element()!=Element.ARC&&!c.room())return;
            nextAttack=now+intervalTicks;attacks++;pendingRelease=now+contactTicks;
            // Master helper is visual/animation only. The gameplay payload and fire sound wait
            // for the provisional contact below, while the full source action finishes its recovery.
            pendingAirAttack=ability.element()==Element.ARC&&!supported(c.owner);
            if(pendingAirAttack) {
                // Shared source-backed airborne pose, not an independent ground-punch source.
                if(ClassSuperModelAssets.hasClip("w229_titan_arc_air"))PlayerAnimations.play(c.owner,"w229_titan_arc_air");
            } else ClassAbilityEffects.attack(c.owner,ability.element(),ability.id().getPath());
        }
        void release() {
            if(!valid())return;
            ServerPlayer p=c.owner;
            if(ability.element()==Element.ARC) {
                Vec3 forward=Motion.horizontalLook(p);
                if(!supported(p)) {
                    pendingSlam=true;slamUntil=c.level.getGameTime()+20;
                    Motion.setVelocity(p,forward.scale(.45).add(0,-.9,0));
                } else {
                    // Landing during windup only changes the pose; preserve the existing payload.
                    if(pendingAirAttack)landAttackPose();
                    Motion.setVelocity(p,forward.scale(.65).add(0,.1,0));strike(false);
                }
                pendingAirAttack=false;
            } else {
                Vec3 launchOrigin=p.getEyePosition();
                SimProjectile flight=c.launchFlight(launchOrigin,p.getLookAngle().scale(TitanAbilities.value(ability,"projectile_speed",1.7,.5,3)),
                        ability.element()==Element.SOLAR?.018:0,40,ability.element(),ability.id().getPath(),hit->{
                            if(!valid())return;
                            if(hit instanceof EntityHitResult collision&&collision.getEntity() instanceof LivingEntity entity
                                    &&!TitanAbilities.visible(c,launchOrigin,entity))return;
                            Vec3 center=TitanAbilities.impactPosition(hit);
                            for(LivingEntity e:TitanAbilities.targets(c,center,TitanAbilities.value(ability,"radius",3,1,5)))damage(e);
                            ClassAbilityEffects.burst(p,center,ability.element(),2);
                            ClassAbilityEffects.soundAt(p,ability.element(),ability.id().getPath(),"super.impact",center);
                        });
                if(flight!=null) {
                    flights.add(flight);
                    ClassAbilityEffects.sound(p,ability.element(),"super.fire");
                }
            }
        }
        void landAttackPose() {
            // Only called after real support: do not play a ground impact while still airborne.
            int land=ClassAbilityEffects.durationTicks(ability.id().getPath(),"land",18)+SwordTiming.START_TICKS;
            nextAttack=Math.max(nextAttack,c.level.getGameTime()+land);
            SuperCamera.blockMovement(c.owner,land);
            if(ClassSuperModelAssets.hasClip("w229_titan_arc_land"))PlayerAnimations.play(c.owner,"w229_titan_arc_land");
        }
        void strike(boolean slam) {
            ServerPlayer p=c.owner;Vec3 center=p.position().add(0,1,0),forward=Motion.horizontalLook(p);
            ClassAbilityEffects.sound(p,ability.element(),"super.fire");
            for(LivingEntity e:TitanAbilities.targets(c,center,TitanAbilities.value(ability,"radius",3.5,1,5))) {
                Vec3 delta=e.getBoundingBox().getCenter().subtract(center);
                if(slam||delta.lengthSqr()<1e-8||forward.dot(delta.normalize())>.25)damage(e);
            }
            ClassAbilityEffects.burst(p,center,ability.element(),slam?3:1.5);
            ClassAbilityEffects.soundAt(p,ability.element(),ability.id().getPath(),"super.impact",center);
        }
        void damage(LivingEntity e) {
            Combat.damage(c.level,c.owner,e,(float)TitanAbilities.value(ability,"damage",24,0,150),ability.element(),AmmoGeneration.SUPER);
        }
        @Override public void end() {
            if(ended)return;ended=true;pendingSlam=false;pendingAirAttack=false;pendingRelease=-1;
            ACTIVE.remove(c.owner.getUUID(),this);
            // Ordinary flights may predate this super and still belong to the same context.
            // The instance API disposes only this session's holders, without impact callbacks.
            for(SimProjectile flight:List.copyOf(flights))flight.cancel();
            flights.clear();c.shots.removeIf(SimProjectile::isDone);
            ClassAbilityEffects.endSuper(c.owner,ability.element(),ability.id().getPath());
        }
        @Override public float remaining() {return ended?0:Math.clamp((until-c.level.getGameTime())/(float)duration,0,1);}
    }
    /** Also validates fake/offline owners; AbilityService owns normal session progression. */
    static void tick(MinecraftServer server) {
        for(Session s:List.copyOf(ACTIVE.values())) {
            if(s.c.level.getServer()!=server)continue;
            if(!s.tick())cleanup(s.c.owner);
        }
    }
    public static boolean active(ServerPlayer p) {var s=ACTIVE.get(p.getUUID());return s!=null&&s.c.owner==p;}
    static void cleanup(ServerPlayer p) {
        Session s=ACTIVE.get(p.getUUID());if(s==null||s.c.owner!=p)return;
        if(Guardians.runtimeIfPresent(p).map(r->r.superSession==s).orElse(false))AbilityService.endSuper(p);
        else s.end();
    }
    static void clearAll() {for(Session s:List.copyOf(ACTIVE.values()))cleanup(s.c.owner);}
}
