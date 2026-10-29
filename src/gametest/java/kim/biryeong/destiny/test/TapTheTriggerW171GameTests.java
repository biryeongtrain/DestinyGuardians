package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Real paid server emission/charge/lifecycle/HUD tests, not native keyboard or pixel proof. */
public final class TapTheTriggerW171GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="tap_the_trigger",PREFIX="destiny:hud_perk_tap_the_trigger_";
    static void check(GameTestHelper h,boolean yes,String why){h.assertTrue(yes,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final ItemStack gun;final WeaponCatalog.Entry entry;final WeaponProfile profile;
        Fixture(GameTestHelper h){this(h,"ammit_ar2");}
        Fixture(GameTestHelper h,String id){
            this.h=h;entry=WeaponCatalog.find(id).orElseThrow();profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W171_"+UUID.randomUUID().toString().substring(0,8));
            p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,true);
            gun=WeaponItems.create(entry);check(h,WeaponPerks.select(gun,ID),"Exact base TTT socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),200));
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
            h.onEachTick(()->TestPlayers.drain(p));
            TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        WeaponMagazine ammo(){return WeaponItems.magazine(gun,profile);}
        void fire(){check(h,beginUse(p),"Actual use accepted");}
        void release(){WeaponRuntime.releaseUse(p,gun);}
        int remaining(){return WeaponTapTheTrigger.remaining(p);}
    }
    static void hud(GameTestHelper h,ServerPlayer p,boolean active){
        CombatHud.update(p);var nodes=DisplayHud.getHuds(p);
        check(h,nodes.keySet().stream().filter(k->k.startsWith(PREFIX)).count()==(active?6:0),"Live six-node timer only while actual state active");
        if(active){var n=nodes.get(PREFIX+"ones");check(h,n instanceof ItemDisplayHud&&Identifier.parse("destiny:gui/hud/ammo_digit_1").equals(((ItemDisplayHud)n).getItem().get(DataComponents.ITEM_MODEL)),"Twelve ticks ceil to1second; not an invented long timer");}
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void paidFirstEmissionChangesActualRecoilAndHudThenExpires(GameTestHelper h){
        var f=new Fixture(h);WeaponAiming.cleanup(f.p);WeaponAiming.tick(f.p);int before=f.ammo().rounds();f.fire();
        float expected=RapidHitStability.kick(WeaponAimProfile.of(f.entry),40)*.5f;
        check(h,f.ammo().rounds()==before-1&&f.remaining()==12,"Exactly one paid round starts12ticks");
        check(h,Math.abs(f.p.getXRot()+expected)<1e-5,"First paid shot receives +40stability and half recoil");
        check(h,WeaponTapTheTrigger.accuracyScalar(f.p)==.9f,"Actual source accuracy adapter");
        var accuracy=WeaponAccuracy.of(f.entry);
        double hip=(accuracy.hipDegrees()+Math.toDegrees(.006*RapidHitStability.bloom(WeaponAimProfile.of(f.entry),40)))*.9;
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
        f.release();hud(h,f.p,true);
        h.startSequence().thenIdle(13).thenExecute(()->{check(h,f.remaining()==0&&WeaponTapTheTrigger.stabilityBonus(f.p)==0,"Twelve ticks expired");hud(h,f.p,false);h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=55,environment=ENV)
    public void heldAutomaticDoesNotRefreshUntilRealRelease(GameTestHelper h){
        var f=new Fixture(h);check(h,WeaponRuntime.heartbeatUse(f.p),"Real two-hand heartbeat accepted");
        for(int i=1;i<=28;i++){int t=i;h.startSequence().thenIdle(i).thenExecute(()->{if(t%4==0)WeaponRuntime.heartbeatUse(f.p);WeaponRuntime.tickPlayer(f.p);});}
        h.startSequence().thenIdle(20).thenExecute(()->{check(h,f.ammo().rounds()<f.profile.magazine()-2,"Actual held automatic emits multiple paid shots");check(h,f.remaining()==0,"Held shots/heartbeats cannot refresh expired window");hud(h,f.p,false);});
        h.startSequence().thenIdle(36).thenExecute(()->{f.release();f.fire();check(h,f.remaining()==12,"Accepted new paid trigger after real stop rearms");f.release();h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void emptyAndCadenceDeniedTriggersDoNotFabricateWindows(GameTestHelper h){
        var f=new Fixture(h);WeaponItems.save(f.gun,new WeaponMagazine(f.profile,0,0));
        check(h,!beginUse(f.p)&&f.remaining()==0,"Empty primary may start infinite-reserve reload, but no paid emission or buff");hud(h,f.p,false);
        WeaponRuntime.cancelUseForSkill(f.p);
        WeaponItems.save(f.gun,new WeaponMagazine(f.profile,5,0));f.fire();f.release();int rounds=f.ammo().rounds();
        check(h,!beginUse(f.p)&&f.ammo().rounds()==rounds&&f.remaining()==12,"Same-tick cadence denial cannot refresh/pay");
        for(int i=0;i<100;i++)WeaponTapTheTrigger.remaining(f.p);
        h.startSequence().thenIdle(13).thenExecute(()->{check(h,f.remaining()==0,"Pure queries do not extend deadline");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=100,environment=ENV)
    public void fusionChargeIsUnpaidThenSinglePaidBurstGetsQuarterBenefits(GameTestHelper h){
        var f=new Fixture(h,"dream_breaker");int before=f.ammo().rounds();f.fire();
        check(h,f.remaining()==0&&f.ammo().rounds()==before,"Charge alone grants nothing");
        for(int i=1;i<=f.profile.chargeTicks();i++)h.startSequence().thenIdle(i).thenExecute(()->WeaponRuntime.continueUse(f.p));
        h.startSequence().thenIdle(f.profile.chargeTicks()+1).thenExecute(()->{
            check(h,f.ammo().rounds()==before-1,"Only one shared cartridge funds fusion burst");
            check(h,f.remaining()>0&&f.remaining()<=12&&WeaponTapTheTrigger.stabilityBonus(f.p)==10,"Quarter fusion stability and current12tickwindow");
            check(h,WeaponTapTheTrigger.recoilScalar(f.p)==.875f&&WeaponTapTheTrigger.accuracyScalar(f.p)==.975f,"Quarter recoil/accuracy benefits");f.release();
        });
        for(int i=f.profile.chargeTicks()+2;i<=f.profile.chargeTicks()+16;i++)h.startSequence().thenIdle(i).thenExecute(()->WeaponRuntime.tickPlayer(f.p));
        h.startSequence().thenIdle(f.profile.chargeTicks()+17).thenExecute(()->{check(h,f.remaining()==0&&f.ammo().rounds()==before-1,"Supplemental bolts never refresh or spend another cartridge");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=60,environment=ENV)
    public void copyEditsStowAndCleanupCannotCarryActivation(GameTestHelper h){
        var f=new Fixture(h);f.fire();f.release();check(h,f.remaining()==12,"Earned window");
        int slot=f.p.getInventory().getSelectedSlot();var copy=f.gun.copy();f.p.getInventory().setItem(slot,copy);WeaponRuntime.tickPlayer(f.p);
        check(h,f.remaining()==0,"Copy has no live source");f.p.getInventory().setItem(slot,f.gun);WeaponRuntime.tickPlayer(f.p);check(h,f.remaining()==0,"Observed replacement revokes old session");
        h.startSequence().thenIdle(35).thenExecute(()->{f.fire();f.release();check(h,f.remaining()==12,"Re-earned window");check(h,WeaponPerks.clear(f.gun)&&WeaponPerks.select(f.gun,ID),"Actual selection edit");check(h,f.remaining()==0,"Edit revokes same-tick activation");WeaponRuntime.cleanup(f.p);check(h,f.remaining()==0,"Cleanup inert");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=10,environment=ENV)
    public void onlySixExactBaseWeaponSocketsAreSelectable(GameTestHelper h){
        var ids=Set.of("ammit_ar2","gnawing_hunger","dead_man_walking_xx7463","dream_breaker","hammerhead","retrofit_escapade");int found=0;
        for(var e:WeaponCatalog.all()){var stack=WeaponItems.create(e);boolean expected=ids.contains(e.id());check(h,WeaponPerks.select(stack,ID)==expected,"Exact6 baseeligibility: "+e.id());if(expected)found++;}
        check(h,found==6,"All six and no accidental catalog expansion");h.succeed();
    }
}
