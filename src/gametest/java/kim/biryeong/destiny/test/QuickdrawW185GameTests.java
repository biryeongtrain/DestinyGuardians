package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

/** Real server hotbar/input packet handlers; neither native client input nor rendering proof. */
public final class QuickdrawW185GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    /** Production left-click ADS; does not bypass the three-tick toggle debounce. */
    private static void ads(net.minecraft.server.level.ServerPlayer p, boolean requested) {
        if (WeaponAiming.requested(p) != requested) kim.biryeong.destiny.input.InputRouter.onPunch(p);
    }
    static final String FLOOR="destiny-test:floor", ENV="destiny-test:w90_isolated", ID="quickdraw";
    static void check(GameTestHelper h,boolean ok,String why){h.assertTrue(ok,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h; final ServerPlayer p; final WeaponCatalog.Entry entry;
        final WeaponProfile profile; final ItemStack incoming,outgoing;
        Fixture(GameTestHelper h){
            this.h=h;p=TestPlayers.create(h,new Vec3(2.5,1,6),-90,0);p.setNoGravity(true);p.setOnGround(true);
            p.setAttached(WeaponLoadout.ENABLED,false);entry=WeaponCatalog.find("apostate").orElseThrow();profile=WeaponProfile.forEntry(entry);
            incoming=WeaponItems.create(entry);check(h,WeaponPerks.select(incoming,ID),"Real Apostate socket4 Quickdraw");
            WeaponItems.save(incoming,new WeaponMagazine(profile,profile.magazine(),100));
            outgoing=WeaponItems.create(WeaponCatalog.find("steelfeather_repeater").orElseThrow());
            p.getInventory().setItem(0,outgoing);p.getInventory().setItem(1,incoming);p.getInventory().setSelectedSlot(0);
            WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
            h.onEachTick(()->{WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);});
            TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void select(int slot){p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot));TestPlayers.drain(p);}
        void draw(){select(1);check(h,p.getMainHandItem()==incoming,"Vanilla validated handler selected genuine incoming");}
    }
    @GameTest(structure=FLOOR,maxTicks=15,environment=ENV)
    public void initialObservationDoesNotArmButRealDrawDoes(GameTestHelper h){
        var f=new Fixture(h);check(h,WeaponQuickdraw.remaining(f.p)==0,"Initial binding is already equipped, not a draw");
        int oldStow=WeaponHandlingProfile.of(WeaponItems.entry(f.outgoing).orElseThrow()).stowTicks();
        f.draw();check(h,WeaponQuickdraw.remaining(f.p)==20,"Actual selection begins exactly one-second window");
        var hp=WeaponHandlingProfile.of(f.entry);int ready=WeaponQuickdraw.handlingTicks(f.p,f.incoming,true,hp.readyTicks());
        check(h,ready<hp.readyTicks()&&WeaponHandling.remaining(f.p)==oldStow+ready,"Actual clock uses untouched outgoing then Quickdraw incoming duration");
        for(int i=0;i<100;i++)check(h,WeaponQuickdraw.remaining(f.p)==20,"Read-only observations cannot extend or consume deadline");
        f.select(1);check(h,WeaponQuickdraw.remaining(f.p)==20,"Same slot is not another draw");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=35,environment=ENV)
    public void actualClockExpiresAtTwentyWithoutReadRefresh(GameTestHelper h){
        var f=new Fixture(h);f.draw();
        h.startSequence().thenIdle(19).thenExecute(()->check(h,WeaponQuickdraw.remaining(f.p)==1,"Nineteen elapsed leaves exactly one tick"));
        h.startSequence().thenIdle(20).thenExecute(()->{check(h,WeaponQuickdraw.remaining(f.p)==0,"Exactly twenty elapsed is expired");var hp=WeaponHandlingProfile.of(f.entry);check(h,WeaponQuickdraw.handlingTicks(f.p,f.incoming,false,hp.stowTicks())==hp.stowTicks(),"Expired stow falls back without arming");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=15,environment=ENV)
    public void actualAdsPressReleaseWithinOneTickCancelsEvenWhileBlocked(GameTestHelper h){
        var f=new Fixture(h);f.draw();long accepted=WeaponHandling.remaining(f.p);check(h,accepted>0,"Draw still in handling");
        kim.biryeong.destiny.input.InputRouter.onPunch(f.p);
        check(h,WeaponQuickdraw.remaining(f.p)==0,"Real left-click ADS request cancels before delayed ADS transition");
        check(h,!WeaponAiming.requested(f.p),"Handling consumed the click without queued ADS");
        kim.biryeong.destiny.input.InputRouter.onPunch(f.p);
        check(h,WeaponQuickdraw.remaining(f.p)==0&&!WeaponAiming.requested(f.p),"Same-tick repeated click cannot resurrect the consumed grant or queue ADS");
        check(h,WeaponHandling.remaining(f.p)==accepted,"Already accepted switch deadline is immutable, not retroactively retimed");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=35,environment=ENV)
    public void outgoingStowUsesLiveGrantBeforeIncomingWindowReplacement(GameTestHelper h){
        var f=new Fixture(h);f.draw();int delay=(int)WeaponHandling.remaining(f.p)+1;check(h,delay<20,"Representative draw completes inside sourced window");
        h.startSequence().thenIdle(delay).thenExecute(()->{
            var hp=WeaponHandlingProfile.of(f.entry);int fast=WeaponQuickdraw.handlingTicks(f.p,f.incoming,false,hp.stowTicks());
            check(h,WeaponQuickdraw.remaining(f.p)>0&&fast<hp.stowTicks(),"Still-live100 handling applies to stow, without ready-only scalar");
            int ready=WeaponHandlingProfile.of(WeaponItems.entry(f.outgoing).orElseThrow()).readyTicks();f.select(0);
            check(h,WeaponHandling.remaining(f.p)==fast+ready,"Capture outgoing duration before retiring source for ordinary incoming");check(h,WeaponQuickdraw.remaining(f.p)==0,"No grant on ordinary incoming");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void noAdsSpeedReloadOrFreeAmmoIsInvented(GameTestHelper h){
        var f=new Fixture(h);f.draw();int delay=(int)WeaponHandling.remaining(f.p)+1;
        check(h,WeaponItems.magazine(f.incoming,f.profile).rounds()==f.profile.magazine(),"Draw creates no ammo transfer");
        h.startSequence().thenIdle(delay).thenExecute(()->{
            WeaponAiming.cleanup(f.p);ads(f.p,true);WeaponAiming.tick(f.p);
            int ads=WeaponAimProfile.of(f.entry).transitionTicks();check(h,Math.abs(WeaponAiming.progress(f.p)-1f/ads)<.0001,"No Quickdraw ADS stat or scalar");
            ads(f.p,false);WeaponAiming.cleanup(f.p);check(h,beginUse(f.p),"Ready real trigger accepted");WeaponRuntime.releaseUse(f.p,f.incoming);
            check(h,WeaponItems.magazine(f.incoming,f.profile).rounds()==f.profile.magazine()-1,"One real paid shot, no free cartridge");
            check(h,WeaponRuntime.reload(f.p),"Actual normal reload accepted");check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==f.profile.reloadTicks(),"Quickdraw does not accelerate reload");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void copiesSocketClearAndSourceLossCannotBorrowGrant(GameTestHelper h){
        var f=new Fixture(h);f.draw();var hp=WeaponHandlingProfile.of(f.entry);
        check(h,WeaponQuickdraw.handlingTicks(f.p,f.incoming.copy(),true,777)==777,"Equal-data detached copy has no identity grant");
        WeaponPerks.clear(f.incoming);check(h,WeaponQuickdraw.remaining(f.p)==0,"Real socket edit immediately invalidates grant");
        check(h,WeaponPerks.select(f.incoming,ID),"Reselect exact source");check(h,WeaponQuickdraw.remaining(f.p)==0,"Perk choice is not a weapon draw");
        f.select(0);f.select(1);check(h,WeaponQuickdraw.remaining(f.p)==20,"Real away-and-back draw can grant");
        var copy=f.incoming.copy();f.p.getInventory().setItem(1,copy);WeaponQuickdraw.update(f.p);
        check(h,WeaponQuickdraw.remaining(f.p)==0&&WeaponQuickdraw.handlingTicks(f.p,copy,true,hp.readyTicks())==hp.readyTicks(),"Copied persistence does not contain runtime window; getter cannot bind new one");
        WeaponRuntime.cleanup(f.p);WeaponRuntime.cleanup(f.p);check(h,WeaponQuickdraw.remaining(f.p)==0,"Repeated cleanup neutral");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void genuineEquippedIncomingWorksBeforeNonweaponSelectionChanges(GameTestHelper h){
        var f=new Fixture(h);f.p.setAttached(WeaponLoadout.ENABLED,true);f.p.getInventory().setItem(7,new ItemStack(Items.STONE));f.select(7);f.draw();
        check(h,WeaponQuickdraw.remaining(f.p)==20,"Genuine equipped energy slot accepted from nonweapon selection");
        var hp=WeaponHandlingProfile.of(f.entry);check(h,WeaponQuickdraw.handlingTicks(f.p,f.incoming,true,hp.readyTicks())<hp.readyTicks(),"Incoming ready benefit not gated by outgoing weapon");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=60,environment=ENV)
    public void legalThreatDetectorIncomingSampleKeepsScalarBeforeSelection(GameTestHelper h){
        var f=new ThreatDetectorW178GameTests.Fixture(h,"dream_breaker");
        check(h,WeaponPerks.select(f.gun,ID)&&WeaponPerks.selected(f.gun,ThreatDetectorProfile.ID).isPresent(),"Exact Dream TD3+Quickdraw4 distinct pair");
        f.enemy(2,0,0);f.enemy(3,0,0);f.scan();check(h,f.stacks()==2,"Two real loaded enemies in isolated vertical plane");
        var ordinary=WeaponItems.create(WeaponCatalog.find("steelfeather_repeater").orElseThrow());f.p.getInventory().setItem(0,ordinary);
        f.p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));int delay=(int)WeaponHandling.remaining(f.p)+1;
        h.startSequence().thenIdle(delay).thenExecute(()->{
            f.tick();check(h,WeaponThreatDetector.stacks(f.p)==0,"Ordinary outgoing source has no held TD sample");
            check(h,WeaponThreatDetector.selectionSample(f.p,f.gun.copy())==0,"Detached incoming copy cannot sample a scalar");
            int stow=WeaponHandlingProfile.of(WeaponItems.entry(ordinary).orElseThrow()).stowTicks();
            int ready=QuickdrawProfile.handlingTicks(f.entry,ThreatDetectorProfile.handlingScalar(2),true);
            f.p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
            check(h,WeaponQuickdraw.remaining(f.p)==20&&WeaponHandling.remaining(f.p)==stow+ready,"Accepted real incoming ready uses sampled TD2 scalar and .95 before one ceil");
            f.tick();check(h,f.stacks()==2,"Normal held TD state takes over without borrowing outgoing state");
            int fast=WeaponQuickdraw.handlingTicks(f.p,f.gun,false,999);
            check(h,fast==QuickdrawProfile.handlingTicks(f.entry,ThreatDetectorProfile.handlingScalar(2),false),"Held stow uses real TD2 scalar, no ready-only .95");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void exactOptionalRollsAndNoFabricatedPassiveHud(GameTestHelper h){
        var ids=QuickdrawProfile.rolls().stream().map(WeaponPerks.Roll::id).collect(java.util.stream.Collectors.toSet());check(h,!ids.isEmpty(),"Official finite optional pool");
        for(var e:WeaponCatalog.all()){var stack=WeaponItems.create(e);check(h,WeaponPerks.selected(stack,ID).isEmpty(),"No default grant");check(h,WeaponPerks.select(stack,ID)==ids.contains(e.id()),"Exact source roll "+e.id());}
        var f=new Fixture(h);f.draw();CombatHud.update(f.p);check(h,DisplayHud.getHuds(f.p).keySet().stream().noneMatch(k->k.contains("quickdraw")),"No fabricated passive timer/count HUD");h.succeed();
    }
}
