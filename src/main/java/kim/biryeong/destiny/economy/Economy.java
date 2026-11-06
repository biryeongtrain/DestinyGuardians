package kim.biryeong.destiny.economy;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.inventory.WeaponEquipmentService;
import kim.biryeong.destiny.inventory.WeaponStorage;
import kim.biryeong.destiny.inventory.WeaponScreenText;
import kim.biryeong.destiny.inventory.gear.GearAcquisition;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtAccounter;
import net.minecraft.nbt.NbtIo;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.storage.LevelResource;

import java.io.IOException;
import java.nio.file.*;
import java.util.*;

/**
 * Server glue for the {@link EconomyLedger}: loads/saves it under {@code <world>/destiny_economy/}, moves real item
 * stacks into and out of it, pays Glimmer income and expires auction listings. Server thread only.
 *
 * <p>Duplication safety: every operation that moves an item between a player's inventory and the ledger writes the
 * touched account files and that player's data file before returning ({@link #commit}), so a crash cannot leave the
 * item in both places. Account files are written atomically (temp file + move) with the previous copy kept as
 * {@code .bak}, which is read when the main file is damaged.
 */
public final class Economy {
    public static final String GLIMMER_ACCOUNT = "glimmer";
    /** Storage slots of the player inventory the economy may take from or put into (hotbar 0..2 is the loadout). */
    public static final int FIRST_SLOT = 3, LAST_SLOT = 35;
    private static EconomyLedger LEDGER;
    private static MinecraftServer SERVER;
    private static Path DIR;

    private Economy() { }

