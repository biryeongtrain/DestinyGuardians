package kim.biryeong.destiny.test;

import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.state.properties.SlabType;
import net.minecraft.world.phys.Vec3;

/** Calls actual ServerPlayer.doTick -> Player.tick -> vanilla pose resolution.
 * Never invokes the cosmetic updater or forces the desired pose in the acceptance action.
 */
public final class WeaponPoseTransitionW162GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static ServerPlayer player(GameTestHelper h, String name) {
        var p=TestPlayers.create(h,new Vec3(2,2,2),0,0,name);
        p.setNoGravity(true); p.setAttached(WeaponLoadout.ENABLED,false);
        TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);TestPlayers.remove(p);});
        return p;
    }
    private static ItemStack gun(ServerPlayer p,String id) {
        var stack=WeaponItems.create(WeaponCatalog.find(id).orElseThrow());
        stack=WeaponModels.withGrip(stack,WeaponModels.Grip.TWO_HAND).orElseThrow();
        p.getInventory().setItem(0,stack);p.getInventory().setSelectedSlot(0);
        return stack;
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=20)
    public void realPlayerTickPublishesPoseBeforeRuntimeTick(GameTestHelper h) {
        var p=player(h,"W162_transition");var stack=gun(p,"ammit_ar2");
        var before=stack.copy();var entry=WeaponItems.entry(stack).orElseThrow();var profile=WeaponProfile.forEntry(entry);
        p.setShiftKeyDown(true);p.doTick();
        check(h,p.getPose()==Pose.CROUCHING && WeaponCrouchPresentation.crouched(stack),
                "Actual vanilla resolution publishes crouch without a later WeaponRuntime.tickPlayer call");
        p.setShiftKeyDown(false);p.doTick();
        check(h,p.getPose()==Pose.STANDING && !WeaponCrouchPresentation.crouched(stack),
                "Actual stand resolution clears compensation in that player tick");
        check(h,WeaponItems.magazine(stack,profile).rounds()==WeaponItems.magazine(before,profile).rounds()
                && !p.isUsingItem() && !WeaponRuntime.reloading(p) && p.getCamera()==p,
                "Pose publication cannot fire/spend/reload/start use or replace camera");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=20)
    public void lowCeilingRetainsActualCrouchAfterInputRelease(GameTestHelper h) {
        var p=player(h,"W162_clearance");var stack=gun(p,"ammit_ar2");
        p.setShiftKeyDown(true);p.doTick();
        check(h,p.isCrouching() && WeaponCrouchPresentation.crouched(stack),"Crouch admitted");
        var ceiling=new BlockPos(2,3,2);
        h.setBlock(ceiling,Blocks.STONE_SLAB.defaultBlockState().setValue(SlabBlock.TYPE,SlabType.TOP));
        p.setShiftKeyDown(false);p.doTick();
        check(h,p.isCrouching() && WeaponCrouchPresentation.crouched(stack),
                "Key release under a 1.5-block ceiling must not claim standing");
        h.setBlock(ceiling,Blocks.AIR);p.doTick();
        check(h,!p.isCrouching() && !WeaponCrouchPresentation.crouched(stack),"Clearance permits standing and clears flag");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=20)
    public void otherWeaponDataIsUntouchedByPoseHook(GameTestHelper h) {
        var p=player(h,"W162_other");var stack=gun(p,"the_recluse");
        var data=new CustomModelData(java.util.List.of(7f),java.util.List.of(true,false,true),
                java.util.List.of("hip","other"),java.util.List.of(0xABCDEF));
        stack.set(DataComponents.CUSTOM_MODEL_DATA,data);
        p.setShiftKeyDown(true);p.doTick();p.setShiftKeyDown(false);p.doTick();
        check(h,data.equals(stack.get(DataComponents.CUSTOM_MODEL_DATA)),"Unrelated weapon flags/components preserved");
        h.succeed();
    }
}
