package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
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
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Real post-mitigation hurt hooks/paid shots, not synthetic Frenzy event-token injection or native input. */
public final class FrenzyW172GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    /** Production left-click ADS; does not bypass the three-tick toggle debounce. */
    private static void ads(net.minecraft.server.level.ServerPlayer p, boolean requested) {
        if (WeaponAiming.requested(p) != requested) kim.biryeong.destiny.input.InputRouter.onPunch(p);
    }
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="frenzy",PREFIX="destiny:hud_perk_frenzy_";
    static void check(GameTestHelper h,boolean yes,String why){h.assertTrue(yes,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final ItemStack gun;final WeaponCatalog.Entry entry;final WeaponProfile profile;
        final List<Husk> targets=new ArrayList<>();
        Fixture(GameTestHelper h){this(h,"austringer");}
        Fixture(GameTestHelper h,String id){
            this.h=h;entry=WeaponCatalog.find(id).orElseThrow();profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W172_"+UUID.randomUUID().toString().substring(0,8));
            p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,true);
            gun=WeaponItems.create(entry);check(h,WeaponPerks.select(gun,ID),"Official base Frenzy socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),200));
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
            h.onEachTick(()->{WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);});
            TestCleanup.register(h,()->{targets.forEach(Husk::discard);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        Husk target(){
            targets.forEach(Husk::discard);targets.clear();
            var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,1.8,6));targets.add(t);t.setNoAi(true);t.setNoGravity(true);t.setPersistenceRequired();
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(1000);return t;
        }
        void dealt(){var t=target();Combat.damage(p.level(),p,t,1,Element.VOID,AmmoGeneration.ABILITY);check(h,t.getHealth()==999,"Actual ability HP loss primes combat");}
        void prime(){dealt();for(int t:new int[]{80,160,230})h.startSequence().thenIdle(t).thenExecute(this::dealt);}
        void received(){
            var t=target();p.setHealth(p.getMaxHealth());p.damageCooldownTime=0;float before=p.getHealth();
            p.hurtServer(p.level(),p.damageSources().mobAttack(t),2);check(h,p.getHealth()<before,"Actual postmitigation enemy-sourced player loss");
        }
        float fire(){
            var t=target();p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            int before=ammo().rounds();check(h,beginUse(p),"Actual paid firing accepted");WeaponRuntime.releaseUse(p,gun);
            check(h,ammo().rounds()==before-1,"Exactly one cartridge paid");check(h,t.getHealth()<1000,"Real body contact");return 1000-t.getHealth();
        }
        WeaponMagazine ammo(){return WeaponItems.magazine(gun,profile);}
        int remaining(){return WeaponFrenzy.remaining(p);}
    }
    static void hud(GameTestHelper h,Fixture f,boolean active){
        CombatHud.update(f.p);var nodes=DisplayHud.getHuds(f.p);
        check(h,nodes.keySet().stream().filter(s->s.startsWith(PREFIX)).count()==(active?6:0),"Real six-node Frenzy timer visibility");
        if(active){int seconds=(f.remaining()+19)/20;var n=nodes.get(PREFIX+"ones");check(h,n instanceof ItemDisplayHud&&Identifier.parse("destiny:gui/hud/ammo_digit_"+seconds%10).equals(((ItemDisplayHud)n).getItem().get(DataComponents.ITEM_MODEL)),"Countdown observes actual remaining ticks");}
    }
    @GameTest(structure=FLOOR,maxTicks=410,environment=ENV)
    public void actualCombatTwelveSecondsGivesPaidDamageFifteenPercentAndHudThenExpires(GameTestHelper h){
        var f=new Fixture(h);float base=f.fire();for(int t:new int[]{80,160,230})h.startSequence().thenIdle(t).thenExecute(f::dealt);
        h.startSequence().thenIdle(239).thenExecute(()->{check(h,f.remaining()==0,"Not before twelve seconds");hud(h,f,false);});
        h.startSequence().thenIdle(242).thenExecute(()->{
            check(h,f.remaining()>0&&f.remaining()<=144,"Actual hurt hook and ticks activate");float boosted=f.fire();
            check(h,Math.abs(boosted/base-1.15)<.0001,"Paid body damage receives sourced fifteen percent, not ability damage");hud(h,f,true);
            check(h,WeaponFrenzy.capture(f.p).multiplier()==1.15f,"Firing-time immutable multiplier");
        });
        h.startSequence().thenIdle(390).thenExecute(()->{check(h,f.remaining()==0&&WeaponFrenzy.capture(f.p).multiplier()==1,"No damage refresh after last paid hit");hud(h,f,false);h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=430,environment=ENV)
    public void realEnemyReceivedDamagePrimesAndRefreshesButReadsCannot(GameTestHelper h){
        var f=new Fixture(h);f.received();for(int t:new int[]{80,160,230})h.startSequence().thenIdle(t).thenExecute(f::received);
        h.startSequence().thenIdle(242).thenExecute(()->{check(h,f.remaining()>0,"Received-only real player loss activates");f.received();check(h,f.remaining()==144,"Real received event refreshes144ticks");hud(h,f,true);});
        h.startSequence().thenIdle(300).thenExecute(()->{check(h,f.remaining()==86,"Elapsed deadline unchanged by HUD/read calls");for(int i=0;i<100;i++){WeaponFrenzy.remaining(f.p);CombatHud.update(f.p);}});
        h.startSequence().thenIdle(387).thenExecute(()->{check(h,f.remaining()==0,"Received-event buff expires");hud(h,f,false);h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=280,environment=ENV)
    public void environmentalSelfAndInvulnerableDamageDoNotPrimeCombat(GameTestHelper h){
        var f=new Fixture(h);
        for(int t:new int[]{1,60,120,180,240})h.startSequence().thenIdle(t).thenExecute(()->{
            f.p.setHealth(f.p.getMaxHealth());f.p.damageCooldownTime=0;f.p.hurtServer(f.p.level(),f.p.damageSources().fall(),1);
            f.p.damageCooldownTime=0;f.p.hurtServer(f.p.level(),f.p.damageSources().playerAttack(f.p),1);
            var target=f.target();target.setPermanentlyInvulnerable(true);Combat.damage(f.p.level(),f.p,target,10,Element.SOLAR,AmmoGeneration.ABILITY);
            check(h,target.getHealth()==1000,"Rejected damage has no actual loss");
            check(h,WeaponFrenzy.combatTicks(f.p)==0&&f.remaining()==0,"Self/environment and denied hit never credit");
        });
        h.startSequence().thenIdle(260).thenExecute(()->{check(h,f.remaining()==0,"Time alone cannot prime");hud(h,f,false);h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=300,environment=ENV)
    public void originalStowedSourceActivatesButBackpackCopyAndEditedSourceDoNotInherit(GameTestHelper h){
        var f=new Fixture(h);var copy=f.gun.copy();f.p.getInventory().setItem(9,copy);
        var other=WeaponCatalog.find("ammit_ar2").orElseThrow();f.p.getInventory().setItem(1,WeaponItems.create(other));f.p.getInventory().setSelectedSlot(1);WeaponRuntime.tickPlayer(f.p);f.prime();
        h.startSequence().thenIdle(242).thenExecute(()->{
            check(h,f.remaining()==0&&WeaponFrenzy.ownedRemaining(f.p,f.gun)>0,"Equipped original primes while stowed, HUD observes held only");
            check(h,WeaponFrenzy.ownedRemaining(f.p,copy)==0,"Backpack copied NBT not active equipment");hud(h,f,false);
            f.p.getInventory().setSelectedSlot(0);WeaponHandling.update(f.p);
            int expected=WeaponHandlingProfile.of(other).stowTicks()+FrenzyProfile.timing(f.entry).readyTicks();
            check(h,WeaponHandling.remaining(f.p)==expected,"Actual swap includes boosted incoming ready");
        });
        h.startSequence().thenIdle(275).thenExecute(()->{
            check(h,f.remaining()>0,"Original still active when held");hud(h,f,true);
            f.p.getInventory().setItem(0,f.gun.copy());WeaponRuntime.tickPlayer(f.p);check(h,f.remaining()==0,"Copy cannot inherit live combat");
            f.p.getInventory().setItem(0,f.gun);WeaponRuntime.tickPlayer(f.p);check(h,f.remaining()==0,"Removed original session retired");
            check(h,WeaponPerks.clear(f.gun)&&WeaponPerks.select(f.gun,ID),"Real edit epoch");
            check(h,f.remaining()==0&&WeaponFrenzy.combatTicks(f.p)==0,"Same-tick clear/reselect resets");WeaponRuntime.cleanup(f.p);check(h,f.remaining()==0,"Explicit cleanup inert");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=440,environment=ENV)
    public void realSpecialReloadAndAdsUseStatOneHundredAndReloadDoesNotRetimeOnExpiry(GameTestHelper h){
        var f=new Fixture(h,"retraced_path");WeaponItems.save(f.gun,new WeaponMagazine(f.profile,1,200));f.prime();
        h.startSequence().thenIdle(242).thenExecute(()->{check(h,f.remaining()>0,"Earned buff");ads(f.p,true);check(h,WeaponFrenzy.adsTicks(f.p,f.entry,99,true)==FrenzyProfile.timing(f.entry).adsTicks(),"ADS handling100 adapter");});
        h.startSequence().thenIdle(260).thenExecute(()->{check(h,WeaponAiming.progress(f.p)>=.99f,"Actual ADS reaches fully aimed");ads(f.p,false);});
        h.startSequence().thenIdle(377).thenExecute(()->{
            check(h,f.remaining()>0&&f.remaining()<12,"Near-expiry earned state");int fast=FrenzyProfile.timing(f.entry).reloadTicks();
            check(h,fast<f.profile.reloadTicks()&&WeaponRuntime.reload(f.p),"Actual stat100 faster reload");
            check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==fast,"Live reload snapshots boost");
            h.startSequence().thenIdle(10).thenExecute(()->{check(h,f.remaining()==0,"Frenzy expired during accepted reload");check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==fast,"Accepted reload not retimed");});
            h.startSequence().thenIdle(fast+3).thenExecute(()->{check(h,!WeaponRuntime.reloading(f.p)&&f.ammo().rounds()==f.profile.magazine()&&f.ammo().reserve()==201-f.profile.magazine(),"Real reserve payment and full recovery");h.succeed();});
        });
    }
    @GameTest(structure=FLOOR,maxTicks=15,environment=ENV)
    public void exactTenOptionalBaseSocketsAndNoImplicitSelection(GameTestHelper h){
        var ids=Set.of("austringer","allied_demand","farewell","brass_attacks","dream_breaker","stormchaser","retraced_path","code_duello","retrofit_escapade","nezarec_s_whisper");int count=0;
        for(var e:WeaponCatalog.all()){var stack=WeaponItems.create(e);check(h,WeaponPerks.selected(stack,ID).isEmpty(),"Optional not default");boolean expected=ids.contains(e.id());check(h,WeaponPerks.select(stack,ID)==expected,"Exact65 scan: "+e.id());if(expected)count++;}
        check(h,count==10,"Ten exact base sockets, not a weapon-family expansion");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=285,environment=ENV)
    public void paidRocketKeepsItsFiringTimeBuffAfterSourceReplacement(GameTestHelper h){
        var f=new Fixture(h,"code_duello");var baseTarget=f.target();float[] baseline={0};
        check(h,beginUse(f.p),"Baseline actual paid rocket");WeaponRuntime.releaseUse(f.p,f.gun);
        check(h,f.ammo().rounds()==0&&WeaponRuntime.activeProjectiles(f.p)==1,"One cartridge launches one real projectile");
        h.startSequence().thenIdle(10).thenExecute(()->{baseline[0]=1000-baseTarget.getHealth();check(h,baseline[0]>0,"Actual baseline rocket contact");});
        for(int t:new int[]{80,160,230})h.startSequence().thenIdle(t).thenExecute(f::dealt);
        h.startSequence().thenIdle(250).thenExecute(()->{
            check(h,f.remaining()>0,"Real combat earned source buff");var target=f.target();
            // Authorized ammo fixture for the independent second emission, not native reload proof.
            WeaponItems.save(f.gun,new WeaponMagazine(f.profile,1,200));f.p.setYRot(-90);f.p.setYHeadRot(-90);f.p.setXRot(0);WeaponAiming.cleanup(f.p);WeaponAiming.tick(f.p);
            check(h,beginUse(f.p),"Buffed paid rocket accepted");WeaponRuntime.releaseUse(f.p,f.gun);
            check(h,f.ammo().rounds()==0&&WeaponRuntime.activeProjectiles(f.p)==1,"Only one paid new rocket");
            int slot=f.p.getInventory().getSelectedSlot();f.p.getInventory().setItem(slot,f.gun.copy());WeaponFrenzy.update(f.p);
            check(h,f.remaining()==0,"Replacement cannot acquire source buff");
            h.startSequence().thenIdle(10).thenExecute(()->{float boosted=1000-target.getHealth();check(h,Math.abs(boosted/baseline[0]-1.15)<.001,"Actual delayed impact retains immutable paid-firing multiplier");h.succeed();});
        });
    }
    @GameTest(structure=FLOOR,maxTicks=310,environment=ENV)
    public void actualPrecisionOutlawKeepsItsDurationScalarWithFrenzyStatOneHundred(GameTestHelper h){
        var f=new Fixture(h);check(h,WeaponPerks.select(f.gun,OutlawProfile.ID),"Distinct actual Outlaw socket3 alongside Frenzy4");f.prime();
        h.startSequence().thenIdle(242).thenExecute(()->{
            var t=f.target();t.setPos(h.absoluteVec(new Vec3(8.5,1,6)));t.setHealth(1);
            f.p.setYRot(-90);f.p.setYHeadRot(-90);f.p.setXRot(0);WeaponAiming.cleanup(f.p);WeaponAiming.tick(f.p);
            check(h,beginUse(f.p),"Paid precision final blow");WeaponRuntime.releaseUse(f.p,f.gun);
            check(h,!t.isAlive()&&WeaponOutlaw.remaining(f.p)>0&&f.remaining()>0,"Real head final blow earns both live buffs");
            int expected=FrenzyProfile.reloadTicks(f.entry,OutlawProfile.perk().durationMultiplier());
            check(h,expected<FrenzyProfile.timing(f.entry).reloadTicks(),"Outlaw scalar survives at capped reload stat");
            check(h,WeaponRuntime.reload(f.p)&&WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==expected,"Actual reload snapshots combined raw stat/scalar single-ceil plan");
            h.startSequence().thenIdle(expected+2).thenExecute(()->{check(h,!WeaponRuntime.reloading(f.p),"Combined reload completes");h.succeed();});
        });
    }
    @GameTest(structure=FLOOR,maxTicks=275,environment=ENV)
    public void actualDistinctSnapshotOnlyScalesFrenzyAdsEntryNotExit(GameTestHelper h){
        var f=new Fixture(h);check(h,WeaponPerks.select(f.gun,SnapshotAimProfile.ID),"Distinct actual Snapshot3 alongside Frenzy4");f.prime();
        h.startSequence().thenIdle(242).thenExecute(()->{
            check(h,f.remaining()>0,"Earned real combat buff");
            check(h,WeaponFrenzy.adsTicks(f.p,f.entry,99,true)==2,"Primary half scalar applied before single ceil to raw stat100 ADS");
            check(h,WeaponFrenzy.adsTicks(f.p,f.entry,99,false)==4,"ADS exit retains full stat100 curve, not Snapshot");
            ads(f.p,true);
        });
        h.startSequence().thenIdle(246).thenExecute(()->{check(h,WeaponAiming.progress(f.p)>=.99f,"Production ADS state reaches full aim with selected pair");h.succeed();});
    }
}
