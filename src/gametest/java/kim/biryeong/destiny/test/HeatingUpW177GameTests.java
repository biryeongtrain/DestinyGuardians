package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.combat.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
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

/** Actual paid final blows and server aim/HUD/lifecycle, not native input or rendered pixels. */
public final class HeatingUpW177GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="heating_up";
    static void check(GameTestHelper h,boolean yes,String why){h.assertTrue(yes,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final ItemStack gun;final WeaponCatalog.Entry entry;
        final WeaponProfile profile;final List<Husk> targets=new ArrayList<>();
        Fixture(GameTestHelper h){
            this.h=h;
            entry=HeatingUpProfile.rolls().stream().map(x->WeaponCatalog.find(x.id()).orElseThrow())
                    .filter(e->{var a=WeaponProfile.forEntry(e);return a.mode()==WeaponProfile.Mode.HITSCAN&&a.burst()==1;}).findFirst().orElseThrow();
            profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W177_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,true);
            gun=WeaponItems.create(entry);check(h,WeaponPerks.select(gun,ID),"Exact official base Heating Up socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),200));
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
            h.onEachTick(()->{WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);});
            TestCleanup.register(h,()->{targets.forEach(t->{Statuses.forget(t);t.discard();});WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        Husk target(float health){
            targets.forEach(t->{Statuses.forget(t);t.discard();});targets.clear();
            var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,1.8,6));targets.add(t);t.setNoAi(true);t.setNoGravity(true);
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(health);return t;
        }
        float fire(Husk t){
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            int before=WeaponItems.magazine(gun,profile).rounds();float health=t.getHealth();
            check(h,beginUse(p),"Actual paid trigger accepted");WeaponRuntime.releaseUse(p,gun);
            check(h,WeaponItems.magazine(gun,profile).rounds()==before-1,"One cartridge funds this final-blow candidate");return health-t.getHealth();
        }
        Husk kill(){var t=target(1);check(h,fire(t)>0&&t.isDeadOrDying(),"Actual paid enemy final blow");return t;}
        int gap(){return Math.max(12,(int)Math.ceil(profile.cadenceTicks())+2);}
        void two(Runnable done){kill();h.startSequence().thenIdle(gap()).thenExecute(()->{kill();done.run();});}
        int stacks(){return WeaponHeatingUp.stacks(p);} int remaining(){return WeaponHeatingUp.remaining(p);}
        void hud(boolean active){CombatHud.update(p);check(h,DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith("destiny:hud_perk_heating_up_")).count()==(active?8:0),"Actual x/count/timer nodes reflect runtime");}
        void stow(){WeaponRuntime.selectedSlotChanging(p,7);p.getInventory().setSelectedSlot(7);WeaponRuntime.tickPlayer(p);}
        void restore(){p.getInventory().setSelectedSlot(WeaponCharacteristics.of(entry).slot().hotbar());WeaponRuntime.tickPlayer(p);}
    }
    @GameTest(structure=FLOOR,maxTicks=200,environment=ENV)
    public void actualPaidKillsStackCapRefreshAndExactExpiryDriveHud(GameTestHelper h){
        var f=new Fixture(h);f.hud(false);f.kill();
        check(h,f.stacks()==1&&f.remaining()==110&&WeaponHeatingUp.stabilityBonus(f.p)==15,"First real kill: sourced one-stack/5.5seconds");f.hud(true);
        h.startSequence().thenIdle(f.gap()).thenExecute(()->{f.kill();check(h,f.stacks()==2&&f.remaining()==110,"Second real kill refreshes at2");f.hud(true);
            h.startSequence().thenIdle(f.gap()).thenExecute(()->{f.kill();check(h,f.stacks()==2&&f.remaining()==110,"Further final blow refreshes without stack3");
                h.startSequence().thenIdle(110).thenExecute(()->{check(h,f.stacks()==0&&f.remaining()==0,"Exact110tick expiry removes whole buff");f.hud(false);h.succeed();});});});
    }
    @GameTest(structure=FLOOR,maxTicks=140,environment=ENV)
    public void livePaidShotUsesStabilityDirectionAndBothAccuracyScalarsWithoutDamageBuff(GameTestHelper h){
        var f=new Fixture(h);float baseline=f.fire(f.target(1000));
        h.startSequence().thenIdle(f.gap()).thenExecute(()->f.two(()->h.startSequence().thenIdle(f.gap()).thenExecute(()->{
            float damage=f.fire(f.target(1000));check(h,Math.abs(damage-baseline)<.001,"No raw damage multiplier from Heating Up");
            var aim=WeaponAimProfile.of(f.entry);float kick=RapidHitStability.kick(aim,30);
            check(h,Math.abs(f.p.getXRot()+kick)<.0001,"Real paid recoil uses stability+30");
            int dir=Math.clamp(aim.recoilDirection()+40,0,100);
            float side=(float)Math.sin(Math.toRadians(dir*18))*(100-dir)/100f*kick*.5f;
            check(h,Math.abs(f.p.getYRot()-(-90+side))<.0001,"Actual horizontal recoil uses capped direction+40");
            float bloom=RapidHitStability.bloom(aim,30)*.75f;
            check(h,Math.abs(WeaponAiming.bloom(f.p)-bloom)<.00001,"Real paid shot applies growth.75 as well as stability");
        var accuracy=WeaponAccuracy.of(f.entry);
        double hip=(accuracy.hipDegrees()+Math.toDegrees(.006*bloom))*.75;
        double air=WeaponAccuracy.airborne(f.p)?accuracy.airDegrees()*(1-WeaponAccuracy.airborne(f.entry,f.gun)/100.0):0;
        double cone=Math.hypot(hip,air);
        check(h,Math.abs(WeaponAiming.coneDegrees(f.p)-cone)<.000001,"W241 hip+bloom scalar applied once; airborne cone stays independent");
        f.p.getRandom().setSeed(171);
        double radius=Math.sqrt(f.p.getRandom().nextDouble())*Math.tan(Math.toRadians(cone));
        double theta=f.p.getRandom().nextDouble()*Math.PI*2;
        var forward=f.p.getLookAngle().normalize();var right=forward.cross(Vec3.Y_AXIS).normalize();var up=right.cross(forward);
        var expectedRay=forward.add(right.scale(Math.cos(theta)*radius)).add(up.scale(Math.sin(theta)*radius)).normalize();
        f.p.getRandom().setSeed(171);
        check(h,WeaponAiming.direction(f.p).distanceTo(expectedRay)<.000001,"Actual stochastic disk ray matches the same seeded preflight");h.succeed();
        })));
    }
    @GameTest(structure=FLOOR,maxTicks=100,environment=ENV)
    public void nonlethalImmuneMissAbilitiesAndReadOnlyQueriesCannotGrantStacks(GameTestHelper h){
        var f=new Fixture(h);check(h,f.fire(f.target(1000))>0&&f.stacks()==0,"Nonlethal actual paid hit is not a kill");
        h.startSequence().thenIdle(f.gap()).thenExecute(()->{var t=f.target(1);t.setPermanentlyInvulnerable(true);check(h,f.fire(t)==0&&f.stacks()==0,"Actual0damage contact");
            h.startSequence().thenIdle(f.gap()).thenExecute(()->{var miss=f.target(1);miss.discard();f.fire(miss);check(h,f.stacks()==0,"Actual paid miss");
                var ability=f.target(1);Combat.damage(f.p.level(),f.p,ability,10,Element.VOID,AmmoGeneration.ABILITY);
                for(int i=0;i<20;i++){f.hud(false);WeaponHeatingUp.capture(f.p);WeaponHeatingUp.stacks(f.p);}
                check(h,ability.isDeadOrDying()&&f.stacks()==0&&f.remaining()==0,"Ability final blow and queries do not create weapon credit");h.succeed();});});
    }
    @GameTest(structure=FLOOR,maxTicks=100,environment=ENV)
    public void equippedStowAndAcceptedReloadPreserveRealAbsoluteClock(GameTestHelper h){
        var f=new Fixture(h);f.kill();int earned=f.remaining();f.stow();
        check(h,f.stacks()==0&&WeaponHeatingUp.ownedStacks(f.p,f.gun)==1,"Sourced stow survival but held-only HUD");f.hud(false);
        h.startSequence().thenIdle(8).thenExecute(()->{f.restore();check(h,f.remaining()==earned-8&&f.stacks()==1,"No pause or refresh while stowed");
            h.startSequence().thenIdle(20).thenExecute(()->{int before=f.remaining();check(h,WeaponRuntime.reload(f.p),"Actual accepted ordinary reload");
                check(h,f.remaining()==before&&f.stacks()==1,"Local reload policy preserves deadline, no made-up reload bonus");
                check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==f.profile.reloadTicks(),"Original accepted duration");h.succeed();});});
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void corpseCreditCannotBeDuplicatedAcrossTokensFromOriginalSource(GameTestHelper h){
        var f=new Fixture(h);var one=WeaponHeatingUp.capture(f.p);var two=WeaponHeatingUp.capture(f.p);var corpse=f.kill();
        WeaponHeatingUp.killed(f.p,one,corpse);WeaponHeatingUp.killed(f.p,two,corpse);
        check(h,f.stacks()==1,"Source-level corpse guard covers multiple pellets/projectiles/callbacks");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void oldCopyEditBackpackRuntimeAndCleanupCannotBorrowOriginalCredit(GameTestHelper h){
        var f=new Fixture(h);var token=WeaponHeatingUp.capture(f.p);int slot=f.p.getInventory().getSelectedSlot();
        var corpse=f.target(1);Combat.damage(f.p.level(),f.p,corpse,10,Element.VOID,AmmoGeneration.ABILITY);
        f.p.getInventory().setItem(slot,f.gun.copy());WeaponRuntime.tickPlayer(f.p);WeaponHeatingUp.killed(f.p,token,corpse);
        check(h,f.stacks()==0,"CopiedNBT cannot use old token");
        f.p.getInventory().setItem(slot,f.gun);WeaponRuntime.tickPlayer(f.p);token=WeaponHeatingUp.capture(f.p);
        WeaponPerks.clear(f.gun);WeaponPerks.select(f.gun,ID);WeaponHeatingUp.killed(f.p,token,corpse);check(h,f.stacks()==0,"Same-tick trait edit invalidates");
        token=WeaponHeatingUp.capture(f.p);f.p.getInventory().setItem(slot,ItemStack.EMPTY);f.p.getInventory().setItem(12,f.gun);
        WeaponRuntime.tickPlayer(f.p);WeaponHeatingUp.killed(f.p,token,corpse);check(h,WeaponHeatingUp.ownedStacks(f.p,f.gun)==0,"Backpack not equipped");
        f.p.getInventory().setItem(12,ItemStack.EMPTY);f.p.getInventory().setItem(slot,f.gun);WeaponRuntime.tickPlayer(f.p);token=WeaponHeatingUp.capture(f.p);
        Guardians.forget(f.p);Guardians.runtime(f.p);WeaponHeatingUp.killed(f.p,token,corpse);check(h,f.stacks()==0,"Guardian runtime replacement invalidates");
        token=WeaponHeatingUp.capture(f.p);WeaponRuntime.cleanup(f.p);WeaponHeatingUp.killed(f.p,token,corpse);check(h,f.stacks()==0,"Cleanup retires source");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=10,environment=ENV)
    public void onlyExactOptionalOfficialBaseSocketsAreSelectable(GameTestHelper h){
        var allowed=HeatingUpProfile.rolls().stream().map(WeaponPerks.Roll::id).collect(java.util.stream.Collectors.toSet());int count=0;
        for(var e:WeaponCatalog.all()){var s=WeaponItems.create(e);check(h,WeaponPerks.selected(s,ID).isEmpty(),"No invented default");
            check(h,WeaponPerks.select(s,ID)==allowed.contains(e.id()),"Exact selected65pool:"+e.id());if(allowed.contains(e.id()))count++;}
        check(h,count==allowed.size()&&count>0,"Only current official base trait pool members");h.succeed();
    }
}
