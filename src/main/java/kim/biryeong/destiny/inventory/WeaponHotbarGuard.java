package kim.biryeong.destiny.inventory;

import com.mojang.serialization.Codec;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import net.fabricmc.fabric.api.attachment.v1.*;
import net.minecraft.network.protocol.game.ClientboundSetHeldSlotPacket;
import net.minecraft.server.level.ServerPlayer;

/** Reject stray combat hotbar choices before any accepted-switch lifecycle callbacks execute. */
public final class WeaponHotbarGuard {
    public static final AttachmentType<Integer> LAST_COMBAT_SLOT = AttachmentRegistry.create(DestinyGuardians.id("last_combat_slot"),
            b -> b.persistent(Codec.intRange(0, 2)).copyOnDeath().initializer(() -> 0));
    private WeaponHotbarGuard() { }
    public static void init() { }
    public static boolean guiOpen(ServerPlayer p) {
        return p.containerMenu != p.inventoryMenu || WeaponScreen.active(p) || InventoryMenuRedirect.nativeOpen(p);
    }
    public static boolean reject(boolean guiOpen, boolean spectator, int requested) {
        return !guiOpen && !spectator && requested >= 3 && requested < 9;
    }
    /** True only when this packet was consumed. Does not cancel reload/use, reset cooldowns or stow perks. */
    public static boolean rejectSlot(ServerPlayer p, int requested) {
        if (!reject(guiOpen(p), p.isSpectator(), requested)) return false;
        int current = p.getInventory().getSelectedSlot();
        if (current >= 0 && current < 3) p.setAttached(LAST_COMBAT_SLOT, current);
        // A preceding GUI close has its own restoration hook; normal invalid input is response-only.
        p.connection.send(new ClientboundSetHeldSlotPacket(current));
        return true;
    }
    public static void observe(ServerPlayer p) {
        int index = p.getInventory().getSelectedSlot();
        if (!guiOpen(p) && index >= 0 && index < 3 && p.getAttachedOrElse(LAST_COMBAT_SLOT, -1) != index)
            p.setAttached(LAST_COMBAT_SLOT, index);
    }
    /** On GUI exit only, restore a valid combat slot; cinematic server-side stows are never policed each tick. */
    public static void restoreCombatSlot(ServerPlayer p) {
        int selected = p.getInventory().getSelectedSlot();
        if (selected >= 0 && selected < 3) { observe(p); return; }
        if (p.hasDisconnected() || p.isRemoved() || p.isSpectator()) return;
        int target = p.getAttachedOrElse(LAST_COMBAT_SLOT, 0);
        if (WeaponItems.entry(p.getInventory().getItem(target)).isEmpty())
            for (int i = 0; i < 3; i++) if (WeaponItems.entry(p.getInventory().getItem(i)).isPresent()) { target = i; break; }
        WeaponRuntime.selectedSlotChanging(p, target);
        p.getInventory().setSelectedSlot(target);
        p.connection.send(new ClientboundSetHeldSlotPacket(target));
        p.containerMenu.broadcastChanges();
    }
}
