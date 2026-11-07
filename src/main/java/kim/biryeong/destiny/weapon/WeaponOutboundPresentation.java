package kim.biryeong.destiny.weapon;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundContainerSetSlotPacket;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import java.util.ArrayList;
import java.util.List;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Freeze a vetted live weapon model into an outbound vanilla carrier BEFORE
 * inventory packet copies lose the original object's binding. Not a gameplay route.
 * Called at the player's native synchronizer construction and recipient-listener send boundaries;
 * never replaces slots, RemoteSlot state, shared suppliers or server listeners.
 */
public final class WeaponOutboundPresentation {
    private record EmptyHand(ServerPlayer owner, Object connection, int slot) {}
    private static final Map<UUID, EmptyHand> EMPTY_HANDS = new HashMap<>();
    private static boolean initialized;
    private WeaponOutboundPresentation() {}

    /** A non-ownable wire-only item prevents vanilla's unarmed first-person arm draw.
     * Source inventory, cursor and observers always retain the actual empty stack. */
    public static void init() {
        if (initialized) return;
        initialized = true;
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            for (var player : server.getPlayerList().getPlayers()) refreshEmptyHand(player);
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            var player = handler.getPlayer();
            var old = EMPTY_HANDS.get(player.getUUID());
            if (old != null && old.owner == player) EMPTY_HANDS.remove(player.getUUID());
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> EMPTY_HANDS.entrySet().removeIf(
                e -> e.getValue().owner.level().getServer() == server));
    }

    /** This is presentation eligibility, never an owned weapon or permission to attack. */
    public static boolean emptyHandCarrier(ServerPlayer player) {
        if (player == null || player.connection == null || player.hasDisconnected()
                || !player.isAlive() || player.isRemoved() || player.isSpectator()
                || kim.biryeong.destiny.inventory.WeaponHotbarGuard.guiOpen(player)) return false;
        int selected = player.getInventory().getSelectedSlot();
        return selected >= 0 && selected < 3 && player.getMainHandItem().isEmpty()
                && player.getInventory().getItem(selected).isEmpty();
    }

    /** Selection and GUI changes need a wire update even if the real inventory stayed empty.
     * Only boundary transitions emit packets; this is not an every-tick inventory broadcast. */
    public static void refreshEmptyHand(ServerPlayer player) {
        if (player == null || !player.level().getServer().isSameThread()) return;
        var old = EMPTY_HANDS.get(player.getUUID());
        if (old != null && (old.owner != player || old.connection != player.connection)) {
            EMPTY_HANDS.remove(player.getUUID()); old = null;
        }
        int next = emptyHandCarrier(player) ? player.getInventory().getSelectedSlot() : -1;
        if ((old == null ? -1 : old.slot) == next) return;
        EMPTY_HANDS.remove(player.getUUID());
        if (old != null) resendInventorySlot(player, old.slot);
        if (next >= 0) {
            EMPTY_HANDS.put(player.getUUID(), new EmptyHand(player, player.connection, next));
            resendInventorySlot(player, next);
        }
    }

    private static void resendInventorySlot(ServerPlayer player, int index) {
        if (player.connection == null || player.hasDisconnected()) return;
        var menu = player.inventoryMenu;
        var slot = menu.findSlot(player.getInventory(), index);
        if (slot.isEmpty()) return;
        player.connection.send(new ClientboundContainerSetSlotPacket(menu.containerId, menu.incrementStateId(),
                slot.getAsInt(), player.getInventory().getItem(index).copy()));
    }

    private static ItemStack invisibleEmptyHand() {
        var carrier = new ItemStack(Items.STICK);
        carrier.set(DataComponents.ITEM_MODEL, kim.biryeong.destiny.DestinyGuardians.id("weapon_sword_hand_empty"));
        carrier.set(DataComponents.ITEM_NAME, Component.empty());
        return carrier;
    }

    /** Recipient-bound listener resends, including Polymer's consumed-use correction.
     * Raw Connection sends/constructors/codecs are NOT intercepted. Preserve original
     * container/state/slot and ordering; offhand, cursor and stale snapshots pass through.
     */
    public static Packet<?> projectPacket(ServerPlayer recipient, Packet<?> packet) {
        kim.biryeong.destiny.fx.SwordHandPackets.refreshSecondary(recipient);
        if (recipient == null || !(packet instanceof ClientboundContainerSetSlotPacket slot)) return packet;
        var menu = slot.getContainerId() == recipient.inventoryMenu.containerId ? recipient.inventoryMenu
                : slot.getContainerId() == recipient.containerMenu.containerId ? recipient.containerMenu : null;
        if (menu == null) return packet;
        var projected = projectSlot(recipient, menu, slot.getSlot(), slot.getItem());
        return projected == slot.getItem() ? packet : new ClientboundContainerSetSlotPacket(
                slot.getContainerId(), slot.getStateId(), slot.getSlot(), projected);
    }

    public static ItemStack projectSlot(ServerPlayer recipient, AbstractContainerMenu menu,
                                        int index, ItemStack snapshot) {
        if (recipient == null || snapshot == null || recipient.connection == null
                || !recipient.level().getServer().isSameThread()
                || recipient.hasDisconnected() || !recipient.isAlive() || recipient.isRemoved()
                || (menu != recipient.inventoryMenu && menu != recipient.containerMenu)
                || index < 0 || index >= menu.slots.size()) return snapshot;
        var slot = menu.slots.get(index);
        // Slot provenance, recipient and exact original binding grant admission.
        // Component equality is only a stale-snapshot REJECTION, never authority.
        if (slot.container != recipient.getInventory()
                || slot.getContainerSlot() != recipient.getInventory().getSelectedSlot()) return snapshot;
        var source = slot.getItem();
        if (source.isEmpty()) {
            return snapshot.isEmpty() && source == recipient.getMainHandItem()
                    && emptyHandCarrier(recipient) && contextFor(recipient) != null
                    ? invisibleEmptyHand() : snapshot;
        }
        boolean swordHand = kim.biryeong.destiny.fx.PlayerAnimations.ownsSwordHand(recipient, source);
        boolean grenadeHand = kim.biryeong.destiny.fx.PlayerAnimations.ownsGrenadeHand(recipient, source);
        if (source != recipient.getMainHandItem() || source.isEmpty()
                || !(swordHand || grenadeHand || ownedBy(recipient, source))
                || !ItemStack.matches(source, snapshot)) return snapshot;
        var context = contextFor(recipient);
        if (context == null) return snapshot;
        // Existing Polymer route precedence, canonical recognition, scope and grip
        // all evaluate against the original. The resulting carrier retains Polymer's
        // real-item roundtrip tag, so later encoding must not convert it a second time.
        var carrier = PolymerItemUtils.getPolymerItemStack(source, context, recipient.level().registryAccess());
        if (swordHand || grenadeHand) {
            // Late, client-only projection AFTER Polymer. Preserve consumable and
            // roundtrip data; don't turn the authoritative item or BM prop invisible.
            carrier = carrier.copy();
            carrier.set(net.minecraft.core.component.DataComponents.ITEM_MODEL,
                    kim.biryeong.destiny.DestinyGuardians.id("weapon_sword_hand_empty"));
        }
        return carrier;
    }

    private static PacketContext contextFor(ServerPlayer recipient) {
        if (!((Object) recipient.connection instanceof PacketContextProvider provider)) return null;
        var context = provider.getPacketContext();
        var profile = context.get(PacketContext.GAME_PROFILE);
        var connection = context.get(PacketContext.CONNECTION);
        if (context.get(PacketContext.SERVER_INSTANCE) != recipient.level().getServer()
                || connection == null || connection.getPacketListener() != recipient.connection || profile == null
                || !profile.id().equals(recipient.getUUID())) return null;
        return context;
    }

    /** Admission only; model construction stays in WeaponCombatItem.
     * W93 covers the older exact-object reload/insert/ADS/bow routes as well as W91.
     * Neither a persisted selector nor a different player's binding grants authority.
     * Check the actual highest-priority route, NOT any owned lower-priority route:
     * an aliased original can still have a donor's earlier binding in another helper.
     */
    private static boolean ownedBy(ServerPlayer recipient, ItemStack source) {
        if (WeaponSwapPresentation.active(source)) return WeaponSwapPresentation.ownedBy(recipient, source);
        if (WeaponInsertPresentation.active(source)) return WeaponInsertPresentation.ownedBy(recipient, source);
        if (WeaponIzanagiPresentation.active(source)) return WeaponIzanagiPresentation.ownedBy(recipient, source);
        if (WeaponReloadPresentation.active(source)) return WeaponReloadPresentation.ownedBy(recipient, source);
        if (WeaponAimPresentation.active(source) && !(WeaponScopes.scoped(source)
                && WeaponItems.entry(source).filter(e -> e.family().equals("sniper_rifle")).isPresent()))
            // The ADS bow model is a composite route and also reads the live bow binding.
            return WeaponAimPresentation.ownedBy(recipient, source)
                    && (!WeaponBowPresentation.active(source) || WeaponBowPresentation.ownedBy(recipient, source));
        if (WeaponBowPresentation.active(source)) return WeaponBowPresentation.ownedBy(recipient, source);
        return false;
    }

    public static List<ItemStack> projectContent(ServerPlayer recipient, AbstractContainerMenu menu,
                                                List<ItemStack> snapshots) {
        List<ItemStack> result = null;
        for (int i = 0; i < snapshots.size(); i++) {
            var original = snapshots.get(i);
            var projected = projectSlot(recipient, menu, i, original);
            if (projected != original) {
                if (result == null) result = new ArrayList<>(snapshots);
                result.set(i, projected);
            }
        }
        // Keep callers' snapshot list byte-pure. No mutation of shared menu data.
        return result == null ? snapshots : result;
    }
}
