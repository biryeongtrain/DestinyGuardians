package kim.biryeong.destiny.campaign;

import kim.biryeong.destiny.tutorial.TutorialLoan;
import kim.biryeong.destiny.weapon.*;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.protocol.game.ClientboundSetHeldSlotPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;

import java.util.ArrayList;
import java.util.Optional;

/**
 * Mission weapons on top of the persistent {@link TutorialLoan} escrow. The Guardian wakes unarmed: the three
 * equipment slots go into the same escrow the tutorial uses (persistent, restored on join if a run was
 * interrupted), then the mission hands out a rifle and later a shotgun. Both are marked with the escrow's
 * borrow tag so {@link TutorialLoan#restore} removes them and returns the player's own gear exactly once.
 *
 * <p>Unlike {@link TutorialLoan#equip}, granting the shotgun keeps the rifle (two borrowed weapons at once).
 */
public final class RisingLoadout {
    /** Same marker key as TutorialLoan's private constant; TutorialLoan.borrowed/restore recognise it. */
    private static final String LOAN_MARKER = "destiny_tutorial_loan";
    public static final String RIFLE = "gnawing_hunger";
    public static final String SHOTGUN = "mindbender_s_ambition_adept";
    /** W302: the mission hands out the real launch-mission guns (user-ripped models). Gameplay rows are the catalog
     * weapons with the same D2 frame (Khvostov 7G-02: Adaptive 600 RPM auto rifle; Stubborn Oak: Aggressive 55 RPM shotgun). */
    public static final String RIFLE_SKIN = "khvostov_7g_02";
    public static final String SHOTGUN_SKIN = "stubborn_oak";

    private RisingLoadout() { }

    /** Put the player's own equipment into escrow and leave the weapon slots empty. Idempotent. */
    public static void stow(ServerPlayer p) {
        if (TutorialLoan.active(p)) return;
        var gear = new ArrayList<ItemStack>();
        for (int i = 0; i < 3; i++) gear.add(p.getInventory().getItem(i).copy());
        p.setAttached(TutorialLoan.BACKUP, new TutorialLoan.Backup(gear, p.getInventory().getSelectedSlot(), WeaponLoadout.enabled(p)));
        WeaponRuntime.cleanup(p);
        for (int i = 0; i < 3; i++) p.getInventory().setItem(i, ItemStack.EMPTY);
        p.setAttached(WeaponLoadout.ENABLED, true);
        WeaponHandling.update(p);
        sync(p);
    }

    public static void grantRifle(ServerPlayer p) { grant(p, RIFLE, RIFLE_SKIN, true); }
    public static void grantShotgun(ServerPlayer p) { grant(p, SHOTGUN, SHOTGUN_SKIN, true); }

    public static boolean ownsRifle(ServerPlayer p) { return find(p, RIFLE) >= 0; }
    public static boolean holdingRifle(ServerPlayer p) { return holding(p, RIFLE); }
    public static boolean holding(ServerPlayer p, String weapon) {
        var stack = p.getMainHandItem();
        return TutorialLoan.borrowed(p, stack) && WeaponItems.entry(stack).filter(e -> e.id().equals(weapon)).isPresent();
    }

    /** Return the escrow (removes every borrowed weapon). Safe to call repeatedly. */
    public static void restore(ServerPlayer p) { TutorialLoan.restore(p); }

    private static void grant(ServerPlayer p, String id, String skin, boolean select) {
        Optional<WeaponCatalog.Entry> weapon = WeaponCatalog.find(id);
        if (weapon.isEmpty()) throw new IllegalStateException("Missing mission weapon " + id);
        stow(p);
        int existing = find(p, id);
        var inv = p.getInventory();
        var stack = existing >= 0 ? inv.getItem(existing) : WeaponItems.create(weapon.get());
        if (existing < 0) {
            var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
            tag.putString(LOAN_MARKER, p.getUUID().toString());
            stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        }
        WeaponSkins.apply(stack, skin);
        int slot = WeaponLoadout.slot(p, stack, weapon.get()).hotbar();
        if (existing != slot) {
            var displaced = inv.getItem(slot);
            // A saved pre-fix loan can occupy the wrong slot. Swap references, never copy/mint it.
            if (existing >= 0) inv.setItem(existing, displaced);
            inv.setItem(slot, stack);
            if (existing < 0 && !displaced.isEmpty())
                inv.placeItemBackInInventory(displaced, net.minecraft.util.Prediction.SERVER_ONLY);
        }
        if (select) select(p, slot);
        WeaponHandling.update(p);
        sync(p);
    }

    private static int find(ServerPlayer p, String id) {
        var inv = p.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            var stack = inv.getItem(i);
            if (TutorialLoan.borrowed(p, stack) && WeaponItems.entry(stack).filter(e -> e.id().equals(id)).isPresent()) return i;
        }
        return -1;
    }

    private static void select(ServerPlayer p, int slot) {
        if (slot < 0 || slot > 8) return;
        WeaponRuntime.cleanup(p);
        p.getInventory().setSelectedSlot(slot);
        if (!p.hasDisconnected()) p.connection.send(new ClientboundSetHeldSlotPacket(slot));
    }

    private static void sync(ServerPlayer p) {
        p.getInventory().setChanged();
        if (!p.hasDisconnected()) p.containerMenu.broadcastChanges();
    }
}
