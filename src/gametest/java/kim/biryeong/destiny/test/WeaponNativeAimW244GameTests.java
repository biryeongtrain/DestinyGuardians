package kim.biryeong.destiny.test;

import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPunchPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/** W244 live packet routing, attribute ownership and cancellation; framebuffer evidence is separate. */
public final class WeaponNativeAimW244GameTests {
    private static final Identifier SPEED=Identifier.fromNamespaceAndPath("destiny","weapon_ads_movement_w75");
    private static void check(GameTestHelper h,boolean value,String message) { h.assertTrue(value,Component.literal(message)); }
    private static void near(GameTestHelper h,double value,double expected,String message) { check(h,Math.abs(value-expected)<1e-7,message+": "+value+" != "+expected); }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static ServerPlayer player(GameTestHelper h,String id) {
        var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,0);
        p.setAttached(WeaponLoadout.ENABLED,false);p.setOnGround(true);
        p.setItemInHand(InteractionHand.MAIN_HAND,WeaponItems.create(entry(id)));
        TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);TestPlayers.remove(p);});
        WeaponRuntime.tickPlayer(p);return p;
    }
    private static void click(ServerPlayer p) { p.connection.handlePunch(ServerboundPunchPacket.INSTANCE); }
    private static void neutral(GameTestHelper h,ServerPlayer p) {
        check(h,!WeaponAiming.requested(p)&&!WeaponAiming.aimInput(p),"No retained ADS intent");
        check(h,!p.getAttribute(Attributes.MOVEMENT_SPEED).hasModifier(SPEED),"No owned slowdown");
        near(h,p.getAttribute(Attributes.SNEAKING_SPEED).getValue(),.3,"Native crouch untouched");
    }
    @GameTest(structure="destiny-test:floor",maxTicks=35,environment="destiny-test:w90_isolated")
    public void nativePunchTogglesWithoutShiftAndRepeatedHeldPunchesDoNotRetoggle(GameTestHelper h) {
        var p=player(h,"ace_of_spades");var stack=p.getMainHandItem();
        p.setShiftKeyDown(true);WeaponRuntime.tickPlayer(p);
        check(h,WeaponAiming.progress(p)==0,"Shift alone no longer enters ADS");p.setShiftKeyDown(false);
        click(p);click(p);
        check(h,WeaponAiming.requested(p)&&!p.isShiftKeyDown(),"Native punch starts ADS once without crouch");
        for(int i=1;i<=15;i++)h.runAfterDelay(i,()->{ click(p);WeaponRuntime.tickPlayer(p); });
        h.runAfterDelay(16,()->{
            check(h,WeaponAiming.progress(p)==1,"Continuous mining punches do not oscillate ADS");
            double ratio=WeaponNativeZoom.movementScalar(WeaponAimMovementProfile.scalar(entry("ace_of_spades")),WeaponAimProfile.of(entry("ace_of_spades")).zoom(),1);
            near(h,p.getAttribute(Attributes.MOVEMENT_SPEED).getValue(),.1*ratio,"Real speed drives native FOV");
            check(h,p.getMainHandItem()==stack,"Toggle never replaces weapon");
            near(h,p.getAttribute(Attributes.SNEAKING_SPEED).getValue(),.3,"No old Shift neutralizer");
        });
        h.runAfterDelay(19,()->{click(p);neutral(h,p);});
        for(int i=20;i<=29;i++)h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(30,()->{WeaponRuntime.tickPlayer(p);check(h,WeaponAiming.progress(p)==0,"Second click exits ADS");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=35,environment="destiny-test:w90_isolated")
    public void highZoomActuallyMovesSlowerAndReloadRequiresNewClick(GameTestHelper h) {
        var low=player(h,"ace_of_spades");var high=player(h,"izanagis_burden");click(low);click(high);
        for(int i=1;i<=12;i++)h.runAfterDelay(i,()->{WeaponRuntime.tickPlayer(low);WeaponRuntime.tickPlayer(high);});
        h.runAfterDelay(13,()->{
            check(h,WeaponAiming.progress(low)==1&&WeaponAiming.progress(high)==1,"Both transitions complete");
            check(h,high.getAttribute(Attributes.MOVEMENT_SPEED).getValue()<low.getAttribute(Attributes.MOVEMENT_SPEED).getValue(),"High magnification has greater actual slowdown");
            check(h,kim.biryeong.minigamelib.camera.api.CameraEffects.getFov(low)==null&&kim.biryeong.minigamelib.camera.api.CameraEffects.getFov(high)==null,"ADS never owns custom FOV transport");
            var profile=WeaponProfile.forEntry(entry("izanagis_burden"));WeaponItems.save(high.getMainHandItem(),new WeaponMagazine(profile,1,4));
            check(h,WeaponRuntime.reload(high),"Real reload starts");neutral(h,high);click(high);neutral(h,high);
            check(h,WeaponAiming.requested(low),"Other player's toggle preserved");
        });
        h.runAfterDelay(14,()->{WeaponRuntime.tickPlayer(high);neutral(h,high);WeaponAiming.suspend(low);neutral(h,low);h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30,environment="destiny-test:w90_isolated")
    public void stowRoundTripAndDeathDoNotResumeOldToggle(GameTestHelper h) {
        var p=player(h,"ace_of_spades");click(p);
        h.runAfterDelay(4,()->{
            WeaponRuntime.tickPlayer(p);check(h,WeaponAiming.progress(p)>0,"Positive ADS session");
            var original=p.getMainHandItem();WeaponAiming.inventoryStowing(p,original);
            p.setItemInHand(InteractionHand.MAIN_HAND,new ItemStack(Items.DIAMOND));p.setItemInHand(InteractionHand.MAIN_HAND,original);
            neutral(h,p);WeaponRuntime.tickPlayer(p);neutral(h,p);
            click(p);check(h,WeaponAiming.requested(p),"Fresh click legitimately enters again");
        });
        h.runAfterDelay(8,()->{p.setHealth(0);WeaponRuntime.tickPlayer(p);p.setHealth(20);WeaponRuntime.tickPlayer(p);neutral(h,p);h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30,environment="destiny-test:w90_isolated")
    public void foreignMovementObjectSurvivesCleanupAndShiftPacketDoesNotReleaseToggle(GameTestHelper h) {
        var p=player(h,"ace_of_spades");click(p);
        h.runAfterDelay(5,()->{
            WeaponRuntime.tickPlayer(p);check(h,WeaponAiming.progress(p)>0,"Live ADS before Shift input");
            p.connection.handlePlayerInput(new net.minecraft.network.protocol.game.ServerboundPlayerInputPacket(Input.EMPTY));
            check(h,WeaponAiming.requested(p),"Ordinary movement packet does not release click toggle");
            var speed=p.getAttribute(Attributes.MOVEMENT_SPEED);speed.removeModifier(SPEED);
            var foreign=new AttributeModifier(SPEED,-.12,AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);speed.addTransientModifier(foreign);
            WeaponRuntime.tickPlayer(p);WeaponAiming.cleanup(p);
            check(h,speed.getModifier(SPEED)==foreign,"Cleanup preserves exact foreign modifier");speed.removeModifier(SPEED);
            near(h,speed.getValue(),.1,"Native base restored after fixture owner cleanup");h.succeed();
        });
    }
}
