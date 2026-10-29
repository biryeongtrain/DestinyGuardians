package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponPerkHud;
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

/** Real paid production paths, server clocks and HUD graphs. No positive proc injection.
 * Each 48x8x48 structure keeps its 15m scan away from adjacent test entities.
 */
public final class DamageTraitsW109GameTests {
    private static final String FLOOR="destiny-test:w109_arena", ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why) { h.assertTrue(ok,Component.literal(why)); }
    private static void near(GameTestHelper h,float actual,float expected,String why) {
        check(h,Math.abs(actual-expected)<.025f,why+": expected "+expected+", got "+actual);
    }
    private static final class Fixture {
        final GameTestHelper h;
        final List<ServerPlayer> players=new ArrayList<>();
        final List<Husk> targets=new ArrayList<>();
        Fixture(GameTestHelper h) {
            this.h=h;
            TestCleanup.register(h,()->{
                targets.forEach(Husk::discard);
                players.forEach(p->{p.stopUsingItem();WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
            });
            h.onEachTick(()->players.forEach(TestPlayers::drain));
        }
        ServerPlayer player() {
            var p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(24,1,24),-90,0,"W109_"+UUID.randomUUID().toString().substring(0,8));
            p.setAttached(WeaponLoadout.ENABLED,true);p.setNoGravity(true);p.setOnGround(true);players.add(p);return p;
        }
        ItemStack equip(ServerPlayer p,String id,String perk) {
            var e=WeaponCatalog.find(id).orElseThrow();var gun=WeaponItems.create(e);
            if(perk!=null)check(h,WeaponPerks.select(gun,perk),"Exact optional source socket "+id+"/"+perk);
            var profile=WeaponProfile.forEntry(e);WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),profile.reserve()));
            int slot=WeaponCharacteristics.of(e).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);return gun;
        }
        Husk target(double x,double z) {
            var t=h.spawn(EntityTypes.HUSK,new Vec3(x,1.8,z));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.setPersistenceRequired();
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(1000);return t;
        }
        float fire(ServerPlayer p,Husk target) {
            p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
            var gun=p.getMainHandItem();var profile=WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());
            int before=WeaponItems.magazine(gun,profile).rounds();float hp=target.getHealth();
            check(h,profile.chargeTicks()==0&&WeaponRuntime.beginUse(p),"Real paid instant trigger");WeaponRuntime.releaseUse(p,gun);
            check(h,WeaponItems.magazine(gun,profile).rounds()==before-1,"Exactly one paid cartridge");
            float damage=hp-target.getHealth();check(h,damage>0,"Production target took actual HP damage");return damage;
        }
        void chain(ServerPlayer p,int next,Runnable done) {
            var t=target(30,24);fire(p,t);t.discard();
            if(next==3)done.run();else h.runAfterDelay(6,()->chain(p,next+1,done));
        }
        void flanks() { target(24,29);target(24,19); }
    }
    private static long nodes(ServerPlayer p,String id) {
        return DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith(WeaponPerkHud.PREFIX+id+"_")).count();
    }

    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void exactEightEachNoDefaultsNoFamilyWideExpansion(GameTestHelper h) {
        var f=new Fixture(h);f.player();
        for(String trait:List.of("one_for_all","surrounded")) {
            int count=0;
            for(var e:WeaponCatalog.all()) {
                var gun=WeaponItems.create(e);check(h,WeaponPerks.selected(gun,trait).isEmpty(),"No auto equipped trait");
                boolean eligible=(trait.equals("one_for_all")?OneForAllProfile.rolls():SurroundedProfile.rolls()).stream().anyMatch(r->r.id().equals(e.id()));
                check(h,WeaponPerks.select(gun,trait)==eligible,"No socket broadening "+e.id());if(eligible)count++;
            }
            check(h,count==8,"Exactly eight pinned base sockets for "+trait);
        }h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void paidHitsActivateOnlyAfterThirdThenIncreaseActualDamageAndHud(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();f.equip(p,"ammit_ar2","one_for_all");
        var a=f.target(30,24);float baseline=f.fire(p,a);a.discard();
        check(h,WeaponOneForAll.progress(p)==1&&WeaponOneForAll.remaining(p)==0,"First distinct paid hit");
        h.runAfterDelay(6,()->{
            var b=f.target(30,24);near(h,f.fire(p,b),baseline,"Second hit unbuffed");b.discard();
            h.runAfterDelay(6,()->{
                var c=f.target(30,24);near(h,f.fire(p,c),baseline,"Triggering third hit unbuffed");c.discard();
                check(h,WeaponOneForAll.remaining(p)==200,"Actual ten-second window");CombatHud.update(p);
                check(h,nodes(p,"one_for_all")==6,"Six actual HUD nodes");
                h.runAfterDelay(6,()->{
                    var d=f.target(30,24);near(h,f.fire(p,d),baseline*1.35f,"Next paid emission 35 percent");
                    check(h,WeaponOneForAll.remaining(p)==194,"Damage does not refresh active clock");h.succeed();
                });
            });
        });
    }

    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void repeatedTargetNeverCountsThree(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();f.equip(p,"ammit_ar2","one_for_all");var t=f.target(30,24);f.fire(p,t);
        h.runAfterDelay(6,()->{f.fire(p,t);h.runAfterDelay(6,()->{f.fire(p,t);
            check(h,WeaponOneForAll.progress(p)==1&&WeaponOneForAll.remaining(p)==0,"One enemy UUID remains one target");h.succeed();});});
    }

    @GameTest(structure=FLOOR,maxTicks=260,environment=ENV)
    public void actualServerExpiryRemovesHudWithoutAnotherHit(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();f.equip(p,"ammit_ar2","one_for_all");
        f.chain(p,1,()->{
            h.runAfterDelay(199,()->check(h,WeaponOneForAll.remaining(p)==1,"Last live buff tick"));
            h.runAfterDelay(200,()->{check(h,WeaponOneForAll.remaining(p)==0,"Exact expiry");CombatHud.update(p);
                check(h,nodes(p,"one_for_all")==0,"Expired HUD fully removed");h.succeed();});
        });
    }

    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void editedCapturedTokenCannotSeedNewSelection(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"ammit_ar2","one_for_all");
        var old=WeaponOneForAll.capture(p);WeaponPerks.clear(gun);WeaponPerks.select(gun,"one_for_all");
        var t=f.target(30,24);WeaponOneForAll.confirmed(p,old,t); // Negative stale-token injection only.
        check(h,WeaponOneForAll.progress(p)==0,"Captured pre-edit source is permanently invalid");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=70,environment=ENV)
    public void paidGoldtuskCleaveCountsThreeButNotSameSwingDamage(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"goldtusk","one_for_all");
        var a=f.target(25.6,23.6);var b=f.target(25.6,24);var c=f.target(25.6,24.4);
        int before=WeaponItems.magazine(gun,WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow())).rounds();
        check(h,WeaponRuntime.onPunch(p),"Production sword input accepted");
        h.runAfterDelay(15,()->{
            check(h,a.getHealth()<1000&&b.getHealth()<1000&&c.getHealth()<1000,"Actual cleave damage to three enemies");
            near(h,1000-a.getHealth(),1000-c.getHealth(),"All targets use same pre-proc snapshot");
            check(h,WeaponOneForAll.remaining(p)>180,"Paid sword hits proc actual buff");
            check(h,WeaponItems.magazine(gun,WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow())).rounds()==before-1,"Sword costs one ammo");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=70,environment=ENV)
    public void surroundedPaidGunDamageUsesFortyPercentAndPureHud(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"steelfeather_repeater",null);var t=f.target(30,24);f.flanks();
        float base=f.fire(p,t);check(h,!WeaponSurrounded.active(p),"Unselected remains inert");
        h.runAfterDelay(6,()->{
            check(h,WeaponPerks.select(gun,"surrounded"),"Select source trait");WeaponRuntime.tickPlayer(p);
            near(h,f.fire(p,t),base*1.4f,"Actual ranged damage gets 40 percent");
            CombatHud.update(p);check(h,WeaponSurrounded.active(p)&&nodes(p,"surrounded")==2,"Actual non-timed proximity HUD");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=70,environment=ENV)
    public void surroundedThresholdLossStartsThirtyTickLingerAndStowClears(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();f.equip(p,"hammerhead","surrounded");
        f.target(30,24);f.target(24,29);var third=f.target(24,19);WeaponSurrounded.update(p);
        check(h,WeaponSurrounded.active(p),"Three loaded enemies activate");third.discard();WeaponSurrounded.update(p);
        h.runAfterDelay(29,()->check(h,WeaponSurrounded.active(p),"Linger tick29 remains live"));
        h.runAfterDelay(30,()->{
            check(h,!WeaponSurrounded.active(p),"Linger ends at30");f.target(24,19);WeaponSurrounded.update(p);
            check(h,WeaponSurrounded.active(p),"Threshold reacquisition");
            p.getInventory().setSelectedSlot(0);WeaponSurrounded.update(p);check(h,!WeaponSurrounded.active(p),"Stow clears immediately");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void fifteenMeterFootSphereIncludesBoundaryNotJustOldEightMeters(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();f.equip(p,"hammerhead","surrounded");
        // Align feet for an independent exact horizontal boundary measurement.
        var a=f.target(39,24);var b=f.target(24,39);var c=f.target(9,24);
        for(var t:List.of(a,b,c))t.setPos(t.getX(),p.getY(),t.getZ());
        WeaponSurrounded.update(p);check(h,WeaponSurrounded.active(p),"Exactly15m is inside; source is not obsolete8m");
        WeaponSurrounded.changed(p,p.getMainHandItem());c.setPos(c.getX()-.001,c.getY(),c.getZ());WeaponSurrounded.update(p);
        check(h,!WeaponSurrounded.active(p),"15.001m fails threshold with no prior linger");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void surroundedSwordSnapshotIsThirtyFiveNotFortyPercent(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();f.equip(p,"falling_guillotine","surrounded");
        f.target(30,24);f.flanks();near(h,WeaponSurrounded.capture(p).multiplier(),1.35f,"Exact selected sword exception");
        WeaponPerks.clear(p.getMainHandItem());near(h,WeaponSurrounded.capture(p).multiplier(),1,"Cleared trait inert");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void paidWaveHitsThreeAfterStowCreditOnlyOriginalStillOwnedSource(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"dimensional_hypotrochoid","one_for_all");
        var a=f.target(29,24);var b=f.target(31,24);var c=f.target(33,24);
        for(var t:List.of(a,b,c))t.setPos(t.getX(),p.getY(),t.getZ());
        p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(35);WeaponAiming.cleanup(p);WeaponAiming.tick(p);
        var profile=WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());int before=WeaponItems.magazine(gun,profile).rounds();
        check(h,WeaponRuntime.beginUse(p),"Production paid wave launch");WeaponRuntime.releaseUse(p,gun);
        check(h,WeaponItems.magazine(gun,profile).rounds()==before-1,"Wave pays one cartridge");
        p.getInventory().setSelectedSlot(0);WeaponRuntime.tickPlayer(p);
        h.runAfterDelay(40,()->{
            check(h,a.getHealth()<1000&&b.getHealth()<1000&&c.getHealth()<1000,"One real floor wave hits three separate enemies");
            check(h,WeaponOneForAll.remaining(p)==0,"Stowed source never leaks held HUD buff");
            p.getInventory().setSelectedSlot(2);WeaponRuntime.tickPlayer(p);
            check(h,p.getMainHandItem()==gun&&WeaponOneForAll.remaining(p)>150,"Only original retained source receives confirmed wave proc");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void surroundedPaidSwordLightDamageUsesSwordException(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"falling_guillotine",null);var t=f.target(25.6,24);f.flanks();
        check(h,WeaponRuntime.onPunch(p),"Unselected production sword light");
        h.runAfterDelay(15,()->{
            float base=1000-t.getHealth();check(h,base>0,"Unselected paid sword dealt damage");
            check(h,WeaponPerks.select(gun,"surrounded"),"Exact sword trait socket");
            // Combo2 has the same authored base multiplier as combo1; wait the genuine cadence.
            h.runAfterDelay(20,()->{
                float before=t.getHealth();check(h,WeaponRuntime.onPunch(p),"Selected production sword light");
                h.runAfterDelay(15,()->{near(h,before-t.getHealth(),base*1.35f,"Actual paid sword uses35 not40 percent");h.succeed();});
            });
        });
    }

    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void emptySwordWeakCleaveCannotProcPaidWeaponTrait(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"goldtusk","one_for_all");
        var profile=WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());WeaponItems.save(gun,new WeaponMagazine(profile,0,0));
        var a=f.target(25.6,23.6);var b=f.target(25.6,24);var c=f.target(25.6,24.4);
        check(h,WeaponRuntime.onPunch(p),"Real empty weak sword input");
        h.runAfterDelay(15,()->{
            check(h,a.getHealth()<1000&&b.getHealth()<1000&&c.getHealth()<1000,"Weak unpaid cleave still damages");
            check(h,WeaponOneForAll.progress(p)==0&&WeaponOneForAll.remaining(p)==0,"No paid emission token from empty sword");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=60,environment=ENV)
    public void copiedItemCannotInheritActiveSourceBuff(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"ammit_ar2","one_for_all");
        f.chain(p,1,()->{
            check(h,WeaponOneForAll.remaining(p)==200,"Original identity proc");var copy=gun.copy();
            int slot=WeaponCharacteristics.of(WeaponItems.entry(gun).orElseThrow()).slot().hotbar();
            p.getInventory().setItem(slot,copy);WeaponRuntime.tickPlayer(p);
            check(h,WeaponOneForAll.remaining(p)==0,"Selected trait copies but ephemeral buff does not");
            CombatHud.update(p);check(h,nodes(p,"one_for_all")==0,"No stale original HUD on copied source");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void actualLethalHitsStillCountThreeDistinctVictims(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();f.equip(p,"ammit_ar2","one_for_all");
        Runnable third=()->{var t=f.target(30,24);t.setHealth(1);f.fire(p,t);
            check(h,t.isDeadOrDying()&&WeaponOneForAll.remaining(p)==200,"Third lethal confirmed by post-damage UUID");h.succeed();};
        var first=f.target(30,24);first.setHealth(1);f.fire(p,first);first.discard();
        h.runAfterDelay(6,()->{var second=f.target(30,24);second.setHealth(1);f.fire(p,second);second.discard();h.runAfterDelay(6,third);});
    }

    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void sameTickNativeStowClearsLiveBuffButKeepsPaidSnapshot(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player();var gun=f.equip(p,"hammerhead","surrounded");
        f.target(30,24);f.target(24,29);var third=f.target(24,19);var token=WeaponSurrounded.capture(p);
        check(h,WeaponSurrounded.active(p),"Original threshold active");near(h,token.multiplier(),1.4f,"Original emission snapshot");
        third.discard();WeaponRuntime.selectedSlotChanging(p,0);p.getInventory().setSelectedSlot(0);
        WeaponRuntime.selectedSlotChanging(p,2);p.getInventory().setSelectedSlot(2);
        check(h,p.getMainHandItem()==gun&&!WeaponSurrounded.active(p),"Accepted same-tick stow cannot preserve live linger");
        near(h,token.multiplier(),1.4f,"Already-paid snapshot remains source-owned after stow");
        WeaponSurrounded.update(p);check(h,!WeaponSurrounded.active(p),"No phantom linger after returning below threshold");
        WeaponPerks.clear(gun);near(h,token.multiplier(),1,"Real edit permanently revokes old source");h.succeed();
    }

}
