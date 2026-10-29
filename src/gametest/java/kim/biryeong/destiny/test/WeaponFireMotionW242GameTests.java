package kim.biryeong.destiny.test;

import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;

/** Accepted runtime emissions and exact-stack retirement, separate from actual framebuffer QA. */
public final class WeaponFireMotionW242GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) { h.assertTrue(ok,Component.literal(message)); }
    private static ServerPlayer player(GameTestHelper h) { return player(h,"ace_of_spades"); }
    private static ServerPlayer player(GameTestHelper h,String weapon) {
        var p=TestPlayers.create(h,new Vec3(2.5,4,6.5),-90,0);
        p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,false);
        p.setItemInHand(InteractionHand.MAIN_HAND,WeaponItems.create(WeaponCatalog.find(weapon).orElseThrow()));
        WeaponRuntime.tickPlayer(p);
        TestCleanup.register(h,()->{WeaponFireMotion.clear(p);WeaponRuntime.cleanup(p);TestPlayers.remove(p);});
        return p;
    }
    private static int impulses(ServerPlayer p) {
        try {
            var f=WeaponFireMotion.class.getDeclaredField("LIVE");f.setAccessible(true);var controller=f.get(null);
            var m=controller.getClass().getDeclaredMethod("count",Object.class);m.setAccessible(true);return (int)m.invoke(controller,p.getUUID());
        } catch(ReflectiveOperationException e) {throw new AssertionError(e);}
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30,environment="destiny-test:w90_isolated")
    public void paidShotMovesRootWithoutAComponentSelectorAndDeniedRepeatAddsNothing(GameTestHelper h) {
        var p=player(h);var stack=p.getMainHandItem();var profile=WeaponProfile.forEntry(WeaponCatalog.find("ace_of_spades").orElseThrow());
        int before=WeaponItems.magazine(stack,profile).rounds();
        check(h,WeaponRuntime.beginUse(p),"Actual trigger accepted");
        check(h,impulses(p)==1,"One paid emission creates one source impulse");
        WeaponRuntime.beginUse(p);
        check(h,impulses(p)==1&&WeaponItems.magazine(stack,profile).rounds()==before-1,"Repeated held input spends no extra round or visual impulse");
        h.runAfterDelay(2,()->{
            var data=stack.get(DataComponents.CUSTOM_MODEL_DATA);var a=WeaponFireMotion.matrix(p);var b=WeaponFireMotion.matrix(p);
            check(h,!a.equals(new Matrix4f(),1e-6f),"Accepted source root has advanced");
            check(h,a.equals(b,0)&&java.util.Objects.equals(data,stack.get(DataComponents.CUSTOM_MODEL_DATA)),"Detached observation changes no selector or clock");
            WeaponRuntime.inventoryStowing(p,stack);
            check(h,impulses(p)==0&&WeaponFireMotion.matrix(p).equals(new Matrix4f(),0),"Same-object stow cannot resurrect recoil");
            h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30,environment="destiny-test:w90_isolated")
    public void acceptedReloadRetiresRootAndStaleSourceCannotStartNewMotion(GameTestHelper h) {
        var p=player(h);check(h,WeaponRuntime.beginUse(p),"Actual trigger accepted");
        check(h,impulses(p)==1,"Source impulse exists before reload");
        check(h,WeaponRuntime.reload(p),"Partially empty actual weapon reload accepted");
        check(h,impulses(p)==0,"Reload removes playback rather than merely hiding its matrix");
        var e=WeaponCatalog.find("ace_of_spades").orElseThrow();var profile=WeaponProfile.forEntry(e);
        check(h,WeaponFireMotion.matrix(p).equals(new Matrix4f(),0),"Reload never displays a firing root");
        WeaponFireMotion.clear(p);p.setItemInHand(InteractionHand.MAIN_HAND,net.minecraft.world.item.ItemStack.EMPTY);
        WeaponFireMotion.emitted(p,e,profile,true,0);check(h,impulses(p)==0,"Stale non-held source cannot start motion");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30,environment="destiny-test:w90_isolated")
    public void emptyRocketAutoReloadKeepsPaidShotRecoveryWithoutDelayingAmmo(GameTestHelper h) {
        var p=player(h,"bad_omens");var entry=WeaponCatalog.find("bad_omens").orElseThrow();
        check(h,WeaponRuntime.beginUse(p),"Loaded rocket accepts native trigger");
        check(h,impulses(p)==1,"One paid rocket starts one source curve");
        WeaponRuntime.tickPlayer(p);
        check(h,WeaponRuntime.reloading(p),"Automatic empty-magazine reload starts without visual delay");
        check(h,WeaponItems.magazine(p.getMainHandItem(),WeaponProfile.forEntry(entry)).rounds()==0,"No cosmetic ammo credit");
        check(h,impulses(p)==1,"Automatic reload retains the already-paid source recovery");
        h.runAfterDelay(2,()->{
            check(h,!WeaponFireMotion.matrix(p).equals(new Matrix4f(),1e-6f),"Rocket recovery remains visible during automatic reload");
            WeaponAiming.suspend(p);
            check(h,impulses(p)==0,"Skill/manual suspension still clears the automatic recovery");
            h.succeed();
        });
    }

}
