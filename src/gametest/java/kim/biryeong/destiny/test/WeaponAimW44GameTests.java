package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.minigamelib.camera.api.CameraEffects;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

public final class WeaponAimW44GameTests {
    private static void check(GameTestHelper h,boolean c,String m) {h.assertTrue(c,Component.literal(m));}
    private static WeaponCatalog.Entry entry(String id){return WeaponCatalog.find(id).orElseThrow();}
    private static ServerPlayer player(GameTestHelper h,String id) {
        var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,0);
        p.setItemInHand(InteractionHand.MAIN_HAND,WeaponItems.create(entry(id)));
        TestCleanup.register(h, ()-> {WeaponRuntime.cleanup(p);CameraEffects.resetFov(p);TestPlayers.remove(p);});return p;
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30,skyAccess=true, environment = "destiny-test:w90_isolated")
    public void realAdsShotUsesSeparateFalloffScalarNotCosmeticModelOrZoom(GameTestHelper h) {
        var p=player(h,"austringer");
        // Embedded TestPlayers do not run vanilla ground-contact ticks. This fixture stands on
        // the floor; full ADS removes hip spread but must not bypass the independent AE term.
        p.setOnGround(true);ads(p, true);p.setXRot(-90);
        var e=h.spawn(net.minecraft.world.entity.EntityTypes.HUSK,new Vec3(2.5,27,6.5));
        e.setNoAi(true);e.setNoGravity(true);
        e.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH).setBaseValue(1000);
        e.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.ARMOR).setBaseValue(0);e.setHealth(1000);
        TestCleanup.register(h, e::discard);
        for(int i=1;i<=12;i++)h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(13,()-> {
            check(h,WeaponAiming.progress(p)==1,"Real left-click toggle reaches ADS");
            check(h,p.onGround()&&!WeaponAccuracy.airborne(p)&&WeaponAiming.coneDegrees(p)==0,
                    "Grounded full ADS has an exact ray; no airborne-effectiveness spread in this range fixture");
            var origin=p.getEyePosition();var direction=WeaponAiming.direction(p);
            // WeaponRuntime.trace uses ProjectileUtil with a .03f hitscan AABB margin.
            // Use that geometric entry distance, rather than the uninflated target feet.
            var contact=e.getBoundingBox().inflate(.03f).clip(origin,origin.add(direction.scale(64))).orElseThrow();
            check(h,Math.abs(contact.y-(e.getBoundingBox().minY-.03f))<.000001,
                    "Exact upward ray enters the lower hitscan boundary, independently establishing a body hit");
            double distance=origin.distanceTo(contact);
            var hip=WeaponBallistics.of(entry("austringer"));
            var expected=WeaponAiming.ballistics(p,entry("austringer"));
            double rangeScalar=WeaponAimProfile.of(entry("austringer")).falloffScalar();
            check(h,Math.abs(expected.start()-hip.start()*rangeScalar)<.000001
                            &&Math.abs(expected.end()-hip.end()*rangeScalar)<.000001
                            &&expected.floor()==hip.floor()&&expected.precision()==hip.precision(),
                    "Full ADS scales only falloff distances by the authored range scalar");
            float damage=expected.damage(7,distance,false);
            check(h,damage>hip.damage(7,distance,false),"ADS retains more damage than hip at this distance");
            var stack=p.getMainHandItem();var profile=WeaponProfile.forEntry(entry("austringer"));
            int loaded=WeaponItems.magazine(stack,profile).rounds();float before=e.getHealth();
            check(h,before==1000&&loaded>0,"Pristine living target and funded authoritative magazine before paid shot");
            p.gameMode.useItem(p,h.getLevel(),stack,InteractionHand.MAIN_HAND);
            check(h,WeaponItems.magazine(stack,profile).rounds()==loaded-1,"Real item use pays exactly one cartridge");
            float actual=before-e.getHealth();
            check(h,Math.abs(actual-damage)<.002,"Actual HP uses ADS body falloff: expected="+damage
                    +", actual="+actual+", distance="+distance+", contact="+contact+", direction="+direction);h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void crouchAimsWithoutReloadThenReleaseRestoresPose(GameTestHelper h) {
        var p=player(h,"austringer");var stack=p.getMainHandItem();
        p.setShiftKeyDown(true); WeaponRuntime.tickPlayer(p);
        check(h,!WeaponAiming.requested(p)&&WeaponAiming.progress(p)==0,"Shift alone stays crouch, never ADS");
        p.setShiftKeyDown(false);
        var profile=WeaponProfile.forEntry(entry("austringer"));WeaponItems.save(stack,new WeaponMagazine(profile,2,5));
        ads(p, true);
        check(h,WeaponAiming.requested(p)&&!WeaponRuntime.reloading(p),"Left-click requests ADS without reload");
        h.runAfterDelay(1,()-> {
            WeaponRuntime.tickPlayer(p);
            check(h,WeaponAiming.progress(p)>0&&!WeaponRuntime.reloading(p),"Next actual tick advances accepted ADS");
        });
        h.runAfterDelay(12,()-> {
            WeaponRuntime.tickPlayer(p); // Dummy players are not registered in the actual server list.
            check(h,WeaponAiming.progress(p)>0,"Timed ADS is live");
            p.gameMode.useItem(p,h.getLevel(),stack,InteractionHand.MAIN_HAND);
            check(h,WeaponItems.magazine(stack,profile).rounds()==1&&!WeaponRuntime.reloading(p),"RMB while ADS fires instead of reloading");
            p.releaseUsingItem();ads(p, false);
        });
        for(int i=1;i<=30;i++)h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(31,()-> {
            check(h,WeaponAiming.progress(p)==0,"Release returns hip");
            check(h,stack.get(DataComponents.CUSTOM_MODEL_DATA).getString(0).equals("hip"),"HIP selector restored");h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=20, environment = "destiny-test:w90_isolated")
    public void qAndCtrlQReloadNeverDiscardEvenOnFailureAndNonweaponStillDrops(GameTestHelper h) {
        var p=player(h,"beloved");var stack=p.getMainHandItem();var profile=WeaponProfile.forEntry(entry("beloved"));
        WeaponItems.save(stack,new WeaponMagazine(profile,1,2));
        check(h,InputRouter.onPlayerAction(p,ServerboundPlayerActionPacket.Action.DROP_ITEM),"Q packet intercepted");
        check(h,p.getMainHandItem()==stack&&WeaponRuntime.reloading(p),"Q starts reload preserving actual stack");
        check(h,InputRouter.onPlayerAction(p,ServerboundPlayerActionPacket.Action.DROP_ALL_ITEMS),"Ctrl Q also intercepted");
        check(h,WeaponItems.magazine(stack,profile).rounds()==1,"No early ammo or drop");
        p.setItemInHand(InteractionHand.MAIN_HAND,new ItemStack(Items.DIAMOND));
        check(h,!InputRouter.onPlayerAction(p,ServerboundPlayerActionPacket.Action.DROP_ITEM),"Ordinary items keep vanilla drop");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void successfulShotSendsRelativeRotationWithoutTeleportAndDryFireDoesNot(GameTestHelper h) {
        var p=player(h,"austringer");WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);
        float yaw=p.getYRot(),pitch=p.getXRot();Vec3 pos=p.position();
        check(h,WeaponRuntime.beginUse(p),"Real shot accepted");
        var packets=TestPlayers.outbound(p);
        check(h,packets.stream().anyMatch(x->x instanceof ClientboundPlayerRotationPacket),"Actual rotation packet emitted");
        check(h,packets.stream().noneMatch(x->x instanceof ClientboundPlayerPositionPacket),"Recoil never teleports");
        check(h,p.getXRot()<pitch&&p.position().equals(pos),"Server aim changes, body does not");
        check(h,WeaponAiming.bloom(p)>0,"Actual shot adds bloom");
        p.releaseUsingItem();WeaponRuntime.releaseUse(p,p.getMainHandItem());TestPlayers.drain(p);
        WeaponRuntime.beginUse(p);
        check(h,TestPlayers.outbound(p).stream().noneMatch(x->x instanceof ClientboundPlayerRotationPacket),"Cooldown rejection emits no recoil");h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30, environment = "destiny-test:w90_isolated")
    public void previewPoseNeverGrantsAdsFalloffAndNeutralFamiliesRemainNeutral(GameTestHelper h) {
        var p=player(h,"austringer");WeaponModels.setPose(p.getMainHandItem(),WeaponModels.Pose.ADS);
        check(h,WeaponAiming.progress(p)==0,"OP cosmetic pose is not ADS input");
        check(h,WeaponAiming.ballistics(p,entry("austringer")).equals(WeaponBallistics.of(entry("austringer"))),"No cosmetic range exploit");
        p.setItemInHand(InteractionHand.MAIN_HAND,WeaponModels.create(entry("austringer")));ads(p, true);WeaponAiming.tick(p);
        check(h,WeaponAiming.progress(p)==0,"Preview never binds aiming state");
        for(String family:new String[]{"glaive","sword"}) {
            var e=WeaponCatalog.family(family).getFirst();p.setItemInHand(InteractionHand.MAIN_HAND,WeaponItems.create(e));WeaponAiming.tick(p);
            check(h,WeaponAiming.progress(p)==0,"Excluded family "+family);
        }h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=45, environment = "destiny-test:w90_fov_w44")
    public void fovIsRestoredAndExternalOwnershipIsNotOverwritten(GameTestHelper h) {
        var config=kim.biryeong.minigamelib.shaderfx.impl.ModConfig.getInstance();boolean old=config.dynamicFovShader;
        config.dynamicFovShader=true;TestCleanup.register(h, ()->config.dynamicFovShader=old);
        var p=player(h,"austringer");CameraEffects.setFov(p,80);ads(p, true);
        for(int i=1;i<=12;i++)h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(13,()-> {
            check(h,CameraEffects.getFov(p)==80 && WeaponAiming.progress(p)==1,"Native ADS progresses without owning the shader FOV API");
            WeaponAiming.suspend(p);check(h,CameraEffects.getFov(p)==80,"Prior override restored");
            ads(p, false);
        });
        h.runAfterDelay(14,()-> {WeaponRuntime.tickPlayer(p);ads(p, true);});
        for(int i=15;i<=26;i++)h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(27,()-> {CameraEffects.setFov(p,55);WeaponAiming.tick(p);WeaponAiming.cleanup(p);
            check(h,CameraEffects.getFov(p)==55,"External shader FOV survives ADS cleanup");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30, environment = "destiny-test:w90_isolated")
    public void reloadAndStackSwapClearRealAdsAndDoNotTransferProgress(GameTestHelper h) {
        var p=player(h,"austringer");ads(p, true);
        for(int i=1;i<=12;i++)h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(13,()-> {
            var stack=p.getMainHandItem();var profile=WeaponProfile.forEntry(entry("austringer"));
            WeaponItems.save(stack,new WeaponMagazine(profile,1,5));
            check(h,WeaponAiming.progress(p)==1,"ADS reaches full transition");
            check(h,WeaponRuntime.reload(p)&&WeaponAiming.progress(p)==0,"Reload cancels ADS immediately");
            WeaponRuntime.tickPlayer(p);check(h,WeaponAiming.progress(p)==0,"Held crouch cannot re-enter canceled ADS");
            p.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);WeaponRuntime.tickPlayer(p);
            check(h,WeaponAiming.progress(p)==0,"Swap removes session");h.succeed();
        });
    }
}
