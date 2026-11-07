package kim.biryeong.destiny.fx;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kr.toxicity.model.impl.fabric.network.BetterModelBundlePacket;
import kr.toxicity.model.impl.fabric.network.PacketsKt;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.ServerPlayerConnection;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Predicate;
import java.util.function.UnaryOperator;

/** Keep the owner's logical use item while BM hides the physical equipment.
 * No world/inventory/presentation reads on Netty. Publication and retirement are
 * ordered with packet writes on that connection's event loop, including teardown.
 */
public final class SwordHandPackets {
    private static final Identifier COMBAT = Identifier.fromNamespaceAndPath("destiny", "weapon_combat");
    private static final Identifier EMPTY_MODEL = Identifier.fromNamespaceAndPath("destiny", "weapon_sword_hand_empty");
    private static final Map<ServerPlayerConnection, Protection> PROTECTED = new ConcurrentHashMap<>();
    // Identity, not entity id/UUID alone: reconnects and an old close cannot retire a new pose.
    public static final class Protection {
        final ServerPlayerConnection connection;
        final int entityId;
        final boolean secondaryInput;
        // Main-thread admission is captured before writes; Netty consumes only this immutable snapshot.
        private record Secondary(int slot, boolean carrier) { }
        private Secondary admitted;
        private Secondary wire;
        private Protection(ServerPlayer player) { this(player,false); }
        private Protection(ServerPlayer player,boolean secondaryInput) {
            connection=player.connection;entityId=player.getId();this.secondaryInput=secondaryInput;
            admitted=wire=new Secondary(player.getInventory().getSelectedSlot(),false);
        }
    }
    private SwordHandPackets() {}

    public static Protection begin(ServerPlayer player) {
        var protection = new Protection(player);
        ordered(protection, () -> PROTECTED.put(protection.connection, protection));
        return protection;
    }

    /** Wire-only non-usable carrier lets an unmodified client emit use-in-air while BM hides its hand. */
    public static Protection beginSecondary(ServerPlayer player) {
        var protection=new Protection(player,true);
        ordered(protection,()->PROTECTED.put(protection.connection,protection));return protection;
    }

    public static void refreshSecondary(ServerPlayer player) {
        if(player!=null&&player.connection!=null)refreshSecondary(PROTECTED.get(player.connection),player);
    }
    static void refreshSecondary(Protection protection,ServerPlayer player) {
        if(protection==null||!protection.secondaryInput||player.connection!=protection.connection
                ||!player.level().getServer().isSameThread())return;
        int selected=player.getInventory().getSelectedSlot();
        boolean carrier=PlayerAnimations.ownsSecondaryHand(player)
                &&player.containerMenu==player.inventoryMenu
                &&!kim.biryeong.destiny.inventory.WeaponHotbarGuard.guiOpen(player);
        var next=new Protection.Secondary(selected,carrier);var old=protection.admitted;
        if(next.equals(old))return;
        protection.admitted=next;
        ordered(protection,()->protection.wire=next);
        // Restore the CURRENT logical source at each old/new boundary, never a stored weapon snapshot.
        if(old.slot()!=selected)syncSlot(player,old.slot());
        syncSlot(player,selected);
    }

    public static void end(Protection protection) {
        if (protection != null)
            ordered(protection, () -> PROTECTED.remove(protection.connection, protection));
    }

    private static void ordered(Protection protection, Runnable action) {
        var listener = (net.minecraft.server.network.ServerGamePacketListenerImpl) protection.connection;
        var loop = PacketsKt.getChannel(PacketsKt.getConnection(listener)).eventLoop();
        if (loop.inEventLoop()) action.run(); else loop.execute(action);
    }

    /** Main-thread one-shot repair after show/close; never restore a captured sword. */
    public static void syncCurrent(ServerPlayer player) {
        if (player.connection != null && !player.hasDisconnected() && !player.isRemoved()
                && player.level().getServer().isSameThread()) {
            syncSlot(player,player.getInventory().getSelectedSlot());
        }
    }

    private static void syncSlot(ServerPlayer player,int slot) {
        if(slot>=0&&slot<9&&player.connection!=null&&!player.hasDisconnected())
            player.connection.send(new ClientboundContainerSetSlotPacket(0,player.inventoryMenu.incrementStateId(),
                    36+slot,player.getInventory().getItem(slot).copy()));
    }

