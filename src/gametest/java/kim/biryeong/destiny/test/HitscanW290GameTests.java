package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.*;

public final class HitscanW290GameTests {
    private static void check(GameTestHelper h,boolean ok,String message) {h.assertTrue(ok,Component.literal(message));}
    private static ServerPlayer player(GameTestHelper h,String id,double z) {
        var p=TestPlayers.hunter(h,Element.ARC,new Vec3(2.5,1,z),-90,0);
        var entry=WeaponCatalog.find(id).orElseThrow();
        var gun=WeaponItems.create(entry);
        WeaponAccuracy.setAirborneBonus(gun,100);
        int hot=WeaponLoadout.slot(p,gun,entry).hotbar();p.getInventory().setItem(hot,gun);p.getInventory().setSelectedSlot(hot);
        {var why=WeaponLoadout.equipHeld(p);check(h,why==null,"Weapon equipped: "+why);}
        TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);WeaponAiming.cleanup(p);TestPlayers.remove(p);});
        h.onEachTick(()->{WeaponRuntime.tickPlayer(p);WeaponAiming.tick(p);});
        return p;
    }
    private static LivingEntity target(GameTestHelper h,double z) {
        var mob=h.spawn(EntityTypes.HUSK,new Vec3(10.5,1,z));
        mob.setNoAi(true);mob.setNoGravity(true);
        mob.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);mob.setHealth(1000);
        mob.getAttribute(Attributes.ARMOR).setBaseValue(0);
        mob.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        return mob;
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w290_hitscan",maxTicks=75)
    public void paidGunHitsRenderedMovingTargetInSameCallWithoutFlight(GameTestHelper h) {
        var p=player(h,"halfdan_d",6.5);var target=target(h,6.5);
        var old=target.position();
        h.runAfterDelay(20,()->check(h,WeaponAiming.toggle(p),"ADS starts"));
        h.runAfterDelay(40,()->target.setPos(old.add(0,0,1.4)));
        h.runAfterDelay(41,()->{
            check(h,WeaponAiming.coneDegrees(p)==0,"Deterministic ADS firing axis");
            Vec3 from=p.getEyePosition(),to=from.add(20,0,0);
            check(h,target.getBoundingBox().clip(from,to).isEmpty(),"Current body has left the rendered firing line");
            var contact=WeaponHitscan.trace(p,from,to,.03f,e->e==target);
            check(h,contact.hit() instanceof EntityHitResult e&&e.getEntity()==target,"Historical body is hit on its rendered line");
            check(h,WeaponPrecision.critical(target,from,contact.hit().getLocation(),2,contact.body()),"Headshot uses the sampled head");
            int before=WeaponItems.magazine(p.getMainHandItem(),WeaponProfile.forEntry(WeaponCatalog.find("halfdan_d").orElseThrow())).rounds();
            Vec3 live=target.position();
            check(h,WeaponRuntime.beginUse(p),"Paid automatic rifle emission accepted");
            check(h,target.getHealth()<1000,"Health changes synchronously in the firing call");
            check(h,WeaponRuntime.activeProjectiles(p)==0,"No bullet flight to wait for or lead");
            check(h,target.position().equals(live),"Lag compensation never teleports the actual entity");
            check(h,WeaponItems.magazine(p.getMainHandItem(),WeaponProfile.forEntry(WeaponCatalog.find("halfdan_d").orElseThrow())).rounds()==before-1,"Exactly one paid round");
            WeaponRuntime.releaseUse(p,p.getMainHandItem());
            h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w290_hitscan",maxTicks=45)
    public void wallsTeleportAndExpiryCannotCreateOldPositionHits(GameTestHelper h) {
        var p=player(h,"halfdan_d",6.5);var target=target(h,6.5);var old=target.position();
        h.runAfterDelay(15,()->target.setPos(old.add(0,0,1.4)));
        h.runAfterDelay(16,()->{
            Vec3 from=p.getEyePosition(),to=from.add(20,0,0);
            check(h,WeaponHitscan.trace(p,from,to,.03f,e->e==target).hit() instanceof EntityHitResult,"Recent moving target admitted");
            h.setBlock(6,2,6,Blocks.STONE);
            check(h,WeaponHitscan.trace(p,from,to,.03f,e->e==target).hit() instanceof BlockHitResult,"Wall wins against historical target");
            h.setBlock(6,2,6,Blocks.AIR);
            target.setPos(old.add(0,0,10));
            check(h,!(WeaponHitscan.trace(p,from,to,.03f,e->e==target).hit() instanceof EntityHitResult),"Teleport immediately invalidates old body");
        });
        h.runAfterDelay(25,()->{
            target.setPos(old);
        });
        h.runAfterDelay(33,()->target.setPos(old.add(0,0,1.4)));
        h.runAfterDelay(41,()->{
            Vec3 from=p.getEyePosition();
            check(h,!(WeaponHitscan.trace(p,from,from.add(20,0,0),.03f,e->e==target).hit() instanceof EntityHitResult),"Expired historical position is not hittable");
            h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w290_projectiles",maxTicks=65)
    public void grenadeAndRocketStillTravelBeforeDamageAndCatalogModesRemainExplicit(GameTestHelper h) {
        for(var e:WeaponCatalog.all()) {
            var mode=WeaponProfile.forEntry(e).mode();
            var expected=switch(e.family()) {
                case "grenade_launcher","heavy_grenade_launcher","rocket_launcher","bow","glaive" -> WeaponProfile.Mode.PROJECTILE;
                case "sword" -> WeaponProfile.Mode.MELEE;
                default -> WeaponProfile.Mode.HITSCAN;
            };
            check(h,mode==expected,"Explicit collision mode: "+e.id());
        }
        var grenade=player(h,"salvager_s_salvo",2.5);var rocket=player(h,"bad_omens",10.5);
        var a=target(h,2.5);var b=target(h,10.5);
        h.runAfterDelay(20,()->{WeaponAiming.toggle(grenade);WeaponAiming.toggle(rocket);});
        h.runAfterDelay(40,()->{
            check(h,WeaponRuntime.beginUse(grenade)&&WeaponRuntime.beginUse(rocket),"Both paid explosive launches accepted");
            check(h,a.getHealth()==1000&&b.getHealth()==1000,"Explosives cannot deal instant hitscan damage");
            check(h,WeaponRuntime.activeProjectiles(grenade)==1&&WeaponRuntime.activeProjectiles(rocket)==1,"Both retain real flight state");
        });
        h.runAfterDelay(55,()->{
            check(h,a.getHealth()<1000&&b.getHealth()<1000,"Explosives damage only after travelling to the target");
            h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w290_payload",maxTicks=65)
    public void compensatedExplosivePayloadRetainsDirectVictimAndOneAmmoCost(GameTestHelper h) {
        var p=player(h,"distant_relation",6.5);var target=target(h,6.5);var old=target.position();
        check(h,WeaponPerks.select(p.getMainHandItem(),"explosive_payload"),"Official explosive payload selected");
        h.runAfterDelay(20,()->check(h,WeaponAiming.toggle(p),"ADS starts"));
        h.runAfterDelay(40,()->target.setPos(old.add(0,0,2)));
        h.runAfterDelay(41,()->target.setPos(old.add(0,0,4)));
        h.runAfterDelay(42,()->{
            target.setPos(old.add(0,0,6));
            check(h,WeaponAiming.coneDegrees(p)==0,"No stochastic spread in this fixture");
            var entry=WeaponCatalog.find("distant_relation").orElseThrow();
            var profile=WeaponProfile.forEntry(entry);
            float expected=PayloadProfile.impact(profile.damage(),WeaponBallistics.of(entry).precision(),true,1)
                    +PayloadProfile.explosion(profile.damage());
            check(h,WeaponRuntime.beginUse(p),"Paid explosive bullet accepted");
            check(h,Math.abs(1000-target.getHealth()-expected)<.005,"Both direct impact and payload reach sampled victim even outside current splash radius: expected="+expected+" actual="+(1000-target.getHealth()));
            check(h,WeaponRuntime.activeProjectiles(p)==0,"Explosive payload remains an immediate bullet, not a grenade");
            WeaponRuntime.releaseUse(p,p.getMainHandItem());
            h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w290_control",maxTicks=530)
    public void controlPlayerMovingOffTheRenderedLineTakesImmediatePaidGunDamage(GameTestHelper h) {
        var server=h.getLevel().getServer();
        check(h,kim.biryeong.destiny.crucible.CrucibleRuntime.snapshot().members().isEmpty(),"Exclusive Control fixture");
        kim.biryeong.destiny.world.TowerSpawnWorld.open(server);
        var logins=new java.util.ArrayList<CrucibleW263GameTests.Login>();
        var p=CrucibleW263GameTests.login(h,logins,"W290Shooter",Element.SOLAR);
        var target=CrucibleW263GameTests.login(h,logins,"W290Target",Element.ARC);
        h.onEachTick(()->{for(var login:logins)CrucibleW263GameTests.tickLogin(server,login);});
        check(h,kim.biryeong.destiny.world.TowerSpawnWorld.teleport(p)&&kim.biryeong.destiny.world.TowerSpawnWorld.teleport(target),"Tower ready");
        var entry=WeaponCatalog.find("halfdan_d").orElseThrow();
        var gun=WeaponItems.create(entry);WeaponAccuracy.setAirborneBonus(gun,100);
        int hot=WeaponLoadout.slot(p,gun,entry).hotbar();p.getInventory().setItem(hot,gun);p.getInventory().setSelectedSlot(hot);
        check(h,WeaponLoadout.equipHeld(p)==null,"Primary equipped");
        check(h,kim.biryeong.destiny.crucible.CrucibleRuntime.join(p)
                &&kim.biryeong.destiny.crucible.CrucibleRuntime.join(target),"Opposing Control teams");
        h.runAfterDelay(450,()->{
            var origin=p.position().add(0,64,0);
            p.setPos(origin);p.setNoGravity(true);p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0);
            target.setPos(origin.add(8,0,0));target.setNoGravity(true);
            check(h,WeaponAiming.toggle(p),"Native server ADS state starts");
        });
        h.runAfterDelay(490,()->{
            check(h,kim.biryeong.destiny.crucible.CrucibleRuntime.canFight(p,target),"PvP damage/protection gate admits the shot");
            check(h,WeaponAiming.coneDegrees(p)==0,"Exact ADS axis");
            target.setPos(target.position().add(0,0,1.4));
            var from=p.getEyePosition();
            check(h,target.getBoundingBox().clip(from,from.add(20,0,0)).isEmpty(),"Live enemy player has moved off the rendered line");
            float before=target.getHealth();
            int rounds=WeaponItems.magazine(gun,WeaponProfile.forEntry(entry)).rounds();
            check(h,WeaponRuntime.beginUse(p),"Actual paid PvP emission");
            check(h,target.getHealth()<before&&target.isAlive(),"Same-call damage to the moving enemy player");
            check(h,WeaponRuntime.activeProjectiles(p)==0&&WeaponItems.magazine(gun,WeaponProfile.forEntry(entry)).rounds()==rounds-1,"No flight and exactly one round paid");
            WeaponRuntime.releaseUse(p,gun);
            h.succeed();
        });
    }
}
