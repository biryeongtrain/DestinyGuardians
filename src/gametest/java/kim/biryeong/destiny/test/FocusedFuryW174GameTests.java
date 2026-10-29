package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
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

/** Actual paid geometry and accepted reloads, not native-input or injected positive credit. */
public final class FocusedFuryW174GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="focused_fury";
    static void check(GameTestHelper h,boolean yes,String why){h.assertTrue(yes,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final ItemStack gun;final WeaponCatalog.Entry entry;
        final WeaponProfile profile;final List<Husk> targets=new ArrayList<>();
        Fixture(GameTestHelper h) {
            this.h=h;entry=WeaponCatalog.find("aishas_embrace").orElseThrow();profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W174_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,true);
            gun=WeaponItems.create(entry);check(h,WeaponPerks.select(gun,ID),"Exact official Focused Fury socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),0));
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
            h.onEachTick(()->TestPlayers.drain(p));
            TestCleanup.register(h,()->{targets.forEach(t->{Statuses.forget(t);t.discard();});WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        Husk target(boolean head) {
            targets.forEach(t->{Statuses.forget(t);t.discard();});targets.clear();
            var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,head?1:1.8,6));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.setPersistenceRequired();
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(1000);return t;
        }
        float fire(Husk t) {
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            if(!t.isRemoved()) {
                var from=p.getEyePosition();p.getRandom().setSeed(0x5DEECE66DL);
                var ray=WeaponAiming.direction(p);
                var hit=t.getBoundingBox().inflate(.03).clip(from,from.add(ray.scale(16))).orElseThrow();
                check(h,WeaponPrecision.critical(t,from,hit,WeaponBallistics.of(entry).precision())==(t.getY()==p.getY()),"Same-seed preflight distinguishes actual head from body before paying");
            }
            int rounds=WeaponItems.magazine(gun,profile).rounds();float before=t.getHealth();
            boolean refund=WeaponPerks.selected(gun,PrecisionReturnProfile.TRIPLE_TAP).isPresent()&&WeaponPrecisionReturn.progress(p,PrecisionReturnProfile.TRIPLE_TAP)==2;
            check(h,beginUse(p),"Actual paid trigger");WeaponRuntime.releaseUse(p,gun);
            check(h,WeaponItems.magazine(gun,profile).rounds()==rounds-1+(refund?1:0),"One paid cartridge plus independently earned Triple Tap refund");
            return before-t.getHealth();
        }
        int gap(){return (int)Math.ceil(profile.cadenceTicks())+2;}
        void chain(int n,Runnable done) {
            float loss=fire(target(true));check(h,loss>0,"Actual precision HP loss");
            if(n==1)done.run();else h.startSequence().thenIdle(gap()).thenExecute(()->chain(n-1,done));
        }
        void hud(boolean live) {
            CombatHud.update(p);check(h,DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith("destiny:hud_perk_focused_fury_")).count()==(live?6:0),"Actual six-node timer row");
        }
        void stow(){WeaponRuntime.selectedSlotChanging(p,7);p.getInventory().setSelectedSlot(7);WeaponRuntime.tickPlayer(p);}
        void restore(){p.getInventory().setSelectedSlot(WeaponCharacteristics.of(entry).slot().hotbar());WeaponRuntime.tickPlayer(p);}
    }
    @GameTest(structure=FLOOR,maxTicks=330,environment=ENV)
    public void sixPaidPrecisionHitsThenNextShotBuffsAndHudExpires(GameTestHelper h) {
        var f=new Fixture(h);float baseline=f.fire(f.target(true));check(h,baseline>0,"Actual baseline precision");
        check(h,WeaponFocusedFury.progress(f.p)==1&&WeaponFocusedFury.remaining(f.p)==0,"No early buff");f.hud(false);
        h.startSequence().thenIdle(f.gap()).thenExecute(()->f.chain(5,()->{
            check(h,WeaponFocusedFury.progress(f.p)==0&&WeaponFocusedFury.remaining(f.p)==220,"Six of base17 rounds,220ticks");f.hud(true);
            h.startSequence().thenIdle(f.gap()).thenExecute(()->{float boosted=f.fire(f.target(true));check(h,Math.abs(boosted/baseline-1.25)<.002,"Only subsequent emission receives25percent");});
            h.startSequence().thenIdle(220).thenExecute(()->{check(h,WeaponFocusedFury.remaining(f.p)==0,"Exact expiration");f.hud(false);h.succeed();});
        }));
    }
    @GameTest(structure=FLOOR,maxTicks=130,environment=ENV)
    public void stowResetsPartialCounterAndPreservesEarnedWindow(GameTestHelper h) {
        var f=new Fixture(h);f.chain(2,()->{check(h,WeaponFocusedFury.progress(f.p)==2,"Partial progress2");f.stow();f.restore();
            check(h,WeaponFocusedFury.progress(f.p)==0,"Same-tick actual selected-slot stow resets");
            h.startSequence().thenIdle(f.gap()+20).thenExecute(()->f.chain(6,()->{int before=WeaponFocusedFury.remaining(f.p);f.stow();
                check(h,WeaponFocusedFury.remaining(f.p)==0&&WeaponFocusedFury.ownedRemaining(f.p,f.gun)==before,"Unrelated held source no HUD; original retains deadline");f.hud(false);
                h.startSequence().thenIdle(5).thenExecute(()->{f.restore();check(h,WeaponFocusedFury.remaining(f.p)==before-5&&WeaponFocusedFury.progress(f.p)==0,"Earned buff resumes without refreshed clock");f.hud(true);h.succeed();});
            }));
        });
    }
    @GameTest(structure=FLOOR,maxTicks=180,environment=ENV)
    public void acceptedReloadResetsPartialButCannotEraseEarnedBuff(GameTestHelper h) {
        var f=new Fixture(h);f.chain(6,()->h.startSequence().thenIdle(f.gap()).thenExecute(()->{
            f.fire(f.target(true));check(h,WeaponFocusedFury.progress(f.p)==1,"Next cycle has one precision");
            int remaining=WeaponFocusedFury.remaining(f.p);check(h,WeaponRuntime.reload(f.p),"Actual partially depleted primary reload");
            check(h,WeaponFocusedFury.progress(f.p)==0&&WeaponFocusedFury.remaining(f.p)==remaining,"Accepted reload clears only count");
            check(h,!WeaponRuntime.reload(f.p),"Duplicate denied reload");
            for(int i=1;i<=f.profile.reloadTicks()+2;i++)h.startSequence().thenIdle(i).thenExecute(()->WeaponRuntime.tickPlayer(f.p));
            h.startSequence().thenIdle(f.profile.reloadTicks()+3).thenExecute(()->{check(h,WeaponItems.magazine(f.gun,f.profile).rounds()==17,"Actual ammo credit");check(h,WeaponFocusedFury.remaining(f.p)>0,"Buff survives recovery");h.succeed();});
        }));
    }
    @GameTest(structure=FLOOR,maxTicks=120,environment=ENV)
    public void tripleTapRefundDoesNotChangeBaseThresholdOrCountRefundAsPrecision(GameTestHelper h) {
        var f=new Fixture(h);check(h,WeaponPerks.select(f.gun,PrecisionReturnProfile.TRIPLE_TAP),"Official separate Triple Tap socket");
        check(h,WeaponPerks.selected(f.gun,ID).isPresent(),"Distinct Focused Fury socket remains selected");
        f.chain(6,()->{
            check(h,WeaponItems.magazine(f.gun,f.profile).rounds()==13,"Six paid rounds and two earned Triple Tap refunds");
            check(h,WeaponFocusedFury.progress(f.p)==0&&WeaponFocusedFury.remaining(f.p)==220,"Refund neither changes six-hit threshold nor counts as a hit");
            check(h,WeaponProfile.forEntry(f.entry).reloadTicks()==f.profile.reloadTicks(),"No invented reload speed");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=100,environment=ENV)
    public void bodyWeakenedBodyAbilityImmuneAndMissCannotPrimePrecision(GameTestHelper h) {
        var f=new Fixture(h);var body=f.target(false);Statuses.apply(body,Keyword.WEAKENED,100);check(h,f.fire(body)>0,"Real weakened body hit");
        check(h,WeaponFocusedFury.progress(f.p)==0,"Weakened body still not precision");
        Combat.damage(f.p.level(),f.p,body,1,Element.VOID,AmmoGeneration.ABILITY);check(h,WeaponFocusedFury.progress(f.p)==0,"Ability excluded");
        h.startSequence().thenIdle(f.gap()).thenExecute(()->{var immune=f.target(true);immune.setPermanentlyInvulnerable(true);check(h,f.fire(immune)==0,"Real immune head");
            check(h,WeaponFocusedFury.progress(f.p)==0,"No immune credit");immune.discard();
            h.startSequence().thenIdle(f.gap()).thenExecute(()->{f.fire(immune);check(h,WeaponFocusedFury.progress(f.p)==0,"Miss consumes but no credit");f.hud(false);h.succeed();});
        });
    }
    @GameTest(structure=FLOOR,maxTicks=50,environment=ENV)
    public void onePaidTokenCannotCountTargetsTwiceOrCrossReloadStowEpoch(GameTestHelper h) {
        var f=new Fixture(h);var token=WeaponFocusedFury.capture(f.p);f.fire(f.target(true));int n=WeaponFocusedFury.progress(f.p);
        // Negative duplicate/epoch probes are explicit API tests, not positive native proof.
        WeaponFocusedFury.confirmed(f.p,token,false,1);WeaponFocusedFury.confirmed(f.p,token,true,0);
        check(h,WeaponFocusedFury.progress(f.p)==n,"Invalid confirmation inert");
        f.stow();f.restore();WeaponFocusedFury.confirmed(f.p,token,true,1);
        check(h,WeaponFocusedFury.progress(f.p)==0,"Pre-stow emission cannot prime new counter");
        var reloadToken=WeaponFocusedFury.capture(f.p);h.startSequence().thenIdle(f.gap()+20).thenExecute(()->{
            check(h,WeaponRuntime.reload(f.p),"Actual reload accepted");WeaponFocusedFury.confirmed(f.p,reloadToken,true,1);
            check(h,WeaponFocusedFury.progress(f.p)==0,"Pre-reload emission stale");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void copyEditRuntimeReplacementAndCleanupCannotBorrowState(GameTestHelper h) {
        var f=new Fixture(h);f.fire(f.target(true));var token=WeaponFocusedFury.capture(f.p);
        int slot=f.p.getInventory().getSelectedSlot();var copy=f.gun.copy();f.p.getInventory().setItem(slot,copy);WeaponRuntime.tickPlayer(f.p);
        WeaponFocusedFury.confirmed(f.p,token,true,1);check(h,WeaponFocusedFury.progress(f.p)==0,"Copied replacement cannot borrow source");
        f.p.getInventory().setItem(slot,f.gun);WeaponRuntime.tickPlayer(f.p);var edit=WeaponFocusedFury.capture(f.p);
        WeaponPerks.clear(f.gun);WeaponPerks.select(f.gun,ID);WeaponFocusedFury.confirmed(f.p,edit,true,1);check(h,WeaponFocusedFury.progress(f.p)==0,"Edit invalidates");
        var rt=WeaponFocusedFury.capture(f.p);Guardians.forget(f.p);Guardians.runtime(f.p);WeaponFocusedFury.confirmed(f.p,rt,true,1);
        check(h,WeaponFocusedFury.progress(f.p)==0,"Guardian runtime replacement invalidates");
        var clean=WeaponFocusedFury.capture(f.p);WeaponRuntime.cleanup(f.p);WeaponFocusedFury.confirmed(f.p,clean,true,1);
        check(h,WeaponFocusedFury.progress(f.p)==0&&WeaponFocusedFury.remaining(f.p)==0,"Cleanup invalidates all");f.hud(false);h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=10,environment=ENV)
    public void exactThreeOptionalSocketsAndOfficialBaseThresholds(GameTestHelper h) {
        var ids=Set.of("aishas_embrace","retraced_path","fixed_odds");int n=0;
        for(var e:WeaponCatalog.all()){var s=WeaponItems.create(e);check(h,WeaponPerks.selected(s,ID).isEmpty(),"No default");
            check(h,WeaponPerks.select(s,ID)==ids.contains(e.id()),"Exact source socket "+e.id());if(ids.contains(e.id()))n++;}
        check(h,n==3,"Only official basic3; no enhanced/exotic/family expansion");
        for(var row:Map.of("aishas_embrace",6,"retraced_path",33,"fixed_odds",16).entrySet())
            check(h,FocusedFuryProfile.threshold(WeaponCatalog.find(row.getKey()).orElseThrow())==row.getValue(),"Ceil35percent official baseline");
        h.succeed();
    }
}
