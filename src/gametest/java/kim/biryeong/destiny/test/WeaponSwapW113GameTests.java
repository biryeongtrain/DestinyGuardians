package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.projected;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** All ten added routes through actual Handling/recipient-scoped Polymer encoding. Not pixels/IK. */
public final class WeaponSwapW113GameTests {
    private static final String FLOOR="destiny-test:w109_arena", ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why) { h.assertTrue(ok,Component.literal(why)); }
    private record Swap(ServerPlayer p,ItemStack from,ItemStack to,String path,int stow,int ready,int rounds,int reserve) {}
    private static WeaponCatalog.Entry entry(ItemStack s) { return WeaponItems.entry(s).orElseThrow(); }
    private static WeaponMagazine ammo(ItemStack s) { return WeaponItems.magazine(s,WeaponProfile.forEntry(entry(s))); }
    private static ItemStack wire(ServerPlayer p,ItemStack s) {
        return PolymerItemUtils.getPolymerItemStack(s,((PacketContextProvider)(Object)p.connection).getPacketContext(),p.level().registryAccess());
    }
    private static Swap start(GameTestHelper h,String from,String to,WeaponModels.Grip grip) {
        var p=TestPlayers.create(h,new Vec3(24,1,24),0,-85,"WS113_"+UUID.randomUUID().toString().substring(0,7));
        p.setNoGravity(true);
        var a=WeaponItems.create(WeaponCatalog.find(from).orElseThrow());
        var b=WeaponModels.withGrip(WeaponItems.create(WeaponCatalog.find(to).orElseThrow()),grip).orElseThrow();
        p.getInventory().setItem(0,a);p.getInventory().setItem(1,b);p.getInventory().setSelectedSlot(0);
        p.setAttached(WeaponLoadout.ENABLED,false);WeaponRuntime.tickPlayer(p);
        TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);TestPlayers.remove(p);});
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));WeaponRuntime.tickPlayer(p);
        return new Swap(p,a,b,"destiny:weapon_swap_w113/"+from+"_to_"+to,
                WeaponHandlingProfile.of(entry(a)).stowTicks(),WeaponHandlingProfile.of(entry(b)).readyTicks(),ammo(b).rounds(),ammo(b).reserve());
    }
    private static void validate(GameTestHelper h,Swap s,int elapsed) {
        var p=s.p;WeaponRuntime.tickPlayer(p);var before=s.to.copy();
        if(elapsed<s.stow+s.ready) {
            var phase=elapsed<s.stow?WeaponSwapCycle.Phase.STOW:WeaponSwapCycle.Phase.READY;
            check(h,WeaponHandling.presentation(p).orElseThrow().phase()==phase,"Existing phase clock");
            check(h,WeaponSwapPresentation.active(s.to)&&WeaponSwapPresentation.model(s.to).toString().equals(s.path),"Exact new pair route");
            check(h,WeaponSwapPresentation.ownedBy(p,s.to)&&!WeaponSwapPresentation.active(s.to.copy()),"Exact owned object only, copies cannot borrow presentation");
            for(int i=0;i<3;i++) {
                var out=wire(p,s.to);
                check(h,out.get(DataComponents.ITEM_MODEL).equals(projected(net.minecraft.resources.Identifier.parse(s.path))),"Production Polymer transport selects new graph");
                check(h,out.is(WeaponModels.twoHanded(s.to)?Items.CROSSBOW:Items.STICK),"Actual current carrier");
            }
            check(h,!WeaponRuntime.beginUse(p)&&!WeaponRuntime.reload(p),"Cosmetic graph cannot bypass original handling deadlines");
        } else {
            check(h,!WeaponSwapPresentation.active(s.to)&&!WeaponHandling.blocked(p),"Actual ready deadline retires presentation");
            check(h,wire(p,s.to).get(DataComponents.ITEM_MODEL).equals(projected(s.to.get(DataComponents.ITEM_MODEL))),"Exact original incoming item graph restored");
        }
        check(h,ItemStack.matches(before,s.to)&&ammo(s.to).rounds()==s.rounds&&ammo(s.to).reserve()==s.reserve,
                "Wire/queries leave all components and actual ammunition unchanged");TestPlayers.drain(p);
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=40)
    public void tenNewDirectionsBothCarriersKeepActualClockCostOwnershipAndFallback(GameTestHelper h) {
        var swaps=new ArrayList<Swap>();var ids=List.of("austringer","beloved","ammit_ar2","the_recluse");
        for(String from:ids)for(String to:ids)if(!from.equals(to)&&!(Set.of(from,to).equals(Set.of("austringer","beloved"))))
            for(var grip:WeaponModels.Grip.values())swaps.add(start(h,from,to,grip));
        check(h,swaps.size()==20,"Ten directions and both incoming carriers");
        for(var s:swaps)validate(h,s,0);
        for(int i=1;i<=24;i++){int elapsed=i;h.runAfterDelay(i,()->{
            for(var s:swaps)validate(h,s,elapsed);
            if(elapsed==24)h.succeed();
        });}
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=25)
    public void newRouteCancellationRestoresUnrelatedSlotsAndCannotLeakToOtherOwner(GameTestHelper h) {
        var s=start(h,"ammit_ar2","the_recluse",WeaponModels.Grip.TWO_HAND);validate(h,s,0);
        var other=TestPlayers.create(h,new Vec3(3,1,3),0,-85);
        TestCleanup.register(h,()->{WeaponRuntime.cleanup(other);TestPlayers.remove(other);});
        check(h,!WeaponSwapPresentation.ownedBy(other,s.to),"Foreign recipient cannot use live route");
        other.getInventory().setItem(0,s.to.copy());
        check(h,wire(other,other.getMainHandItem()).get(DataComponents.ITEM_MODEL).equals(projected(s.to.get(DataComponents.ITEM_MODEL))),
                "Persisted/copy selector falls back for another owner");
        var floats=s.to.get(DataComponents.CUSTOM_MODEL_DATA).floats();
        var unowned=floats.subList(0,Math.min(5,floats.size()));
        WeaponRuntime.cleanup(s.p);
        check(h,!WeaponSwapPresentation.active(s.to),"Owner cleanup retires route");
        var restored=s.to.get(DataComponents.CUSTOM_MODEL_DATA).floats();
        check(h,restored.subList(0,Math.min(5,restored.size())).equals(unowned),"Only owned selector5 restored");h.succeed();
    }
}
