package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Actual paid server transactions. These do not claim native input, rendered UI or animation QA. */
public final class PerksW191GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    private static final String FLOOR="destiny-test:floor", ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why){h.assertTrue(ok,Component.literal(why));}
    private static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final List<ServerPlayer> allies=new ArrayList<>();
        final List<Husk> targets=new ArrayList<>();ItemStack gun;WeaponProfile profile;
        Fixture(GameTestHelper h){
            this.h=h;p=TestPlayers.hunter(h,Element.ARC,new Vec3(2.5,1,6),-90,0,"W191_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,true);
            TestCleanup.register(h,()->{targets.forEach(Husk::discard);for(var a:allies){p.level().players().remove(a);TestPlayers.remove(a);}
                WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void equip(String id,String perk){
            WeaponRuntime.cleanup(p);gun=WeaponItems.create(WeaponCatalog.find(id).orElseThrow());
            if(perk!=null)check(h,WeaponPerks.select(gun,perk),"Exact selected base socket "+id+"/"+perk);
            profile=WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),0));
            int slot=WeaponCharacteristics.of(WeaponItems.entry(gun).orElseThrow()).slot().hotbar();
            p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);WeaponRuntime.tickPlayer(p);
        }
        Husk target(float hp,boolean precision){
            targets.forEach(Husk::discard);targets.clear();
            var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,precision?1:1.8,6));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(hp);return t;
        }
        void fire(){
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            int before=rounds();check(h,profile.chargeTicks()==0,"Immediate fixture");
            check(h,beginUse(p),"Production trigger accepted");WeaponRuntime.releaseUse(p,gun);
            check(h,rounds()==before-1,"Exactly one paid cartridge");TestPlayers.drain(p);
        }
        int rounds(){return WeaponItems.magazine(gun,profile).rounds();}
        ServerPlayer ally(double distance){
            var a=TestPlayers.create(h,new Vec3(2.5,1,3),0,0,"W191a_"+UUID.randomUUID().toString().substring(0,7));
            a.setPos(p.position().add(0,0,distance));p.level().players().add(a);allies.add(a);return a;
        }
        float damage(boolean selected,boolean precision){
            equip("fixed_odds",selected?"firing_line":null);var t=target(1000,precision);fire();
            float loss=1000-t.getHealth();check(h,loss>0,"Paid target actually loses HP");return loss;
        }
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=20)
    public void paidWellspringKillSplitsOnlyUnchargedEquippedSlots(GameTestHelper h){
        var f=new Fixture(h);f.equip("long_arm","wellspring");var d=Guardians.data(f.p);
        int grenade=AbilityService.equipped(f.p,AbilitySlot.GRENADE).orElseThrow().cooldownTicks();
        int melee=AbilityService.equipped(f.p,AbilitySlot.MELEE).orElseThrow().cooldownTicks();
        d.setCooldown(AbilitySlot.GRENADE,grenade);d.setCooldown(AbilitySlot.MELEE,melee);d.setCooldown(AbilitySlot.CLASS_ABILITY,0);
        var corpse=f.target(1,false);f.fire();check(h,!corpse.isAlive(),"Actual paid weapon final blow");
        check(h,d.cooldown(AbilitySlot.GRENADE)==grenade-(int)Math.ceil(grenade*.08/2),"Only two uncharged slots split the fixed grant");
        check(h,d.cooldown(AbilitySlot.MELEE)==melee-(int)Math.ceil(melee*.08/2)&&d.cooldown(AbilitySlot.CLASS_ABILITY)==0,"No overflow grant to charged class ability");
        h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=20)
    public void paidThreshAddsToBaselineSuperRewardOnce(GameTestHelper h){
        var f=new Fixture(h);f.equip("farewell",null);Guardians.data(f.p).setSuperEnergy(0);var a=f.target(1,false);f.fire();
        check(h,!a.isAlive(),"Unperked control final blow");float baseline=Guardians.data(f.p).superEnergy();
        f.equip("farewell","thresh");Guardians.data(f.p).setSuperEnergy(0);var b=f.target(1,false);f.fire();
        check(h,!b.isAlive(),"Selected paid final blow");
        check(h,Math.abs(Guardians.data(f.p).superEnergy()-baseline-.01f)<1e-5,"Adds exactly one reward over generic baseline, not a second generic kill");
        h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=20)
    public void paidPugilistKillRecoversMeleeAndPositiveContactActivatesHandling(GameTestHelper h){
        var f=new Fixture(h);f.equip("ammit_ar2","pugilist");var d=Guardians.data(f.p);
        int full=AbilityService.equipped(f.p,AbilitySlot.MELEE).orElseThrow().cooldownTicks();d.setCooldown(AbilitySlot.MELEE,full);
        var corpse=f.target(1,false);f.fire();check(h,!corpse.isAlive()&&d.cooldown(AbilitySlot.MELEE)==full-(int)Math.ceil(full*.1),"Actual paid kill recovers melee");
        var token=MeleeWeaponTraits.accepted(f.p);var target=f.target(100,false);
        check(h,!MeleeWeaponTraits.poweredDamage(f.p.level(),f.p,target,1,Element.ARC,token),"Nonlethal powered melee contact");
        check(h,WeaponPugilist.handlingBonus(f.p)>0,"Real positive nonlethal contact activates handling");
        WeaponPerks.clear(f.gun);check(h,WeaponPugilist.handlingBonus(f.p)==0,"Clearing original socket revokes live bonus");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=20)
    public void firingLineRequiresTwoAlliesAndNeverBuffsBodyDamage(GameTestHelper h){
        var f=new Fixture(h);f.ally(3);var second=f.ally(-3);
        float body=f.damage(false,false),boostedBody=f.damage(true,false);
        check(h,Math.abs(body-boostedBody)<.003,"Body components remain unchanged with two allies");
        float precision=f.damage(false,true),boostedPrecision=f.damage(true,true);
        check(h,precision>body&&Math.abs(boostedPrecision/precision-1.2)<.003,"Actual precision contact receives conditional damage bonus");
        second.setPos(f.p.position().add(0,0,16));float oneAlly=f.damage(true,true);
        check(h,Math.abs(oneAlly-precision)<.003,"Second ally leaving radius removes bonus for future shots");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=65)
    public void fullAutoPerkRepeatsWithoutChangingPreferenceAndStopsAfterRelease(GameTestHelper h){
        var f=new Fixture(h);f.equip("lonesome","full_auto_trigger_system");
        check(h,WeaponAccessibility.enabled(f.p),"Hold-to-fire preference defaults on");
        check(h,WeaponAccessibility.setEnabled(f.p,false)&&!WeaponAccessibility.enabled(f.p),"Explicit opt-out isolates the selected full-auto trait");int before=f.rounds();
        boolean twoHanded=WeaponModels.twoHanded(f.gun);
        check(h,twoHanded?WeaponRuntime.heartbeatUse(f.p):beginUse(f.p),"Actual weapon carrier input accepted");
        if(!twoHanded)f.p.startUsingItem(net.minecraft.world.InteractionHand.MAIN_HAND);
        final boolean[] renew={true};h.onEachTick(()->{if(renew[0]) {
            if(twoHanded)WeaponRuntime.heartbeatUse(f.p);
            else if(f.p.isUsingItem())WeaponRuntime.continueUse(f.p);
        }WeaponRuntime.tickPlayer(f.p);TestPlayers.drain(f.p);});
        h.startSequence().thenIdle(20).thenExecute(()->{check(h,f.rounds()<before-1&&!WeaponAccessibility.enabled(f.p),"Trait repeats actual paid shots while preference remains off");
            renew[0]=false;WeaponRuntime.releaseUse(f.p,f.gun);f.p.stopUsingItem();int released=f.rounds();
            h.startSequence().thenIdle(12).thenExecute(()->{check(h,f.rounds()==released,"Release ends repeat lease");h.succeed();});});
    }
}
