package kim.biryeong.destiny.test;

import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.fx.GlaiveShieldVfx;
import kim.biryeong.destiny.hud.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

public final class GlaiveW41GameTests {
    private static void check(GameTestHelper h,boolean b,String m){h.assertTrue(b,Component.literal(m));}
    private static ServerPlayer player(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,0);
        TestCleanup.register(h, ()->{WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});return p;
    }
    private static ItemStack equip(ServerPlayer p,int rounds,int reserve,int energy) {
        var e=WeaponCatalog.find("nezarec_s_whisper").orElseThrow();var s=WeaponItems.create(e);
        WeaponItems.save(s,new WeaponMagazine(WeaponProfile.forEntry(e),rounds,reserve));GlaiveItems.saveEnergy(s,energy);
        p.setItemInHand(InteractionHand.MAIN_HAND,s);WeaponRuntime.tickPlayer(p);return s;
    }
    private static Husk target(GameTestHelper h,double x) {
        var e=h.spawn(EntityTypes.HUSK,new Vec3(x,1,6.5));e.setNoAi(true);e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(100);
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        e.setHealth(100);TestCleanup.register(h, e::discard);return e;
    }
    private static int rounds(ItemStack s){return WeaponItems.magazine(s,WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow())).rounds();}
    private static void use(GameTestHelper h,ServerPlayer p){p.gameMode.useItem(p,h.getLevel(),p.getMainHandItem(),InteractionHand.MAIN_HAND);}

    @GameTest(structure="destiny-test:floor",maxTicks=45, environment = "destiny-test:w90_isolated")
    public void emptyGlaiveHasThreeFreeMeleeSwingsWithDoubleFinisherAndNoDuplicateDamage(GameTestHelper h) {
        var p=player(h);var stack=equip(p,0,0,0);var enemy=target(h,4.5);
        WeaponRuntime.onPunch(p);check(h,enemy.getHealth()==93&&rounds(stack)==0,"Empty melee hits without spending or minting ammo");
        WeaponRuntime.onPunch(p);check(h,enemy.getHealth()==93,"Duplicate packet same tick cannot hit twice");
        h.runAfterDelay(12,()->{WeaponRuntime.onPunch(p);check(h,enemy.getHealth()==86,"Second melee is ordinary damage");});
        h.runAfterDelay(24,()->{WeaponRuntime.onPunch(p);check(h,enemy.getHealth()==72&&rounds(stack)==0,"Third melee is double, no ammo cost");
            check(h,WeaponItems.magazine(stack,WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow())).reserve()==0,"Reserve stays empty");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=35, environment = "destiny-test:w90_isolated")
    public void actualProjectileDamageChargesOriginalItemAndShotMeleeRecoveryIsFourTicks(GameTestHelper h) {
        var p=player(h);var stack=equip(p,6,30,0);var enemy=target(h,4.5);
        use(h,p);WeaponRuntime.onPunch(p);check(h,rounds(stack)==5&&enemy.getHealth()==100,"No immediate melee after shot");
        h.runAfterDelay(3,()->{check(h,enemy.getHealth()<100,"Server projectile actually hit");
            check(h,GlaiveItems.energy(stack)>=25000&&GlaiveItems.energy(stack)<26000,"Only confirmed projectile damage awards 25 percent plus tiny passive tick");});
        h.runAfterDelay(4,()->{float before=enemy.getHealth();WeaponRuntime.onPunch(p);
            check(h,enemy.getHealth()==before-7&&rounds(stack)==5,"Melee available after 0.2s and uses no extra shot");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void wallAndMissCannotGenerateProjectileHitEnergy(GameTestHelper h) {
        var p=player(h);var s=equip(p,6,30,0);var enemy=target(h,6.5);
        h.setBlock(4,2,6,Blocks.STONE);h.setBlock(4,1,6,Blocks.STONE);use(h,p);
        h.runAfterDelay(5,()->{check(h,enemy.getHealth()==100,"Wall blocks actual projectile");
            check(h,GlaiveItems.energy(s)<1000,"No hit charge for wall impact");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void invulnerableTargetCannotGrantShieldEnergyFromCollisionAlone(GameTestHelper h) {
        var p=player(h);var s=equip(p,6,30,0);var enemy=target(h,5.5);enemy.setPermanentlyInvulnerable(true);use(h,p);
        h.runAfterDelay(5,()->{check(h,enemy.getHealth()==100,"Invulnerable enemy rejects damage");
            check(h,GlaiveItems.energy(s)<1000,"Collision without damage cannot award hit energy");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void storedShieldEnergyRoundtripsAndGripChangeCannotRefillIt(GameTestHelper h) {
        var p=player(h);var s=equip(p,2,3,27150);var before=s.copy();
        var ops=h.getLevel().registryAccess().createSerializationContext(com.mojang.serialization.JsonOps.INSTANCE);
        var decoded=ItemStack.CODEC.parse(ops,ItemStack.CODEC.encodeStart(ops,s).getOrThrow()).getOrThrow();
        check(h,GlaiveItems.energy(decoded)==27150&&rounds(decoded)==2,"Persistent item roundtrip retains real energy and rounds");
        var nativeGrip=WeaponModels.withGrip(s,WeaponModels.Grip.NATIVE).orElseThrow();
        check(h,GlaiveItems.energy(nativeGrip)==27150&&rounds(nativeGrip)==2,"Wire grip change cannot refill or erase energy");
        check(h,ItemStack.matches(s,before),"Read-only codec/grip leave original unchanged");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30, environment = "destiny-test:w90_isolated")
    public void incomingRealMobDamageIsReducedOnlyFromFrontWhileGuarded(GameTestHelper h) {
        var p=player(h);equip(p,0,0,75000);var front=target(h,5.5);var back=target(h,.5);p.setShiftKeyDown(true);
        h.runAfterDelay(2,()->{
            WeaponRuntime.tickPlayer(p);check(h,WeaponRuntime.glaiveStatus(p).orElseThrow().guarding(),"Guard is actually active");
            check(h,GlaiveShieldVfx.displays(p)==1,"One cosmetic shield display");
            p.damageCooldownTime=0;p.setHealth(20);p.hurtServer(h.getLevel(),p.damageSources().mobAttack(front),8);
            check(h,Math.abs(p.getHealth()-19.8f)<.001f,"97.5 percent frontal PvE reduction reaches actual hurtServer");
            p.damageCooldownTime=0;p.setHealth(20);p.hurtServer(h.getLevel(),p.damageSources().mobAttack(back),8);
            check(h,p.getHealth()==12,"Rear damage is not reduced");
            p.damageCooldownTime=0;p.setHealth(20);p.hurtServer(h.getLevel(),p.damageSources().fall(),8);
            check(h,p.getHealth()==12,"Environmental damage is not blocked");
            p.setShiftKeyDown(false);p.damageCooldownTime=0;p.setHealth(20);p.hurtServer(h.getLevel(),p.damageSources().mobAttack(front),8);
            check(h,p.getHealth()==12,"Releasing sneak removes protection immediately, even before next tick");h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=35, environment = "destiny-test:w90_isolated")
    public void guardCanFireAndReloadCancelsProtectionWithoutThrowingItem(GameTestHelper h) {
        var p=player(h);var stack=equip(p,2,3,75000);p.setShiftKeyDown(true);
        h.runAfterDelay(2,()->{
            use(h,p);check(h,rounds(stack)==1&&!WeaponRuntime.reloading(p),"Sneak plus RMB fires, not reloads a glaive");
            check(h,WeaponRuntime.glaiveStatus(p).orElseThrow().guarding(),"Ranged fire retains guard");
            p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(ServerboundPlayerActionPacket.Action.DROP_ITEM,BlockPos.ZERO,Direction.UP));
            check(h,p.getMainHandItem()==stack&&rounds(stack)==1&&WeaponRuntime.reloading(p),"Real vanilla Q packet starts reload and preserves actual item");
            check(h,!WeaponRuntime.glaiveStatus(p).orElseThrow().guarding(),"Reload immediately removes protection");h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30, environment = "destiny-test:w90_isolated")
    public void swappingDuringFlightNeverChargesTheReplacementGlaive(GameTestHelper h) {
        var p=player(h);var first=equip(p,6,30,0);var enemy=target(h,8.5);use(h,p);
        p.getInventory().setSelectedSlot(1);var replacement=equip(p,6,30,0);
        h.runAfterDelay(5,()->{check(h,enemy.getHealth()<100,"In-flight owned shot still lands");
            check(h,GlaiveItems.energy(first)>=25000&&GlaiveItems.energy(replacement)<1000,"Energy stays on source item, not newly held glaive");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30, environment = "destiny-test:w90_isolated")
    public void droppedSourceCannotGainEnergyAndOtherOwnerIsNotMutated(GameTestHelper h) {
        var p=player(h);var other=player(h);other.setPos(h.absoluteVec(new Vec3(2.5,1,9.5)));
        var source=equip(p,6,30,0);var otherItem=equip(other,6,30,0);target(h,8.5);use(h,p);
        p.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);
        h.runAfterDelay(5,()->{check(h,GlaiveItems.energy(source)<1000,"Removed/traded original reference receives no hit charge");
            check(h,GlaiveItems.energy(otherItem)<1000,"Other owner never receives projectile energy");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30, environment = "destiny-test:w90_isolated")
    public void reticleIsReadOnlyBoundedAndSwapClearsGuardAndDisplays(GameTestHelper h) {
        var p=player(h);var s=equip(p,0,0,75000);p.setShiftKeyDown(true);
        h.runAfterDelay(2,()->{
            WeaponRuntime.tickPlayer(p);int energy=GlaiveItems.energy(s);CombatHud.update(p);CombatHud.update(p);
            check(h,GlaiveItems.energy(s)==energy,"HUD queries cannot recharge shield");
            check(h,DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith(AmmoHud.PREFIX+"glaive_")).count()==17,"Exactly sixteen charge segments plus one reticle");
            check(h,GlaiveShieldVfx.displays(p)==1,"No duplicate visual allocation");
            p.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);WeaponRuntime.tickPlayer(p);CombatHud.update(p);
            check(h,WeaponRuntime.glaiveStatus(p).isEmpty()&&GlaiveShieldVfx.displays(p)==0,"Swap revokes actual protection and world display");
            check(h,DisplayHud.getHuds(p).keySet().stream().noneMatch(k->k.startsWith(AmmoHud.PREFIX)),"No stale reticle or ammo UI");h.succeed();
        });
    }
}
