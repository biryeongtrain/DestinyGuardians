package kim.biryeong.destiny.ability.titan;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.combat.AbilityDamage;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.*;
import net.minecraft.world.effect.*;
import net.minecraft.world.phys.*;
import java.util.*;

/** Pulse, delayed fusion and suppressor. All damage uses accepted grenade provenance. */
public final class TitanGrenade extends Ability {
    private static final List<Field> FIELDS=new ArrayList<>();
    private static final class OwnedEffect {
        final LivingEntity target;
        final net.minecraft.core.Holder<MobEffect> type;
        final MobEffectInstance installed;
        final long until;
        final int amplifier;
        OwnedEffect(LivingEntity target,net.minecraft.core.Holder<MobEffect> type,int duration,int amplifier,long now) {
            this.target=target;this.type=type;this.until=now+duration;this.amplifier=amplifier;
            target.addEffect(new MobEffectInstance(type,duration,amplifier,false,false));installed=target.getEffect(type);
        }
        void remove(long now) {
            var current=target.getEffect(type);
            // An unrelated stronger/longer refresh retains ownership. Never clear all target effects.
            if(current==installed&&current.getAmplifier()==amplifier&&current.getDuration()<=Math.max(0,until-now)+1)
                target.removeEffect(type);
        }
    }
    private static final class Field {
        final TitanAbilities.Context c;
        final TitanGrenade ability;
        final WeaponAdrenalineJunkie.GrenadeToken token;
        final LivingEntity attached;
        final long detonate,until;
        final List<OwnedEffect> effects=new ArrayList<>();
        Vec3 position;
        long last=Long.MIN_VALUE,nextPulse;
        boolean fired;
        Field(TitanAbilities.Context c,TitanGrenade a,Vec3 pos,LivingEntity attached,WeaponAdrenalineJunkie.GrenadeToken token) {
            this.c=c;ability=a;position=pos;this.attached=attached;this.token=token;
            long now=c.level.getGameTime();detonate=now+(a.element()==Element.SOLAR?TitanAbilities.ticks(a,"fuse_ticks",20,60):0);
            until=detonate+(a.element()==Element.SOLAR?1:TitanAbilities.ticks(a,"duration_ticks",80,200));nextPulse=detonate;
        }
        boolean tick() {
            if(!c.valid())return false;
            long now=c.level.getGameTime();if(now>=until)return false;
            if(last==now)return true;last=now;
            if(attached!=null&&attached.isAlive()&&attached.level()==c.level)position=attached.getBoundingBox().getCenter();
            if(now<detonate) {if(now%4==0)Fx.burst(c.owner, c.level,position,ability.element(),3,.12);return true;}
            if(now<nextPulse)return true;
            nextPulse=now+TitanAbilities.ticks(ability,"pulse_ticks",20,60);
            ClassAbilityEffects.burst(c.owner,position,ability.element(),radius());
            // Pulse grenade has a separate first impact; suppressor is a local four-pulse field.
            String contact=ability.element()==Element.ARC?(fired?"pulse":"detonation")
                    :ability.element()==Element.SOLAR?"explosion":"pulse";
            if(!fired)ClassAbilityEffects.sound(c.owner,ability.element(),"grenade.impact");fired=true;
            for(LivingEntity e:TitanAbilities.targets(c,position,radius())) {
                WeaponAdrenalineJunkie.grenadeDamage(c.owner,token,c.level,e,
                        AbilityDamage.pvp(ability,contact,e,
                                (float)TitanAbilities.value(ability,"damage",ability.element()==Element.SOLAR?16:5,0,100)),ability.element());
                if(ability.element()==Element.VOID&&e.isAlive())suppress(e,now);
            }
            return ability.element()!=Element.SOLAR;
        }
        double radius() {return TitanAbilities.value(ability,"radius",3.5,1,6);}
        void suppress(LivingEntity e,long now) {
            if(e instanceof Mob mob)mob.setTarget(null);
            // Do not replace pre-existing effects: their ownership and duration remain untouched.
            int remaining=(int)Math.max(1,until-now);
            if(!e.hasEffect(MobEffects.SLOWNESS))effects.add(new OwnedEffect(e,MobEffects.SLOWNESS,remaining,3,now));
            if(!e.hasEffect(MobEffects.WEAKNESS))effects.add(new OwnedEffect(e,MobEffects.WEAKNESS,remaining,1,now));
        }
        void finish() {long now=c.level.getGameTime();for(var e:effects)e.remove(now);effects.clear();}
    }
    public TitanGrenade(Element e) {super(TitanAbilities.abilityId(e,"grenade"),GuardianClass.TITAN,AbilitySlot.GRENADE,e,e==Element.VOID?175.6:40,
            switch(e){case ARC->"파동 수류탄";case SOLAR->"융합 수류탄";default->"억제 수류탄";});}
    @Override public boolean activate(ServerPlayer p) {
        if(!TitanAbilities.eligible(p)||AbilityService.inSuper(p))return false;
        var c=TitanAbilities.context(p);
        if(!c.valid()||!c.room()||FIELDS.stream().filter(f->f.c.owner==p).count()>=2)return false;
        var junkie=WeaponAdrenalineJunkie.grenadeAccepted(p);var demo=WeaponDemolitionist.grenadeAccepted(p);
        return GrenadeThrow.begin(p,id(),GrenadeModels.item(GuardianClass.TITAN,element()),c::valid,()->{
        Vec3 launchOrigin=GrenadeThrow.origin(p);
        boolean launched=c.launch(launchOrigin,p.getLookAngle().scale(TitanAbilities.value(this,"throw_speed",1.1,.2,2)).add(0,.1,0),
                .04,60,element(),id().getPath(),hit->{
                    if(hit instanceof EntityHitResult collision&&collision.getEntity() instanceof LivingEntity entity
                            &&!TitanAbilities.visible(c,launchOrigin,entity))return;
                    LivingEntity attach=element()==Element.SOLAR&&hit instanceof EntityHitResult eh&&eh.getEntity() instanceof LivingEntity e?e:null;
                    FIELDS.add(new Field(c,this,TitanAbilities.impactPosition(hit),attach,junkie));
                });
        if(!launched)return;
        WeaponDemolitionist.grenadeReleased(p,demo);ClassAbilityEffects.sound(p,element(),"grenade.throw");
        });
    }
    static void tick(MinecraftServer server) {
        for(Field f:List.copyOf(FIELDS)) {
            if(f.c.level.getServer()!=server)continue;
            if(!f.tick()) {FIELDS.remove(f);f.finish();}
            else if(f.ability.element()==Element.VOID) {
                for(var effect:f.effects)if(effect.target instanceof Mob mob&&mob.isAlive())mob.setTarget(null);
            }
        }
    }
    public static boolean active(ServerPlayer p) {return FIELDS.stream().anyMatch(f->f.c.owner==p);}
    public static int fields(ServerPlayer p) {return (int)FIELDS.stream().filter(f->f.c.owner==p).count();}
    static void cleanup(ServerPlayer p) {for(Field f:List.copyOf(FIELDS))if(f.c.owner==p){FIELDS.remove(f);f.finish();}}
    static void clearAll() {for(Field f:List.copyOf(FIELDS)){FIELDS.remove(f);f.finish();}}
}
