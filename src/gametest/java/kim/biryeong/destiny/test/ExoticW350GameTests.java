package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.*;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** Real item-owned ammo, actual damage and lifecycle fixtures. These do not certify client visuals/audio. */
public final class ExoticW350GameTests {
    private static void check(GameTestHelper h,boolean ok,String message){h.assertTrue(ok,Component.literal(message));}
    private static ServerPlayer player(GameTestHelper h,double z){return TestPlayers.create(h,new Vec3(2.5,1,z),-90,0);}
    private static ItemStack equip(ServerPlayer p,String id){var stack=WeaponItems.create(WeaponCatalog.find(id).orElseThrow());p.setItemInHand(InteractionHand.MAIN_HAND,stack);return stack;}
    private static WeaponMagazine ammo(ItemStack stack){return WeaponItems.magazine(stack,WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()));}
    private static Husk target(GameTestHelper h,double x,double z,float health){
        var target=h.spawn(EntityTypes.HUSK,new Vec3(x,1,z));target.setNoAi(true);target.setPersistenceRequired();
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(health);target.setHealth(health);return target;
    }
    private static void cleanup(ServerPlayer p){WeaponRuntime.cleanup(p);TestPlayers.remove(p);}
    private static ExoticWeaponsW350.Token paid(ServerPlayer p){
        var stack=p.getMainHandItem();var magazine=ammo(stack);
        if(!magazine.consume())throw new IllegalStateException("Fixture cannot create an unpaid intrinsic receipt");
        WeaponItems.save(stack,magazine);return ExoticWeaponsW350.capture(p);
    }
    private static void contact(ServerPlayer p,ExoticWeaponsW350.Token token,Husk target,float amount,boolean precision){
        var snapshot=CombatantShields.snapshot(target);float before=Combat.damagePool(target);
        boolean killed=Combat.damage(p.level(),p,target,amount,Element.KINETIC,AmmoGeneration.weapon(WeaponItems.entry(p.getMainHandItem()).orElseThrow()));
        ExoticWeaponsW350.confirmed(p,token,target,precision,before-Combat.damagePool(target),killed,snapshot);
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40,environment="destiny-test:w90_isolated")
    public void crimsonPositivePrecisionKillHealsAndRefillsOnlyItsPaidSource(GameTestHelper h){
        var p=player(h,6.5);var stack=equip(p,"crimson");var enemy=target(h,5,6.5,1);
        TestCleanup.register(h,()->{enemy.discard();cleanup(p);});p.setHealth(5);
        var token=paid(p);contact(p,token,enemy,2,true);
        check(h,!enemy.isAlive()&&p.getHealth()>5,"Actual Crimson final blow heals");
        check(h,ammo(stack).rounds()==WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()).magazine(),"Precision kill refills original source");
        var second=paid(p);var copy=stack.copy();p.setItemInHand(InteractionHand.MAIN_HAND,copy);
        var untouched=target(h,6,7.5,1);untouched.setHealth(0);
        float hp=p.getHealth();ExoticWeaponsW350.confirmed(p,second,untouched,true,1,true,CombatantShields.Snapshot.NONE);
        check(h,p.getHealth()==hp,"Replaced source cannot authorize a forged late kill");untouched.discard();h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=40,environment="destiny-test:w90_isolated")
    public void thornPoisonIsStackedWeaponDamageAndCleanupRevokesOnlyItsOwner(GameTestHelper h){
        var a=player(h,4.5);var b=player(h,9.5);equip(a,"thorn");equip(b,"thorn");
        var one=target(h,5,4.5,100);var two=target(h,5,9.5,100);
        TestCleanup.register(h,()->{one.discard();two.discard();cleanup(a);cleanup(b);});
        contact(a,paid(a),one,1,false);contact(a,paid(a),one,1,false);contact(b,paid(b),two,1,false);
        check(h,ExoticWeaponsW350.pending(a)==2&&ExoticWeaponsW350.pending(b)==1,"Each actual contact owns its poison instance");
        float saved=one.getHealth(),other=two.getHealth();ExoticWeaponsW350.cleanup(a);
        h.runAfterDelay(7,()->{
            ExoticWeaponsW350.tick(h.getLevel().getServer());
            check(h,one.getHealth()==saved,"Cleaned owner cannot poison from an old callback");
            check(h,two.getHealth()<other,"Other owner's poison remains active");h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=40,environment="destiny-test:w90_isolated")
    public void whiteNailUsesThreeActualPrecisionReceiptsAndFiniteReserves(GameTestHelper h){
        var p=player(h,6.5);var stack=equip(p,"whisper_of_the_worm");var enemy=target(h,5,6.5,200);
        TestCleanup.register(h,()->{enemy.discard();cleanup(p);});
        var profile=WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow());WeaponItems.save(stack,new WeaponMagazine(profile,3,2));
        for(int i=0;i<3;i++){
            var token=paid(p);contact(p,token,enemy,1,true);
            ExoticWeaponsW350.confirmed(p,token,enemy,true,1,false,CombatantShields.Snapshot.NONE);
        }
        check(h,ammo(stack).rounds()==3&&ammo(stack).reserve()==0,"Three distinct actual receipts generate one and transfer exactly two");
        var token=paid(p);ExoticWeaponsW350.confirmed(p,token,enemy,true,0,false,CombatantShields.Snapshot.NONE);
        check(h,ammo(stack).rounds()==2,"Zero-loss precision callback grants no ammunition");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=40,environment="destiny-test:w90_isolated")
    public void sunshotQueuesBoundedChainsAndDroppedSourceCannotExecuteThem(GameTestHelper h){
        var p=player(h,6.5);var stack=equip(p,"sunshot");var first=target(h,5,6.5,1);var neighbor=target(h,6,6.5,100);
        TestCleanup.register(h,()->{first.discard();neighbor.discard();cleanup(p);});
        var token=paid(p);contact(p,token,first,2,false);
        check(h,ExoticWeaponsW350.pending(p)==1,"Final blow queues one blast instead of recursively dealing damage");
        float saved=neighbor.getHealth();p.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);
        h.runAfterDelay(2,()->{ExoticWeaponsW350.tick(h.getLevel().getServer());
            check(h,neighbor.getHealth()==saved&&ExoticWeaponsW350.pending(p)==0,"Dropped source revokes queued chains");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=40,environment="destiny-test:w90_isolated")
    public void tractorWeakensWithoutMultiplicativeStackingAndCleanupRemovesOwnedSpeed(GameTestHelper h){
        var p=player(h,6.5);equip(p,"tractor_cannon");var enemy=target(h,5,6.5,200);
        TestCleanup.register(h,()->{enemy.discard();cleanup(p);});
        contact(p,paid(p),enemy,1,false);contact(p,paid(p),enemy,1,false);
        check(h,Statuses.has(enemy,Keyword.SUPPRESSED),"Confirmed pulse suppresses");
        check(h,Math.abs(Statuses.modifyIncoming(enemy,10)-13)<.001,"Repeated strong weaken remains 30%, never multiplies itself");
        double base=p.getAttributeValue(Attributes.MOVEMENT_SPEED);
        ExoticWeaponsW350.tick(h.getLevel().getServer());
        check(h,p.getAttributeValue(Attributes.MOVEMENT_SPEED)>base,"Scientific Method owns a walking modifier");
        ExoticWeaponsW350.cleanup(p);check(h,p.getAttributeValue(Attributes.MOVEMENT_SPEED)==base,"Owner cleanup removes only its modifier");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=40,environment="destiny-test:w90_isolated")
    public void packHunterTransfersToNearbyAlliesAndOnlyLegendaryRocketReceiptsSpawnWolves(GameTestHelper h) {
        var caster=player(h,4.5);var ally=player(h,6.5);var far=player(h,30.5);
        caster.setNoGravity(true);ally.setNoGravity(true);far.setNoGravity(true);
        h.getLevel().addNewPlayer(caster);h.getLevel().addNewPlayer(ally);h.getLevel().addNewPlayer(far);
        equip(caster,"gjallarhorn");equip(ally,"bad_omens");equip(far,"bad_omens");
        TestCleanup.register(h,()->{caster.discard();ally.discard();far.discard();cleanup(caster);cleanup(ally);cleanup(far);});
        paid(caster);
        check(h,ExoticWeaponsW350.packRemaining(ally)>0,"A real nearby ally receives Pack Hunter");
        check(h,ExoticWeaponsW350.packRemaining(far)==0,"Out-of-range player does not receive the aura");
        var rocket=paid(ally);ExoticWeaponsW350.rocketDetonated(rocket,ally.position().add(3,1,0));
        ExoticWeaponsW350.rocketDetonated(rocket,ally.position().add(3,1,0));
        check(h,ExoticWeaponsW350.pending(ally)==8,"Captured legendary rocket produces exactly eight missiles once");
        ExoticWeaponsW350.cleanup(ally);equip(ally,"sunshot");var exotic=paid(ally);
        ExoticWeaponsW350.rocketDetonated(exotic,ally.position());
        check(h,ExoticWeaponsW350.pending(ally)==0,"Unrelated exotic does not inherit a previous rocket receipt");h.succeed();
    }

}