    public static void init() {
        GlimmerEconomyProvider.register();
        EconomyCommands.init();
        EconomyMenus.init();
        ServerLifecycleEvents.SERVER_STARTED.register(Economy::load);
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> { if (server == SERVER) { EconomyMenus.closeAll(server); save(true); } });
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> { if (server == SERVER) { LEDGER = null; SERVER = null; DIR = null; } });
        ServerTickEvents.END_SERVER_TICK.register(Economy::tick);
        ServerPlayConnectionEvents.JOIN.register((h, s, server) -> server.execute(() -> joined(h.getPlayer())));
    }

    public static EconomyLedger ledger() { return LEDGER; }
    public static EconomyLedger ledger(MinecraftServer server) { return server == SERVER ? LEDGER : null; }
    public static long now() { return System.currentTimeMillis(); }

    /** Balance changed from outside a commit (Common Economy API, rewards): refresh open menus. */
    static void changed(UUID id) { EconomyMenus.refresh(id); }

    // ------------------------------------------------------------------ lifecycle / persistence

    private static void load(MinecraftServer server) {
        SERVER = server;
        DIR = server.getWorldPath(LevelResource.ROOT).resolve("destiny_economy");
        LEDGER = new EconomyLedger();
        int accounts = 0;
        try {
            Files.createDirectories(DIR.resolve("accounts"));
            try (var files = Files.list(DIR.resolve("accounts"))) {
                for (var f : files.filter(f -> f.toString().endsWith(".dat")).sorted().toList()) {
                    var tag = read(f);
                    if (tag == null) continue;
                    try { LEDGER.readAccount(tag); accounts++; }
                    catch (RuntimeException e) { DestinyGuardians.LOGGER.error("Economy: unreadable account {}", f, e); }
                }
            }
            var listings = read(DIR.resolve("listings.dat"));
            if (listings != null) LEDGER.readListings(listings);
        } catch (IOException e) {
            DestinyGuardians.LOGGER.error("Economy: cannot open {}", DIR, e);
        }
        DestinyGuardians.LOGGER.info("Economy loaded: {} accounts, {} listings", accounts, LEDGER.listings().size());
        for (var p : server.getPlayerList().getPlayers()) joined(p);
    }

    /** Read a file, falling back to its .bak copy; a damaged main file is set aside, never deleted. */
    private static CompoundTag read(Path file) {
        for (var f : List.of(file, Path.of(file + ".bak"))) {
            if (!Files.exists(f)) continue;
            try { return NbtIo.readCompressed(f, NbtAccounter.unlimitedHeap()); }
            catch (IOException | RuntimeException e) {
                DestinyGuardians.LOGGER.error("Economy: damaged {}; trying backup", f, e);
                try { Files.copy(f, Path.of(f + ".corrupt-" + now()), StandardCopyOption.REPLACE_EXISTING); } catch (IOException ignored) { }
            }
        }
        return null;
    }

    private static void write(Path file, CompoundTag tag) throws IOException {
        var tmp = Path.of(file + ".tmp");
        NbtIo.writeCompressed(tag, tmp);
        if (Files.exists(file)) Files.copy(file, Path.of(file + ".bak"), StandardCopyOption.REPLACE_EXISTING);
        Files.move(tmp, file, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
    }

    /** Flush dirty accounts/listings. {@code all} rewrites everything (shutdown). */
    public static void save(boolean all) {
        if (LEDGER == null || DIR == null) return;
        if (all) LEDGER.markAllDirty();
        var dirty = LEDGER.drainDirty();
        boolean failed = false;
        for (var id : dirty.accounts()) {
            try { write(DIR.resolve("accounts").resolve(id + ".dat"), LEDGER.writeAccount(id)); }
            catch (IOException e) { failed = true; DestinyGuardians.LOGGER.error("Economy: cannot save account {}", id, e); }
        }
        if (dirty.listings()) {
            try { write(DIR.resolve("listings.dat"), LEDGER.writeListings()); }
            catch (IOException e) { failed = true; DestinyGuardians.LOGGER.error("Economy: cannot save listings", e); }
        }
        if (failed) LEDGER.markAllDirty();   // retry next flush
    }

    /** Persist the ledger and the given online players now (after any inventory/ledger item move). */
    static void commit(ServerPlayer... players) {
        save(false);
        if (SERVER == null) return;
        for (var p : players) if (p != null && !p.hasDisconnected())
            ((kim.biryeong.destiny.mixin.PlayerListSaveInvoker) SERVER.getPlayerList()).destiny$save(p);
    }

    private static void tick(MinecraftServer server) {
        if (server != SERVER || LEDGER == null) return;
        int t = server.getTickCount();
        if (t % 200 == 0) {
            var expired = LEDGER.expire(now());
            for (var l : expired) notify(l.seller(), "경매 판매 기간이 끝나 " + l.item().name() + "이(가) 우편함으로 돌아왔습니다.");
            if (!expired.isEmpty()) EconomyMenus.refreshAll();
        }
        if (t % 100 == 0) save(false);
        if (t % 10 == 0) EconomyMenus.tick(server);
    }

    private static void joined(ServerPlayer p) {
        if (LEDGER == null) return;
        LEDGER.touch(p.getUUID(), p.getGameProfile().name());
        int mail = LEDGER.mail(p.getUUID()).size();
        if (mail > 0) p.sendSystemMessage(Component.literal("우편함에 받을 물품이 " + mail + "개 있습니다. /우편").withStyle(ChatFormatting.AQUA));
    }

    static void notify(UUID id, String text) {
        if (SERVER == null) return;
        var p = SERVER.getPlayerList().getPlayer(id);
        if (p != null) p.sendSystemMessage(Component.literal(text).withStyle(ChatFormatting.AQUA));
    }

    // ------------------------------------------------------------------ glimmer income

    /** Give a Glimmer reward. Returns what was credited. */
    public static long reward(ServerPlayer p, long amount, String reason) {
        if (LEDGER == null || amount <= 0) return 0;
        LEDGER.touch(p.getUUID(), p.getGameProfile().name());
        long lost = LEDGER.creditCapped(p.getUUID(), amount);
        long got = amount - lost;
        if (got > 0) p.sendOverlayMessage(Component.literal("+" + String.format("%,d", got) + " 미광체 · " + reason).withStyle(ChatFormatting.AQUA));
        
        changed(p.getUUID());
        return got;
    }

    /** Glimmer for dismantling a weapon of this tier. */
    public static long dismantleValue(WeaponRarity r) {
        return switch (r) { case COMMON -> 2; case UNCOMMON -> 5; case RARE -> 10; case LEGENDARY -> 25; case EXOTIC -> 50; };
    }

    // ------------------------------------------------------------------ item conversion

    public static ItemPayload payload(ItemStack stack) {
        var ops = SERVER.registryAccess().createSerializationContext(NbtOps.INSTANCE);
        var tag = (CompoundTag) ItemStack.CODEC.encodeStart(ops, stack).getOrThrow();
        var entry = WeaponItems.entry(stack);
        if (entry.isEmpty()) return new ItemPayload(LEDGER.newId(), tag, "", stack.getHoverName().getString(), "", "");
        var skin = WeaponSkins.of(stack);
        String name = skin.map(WeaponSkins.Skin::display).orElse(WeaponScreenText.weapon(entry.get().id(), entry.get().name()));
        return new ItemPayload(LEDGER.newId(), tag, skin.map(WeaponSkins.Skin::id).orElse(entry.get().id()), name,
                WeaponRarity.of(stack).id(), WeaponCharacteristics.of(entry.get()).slot().name());
    }

    /** Describe a stack without reserving a ledger id (uid 0): previews and validation only. */
    static ItemPayload payloadPreview(ItemStack stack) {
        var p = payload(stack);
        return new ItemPayload(0, p.stack(), p.weaponId(), p.name(), p.rarity(), p.slot());
    }

    /** Decode a payload; empty when it no longer decodes (shown as damaged, never deleted). */
    public static Optional<ItemStack> stack(ItemPayload p) {
        if (SERVER == null) return Optional.empty();
        var ops = SERVER.registryAccess().createSerializationContext(NbtOps.INSTANCE);
        return ItemStack.CODEC.parse(ops, p.stack()).result().filter(s -> !s.isEmpty());
    }

    /** Null when inventory slot {@code index} may leave the player for the economy, else why not. */
    public static String movable(ServerPlayer p, int index) {
        if (index < FIRST_SLOT || (!WeaponStorage.token(index) && index > LAST_SLOT)) return "장착 중인 무기는 옮길 수 없습니다.";
        var stack = WeaponStorage.resolve(p, index);
        if (stack.isEmpty()) return "빈 칸입니다.";
        if (kim.biryeong.destiny.tutorial.TutorialLoan.active(p) || kim.biryeong.destiny.tutorial.TutorialLoan.borrowed(p, stack))
            return "실습용으로 빌린 무기는 옮길 수 없습니다.";
        for (var slot : WeaponSlot.values())
            for (var o : WeaponEquipmentService.owned(p, slot)) if (o.inventoryIndex() == index && o.equipped()) return "장착 중인 무기는 옮길 수 없습니다.";
        return null;
    }

    /**
     * Destiny postmaster: an uncollected reward (drop left behind, activity ended) goes to the Guardian's mailbox.
     * Works for offline owners. Returns false only when the mailbox is at its system cap or the economy is down.
     */
    public static boolean postmaster(java.util.UUID id, String name, ItemStack stack, String message) {
        if (LEDGER == null || SERVER == null || stack.isEmpty()) return false;
        LEDGER.touch(id, name);
        var r = LEDGER.deliver(id, EconomyLedger.MailKind.LOST_ITEM, "우편 관리자", payload(stack), 0, message, now());
        if (!r.ok()) { kim.biryeong.destiny.DestinyGuardians.LOGGER.warn("[Economy] postmaster refused {} for {}: {}", stack.getHoverName().getString(), name, r.error()); return false; }
        changed(id);
        // Activities drain during shutdown, possibly after the stopping save: persist now.
        if (!SERVER.isRunning()) save(true);
        return true;
    }

    /** Null when {@code stack} can be placed into the player's storage now, else why not. Never mutates. */
    public static String canReceive(ServerPlayer p, ItemStack stack) {
        var engram = kim.biryeong.destiny.loot.Loot.engramTier(stack);
        if (engram.isPresent()) return kim.biryeong.destiny.loot.Loot.engramRoom(p);
        var entry = WeaponItems.entry(stack);
        if (entry.isPresent()) return WeaponStorage.room(p, stack);
        for (int i = FIRST_SLOT; i <= LAST_SLOT; i++) if (p.getInventory().getItem(i).isEmpty()) return null;
        return "인벤토리에 빈 칸이 없습니다.";
    }

    /** Place a stack (already checked with {@link #canReceive}). Null on success. */
    static String place(ServerPlayer p, ItemStack stack) {
        var engram = kim.biryeong.destiny.loot.Loot.engramTier(stack);
        if (engram.isPresent()) return kim.biryeong.destiny.loot.Loot.storeEngram(p, engram.get());
        if (WeaponItems.entry(stack).isPresent()) return GearAcquisition.store(p, stack);
        for (int i = FIRST_SLOT; i <= LAST_SLOT; i++) if (p.getInventory().getItem(i).isEmpty()) {
            p.getInventory().setItem(i, stack); p.getInventory().setChanged(); return null;
        }
        return "인벤토리에 빈 칸이 없습니다.";
    }

    /** Take inventory slot {@code index} out as a payload (removing it). Caller must commit. */
    static ItemPayload take(ServerPlayer p, int index) {
        var stack = WeaponStorage.resolve(p, index);
        var payload = payload(stack);
        if (WeaponStorage.token(index)) {
            if (!WeaponStorage.remove(p, index, stack)) throw new IllegalStateException("Storage ownership changed");
        } else { p.getInventory().setItem(index, ItemStack.EMPTY); p.getInventory().setChanged(); }
        return payload;
    }

    /** Undo {@link #take} when the ledger refused the payload. */
    static void restore(ServerPlayer p, int index, ItemPayload payload) {
        var stack = stack(payload).orElseThrow();
        if (WeaponStorage.token(index) && WeaponStorage.restore(p, index, stack)) return;
        if (!WeaponStorage.token(index) && WeaponItems.entry(stack).isPresent()) { WeaponStorage.retain(p, stack); return; }
        if (!WeaponStorage.token(index) && p.getInventory().getItem(index).isEmpty()) { p.getInventory().setItem(index, stack); p.getInventory().setChanged(); }
        else if (place(p, stack) != null) LEDGER.deliver(p.getUUID(), EconomyLedger.MailKind.OVERFLOW, "시스템", payload, 0, "보관 실패로 반환된 물품", now());
    }
}