    public static Packet<?> around(ServerPlayerConnection connection, Packet<?> incoming,
                                   UnaryOperator<Packet<?>> betterModel) {
        var protection = PROTECTED.get(connection);
        if (protection == null) return betterModel.apply(incoming);
        if(protection.secondaryInput) {
            var state=protection.wire;
            return secondaryTransform(incoming,protection.entityId,state.slot(),state.carrier(),betterModel);
        }
        return transform(incoming, protection.entityId, betterModel, SwordHandPackets::combat,
                stack -> concealProjected(stack, PolymerItemUtils.getPolymerIdentifier(stack)));
    }

    static Packet<?> secondaryTransform(Packet<?> incoming,int ownerId,int selected,boolean carrier,
                                         UnaryOperator<Packet<?>> betterModel) {
        Packet<?> isolated=incoming;
        if(incoming instanceof ClientboundContainerSetContentPacket content)
            isolated=new ClientboundContainerSetContentPacket(content.containerId(),content.stateId(),
                    new ArrayList<>(content.items()),content.carriedItem());
        Packet<?> outgoing=betterModel.apply(isolated);
        int slot=36+selected;
        if(selected>=0&&selected<9&&incoming instanceof ClientboundContainerSetSlotPacket before
                &&outgoing instanceof ClientboundContainerSetSlotPacket after
                &&before.getContainerId()==0&&after.getContainerId()==0&&before.getSlot()==slot
                &&after.getSlot()==slot&&before.getStateId()==after.getStateId()) {
            outgoing=new ClientboundContainerSetSlotPacket(0,after.getStateId(),slot,
                    carrier?secondaryCarrier():before.getItem());
        } else if(selected>=0&&selected<9&&incoming instanceof ClientboundContainerSetContentPacket before
                &&outgoing instanceof ClientboundContainerSetContentPacket after
                &&before.containerId()==0&&after.containerId()==0&&before.stateId()==after.stateId()
                &&before.items().size()==after.items().size()&&slot<before.items().size()) {
            var items=new ArrayList<>(after.items());items.set(slot,carrier?secondaryCarrier():before.items().get(slot));
            outgoing=new ClientboundContainerSetContentPacket(0,after.stateId(),items,after.carriedItem());
        }
        return withoutSelfMainHand(outgoing,ownerId);
    }
    private static ItemStack secondaryCarrier() {
        var carrier=new ItemStack(net.minecraft.world.item.Items.STICK);
        carrier.set(net.minecraft.core.component.DataComponents.ITEM_MODEL,EMPTY_MODEL);
        carrier.set(net.minecraft.core.component.DataComponents.ITEM_NAME,net.minecraft.network.chat.Component.empty());
        // Consume the client's main-hand input, avoiding offhand fallthrough. This is the same silent
        // long-use contract as weapon carriers; no food, ammo or Polymer ownership is copied.
        carrier.set(net.minecraft.core.component.DataComponents.USE_EFFECTS,new net.minecraft.world.item.component.UseEffects(true,false,1f));
        carrier.set(net.minecraft.core.component.DataComponents.CONSUMABLE,net.minecraft.world.item.component.Consumable.builder()
                .consumeSeconds(3600).animation(net.minecraft.world.item.ItemUseAnimation.NONE).hasConsumeParticles(false)
                .sound(net.minecraft.core.Holder.direct(net.minecraft.sounds.SoundEvent.createVariableRangeEvent(
                        Identifier.withDefaultNamespace("intentionally_empty")))).build());
        return carrier;
    }

    static boolean combat(ItemStack stack) {
        return !stack.isEmpty() && combatIdentity(BuiltInRegistries.ITEM.getKey(stack.getItem()),
                PolymerItemUtils.getPolymerIdentifier(stack));
    }

    static boolean combatIdentity(Identifier actualItem, Identifier polymerItem) {
        return COMBAT.equals(actualItem) || COMBAT.equals(polymerItem);
    }

