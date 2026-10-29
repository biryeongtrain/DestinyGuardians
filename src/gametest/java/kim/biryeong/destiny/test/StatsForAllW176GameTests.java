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

/** Real paid hits/server timings/HUD registry, not a native-keyboard or rendered-pixel claim. */
public final class StatsForAllW176GameTests {
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="stats_for_all";
    static void check(GameTestHelper h,boolean yes,String why){h.assertTrue(yes,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final ItemStack gun;final WeaponCatalog.Entry entry;
        final WeaponProfile profile;final List<Husk> targets=new ArrayList<>();
        Fixture(GameTestHelper h){this(h,"aishas_embrace");}
        Fixture(GameTestHelper h,String id){
            this.h=h;entry=WeaponCatalog.find(id).orElseThrow();profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W176_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,true);
            gun=WeaponItems.create(entry);check(h,WeaponPerks.select(gun,ID),"Exact official base Stats for All socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),200));
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
            h.onEachTick(()->{WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);});
            TestCleanup.register(h,()->{targets.forEach(t->{Statuses.forget(t);t.discard();});WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        Husk target(){return target(8.5);}
        Husk target(double x){
            targets.forEach(t->{Statuses.forget(t);t.discard();});targets.clear();
            var t=h.spawn(EntityTypes.HUSK,new Vec3(x,1.8,6));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.setPersistenceRequired();
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(1000);return t;
        }
        float fire(Husk t){
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            int before=WeaponItems.magazine(gun,profile).rounds();float health=t.getHealth();
            // Replay the inspected W241 ray, keeping real hip/air spread, payment and collision.
            p.getRandom().setSeed(0x5DEECE66DL);
            check(h,WeaponRuntime.beginUse(p),"Actual paid trigger accepted");WeaponRuntime.releaseUse(p,gun);
            check(h,WeaponItems.magazine(gun,profile).rounds()==before-1,"Exactly one cartridge paid");return health-t.getHealth();
        }
        int gap(){return Math.max(12,(int)Math.ceil(profile.cadenceTicks())+2);}
        void three(Runnable done){
            check(h,fire(target())>0,"First actual distinct positive body contact");
            h.runAfterDelay(gap(),()->{check(h,fire(target())>0,"Second distinct positive contact");
                h.runAfterDelay(gap(),()->{check(h,fire(target())>0,"Third distinct positive contact");done.run();});});
        }
        int remaining(){return WeaponStatsForAll.remaining(p);}
        void hud(boolean active){CombatHud.update(p);check(h,DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith("destiny:hud_perk_stats_for_all_")).count()==(active?6:0),"Actual six-node timer uses live state");}
        void stow(){WeaponRuntime.selectedSlotChanging(p,7);p.getInventory().setSelectedSlot(7);WeaponRuntime.tickPlayer(p);}
        void restore(){p.getInventory().setSelectedSlot(WeaponCharacteristics.of(entry).slot().hotbar());WeaponRuntime.tickPlayer(p);}
    }
    @GameTest(structure=FLOOR,maxTicks=270,environment=ENV)
    public void actualThreeDistinctPaidHitsActivateStatsNotDamageAndCannotRefresh(GameTestHelper h){
        var f=new Fixture(h);float baseline=f.fire(f.target());check(h,baseline>0&&WeaponStatsForAll.progress(f.p)==1&&f.remaining()==0,"First paid body hit primes only");f.hud(false);
        h.runAfterDelay(f.gap(),()->{f.fire(f.target());check(h,WeaponStatsForAll.progress(f.p)==2&&f.remaining()==0,"Second distinct target primes only");
            h.runAfterDelay(f.gap(),()->{f.fire(f.target());check(h,f.remaining()==200&&WeaponStatsForAll.progress(f.p)==0,"Third actual enemy starts sourced10seconds");f.hud(true);
                check(h,WeaponStatsForAll.stabilityBonus(f.p)==10,"Real stability bonus");
                var hip=WeaponBallistics.of(f.entry);var active=WeaponStatsForAll.ballistics(f.p,f.entry);
                check(h,active.start()>hip.start()&&active.end()>hip.end()&&active.floor()==hip.floor()&&active.precision()==hip.precision(),"Range shifts falloff, not precision or floor");
                h.runAfterDelay(f.gap(),()->{float damage=f.fire(f.target());check(h,Math.abs(damage-baseline)<.001,"No invented raw damage buff");check(h,f.remaining()==200-f.gap(),"New distinct enemy cannot refresh active window");});
                h.runAfterDelay(200,()->{check(h,f.remaining()==0&&WeaponStatsForAll.stabilityBonus(f.p)==0,"Exact200tick expiry");check(h,WeaponStatsForAll.ballistics(f.p,f.entry).equals(hip),"Original range restored");f.hud(false);h.succeed();});
            });
        });
    }
    @GameTest(structure=FLOOR,maxTicks=140,environment=ENV)
    public void collectionWindowIsBetweenDistinctTargetsNotTotalAndDuplicatesCannotRenew(GameTestHelper h){
        var f=new Fixture(h);var first=f.target();f.fire(first);
        h.runAfterDelay(40,()->{check(h,f.fire(first)>0,"Actual repeated enemy can be hurt again");check(h,WeaponStatsForAll.progress(f.p)==1,"Same UUID remains one enemy");});
        h.runAfterDelay(60,()->{f.fire(f.target());check(h,WeaponStatsForAll.progress(f.p)==1&&f.remaining()==0,"Duplicate did not renew original deadline; exact60 expired");});
        h.runAfterDelay(119,()->{f.fire(f.target());check(h,WeaponStatsForAll.progress(f.p)==2,"Second new enemy59ticks later renews collection");});
        h.runAfterDelay(131,()->{f.fire(f.target());check(h,f.remaining()==200,"Three distinct within3seconds of each, not all within first3seconds");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=100,environment=ENV)
    public void abilitiesImmuneMissAndReadOnlyHudCannotCollect(GameTestHelper h){
        var f=new Fixture(h);var ability=f.target();Combat.damage(f.p.level(),f.p,ability,1,Element.VOID,AmmoGeneration.ABILITY);
        check(h,WeaponStatsForAll.progress(f.p)==0,"Ability-only actual damage excluded");
        var immune=f.target();immune.setPermanentlyInvulnerable(true);check(h,f.fire(immune)==0,"Actual invulnerable contact");
        check(h,WeaponStatsForAll.progress(f.p)==0,"No0damage credit");
        h.runAfterDelay(f.gap(),()->{immune.discard();f.fire(immune);check(h,WeaponStatsForAll.progress(f.p)==0,"Paid miss cannot collect");
            for(int i=0;i<30;i++){f.hud(false);WeaponStatsForAll.capture(f.p);WeaponStatsForAll.remaining(f.p);}
            check(h,WeaponStatsForAll.progress(f.p)==0&&f.remaining()==0,"Reads/captures do not invent hit credit");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=120,environment=ENV)
    public void originalStowAndReloadPreserveClockAndSnapshotFasterReload(GameTestHelper h){
        var f=new Fixture(h);f.three(()->{
            int earned=f.remaining();f.stow();check(h,f.remaining()==0&&WeaponStatsForAll.ownedRemaining(f.p,f.gun)==earned,"Held-only HUD, equipped original clock retained");f.hud(false);
            h.runAfterDelay(8,()->{f.restore();check(h,f.remaining()==earned-8,"No pause/refresh while stowed");f.hud(true);
                h.runAfterDelay(20,()->{int before=f.remaining();int fast=StatsForAllProfile.reloadTicks(f.entry,35,.95);
                    check(h,fast<f.profile.reloadTicks()&&WeaponRuntime.reload(f.p),"Real sourced35stat/.95 faster reload accepted");
                    check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==fast,"Accepted reload snapshots sourced duration");
                    check(h,f.remaining()==before,"Reload did not consume/refresh active window");
                    h.runAfterDelay(fast+2,()->{check(h,!WeaponRuntime.reloading(f.p)&&WeaponItems.magazine(f.gun,f.profile).rounds()==f.profile.magazine(),"Actual ammo credit/full recovery");h.succeed();});
                });
            });
        });
    }
    @GameTest(structure=FLOOR,maxTicks=300,environment=ENV)
    public void acceptedReloadKeepsItsSnapshotAfterBuffExpiresMidRecovery(GameTestHelper h){
        var f=new Fixture(h);f.three(()->h.runAfterDelay(190,()->{
            check(h,f.remaining()==10,"Exact near-expiry window");int fast=StatsForAllProfile.reloadTicks(f.entry,35,.95);
            check(h,fast>10&&WeaponRuntime.reload(f.p),"Actual fast reload extends beyond buff expiry");
            check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==fast,"Sourced duration captured");
            h.runAfterDelay(11,()->{check(h,f.remaining()==0&&WeaponRuntime.reloading(f.p),"Buff expired during real reload");
                check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==fast,"No in-flight duration extension on expiry");f.hud(false);});
            h.runAfterDelay(fast+2,()->{check(h,!WeaponRuntime.reloading(f.p)&&WeaponItems.magazine(f.gun,f.profile).rounds()==17,"Real primary refill completes at snapshotted speed");h.succeed();});
        }));
    }
    @GameTest(structure="destiny-test:w109_arena",maxTicks=80,environment=ENV)
    public void activeRangeBonusActuallyReducesPaidLongDistanceFalloff(GameTestHelper h){
        var f=new Fixture(h,"ammit_ar2");
        var baseCurve=WeaponBallistics.of(f.entry);var activeCurve=StatsForAllProfile.ballistics(f.entry);
        double[] distance={0};
        java.util.function.Supplier<Float> longShot=()->{
            var target=f.target(30);
            f.p.setYRot(-90);f.p.setYHeadRot(-90);f.p.setXRot(0);WeaponAiming.cleanup(f.p);WeaponAiming.tick(f.p);
            check(h,WeaponAiming.progress(f.p)==0,"Both compared shots use the original hip-fire falloff contract");
            f.p.getRandom().setSeed(0x5DEECE66DL);
            var from=f.p.getEyePosition();var ray=WeaponAiming.direction(f.p);
            var hit=target.getBoundingBox().inflate(.03).clip(from,from.add(ray.scale(40))).orElseThrow();
            check(h,!WeaponPrecision.critical(target,from,hit,baseCurve.precision()),"Seeded long-distance ray hits body, not a random precision region");
            check(h,f.p.level().clip(new net.minecraft.world.level.ClipContext(from,hit,net.minecraft.world.level.ClipContext.Block.COLLIDER,net.minecraft.world.level.ClipContext.Fluid.NONE,f.p)).getType()==net.minecraft.world.phys.HitResult.Type.MISS,"Both paid rays have an unobstructed loaded corridor");
            distance[0]=from.distanceTo(hit);
            return f.fire(target); // Replays the same seed after resetting aim; no injected hit credit.
        };
        float baseline=longShot.get();double baselineDistance=distance[0];
        check(h,baseline>0,"Actual unbuffed long-distance body loss");
        check(h,baselineDistance>activeCurve.start()&&baselineDistance<baseCurve.end(),"Original target lies within both sloped falloff intervals");
        check(h,Math.abs(baseline-baseCurve.damage(f.profile.damage(),baselineDistance,false))<.001,"Unbuffed actual body loss follows its original curve");
        // Register all three deadlines before callbacks run; preserve the original 12/24/36-tick cadence.
        h.runAfterDelay(f.gap(),()->check(h,f.fire(f.target())>0,"Second distinct enemy receives real paid damage"));
        h.runAfterDelay(2*f.gap(),()->{
            check(h,f.fire(f.target())>0,"Third distinct enemy receives real paid damage");
            check(h,f.remaining()==200,"Actual three different enemies activate");
        });
        h.runAfterDelay(3*f.gap(),()->{
            float improved=longShot.get();
            check(h,Math.abs(distance[0]-baselineDistance)<.000001,"Both paid body hits use the same impact distance");
            check(h,improved>baseline+.01,"Next paid long-distance shot uses extended falloff curve, not merely a query; baseline="+baseline+" improved="+improved+" distance="+distance[0]);
            check(h,Math.abs(improved-activeCurve.damage(f.profile.damage(),distance[0],false))<.001,"Buffed actual body loss follows +10 Range then 1.05 falloff, with no raw damage bonus");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void copySameTickEditRuntimeAndOwnerCleanupInvalidateCredit(GameTestHelper h){
        var f=new Fixture(h);f.fire(f.target());var token=WeaponStatsForAll.capture(f.p);int slot=f.p.getInventory().getSelectedSlot();
        f.p.getInventory().setItem(slot,f.gun.copy());WeaponRuntime.tickPlayer(f.p);WeaponStatsForAll.confirmed(f.p,token,f.target(),1);
        check(h,WeaponStatsForAll.progress(f.p)==0,"Copied NBT cannot inherit old source credit");
        f.p.getInventory().setItem(slot,f.gun);WeaponRuntime.tickPlayer(f.p);var edit=WeaponStatsForAll.capture(f.p);
        WeaponPerks.clear(f.gun);WeaponPerks.select(f.gun,ID);WeaponStatsForAll.confirmed(f.p,edit,f.target(),1);
        check(h,WeaponStatsForAll.progress(f.p)==0,"Same-tick edit invalidates session token");
        var runtime=WeaponStatsForAll.capture(f.p);Guardians.forget(f.p);Guardians.runtime(f.p);WeaponStatsForAll.confirmed(f.p,runtime,f.target(),1);
        check(h,WeaponStatsForAll.progress(f.p)==0,"Guardian runtime replacement invalidates");
        var cleanup=WeaponStatsForAll.capture(f.p);WeaponRuntime.cleanup(f.p);WeaponStatsForAll.confirmed(f.p,cleanup,f.target(),1);
        check(h,WeaponStatsForAll.progress(f.p)==0&&f.remaining()==0,"Cleanup retires all epochs");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=360,environment=ENV)
    public void retrofitFrenzyAndStatsForAllComposeBeforeStatCapAndSingleCeil(GameTestHelper h){
        var f=new Fixture(h,"retrofit_escapade");check(h,WeaponPerks.select(f.gun,FrenzyProfile.ID),"Actual distinct socketFrenzy4");
        check(h,WeaponPerks.selected(f.gun,ID).isPresent(),"Stats for All3 remains selected");
        Runnable combat=()->{var t=f.target();Combat.damage(f.p.level(),f.p,t,1,Element.VOID,AmmoGeneration.ABILITY);
            check(h,t.getHealth()==999,"Real combat witness loses1HP; selected="+WeaponPerks.selected(f.gun,FrenzyProfile.ID));
            System.out.println("W176_COMBO tick="+h.getTick()+" server="+f.p.level().getServer().getTickCount()+" combat="+WeaponFrenzy.combatTicks(f.p)+" frenzy="+WeaponFrenzy.remaining(f.p)+" selected="+WeaponPerks.selected(f.gun,FrenzyProfile.ID));};
        combat.run();
        // GameTestHelper schedules by Runnable identity: reusing combat overwrites earlier entries.
        for(int tick:new int[]{80,160,230})h.runAfterDelay(tick,new Runnable(){public void run(){combat.run();}});
        h.runAfterDelay(242,()->{check(h,WeaponFrenzy.remaining(f.p)>0,"Actual combat primes Frenzy; combat="+WeaponFrenzy.combatTicks(f.p)+" selected="+WeaponPerks.selected(f.gun,FrenzyProfile.ID));f.three(()->{
            check(h,f.remaining()==200&&WeaponFrenzy.remaining(f.p)>0,"Both exact sockets active after paid hits");
            int expected=StatsForAllProfile.reloadTicks(f.entry,135,.95);
            check(h,WeaponRuntime.reload(f.p),"Actual combined reload");
            check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==expected,"35+100clamp then.95scalar before one ceil");
            check(h,WeaponStatsForAll.adsTicks(f.p,f.entry,99,true)==StatsForAllProfile.adsTicks(f.entry,135,false),"CombinedADS cannot overwrite stat100 with35");
            h.succeed();
        });});
    }
    @GameTest(structure="destiny-test:w78_floor",maxTicks=90,environment=ENV)
    public void oneRealPaidHeavyWaveCanCountThreeActualDistinctEnemies(GameTestHelper h){
        // Same explicit raised deck/flight geometry as W78; witnesses cannot intercept launch.
        for(int x=0;x<48;x++)for(int z=0;z<32;z++)h.setBlock(x,3,z,net.minecraft.world.level.block.Blocks.STONE);
        var f=new Fixture(h,"dimensional_hypotrochoid");f.p.setPos(h.absoluteVec(new Vec3(3,4,16)));
        f.p.setYRot(-90);f.p.setYHeadRot(-90);f.p.setXRot(35);f.p.setOnGround(true);
        for(double x:new double[]{8,11,14}){
            var t=h.spawn(EntityTypes.HUSK,new Vec3(x,4,16));f.targets.add(t);t.setNoAi(true);t.setNoGravity(true);
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(1000);
        }
        WeaponAiming.cleanup(f.p);WeaponAiming.tick(f.p);int before=WeaponItems.magazine(f.gun,f.profile).rounds();
        check(h,WeaponRuntime.beginUse(f.p),"Actual paid downward heavy grenade");WeaponRuntime.releaseUse(f.p,f.gun);
        check(h,WeaponItems.magazine(f.gun,f.profile).rounds()==before-1,"Only one cartridge funded all contacts");
        h.succeedWhen(()->{check(h,f.targets.stream().allMatch(t->t.getHealth()<1000),"Real server wave hurt all three witnesses");
            check(h,f.remaining()>0&&f.remaining()<=200,"Original paid wave token credits three distinct enemies");f.hud(true);});
    }
    @GameTest(structure=FLOOR,maxTicks=10,environment=ENV)
    public void exactFourOptionalBaseSocketsAndNoFamilyWideOrEnhancedSelection(GameTestHelper h){
        var ids=Set.of("ammit_ar2","aishas_embrace","dimensional_hypotrochoid","retrofit_escapade");int count=0;
        for(var e:WeaponCatalog.all()){var stack=WeaponItems.create(e);check(h,WeaponPerks.selected(stack,ID).isEmpty(),"No default trait");
            check(h,WeaponPerks.select(stack,ID)==ids.contains(e.id()),"Exact selected65membership:"+e.id());if(ids.contains(e.id()))count++;}
        check(h,count==4,"Only four official base pools");
        var explosive=WeaponCatalog.find("dimensional_hypotrochoid").orElseThrow();check(h,StatsForAllProfile.ballistics(explosive).equals(WeaponBallistics.of(explosive)),"Range-independent explosive sentinel unchanged; no invented radius/travel buff");
        h.succeed();
    }
}
