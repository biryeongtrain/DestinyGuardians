package kim.biryeong.destiny.test;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

public final class FirstPersonHandsW201GameTests {
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=160)
    public void realPolymerReloadCarriesHandsWithoutMutatingInventoryOrCreditingAmmunition(GameTestHelper h){
        var p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,0);
        var e=WeaponCatalog.find("ace_of_spades").orElseThrow();var gun=WeaponItems.create(e);
        var profile=WeaponProfile.forEntry(e);WeaponItems.save(gun,new WeaponMagazine(profile,5,0));
        p.setItemInHand(InteractionHand.MAIN_HAND,gun);
        TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);TestPlayers.remove(p);});
        var context=((PacketContextProvider)(Object)p.connection).getPacketContext();
        var canonical=gun.get(DataComponents.ITEM_MODEL);var before=gun.copy();
        var idle=PolymerItemUtils.getPolymerItemStack(gun,context,p.level().registryAccess());
        h.assertTrue(WeaponFirstPersonHands.model(canonical).equals(idle.get(DataComponents.ITEM_MODEL)),Component.literal("Final Polymer carrier includes glove wrapper"));
        h.assertTrue(ItemStack.matches(before,gun),Component.literal("Cosmetic conversion leaves authoritative inventory unchanged"));
        h.assertTrue(WeaponRuntime.reload(p),Component.literal("Real existing reload starts"));
        var route=WeaponFirstPersonHands.model(WeaponReloadPresentation.model(e));
        var live=PolymerItemUtils.getPolymerItemStack(gun,context,p.level().registryAccess());
        h.assertTrue(route.equals(live.get(DataComponents.ITEM_MODEL)),Component.literal("Authorized reload gets hand overlay"));
        h.assertTrue(WeaponItems.magazine(gun,profile).rounds()==5,Component.literal("Projection never pays ammunition"));
        for(int i=1;i<=profile.reloadTicks()+1;i++)h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(profile.reloadTicks()+2,()->{
            var end=PolymerItemUtils.getPolymerItemStack(gun,context,p.level().registryAccess());
            h.assertTrue(!WeaponRuntime.reloading(p)&&!WeaponReloadPresentation.active(gun),Component.literal("Original reload retires"));
            h.assertTrue(WeaponFirstPersonHands.model(canonical).equals(end.get(DataComponents.ITEM_MODEL))&&canonical.equals(gun.get(DataComponents.ITEM_MODEL)),Component.literal("Idle gloves return while inventory identity remains canonical"));
            h.assertTrue(WeaponItems.magazine(gun,profile).rounds()==13,Component.literal("Original commit fills magazine once"));
            h.succeed();
        });
    }
}
