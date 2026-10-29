package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.*;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.List;

public final class AmmoEconomyW42GameTests {
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void privateDisplayLiftsCentredItemGeometryAbovePickupFloor(GameTestHelper h) {
        var p=player(h);var at=p.position();
        var holder=kim.biryeong.destiny.fx.AmmoBrickVisual.create(p,WeaponAmmoType.SPECIAL,at);
        TestCleanup.register(h, holder::destroy);
        var display=(eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement)holder.getElements().getFirst();
        double bottom=at.y-.5*display.getScale().y()+display.getTranslation().y();
        double top=bottom+5.2/16*display.getScale().y();
        check(h,Math.abs(bottom-at.y)<.00001&&top>at.y+.2,"Centred model bottom must not sink under the actual floor");
        check(h,holder.getPos().equals(at)&&holder.getWatchingPlayers().size()==1,"Private holder keeps the pickup anchor and owner only");
        h.succeed();
    }
    private static void check(GameTestHelper h,boolean b,String message){h.assertTrue(b,Component.literal(message));}
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void simultaneousAmmoTypesHaveDistinctSafeRenderAnchors(GameTestHelper h) {
        var p=player(h);p.setAttached(AmmoEconomy.METERS,new AmmoMeters(AmmoMeters.FULL,AmmoMeters.FULL));
        kill(h,p,5.5,1,AmmoGeneration.ABILITY);
        var positions=AmmoEconomy.brickPositions(p);
        check(h,positions.size()==2&&positions.getFirst().distanceToSqr(positions.getLast())>.4,
                "Green/purple shells cannot overlap and hide each other on a simultaneous drop");
        check(h,positions.stream().allMatch(pos->h.getLevel().noCollision(net.minecraft.world.phys.AABB.ofSize(pos,.1,.1,.1))),
                "Both visual anchors remain in safe free space");h.succeed();
    }
    private static ServerPlayer player(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,0);
        TestCleanup.register(h, ()->{AmmoEconomy.cleanup(p);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        p.setAttached(WeaponLoadout.ENABLED,true);
        p.getInventory().setItem(0,item("austringer",10,0));
        p.getInventory().setItem(1,item("nezarec_s_whisper",0,0));
        p.getInventory().setItem(2,item("bad_omens",0,0));
        p.getInventory().setSelectedSlot(0);return p;
    }
    private static ItemStack item(String id,int rounds,int reserve) {
        var e=WeaponCatalog.find(id).orElseThrow();var stack=WeaponItems.create(e);
        WeaponItems.save(stack,new WeaponMagazine(WeaponProfile.forEntry(e),rounds,reserve));return stack;
    }
    private static Husk enemy(GameTestHelper h,double x,double y) {
        var e=h.spawn(EntityTypes.HUSK,new Vec3(x,y,6.5));e.setNoAi(true);e.setPersistenceRequired();
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        e.setHealth(20);TestCleanup.register(h, e::discard);return e;
    }
    private static void kill(GameTestHelper h,ServerPlayer p,double x,double y,AmmoGeneration source) {
        Combat.damage(h.getLevel(),p,enemy(h,x,y),100,Element.KINETIC,source);
    }
    private static WeaponMagazine ammo(ServerPlayer p,int slot) {
        var s=p.getInventory().getItem(slot);return WeaponItems.magazine(s,WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow()));
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void realDamageFinalBlowEarnsOneGainAndCorpseOrReadCannotEarnAgain(GameTestHelper h) {
        var p=player(h);var e=enemy(h,5.5,1);var source=AmmoGeneration.weapon(WeaponItems.entry(p.getMainHandItem()).orElseThrow());
        Combat.damage(h.getLevel(),p,e,2,Element.KINETIC,source);
        check(h,AmmoEconomy.meters(p).equals(AmmoMeters.EMPTY),"Damage without defeat does not produce kill progress");
        Combat.damage(h.getLevel(),p,e,100,Element.KINETIC,source);var gained=source.gains(false);
        check(h,AmmoEconomy.meters(p).equals(gained),"Actual primary kill uses the captured source stat");
        Combat.damage(h.getLevel(),p,e,100,Element.KINETIC,source);CombatHud.update(p);CombatHud.update(p);
        check(h,AmmoEconomy.meters(p).equals(gained)&&AmmoEconomy.bricks(p)==0,"Corpse/HUD reads cannot repeat rewards");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void realAssistAndFinalBlowAreSeparatePersonalMeters(GameTestHelper h) {
        var a=player(h);var b=player(h);var e=enemy(h,5.5,1);
        var source=AmmoGeneration.weapon(WeaponItems.entry(a.getMainHandItem()).orElseThrow());
        Combat.damage(h.getLevel(),a,e,2,Element.KINETIC,source);
        Combat.damage(h.getLevel(),b,e,100,Element.KINETIC,source);
        check(h,AmmoEconomy.meters(a).equals(source.gains(true)),"A gets assist, not a second final blow");
        check(h,AmmoEconomy.meters(b).equals(source.gains(false)),"B gets full personal final blow");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=230, environment = "destiny-test:w90_isolated")
    public void expiredAssistDoesNotReceiveLaterDeathCredit(GameTestHelper h) {
        var a=player(h);var b=player(h);var e=enemy(h,5.5,1);
        Combat.damage(h.getLevel(),a,e,1,Element.KINETIC,AmmoGeneration.ABILITY);
        h.runAfterDelay(AmmoEconomy.ASSIST_TICKS+1,()->{
            Combat.damage(h.getLevel(),b,e,100,Element.KINETIC,AmmoGeneration.SUPER);
            check(h,AmmoEconomy.meters(a).equals(AmmoMeters.EMPTY),"Expired contribution cannot earn");
            check(h,AmmoEconomy.meters(b).equals(AmmoGeneration.SUPER.gains(false)),"Super source remains separate");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void actualInFlightGlaiveKillKeepsShotSourceAfterSwitchToPrimary(GameTestHelper h) {
        var p=player(h);p.getInventory().setItem(1,item("nezarec_s_whisper",6,0));p.getInventory().setSelectedSlot(1);
        var e=enemy(h,7.5,1);e.setHealth(1);var source=AmmoGeneration.weapon(WeaponItems.entry(p.getMainHandItem()).orElseThrow());
        p.gameMode.useItem(p,h.getLevel(),p.getMainHandItem(),InteractionHand.MAIN_HAND);
        WeaponLoadout.select(p,WeaponSlot.KINETIC);
        h.runAfterDelay(5,()->{check(h,e.isDeadOrDying(),"Actual projectile killed target");
            check(h,AmmoEconomy.meters(p).equals(source.gains(false)),"Weapon swapped in flight cannot turn Special credit into Primary");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void earnedPersonalBrickFillsReserveOnlyAndCannotBePickedTwice(GameTestHelper h) {
        var p=player(h);var other=player(h);var special=p.getInventory().getItem(1);
        GlaiveItems.saveEnergy(special,27150);p.setAttached(AmmoEconomy.METERS,new AmmoMeters(AmmoMeters.FULL-2000,0));
        kill(h,p,5.5,1,AmmoGeneration.ABILITY);
        check(h,AmmoEconomy.bricks(p)==1&&AmmoEconomy.bricks(other)==0,"One personal earned special brick exists");
        check(h,AmmoEconomy.brickWatchers(p).size()==1&&AmmoEconomy.brickWatchers(p).contains(p.connection),"Only owner receives virtual pickup packets");
        var pos=AmmoEconomy.brickPositions(p).getFirst();other.setPos(pos);AmmoEconomy.tickPlayer(other);
        check(h,ammo(other,1).reserve()==0&&AmmoEconomy.bricks(p)==1,"Another owner cannot collect or inherit the brick");
        p.setPos(pos);AmmoEconomy.tickPlayer(p);AmmoEconomy.tickPlayer(p);
        check(h,ammo(p,1).rounds()==0&&ammo(p,1).reserve()==4,"Pickup goes to reserve, never current magazine");
        check(h,GlaiveItems.energy(special)==27150&&WeaponModels.twoHanded(special),"Energy/model grip survives pickup save");
        check(h,AmmoEconomy.bricks(p)==0,"Consumed brick cannot collect twice");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void fullOrUnequippedReservesLeaveBrickAndNoHiddenInventoryToken(GameTestHelper h) {
        var p=player(h);p.getInventory().setItem(1,item("nezarec_s_whisper",0,30));
        p.getInventory().setItem(8,item("nezarec_s_whisper",0,0));
        p.setAttached(AmmoEconomy.METERS,new AmmoMeters(AmmoMeters.FULL-2000,0));kill(h,p,5.5,1,AmmoGeneration.ABILITY);
        p.setPos(AmmoEconomy.brickPositions(p).getFirst());AmmoEconomy.tickPlayer(p);
        check(h,AmmoEconomy.bricks(p)==1&&ammo(p,8).reserve()==0,"Full canonical reserve does not consume or refill a stowed duplicate");
        p.getInventory().setItem(1,ItemStack.EMPTY);AmmoEconomy.tickPlayer(p);
        check(h,AmmoEconomy.bricks(p)==1,"No equipped matching weapon means no consumption");
        check(h,p.getInventory().getItem(3).isEmpty()&&ammo(p,0).reserve()==0,"No inventory brick token or fake primary reserve");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void doubleSpecialSplitsOneBrickAndCannotRefillBothAtFullRate(GameTestHelper h) {
        var p=player(h);p.getInventory().setItem(0,item("bite_of_the_fox",0,0));
        p.setAttached(AmmoEconomy.METERS,new AmmoMeters(AmmoMeters.FULL-2000,0));kill(h,p,5.5,1,AmmoGeneration.ABILITY);
        p.setPos(AmmoEconomy.brickPositions(p).getFirst());AmmoEconomy.tickPlayer(p);
        check(h,ammo(p,0).reserve()==1&&ammo(p,1).reserve()==2,"Both Special weapons get divided archetype grant");
        check(h,ammo(p,0).rounds()==0&&ammo(p,1).rounds()==0,"Neither magazine gets free loading");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void pitDefersOwedAmmoUntilNextSafeActualKill(GameTestHelper h) {
        var p=player(h);p.setAttached(AmmoEconomy.METERS,new AmmoMeters(AmmoMeters.FULL-2000,0));
        kill(h,p,5.5,20,AmmoGeneration.ABILITY);
        check(h,AmmoEconomy.bricks(p)==0&&AmmoEconomy.meters(p).owed(WeaponAmmoType.SPECIAL),"Pit kill retains full owed meter");
        CombatHud.update(p);AmmoEconomy.tickPlayer(p);
        check(h,AmmoEconomy.bricks(p)==0,"HUD/tick cannot replace safe final blow with automatic grant");
        kill(h,p,5.5,1,AmmoGeneration.ABILITY);
        check(h,AmmoEconomy.bricks(p)==1&&AmmoEconomy.meters(p).special()==2000,"Next safe defeat materializes owed brick and preserves overflow");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void collisionPreventsPickupThroughWallAndRemovalAllowsCollection(GameTestHelper h) {
        var p=player(h);p.setAttached(AmmoEconomy.METERS,new AmmoMeters(AmmoMeters.FULL-2000,0));kill(h,p,4.5,1,AmmoGeneration.ABILITY);
        check(h,AmmoEconomy.bricks(p)==1,"Collision fixture must start with one earned brick");
        var brick=AmmoEconomy.brickPositions(p).getFirst();
        p.setPos(h.absoluteVec(new Vec3(3.4,1,6.5)));h.setBlock(4,1,6,Blocks.STONE);h.setBlock(4,0,6,Blocks.STONE);
        AmmoEconomy.tickPlayer(p);check(h,ammo(p,1).reserve()==0&&AmmoEconomy.bricks(p)==1,"Nearby brick behind solid collider cannot collect: body="+p.position()+", brick="+brick+", wall="+h.absolutePos(new net.minecraft.core.BlockPos(4,1,6)));
        h.setBlock(4,1,6,Blocks.AIR);h.setBlock(4,0,6,Blocks.AIR);AmmoEconomy.tickPlayer(p);
        check(h,ammo(p,1).reserve()==4&&AmmoEconomy.bricks(p)==0,"Removing wall enables actual proximity pickup");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=80, environment = "destiny-test:w90_isolated")
    public void reservePickupDoesNotRestartOrCompleteAnExistingReload(GameTestHelper h) {
        var p=player(h);p.getInventory().setItem(1,item("nezarec_s_whisper",1,1));p.getInventory().setSelectedSlot(1);
        check(h,WeaponRuntime.reload(p),"Start reload before earning pickup");
        p.setAttached(AmmoEconomy.METERS,new AmmoMeters(AmmoMeters.FULL-2000,0));kill(h,p,5.5,1,AmmoGeneration.ABILITY);
        p.setPos(AmmoEconomy.brickPositions(p).getFirst());AmmoEconomy.tickPlayer(p);
        check(h,ammo(p,1).rounds()==1&&ammo(p,1).reserve()==5&&WeaponRuntime.reloading(p),"Pickup changes reserve only while original reload is pending");
        int duration=WeaponProfile.forEntry(WeaponCatalog.find("nezarec_s_whisper").orElseThrow()).reloadTicks();
        h.runAfterDelay(duration-1,()->{WeaponRuntime.tickPlayer(p);check(h,ammo(p,1).rounds()==1,"No early magazine refill");});
        h.runAfterDelay(duration,()->{WeaponRuntime.tickPlayer(p);check(h,ammo(p,1).rounds()==6&&ammo(p,1).reserve()==0,"Original deadline transfers updated actual reserve");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void meterHudIsReadOnlyBoundedAndEquipmentRemovalHidesOnlyItsType(GameTestHelper h) {
        var p=player(h);p.setAttached(AmmoEconomy.METERS,new AmmoMeters(50000,75000));CombatHud.update(p);
        long count=DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith(AmmoMeterHud.PREFIX)).count();
        check(h,count==6,"Two meters have exactly six nodes including real fills");
        var before=AmmoEconomy.meters(p);CombatHud.update(p);CombatHud.update(p);
        check(h,AmmoEconomy.meters(p).equals(before)&&AmmoEconomy.bricks(p)==0,"Repeated HUD reads earn no progress or items");
        p.getInventory().setItem(1,ItemStack.EMPTY);CombatHud.update(p);
        check(h,DisplayHud.getHuds(p).keySet().stream().noneMatch(k->k.startsWith(AmmoMeterHud.PREFIX+"special")),"Unowned Special meter disappears");
        check(h,DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith(AmmoMeterHud.PREFIX)).count()==3,"Owned Heavy meter remains");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void capPreservesDebtAndCleanupRemovesOnlySceneObjectsNotPersistentMeters(GameTestHelper h) {
        var p=player(h);p.setAttached(AmmoEconomy.METERS,new AmmoMeters(AmmoMeters.MAX,0));
        for(int i=0;i<AmmoEconomy.MAX_BRICKS+2;i++)kill(h,p,5.5,1,AmmoGeneration.ABILITY);
        check(h,AmmoEconomy.bricks(p)==AmmoEconomy.MAX_BRICKS&&AmmoEconomy.meters(p).owed(WeaponAmmoType.SPECIAL),"Scene cap defers rather than spending nonexistent brick");
        var saved=AmmoEconomy.meters(p);AmmoEconomy.cleanup(p);
        check(h,AmmoEconomy.bricks(p)==0&&AmmoEconomy.meters(p).equals(saved),"Scene cleanup keeps immutable persistent progress");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void invulnerabilityAndNonHostilesNeverEarnAmmoProgress(GameTestHelper h) {
        var p=player(h);var e=enemy(h,5.5,1);e.setPermanentlyInvulnerable(true);
        Combat.damage(h.getLevel(),p,e,100,Element.KINETIC,AmmoGeneration.ABILITY);
        var cow=h.spawn(EntityTypes.COW,new Vec3(5.5,1,8.5));TestCleanup.register(h, cow::discard);
        Combat.damage(h.getLevel(),p,cow,100,Element.KINETIC,AmmoGeneration.ABILITY);
        check(h,AmmoEconomy.meters(p).equals(AmmoMeters.EMPTY)&&AmmoEconomy.bricks(p)==0,"Damage rejection or passive creature farming cannot mint ammo");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void emptyHandsDoNotRecreateOrHideOwnedMeterEveryFrame(GameTestHelper h) {
        var p=player(h);p.getInventory().setSelectedSlot(8);CombatHud.update(p);
        String id=AmmoMeterHud.PREFIX+"special_track";
        var first=(kim.biryeong.minigamelib.displayhud.ItemDisplayHud)DisplayHud.getHud(p,id);
        check(h,first!=null,"Non-Guardian with empty hands still sees owned ammo progress");
        int entity=first.getEntityId();CombatHud.update(p);CombatHud.update(p);
        check(h,((kim.biryeong.minigamelib.displayhud.ItemDisplayHud)DisplayHud.getHud(p,id)).getEntityId()==entity,
                "Separate meter ownership prevents ammo clear from destroying/reallocating displays each frame");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void legacyTeammateFinalBlowStillCreditsEligibleAssists(GameTestHelper h) {
        var a=player(h);var b=player(h);b.setAttached(WeaponLoadout.ENABLED,false);var e=enemy(h,5.5,1);
        Combat.damage(h.getLevel(),a,e,1,Element.KINETIC,AmmoGeneration.ABILITY);
        Combat.damage(h.getLevel(),b,e,100,Element.KINETIC,AmmoGeneration.ABILITY);
        check(h,AmmoEconomy.meters(a).equals(AmmoGeneration.ABILITY.gains(true)),"Eligible helper earns assist even when killer is in legacy standalone mode");
        check(h,AmmoEconomy.meters(b).equals(AmmoMeters.EMPTY),"Legacy killer is not silently opted into equipment economy");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void actualPlayerDeathRemovesSceneBricksAndKeepsStoredProgress(GameTestHelper h) {
        var p=player(h);p.setAttached(AmmoEconomy.METERS,new AmmoMeters(AmmoMeters.FULL-2000,6000));kill(h,p,5.5,1,AmmoGeneration.ABILITY);
        check(h,AmmoEconomy.bricks(p)==1,"Earned scene brick before death");var saved=AmmoEconomy.meters(p);
        p.hurtServer(h.getLevel(),p.damageSources().genericKill(),10000);
        check(h,p.isDeadOrDying()&&AmmoEconomy.bricks(p)==0,"Actual death event clears private display manager");
        check(h,AmmoEconomy.meters(p).equals(saved),"Death cleanup cannot erase persistent earned debt/progress");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=2450, environment = "destiny-test:w90_isolated")
    public void lifetimeExpiresActualSceneBrickWithoutGrantingInventoryAmmo(GameTestHelper h) {
        var p=player(h);p.setAttached(AmmoEconomy.METERS,new AmmoMeters(AmmoMeters.FULL-2000,0));kill(h,p,5.5,1,AmmoGeneration.ABILITY);
        h.runAfterDelay(AmmoEconomy.BRICK_LIFETIME-1,()->{AmmoEconomy.tickPlayer(p);check(h,AmmoEconomy.bricks(p)==1,"Lifetime does not expire early");});
        h.runAfterDelay(AmmoEconomy.BRICK_LIFETIME,()->{AmmoEconomy.tickPlayer(p);
            check(h,AmmoEconomy.bricks(p)==0&&ammo(p,1).reserve()==0,"Expired world pickup disappears without remote/free granting");h.succeed();});
    }
}
