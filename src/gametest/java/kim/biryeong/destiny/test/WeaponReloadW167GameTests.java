package kim.biryeong.destiny.test;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.phys.Vec3;
import java.util.List;

/** Actual server reload ownership and paid ammunition; not a native keyboard/render claim. */
public final class WeaponReloadW167GameTests {
    static final String FLOOR="destiny-test:floor", ENV="destiny-test:w90_isolated";
    static void check(GameTestHelper h, boolean yes, String why) { h.assertTrue(yes,Component.literal(why)); }
    static Identifier model(String id) { return WeaponGripGameTests.projected(MagazineReloadW114GameTests.expectedReloadRoute(id)); }
    static ServerPlayer player(GameTestHelper h,String id) {
        var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,0);
        var e=WeaponCatalog.find(id).orElseThrow(); var s=WeaponItems.create(e);
        WeaponItems.save(s,new WeaponMagazine(WeaponProfile.forEntry(e),2,0));
        p.setItemInHand(InteractionHand.MAIN_HAND,s);
        TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        return p;
    }
    static ItemStack wire(ServerPlayer p,ItemStack s) {
        var context=((PacketContextProvider)(Object)p.connection).getPacketContext();
        return PolymerItemUtils.getPolymerItemStack(s,context,p.level().registryAccess());
    }
    static WeaponProfile profile(ItemStack s) { return WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow()); }
    static void actual(GameTestHelper h,String id) {
        var p=player(h,id);var s=p.getMainHandItem();var profile=profile(s);var canonical=s.get(DataComponents.ITEM_MODEL);
        check(h,WeaponRuntime.reload(p),"Real reload accepted");
        check(h,WeaponReloadPresentation.ownedBy(p,s)&&model(id).equals(wire(p,s).get(DataComponents.ITEM_MODEL)),"Actual Polymer owner gets the authored reload route with first-person hands");
        check(h,canonical.equals(s.get(DataComponents.ITEM_MODEL)),"Live reload never changes server canonical identity");
        var copy=s.copy();
        check(h,!WeaponReloadPresentation.active(copy)&&WeaponGripGameTests.projected(canonical).equals(wire(p,copy).get(DataComponents.ITEM_MODEL)),"Persisted selector alone has no live authority or reload wire route");
        for(int i=1;i<=profile.reloadTicks()+1;i++)h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(profile.reloadTicks()/2,()->{
            var progress=s.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(1);
            check(h,progress!=null&&progress>.2f&&progress<.8f&&WeaponReloadPresentation.ownedBy(p,s),"Real server progress drives midpoint sample");
        });
        h.runAfterDelay(profile.reloadTicks()+2,()->{
            check(h,!WeaponRuntime.reloading(p)&&!WeaponReloadPresentation.active(s),"Full recovery retires motion");
            check(h,WeaponGripGameTests.projected(canonical).equals(wire(p,s).get(DataComponents.ITEM_MODEL))&&canonical.equals(s.get(DataComponents.ITEM_MODEL)),"Canonical identity and idle wire route restored");
            check(h,WeaponItems.magazine(s,profile).rounds()==profile.magazine(),"Existing primary reload fills only at existing credit/recovery lifecycle");
            h.succeed();
        });
    }
    static void cancel(GameTestHelper h,String id) {
        var p=player(h,id);var s=p.getMainHandItem();check(h,WeaponRuntime.reload(p),"Reload accepted");
        WeaponRuntime.cancelUseForSkill(p);
        check(h,!WeaponReloadPresentation.active(s)&&!WeaponReloadPresentation.ownedBy(p,s),"Ability cancel retires binding immediately");
        check(h,WeaponGripGameTests.projected(s.get(DataComponents.ITEM_MODEL)).equals(wire(p,s).get(DataComponents.ITEM_MODEL))&&s.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(1)==-1,"No lingering open part");
        check(h,WeaponItems.magazine(s,profile(s)).rounds()==2,"Early cancellation cannot fund ammunition");
        check(h,WeaponRuntime.reload(p),"Second reload accepted");var copy=s.copy();p.setItemInHand(InteractionHand.MAIN_HAND,copy);WeaponRuntime.tickPlayer(p);
        check(h,!WeaponReloadPresentation.active(s)&&!WeaponReloadPresentation.active(copy),"Actual stack replacement invalidates old owner and copied selector");h.succeed();
    }
    static void cosmetic(GameTestHelper h,String id) {
        var p=player(h,id);var s=p.getMainHandItem();
        s.set(DataComponents.CUSTOM_MODEL_DATA,new CustomModelData(List.of(9f,.7f,5f,.3f),List.of(true),List.of("hip","other"),List.of(0x123456)));
        WeaponReloadPresentation.update(s,true,.5f);var d=s.get(DataComponents.CUSTOM_MODEL_DATA);
        check(h,d.floats().equals(List.of(9f,.5f,5f,.3f))&&d.flags().equals(List.of(true))&&d.strings().equals(List.of("hip","other"))&&d.colors().equals(List.of(0x123456)),"Only reload progress slot1 changes");
        check(h,!WeaponReloadPresentation.ownedBy(p,s),"Cosmetic helper cannot authorize wire model");WeaponReloadPresentation.clear(s);
        var preview=WeaponModels.create(WeaponCatalog.find(id).orElseThrow());var before=preview.copy();WeaponReloadPresentation.update(preview,true,.5f);
        check(h,!WeaponReloadPresentation.active(preview)&&ItemStack.matches(preview,before),"OP preview is inert");
        check(h,WeaponItems.magazine(s,profile(s)).rounds()==2,"No cosmetic ammo transfer");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=150,environment=ENV) public void coldDenialActualReload(GameTestHelper h){actual(h,"cold_denial");}
    @GameTest(structure=FLOOR,maxTicks=15,environment=ENV) public void coldDenialCancelAndReplacement(GameTestHelper h){cancel(h,"cold_denial");}
    @GameTest(structure=FLOOR,maxTicks=10,environment=ENV) public void coldDenialCosmeticIsolation(GameTestHelper h){cosmetic(h,"cold_denial");}
}
