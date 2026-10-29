package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
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

/** Real server ability activation, paid shot and accepted reload, NOT native input/pixels. */
public final class SurplusW183GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    /** Production left-click ADS; does not bypass the three-tick toggle debounce. */
    private static void ads(net.minecraft.server.level.ServerPlayer p, boolean requested) {
        if (WeaponAiming.requested(p) != requested) kim.biryeong.destiny.input.InputRouter.onPunch(p);
    }
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="surplus";
    static final List<AbilitySlot> POWERED=List.of(AbilitySlot.GRENADE,AbilitySlot.MELEE,AbilitySlot.CLASS_ABILITY);
    static void check(GameTestHelper h,boolean ok,String why){h.assertTrue(ok,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final WeaponCatalog.Entry entry;final WeaponProfile profile;final ItemStack gun;
        final List<Husk> mobs=new ArrayList<>();
        Fixture(GameTestHelper h){this(h,"ammit_ar2");}
        Fixture(GameTestHelper h,String weapon){
            this.h=h;entry=WeaponCatalog.find(weapon).orElseThrow();profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W183_"+UUID.randomUUID().toString().substring(0,8));
            p.setNoGravity(true);p.setOnGround(true);Guardians.runtime(p);p.setAttached(WeaponLoadout.ENABLED,true);
            gun=WeaponItems.create(entry);check(h,WeaponPerks.select(gun,ID),"Official optional Surplus selected");
            WeaponItems.save(gun,new WeaponMagazine(profile,1,200));
            int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            tick();h.onEachTick(()->tick());TestCleanup.register(h,()->{mobs.forEach(Husk::discard);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void tick(){WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);}
        void charged(int n){for(int i=0;i<POWERED.size();i++)Guardians.data(p).setCooldown(POWERED.get(i),i<n?0:200);}
        void hud(int n){CombatHud.update(p);var keys=DisplayHud.getHuds(p).keySet();check(h,keys.stream().filter(x->x.startsWith("destiny:hud_perk_surplus_")).count()==(n==0?0:4),"Actual count has exactly four nodes, no timer");}
        Husk target(){var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,1.8,6));t.setNoAi(true);t.setNoGravity(true);t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(1000);mobs.add(t);return t;}
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV) public void actualAbilityActivationAndCooldownRecoveryDriveCountHud(GameTestHelper h){
        var f=new Fixture(h);f.charged(3);check(h,WeaponSurplus.stacks(f.p)==3,"Three real equipped charged powered slots");f.hud(3);
        check(h,AbilityService.use(f.p,AbilitySlot.GRENADE)==AbilityService.Result.OK,"Actual registered grenade activation succeeds");
        check(h,Guardians.data(f.p).cooldown(AbilitySlot.GRENADE)>0&&WeaponSurplus.stacks(f.p)==2,"Successful ability consumes ready charge immediately");f.hud(2);
        Guardians.data(f.p).setCooldown(AbilitySlot.GRENADE,1);Guardians.data(f.p).tickCooldowns();
        check(h,WeaponSurplus.stacks(f.p)==3,"Actual cooldown tick reaches ready without fabricated proc timer");f.hud(3);
        for(int n=0;n<=3;n++){f.charged(n);check(h,WeaponSurplus.stacks(f.p)==n,"Real cooldown map tier "+n);f.hud(n);}h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV) public void superJumpWrongSlotUnknownAndClassNoneDoNotInventCharges(GameTestHelper h){
        var f=new Fixture(h);f.charged(0);var d=Guardians.data(f.p);d.setSuperEnergy(1);d.setCooldown(AbilitySlot.SUPER,0);d.setCooldown(AbilitySlot.JUMP,0);
        check(h,WeaponSurplus.stacks(f.p)==0,"Super and jump cannot count");
        var original=d.loadout().orElseThrow();var map=new EnumMap<AbilitySlot,Identifier>(AbilitySlot.class);map.putAll(original.abilities());
        map.put(AbilitySlot.GRENADE,original.get(AbilitySlot.SUPER));map.put(AbilitySlot.MELEE,Identifier.parse("destiny:not_registered"));map.remove(AbilitySlot.CLASS_ABILITY);
        d.setLoadout(GuardianClass.HUNTER,new Loadout(map));f.charged(3);check(h,WeaponSurplus.stacks(f.p)==0,"Known wrong slot, unknown and missing ability are not powered charges");f.hud(0);
        d.setLoadout(GuardianClass.HUNTER,original);d.setGuardianClass(GuardianClass.NONE);check(h,WeaponSurplus.stacks(f.p)==0,"No active class");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=120,environment=ENV) public void acceptedReloadKeepsItsPaidPlanWhenAbilityReadinessChanges(GameTestHelper h){
        var f=new Fixture(h);f.charged(3);var base=WeaponReloadPolicy.forEntry(f.entry,f.profile.reloadTicks(),f.profile.shellReload());
        var accepted=WeaponSurplus.plan(f.p,f.entry,base);check(h,accepted.firstTicks()<base.firstTicks(),"Real tier3 stat shortens reload");
        check(h,WeaponRuntime.reload(f.p),"Actual reload accepted");check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==accepted.firstTicks(),"Runtime uses Surplus accepted plan");
        // Deliberate server cooldown fixture, not an ability input: real ability use legitimately cancels reload.
        f.charged(0);check(h,WeaponSurplus.stacks(f.p)==0,"Live readiness changed");f.hud(0);
        h.startSequence().thenIdle(1).thenExecute(()->check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==accepted.firstTicks(),"Already accepted reload is not retimed"));
        h.startSequence().thenIdle(accepted.firstTicks()+2).thenExecute(()->{check(h,!WeaponRuntime.reloading(f.p)&&WeaponItems.magazine(f.gun,f.profile).rounds()==f.profile.magazine(),"Original funded magazine transfer and full recovery complete");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV) public void actualPaidEmissionUsesStabilityWithoutFreeDamageOrAmmo(GameTestHelper h){
        var f=new Fixture(h);f.charged(3);var t=f.target();float before=t.getHealth();int rounds=WeaponItems.magazine(f.gun,f.profile).rounds();
        f.p.setYRot(-90);f.p.setYHeadRot(-90);f.p.setXRot(0);WeaponAiming.cleanup(f.p);WeaponAiming.tick(f.p);
        check(h,beginUse(f.p),"Real trigger accepted");WeaponRuntime.releaseUse(f.p,f.gun);
        check(h,WeaponItems.magazine(f.gun,f.profile).rounds()==rounds-1,"One real funded cartridge");
        var aim=WeaponAimProfile.of(f.entry);check(h,Math.abs(f.p.getXRot()+RapidHitStability.kick(aim,25))<.0001,"Actual recoil uses sourced tier3 stability25");
        check(h,Math.abs(WeaponAiming.bloom(f.p)-RapidHitStability.bloom(aim,25))<.00001,"Actual bloom uses stability, not invented accuracy scalar");
        var ballistics=WeaponAiming.ballistics(f.p,f.entry);float expected=ballistics.damage(f.profile.damage(),6,false);
        check(h,before-t.getHealth()>0&&Math.abs((before-t.getHealth())-expected)<.01,"Surplus grants no raw damage multiplier");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV) public void actualAdsAndEquippedIncomingOutgoingTimingUseLiveHandling(GameTestHelper h){
        var f=new Fixture(h);f.charged(3);int baseAds=SnapshotAimProfile.enterTicks(f.gun);
        int enter=WeaponSurplus.adsTicks(f.p,f.entry,baseAds,true);check(h,enter<baseAds,"Sourced handling shortens ADS");
        WeaponAiming.cleanup(f.p);ads(f.p,true);WeaponAiming.tick(f.p);
        check(h,Math.abs(WeaponAiming.progress(f.p)-1f/enter)<.0001,"Actual first ADS tick uses Surplus wrapper");ads(f.p,false);
        var handling=WeaponHandlingProfile.of(f.entry);int stow=WeaponSurplus.handlingTicks(f.p,f.gun,false,handling.stowTicks()),ready=WeaponSurplus.handlingTicks(f.p,f.gun,true,handling.readyTicks());
        check(h,stow<=handling.stowTicks()&&ready<handling.readyTicks(),"Handling raw-stat ready/stow");
        WeaponRuntime.selectedSlotChanging(f.p,7);f.p.getInventory().setSelectedSlot(7);
        check(h,WeaponSurplus.stacks(f.p)==0,"Unarmed held HUD has no source");
        check(h,WeaponSurplus.handlingTicks(f.p,f.gun,true,handling.readyTicks())==ready,"Genuine owned equipped incoming source can ready before selection");
        f.p.getInventory().setSelectedSlot(WeaponCharacteristics.of(f.entry).slot().hotbar());WeaponHandling.update(f.p);
        check(h,WeaponHandling.remaining(f.p)==stow+ready,"Actual outgoing+incoming acceptance uses live ability state for both sources");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV) public void sourceAuthoritySuperAndSocketEditsAreReadOnlyAndImmediate(GameTestHelper h){
        var f=new Fixture(h);f.charged(3);int slot=f.p.getInventory().getSelectedSlot();var copy=f.gun.copy();
        check(h,WeaponSurplus.handlingTicks(f.p,copy,true,999)==999,"Unowned equal-data copy cannot claim equipped handling");
        var d=Guardians.data(f.p).cooldownsView();var tag=f.gun.copy();for(int i=0;i<10;i++)check(h,WeaponSurplus.stacks(f.p)==3,"Repeated pure query");
        check(h,d.equals(Guardians.data(f.p).cooldownsView())&&ItemStack.matches(tag,f.gun),"Query neither consumes charge nor edits item");
        var runtime=Guardians.runtime(f.p);runtime.superSession=new SuperSession(){public boolean tick(){return true;}public void primary(){}public void end(){}public float remaining(){return 1;}};
        check(h,WeaponSurplus.stacks(f.p)==0,"Super context excludes weapon handling bonus");f.hud(0);runtime.superSession=null;
        WeaponPerks.clear(f.gun);check(h,WeaponSurplus.stacks(f.p)==0,"Socket clear removes live bonus without a session cleanup");
        check(h,WeaponPerks.select(f.gun,ID),"Official source can be selected again");check(h,WeaponSurplus.stacks(f.p)==3,"Real readiness can be observed anew");
        f.p.getInventory().setItem(slot,ItemStack.EMPTY);check(h,WeaponSurplus.stacks(f.p)==0,"Original removed from inventory cannot keep HUD");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV) public void legalSnapshotPairPreservesScalarWithRealHandlingAndCount(GameTestHelper h){
        var f=new Fixture(h,"high_albedo");f.charged(3);int base=WeaponAimProfile.of(f.entry).transitionTicks();
        int surplusOnly=WeaponSurplus.adsTicks(f.p,f.entry,base,true);
        check(h,WeaponPerks.select(f.gun,SnapshotAimProfile.ID),"Official different socket Snapshot companion");
        check(h,WeaponPerks.selected(f.gun,ID).isPresent(),"Selecting legal companion preserves Surplus socket");
        int together=WeaponSurplus.adsTicks(f.p,f.entry,SnapshotAimProfile.enterTicks(f.gun),true);
        check(h,together<=surplusOnly&&together<=SnapshotAimProfile.enterTicks(f.gun),"Real Snapshot and handling do not erase one another");
        WeaponAiming.cleanup(f.p);ads(f.p,true);WeaponAiming.tick(f.p);
        check(h,Math.abs(WeaponAiming.progress(f.p)-1f/together)<.0001,"Actual ADS clock uses legal combined plan");
        f.hud(3);h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV) public void exactOptionalSocketsWithoutDefaultOrEnhancedGrant(GameTestHelper h){
        var ids=SurplusProfile.rolls().stream().map(WeaponPerks.Roll::id).collect(java.util.stream.Collectors.toSet());check(h,ids.size()==9,"Exact official base9");
        for(var e:WeaponCatalog.all()){var s=WeaponItems.create(e);check(h,WeaponPerks.selected(s,ID).isEmpty(),"No free default");check(h,WeaponPerks.select(s,ID)==ids.contains(e.id()),"Exact optional socket "+e.id());}h.succeed();
    }
}
