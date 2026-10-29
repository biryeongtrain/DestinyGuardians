package kim.biryeong.destiny.test;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.phys.Vec3;
import java.util.List;

public final class WeaponReloadW47GameTests {
    private static void check(GameTestHelper h,boolean ok,String text){h.assertTrue(ok,Component.literal(text));}
    private static ServerPlayer player(GameTestHelper h){
        var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,0);
        var e=WeaponCatalog.find("beloved").orElseThrow();var s=WeaponItems.create(e);
        WeaponItems.save(s,new WeaponMagazine(WeaponProfile.forEntry(e),0,3));
        p.setItemInHand(InteractionHand.MAIN_HAND,s);
        TestCleanup.register(h, ()->{WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});return p;
    }
    private static WeaponProfile profile(ItemStack s){return WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow());}
    private static boolean wrapper(ServerPlayer p,ItemStack s){
        var context=((PacketContextProvider)(Object)p.connection).getPacketContext();
        var wire=PolymerItemUtils.getPolymerItemStack(s,context,p.level().registryAccess());
        return WeaponFirstPersonHands.model(WeaponReloadPresentation.model(WeaponItems.entry(s).orElseThrow())).equals(wire.get(DataComponents.ITEM_MODEL));
    }

    @GameTest(structure="destiny-test:floor",maxTicks=150, environment = "destiny-test:w90_isolated")
    public void reloadUsesLiveWireWrapperActualDeadlineAndReadOnlyHud(GameTestHelper h){
        var p=player(h);var s=p.getMainHandItem();var f=profile(s);var original=s.get(DataComponents.ITEM_MODEL);
        check(h,WeaponRuntime.reload(p),"Real reload started");
        check(h,WeaponReloadPresentation.active(s)&&wrapper(p,s),"Live packet uses animated wrapper");
        for(int i=1;i<=f.reloadTicks()+1;i++)h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(Math.max(1,f.reloadTicks()/2),()->{
            var d=s.get(DataComponents.CUSTOM_MODEL_DATA);
            check(h,d.getFloat(1)>.2f&&d.getFloat(1)<.8f,"Real server deadline drives progress");
            var before=s.copy();CombatHud.update(p);CombatHud.update(p);
            check(h,ItemStack.matches(before,s),"HUD cannot advance reload or mutate presentation");
            check(h,AmmoHud.current(p).orElseThrow().rounds()==0,"No ammo before true finish");
        });
        h.runAfterDelay(f.reloadTicks()+2,()->{
            check(h,!WeaponRuntime.reloading(p)&&!WeaponReloadPresentation.active(s)&&!wrapper(p,s),"Finish restores original wire model");
            check(h,original.equals(s.get(DataComponents.ITEM_MODEL)),"Real identity never changed");
            check(h,WeaponItems.magazine(s,f).rounds()==3&&WeaponItems.magazine(s,f).reserve()==0,"Only real reload transfers three");h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void copiedSavedProgressAndPreviewNeverAuthorizeAnimation(GameTestHelper h){
        var p=player(h);var s=p.getMainHandItem();WeaponRuntime.reload(p);
        var copy=s.copy();check(h,!WeaponReloadPresentation.active(copy)&&!wrapper(p,copy),"Serialization/copy cannot clone identity authority");
        var started=s.copy();WeaponRuntime.cancelUseForSkill(p);
        check(h,!ItemStack.matches(started,s)&&s.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(1)==-1
                &&!wrapper(p,s),"Same-tick cancellation changes wire-cache key and restores original model");
        var preview=WeaponModels.create(WeaponItems.entry(s).orElseThrow());
        preview.set(DataComponents.CUSTOM_MODEL_DATA,new CustomModelData(List.of(9f,.8f),List.of(true),List.of("scope","other"),List.of(0xFFFFFF)));
        WeaponReloadPresentation.update(preview,true,.8f);
        check(h,!WeaponReloadPresentation.active(preview),"Preview cannot bind reload state");
        check(h,WeaponModels.setPose(preview,WeaponModels.Pose.HIP),"Known preview pose change");
        var d=preview.get(DataComponents.CUSTOM_MODEL_DATA);
        check(h,d.floats().equals(List.of(9f,.8f))&&d.flags().equals(List.of(true))&&d.colors().equals(List.of(0xFFFFFF))
                &&d.getString(1).equals("other"),"Pose preserves independent component slots");h.succeed();
    }

    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void swapSkillAndCleanupClearOldStackAndCannotTransferAmmo(GameTestHelper h){
        var p=player(h);var old=p.getMainHandItem();var f=profile(old);
        WeaponRuntime.reload(p);p.setItemInHand(InteractionHand.MAIN_HAND,old.copy());WeaponRuntime.tickPlayer(p);
        check(h,!WeaponReloadPresentation.active(old)&&!wrapper(p,old),"Old stack loses authority immediately on observed swap");
        check(h,WeaponItems.magazine(old,f).rounds()==0&&WeaponItems.magazine(old,f).reserve()==3,"Swap has no transfer");
        check(h,!WeaponRuntime.reload(p),"W58: replacement waits for ready, not free reload");
        h.runAfterDelay(WeaponHandling.remaining(p),()->{
            check(h,WeaponRuntime.reload(p),"Reload new held instance after ready");var current=p.getMainHandItem();
            WeaponRuntime.cancelUseForSkill(p);check(h,!WeaponReloadPresentation.active(current),"Skill clears presentation");
            check(h,WeaponRuntime.reload(p),"Reload can start again");WeaponRuntime.cleanup(p);
            check(h,!WeaponReloadPresentation.active(current)&&!WeaponRuntime.reloading(p),"Disconnect/death cleanup clears owned state");h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=25, environment = "destiny-test:w90_isolated")
    public void allOtherWeaponsKeepExistingIdentityGripAndWireModels(GameTestHelper h){
        var p=player(h);
        for(var e:WeaponCatalog.all()){
            if(WeaponReloadPresentation.supports(e))continue;
            var s=WeaponItems.create(e);var before=s.copy();WeaponReloadPresentation.update(s,true,.5f);
            check(h,!WeaponReloadPresentation.active(s)&&ItemStack.matches(before,s),"Unsupported item is untouched: "+e.id());
        }
        h.succeed();
    }
}
