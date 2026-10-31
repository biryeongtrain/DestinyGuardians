package kim.biryeong.destiny.tutorial;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.protocol.game.ClientboundSetHeldSlotPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import java.util.ArrayList;
import java.util.List;

/** Persistent escrow for three equipment slots. Never consumes or upgrades the player's own gear. */
public final class TutorialLoan {
    private static final String MARKER = "destiny_tutorial_loan";
    public record Backup(List<ItemStack> equipment, int selected, boolean enabled) {
        static final Codec<Backup> CODEC = RecordCodecBuilder.create(i -> i.group(
            ItemStack.OPTIONAL_CODEC.listOf().fieldOf("equipment").forGetter(Backup::equipment),
            Codec.intRange(0, 8).fieldOf("selected").forGetter(Backup::selected),
            Codec.BOOL.fieldOf("enabled").forGetter(Backup::enabled)
        ).apply(i, Backup::new));
        public Backup { if (equipment.size() != 3) throw new IllegalArgumentException("Three equipment slots required"); equipment = List.copyOf(equipment); }
    }
    public static final AttachmentType<Backup> BACKUP = AttachmentRegistry.create(DestinyGuardians.id("tutorial_loan_backup"),
        b -> b.persistent(Backup.CODEC).copyOnDeath());
    private TutorialLoan() { }
    public static void init() { }
    public static boolean active(ServerPlayer p) { return p.getAttached(BACKUP) != null; }
    public static boolean borrowed(ServerPlayer p, ItemStack stack) {
        var data = stack.get(DataComponents.CUSTOM_DATA);
        return data != null && p.getUUID().toString().equals(data.copyTag().getStringOr(MARKER, ""));
    }
    public static void equip(ServerPlayer p, WeaponCatalog.Entry weapon) {
        if (!active(p)) {
            var gear = new ArrayList<ItemStack>();
            for (int i = 0; i < 3; i++) gear.add(p.getInventory().getItem(i).copy());
            p.setAttached(BACKUP, new Backup(gear, p.getInventory().getSelectedSlot(), WeaponLoadout.enabled(p)));
            for (int i = 0; i < 3; i++) p.getInventory().setItem(i, ItemStack.EMPTY);
        }
        WeaponRuntime.cleanup(p);
        clearBorrowed(p);
        var stack = WeaponItems.create(weapon);
        var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putString(MARKER, p.getUUID().toString());
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        int slot = WeaponCharacteristics.of(weapon).slot().hotbar();
        var displaced = p.getInventory().getItem(slot);
        p.getInventory().setItem(slot, stack);
        if (!displaced.isEmpty()) p.getInventory().placeItemBackInInventory(displaced, net.minecraft.util.Prediction.SERVER_ONLY);
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.getInventory().setSelectedSlot(slot);
        p.connection.send(new ClientboundSetHeldSlotPacket(slot));
        WeaponHandling.update(p);
        sync(p);
    }
    public static void restore(ServerPlayer p) {
        var backup = p.getAttached(BACKUP);
        if (backup == null) return;
        WeaponRuntime.cleanup(p);
        clearBorrowed(p);
        var displaced = new ArrayList<ItemStack>();
        for (int i = 0; i < 3; i++) {
            var stack = p.getInventory().getItem(i);
            if (!stack.isEmpty()) displaced.add(stack);
            p.getInventory().setItem(i, backup.equipment().get(i).copy());
        }
        p.setAttached(WeaponLoadout.ENABLED, backup.enabled());
        p.getInventory().setSelectedSlot(backup.selected());
        p.removeAttached(BACKUP);
        for (var stack : displaced) p.getInventory().placeItemBackInInventory(stack, net.minecraft.util.Prediction.SERVER_ONLY);
        if (!p.hasDisconnected()) p.connection.send(new ClientboundSetHeldSlotPacket(backup.selected()));
        sync(p);
    }
    private static void clearBorrowed(ServerPlayer p) {
        for (int i = 0; i < p.getInventory().getContainerSize(); i++)
            if (borrowed(p, p.getInventory().getItem(i))) p.getInventory().setItem(i, ItemStack.EMPTY);
    }
    private static void sync(ServerPlayer p) {
        p.getInventory().setChanged();
        if (!p.hasDisconnected()) p.containerMenu.broadcastChanges();
    }
}