    /** Polymer's use correction may already contain a vanilla carrier copied
     * before current ammo changed. Never re-project live state on Netty. Hide
     * only that captured carrier's model; retain every use/roundtrip component.
     * Native mod items must still be converted on the normal Polymer path.
     */
    static ItemStack concealProjected(ItemStack stack, Identifier polymerItem) {
        if (!COMBAT.equals(polymerItem)) return stack;
        var copy = stack.copy();
        copy.set(net.minecraft.core.component.DataComponents.ITEM_MODEL, EMPTY_MODEL);
        return copy;
    }

    /** Capture before BM: 3.5.1 mutates content lists in place. */
    static Packet<?> transform(Packet<?> incoming, int ownerId, UnaryOperator<Packet<?>> betterModel,
                               Predicate<ItemStack> combat) {
        return transform(incoming, ownerId, betterModel, combat, UnaryOperator.identity());
    }

    static Packet<?> transform(Packet<?> incoming, int ownerId, UnaryOperator<Packet<?>> betterModel,
                               Predicate<ItemStack> combat, UnaryOperator<ItemStack> presentation) {
        Packet<?> isolated = incoming;
        if (incoming instanceof ClientboundContainerSetContentPacket content)
            isolated = new ClientboundContainerSetContentPacket(content.containerId(), content.stateId(),
                    new ArrayList<>(content.items()), content.carriedItem());
        Packet<?> outgoing = betterModel.apply(isolated);
        if (incoming instanceof ClientboundContainerSetSlotPacket before
                && outgoing instanceof ClientboundContainerSetSlotPacket after
                && before.getContainerId() == 0 && after.getContainerId() == 0
                && before.getSlot() == after.getSlot() && before.getStateId() == after.getStateId()
                && hotbar(before.getSlot()) && after.getItem().isEmpty() && combat.test(before.getItem())) {
            outgoing = new ClientboundContainerSetSlotPacket(after.getContainerId(), after.getStateId(),
                    after.getSlot(), presentation.apply(before.getItem()));
        } else if (incoming instanceof ClientboundContainerSetContentPacket before
                && outgoing instanceof ClientboundContainerSetContentPacket after
                && before.containerId() == 0 && after.containerId() == 0
                && before.stateId() == after.stateId() && before.items().size() == after.items().size()) {
            var items = new ArrayList<>(after.items());
            boolean changed = false;
            for (int i = 36; i < Math.min(45, items.size()); i++) {
                if (items.get(i).isEmpty() && combat.test(before.items().get(i))) {
                    items.set(i, presentation.apply(before.items().get(i))); changed = true;
                }
            }
            if (changed) outgoing = new ClientboundContainerSetContentPacket(after.containerId(), after.stateId(),
                    items, after.carriedItem());
        }
        return withoutSelfMainHand(outgoing, ownerId);
    }

    private static boolean hotbar(int slot) { return slot >= 36 && slot < 45; }

    /** Marked BM bundles skip its normal recursion. Inspect, never re-handle them.
     * Removing self MAINHAND avoids writing stale cached equipment into a new slot.
     * Other players still receive BM's original hidden equipment.
     */
    static Packet<?> withoutSelfMainHand(Packet<?> packet, int ownerId) {
        if (packet instanceof ClientboundSetEquipmentPacket equipment && equipment.getEntity() == ownerId) {
            var slots = equipment.getSlots().stream().filter(e -> e.getFirst() != EquipmentSlot.MAINHAND).toList();
            if (slots.size() == equipment.getSlots().size()) return packet;
            return slots.isEmpty() ? null : new ClientboundSetEquipmentPacket(ownerId, slots);
        }
        if (packet instanceof ClientboundBundlePacket bundle) {
            var items = new ArrayList<Packet<? super ClientGamePacketListener>>();
            boolean changed = false;
            for (var item : bundle.subPackets()) {
                var filtered = withoutSelfMainHand(item, ownerId);
                changed |= filtered != item;
                if (filtered != null) {
                    @SuppressWarnings("unchecked") var cast = (Packet<? super ClientGamePacketListener>) filtered;
                    items.add(cast);
                }
            }
            if (changed) {
                var copy = new ClientboundBundlePacket(items);
                if ((Object) bundle instanceof BetterModelBundlePacket original
                        && (Object) copy instanceof BetterModelBundlePacket marked)
                    marked.bettermodel$setBetterModelPacket(original.bettermodel$isBetterModelPacket());
                return copy;
            }
        }
        return packet;
    }
}
