package kim.biryeong.destiny.test;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.combat.*;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Actual paid geometry/status tests. No positive confirmation-token injection or native-input claims.
 * Persistence through stow, whole-window refresh and reload snapshot are declared local policies.
 */
public final class RapidHitW169GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    private static final String FLOOR="destiny-test:floor", ENV="destiny-test:w90_isolated";
    private static final String RH="rapid_hit", DUKE="duke_mk_44", PREFIX="destiny:hud_perk_rapid_hit_";
    private static void check(GameTestHelper h,boolean ok,String message){h.assertTrue(ok,Component.literal(message));}
    private static final class Fixture {
        final GameTestHelper h; final ServerPlayer p; final ItemStack gun;
        final WeaponCatalog.Entry entry;
        final WeaponProfile profile;
        final List<Husk> targets=new ArrayList<>();
        boolean headTarget;
        Fixture(GameTestHelper h) {this(h,DUKE);}
        Fixture(GameTestHelper h,String id) {
            entry=WeaponCatalog.find(id).orElseThrow();profile=WeaponProfile.forEntry(entry);
            this.h=h;p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W169_"+UUID.randomUUID().toString().substring(0,8));
            p.setAttached(WeaponLoadout.ENABLED,true);p.setNoGravity(true);p.setOnGround(true);
            gun=WeaponItems.create(entry);check(h,WeaponPerks.select(gun,RH),"Exact official source socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),0));
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
            TestCleanup.register(h,()->{targets.forEach(t->{Statuses.forget(t);t.discard();});WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
            h.onEachTick(()->TestPlayers.drain(p));
        }
        WeaponMagazine ammo(){return WeaponItems.magazine(gun,profile);}
        Husk target(boolean head){
            headTarget=head;
            targets.forEach(t->{Statuses.forget(t);t.discard();});targets.clear();
            var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,head?1:1.8,6));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.setPersistenceRequired();t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(1000);
            var b=t.getBoundingBox();double eye=p.getEyeY();check(h,head?eye>=b.maxY-b.getYsize()*.25&&eye<b.maxY:eye>b.minY&&eye<b.maxY-b.getYsize()*.25,"Actual horizontal head/body geometry");
            return t;
        }
        void fire(){
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            if(!targets.isEmpty()&&!targets.getFirst().isRemoved()) {
                var target=targets.getFirst();var from=p.getEyePosition();
                p.getRandom().setSeed(0x5DEECE66DL);
                var ray=WeaponAiming.direction(p);
                var hit=target.getBoundingBox().inflate(.03).clip(from,from.add(ray.scale(16))).orElseThrow();
                check(h,WeaponPrecision.critical(target,from,hit,WeaponBallistics.of(entry).precision())==headTarget,"Seeded preflight crosses the intended precision/body region");
            }
            // beginUse replays the exact preflight seed for the paid production emission.
            var before=ammo();check(h,beginUse(p),"Paid trigger accepted");WeaponRuntime.releaseUse(p,gun);
            check(h,ammo().rounds()==before.rounds()-1&&ammo().reserve()==before.reserve(),"Exactly one paid cartridge, no generated ammo");
        }
        void hit(boolean head,boolean weakened){
            var t=target(head);if(weakened)Statuses.apply(t,Keyword.WEAKENED,80);fire();
            check(h,t.getHealth()<1000&&t.isAlive(),"Real positive nonfinal damage transaction");
        }
        int gap(){return (int)Math.ceil(profile.cadenceTicks())+2;}
        void chain(int next,int max,Runnable done){
            hit(true,false);state(h,p,Math.min(5,next),40);
            if(next==max)done.run();else h.startSequence().thenIdle(gap()).thenExecute(()->chain(next+1,max,done));
        }
    }
    private static void state(GameTestHelper h,ServerPlayer p,int count,int ticks){
        check(h,WeaponRapidHit.stacks(p)==count&&WeaponRapidHit.remaining(p)==ticks,"RapidHit expected x"+count+"/"+ticks+" got x"+WeaponRapidHit.stacks(p)+"/"+WeaponRapidHit.remaining(p));
    }
    private static void hud(GameTestHelper h,ServerPlayer p,int count,int seconds){
        CombatHud.update(p);long n=DisplayHud.getHuds(p).keySet().stream().filter(s->s.startsWith(PREFIX)).count();
        check(h,n==(count==0?0:8),"Actual row node count");if(count==0)return;
        for(var row:Map.of("label","perk_rapid_hit_w169","count","ammo_digit_"+count,"ones","ammo_digit_"+seconds).entrySet()) {
            var node=DisplayHud.getHud(p,PREFIX+row.getKey());
            check(h,node instanceof ItemDisplayHud&&Identifier.parse("destiny:gui/hud/"+row.getValue()).equals(((ItemDisplayHud)node).getItem().get(DataComponents.ITEM_MODEL)),"Real HUD "+row);
        }
    }

    @GameTest(structure=FLOOR,maxTicks=180,environment=ENV)
    public void paidPrecisionReachesFiveRefreshesCapAndExpiresWithActualHud(GameTestHelper h){
        var f=new Fixture(h);f.chain(1,6,()->{
            check(h,f.ammo().rounds()==f.profile.magazine()-6,"Six paid emissions; no kill needed");hud(h,f.p,5,2);
            check(h,WeaponRapidHit.stabilityBonus(f.p)==25,"Sourced fifth-tier stability");
            check(h,WeaponRapidHit.stability(f.p,f.entry)==Math.min(100,WeaponAimProfile.of(f.entry).stability()+25),"Actual stability cap");
            h.startSequence().thenIdle(39).thenExecute(()->{state(h,f.p,5,1);hud(h,f.p,5,1);});
            h.startSequence().thenIdle(40).thenExecute(()->{state(h,f.p,0,0);hud(h,f.p,0,0);check(h,WeaponRapidHit.stabilityBonus(f.p)==0,"Expired stability returns to base");h.succeed();});
        });
    }
    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void ordinaryBodyCannotProcButActualWeakenedBodyCanAndAbilityDamageCannot(GameTestHelper h){
        var f=new Fixture(h);f.hit(false,false);state(h,f.p,0,0);
        h.startSequence().thenIdle(f.gap()).thenExecute(()->{
            var t=f.target(false);Statuses.apply(t,Keyword.WEAKENED,80);
            Combat.damage(f.p.level(),f.p,t,1,Element.VOID,AmmoGeneration.ABILITY);state(h,f.p,0,0);
            t.damageCooldownTime=0;f.fire();state(h,f.p,1,40);hud(h,f.p,1,2);h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void immuneHeadAndMissConsumeAmmoWithoutGrantingStacks(GameTestHelper h){
        var f=new Fixture(h);var t=f.target(true);t.setPermanentlyInvulnerable(true);f.fire();
        check(h,t.getHealth()==1000,"Actual target rejected damage");state(h,f.p,0,0);
        t.discard();h.startSequence().thenIdle(f.gap()).thenExecute(()->{f.fire();state(h,f.p,0,0);h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=160,environment=ENV)
    public void reloadSnapshotsFifthTierAndExpiryCannotRetimeOrConsumeIt(GameTestHelper h){
        var f=new Fixture(h);f.chain(1,5,()->h.startSequence().thenIdle(35).thenExecute(()->{
            state(h,f.p,5,5);int fast=RapidHitProfile.reload(f.entry,5).firstTicks();
            check(h,fast<f.profile.reloadTicks()&&WeaponRuntime.reload(f.p),"Actual faster reload starts");
            check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==fast,"Live accepted reload snapshots tier5");
            state(h,f.p,5,5);
            for(int i=1;i<=fast+1;i++)h.startSequence().thenIdle(i).thenExecute(()->WeaponRuntime.tickPlayer(f.p));
            h.startSequence().thenIdle(6).thenExecute(()->{state(h,f.p,0,0);check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==fast,"Expired buff cannot retime in-flight reload");});
            h.startSequence().thenIdle(fast+2).thenExecute(()->{check(h,!WeaponRuntime.reloading(f.p)&&f.ammo().rounds()==f.profile.magazine(),"Existing primary reload credit/recovery completed");h.succeed();});
        }));
    }
    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void sameIdentityStowKeepsClockButCopyEditAndRemovedSourceCannotInherit(GameTestHelper h){
        var f=new Fixture(h);f.hit(true,false);var stale=WeaponRapidHit.capture(f.p);state(h,f.p,1,40);
        int slot=f.p.getInventory().getSelectedSlot();f.p.getInventory().setSelectedSlot(7);WeaponRuntime.tickPlayer(f.p);state(h,f.p,0,0);hud(h,f.p,0,0);
        h.startSequence().thenIdle(5).thenExecute(()->{
            f.p.getInventory().setSelectedSlot(slot);WeaponRuntime.tickPlayer(f.p);state(h,f.p,1,35);
            var copy=f.gun.copy();f.p.getInventory().setItem(slot,copy);WeaponRuntime.tickPlayer(f.p);state(h,f.p,0,0);
            WeaponRapidHit.confirmed(f.p,stale,true,true,1);state(h,f.p,0,0);
            f.p.getInventory().setItem(slot,f.gun);WeaponRuntime.tickPlayer(f.p);state(h,f.p,0,0);
            check(h,WeaponPerks.clear(f.gun)&&WeaponPerks.select(f.gun,RH),"Exact clear/reselect has new session identity");
            WeaponRapidHit.confirmed(f.p,stale,true,true,1);state(h,f.p,0,0);h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=15,environment=ENV)
    public void cleanupInvalidatesPaidTokenEvenIfSameStackReturns(GameTestHelper h){
        var f=new Fixture(h);f.hit(true,false);var old=WeaponRapidHit.capture(f.p);WeaponRuntime.cleanup(f.p);
        WeaponRapidHit.confirmed(f.p,old,true,true,1);state(h,f.p,0,0);hud(h,f.p,0,0);h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=15,environment=ENV)
    public void exactElevenOptionalSocketsDoNotBecomeFamilyWideOrDefault(GameTestHelper h){
        var ids=Set.of("duke_mk_44","patron_of_lost_causes","long_arm","allied_demand","lonesome","brass_attacks","biting_winds","bite_of_the_fox","apostate","line_in_the_sand","stormchaser");
        int selected=0;
        for(var e:WeaponCatalog.all()) {
            var item=WeaponItems.create(e);var copy=item.copy();
            check(h,WeaponPerks.selected(item,RH).isEmpty()&&ItemStack.matches(item,copy),"No implicit trait "+e.id());
            check(h,WeaponPerks.select(item,RH)==ids.contains(e.id()),"Exact selected65catalog admission "+e.id());
            if(ids.contains(e.id())){selected++;check(h,WeaponPerks.selected(item,RH).isPresent(),"Exact serialized source socket");}
        }
        check(h,selected==11,"Eleven selected item sockets, no enhanced or exotic expansion");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=160,environment=ENV)
    public void longArmKeepsDistinctFirstIntervalAndTwoRoundInserts(GameTestHelper h){
        var f=new Fixture(h,"long_arm");f.chain(1,5,()->{
            var plan=WeaponRapidHit.plan(f.p,f.entry,f.profile);
            double ratio=RapidHitProfile.reloadMultiplier(f.entry,5);
            check(h,f.profile.firstReloadTicks()==20&&f.profile.reloadTicks()==13&&f.profile.roundsPerInsert()==2,"Existing local Long Arm baseline");
            check(h,plan.firstTicks()==(int)Math.ceil(20*ratio)&&plan.intervalTicks()==(int)Math.ceil(13*ratio)&&plan.roundsPerInsert()==2,"Explicit per-phase ratio adaptation, not whole-magazine timing");
            int before=f.ammo().rounds();check(h,WeaponRuntime.reload(f.p),"Actual incremental reload starts");
            check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==plan.firstTicks(),"Live first phase snapshot");
            for(int i=1;i<=plan.firstTicks()+1;i++)h.startSequence().thenIdle(i).thenExecute(()->WeaponRuntime.tickPlayer(f.p));
            h.startSequence().thenIdle(plan.firstTicks()+1).thenExecute(()->{
                check(h,f.ammo().rounds()==before+2,"Exactly two cartridges inserted in first phase");
                check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==plan.intervalTicks(),"Distinct next insert phase");
                WeaponRuntime.cancelUseForSkill(f.p);h.succeed();
            });
        });
    }
    private static void bow(GameTestHelper h,boolean replaceBeforeImpact){
        var f=new Fixture(h,"biting_winds");var t=f.target(true);
        h.onEachTick(()->WeaponRuntime.tickPlayer(f.p));
        f.p.setYRot(-90);f.p.setXRot(0);WeaponAiming.tick(f.p);
        WeaponCombatItem.INSTANCE.use(h.getLevel(),f.p,net.minecraft.world.InteractionHand.MAIN_HAND);
        check(h,f.p.isUsingItem(),"Actual vanilla bow item use accepted");
        h.startSequence().thenIdle(f.profile.chargeTicks()+1).thenExecute(()->{
            f.p.setYRot(-90);f.p.setXRot(0);f.p.getRandom().setSeed(0x5DEECE66DL);f.p.releaseUsingItem();
            check(h,f.ammo().rounds()==0&&WeaponRuntime.activeProjectiles(f.p)==1,"One paid arrow in flight, no injected hit");
            if(replaceBeforeImpact){
                int slot=f.p.getInventory().getSelectedSlot();f.p.getInventory().setItem(slot,f.gun.copy());WeaponRapidHit.update(f.p);
            }
        });
        h.startSequence().thenIdle(f.profile.chargeTicks()+8).thenExecute(()->{
            check(h,t.getHealth()<1000&&WeaponRuntime.activeProjectiles(f.p)==0,"Real positive arrow contact completed");
            if(replaceBeforeImpact)state(h,f.p,0,0);
            else{
                check(h,WeaponRapidHit.stacks(f.p)==1&&WeaponRapidHit.remaining(f.p)>0,"Paid precision arrow earns source stack");
                var plan=WeaponRapidHit.plan(f.p,f.entry,f.profile);
                check(h,plan.firstTicks()==RapidHitProfile.reload(f.entry,1).firstTicks(),"Bow bonus changes sourced nock plan only");
                check(h,WeaponProfile.forEntry(f.entry).chargeTicks()==f.profile.chargeTicks(),"Bow draw duration is not reload speed");
            }
            h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=100,environment=ENV)
    public void paidPrecisionArrowEarnsBuffWithoutChangingDrawTime(GameTestHelper h){bow(h,false);}
    @GameTest(structure=FLOOR,maxTicks=100,environment=ENV)
    public void realArrowDamageCannotRewardCopiedReplacement(GameTestHelper h){bow(h,true);}
    @GameTest(structure=FLOOR,maxTicks=15,environment=ENV)
    public void deadOwnerCannotKeepOrResurrectOldPaidSession(GameTestHelper h){
        var f=new Fixture(h);f.hit(true,false);var stale=WeaponRapidHit.capture(f.p);
        f.p.setHealth(0);WeaponRapidHit.update(f.p);state(h,f.p,0,0);hud(h,f.p,0,0);
        f.p.setHealth(20);WeaponRapidHit.confirmed(f.p,stale,true,true,1);state(h,f.p,0,0);h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void apostatePrecisionKillCombinesRealDistinctOutlawAndRapidHit(GameTestHelper h){
        var f=new Fixture(h,"apostate");check(h,WeaponPerks.select(f.gun,OutlawProfile.ID),"Apostate distinct Outlaw socket");
        WeaponItems.save(f.gun,new WeaponMagazine(f.profile,f.profile.magazine(),10)); // explicit finite-ammo fixture
        check(h,WeaponPerks.selected(f.gun,RH).isPresent(),"Both base traits selected concurrently");
        var t=f.target(true);t.setHealth(1);f.fire();check(h,t.isDeadOrDying(),"Real paid precision final blow");
        state(h,f.p,1,40);check(h,WeaponOutlaw.remaining(f.p)==120,"Same real hit earns Outlaw too");
        var plan=WeaponRapidHit.plan(f.p,f.entry,WeaponOutlaw.plan(f.p,f.entry,f.profile));
        check(h,plan.firstTicks()==40&&plan.intervalTicks()==40,"One-ceil capped stat + multiplied scalar local pair policy");
        check(h,WeaponRuntime.reload(f.p)&&WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==40,"Actual runtime accepts combined plan");h.succeed();
    }
}
