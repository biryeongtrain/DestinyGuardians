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
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Actual paid server gameplay and real HUD registry; no native input or framebuffer claim. */
public final class PerksW202GameTests {
    private static void check(GameTestHelper h,boolean ok,String why) { h.assertTrue(ok,Component.literal(why)); }
    private static void hud(GameTestHelper h,ServerPlayer p,String id,boolean active) {
        CombatHud.update(p);
        check(h,DisplayHud.getHuds(p).containsKey("destiny:hud_perk_"+id+"_label")==active,"Actual HUD "+id+" visibility="+active);
    }
    private static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final List<Husk> targets=new ArrayList<>();
        final ItemStack gun;final WeaponCatalog.Entry entry;final WeaponProfile profile;final int slot;
        Fixture(GameTestHelper h,String id,String perk) {
            this.h=h;p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W202_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,false);
            entry=WeaponCatalog.find(id).orElseThrow();gun=WeaponItems.create(entry);
            check(h,WeaponPerks.select(gun,perk),"Exact current base socket "+id+"/"+perk);
            profile=WeaponProfile.forEntry(entry);WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),profile.reserve()));
            slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);tick();
            TestCleanup.register(h,()->{targets.forEach(Husk::discard);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void tick() { WeaponRuntime.tickPlayer(p);TestPlayers.drain(p); }
        void face() {p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);}
        Husk target(float health,boolean precision) {
            var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,precision?1:1.8,6));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(health);return t;
        }
        int rounds() {return WeaponItems.magazine(gun,profile).rounds();}
        void fire() {face();check(h,WeaponRuntime.beginUse(p),"Production paid trigger accepted");WeaponRuntime.releaseUse(p,gun);TestPlayers.drain(p);}
        void select(int s) {p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(s));TestPlayers.drain(p);}
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=50)
    public void actualBodyHitEnablesLaterPrecisionBoltsAndShortHudExpiresWithoutReaderRefresh(GameTestHelper h) {
        var f=new Fixture(h,"high_albedo","headseeker");
        WeaponItems.save(f.gun,new WeaponMagazine(f.profile,3,0));var body=f.target(1000,false);
        check(h,WeaponHeadseeker.remaining(f.p)==0,"Equip/HUD polling cannot pre-arm Headseeker");hud(h,f.p,"headseeker",false);
        f.fire();check(h,body.getHealth()<1000&&f.rounds()==2,"First real direct body hit spends one cartridge");
        check(h,WeaponHeadseeker.remaining(f.p)>0,"Positive actual nonprecision damage arms short window");hud(h,f.p,"headseeker",true);
        body.discard();var head=f.target(1000,true);f.face();h.onEachTick(f::tick);
        h.runAfterDelay(4,()->{
            int bolts=2-f.rounds();double unbuffed=bolts*f.profile.damage()*WeaponBallistics.of(f.entry).precision();
            check(h,bolts>0&&1000-head.getHealth()>unbuffed+.01,"Later paid burst bolts use increased precision BONUS on actual target");
            int remaining=WeaponHeadseeker.remaining(f.p);
            for(int i=0;i<15;i++)check(h,WeaponHeadseeker.remaining(f.p)==remaining,"Observer cannot refresh short duration");
        });
        h.runAfterDelay(18,()->{check(h,WeaponHeadseeker.remaining(f.p)==0,"Body-hit window expires despite polling");hud(h,f.p,"headseeker",false);h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=45)
    public void actualSlotAndInventoryReplacementCannotResurrectHeadseekerWindow(GameTestHelper h) {
        var f=new Fixture(h,"high_albedo","headseeker");f.target(1000,false);f.fire();
        check(h,WeaponHeadseeker.remaining(f.p)>0,"Actual body damage arms original");
        int other=f.slot==0?1:0;f.select(other);f.select(f.slot);
        check(h,WeaponHeadseeker.remaining(f.p)==0,"Native same-tick away/back cancels weapon-specific short state");hud(h,f.p,"headseeker",false);
        f.p.getInventory().setItem(f.slot,f.gun.copy());
        check(h,WeaponHeadseeker.remaining(f.p)==0,"Equal copied item has no source episode");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=70)
    public void paidShotgunFinalBlowSpeedsOtherEquippedWeaponsAndKeepsHudAfterStow(GameTestHelper h) {
        var f=new Fixture(h,"mindbender_s_ambition_adept","steady_hands");
        var ammit=WeaponItems.create(WeaponCatalog.find("ammit_ar2").orElseThrow());
        int other=f.slot==0?1:0;f.p.getInventory().setItem(other,ammit);
        int baseline=WeaponSteadyHands.handlingTicks(f.p,ammit,true,999);
        check(h,baseline==999&&WeaponSteadyHands.remaining(f.p)==0,"No free handling before actual final blow");
        var target=f.target(1,false);int ammo=f.rounds();f.fire();
        check(h,!target.isAlive()&&f.rounds()==ammo-1,"Actual pellet final blow has exactly one paid cartridge");
        int active=WeaponSteadyHands.remaining(f.p);check(h,active>130&&active<=170,"First paid kill owns8.5second window");
        hud(h,f.p,"steady_hands",true);
        int boosted=WeaponSteadyHands.handlingTicks(f.p,ammit,true,999);
        check(h,boosted>0&&boosted<WeaponHandlingProfile.of(WeaponItems.entry(ammit).orElseThrow()).readyTicks(),"Other equipped weapon receives actual handling result");
        f.select(other);f.tick();
        check(h,WeaponSteadyHands.remaining(f.p)>0,"Actual source stow retains character-wide window");hud(h,f.p,"steady_hands",true);
        check(h,WeaponSteadyHands.handlingTicks(f.p,ammit,true,999)==boosted,"Other held weapon retains original buff");
        var original=f.gun.copy();
        for(int i=0;i<20;i++){WeaponSteadyHands.remaining(f.p);CombatHud.update(f.p);}
        check(h,ItemStack.matches(original,f.gun),"Handling/HUD observation never changes source ammo");
        WeaponPerks.clear(f.gun);
        check(h,WeaponSteadyHands.remaining(f.p)==0&&WeaponSteadyHands.handlingTicks(f.p,ammit,true,999)==999,"Actual stowed source edit revokes own state");
        hud(h,f.p,"steady_hands",false);h.succeed();
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=65)
    public void laterActualPaidKillRefreshesSixPointFiveSecondsAndDeniedDamageDoesNotActivate(GameTestHelper h) {
        var f=new Fixture(h,"mindbender_s_ambition_adept","steady_hands");var denied=f.target(1000,false);
        denied.setPermanentlyInvulnerable(true);f.fire();
        check(h,WeaponSteadyHands.remaining(f.p)==0,"Paid denied hit is not a weapon final blow");denied.discard();h.onEachTick(f::tick);
        int gap=(int)Math.ceil(f.profile.cadenceTicks())+2;
        h.runAfterDelay(gap,()->{
            var first=f.target(1,false);f.fire();check(h,!first.isAlive()&&WeaponSteadyHands.remaining(f.p)>130,"First actual kill starts170tick window");first.discard();
            h.runAfterDelay(gap,()->{
                var second=f.target(1,false);f.fire();check(h,!second.isAlive(),"Second actual paid final blow");
                check(h,WeaponSteadyHands.remaining(f.p)>0&&WeaponSteadyHands.remaining(f.p)<=130,"Additional kill refreshes130ticks rather than first170");
                h.succeed();
            });
        });
    }
}
