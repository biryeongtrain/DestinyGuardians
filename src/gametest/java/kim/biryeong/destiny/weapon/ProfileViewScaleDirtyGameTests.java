package kim.biryeong.destiny.weapon;

import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.util.Brightness;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import org.joml.Matrix4f;
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.List;

/** Native dirty-data oracle. These displays are never spawned and no fake socket is claimed. */
public final class ProfileViewScaleDirtyGameTests {
    private static final class RecordingHud extends ItemDisplayHud {
        final List<List<SynchedEntityData.DataValue<?>>> batches=new ArrayList<>();
        @Override public void update() {
            var dirty=getDisplay().getEntityData().packDirty();
            if(dirty!=null&&!dirty.isEmpty())batches.add(dirty);
        }
    }
    private static void check(GameTestHelper h,boolean condition,String message) {h.assertTrue(condition,Component.literal(message));}

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=30)
    public void unchangedTargetsAreSilentWhileMarkersAndItemOnlyChangesStillFlush(GameTestHelper h) {
        var hud=new RecordingHud();hud.updateWhenDataChanged(false);
        hud.getDisplay().getEntityData().packDirty();
        var state=new ProfileWeaponView.TransformState();var pose=new Matrix4f().translation(.5f,-.5f,-.75f);
        ProfileWeaponView.apply(hud,state,pose,false);
        check(h,hud.batches.size()==1,"Initial target has one native metadata batch");hud.batches.clear();
        for(int i=0;i<200;i++)ProfileWeaponView.apply(hud,state,new Matrix4f(pose),false);
        check(h,hud.batches.isEmpty(),"200 unchanged targets cannot force-dirty interpolation start");

        hud.getDisplay().setBrightnessOverride(new Brightness(1,2));
        ProfileWeaponView.apply(hud,state,pose,false);
        check(h,hud.batches.size()==1&&hud.batches.getFirst().size()==1,
                "A marker-only change flushes without a transform restart");hud.batches.clear();

        var item=new ItemStack(Items.STICK);item.set(DataComponents.ITEM_NAME,Component.literal("changed presentation"));
        var shown=ProfileWeaponView.setItem(hud,state,item,ItemStack.EMPTY);
        ProfileWeaponView.apply(hud,state,pose,false);
        var expected=new Vector3f(16000,-10016000,-24000);
        check(h,hud.batches.size()==1&&hud.batches.getFirst().stream().anyMatch(value->
                        value.value() instanceof Vector3f vector&&vector.equals(expected)),
                "Item setter resets the HUD location, so the raw profile target must be restored in the same batch");
        check(h,hud.getItem().getHoverName().getString().equals("changed presentation"),"Actual item-only change is retained");
        hud.batches.clear();
        shown=ProfileWeaponView.setItem(hud,state,item.copy(),shown);
        ProfileWeaponView.apply(hud,state,pose,false);
        check(h,hud.batches.isEmpty(),"Equivalent item copies cannot restart the stable view");

        ProfileWeaponView.apply(hud,state,new Matrix4f(pose).translate(.1f,0,0),true);
        check(h,hud.batches.size()==1&&hud.getInterpolationDuration()==1,"Moving target retains one-tick interpolation");
        h.succeed();
    }
}
