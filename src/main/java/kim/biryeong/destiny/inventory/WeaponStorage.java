package kim.biryeong.destiny.inventory;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.inventory.gear.GearLayout;
import kim.biryeong.destiny.inventory.gear.GearSlot;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.attachment.v1.*;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Persistent player-owned spare weapons. Only equipped hotbar 0..2 remains vanilla inventory.
 * Tokens are monotonic storage ids, not inventory positions. UI copies never confer ownership.
 * Lists are immutable; canonical stack objects are moved, never cloned during an equip transaction. */
public final class WeaponStorage {
    public static final int FIRST_TOKEN = 1000;
    public record Stored(int token, ItemStack stack) {
        static final Codec<Stored> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.intRange(FIRST_TOKEN, Integer.MAX_VALUE - 1).fieldOf("id").forGetter(Stored::token),
                ItemStack.CODEC.fieldOf("stack").forGetter(Stored::stack)).apply(i, Stored::new));
    }
    public record Data(int nextId, List<Stored> entries) {
        public static final Codec<Data> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.intRange(FIRST_TOKEN, Integer.MAX_VALUE).optionalFieldOf("next_id", FIRST_TOKEN).forGetter(Data::nextId),
                Stored.CODEC.listOf().optionalFieldOf("weapons", List.of()).forGetter(Data::entries)).apply(i, Data::new));
        public Data {
            entries = List.copyOf(entries);
            var ids = new HashSet<Integer>();
            for (var e : entries) {
                if (!ids.add(e.token())) throw new IllegalArgumentException("Duplicate weapon storage id");
                nextId = Math.max(nextId, e.token() + 1);
            }
        }
        Data plus(ItemStack stack) {
            if (nextId == Integer.MAX_VALUE) throw new IllegalStateException("Weapon storage id exhausted");
            var next = new ArrayList<>(entries); next.add(new Stored(nextId, stack));
            return new Data(nextId + 1, next);
        }
        Data minus(int token) { return new Data(nextId, entries.stream().filter(e -> e.token() != token).toList()); }
        Data copy() { return new Data(nextId, entries.stream().map(e -> new Stored(e.token(), e.stack().copy())).toList()); }
    }
    public static final Data EMPTY = new Data(FIRST_TOKEN, List.of());
    public static final AttachmentType<Data> DATA = AttachmentRegistry.create(DestinyGuardians.id("weapon_storage"),
            b -> b.persistent(Data.CODEC).copyOnDeath().initializer(() -> EMPTY));
    private WeaponStorage() { }
    public static void init() {
        ServerPlayConnectionEvents.JOIN.register((h, sender, server) -> server.execute(() -> { migrate(h.getPlayer()); WeaponHotbarGuard.restoreCombatSlot(h.getPlayer()); }));
        net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents.AFTER_RESPAWN.register((old, fresh, alive) -> {
            var data = fresh.getAttached(DATA);
            if (data != null) fresh.setAttached(DATA, data.copy());
            migrate(fresh); WeaponHotbarGuard.restoreCombatSlot(fresh);
        });
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            for (var p : server.getPlayerList().getPlayers()) migrate(p);
        });
        WeaponHotbarGuard.init(); WeaponStorageQa.init();
    }
    public static Data data(ServerPlayer p) { return p.getAttachedOrElse(DATA, EMPTY); }
    public static List<Stored> entries(ServerPlayer p) { return data(p).entries(); }
    public static boolean token(int index) { return index >= FIRST_TOKEN && index < Integer.MAX_VALUE; }
    public static ItemStack get(ServerPlayer p, int token) {
        return entries(p).stream().filter(e -> e.token() == token).map(Stored::stack).findFirst().orElse(ItemStack.EMPTY);
    }
    /** One ownership resolver for E, lock/dismantle and economy click tokens. */
    public static ItemStack resolve(ServerPlayer p, int index) {
        return token(index) ? get(p, index) : index >= 0 && index < p.getInventory().getContainerSize()
                ? p.getInventory().getItem(index) : ItemStack.EMPTY;
    }
    public static String room(ServerPlayer p, ItemStack stack) {
        var entry = WeaponItems.entry(stack);
        if (entry.isEmpty() || stack.getCount() != 1) return "소유 가능한 전투 무기 한 개를 선택해 주세요.";
        var slot = WeaponLoadout.slot(p, stack, entry.get());
        long count = entries(p).stream().filter(e -> WeaponItems.entry(e.stack())
                .filter(w -> WeaponLoadout.slot(p, e.stack(), w) == slot).isPresent()).count();
        if (count >= GearLayout.STORAGE_COUNT) return GearSlot.of(slot).label() + " 보관 칸이 가득 찼습니다.";
        return data(p).nextId() == Integer.MAX_VALUE ? "무기 보관함에 더 저장할 수 없습니다." : null;
    }
    /** New rewards enter the attachment directly. Caller transfers ownership only on success. */
    public static String store(ServerPlayer p, ItemStack stack) {
        String why = room(p, stack); if (why != null) return why;
        if (entries(p).stream().anyMatch(e -> e.stack() == stack)) return "이미 보유한 무기입니다.";
        for (int i = 0; i < p.getInventory().getContainerSize(); i++)
            if (p.getInventory().getItem(i) == stack) return "이미 인벤토리에 있는 무기입니다.";
        p.setAttached(DATA, data(p).plus(stack)); return null;
    }
    /** Remove only the exact still-owned object. Stale UI callbacks cannot consume a replacement. */
    public static boolean remove(ServerPlayer p, int token, ItemStack expected) {
        if (!token(token) || expected == null || expected.isEmpty() || get(p, token) != expected) return false;
        p.setAttached(DATA, data(p).minus(token)); return true;
    }
    /** Transactional rollback for a removed economy item; never overwrites a newer owner. */
    public static boolean restore(ServerPlayer p, int token, ItemStack stack) {
        if (!token(token) || !get(p, token).isEmpty() || stack.isEmpty()) return false;
        var list = new ArrayList<>(entries(p)); list.add(new Stored(token, stack));
        p.setAttached(DATA, new Data(data(p).nextId(), list)); return true;
    }
    /** Migration/equip only: existing ownership is retained even when an old bucket exceeds today's cap. */
    public static void retain(ServerPlayer p, ItemStack stack) {
        if (!stack.isEmpty()) p.setAttached(DATA, data(p).plus(stack));
    }
    /** Validated equip transaction: incoming leaves storage and the previous equipped object enters it.
     * An existing over-cap legacy bucket can still exchange gear without losing either object. */
    public static boolean exchange(ServerPlayer p, int token, ItemStack expected, ItemStack displaced) {
        if (get(p, token) != expected || expected.isEmpty()) return false;
        Data next = data(p).minus(token);
        if (!displaced.isEmpty()) {
            if (next.nextId() == Integer.MAX_VALUE) return false;
            next = next.plus(displaced);
        }
        p.setAttached(DATA, next); return true;
    }
    /** Lossless one-way migration, also catches vanilla/admin ingress. Legacy over-cap rows are retained.
     * The active three slots and unrelated items are untouched; temporary tutorial loans stay in escrow. */
    public static void migrate(ServerPlayer p) {
        if (p.hasDisconnected() || p.isRemoved() || !p.level().getServer().isSameThread()) return;
        boolean changed = false;
        for (int i = 3; i < p.getInventory().getContainerSize(); i++) {
            ItemStack stack = p.getInventory().getItem(i);
            if (WeaponItems.entry(stack).isEmpty() || kim.biryeong.destiny.tutorial.TutorialLoan.borrowed(p, stack)) continue;
            boolean duplicate = entries(p).stream().anyMatch(e -> e.stack() == stack);
            for (int equipped = 0; equipped < 3; equipped++) duplicate |= p.getInventory().getItem(equipped) == stack;
            if (!duplicate && data(p).nextId() == Integer.MAX_VALUE) continue;
            if (!duplicate) p.setAttached(DATA, data(p).plus(stack));
            p.getInventory().setItem(i, ItemStack.EMPTY); changed = true;
        }
        if (changed) {
            p.getInventory().setChanged();
            if (!WeaponHotbarGuard.guiOpen(p)) WeaponHotbarGuard.restoreCombatSlot(p);
            p.containerMenu.broadcastChanges();
        }
        WeaponHotbarGuard.observe(p);
    }
}
