package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.OptionalInt;

public final class FallbackAimW45GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) { h.assertTrue(ok, Component.literal(message)); }
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2, 1, 6), 0, 0);
        TestCleanup.register(h, () -> {
            Guardians.runtime(p).superSession = null;
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            TestPlayers.remove(p);
        });
        return p;
    }
    private static void equip(ServerPlayer p, String id) {
        p.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(WeaponCatalog.find(id).orElseThrow()));
    }
    private static boolean shown(ServerPlayer p) { return DisplayHud.getHud(p, FallbackAimHud.ID) != null; }

    @GameTest(structure="destiny-test:floor", maxTicks=20, environment = "destiny-test:w90_isolated")
    public void savedScopeWithoutItsSessionCannotLeaveFreshlyBoundWeaponInvisible(GameTestHelper h) {
        var p=player(h);equip(p,"beloved");var stack=p.getMainHandItem();
        WeaponModels.setPose(stack,WeaponModels.Pose.SCOPE);
        var model=stack.get(net.minecraft.core.component.DataComponents.ITEM_MODEL);
        var profile=WeaponProfile.forEntry(WeaponCatalog.find("beloved").orElseThrow());
        var rounds=WeaponItems.magazine(stack,profile).rounds();
        WeaponRuntime.tickPlayer(p);CombatHud.update(p);
        check(h,!WeaponAiming.scoped(p)&&!WeaponScopes.scoped(stack)
                &&"hip".equals(stack.get(net.minecraft.core.component.DataComponents.CUSTOM_MODEL_DATA).getString(0)),
                "Fresh binding clears persisted scope selector even without a new crouch edge");
        check(h,model.equals(stack.get(net.minecraft.core.component.DataComponents.ITEM_MODEL))
                &&WeaponItems.magazine(stack,profile).rounds()==rounds,"Recovery changes no identity or ammunition");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=30, environment = "destiny-test:w90_isolated")
    public void ordinaryHandsKeepOneStableReadOnlyAimPointAndCleanupIsPlayerLocal(GameTestHelper h) {
        var a=player(h);var b=player(h);
        a.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.DIAMOND, 3));
        var before=a.getMainHandItem().copy();
        CombatHud.update(a);CombatHud.update(b);
        var dot=DisplayHud.getHud(a,FallbackAimHud.ID);
        check(h,dot!=null && dot.isAboveHand() && dot.getLocation().x()==960 && dot.getLocation().y()==540,
                "Ordinary items and empty hands keep an above-hand aim point");
        CombatHud.update(a);CombatHud.update(a);
        check(h,DisplayHud.getHud(a,FallbackAimHud.ID)==dot && ItemStack.matches(before,a.getMainHandItem()),
                "Stable display identity, no item mutations");
        FallbackAimHud.remove(b);FallbackAimHud.remove(b);
        check(h,shown(a)&&!shown(b),"Cleanup does not remove another player's aim point");
        CombatHud.remove(a);check(h,!shown(a)&&dot.isRemoved(),"Combat cleanup removes fallback too");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=30, environment = "destiny-test:w90_isolated")
    public void actualWeaponSightSuppressesFallbackButFiniteSuperKeepsAimWithoutChangingItsShots(GameTestHelper h) {
        var p=player(h);equip(p,"austringer");CombatHud.update(p);
        check(h,!shown(p)&&DisplayHud.getHud(p,WeaponReticleHud.CENTER_ID)!=null,"No duplicate dot over gun reticle");
        p.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);
        Guardians.runtime(p).superSession=new SuperSession() {
            public boolean tick(){return true;} public void primary(){} public void end(){} public float remaining(){return 1;}
            public OptionalInt ammunition(){return OptionalInt.of(3);} public int ammunitionCapacity(){return 3;}
        };
        CombatHud.update(p);
        check(h,!shown(p)&&DisplayHud.getHud(p,WeaponReticleHud.CENTER_ID)!=null
                &&AmmoHud.current(p).orElseThrow().rounds()==3,"Finite super owns its aim point without duplicate fallback or changed actual ammunition");
        Guardians.runtime(p).superSession=null;equip(p,"beloved");CombatHud.update(p);
        check(h,!shown(p),"Weapon-specific sight owns aim after super ends");
        var profile=WeaponProfile.forEntry(WeaponCatalog.find("beloved").orElseThrow());
        WeaponItems.save(p.getMainHandItem(),new WeaponMagazine(profile,1,2));
        check(h,WeaponRuntime.reload(p),"Actual reload starts");CombatHud.update(p);
        check(h,!shown(p)&&DisplayHud.getHud(p,WeaponReticleHud.CENTER_ID)==null,"Reload does not invent another sight");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=40, environment = "destiny-test:w90_isolated")
    public void scopedSightHasNoFallbackAndDeathOrSpectatorClearsAllAimOwners(GameTestHelper h) {
        var a=player(h);var b=player(h);
        for(var p:List.of(a,b)){equip(p,"beloved");ads(p, true);}
        for(int i=1;i<=22;i++)h.runAfterDelay(i,()-> {
            for(var p:List.of(a,b)){WeaponRuntime.tickPlayer(p);CombatHud.update(p);}
        });
        h.runAfterDelay(23,()-> {
            for(var p:List.of(a,b))check(h,WeaponAiming.scoped(p)&&!shown(p),"Hollow scope does not receive fallback center fill");
            a.setHealth(0);b.setGameMode(GameType.SPECTATOR);
            for(var p:List.of(a,b)){
                WeaponAiming.tick(p);CombatHud.update(p);
                check(h,!WeaponAiming.scoped(p)&&!shown(p)&&DisplayHud.getHud(p,WeaponScopeHud.CENTER_ID)==null
                        &&DisplayHud.getHud(p,WeaponReticleHud.CENTER_ID)==null,"Death/spectator clears aim HUD ownership");
            }
            h.succeed();
        });
    }
}
