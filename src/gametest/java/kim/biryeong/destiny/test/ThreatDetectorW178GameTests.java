package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

/** Real loaded enemies/paid shots/server state. No native input or framebuffer claim. */
public final class ThreatDetectorW178GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    /** Production left-click ADS; does not bypass the three-tick toggle debounce. */
    private static void ads(net.minecraft.server.level.ServerPlayer p, boolean requested) {
        if (WeaponAiming.requested(p) != requested) kim.biryeong.destiny.input.InputRouter.onPunch(p);
    }
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="threat_detector";
    static final AtomicInteger PLANE=new AtomicInteger();
    static void check(GameTestHelper h,boolean ok,String why){h.assertTrue(ok,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final WeaponCatalog.Entry entry;
        final WeaponProfile profile;final ItemStack gun;final List<LivingEntity> mobs=new ArrayList<>();
        Fixture(GameTestHelper h){this(h,"seventh_seraph_officer_revolver");}
        Fixture(GameTestHelper h,String id){
            this.h=h;entry=WeaponCatalog.find(id).orElseThrow();profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W178_"+UUID.randomUUID().toString().substring(0,8));
            // Parallel proximity tests must not count one another's witnesses. NoGravity allows
            // separated vertical air planes above the disposable GameTest level, not a user world.
            p.setPos(p.position().add(0,64+40*PLANE.getAndIncrement(),0));p.setNoGravity(true);p.setOnGround(true);
            Guardians.runtime(p);p.setAttached(WeaponLoadout.ENABLED,true);gun=WeaponItems.create(entry);
            check(h,WeaponPerks.select(gun,ID),"Exact optional official Threat Detector socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,Math.min(3,profile.magazine()-1),200));
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            tick();h.onEachTick(()->tick());
            TestCleanup.register(h,()->{mobs.forEach(LivingEntity::discard);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void tick(){WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);}
        Husk enemy(double x,double y,double z){var e=h.spawn(EntityTypes.HUSK,new Vec3(3,1,3));e.setPos(p.position().add(x,y,z));e.setNoAi(true);e.setNoGravity(true);e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);e.getAttribute(Attributes.ARMOR).setBaseValue(0);e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);e.setHealth(1000);mobs.add(e);return e;}
        void scan(){WeaponThreatDetector.update(p);}
        int stacks(){return WeaponThreatDetector.stacks(p);}
        void hud(int expected){CombatHud.update(p);check(h,DisplayHud.getHuds(p).keySet().stream().filter(x->x.startsWith("destiny:hud_perk_threat_detector_")).count()==(expected==0?0:4),"Observed proximity gives count-only four nodes; no timer");}
        float fire(Husk e){p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);int ammo=WeaponItems.magazine(gun,profile).rounds();float before=e.getHealth();check(h,beginUse(p),"Actual trigger accepted");WeaponRuntime.releaseUse(p,gun);check(h,WeaponItems.magazine(gun,profile).rounds()==ammo-1,"Actual paid shot");return before-e.getHealth();}
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void loadedEnemySphereDrivesZeroOneTwoCapAndImmediateRemovalHud(GameTestHelper h){
        var f=new Fixture(h);check(h,f.stacks()==0,"Empty loaded scene is tier0");f.hud(0);
        var a=f.enemy(15.0001,0,0);f.scan();check(h,f.stacks()==0,"Outside exact fifteen-metre footpoint sphere");
        a.setPos(f.p.position().add(15,0,0));f.scan();check(h,f.stacks()==1&&WeaponThreatDetector.stabilityBonus(f.p)==15,"Boundary single enemy tier1");f.hud(1);
        var b=f.enemy(0,15,0);f.scan();check(h,f.stacks()==2&&WeaponThreatDetector.stabilityBonus(f.p)==40,"3D vertical boundary second enemy tier2");f.hud(2);
        var c=f.enemy(5,0,5);f.scan();check(h,f.stacks()==2,"Three enemies remain capped at2");
        a.discard();b.discard();c.discard();f.scan();check(h,f.stacks()==0,"No invented linger or timer");f.hud(0);h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void deadAlliedTamedDecorativeAndPlayerEntitiesCannotGrantProximity(GameTestHelper h){
        var f=new Fixture(h);var ally=f.enemy(2,0,0);var board=f.p.level().getScoreboard();var team=board.addPlayerTeam("td"+UUID.randomUUID().toString().substring(0,8));board.addPlayerToTeam(f.p.getScoreboardName(),team);board.addPlayerToTeam(ally.getScoreboardName(),team);
        TestCleanup.register(h,()->board.removePlayerTeam(team));
        var dead=f.enemy(3,0,0);dead.setHealth(0);
        var stand=h.spawn(EntityTypes.ARMOR_STAND,new Vec3(3,1,3));stand.setPos(f.p.position().add(4,0,0));stand.setNoGravity(true);f.mobs.add(stand);
        var wolf=h.spawn(EntityTypes.WOLF,new Vec3(3,1,3));wolf.setPos(f.p.position().add(4,0,0));wolf.setNoAi(true);wolf.setNoGravity(true);wolf.setTame(true,false);f.mobs.add(wolf);
        var peer=TestPlayers.create(h,new Vec3(3,1,3),0,0);peer.setPos(f.p.position().add(1,0,0));f.p.level().players().add(peer);TestCleanup.register(h,()->{f.p.level().players().remove(peer);TestPlayers.remove(peer);});
        f.scan();check(h,f.stacks()==0,"PvE excludes allies/dead/tamed/decorations/players");f.hud(0);
        f.enemy(5,0,5);f.scan();check(h,f.stacks()==1,"One valid hostile alongside excluded entities");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void actualPaidShotUsesFortyStabilityWithoutDamageOrAccuracyScalarInvention(GameTestHelper h){
        var f=new Fixture(h);var target=f.enemy(6,.8,0);WeaponPerks.clear(f.gun);float baseline=f.fire(target);
        h.startSequence().thenIdle(Math.max(15,(int)Math.ceil(f.profile.cadenceTicks())+2)).thenExecute(()->{
            check(h,WeaponPerks.select(f.gun,ID),"Restore same optional socket");f.enemy(-5,0,0);f.scan();check(h,f.stacks()==2,"Two actual nearby enemies");
            float damage=f.fire(target);check(h,baseline>0&&Math.abs(damage-baseline)<.001,"No raw damage bonus");
            var aim=WeaponAimProfile.of(f.entry);check(h,Math.abs(f.p.getXRot()+RapidHitStability.kick(aim,40))<.0001,"Actual paid recoil uses stability+40");
            check(h,Math.abs(WeaponAiming.bloom(f.p)-RapidHitStability.bloom(aim,40))<.00001,"Actual bloom uses stability only, no invented accuracy scalar");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=100,environment=ENV)
    public void acceptedReloadSnapshotsRealTierAndDoesNotRetimeAfterEnemyLeaves(GameTestHelper h){
        var f=new Fixture(h);f.enemy(-4,0,0);f.enemy(-5,0,0);f.scan();
        int expected=ThreatDetectorProfile.reloadTicks(f.entry,60,1);
        check(h,WeaponRuntime.reload(f.p),"Actual reload accepted");check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==expected,"Tier2 reload stat is accepted pre-quantization");
        f.mobs.forEach(e->e.setPos(f.p.position().add(50,0,0)));f.scan();check(h,f.stacks()==0,"Proximity tier disappears");
        h.startSequence().thenIdle(1).thenExecute(()->check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==expected,"In-flight reload snapshot remains fixed"));
        h.startSequence().thenIdle(expected+2).thenExecute(()->{check(h,!WeaponRuntime.reloading(f.p)&&WeaponItems.magazine(f.gun,f.profile).rounds()==f.profile.magazine(),"Original funded magazine granularity/completion preserved");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=50,environment=ENV)
    public void actualAdsAndOutgoingStowUseHandlingWithoutInventedAdsMultiplier(GameTestHelper h){
        var f=new Fixture(h);f.enemy(-4,0,0);f.enemy(-5,0,0);f.scan();
        int enter=ThreatDetectorProfile.adsTicks(f.entry,100,false),exit=enter;
        check(h,WeaponThreatDetector.adsTicks(f.p,f.entry,999,true)==enter&&WeaponThreatDetector.adsTicks(f.p,f.entry,999,false)==exit,"Handling-derived entry and exit; no .81 ADS scalar");
        WeaponAiming.cleanup(f.p);ads(f.p,true);WeaponAiming.tick(f.p);
        check(h,Math.abs(WeaponAiming.progress(f.p)-1f/enter)<.0001,"Real ADS tick uses new effective stat");
        h.startSequence().thenIdle(20).thenExecute(()->{check(h,WeaponAiming.progress(f.p)==1,"Actual elapsed ticks finish ADS");ads(f.p,false);});
        h.startSequence().thenIdle(21).thenExecute(()->{WeaponAiming.tick(f.p);check(h,Math.abs(WeaponAiming.progress(f.p)-(1f-1f/exit))<.0001,"Actual exit tick uses handling, not ready/stow scalar; progress="+WeaponAiming.progress(f.p)+" expected="+(1f-1f/exit)+" exit="+exit+" stacks="+f.stacks()+" pugilist="+WeaponPugilist.handlingBonus(f.p));
            int stow=ThreatDetectorProfile.handlingTicks(f.entry,100,.81,false);WeaponRuntime.selectedSlotChanging(f.p,7);f.p.getInventory().setSelectedSlot(7);
            check(h,WeaponHandling.remaining(f.p)==0,"Readiness getter rejects now-nonweapon slot");
            check(h,WeaponThreatDetector.stacks(f.p)==0,"Stowing removes proximity immediately");
            // During selection the old weapon's STOW was accepted; returning it cannot bypass that deadline.
            f.p.getInventory().setSelectedSlot(WeaponCharacteristics.of(f.entry).slot().hotbar());
            WeaponHandling.update(f.p);
            check(h,WeaponHandling.remaining(f.p)==stow+WeaponHandlingProfile.of(f.entry).readyTicks(),"Actual outgoing-stow snapshot survives a same-tick reselect; incoming ready is unbuffed after stow");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void gettersCannotTransferOldSourceAcrossCopyEditStowRuntimeOrCleanup(GameTestHelper h){
        var f=new Fixture(h);f.enemy(-4,0,0);f.enemy(-5,0,0);f.scan();int slot=f.p.getInventory().getSelectedSlot();check(h,f.stacks()==2,"Original source observed");
        f.p.getInventory().setItem(slot,f.gun.copy());check(h,f.stacks()==0,"Copy cannot borrow old source before a real scan");f.scan();check(h,f.stacks()==2,"New copy may legitimately observe current proximity on update");
        f.p.getInventory().setItem(slot,f.gun);WeaponThreatDetector.edited(f.gun);check(h,f.stacks()==0,"Edit retires original epoch");f.scan();check(h,f.stacks()==2,"Actual held update can observe afresh");
        Guardians.forget(f.p);Guardians.runtime(f.p);check(h,f.stacks()==0,"Replaced GuardianRuntime invalidates old binding");f.scan();check(h,f.stacks()==2,"New Guardian context can observe anew");
        WeaponThreatDetector.cleanup(f.p);check(h,f.stacks()==0,"Cleanup does not let getters rearm");f.scan();WeaponThreatDetector.stowing(f.p,f.gun);check(h,f.stacks()==0,"Accepted stow clears even away/back same tick");f.hud(0);h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=10,environment=ENV)
    public void allSixtyFiveWeaponsExposeOnlySeventeenOptionalOfficialSockets(GameTestHelper h){
        var allowed=ThreatDetectorProfile.rolls().stream().map(WeaponPerks.Roll::id).collect(java.util.stream.Collectors.toSet());check(h,allowed.size()==17,"Exact official selected17");
        for(var e:WeaponCatalog.all()){var s=WeaponItems.create(e);check(h,WeaponPerks.selected(s,ID).isEmpty(),"No fabricated default");check(h,WeaponPerks.select(s,ID)==allowed.contains(e.id()),"Exact selected weapon/socket:"+e.id());}h.succeed();
    }
}
