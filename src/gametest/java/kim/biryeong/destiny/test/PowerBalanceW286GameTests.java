package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.phys.Vec3;
import java.util.ArrayList;

/** Server damage evidence. A dedicated environment batch isolates the singleton Control session. */
public final class PowerBalanceW286GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) { h.assertTrue(ok, Component.literal(message)); }
    private static void near(GameTestHelper h, double actual, double expected, String message) {
        check(h, Math.abs(actual - expected) < .001, message + " expected=" + expected + " actual=" + actual);
    }
    private static float damage(WeaponCatalog.Entry e, ServerPlayer p, boolean head, double distance) {
        return CrucibleDamage.ballistics(e,p,WeaponBallistics.of(e))
                .damage(CrucibleDamage.base(e,p,WeaponProfile.forEntry(e).damage()),distance,head);
    }
    
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=20)
    public void blastWaveFalloffAndUnpaidSwordBudgets(GameTestHelper h) {
        var p=TestPlayers.hunter(h,Element.ARC,new Vec3(2,1,2),0,0);
        var mob=h.spawn(EntityTypes.HUSK,new net.minecraft.core.BlockPos(4,1,4));
        TestCleanup.register(h,()->{mob.discard();TestPlayers.remove(p);});
        for(String id:new String[]{"salvager_s_salvo","edge_transit","bad_omens"}) {
            var e=WeaponCatalog.find(id).orElseThrow();float local=WeaponProfile.forEntry(e).damage();
            near(h,CrucibleDamage.blast(e,p,local,true,.3f),damage(e,p,false,0),id+" direct full budget");
            near(h,CrucibleDamage.blast(e,p,local,false,.3f),damage(e,p,false,0)*.3,id+" splash falloff");
            near(h,CrucibleDamage.blast(e,mob,local,true,.3f),local*.3,id+" PvE unchanged");
        }
        for(var wave:WaveFrameProfile.all()) {
            var e=WeaponCatalog.find(wave.id()).orElseThrow();float local=WeaponProfile.forEntry(e).damage();
            near(h,CrucibleDamage.wave(e,p,local,wave.directMultiplier()),damage(e,p,false,0),e.id()+" wave direct");
            near(h,CrucibleDamage.wave(e,p,local,wave.waveMultiplier()),damage(e,p,false,0),e.id()+" ground wave");
            near(h,CrucibleDamage.wave(e,mob,local,wave.directMultiplier()),local*wave.directMultiplier(),e.id()+" PvE split");
        }
        for(var e:WeaponCatalog.family("sword")) {
            float local=WeaponProfile.forEntry(e).damage();
            check(h,CrucibleDamage.melee(e,p,local*.35f)<p.getMaxHealth(),e.id()+" reduced energy not full-power one-shot");
        }
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w286_control", maxTicks=550)
    public void controlActualHealthAndPaidGrenadeDirectHit(GameTestHelper h) {
        check(h,CrucibleRuntime.snapshot().members().isEmpty(),"Run Control fixture alone");
        var server=h.getLevel().getServer();TowerSpawnWorld.open(server);
        var logins=new ArrayList<CrucibleW263GameTests.Login>();
        var owner=CrucibleW263GameTests.login(h,logins,"W286Owner",Element.SOLAR);
        var victim=CrucibleW263GameTests.login(h,logins,"W286Victim",Element.ARC);
        h.onEachTick(()->{for(var login:logins)CrucibleW263GameTests.tickLogin(server,login);});
        h.onEachTick(()->{if(h.getTick()>=494&&h.getTick()<=505)
            System.out.println("W286 shot tick="+h.getTick()+" owner="+owner.position()+" victim="+victim.position()
                    +" hp="+victim.getHealth()+" abs="+victim.getAbsorptionAmount()+" max="+victim.getMaxHealth()
                    +" flights="+WeaponRuntime.flights(owner)+" source="+victim.getLastDamageSource());});
        check(h,TowerSpawnWorld.teleport(owner)&&TowerSpawnWorld.teleport(victim),"Tower ready");
        var grenade=WeaponCatalog.find("salvager_s_salvo").orElseThrow();
        var gun=WeaponModels.withGrip(WeaponItems.create(grenade),WeaponModels.Grip.NATIVE).orElseThrow();
        WeaponAccuracy.setAirborneBonus(gun,100);
        int slot=WeaponCharacteristics.of(grenade).slot().hotbar();
        owner.getInventory().setItem(slot,gun);owner.getInventory().setSelectedSlot(slot);
        check(h,WeaponLoadout.equipHeld(owner)==null,"Equip before joining, so Control owns the legitimate first-life ammo grant");
        check(h,CrucibleRuntime.join(owner)&&CrucibleRuntime.join(victim),"Join opposing Control teams");
        h.runAfterDelay(450,()->{
            check(h,CrucibleRuntime.canFight(owner,victim),"Real Control combat admitted");
            victim.removeAllEffects();victim.getAttribute(Attributes.MAX_HEALTH).setBaseValue(20);
            victim.getAttribute(Attributes.MAX_ABSORPTION).setBaseValue(100);
            // Absorption prevents death while measuring every actual hurtServer contact, including overkill budgets.
            for(var e:WeaponCatalog.all()) if(WeaponCharacteristics.of(e).ammo()!=WeaponAmmoType.PRIMARY) {
                for(boolean head:new boolean[]{false,true}) {
                    victim.setHealth(20);victim.setAbsorptionAmount(100);
                    float amount=damage(e,victim,head,0);
                    check(h,!Combat.damage(owner.level(),owner,victim,amount,Element.KINETIC,AmmoGeneration.weapon(e)),e.id()+" shielded measurement remains nonlethal");
                    near(h,120-victim.getHealth()-victim.getAbsorptionAmount(),amount,e.id()+" actual health/absorption loss");
                }
            }
            victim.setHealth(20);victim.setAbsorptionAmount(0);
            var origin=owner.position().add(0,64,0);
            owner.setPos(origin);owner.setNoGravity(true);owner.setYRot(-90);owner.setXRot(0);owner.setYHeadRot(-90);
            victim.setPos(origin.add(3,0,0));victim.setNoGravity(true);
            check(h,owner.level().noCollision(owner,owner.getBoundingBox())
                    &&victim.level().noCollision(victim,victim.getBoundingBox()),"Both shot witnesses are outside arena geometry");
            check(h,owner.level().clip(new net.minecraft.world.level.ClipContext(owner.getEyePosition(),victim.getEyePosition(),
                    net.minecraft.world.level.ClipContext.Block.COLLIDER,net.minecraft.world.level.ClipContext.Fluid.NONE,owner))
                    .getType()==net.minecraft.world.phys.HitResult.Type.MISS,"Direct shot lane is clear of walls");
            check(h,owner.getMainHandItem()==gun&&WeaponItems.magazine(gun,WeaponProfile.forEntry(grenade)).rounds()==1,"Retain the real starting loaded cartridge");
            WeaponRuntime.tickPlayer(owner);
        });
        h.runAfterDelay(470,()->{
            check(h,!WeaponHandling.blocked(owner),"Real weapon draw has finished before ADS input");
            check(h,WeaponAiming.toggle(owner),"Start earned ADS");
        });
        h.runAfterDelay(495,()->{
            near(h,victim.getHealth(),20,"Uninjured target before the shot");
            check(h,WeaponAiming.progress(owner)==1&&WeaponAiming.coneDegrees(owner)==0,"Exact ADS shot");
            check(h,WeaponRuntime.beginUse(owner),"Accept real paid grenade");
            owner.startUsingItem(net.minecraft.world.InteractionHand.MAIN_HAND);
            check(h,WeaponRuntime.activeProjectiles(owner)==1,"One real projectile");
        });
        h.runAfterDelay(505,()->{
            near(h,victim.getHealth(),4,"Actual direct grenade removes exactly sixteen HP");
            check(h,WeaponRuntime.activeProjectiles(owner)==0,"Grenade retired after one impact");
            owner.stopUsingItem();WeaponRuntime.cleanup(owner);
            var mg=WeaponCatalog.find("hammerhead").orElseThrow();
            victim.setHealth(20);
            Combat.damage(owner.level(),owner,victim,damage(mg,victim,false,0),Element.KINETIC,AmmoGeneration.weapon(mg));
            near(h,victim.getHealth(),10,"First machine-gun body survives with ten HP");
            Combat.damage(owner.level(),owner,victim,damage(mg,victim,false,0),Element.KINETIC,AmmoGeneration.weapon(mg));
            check(h,!victim.isAlive(),"Second machine-gun body kills through real Combat/hurtServer");
            h.succeed();
        });
    }
}
