package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Scoped event/ownership/paid charge regressions. Numeric-only Rangefinder has source/path review.
 * These are headless server actions, not native input, screenshots or animation validation. */
public final class PerksW192GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    private static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why) { h.assertTrue(ok,Component.literal(why)); }
    private static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final List<Husk> targets=new ArrayList<>();
        ItemStack gun;WeaponCatalog.Entry entry;WeaponProfile profile;int slot;
        Fixture(GameTestHelper h) {
            this.h=h;p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W192_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,false);
            TestCleanup.register(h,()->{targets.forEach(Husk::discard);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void equip(String id,String perk) {
            entry=WeaponCatalog.find(id).orElseThrow();gun=WeaponItems.create(entry);
            check(h,WeaponPerks.select(gun,perk),"Exact base socket "+id+"/"+perk);
            profile=WeaponProfile.forEntry(entry);WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),0));
            slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            tick();
        }
        void tick() { WeaponRuntime.tickPlayer(p);TestPlayers.drain(p); }
        void select(int index) { p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(index));TestPlayers.drain(p); }
        Husk target(float hp,boolean precision) {
            var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,precision?1:1.8,6));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(hp);return t;
        }
        int rounds() { return WeaponItems.magazine(gun,profile).rounds(); }
        void face() { p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);p.getRandom().setSeed(0x5DEECE66DL); }
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=30)
    public void wellRoundedOnlySuccessfulAbilityUseCountsAndOwnedStowPreservesIt(GameTestHelper h) {
        var f=new Fixture(h);f.equip("ammit_ar2","well_rounded");var d=Guardians.data(f.p);
        d.setCooldown(AbilitySlot.GRENADE,20);
        check(h,AbilityService.use(f.p,AbilitySlot.GRENADE)==AbilityService.Result.COOLDOWN&&WeaponWellRounded.stacks(f.p)==0,"Rejected ability never grants a stack");
        d.setCooldown(AbilitySlot.GRENADE,0);
        check(h,AbilityService.use(f.p,AbilitySlot.GRENADE)==AbilityService.Result.OK&&WeaponWellRounded.stacks(f.p)==1,"Successful paid grenade grants one stack");
        check(h,AbilityService.use(f.p,AbilitySlot.GRENADE)==AbilityService.Result.BUSY&&WeaponWellRounded.stacks(f.p)==1,"Active grenade recovery rejects duplicate use without a stack");
        int other=f.slot==0?1:0;f.p.getInventory().setItem(other,new ItemStack(Items.STONE));f.select(other);f.tick();
        check(h,WeaponWellRounded.stacks(f.p)==0&&WeaponWellRounded.ownedStacks(f.p,f.gun)==1,"Stow preserves owned timer but never affects another hand");
        f.select(f.slot);f.tick();check(h,WeaponWellRounded.stacks(f.p)==1,"Return to original source preserves active grant");
        var copy=f.gun.copy();f.p.getInventory().setItem(f.slot,copy);WeaponWellRounded.update(f.p);
        check(h,WeaponWellRounded.stacks(f.p)==0&&WeaponWellRounded.ownedStacks(f.p,f.gun)==0,"Detached copies and lost originals cannot inherit runtime buff");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=30)
    public void wellRoundedSuperUseReachesCapAndSurvivesSuperLifecycle(GameTestHelper h) {
        var f=new Fixture(h);f.equip("ammit_ar2","well_rounded");var d=Guardians.data(f.p);d.setSuperEnergy(0);
        check(h,AbilityService.use(f.p,AbilitySlot.SUPER)==AbilityService.Result.NOT_READY&&WeaponWellRounded.ownedStacks(f.p,f.gun)==0,"Unready super gives no credit");
        d.setSuperEnergy(1);
        check(h,AbilityService.use(f.p,AbilitySlot.SUPER)==AbilityService.Result.OK&&d.superEnergy()==0,"Production super activated and paid");
        check(h,AbilityService.inSuper(f.p)&&WeaponWellRounded.ownedStacks(f.p,f.gun)==2,"Accepted source receives two stacks through super activation");
        WeaponWellRounded.update(f.p);check(h,WeaponWellRounded.stacks(f.p)==0&&WeaponWellRounded.ownedStacks(f.p,f.gun)==2,"Super masks weapon effects without erasing deadline");
        AbilityService.endSuper(f.p);check(h,WeaponWellRounded.stacks(f.p)==2,"Return from super retains timed source");
        WeaponPerks.clear(f.gun);check(h,WeaponWellRounded.stacks(f.p)==0,"Socket edit revokes live source");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=30)
    public void wellRoundedPoweredMeleeNeedsRealLossAndDeduplicatesAcceptedContact(GameTestHelper h) {
        var f=new Fixture(h);f.equip("ammit_ar2","well_rounded");var token=MeleeWeaponTraits.accepted(f.p);
        check(h,WeaponWellRounded.stacks(f.p)==0,"Accepted input alone gives nothing");
        var t=f.target(100,false);t.setPermanentlyInvulnerable(true);
        MeleeWeaponTraits.poweredDamage(f.p.level(),f.p,t,1,Element.SOLAR,token);
        check(h,WeaponWellRounded.stacks(f.p)==0,"Rejected actual damage gives no credit");
        t.setPermanentlyInvulnerable(false);
        MeleeWeaponTraits.poweredDamage(f.p.level(),f.p,t,1,Element.SOLAR,token);
        check(h,t.getHealth()<100&&WeaponWellRounded.stacks(f.p)==1,"Positive direct powered melee grants one");
        MeleeWeaponTraits.poweredDamage(f.p.level(),f.p,t,1,Element.SOLAR,token);
        check(h,WeaponWellRounded.stacks(f.p)==1,"Repeated callback/contact on same accepted target cannot duplicate");
        var next=MeleeWeaponTraits.accepted(f.p);MeleeWeaponTraits.poweredDamage(f.p.level(),f.p,t,1,Element.SOLAR,next);
        check(h,WeaponWellRounded.stacks(f.p)==2,"New actual melee event on same target can stack");
        WeaponRuntime.cleanup(f.p);check(h,WeaponWellRounded.stacks(f.p)==0,"Lifecycle cleanup removes active and pending sources");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=30)
    public void encorePaidPrecisionKillStacksAndStowPreservesOnlyOriginalSource(GameTestHelper h) {
        var f=new Fixture(h);f.equip("fixed_odds","encore");var corpse=f.target(1,true);int before=f.rounds();f.face();
        check(h,beginUse(f.p),"Production paid trigger accepted");WeaponRuntime.releaseUse(f.p,f.gun);
        check(h,!corpse.isAlive()&&f.rounds()==before-1&&WeaponEncore.stacks(f.p)==2,"Actual precision final blow grants two on one paid shot");
        int other=f.slot==0?1:0;f.p.getInventory().setItem(other,new ItemStack(Items.STONE));f.select(other);f.tick();
        check(h,WeaponEncore.stacks(f.p)==0,"Stowed buff cannot leak to other hand");f.select(f.slot);f.tick();
        check(h,WeaponEncore.stacks(f.p)==2,"Ordinary stow preserves original live stacks");
        WeaponPerks.clear(f.gun);check(h,WeaponEncore.stacks(f.p)==0,"Exact socket edit revokes credited stack");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=155)
    public void backupPlanPaidChargeKeepsAcceptedPowerAndDeadlineAcrossExpiry(GameTestHelper h) {
        var f=new Fixture(h);f.equip("line_in_the_sand","backup_plan");var t=f.target(1000,false);
        check(h,WeaponBackupPlan.remaining(f.p)==0,"Initial unseen source has no invented stow history");
        int other=f.slot==0?1:0;f.p.getInventory().setItem(other,new ItemStack(Items.STONE));f.select(other);
        h.onEachTick(()->{f.face();f.tick();});
        h.startSequence().thenIdle(61).thenExecute(()->{
            f.select(f.slot);check(h,WeaponBackupPlan.remaining(f.p)>0,"Observed complete stow activates on real incoming ready");
            h.startSequence().thenIdle(39).thenExecute(()->{
                check(h,WeaponBackupPlan.remaining(f.p)==1,"Accepted charge begins on last active tick");
                int before=f.rounds();int duration=(int)Math.ceil(f.profile.chargeTicks()*.7);
                check(h,WeaponRuntime.heartbeatUse(f.p),"Production charged trigger accepted");
                for(int i=1;i<=duration;i++)h.startSequence().thenIdle(i).thenExecute(()->{f.face();WeaponRuntime.heartbeatUse(f.p);WeaponRuntime.continueUse(f.p);});
                h.startSequence().thenIdle(duration-1).thenExecute(()->check(h,f.rounds()==before,"Accepted charge cannot fire before its own deadline"));
                h.startSequence().thenIdle(duration+1).thenExecute(()->{
                    check(h,f.rounds()==before-1,"Immutable faster charge fires once after timed buff expired");
                    check(h,Math.abs((1000-t.getHealth())-f.profile.damage()*.8)<.01,"Accepted reduced damage survives expiry rather than reverting to full power");
                    WeaponRuntime.releaseUse(f.p,f.gun);h.succeed();
                });
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=145)
    public void backupPlanOnlyActualPaidLfrEmissionRefreshesItsWindow(GameTestHelper h) {
        var f=new Fixture(h);f.equip("line_in_the_sand","backup_plan");
        int other=f.slot==0?1:0;f.p.getInventory().setItem(other,new ItemStack(Items.STONE));f.select(other);
        h.onEachTick(()->{f.face();f.tick();});
        h.startSequence().thenIdle(61).thenExecute(()->{
            f.select(f.slot);int delay=(int)WeaponHandling.remaining(f.p)+1;
            h.startSequence().thenIdle(delay).thenExecute(()->{
                int remaining=WeaponBackupPlan.remaining(f.p),before=f.rounds();
                check(h,remaining>0&&WeaponRuntime.heartbeatUse(f.p),"Ready active LFR starts charging");
                check(h,WeaponBackupPlan.remaining(f.p)==remaining,"Starting input cannot refresh the paid-emission window");
                int duration=(int)Math.ceil(f.profile.chargeTicks()*.7);
                for(int i=1;i<=duration;i++)h.startSequence().thenIdle(i).thenExecute(()->{f.face();WeaponRuntime.heartbeatUse(f.p);WeaponRuntime.continueUse(f.p);});
                h.startSequence().thenIdle(duration+1).thenExecute(()->{
                    check(h,f.rounds()==before-1&&WeaponBackupPlan.remaining(f.p)>=39,"Actual paid LFR emission refreshes once");
                    WeaponRuntime.releaseUse(f.p,f.gun);WeaponPerks.clear(f.gun);
                    check(h,WeaponBackupPlan.remaining(f.p)==0,"Socket edit removes pending readiness state");h.succeed();
                });
            });
        });
    }
}
