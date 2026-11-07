package kim.biryeong.destiny.fx;

import com.mojang.datafixers.util.Pair;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.*;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.*;
import net.minecraft.world.item.component.CustomData;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.function.Predicate;
import java.util.function.UnaryOperator;

import static org.junit.jupiter.api.Assertions.*;

class SwordHandPacketsW139Test {
    static final Predicate<ItemStack> OWNED = s -> !s.isEmpty() && s.is(Items.STICK) && s.getCount() == 2;
    static final UnaryOperator<Packet<?>> SAME = UnaryOperator.identity();
    @BeforeAll static void bootstrap() {
        net.minecraft.SharedConstants.tryDetectVersion(); net.minecraft.server.Bootstrap.bootStrap();
        // 26.3 binds default item components from data packs, absent in pure JUnit.
        // These packet fixtures use explicit components, not runtime item defaults.
        for (var item : List.of(Items.STICK, Items.PAPER, Items.DIAMOND, Items.APPLE)) {
            var holder = (net.minecraft.core.Holder.Reference<Item>) net.minecraft.core.registries.BuiltInRegistries.ITEM.wrapAsHolder(item);
            if (!holder.areComponentsBound()) holder.bindComponents(net.minecraft.core.component.DataComponentMap.EMPTY);
        }
    }
    static ItemStack weapon() { return new ItemStack(Items.STICK, 2); }
    static Packet<?> transform(Packet<?> p, UnaryOperator<Packet<?>> bm) {
        return SwordHandPackets.transform(p, 42, bm, OWNED);
    }
    @Test void slotRestoresCapturedCarrierWithoutChangingStateOrComponents() {
        var item = weapon(); item.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "weapon/crown_splitter"));
        var in = new ClientboundContainerSetSlotPacket(0, 19, 36, item);
        var out = (ClientboundContainerSetSlotPacket) transform(in,
                p -> new ClientboundContainerSetSlotPacket(0, 19, 36, ItemStack.EMPTY));
        assertTrue(ItemStack.matches(in.getItem(), out.getItem())); assertEquals(19, out.getStateId());
        assertEquals(item.get(DataComponents.ITEM_MODEL), out.getItem().get(DataComponents.ITEM_MODEL));
    }
    @Test void genuineClearOtherContainersCursorAndUnownedItemsStayEmpty() {
        for (int container : List.of(0, 1, -1)) for (int slot : List.of(-1, 0, 5, 35, 36, 44, 45))
            for (var item : List.of(ItemStack.EMPTY, new ItemStack(Items.STICK), new ItemStack(Items.PAPER))) {
                var out = (ClientboundContainerSetSlotPacket) transform(new ClientboundContainerSetSlotPacket(container, 3, slot, item),
                        p -> new ClientboundContainerSetSlotPacket(container, 3, slot, ItemStack.EMPTY));
                assertTrue(out.getItem().isEmpty());
            }
        for (int slot : List.of(35, 45)) assertTrue(((ClientboundContainerSetSlotPacket) transform(
                new ClientboundContainerSetSlotPacket(0, 3, slot, weapon()),
                p -> new ClientboundContainerSetSlotPacket(0, 3, slot, ItemStack.EMPTY))).getItem().isEmpty());
    }
    @Test void contentMutationCannotDestroyOriginalOrRestoreArmorOrCursor() {
        var items = new ArrayList<>(Collections.nCopies(46, ItemStack.EMPTY));
        items.set(5, weapon()); items.set(36, weapon()); items.set(44, weapon()); items.set(45, weapon());
        var cursor = new ItemStack(Items.DIAMOND);
        var in = new ClientboundContainerSetContentPacket(0, 7, items, cursor);
        var out = (ClientboundContainerSetContentPacket) transform(in, p -> {
            var content = (ClientboundContainerSetContentPacket) p;
            assertNotSame(in.items(), content.items());
            for (int slot : List.of(5, 36, 44, 45)) content.items().set(slot, ItemStack.EMPTY);
            return content;
        });
        assertFalse(in.items().get(36).isEmpty()); assertFalse(in.items().get(5).isEmpty());
        assertFalse(out.items().get(36).isEmpty()); assertFalse(out.items().get(44).isEmpty());
        assertTrue(out.items().get(5).isEmpty()); assertTrue(out.items().get(45).isEmpty());
        assertSame(cursor, out.carriedItem()); assertEquals(7, out.stateId()); assertEquals(46, out.items().size());
    }
    @Test void changedStateOrSlotNeverRecoversAStaleSnapshot() {
        var in = new ClientboundContainerSetSlotPacket(0, 5, 36, weapon());
        for (var out : List.of(new ClientboundContainerSetSlotPacket(0, 6, 36, ItemStack.EMPTY),
                new ClientboundContainerSetSlotPacket(0, 5, 37, ItemStack.EMPTY)))
            assertSame(out, transform(in, p -> out));
    }
    @Test void selfEquipmentIsRemovedNotReplacedAndObserversStayHidden() {
        var self = new ClientboundSetEquipmentPacket(42, List.of(Pair.of(EquipmentSlot.HEAD, ItemStack.EMPTY),
                Pair.of(EquipmentSlot.MAINHAND, ItemStack.EMPTY), Pair.of(EquipmentSlot.OFFHAND, ItemStack.EMPTY)));
        var out = (ClientboundSetEquipmentPacket) transform(self, SAME);
        assertEquals(List.of(EquipmentSlot.HEAD, EquipmentSlot.OFFHAND), out.getSlots().stream().map(Pair::getFirst).toList());
        var observer = new ClientboundSetEquipmentPacket(99, self.getSlots());
        assertSame(observer, transform(observer, SAME));
        assertNull(transform(new ClientboundSetEquipmentPacket(42, List.of(Pair.of(EquipmentSlot.MAINHAND, weapon()))), SAME));
    }
    @Test void nestedBundlesFilterWithoutRehandlingOrMutatingSiblings() {
        var main = new ClientboundSetEquipmentPacket(42, List.of(Pair.of(EquipmentSlot.MAINHAND, ItemStack.EMPTY)));
        var other = new ClientboundSetEquipmentPacket(99, main.getSlots());
        var nested = new ClientboundBundlePacket(List.of(main, other));
        var bundle = new ClientboundBundlePacket(List.of(nested, other));
        int[] calls = {0};
        var out = (ClientboundBundlePacket) transform(bundle, p -> { calls[0]++; return p; });
        assertEquals(1, calls[0]);
        var children = new ArrayList<Packet<? super ClientGamePacketListener>>(); out.subPackets().forEach(children::add);
        assertEquals(2, children.size()); assertSame(other, children.get(1));
        var grandchildren = new ArrayList<Packet<? super ClientGamePacketListener>>();
        ((ClientboundBundlePacket) children.getFirst()).subPackets().forEach(grandchildren::add);
        assertEquals(List.of(other), grandchildren);
        assertEquals(2, ((Collection<?>) nested.subPackets()).size());
    }
    @Test void bothPacketOrdersAndARealDropNeverResurrectCachedSword() {
        var inventory = new ClientboundContainerSetSlotPacket(0, 9, 36, weapon());
        var equipment = new ClientboundSetEquipmentPacket(42, List.of(Pair.of(EquipmentSlot.MAINHAND, ItemStack.EMPTY)));
        for (var order : List.of(List.of(inventory, equipment), List.of(equipment, inventory))) {
            int nonempty = 0;
            for (Packet<?> p : order) {
                Packet<?> out = transform(p, q -> q instanceof ClientboundContainerSetSlotPacket
                        ? new ClientboundContainerSetSlotPacket(0, 9, 36, ItemStack.EMPTY) : q);
                if (out instanceof ClientboundContainerSetSlotPacket slot && !slot.getItem().isEmpty()) nonempty++;
            }
            assertEquals(1, nonempty);
            var drop = new ClientboundContainerSetSlotPacket(0, 10, 36, ItemStack.EMPTY);
            assertSame(drop, transform(drop, SAME));
        }
    }
    @Test void identityAdmissionRejectsOrdinaryAndPreviewButAcceptsNativeAndProjectedCombat() {
        var plain = Identifier.withDefaultNamespace("stick");
        var combat = Identifier.fromNamespaceAndPath("destiny", "weapon_combat");
        var preview = Identifier.fromNamespaceAndPath("destiny", "weapon_preview");
        assertFalse(SwordHandPackets.combatIdentity(plain, null));
        assertFalse(SwordHandPackets.combatIdentity(plain, preview));
        assertTrue(SwordHandPackets.combatIdentity(combat, null));
        assertTrue(SwordHandPackets.combatIdentity(plain, combat));
    }
    @Test void capturedCarrierRetainsUseComponentAndPolymerDataVerbatim() {
        // Pure packet fixture. Actual Polymer API admission requires Fabric and is
        // covered by the native Crown/Falling session, not simulated here.
        var carrier = weapon();
        var inner = new CompoundTag(); inner.putString("id", "destiny:weapon_combat");
        var outer = new CompoundTag(); outer.put("$polymer:stack", inner);
        carrier.set(DataComponents.CUSTOM_DATA, CustomData.of(outer));
        carrier.set(DataComponents.CONSUMABLE, net.minecraft.world.item.component.Consumable.builder().consumeSeconds(3600).build());
        var before = new ClientboundContainerSetSlotPacket(0, 12, 44, carrier);
        var after = (ClientboundContainerSetSlotPacket) transform(before,
                p -> new ClientboundContainerSetSlotPacket(0, 12, 44, ItemStack.EMPTY));
        assertTrue(after.getItem().has(DataComponents.CONSUMABLE));
        assertTrue(ItemStack.matches(carrier, after.getItem()));
    }
    @Test void lifecyclePublicationPrecedesCreationAndRetirementFollowsClose() throws Exception {
        var source = Files.readString(Path.of("src/main/java/kim/biryeong/destiny/fx/PlayerAnimations.java"));
        assertTrue(source.indexOf("SwordHandPackets.begin(player)") < source.indexOf("clip.renderer.getOrCreate"));
        assertTrue(source.contains("state.handProtection = handProtection"));
        var close = source.substring(source.indexOf("private static void close(Playback"));
        assertTrue(close.indexOf("state.tracker.close()") < close.indexOf("SwordHandPackets.end(state.handProtection)"));
        var helper = Files.readString(Path.of("src/main/java/kim/biryeong/destiny/fx/SwordHandPackets.java"));
        assertTrue(helper.contains("PROTECTED.remove(protection.connection, protection)"));
        assertTrue(helper.contains("loop.execute(action)"));
        assertTrue(helper.contains("PolymerItemUtils.getPolymerIdentifier(stack)"));
    }
    @Test void projectedCorrectionConcealsOnlyModelAndDoesNotMutateSource() {
        var combat = Identifier.fromNamespaceAndPath("destiny", "weapon_combat");
        var carrier = weapon();
        carrier.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "weapon/crown_splitter"));
        carrier.set(DataComponents.CONSUMABLE, net.minecraft.world.item.component.Consumable.builder().consumeSeconds(3600).build());
        var inner = new CompoundTag(); inner.putString("id", combat.toString());
        var outer = new CompoundTag(); outer.put("$polymer:stack", inner);
        carrier.set(DataComponents.CUSTOM_DATA, CustomData.of(outer));
        var original = carrier.copy();
        var hidden = SwordHandPackets.concealProjected(carrier, combat);
        assertNotSame(carrier, hidden);
        assertEquals(Identifier.fromNamespaceAndPath("destiny", "weapon_sword_hand_empty"), hidden.get(DataComponents.ITEM_MODEL));
        assertEquals(carrier.get(DataComponents.CONSUMABLE), hidden.get(DataComponents.CONSUMABLE));
        assertEquals(carrier.get(DataComponents.CUSTOM_DATA), hidden.get(DataComponents.CUSTOM_DATA));
        assertEquals(carrier.getCount(), hidden.getCount());
        hidden.set(DataComponents.ITEM_MODEL, carrier.get(DataComponents.ITEM_MODEL));
        assertTrue(ItemStack.matches(original, hidden));
        assertTrue(ItemStack.matches(original, carrier));
        assertSame(carrier, SwordHandPackets.concealProjected(carrier, null));
        assertSame(carrier, SwordHandPackets.concealProjected(carrier, Identifier.fromNamespaceAndPath("destiny", "weapon_preview")));
        assertSame(ItemStack.EMPTY, SwordHandPackets.concealProjected(ItemStack.EMPTY, null));
    }
    @Test void bothRestorationPathsUseCapturedPresentationWithoutLiveReads() {
        var combat = Identifier.fromNamespaceAndPath("destiny", "weapon_combat");
        UnaryOperator<ItemStack> hide = s -> SwordHandPackets.concealProjected(s, combat);
        var emptyModel = Identifier.fromNamespaceAndPath("destiny", "weapon_sword_hand_empty");
        var carrier = weapon();
        carrier.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "weapon/falling_guillotine"));
        var slot = new ClientboundContainerSetSlotPacket(0, 21, 36, carrier);
        var restored = (ClientboundContainerSetSlotPacket) SwordHandPackets.transform(slot, 42,
                p -> new ClientboundContainerSetSlotPacket(0, 21, 36, ItemStack.EMPTY), OWNED, hide);
        assertEquals(emptyModel, restored.getItem().get(DataComponents.ITEM_MODEL));
        assertNotEquals(emptyModel, slot.getItem().get(DataComponents.ITEM_MODEL));
        var items = new ArrayList<>(Collections.nCopies(46, ItemStack.EMPTY)); items.set(44, carrier);
        var content = new ClientboundContainerSetContentPacket(0, 22, items, ItemStack.EMPTY);
        var full = (ClientboundContainerSetContentPacket) SwordHandPackets.transform(content, 42, p -> {
            ((ClientboundContainerSetContentPacket) p).items().set(44, ItemStack.EMPTY); return p;
        }, OWNED, hide);
        assertEquals(emptyModel, full.items().get(44).get(DataComponents.ITEM_MODEL));
        assertEquals(22, full.stateId());
        assertNotEquals(emptyModel, content.items().get(44).get(DataComponents.ITEM_MODEL));
    }
    @Test void secondaryCarrierKeepsEmptyFoodAndGunSourcesPureAndRestoresCurrentGuiSnapshot() {
        var food=new ItemStack(Items.APPLE,3);
        food.set(DataComponents.CONSUMABLE,net.minecraft.world.item.component.Consumable.builder().consumeSeconds(1.6f).build());
        var gun=new ItemStack(Items.PAPER);gun.set(DataComponents.ITEM_MODEL,Identifier.fromNamespaceAndPath("destiny","weapon/ace_of_spades"));
        for(var source:List.of(ItemStack.EMPTY,food,gun)) {
            var original=source.copy();var packet=new ClientboundContainerSetSlotPacket(0,37,38,source);
            UnaryOperator<Packet<?>> bm=p->new ClientboundContainerSetSlotPacket(0,37,38,ItemStack.EMPTY);
            var projected=(ClientboundContainerSetSlotPacket)SwordHandPackets.secondaryTransform(packet,42,2,true,bm);
            var carrier=projected.getItem();assertFalse(carrier.isEmpty());assertTrue(carrier.is(Items.STICK));
            assertEquals(Identifier.fromNamespaceAndPath("destiny","weapon_sword_hand_empty"),carrier.get(DataComponents.ITEM_MODEL));
            assertFalse(carrier.has(DataComponents.FOOD));assertFalse(carrier.has(DataComponents.CUSTOM_DATA));
            assertEquals(3600,carrier.get(DataComponents.CONSUMABLE).consumeSeconds());
            assertEquals(ItemUseAnimation.NONE,carrier.get(DataComponents.CONSUMABLE).animation());
            assertFalse(carrier.get(DataComponents.CONSUMABLE).hasConsumeParticles());
            assertEquals(1f,carrier.get(DataComponents.USE_EFFECTS).speedMultiplier());
            assertTrue(ItemStack.matches(original,source));assertEquals(37,projected.getStateId());
            var gui=(ClientboundContainerSetSlotPacket)SwordHandPackets.secondaryTransform(packet,42,2,false,bm);
            assertTrue(ItemStack.matches(original,gui.getItem()),"GUI gets this packet's current source, never the dummy or a stored gun");
        }
        for(int container:List.of(1,-1))for(int slot:List.of(-1,38,45)) {
            var packet=new ClientboundContainerSetSlotPacket(container,3,slot,food);
            assertSame(packet,SwordHandPackets.secondaryTransform(packet,42,2,true,SAME));
        }
        for(int slot:List.of(-1,5,36,37,39,45)) {
            var packet=new ClientboundContainerSetSlotPacket(0,3,slot,food);
            assertSame(packet,SwordHandPackets.secondaryTransform(packet,42,2,true,SAME));
        }
        var stale=new ClientboundContainerSetSlotPacket(0,38,38,ItemStack.EMPTY);
        assertSame(stale,SwordHandPackets.secondaryTransform(new ClientboundContainerSetSlotPacket(0,37,38,gun),42,2,true,p->stale));
    }
    @Test void secondaryFullContentSelectedBoundaryOffhandCursorAndObserverIsolation() {
        var source=new ArrayList<>(Collections.nCopies(46,ItemStack.EMPTY));
        source.set(36,new ItemStack(Items.PAPER));source.set(37,new ItemStack(Items.APPLE));source.set(45,new ItemStack(Items.DIAMOND));
        var cursor=new ItemStack(Items.DIAMOND);var packet=new ClientboundContainerSetContentPacket(0,15,source,cursor);
        for(int selected:List.of(0,1,2)) {
            var projected=(ClientboundContainerSetContentPacket)SwordHandPackets.secondaryTransform(packet,42,selected,true,p->{
                var copy=(ClientboundContainerSetContentPacket)p;assertNotSame(packet.items(),copy.items());
                copy.items().set(36+selected,ItemStack.EMPTY);return copy;
            });
            assertTrue(projected.items().get(36+selected).is(Items.STICK));assertSame(cursor,projected.carriedItem());
            assertSame(source.get(45),projected.items().get(45));assertEquals(15,projected.stateId());
            for(int slot=0;slot<46;slot++)if(slot!=36+selected)assertSame(source.get(slot),projected.items().get(slot));
            assertTrue(source.get(36).is(Items.PAPER));assertTrue(source.get(37).is(Items.APPLE));assertTrue(source.get(38).isEmpty());
        }
        var observer=new ClientboundSetEquipmentPacket(99,List.of(Pair.of(EquipmentSlot.MAINHAND,ItemStack.EMPTY)));
        assertSame(observer,SwordHandPackets.secondaryTransform(observer,42,0,true,SAME));
        var self=new ClientboundSetEquipmentPacket(42,List.of(Pair.of(EquipmentSlot.MAINHAND,ItemStack.EMPTY),Pair.of(EquipmentSlot.OFFHAND,new ItemStack(Items.DIAMOND))));
        var filtered=(ClientboundSetEquipmentPacket)SwordHandPackets.secondaryTransform(self,42,0,true,SAME);
        assertEquals(List.of(EquipmentSlot.OFFHAND),filtered.getSlots().stream().map(Pair::getFirst).toList());
    }

}
