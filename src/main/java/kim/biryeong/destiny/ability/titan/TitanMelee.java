package kim.biryeong.destiny.ability.titan;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.combat.AbilityDamage;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.MeleeWeaponTraits;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.*;

/** Frontal thunderclap-like strike, throwing hammer, shield throw. No guessed ripped animation. */
public final class TitanMelee extends Ability {
    public TitanMelee(Element e) {super(TitanAbilities.abilityId(e,"melee"),GuardianClass.TITAN,AbilitySlot.MELEE,e,e==Element.SOLAR?131.7:22,
            switch(e){case ARC->"천둥 강타";case SOLAR->"망치 투척";default->"방패 투척";});}
    @Override public boolean activate(ServerPlayer p) {
        if(!TitanAbilities.eligible(p)||AbilityService.inSuper(p))return false;
        var c=TitanAbilities.context(p);if(!c.valid()||(element()!=Element.ARC&&!c.room()))return false;
        var token=MeleeWeaponTraits.accepted(p);
        float damage=(float)TitanAbilities.value(this,"damage",element()==Element.ARC?14:12,0,100);
        if(element()==Element.ARC) {
            Vec3 eye=p.getEyePosition(),forward=Motion.horizontalLook(p);
            for(LivingEntity e:TitanAbilities.targets(c,eye,TitanAbilities.value(this,"reach",4,1,6))) {
                Vec3 delta=e.getBoundingBox().getCenter().subtract(eye);
                if(delta.lengthSqr()>1e-8&&forward.dot(delta.normalize())>=.55) {
                    MeleeWeaponTraits.poweredDamage(c.level,p,e,AbilityDamage.pvp(this,"strike",e,damage),element(),token);
                    Fx.line(c.owner, c.level,eye,e.getBoundingBox().getCenter(),element().color(),.3,1.2f);
                }
            }
            ClassAbilityEffects.burst(p,eye.add(forward.scale(1.5)),element(),1.2);
        } else {
            Vec3 launchOrigin=p.getEyePosition();
            if(!c.launch(launchOrigin,p.getLookAngle().scale(TitanAbilities.value(this,"speed",1.8,.5,3)),
                    element()==Element.SOLAR?.025:0,40,element(),id().getPath(),hit->{
                        if(hit instanceof EntityHitResult eh&&eh.getEntity() instanceof LivingEntity target&&TitanAbilities.visible(c,launchOrigin,target)) {
                            // Extra LOS prevents an inflated entity collision box from reaching through thin walls.
                            MeleeWeaponTraits.poweredDamage(c.level,p,target,AbilityDamage.pvp(this,"impact",target,damage),element(),token);
                        }
                        ClassAbilityEffects.burst(p,TitanAbilities.impactPosition(hit),element(),.7);
                        ClassAbilityEffects.sound(p,element(),"melee.impact");
                    }))return false;
        }
        ClassAbilityEffects.sound(p,element(),"melee.cast");return true;
    }
}
