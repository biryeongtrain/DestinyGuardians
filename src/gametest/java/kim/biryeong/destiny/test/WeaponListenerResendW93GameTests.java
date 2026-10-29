package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.*;
import net.minecraft.resources.Identifier;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

/** Real listener use/correction sequence and native encoded frames, not OS/native-key proof. */
public final class WeaponListenerResendW93GameTests {
    private static void check(GameTestHelper h, boolean yes, String why) { h.assertTrue(yes, Component.literal(why)); }
    private static Identifier id(String path) { return Identifier.parse("destiny:" + path); }
    private static int slot(InventoryWireW92 w) { return w.player.inventoryMenu.findSlot(w.player.getInventory(), 0).orElseThrow(); }
    private static List<ClientboundContainerSetSlotPacket> slots(List<Packet<?>> packets) {
        return packets.stream().filter(ClientboundContainerSetSlotPacket.class::isInstance)
                .map(ClientboundContainerSetSlotPacket.class::cast).toList();
    }
    private static InventoryWireW92 equip(GameTestHelper h, int n, String name, WeaponModels.Grip grip) {
        var w = new InventoryWireW92(h, new Vec3(4 + n * 6, 4, 8));
        w.player.setAttached(WeaponLoadout.ENABLED, false);
        var stack = WeaponModels.withGrip(WeaponItems.create(WeaponCatalog.find(name).orElseThrow()), grip).orElseThrow();
        w.player.getInventory().setItem(0, stack); w.player.getInventory().setSelectedSlot(0);
        w.player.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.EMERALD, 3));
        WeaponRuntime.tickPlayer(w.player); w.full();
        h.onEachTick(()->{
            var b=w.player.getBoundingBox();var o=h.absoluteVec(Vec3.ZERO);
            check(h,w.player.level()==h.getLevel() && b.minX>o.x && b.maxX<o.x+48
                    && b.minY>o.y && b.maxY<o.y+12 && b.minZ>o.z && b.maxZ<o.z+32,
                    "Entire owned resend fixture player stays inside isolated deck");
        });
        return w;
    }
    private static void deck(GameTestHelper h) {
        for (int x=0; x<48; x++) for (int z=0; z<32; z++) h.setBlock(x,3,z,Blocks.STONE);
    }
    private static void use(InventoryWireW92 w, InteractionHand hand, int sequence) {
        w.player.connection.handleUseItem(new ServerboundUseItemPacket(hand, sequence, -90, -80));
    }
    private static void frame(GameTestHelper h, InventoryWireW92 w, ClientboundContainerSetSlotPacket packet,
                              Identifier model, int expectedSlot, int stateId) {
        check(h, packet.getContainerId()==w.player.inventoryMenu.containerId && packet.getSlot()==expectedSlot
                && packet.getStateId()==stateId, "Resend preserves native inventory container/slot/stateId");
        check(h, projected(model).equals(packet.getItem().get(DataComponents.ITEM_MODEL)),
                "Actual client decode retains live model " + model + "; actual " + packet.getItem().get(DataComponents.ITEM_MODEL));
        var source=w.player.getMainHandItem();var wire=packet.getItem();
        check(h, wire.is(WeaponModels.twoHanded(source)?Items.CROSSBOW:Items.STICK)
                && !wire.is(WeaponCombatItem.INSTANCE), "Real native encoder gives vanilla carrier, not server restoration");
        var a=source.get(DataComponents.CUSTOM_MODEL_DATA);var b=wire.get(DataComponents.CUSTOM_MODEL_DATA);
        check(h, a.floats().equals(b.floats()) && a.strings().equals(b.strings()) && a.colors().equals(b.colors()),
                "Correction carries actual selector and unrelated data");
    }

    @GameTest(structure="destiny-test:w78_floor", environment="destiny-test:w90_isolated", maxTicks=35)
    public void secondConsumedUseBeforeClientTickEndPreservesActualAdsAndBowModels(GameTestHelper h) {
        deck(h);
        var wires=List.of(equip(h,0,"ammit_ar2",WeaponModels.Grip.NATIVE),
                equip(h,1,"ammit_ar2",WeaponModels.Grip.TWO_HAND),
                equip(h,2,"biting_winds",WeaponModels.Grip.NATIVE),
                equip(h,3,"whispering_slab",WeaponModels.Grip.NATIVE));
        for (int i=0;i<2;i++) ads(wires.get(i).player, true);
        for (int i=2;i<wires.size();i++) {
            var w=wires.get(i);
            WeaponCombatItem.INSTANCE.use(h.getLevel(),w.player,InteractionHand.MAIN_HAND);
            w.player.stopUsingItem();WeaponRuntime.tickPlayer(w.player);
        }
        // Polymer resend is inventory-menu layout even while a chest is current.
        wires.get(1).player.containerMenu=ChestMenu.threeRows(9,wires.get(1).player.getInventory());
        for (int tick=1;tick<=12;tick++) h.runAfterDelay(tick,()->{
            for(var w:wires) WeaponRuntime.tickPlayer(w.player);
        });
        h.runAfterDelay(13,()->{
            for(int i=0;i<wires.size();i++) {
                var w=wires.get(i);var source=w.player.getMainHandItem();
                var expected=i<2?aimRoute("ammit_ar2",false):id("weapon_bow_w50/"+WeaponItems.entry(source).orElseThrow().id());
                check(h,i<2?WeaponAimPresentation.ownedBy(w.player,source):WeaponBowPresentation.ownedBy(w.player,source),
                        "Real production ADS/loaded-bow binding acquired before listener packets, case " + i);
                w.player.connection.handleClientTickEnd(ServerboundClientTickEndPacket.INSTANCE);w.discard();
                use(w,InteractionHand.MAIN_HAND,1); // Real CONSUME stored by Polymer's use wrapper.
                check(h,w.player.isUsingItem()==!WeaponModels.twoHanded(source),"Native consumable hold vs crossbow heartbeat stays distinct");
                w.discard();var before=source.copy();int state=w.player.inventoryMenu.getStateId();
                use(w,InteractionHand.MAIN_HAND,2); // Same client tick: concrete Polymer correction trigger.
                var sent=slots(w.capture());
                check(h,sent.size()==1,"Second consumed interaction emits exactly one actual correction; actual "+sent.size());
                frame(h,w,sent.getFirst(),expected,slot(w),state+1);
                check(h,ItemStack.matches(source,before),"Suppressed duplicate cannot fire/spend/change the canonical source");
                // Offhand correction remains slot45, not the selected main-hand projection.
                use(w,InteractionHand.OFF_HAND,3);var off=slots(w.capture());
                check(h,off.size()==1 && off.getFirst().getSlot()==45 && off.getFirst().getItem().is(Items.EMERALD)
                        && ItemStack.matches(off.getFirst().getItem(),w.player.getOffhandItem()),
                        "Offhand correction remains unchanged vanilla emerald data");
                w.player.connection.handleClientTickEnd(ServerboundClientTickEndPacket.INSTANCE);w.discard();
                use(w,InteractionHand.MAIN_HAND,4);
                check(h,slots(w.capture()).isEmpty(),"First use after real client-tick reset does not take previous-result resend branch");
            }
            h.succeed();
        });
    }

    @GameTest(structure="destiny-test:w78_floor", environment="destiny-test:w90_isolated", maxTicks=35)
    public void recipientListenerPreservesHeaderCallbackAndRejectsStaleOtherSlotsWhileRawConnectionRemainsControl(GameTestHelper h) {
        deck(h);var w=equip(h,0,"ammit_ar2",WeaponModels.Grip.TWO_HAND);
        var other=new InventoryWireW92(h,new Vec3(16,4,8));
        ads(w.player, true);
        for(int tick=1;tick<=12;tick++) h.runAfterDelay(tick,()->WeaponRuntime.tickPlayer(w.player));
        h.runAfterDelay(13,()->{
            var source=w.player.getMainHandItem();var before=source.copy();var model=aimRoute("ammit_ar2",false);w.discard();
            int state=w.player.inventoryMenu.getStateId();var callbacks=new AtomicInteger();
            w.player.connection.send(new ClientboundContainerSetSlotPacket(0,state,slot(w),source),future->callbacks.incrementAndGet());
            var sent=slots(w.capture());check(h,sent.size()==1,"Listener emits one native correction");
            frame(h,w,sent.getFirst(),model,slot(w),state);check(h,callbacks.get()==1,"Original send callback executes exactly once");
            // Deliberately bypass the recipient listener: W92's raw copy control must still fail closed.
            w.connection.send(new ClientboundContainerSetSlotPacket(0,state,slot(w),source));
            var raw=slots(w.capture());check(h,raw.size()==1 && projected(source.get(DataComponents.ITEM_MODEL)).equals(raw.getFirst().getItem().get(DataComponents.ITEM_MODEL)),
                    "Raw Connection constructor/copy control stays canonical, no global codec/constructor rewrite");
            var stale=source.copy();stale.set(DataComponents.CUSTOM_NAME,Component.literal("stale"));
            w.player.connection.send(new ClientboundContainerSetSlotPacket(0,state,slot(w),stale));
            var rejected=slots(w.capture());check(h,rejected.size()==1 && projected(source.get(DataComponents.ITEM_MODEL)).equals(rejected.getFirst().getItem().get(DataComponents.ITEM_MODEL)),
                    "Component-stale snapshot cannot borrow current live ownership");
            for(int otherSlot:List.of(45,9)) {
                w.player.connection.send(new ClientboundContainerSetSlotPacket(0,state,otherSlot,source));
                var otherFrames=slots(w.capture());check(h,otherFrames.size()==1 && otherFrames.getFirst().getSlot()==otherSlot
                        && projected(source.get(DataComponents.ITEM_MODEL)).equals(otherFrames.getFirst().getItem().get(DataComponents.ITEM_MODEL)),
                        "Offhand/nonselected slot payload never becomes selected-hand authority");
            }
            var wrong=new ClientboundContainerSetSlotPacket(-1,state,slot(w),source);
            check(h,WeaponOutboundPresentation.projectPacket(w.player,wrong)==wrong,"Cursor/unknown-container packet stays the exact original packet");
            // A stale emitting listener still references A, but sends through another
            // owned fixture channel. A's current connection/context remain fully valid.
            var current=w.player.connection;
            var staleListener=new net.minecraft.server.network.ServerGamePacketListenerImpl(
                    h.getLevel().getServer(),other.connection,w.player,
                    net.minecraft.server.network.CommonListenerCookie.createInitial(w.player.getGameProfile(),false));
            // Native constructor installs itself on the player; emulate a retired
            // listener by restoring the still-live A listener before the actual send.
            w.player.connection=current;
            check(h,w.player.connection==current,"Stale-listener fixture does not replace A's actual current listener");
            other.discard();
            staleListener.send(new ClientboundContainerSetSlotPacket(0,state,slot(w),source));
            var staleWire=slots(other.capture());
            check(h,staleWire.size()==1 && projected(source.get(DataComponents.ITEM_MODEL)).equals(staleWire.getFirst().getItem().get(DataComponents.ITEM_MODEL)),
                    "Stale emitting listener cannot borrow A's otherwise-valid current recipient context");
            check(h,w.player.getMainHandItem()==source && ItemStack.matches(source,before),"No listener repair mutates authoritative components/ammo/identity");
            h.succeed();
        });
    }
}
