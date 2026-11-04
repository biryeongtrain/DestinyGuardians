package kim.biryeong.destiny.activity.presentation;

import kim.biryeong.destiny.weapon.WeaponRuntime;
import net.minecraft.network.protocol.game.ClientboundContainerSetSlotPacket;
import net.minecraft.network.protocol.game.ClientboundSetHeldSlotPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Shared cinematic weapon stow: the selected hotbar slot moves to an empty slot for the scene, so neither the
 * first-person weapon nor the staged body's held item is drawn. Inventory contents are never changed; when no
 * hotbar slot is empty only the viewer's own copy of the held slot is blanked client-side. Restore is exact.
 */
public final class CinematicHands {
    /** Saved with the player at stow time so a disconnect (whose save precedes the event) still restores. */
    public static final net.fabricmc.fabric.api.attachment.v1.AttachmentType<Integer> STOWED_SLOT =
            net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry.create(kim.biryeong.destiny.DestinyGuardians.id("cinematic_stowed_slot"),
                    b -> b.persistent(com.mojang.serialization.Codec.intRange(0, 8)));
    public static void init() {
        net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            var p = handler.getPlayer(); Integer slot = p.getAttached(STOWED_SLOT);
            if (slot == null || stowed(p)) return;
            p.removeAttached(STOWED_SLOT); STOWED.remove(p.getUUID());
            p.getInventory().setSelectedSlot(slot);
            p.connection.send(new ClientboundSetHeldSlotPacket(slot));
        });
    }
    private record Stowed(ServerPlayer player, int slot, boolean clientOnly) { }
    private static final Map<UUID, Stowed> STOWED = new HashMap<>();
    private CinematicHands() { }

    public static void stow(ServerPlayer p) {
        if (STOWED.containsKey(p.getUUID()) || p.hasDisconnected()) return;
        kim.biryeong.destiny.weapon.ProfileWeaponView.hideForCinematic(p);
        var inventory = p.getInventory(); int selected = inventory.getSelectedSlot();
        if (p.getMainHandItem().isEmpty()) return;
        WeaponRuntime.cancelUseForSkill(p);
        int empty = -1;
        for (int i = 8; i >= 0; i--) if (inventory.getItem(i).isEmpty()) { empty = i; break; }
        if (empty >= 0) {
            WeaponRuntime.selectedSlotChanging(p, empty);
            inventory.setSelectedSlot(empty);
            kim.biryeong.minigamelib.cinematic.CameraViews.send(p, new ClientboundSetHeldSlotPacket(empty));
            STOWED.put(p.getUUID(), new Stowed(p, selected, false)); p.setAttached(STOWED_SLOT, selected);
        } else {
            kim.biryeong.minigamelib.cinematic.CameraViews.send(p, new ClientboundContainerSetSlotPacket(p.inventoryMenu.containerId, p.inventoryMenu.incrementStateId(),
                    36 + selected, ItemStack.EMPTY));
            STOWED.put(p.getUUID(), new Stowed(p, selected, true));
        }
    }
    public static void restore(ServerPlayer p) {
        var stowed = STOWED.get(p.getUUID());
        if (stowed == null || stowed.player != p) return;
        STOWED.remove(p.getUUID()); p.removeAttached(STOWED_SLOT);
        // The selection is saved with the player: restore it even for a disconnect, before the data is written.
        if (!stowed.clientOnly) p.getInventory().setSelectedSlot(stowed.slot);
        if (p.hasDisconnected()) return;
        if (!stowed.clientOnly) {
            WeaponRuntime.selectedSlotChanging(p, stowed.slot);
            kim.biryeong.minigamelib.cinematic.CameraViews.send(p, new ClientboundSetHeldSlotPacket(stowed.slot));
        }
        kim.biryeong.minigamelib.cinematic.CameraViews.sending(p.inventoryMenu::sendAllDataToRemote);
    }
    /** The weapon the player held before the scene (copy), for showing on a staged body's hand; EMPTY if none. */
    public static ItemStack heldBeforeStow(ServerPlayer p) {
        var s = STOWED.get(p.getUUID());
        if (s == null || s.player != p || s.clientOnly) return p.getMainHandItem().copy();
        return p.getInventory().getItem(s.slot).copy();
    }
    public static boolean stowed(ServerPlayer p) { var s = STOWED.get(p.getUUID()); return s != null && s.player == p; }
}
