package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.combat.Combat;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Real paid production shots / server ammo and HUD state, not keyboard or framebuffer evidence. */
public final class SubsistenceW167GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    static final String FLOOR="destiny-test:w109_arena", ENV="destiny-test:w90_isolated";
    static void check(GameTestHelper h,boolean ok,String why){h.assertTrue(ok,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;
        final net.minecraft.server.level.ServerPlayer p;
        final ItemStack gun;
        final WeaponProfile profile;
        final WeaponCatalog.Entry entry;
        final List<Husk> targets=new ArrayList<>();
        Fixture(GameTestHelper h){this(h,"gnawing_hunger");}
        Fixture(GameTestHelper h,String id){
            this.h=h;p=TestPlayers.hunter(h,Element.ARC,new Vec3(24,1,24),-90,0,"W167_"+UUID.randomUUID().toString().substring(0,8));
            p.setAttached(WeaponLoadout.ENABLED,true);p.setNoGravity(true);p.setOnGround(true);
            entry=WeaponCatalog.find(id).orElseThrow();profile=WeaponProfile.forEntry(entry);gun=WeaponItems.create(entry);
            check(h,WeaponPerks.select(gun,"subsistence"),"Exact official Subsistence socket");
            ammo(10,profile.reserve());
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            WeaponRuntime.tickPlayer(p);
            TestCleanup.register(h,()->{targets.forEach(Husk::discard);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
            h.onEachTick(()->{WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);});
        }
        void ammo(int rounds,int reserve){WeaponItems.save(gun,new WeaponMagazine(profile,rounds,reserve));}
        WeaponMagazine ammo(){return WeaponItems.magazine(gun,profile);}
        int reward(){return SubsistenceProfile.refillRounds(entry,profile.magazine());}
        Husk target(float hp){
            targets.forEach(Husk::discard);targets.clear();
            var t=h.spawn(EntityTypes.HUSK,new Vec3(30,1.8,24));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.setPersistenceRequired();t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(hp);return t;
        }
        void fire(Husk t){
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            float hp=t.getHealth();check(h,beginUse(p),"Production instant-use trigger accepted");WeaponRuntime.releaseUse(p,gun);
            check(h,t.getHealth()<hp,"Actual HP damage confirmed");
        }
        Husk corpse(){var t=target(1);t.setHealth(0);return t;}
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void ordinaryLiveWeaponOwnerDoesNotNeedAnAbilityRuntime(GameTestHelper h){
        var f=new Fixture(h);Guardians.data(f.p).setGuardianClass(GuardianClass.NONE);
        check(h,Guardians.runtimeIfPresent(f.p).isEmpty(),"No artificial Guardian runtime before paid shot");
        f.fire(f.target(1));check(h,f.ammo().rounds()==9+f.reward(),"Ordinary eligible live weapon also refills");
        check(h,Guardians.runtimeIfPresent(f.p).isEmpty(),"Capture and ammo HUD cannot create ability runtime");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=35,environment=ENV)
    public void paidFinalBlowRefillsAndAmmoHudIsAuthoritative(GameTestHelper h){
        var f=new Fixture(h);f.fire(f.target(1));
        check(h,f.ammo().rounds()==9+f.reward(),"Paid round then sourced17percent refill");
        check(h,!WeaponRuntime.reloading(f.p),"No reload animation/cycle");
        check(h,AmmoHud.current(f.p).orElseThrow().rounds()==f.ammo().rounds(),"Existing magazine HUD reads real saved refill");
        h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void nonlethalAndAbilityFinalBlowsNeverRefill(GameTestHelper h){
        var f=new Fixture(h);var t=f.target(1000);f.fire(t);
        check(h,f.ammo().rounds()==9,"Nonlethal paid damage has no ammo reward");
        Combat.damage(f.p.level(),f.p,t,2000,Element.ARC,AmmoGeneration.ABILITY);
        check(h,!t.isAlive()&&f.ammo().rounds()==9,"Generic ability kill cannot activate weapon trait");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void lastRoundFinalBlowAvoidsEmptyAutoReloadAndPreservesCadence(GameTestHelper h){
        var f=new Fixture(h);f.ammo(1,f.profile.reserve());f.fire(f.target(1));
        check(h,f.ammo().rounds()==f.reward(),"Last cartridge earns real immediate refill");
        check(h,!beginUse(f.p),"Refill never resets paid firing deadline");
        h.startSequence().thenIdle(2).thenExecute(()->{check(h,!WeaponRuntime.reloading(f.p),"No stale empty candidate starts reload after refill");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void refillDoesNotProcMultikillClipButRealReloadDoes(GameTestHelper h){
        var f=new Fixture(h);check(h,WeaponPerks.select(f.gun,"multikill_clip"),"Separate official right socket");
        check(h,WeaponPerks.selected(f.gun,"subsistence").isPresent(),"Left socket preserved");
        f.fire(f.target(1));check(h,WeaponMultikillClip.stacks(f.p)==0,"Refill is not an on-reload event");
        check(h,WeaponRuntime.reloadFromMarksmanDodge(f.p)>0,"Subsequent real ammo-credit remains functional");
        check(h,WeaponMultikillClip.stacks(f.p)==1,"Only actual reload credit activates pending MKC kill");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void finiteReserveIsTransferredNotGenerated(GameTestHelper h){
        var entry=SubsistenceProfile.rolls().stream().map(r->WeaponCatalog.find(r.id()).orElseThrow())
                .filter(e->!WeaponProfile.forEntry(e).infiniteReserve()).findFirst().orElseThrow();
        var f=new Fixture(h,entry.id());f.ammo(0,2);long before=f.ammo().total();
        var token=WeaponSubsistence.capture(f.p);var corpse=f.corpse();
        int moved=WeaponSubsistence.killed(f.p,token,corpse);
        check(h,moved==Math.min(2,f.reward()),"Available reserves bound refill");
        check(h,f.ammo().total()==before&&f.ammo().rounds()==moved&&f.ammo().reserve()==2-moved,"Finite ammo conserved");
        f.ammo(0,0);check(h,WeaponSubsistence.killed(f.p,WeaponSubsistence.capture(f.p),f.corpse())==0,"Empty finite reserves never generate rounds");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void repeatedCorpseAcrossTokensAndFullMagazineCannotOverfill(GameTestHelper h){
        var f=new Fixture(h);f.ammo(0,0);var a=WeaponSubsistence.capture(f.p);var b=WeaponSubsistence.capture(f.p);var corpse=f.corpse();
        check(h,WeaponSubsistence.killed(f.p,a,corpse)==f.reward(),"First confirmed source corpse");
        check(h,WeaponSubsistence.killed(f.p,b,corpse)==0,"Same corpse does not reward another bullet token");
        f.ammo(f.profile.magazine(),0);check(h,WeaponSubsistence.killed(f.p,WeaponSubsistence.capture(f.p),f.corpse())==0,"Full magazine stays full");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void savedRollEditAndStackReplacementRevokeOldSource(GameTestHelper h){
        var f=new Fixture(h);f.ammo(0,0);var old=WeaponSubsistence.capture(f.p);
        WeaponPerks.clear(f.gun);WeaponPerks.select(f.gun,"subsistence");
        check(h,WeaponSubsistence.killed(f.p,old,f.corpse())==0,"Edit-away-and-back revokes original token");
        var token=WeaponSubsistence.capture(f.p);var copy=f.gun.copy();
        f.p.getInventory().setItem(f.p.getInventory().getSelectedSlot(),copy);WeaponSubsistence.update(f.p);
        check(h,WeaponSubsistence.killed(f.p,token,f.corpse())==0,"Persisted copied roll is not original runtime source");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void paidOwnedSourceMayRefillAfterStowButCleanupRevokes(GameTestHelper h){
        var f=new Fixture(h);f.ammo(0,0);var token=WeaponSubsistence.capture(f.p);
        int slot=f.p.getInventory().getSelectedSlot()==0?1:0;WeaponRuntime.selectedSlotChanging(f.p,slot);f.p.getInventory().setSelectedSlot(slot);
        WeaponSubsistence.update(f.p);
        check(h,WeaponSubsistence.killed(f.p,token,f.corpse())==f.reward(),"Owned/equipped original projectile source, not current hand");
        WeaponSubsistence.cleanup(f.p);
        check(h,WeaponSubsistence.killed(f.p,token,f.corpse())==0,"Lifecycle cleanup revokes paid source");h.succeed();
    }
}
