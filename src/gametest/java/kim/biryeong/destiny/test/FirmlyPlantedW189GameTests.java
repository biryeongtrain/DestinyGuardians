package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Actual Fabric server crouch/source, funded shot, ADS and Handling integration; not native pixels. */
public final class FirmlyPlantedW189GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    /** Production left-click ADS; does not bypass the three-tick toggle debounce. */
    private static void ads(net.minecraft.server.level.ServerPlayer p, boolean requested) {
        if (WeaponAiming.requested(p) != requested) kim.biryeong.destiny.input.InputRouter.onPunch(p);
    }
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="firmly_planted";
    static void check(GameTestHelper h,boolean value,String why){h.assertTrue(value,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final WeaponCatalog.Entry entry;final WeaponProfile profile;final ItemStack gun;
        Fixture(GameTestHelper h){this(h,"steelfeather_repeater");}
        Fixture(GameTestHelper h,String id){
            this.h=h;entry=WeaponCatalog.find(id).orElseThrow();profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W189_"+UUID.randomUUID().toString().substring(0,8));
            p.setNoGravity(true);p.setOnGround(true);Guardians.runtime(p);p.setAttached(WeaponLoadout.ENABLED,true);
            gun=WeaponItems.create(entry);check(h,WeaponPerks.select(gun,ID),"Exact official base socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,1,200));int slot=WeaponCharacteristics.of(entry).slot().hotbar();
            p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);tick();h.onEachTick(this::tick);
            TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void tick(){WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);}
        void crouch(boolean yes){p.setPose(yes?Pose.CROUCHING:Pose.STANDING);}
        void arc(){
            var d=Guardians.data(p);var map=new EnumMap<AbilitySlot,Identifier>(AbilitySlot.class);map.putAll(d.loadout().orElseThrow().abilities());
            map.put(AbilitySlot.SUPER,AbilityRegistry.of(GuardianClass.HUNTER,AbilitySlot.SUPER).stream().filter(a->a.element()==Element.ARC).findFirst().orElseThrow().id());
            d.setLoadout(GuardianClass.HUNTER,new Loadout(map));
        }
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void actualCrouchNotShiftOrCosmeticAdsAndStandingRemoval(GameTestHelper h){
        var f=new Fixture(h);check(h,!WeaponFirmlyPlanted.active(f.p),"Standing source inert");
        f.p.setShiftKeyDown(true);WeaponModels.setPose(f.gun,WeaponModels.Pose.ADS);
        check(h,!WeaponFirmlyPlanted.active(f.p),"Shift flag and cosmetic ADS alone do not grant crouching");
        f.p.setShiftKeyDown(false);f.crouch(true);
        check(h,WeaponFirmlyPlanted.active(f.p)&&WeaponAiming.progress(f.p)==0,"Actual crouch grants hip-fire without ADS session progress");
        check(h,WeaponFirmlyPlanted.stabilityBonus(f.p)==20&&WeaponFirmlyPlanted.handlingBonus(f.p)==30,"Base ordinary20/30");
        check(h,WeaponFirmlyPlanted.accuracyScalar(f.p)==.6&&WeaponFirmlyPlanted.growthScalar(f.p)==.83&&WeaponFirmlyPlanted.yawScalar(f.p)==.2,"Separate DDC ordinary scalars");
        f.crouch(false);check(h,!WeaponFirmlyPlanted.active(f.p)&&WeaponFirmlyPlanted.yawScalar(f.p)==1,"Stand removes immediately without update");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void fusionGetsDifferentConfirmedBaseValues(GameTestHelper h){
        var f=new Fixture(h,"dream_breaker");f.crouch(true);
        check(h,WeaponFirmlyPlanted.stabilityBonus(f.p)==10&&WeaponFirmlyPlanted.handlingBonus(f.p)==15,"Fusion10/15 not enhanced13/18");
        check(h,WeaponFirmlyPlanted.accuracyScalar(f.p)==.8&&WeaponFirmlyPlanted.growthScalar(f.p)==.915&&WeaponFirmlyPlanted.yawScalar(f.p)==.6,"Fusion cone/growth/yaw independent");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void paidHipShotKeepsDamageAndAmmoAndSeparatesYawFromVertical(GameTestHelper h){
        var f=new Fixture(h);f.crouch(true);f.p.setYRot(-90);f.p.setYHeadRot(-90);f.p.setXRot(0);
        var target=h.spawn(EntityTypes.HUSK,new Vec3(8.5,1,6));target.setPos(f.p.getEyePosition().add(6,-.7,0));
        target.setNoAi(true);target.setNoGravity(true);target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);target.getAttribute(Attributes.ARMOR).setBaseValue(0);target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);target.setHealth(1000);TestCleanup.register(h,target::discard);
        WeaponAiming.cleanup(f.p);WeaponAiming.tick(f.p);var aim=WeaponAimProfile.of(f.entry);float kick=RapidHitStability.kick(aim,20);
        float expectedYaw=(float)Math.sin(Math.toRadians(aim.recoilDirection()*18))*(100-aim.recoilDirection())/100f*kick*.5f*.2f;
        check(h,beginUse(f.p),"Actual funded trigger accepted");WeaponRuntime.releaseUse(f.p,f.gun);
        check(h,WeaponItems.magazine(f.gun,f.profile).rounds()==0,"Exactly one paid round");
        check(h,Math.abs(f.p.getXRot()+kick)<.0001&&Math.abs(f.p.getYRot()+90-expectedYaw)<.0001,"Horizontal-only.2 separate from stability-adjusted vertical kick");
        float bloom=(float)(RapidHitStability.bloom(aim,20)*.83);
        check(h,Math.abs(WeaponAiming.bloom(f.p)-bloom)<.00001,".83 growth applied separately from cone.6");
        var accuracy=WeaponAccuracy.of(f.entry);
        double hip=(accuracy.hipDegrees()+Math.toDegrees(.006*bloom))*.6;
        double air=WeaponAccuracy.airborne(f.p)?accuracy.airDegrees()*(1-WeaponAccuracy.airborne(f.entry,f.gun)/100.0):0;
        double cone=Math.hypot(hip,air);
        check(h,Math.abs(WeaponAiming.coneDegrees(f.p)-cone)<.000001,"W241 hip+bloom scalar applied once; airborne cone stays independent");
        f.p.getRandom().setSeed(171);
        double radius=Math.sqrt(f.p.getRandom().nextDouble())*Math.tan(Math.toRadians(cone));
        double theta=f.p.getRandom().nextDouble()*Math.PI*2;
        var dir=f.p.getLookAngle().normalize();var right=dir.cross(Vec3.Y_AXIS).normalize();var up=right.cross(dir);
        var expectedRay=dir.add(right.scale(Math.cos(theta)*radius)).add(up.scale(Math.sin(theta)*radius)).normalize();
        f.p.getRandom().setSeed(171);
        check(h,WeaponAiming.direction(f.p).distanceTo(expectedRay)<.000001,"Actual stochastic disk ray matches the same seeded preflight");
        float damage=WeaponAiming.ballistics(f.p,f.entry).damage(f.profile.damage(),6,false);
        check(h,1000-target.getHealth()>0&&Math.abs(1000-target.getHealth()-damage)<.01,"No invented damage bonus");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void rawArcCompositionFeedsActualAdsAndOwnedIncomingHandling(GameTestHelper h){
        var f=new Fixture(h);f.arc();check(h,WeaponPerks.select(f.gun,ElementalCapacitorProfile.ID),"Steel distinct EC socket");f.crouch(true);
        int total=80;int ads=FirmlyPlantedProfile.adsTicks(f.entry,total,false);
        check(h,WeaponFirmlyPlanted.adsTicks(f.p,f.entry,99,true)==ads,"Raw30+50 stats before one ceil");
        WeaponAiming.cleanup(f.p);ads(f.p,true);WeaponAiming.tick(f.p);
        check(h,Math.abs(WeaponAiming.progress(f.p)-1f/WeaponAiming.fast(ads))<.00001,"Production outer ADS wrapper exact raw composition");ads(f.p,false);
        int stow=FirmlyPlantedProfile.handlingTicks(f.entry,total,1,false),ready=FirmlyPlantedProfile.handlingTicks(f.entry,total,1,true);
        WeaponRuntime.selectedSlotChanging(f.p,7);f.p.getInventory().setSelectedSlot(7);
        check(h,!WeaponFirmlyPlanted.active(f.p),"Stowed source cannot grant held effects");
        check(h,WeaponFirmlyPlanted.handlingTicks(f.p,f.gun,true,99)==ready,"Incoming genuine source retains30+50");
        f.p.getInventory().setSelectedSlot(WeaponCharacteristics.of(f.entry).slot().hotbar());WeaponHandling.update(f.p);
        check(h,WeaponHandling.remaining(f.p)==stow+ready,"Actual accepted handling clock");f.crouch(false);
        h.startSequence().thenIdle(1).thenExecute(()->{check(h,WeaponHandling.remaining(f.p)==stow+ready-1,"Standing cannot retime accepted swap deadline");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void exactSnapshotPairOnlyAcceleratesAdsEntry(GameTestHelper h){
        var f=new Fixture(h,"apostate");check(h,WeaponPerks.select(f.gun,SnapshotAimProfile.ID),"Exact legal Apostate second trait");
        check(h,WeaponPerks.selected(f.gun,ID).isPresent(),"Snapshot does not erase FirmlyPlanted");f.crouch(true);
        int enter=FirmlyPlantedProfile.adsTicks(f.entry,30,true),exit=FirmlyPlantedProfile.adsTicks(f.entry,30,false);
        check(h,enter<exit&&WeaponFirmlyPlanted.adsTicks(f.p,f.entry,99,true)==enter&&WeaponFirmlyPlanted.adsTicks(f.p,f.entry,99,false)==exit,"Snapshot entry scalar composed raw, exit unchanged");
        WeaponAiming.cleanup(f.p);ads(f.p,true);WeaponAiming.tick(f.p);check(h,Math.abs(WeaponAiming.progress(f.p)-1f/WeaponAiming.fast(enter))<.00001,"Actual ADS first tick");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void sourceCopiesBackpackOffhandAndInvalidCountDoNotGrant(GameTestHelper h){
        var f=new Fixture(h);f.crouch(true);check(h,WeaponFirmlyPlanted.active(f.p),"Valid initial source");
        check(h,WeaponFirmlyPlanted.handlingTicks(f.p,f.gun.copy(),true,99)==99,"Detached equal-data copy denied");
        int slot=f.p.getInventory().getSelectedSlot();f.p.getInventory().setItem(slot,ItemStack.EMPTY);f.p.getInventory().setItem(10,f.gun);
        check(h,!WeaponFirmlyPlanted.active(f.p)&&WeaponFirmlyPlanted.handlingTicks(f.p,f.gun,true,99)==99,"Backpack excluded");
        f.p.getInventory().setItem(10,ItemStack.EMPTY);f.p.setItemInHand(net.minecraft.world.InteractionHand.OFF_HAND,f.gun);
        check(h,WeaponFirmlyPlanted.handlingTicks(f.p,f.gun,true,99)==99,"Offhand excluded");
        f.p.setItemInHand(net.minecraft.world.InteractionHand.OFF_HAND,ItemStack.EMPTY);f.p.getInventory().setItem(slot,f.gun);f.gun.setCount(2);
        check(h,!WeaponFirmlyPlanted.active(f.p),"Count2 corrupt source denied");f.gun.setCount(1);check(h,WeaponFirmlyPlanted.active(f.p),"Original restored");WeaponPerks.clear(f.gun);
        check(h,!WeaponFirmlyPlanted.active(f.p),"Socket clear immediate and read-only");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void passiveReadsDoNotMutateOrCreateHudOrReloadBonus(GameTestHelper h){
        var f=new Fixture(h);f.crouch(true);var copy=f.gun.copy();var data=Guardians.data(f.p).copy();
        var before=WeaponReloadPolicy.forEntry(f.entry,f.profile.reloadTicks(),f.profile.shellReload());
        for(int i=0;i<20;i++){check(h,WeaponFirmlyPlanted.active(f.p),"Repeated crouch query");WeaponFirmlyPlanted.handlingTicks(f.p,f.gun,true,99);}
        check(h,ItemStack.matches(copy,f.gun)&&data.cooldownsView().equals(Guardians.data(f.p).cooldownsView()),"No item or ability state writes");
        CombatHud.update(f.p);check(h,DisplayHud.getHuds(f.p).keySet().stream().noneMatch(k->k.contains(ID)),"No fabricated perk proc HUD");
        check(h,WeaponRuntime.reload(f.p)&&WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==before.firstTicks(),"No reload bonus");
        var runtime=Guardians.runtime(f.p);runtime.superSession=new SuperSession(){public boolean tick(){return true;}public void primary(){}public void end(){}public float remaining(){return 1;}};
        check(h,!WeaponFirmlyPlanted.active(f.p),"Active ultimate excludes weapon passive");runtime.superSession=null;h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void actualIncomingHurtUsesCrouchedStabilityWithoutDamageResistance(GameTestHelper h){
        var f=new Fixture(h);var attacker=h.spawn(EntityTypes.HUSK,new Vec3(8,1,6));attacker.setNoAi(true);attacker.setNoGravity(true);TestCleanup.register(h,attacker::discard);
        f.p.getAttribute(Attributes.ARMOR).setBaseValue(0);f.p.getAttribute(Attributes.ARMOR_TOUGHNESS).setBaseValue(0);f.p.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        float[] pitch=new float[2];
        for(int i=0;i<2;i++){
            f.crouch(i==1);f.p.setHealth(20);f.p.setAbsorptionAmount(0);f.p.damageCooldownTime=0;f.p.setXRot(0);
            WeaponAiming.cleanup(f.p);WeaponAiming.tick(f.p);f.p.hurtServer(f.p.level(),f.p.damageSources().mobAttack(attacker),2);
            pitch[i]=-f.p.getXRot();check(h,f.p.getHealth()==18,"No incoming damage resistance");
        }
        var aim=WeaponAimProfile.of(f.entry);
        float expected=WeaponFlinchState.magnitude(2,20,RapidHitStability.effective(aim.stability(),20),WeaponFlinchProfile.maxResistance(f.entry),0,false);
        check(h,pitch[0]>pitch[1]&&Math.abs(pitch[1]-expected)<.0001,"Actual Player hurt hook includes exact crouched stability once");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=270,environment=ENV)
    public void legalEarnedFrenzyComposesWithFusionHandlingBeforeSingleCeil(GameTestHelper h){
        var f=new Fixture(h,"dream_breaker");check(h,WeaponPerks.select(f.gun,FrenzyProfile.ID),"Dream distinct official Frenzy socket");f.tick();
        long started=f.p.level().getServer().getTickCount();
        Runnable damage=()->{
            // Use a fresh persistent enemy for each actual hurt event, as in the Frenzy fixture.
            var enemy=h.spawn(EntityTypes.HUSK,new Vec3(8,1,6));enemy.setNoAi(true);enemy.setNoGravity(true);enemy.setPersistenceRequired();
            enemy.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);enemy.getAttribute(Attributes.ARMOR).setBaseValue(0);enemy.setHealth(1000);TestCleanup.register(h,enemy::discard);
            kim.biryeong.destiny.combat.Combat.damage(f.p.level(),f.p,enemy,1,Element.VOID,AmmoGeneration.ABILITY);
            check(h,enemy.getHealth()==999,"Actual positive combat event at server elapsed "+(f.p.level().getServer().getTickCount()-started));
        };
        damage.run();
        // Each sequence owns its deadline; repeated callbacks cannot replace earlier combat events.
        for(int t:new int[]{80,160,230})h.startSequence().thenIdle(t).thenExecute(new Runnable(){public void run(){damage.run();}});
        h.startSequence().thenIdle(242).thenExecute(()->{
            check(h,WeaponFrenzy.ownedRemaining(f.p,f.gun)>0,"Earned via actual postmitigation combat hooks: serverElapsed="+(f.p.level().getServer().getTickCount()-started)+" combat="+WeaponFrenzy.combatTicks(f.p));f.crouch(true);
            int total=15+FrenzyProfile.handlingBonus();
            check(h,WeaponFirmlyPlanted.handlingTicks(f.p,f.gun,true,99)==FirmlyPlantedProfile.handlingTicks(f.entry,total,1,true),"Fusion15 plus actual Frenzy100 raw curve");
            int ads=FirmlyPlantedProfile.adsTicks(f.entry,total,false);
            WeaponAiming.cleanup(f.p);ads(f.p,true);WeaponAiming.tick(f.p);
            check(h,Math.abs(WeaponAiming.progress(f.p)-1f/WeaponAiming.fast(ads))<.0001,"Actual capped raw handling ADS, no rounded-duration multiplication");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void exactEightOptionalBaseWeaponsNeverGainDefaultOrEnhanced(GameTestHelper h){
        var ids=Set.of("seventh_seraph_officer_revolver","steelfeather_repeater","distant_relation","whispering_slab","bite_of_the_fox","beloved","apostate","dream_breaker");int count=0;
        for(var e:WeaponCatalog.all()){
            var gun=WeaponItems.create(e);check(h,WeaponPerks.selected(gun,ID).isEmpty(),"No implicit trait");
            boolean expected=ids.contains(e.id());check(h,WeaponPerks.select(gun,ID)==expected,"Official base source "+e.id());if(expected)count++;
        }
        check(h,count==8,"Exact eight, not every fusion or remodeled weapon");h.succeed();
    }
}
