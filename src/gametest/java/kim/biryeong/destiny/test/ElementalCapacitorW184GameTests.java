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

/** Actual server state/paid weapon operations; not native input, pixels or listening. */
public final class ElementalCapacitorW184GameTests {
    /** Fixed dispersion draw; actual payment, collision, recoil and perk credit remain production-owned. */
    private static boolean beginUse(net.minecraft.server.level.ServerPlayer p) {
        p.getRandom().setSeed(0x5DEECE66DL);
        return WeaponRuntime.beginUse(p);
    }
    /** Production left-click ADS; does not bypass the three-tick toggle debounce. */
    private static void ads(net.minecraft.server.level.ServerPlayer p, boolean requested) {
        if (WeaponAiming.requested(p) != requested) kim.biryeong.destiny.input.InputRouter.onPunch(p);
    }
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="elemental_capacitor";
    static void check(GameTestHelper h,boolean ok,String why){h.assertTrue(ok,Component.literal(why));}
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final WeaponCatalog.Entry entry;final WeaponProfile profile;final ItemStack gun;
        Fixture(GameTestHelper h){this(h,"steelfeather_repeater");}
        Fixture(GameTestHelper h,String id){
            this.h=h;entry=WeaponCatalog.find(id).orElseThrow();profile=WeaponProfile.forEntry(entry);
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W184_"+UUID.randomUUID().toString().substring(0,8));
            p.setNoGravity(true);p.setOnGround(true);Guardians.runtime(p);p.setAttached(WeaponLoadout.ENABLED,true);
            gun=WeaponItems.create(entry);check(h,WeaponPerks.select(gun,ID),"Exact official EC socket selection");
            WeaponItems.save(gun,new WeaponMagazine(profile,1,200));int slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            tick();h.onEachTick(()->tick());TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void tick(){WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);}
        void superElement(Element e){
            var d=Guardians.data(p);var map=new EnumMap<AbilitySlot,Identifier>(AbilitySlot.class);map.putAll(d.loadout().orElseThrow().abilities());
            var ability=AbilityRegistry.of(GuardianClass.HUNTER,AbilitySlot.SUPER).stream().filter(a->a.element()==e).findFirst().orElseThrow();map.put(AbilitySlot.SUPER,ability.id());d.setLoadout(GuardianClass.HUNTER,new Loadout(map));
        }
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV) public void mixedLoadoutUsesOnlyRegisteredEquippedSuperNotWeaponOrEnergy(GameTestHelper h){
        var f=new Fixture(h);var d=Guardians.data(f.p);
        for(var e:List.of(Element.SOLAR,Element.ARC,Element.VOID)){
            f.superElement(e);for(float energy:new float[]{0,1}){d.setSuperEnergy(energy);check(h,WeaponElementalCapacitor.element(f.p)==e,"Selected SUPER determines passive element at any energy");}
            check(h,AbilityService.equipped(f.p,AbilitySlot.GRENADE).orElseThrow().element()==Element.SOLAR,"Other powered abilities intentionally remain Solar");
        }
        check(h,WeaponElementalCapacitor.stabilityBonus(f.p)==20,"Void source adds exactly20");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV) public void wrongSlotUnknownMissingAndClassNoneNeverGrantElement(GameTestHelper h){
        var f=new Fixture(h);var d=Guardians.data(f.p);var original=d.loadout().orElseThrow();
        for(var wrong:List.of(original.get(AbilitySlot.GRENADE),Identifier.parse("destiny:unknown_super"))){
            var map=new EnumMap<AbilitySlot,Identifier>(AbilitySlot.class);map.putAll(original.abilities());map.put(AbilitySlot.SUPER,wrong);d.setLoadout(GuardianClass.HUNTER,new Loadout(map));check(h,WeaponElementalCapacitor.element(f.p)==Element.KINETIC,"Wrong registered slot or unknown SUPER cannot grant stats");
        }
        var map=new EnumMap<AbilitySlot,Identifier>(AbilitySlot.class);map.putAll(original.abilities());map.remove(AbilitySlot.SUPER);d.setLoadout(GuardianClass.HUNTER,new Loadout(map));check(h,WeaponElementalCapacitor.element(f.p)==Element.KINETIC,"Missing SUPER");d.setLoadout(GuardianClass.HUNTER,original);d.setGuardianClass(GuardianClass.NONE);check(h,WeaponElementalCapacitor.element(f.p)==Element.KINETIC,"No active guardian class");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=120,environment=ENV) public void solarAcceptedReloadStaysImmutableAcrossEquippedSuperChange(GameTestHelper h){
        var f=new Fixture(h);var base=WeaponReloadPolicy.forEntry(f.entry,f.profile.reloadTicks(),f.profile.shellReload());var solar=WeaponElementalCapacitor.plan(f.p,f.entry,base);check(h,solar.firstTicks()<base.firstTicks(),"Solar50 actual raw stat shortens reload");
        check(h,WeaponRuntime.reload(f.p),"Actual reload accepted");check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==solar.firstTicks(),"Runtime accepts exact Solar plan");f.superElement(Element.ARC);check(h,WeaponElementalCapacitor.plan(f.p,f.entry,base).equals(base),"Arc grants no invented reload bonus");
        h.startSequence().thenIdle(1).thenExecute(()->check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==solar.firstTicks(),"Already accepted reload not retimed by live element"));
        h.startSequence().thenIdle(solar.firstTicks()+2).thenExecute(()->{check(h,!WeaponRuntime.reloading(f.p)&&WeaponItems.magazine(f.gun,f.profile).rounds()==f.profile.magazine(),"Existing funded reload transfer completes");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV) public void arcActualAdsAndEquippedIncomingOutgoingHandling(GameTestHelper h){
        var f=new Fixture(h);f.superElement(Element.ARC);int base=WeaponAimProfile.of(f.entry).transitionTicks(),ticks=WeaponElementalCapacitor.adsTicks(f.p,f.entry,base,true);check(h,ticks<base,"Arc handling50 accelerates actual ADS");WeaponAiming.cleanup(f.p);ads(f.p,true);WeaponAiming.tick(f.p);check(h,Math.abs(WeaponAiming.progress(f.p)-1f/ticks)<.0001,"Actual ADS first tick uses EC outer wrapper");ads(f.p,false);
        var hp=WeaponHandlingProfile.of(f.entry);int stow=WeaponElementalCapacitor.handlingTicks(f.p,f.gun,false,hp.stowTicks()),ready=WeaponElementalCapacitor.handlingTicks(f.p,f.gun,true,hp.readyTicks());check(h,ready<hp.readyTicks(),"Arc ready shortened");
        WeaponRuntime.selectedSlotChanging(f.p,7);f.p.getInventory().setSelectedSlot(7);check(h,WeaponElementalCapacitor.element(f.p)==Element.KINETIC,"Held authority absent on nonweapon");check(h,WeaponElementalCapacitor.handlingTicks(f.p,f.gun,true,hp.readyTicks())==ready,"Genuine owned incoming object before selection still gets Arc");f.p.getInventory().setSelectedSlot(WeaponCharacteristics.of(f.entry).slot().hotbar());WeaponHandling.update(f.p);check(h,WeaponHandling.remaining(f.p)==stow+ready,"Actual stow and ready clock composed");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV) public void voidPaidEmissionUsesStabilityWithoutDamageOrAmmoGrant(GameTestHelper h){
        var f=new Fixture(h);f.superElement(Element.VOID);var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,1.8,6));t.setNoAi(true);t.setNoGravity(true);t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(1000);TestCleanup.register(h,t::discard);
        f.p.setYRot(-90);f.p.setYHeadRot(-90);f.p.setXRot(0);WeaponAiming.cleanup(f.p);WeaponAiming.tick(f.p);check(h,beginUse(f.p),"Real trigger accepted");WeaponRuntime.releaseUse(f.p,f.gun);check(h,WeaponItems.magazine(f.gun,f.profile).rounds()==0,"One funded cartridge only");
        var aim=WeaponAimProfile.of(f.entry);check(h,Math.abs(f.p.getXRot()+RapidHitStability.kick(aim,20))<.0001,"Actual Void20 recoil");check(h,Math.abs(WeaponAiming.bloom(f.p)-RapidHitStability.bloom(aim,20))<.00001,"Actual Void20 stability bloom, no independent accuracy multiplier");float expected=WeaponAiming.ballistics(f.p,f.entry).damage(f.profile.damage(),6,false);check(h,1000-t.getHealth()>0&&Math.abs(1000-t.getHealth()-expected)<.01,"No extra raw damage");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV) public void sourceCopiesEditsAndSuperContextAreImmediateReadOnly(GameTestHelper h){
        var f=new Fixture(h);f.superElement(Element.ARC);var hp=WeaponHandlingProfile.of(f.entry);check(h,WeaponElementalCapacitor.handlingTicks(f.p,f.gun.copy(),true,999)==999,"Equal-data unowned copy denied");var d=Guardians.data(f.p).copy();var copy=f.gun.copy();for(int i=0;i<20;i++)check(h,WeaponElementalCapacitor.element(f.p)==Element.ARC,"Repeated passive observation");check(h,d.cooldownsView().equals(Guardians.data(f.p).cooldownsView())&&ItemStack.matches(copy,f.gun),"No charge or item mutation");
        var runtime=Guardians.runtime(f.p);runtime.superSession=new SuperSession(){public boolean tick(){return true;}public void primary(){}public void end(){}public float remaining(){return 1;}};check(h,WeaponElementalCapacitor.element(f.p)==Element.KINETIC,"Weapon context excludes active SUPER");runtime.superSession=null;WeaponPerks.clear(f.gun);check(h,WeaponElementalCapacitor.element(f.p)==Element.KINETIC,"Socket clear immediate");check(h,WeaponPerks.select(f.gun,ID),"Reselect exact source");int slot=f.p.getInventory().getSelectedSlot();f.p.getInventory().setItem(slot,ItemStack.EMPTY);check(h,WeaponElementalCapacitor.element(f.p)==Element.KINETIC,"Removed item no longer source");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV) public void legalPatronRapidHitWithFundedPrecisionPreservesBothRawBonuses(GameTestHelper h){
        var f=new Fixture(h,"patron_of_lost_causes");check(h,!WeaponPerks.select(f.gun,SurplusProfile.ID),"Do not invent absent Patron Surplus roll");check(h,WeaponPerks.select(f.gun,RapidHitProfile.ID),"Actual official different socket Rapid Hit");check(h,WeaponPerks.selected(f.gun,ID).isPresent(),"Companion does not overwrite EC");f.tick();
        var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,1,6));t.setNoAi(true);t.setNoGravity(true);t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(1000);TestCleanup.register(h,t::discard);
        f.p.setYRot(-90);f.p.setYHeadRot(-90);f.p.setXRot(0);WeaponAiming.cleanup(f.p);WeaponAiming.tick(f.p);check(h,beginUse(f.p),"Paid actual precision trigger accepted");WeaponRuntime.releaseUse(f.p,f.gun);check(h,t.getHealth()<1000&&WeaponItems.magazine(f.gun,f.profile).rounds()==0&&WeaponRapidHit.stacks(f.p)==1,"Actual funded precision grants real Rapid Hit tier1");
        var base=WeaponReloadPolicy.forEntry(f.entry,f.profile.reloadTicks(),f.profile.shellReload());var rapid=WeaponRapidHit.plan(f.p,f.entry,base);var together=WeaponElementalCapacitor.plan(f.p,f.entry,rapid);check(h,together.firstTicks()<=rapid.firstTicks(),"Solar50 and real Rapid Hit reload stat/scalar combine without erasure");check(h,WeaponRuntime.reload(f.p),"Actual combined reload accepted");check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==together.firstTicks(),"Actual outer wrapper installs combined accepted plan");WeaponRuntime.cancelUseForSkill(f.p);
        f.superElement(Element.VOID);check(h,WeaponRapidHit.stabilityBonus(f.p)>0&&WeaponElementalCapacitor.stabilityBonus(f.p)==20,"Legal real Rapid Hit +Void20 live stability");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV) public void steelPaidFinalKillKeepsFeedingFrenzyScalarAlongsideSolar(GameTestHelper h){
        var f=new Fixture(h);check(h,WeaponPerks.select(f.gun,FeedingFrenzyProfile.ID),"Real Steel3 Feeding Frenzy pairs with EC4");check(h,WeaponPerks.selected(f.gun,ID).isPresent(),"Actual second socket survives");f.tick();
        var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,1.8,6));t.setNoAi(true);t.setNoGravity(true);t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.setHealth(1);TestCleanup.register(h,t::discard);
        f.p.setYRot(-90);f.p.setYHeadRot(-90);f.p.setXRot(0);WeaponAiming.cleanup(f.p);WeaponAiming.tick(f.p);check(h,beginUse(f.p),"Paid final-hit trigger");WeaponRuntime.releaseUse(f.p,f.gun);check(h,!t.isAlive()&&WeaponItems.magazine(f.gun,f.profile).rounds()==0&&WeaponFeedingFrenzy.stacks(f.p)==1,"Actual paid final kill supplies sourced FF1");
        var base=WeaponReloadPolicy.forEntry(f.entry,f.profile.reloadTicks(),f.profile.shellReload());var ff=WeaponFeedingFrenzy.plan(f.p,f.entry,base);var together=WeaponElementalCapacitor.plan(f.p,f.entry,ff);check(h,together.firstTicks()<=ff.firstTicks(),"Solar raw reload50 preserves real FF scalar before one ceil");check(h,WeaponRuntime.reload(f.p),"Actual combined reload accepted");check(h,WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration()==together.firstTicks(),"Production outer wrapper retains exact FF+Solar plan");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV) public void exactOptionalSocketsAndNoFabricatedPassiveHud(GameTestHelper h){
        var ids=ElementalCapacitorProfile.rolls().stream().map(WeaponPerks.Roll::id).collect(java.util.stream.Collectors.toSet());check(h,ids.equals(Set.of("steelfeather_repeater","patron_of_lost_causes")),"Exact official two source IDs");
        for(var e:WeaponCatalog.all()){var s=WeaponItems.create(e);check(h,WeaponPerks.selected(s,ID).isEmpty(),"No free default");check(h,WeaponPerks.select(s,ID)==ids.contains(e.id()),"Official exact optional socket "+e.id());}
        var f=new Fixture(h);for(var e:List.of(Element.SOLAR,Element.ARC,Element.VOID)){f.superElement(e);CombatHud.update(f.p);check(h,DisplayHud.getHuds(f.p).keySet().stream().noneMatch(k->k.contains("elemental_capacitor")),"Passive stat trait does not invent timer/count HUD");}h.succeed();
    }
}
