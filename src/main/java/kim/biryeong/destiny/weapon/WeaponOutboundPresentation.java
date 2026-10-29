package kim.biryeong.destiny.weapon;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundContainerSetSlotPacket;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;

/** Freeze a vetted live weapon model into an outbound vanilla carrier BEFORE
 * inventory packet copies lose the original object's binding. Not a gameplay route.
 * Called at the player's native synchronizer construction and recipient-listener send boundaries;
 * never replaces slots, RemoteSlot state, shared suppliers or server listeners.
 */
public final class WeaponOutboundPresentation {
    private WeaponOutboundPresentation() {}

    /** Recipient-bound listener resends, including Polymer's consumed-use correction.
     * Raw Connection sends/constructors/codecs are NOT intercepted. Preserve original
     * container/state/slot and ordering; offhand, cursor and stale snapshots pass through.
     */
    public static Packet<?> projectPacket(ServerPlayer recipient, Packet<?> packet) {
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
        boolean swordHand = kim.biryeong.destiny.fx.PlayerAnimations.ownsSwordHand(recipient, source);
        boolean grenadeHand = kim.biryeong.destiny.fx.PlayerAnimations.ownsGrenadeHand(recipient, source);
        if (source != recipient.getMainHandItem() || source.isEmpty()
                || !(swordHand || grenadeHand || ownedBy(recipient, source))
                || !ItemStack.matches(source, snapshot)) return snapshot;
        var context = ((PacketContextProvider) (Object) recipient.connection).getPacketContext();
        var profile = context.get(PacketContext.GAME_PROFILE);
        var connection = context.get(PacketContext.CONNECTION);
        if (context.get(PacketContext.SERVER_INSTANCE) != recipient.level().getServer()
                || connection == null || connection.getPacketListener() != recipient.connection || profile == null
                || !profile.id().equals(recipient.getUUID())) return snapshot;
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
