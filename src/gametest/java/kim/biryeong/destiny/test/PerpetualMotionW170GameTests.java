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
/** Server-position fixtures exercise real runtime/HUD/paid reload/handling. Not native movement evidence. */
public final class PerpetualMotionW170GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    /** Production left-click ADS; does not bypass the three-tick toggle debounce. */
    private static void ads(net.minecraft.server.level.ServerPlayer p, boolean requested) {
        if (WeaponAiming.requested(p) != requested) kim.biryeong.destiny.input.InputRouter.onPunch(p);
    }
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="perpetual_motion",PREFIX="destiny:hud_perk_perpetual_motion_";
    static void check(GameTestHelper h,boolean yes,String why){h.assertTrue(yes,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final ItemStack gun;final WeaponCatalog.Entry entry;final WeaponProfile profile;
        double movement=.12;boolean sampling=true,batched=false;int samples;
        Fixture(GameTestHelper h){this(h,"aishas_embrace");}
        Fixture(GameTestHelper h,String id) {
            this.h=h;entry=WeaponCatalog.find(id).orElseThrow();profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W170_"+UUID.randomUUID().toString().substring(0,8));
            p.setNoGravity(true);p.setOnGround(true);gun=WeaponItems.create(entry);
            check(h,WeaponPerks.select(gun,ID),"Exact base motion socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),200));
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            p.setAttached(WeaponLoadout.ENABLED,true);WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
            h.onEachTick(()->{if(sampling){double d=batched?(++samples%3==0?movement*3:0):movement;p.setPos(p.position().add(d,0,0));WeaponRuntime.tickPlayer(p);}TestPlayers.drain(p);});
            TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        int count(){return WeaponPerpetualMotion.stacks(p);}
    }
    static void hud(GameTestHelper h,ServerPlayer p,int stacks) {
        CombatHud.update(p);var nodes=DisplayHud.getHuds(p);
        check(h,nodes.keySet().stream().filter(s->s.startsWith(PREFIX)).count()==(stacks==0?0:4),"Actual count-only row; no fabricated timer");
        if(stacks>0){var count=nodes.get(PREFIX+"count");check(h,count instanceof ItemDisplayHud&&Identifier.parse("destiny:gui/hud/ammo_digit_"+stacks).equals(((ItemDisplayHud)count).getItem().get(DataComponents.ITEM_MODEL)),"Real x"+stacks+" digit");}
    }
    @GameTest(structure=FLOOR,maxTicks=240,environment=ENV)
    public void actualPositionReachesTwoTiersAndStationaryRemovesCountOnlyHud(GameTestHelper h) {
        var f=new Fixture(h);
        h.startSequence().thenIdle(38).thenExecute(()->check(h,f.count()==0,"Before2seconds no buff"));
        h.startSequence().thenIdle(42).thenExecute(()->{check(h,f.count()==1,"After40movingticks x1");hud(h,f.p,1);});
        h.startSequence().thenIdle(198).thenExecute(()->check(h,f.count()==1,"Before10seconds stillx1"));
        h.startSequence().thenIdle(202).thenExecute(()->{check(h,f.count()==2,"After200movingticks x2");hud(h,f.p,2);f.movement=0;});
        h.startSequence().thenIdle(209).thenExecute(()->check(h,f.count()==2,"Shortstopwithin10tickgrace"));
        h.startSequence().thenIdle(215).thenExecute(()->{check(h,f.count()==0,"Stationary10ticks clears");hud(h,f.p,0);h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=230,environment=ENV)
    public void batchedActualServerPositionsStillReachSecondTierAndStopOnTime(GameTestHelper h) {
        var f=new Fixture(h);f.batched=true;f.movement=.216;
        h.startSequence().thenIdle(207).thenExecute(()->{check(h,f.count()==2,"Three-tick real position batches earn x2 without packet cadence slowdown");hud(h,f.p,2);f.movement=0;});
        h.startSequence().thenIdle(220).thenExecute(()->{check(h,f.count()==0,"Raw stationary10tick bound despite smoothing window");hud(h,f.p,0);h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=230,environment=ENV)
    public void velocityAndSubthresholdActualTravelCannotFabricateStacks(GameTestHelper h) {
        var f=new Fixture(h);f.movement=.099;f.p.setDeltaMovement(new Vec3(1,0,0));
        h.startSequence().thenIdle(205).thenExecute(()->{check(h,f.count()==0&&WeaponPerpetualMotion.movingTicks(f.p)==0,"1.98m/s server displacement belowthreshold despitevelocity");hud(h,f.p,0);h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=245,environment=ENV)
    public void actualOriginalStackAccruesWhileStowedAndSpeedsIncomingReady(GameTestHelper h) {
        var f=new Fixture(h);var backpack=f.gun.copy();f.p.getInventory().setItem(9,backpack);var ace=WeaponCatalog.find("ace_of_spades").orElseThrow();f.p.getInventory().setItem(0,WeaponItems.create(ace));f.p.getInventory().setSelectedSlot(0);
        h.startSequence().thenIdle(202).thenExecute(()->{
            check(h,f.count()==0&&WeaponPerpetualMotion.ownedStacks(f.p,f.gun)==2,"Originalinventorysource accruesstowed nototherweapon");check(h,WeaponPerpetualMotion.ownedStacks(f.p,backpack)==0,"Backpackcopyisnotequippedstow");hud(h,f.p,0);
            f.p.getInventory().setSelectedSlot(WeaponCharacteristics.of(f.entry).slot().hotbar());WeaponHandling.update(f.p);
            int expected=WeaponHandlingProfile.of(ace).stowTicks()+PerpetualMotionProfile.timing(f.entry,2).readyTicks();
            check(h,WeaponHandling.remaining(f.p)==expected,"Real switch snapshots boosted incoming ready and unaffected outgoingAce");
        });
        h.startSequence().thenIdle(235).thenExecute(()->{check(h,f.count()==2,"Re-equipped same source retains movingbuff");hud(h,f.p,2);h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=115,environment=ENV)
    public void exactCopyAndSuccessfulEditsCannotInheritSourceProgress(GameTestHelper h) {
        var f=new Fixture(h);
        h.startSequence().thenIdle(42).thenExecute(()->{
            check(h,f.count()==1,"Earnedfirsttier");var copy=f.gun.copy();f.p.getInventory().setItem(WeaponCharacteristics.of(f.entry).slot().hotbar(),copy);
            check(h,f.count()==0&&WeaponPerpetualMotion.ownedStacks(f.p,f.gun)==0,"CopiedNBTnoidentityprogress;oldunpossessedinert");
        });
        h.startSequence().thenIdle(88).thenExecute(()->{
            check(h,f.count()==1,"Copy must earn its own40movingticks");var stack=f.p.getMainHandItem();
            check(h,WeaponPerks.clear(stack)&&WeaponPerks.select(stack,ID),"Successful exact clear/reselect");
            check(h,f.count()==0,"Same-tickedit invalidates sourceclock");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void teleportAndExplicitCleanupRevokeWithoutHudMutation(GameTestHelper h) {
        var f=new Fixture(h);
        h.startSequence().thenIdle(42).thenExecute(()->{check(h,f.count()==1,"Earnedfirsttier");f.p.setPos(f.p.position().add(10,0,0));});
        h.startSequence().thenIdle(44).thenExecute(()->{check(h,f.count()==0,"Localteleportguardresets");for(int i=0;i<100;i++)WeaponPerpetualMotion.stacks(f.p);check(h,f.count()==0,"Queriesdonotadvance");WeaponRuntime.cleanup(f.p);check(h,f.count()==0,"Cleanup removesmotionclock");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=145,environment=ENV)
    public void realSpecialReloadUsesMotionSnapshotDespiteStationaryExpiry(GameTestHelper h) {
        var f=new Fixture(h,"retraced_path");WeaponItems.save(f.gun,new WeaponMagazine(f.profile,1,200));
        h.startSequence().thenIdle(42).thenExecute(()->{
            check(h,f.count()==1,"Earnedfirsttier");int duration=PerpetualMotionProfile.timing(f.entry,1).reloadTicks();
            check(h,WeaponRuntime.reload(f.p),"Actualfundedspecialreload");check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==duration,"Realreloadsnapshotboosted");f.movement=0;
            h.startSequence().thenIdle(13).thenExecute(()->{check(h,f.count()==0,"Buffexpiredwhilestationary");check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==duration,"No retime after buffremoved");});
            h.startSequence().thenIdle(duration+3).thenExecute(()->{var a=WeaponItems.magazine(f.gun,f.profile);check(h,a.rounds()==f.profile.magazine()&&a.reserve()==201-f.profile.magazine(),"Realpaidreservefundedreload only");check(h,!WeaponRuntime.reloading(f.p),"Reloadfinished");h.succeed();});
        });
    }
    @GameTest(structure=FLOOR,maxTicks=235,environment=ENV)
    public void paidEmissionGetsSourcedStabilityAndActualAdsTransition(GameTestHelper h) {
        var f=new Fixture(h);
        h.startSequence().thenIdle(202).thenExecute(()->{
            check(h,f.count()==2&&WeaponPerpetualMotion.stabilityBonus(f.p)==20,"Sourcedtier2stability");f.p.setXRot(0);WeaponAiming.cleanup(f.p);WeaponAiming.tick(f.p);
            int before=WeaponItems.magazine(f.gun,f.profile).rounds();float kick=RapidHitStability.kick(WeaponAimProfile.of(f.entry),20);
            check(h,beginUse(f.p),"Actualpaiduseaccepted");WeaponRuntime.releaseUse(f.p,f.gun);
            check(h,WeaponItems.magazine(f.gun,f.profile).rounds()==before-1,"Onepaidemission");check(h,Math.abs(f.p.getXRot()+kick)<1e-5,"Actualrecoiluses20stabilitynotbase");
            check(h,WeaponPerpetualMotion.adsTicks(f.p,f.entry,WeaponAimProfile.of(f.entry).transitionTicks())==PerpetualMotionProfile.timing(f.entry,2).adsTicks(),"Actualadstimingadapter");
            ads(f.p,true);
        });
        h.startSequence().thenIdle(225).thenExecute(()->{check(h,WeaponAiming.progress(f.p)>=.99f,"ActualADSprogressreachesscope");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=10,environment=ENV)
    public void exactTwoWeaponsOnly(GameTestHelper h) {
        int count=0;for(var e:WeaponCatalog.all()){var s=WeaponItems.create(e);boolean expected=Set.of("aishas_embrace","retraced_path").contains(e.id());check(h,WeaponPerks.select(s,ID)==expected,"Exactmotioneligibility"+e.id());if(expected)count++;}
        check(h,count==2,"Only2baseofficialselectedsockets");h.succeed();
    }
}
