package kim.biryeong.destiny.test;

import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundContainerSetContentPacket;
import net.minecraft.network.protocol.game.ClientboundContainerSetSlotPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerListener;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** Accepted gameplay reloads and actual server deadlines, using unchanged W92 PLAY encoding/client decoding.
 * Packet inputs are fixtures; these tests do not establish native rendering, keyboard or audio output.
 * Capacity and deadlines follow the current catalog/WeaponTiming without a W100 gameplay rebalance.
 */
public final class RecluseReloadW100GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final String ISOLATED = "destiny-test:w90_isolated";
    private static final String RECLUSE = "the_recluse";
    private static final float EPS = .00001f;
    private static final CustomModelData SENTINEL = new CustomModelData(
            List.of(17f, -1f, 47f, -1f, 99f, 91.125f, 96.125f, 73f),
            List.of(true, false, true), List.of("hip", "w100_keep", "extra"), List.of(0x123456, 0xABCDEF));

    private record Reload(InventoryWireW92 wire, ItemStack stack, int duration, int credit, float offset) {}

    private static void check(GameTestHelper h, boolean yes, String reason) {
        h.assertTrue(yes, Component.literal(reason));
    }
    private static void near(GameTestHelper h, float actual, float expected, String reason) {
        check(h, Math.abs(actual - expected) < EPS, reason + ": " + actual + " != " + expected);
    }
    private static WeaponCatalog.Entry entry(ItemStack s) { return WeaponItems.entry(s).orElseThrow(); }
    private static WeaponProfile profile(ItemStack s) { return WeaponProfile.forEntry(entry(s)); }
    private static CustomModelData data(ItemStack s) {
        return s.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
    }
    private static float progress(ItemStack s) { return data(s).getFloat(1); }
    private static Identifier base(ItemStack s) { return Identifier.parse(entry(s).item_model()); }
    private static Identifier reloadModel(ItemStack s) {
        return Identifier.parse("destiny:" + switch (entry(s).id()) {
            case RECLUSE -> "weapon_reload_w208_the_recluse/the_recluse";
            case "ammit_ar2" -> "weapon_reload_w207_ammit_ar2/ammit_ar2";
            case "duke_mk_44" -> "weapon_reload_w215_duke_mk_44/duke_mk_44";
            case "beloved" -> "weapon_reload_w208_beloved/beloved";
            default -> throw new IllegalArgumentException("Unexpected reload fixture");
        });
    }
    private static int duration(ItemStack s) { return profile(s).firstReloadTicks(); }
    private static int credit(ItemStack s) {
        var p = profile(s);
        return ReloadCreditProfile.ammoTicks(entry(s),
                new WeaponReloadPolicy.Plan(p.firstReloadTicks(), p.reloadTicks(), p.roundsPerInsert()));
    }
    private static void amounts(GameTestHelper h, ItemStack s, int rounds, int reserve) {
        var a = WeaponItems.magazine(s, profile(s));
        check(h, a.rounds() == rounds && a.reserve() == reserve && a.overflow() == 0,
                entry(s).id() + " authoritative rounds/reserve/overflow = " + rounds + "/" + reserve + "/0");
    }

    private static final class Fixture {
        final GameTestHelper h;
        final long created;
        final List<InventoryWireW92> wires = new ArrayList<>();

        Fixture(GameTestHelper h) {
            this.h = h; created = h.getLevel().getServer().getTickCount();
            check(h, !h.getLevel().getGameRules().get(GameRules.SPAWN_MOBS), "W90 isolation disables natural spawning");
            for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
            h.onEachTick(() -> {
                var o = h.absoluteVec(Vec3.ZERO);
                for (var w : wires) {
                    var b = w.player.getBoundingBox();
                    check(h, w.player.level() == h.getLevel() && b.minX > o.x && b.maxX < o.x + 48
                                    && b.minY > o.y && b.maxY < o.y + 12 && b.minZ > o.z && b.maxZ < o.z + 32,
                            "Whole owned player AABB stays inside W90 isolation");
                }
            });
        }
        InventoryWireW92 player() {
            int i = wires.size();
            var w = new InventoryWireW92(h, new Vec3(4 + 6 * (i % 7), 4, 8 + 8 * (i / 7)));
            wires.add(w); w.player.setAttached(WeaponLoadout.ENABLED, false);
            var listener = new ContainerListener() {
                @Override public void slotChanged(AbstractContainerMenu menu, int slot, ItemStack s) {
                    if (s.is(WeaponCombatItem.INSTANCE))
                        check(h, base(s).equals(s.get(DataComponents.ITEM_MODEL)), "Server listener retains canonical combat model");
                    check(h, !(s.is(Items.STICK) || s.is(Items.CROSSBOW)) || !s.has(DataComponents.ITEM_MODEL),
                            "Client grip carrier never replaces server listener snapshots");
                }
                @Override public void dataChanged(AbstractContainerMenu menu, int index, int value) {}
            };
            w.player.inventoryMenu.addSlotListener(listener);
            TestCleanup.register(h, () -> w.player.inventoryMenu.removeSlotListener(listener));
            return w; // W92 registers player/channel cleanup before construction can fail.
        }
        ItemStack equip(InventoryWireW92 w, String id, WeaponModels.Grip grip, int rounds, int reserve, float selector) {
            var e = WeaponCatalog.find(id).orElseThrow();
            var s = WeaponModels.withGrip(WeaponItems.create(e), grip).orElseThrow();
            var floats = new ArrayList<>(SENTINEL.floats()); floats.set(1, selector);
            s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(floats,
                    SENTINEL.flags(), SENTINEL.strings(), SENTINEL.colors()));
            WeaponItems.save(s, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, reserve));
            hold(w, s); WeaponRuntime.tickPlayer(w.player);
            full(h, w, base(s)); // Establish an idle RemoteSlot before accepted reload acquisition.
            return s;
        }
        void at(int tick, Runnable action) {
            check(h, h.getLevel().getServer().getTickCount() == created, "Register deadlines only during test initialization");
            h.runAfterDelay(tick, () -> {
                check(h, h.getLevel().getServer().getTickCount() - created == tick, "Exact real server elapsed tick " + tick);
                for (var w : wires) WeaponRuntime.tickPlayer(w.player);
                action.run();
            });
        }
    }
    private static void hold(InventoryWireW92 w, ItemStack s) {
        w.player.getInventory().setItem(0, s); w.player.getInventory().setSelectedSlot(0);
    }
    private static int menuSlot(ServerPlayer p) {
        return p.inventoryMenu.findSlot(p.getInventory(), p.getInventory().getSelectedSlot()).orElseThrow();
    }
    private static ItemStack selected(GameTestHelper h, InventoryWireW92 w, List<Packet<?>> packets, boolean full) {
        var p = w.player;
        if (full) {
            var frames = packets.stream().filter(ClientboundContainerSetContentPacket.class::isInstance)
                    .map(ClientboundContainerSetContentPacket.class::cast)
                    .filter(f -> f.containerId() == p.inventoryMenu.containerId).toList();
            check(h, frames.size() == 1, "Exactly one encoded full inventory-content frame");
            var frame = frames.getFirst();
            check(h, frame.stateId() == p.inventoryMenu.getStateId() && frame.items().size() == p.inventoryMenu.slots.size()
                            && frame.carriedItem().isEmpty(), "Full frame retains native stateId/slot count/carried stack");
            return frame.items().get(menuSlot(p));
        }
        var frames = packets.stream().filter(ClientboundContainerSetSlotPacket.class::isInstance)
                .map(ClientboundContainerSetSlotPacket.class::cast)
                .filter(f -> f.getContainerId() == p.inventoryMenu.containerId && f.getSlot() == menuSlot(p)).toList();
        check(h, frames.size() == 1, "Exactly one encoded selected-slot delta, actual=" + frames.size());
        var frame = frames.getFirst();
        check(h, frame.getStateId() > 0 && frame.getStateId() <= p.inventoryMenu.getStateId(), "Delta retains ordered native stateId");
        return frame.getItem();
    }
    private static void carrier(GameTestHelper h, InventoryWireW92 w, ItemStack decoded, Identifier model, ItemStack before) {
        var s = w.player.getMainHandItem(); boolean two = WeaponModels.twoHanded(s);
        check(h, decoded != s && decoded.is(two ? Items.CROSSBOW : Items.STICK)
                        && !decoded.is(WeaponCombatItem.INSTANCE) && WeaponFirstPersonHands.model(model).equals(decoded.get(DataComponents.ITEM_MODEL)),
                "Context-free PLAY decode has expected vanilla carrier and model " + model);
        var a = data(s); var b = data(decoded);
        // Ammit's two-hand carrier also transports the owner's actual crouch pose in flag1.
        var flags = two && entry(s).id().equals("ammit_ar2")
                ? List.of(two, w.player.isCrouching()) : List.of(two);
        check(h, b.floats().equals(a.floats()) && b.strings().equals(a.strings()) && b.colors().equals(a.colors())
                        && b.flags().equals(flags), "Encoded selectors and independent CMD survive; exact grip/crouch flags");
        check(h, two ? CrossbowItem.isCharged(decoded) && !decoded.has(DataComponents.CONSUMABLE)
                        : !decoded.has(DataComponents.CHARGED_PROJECTILES) && decoded.has(DataComponents.CONSUMABLE),
                "Native stick / charged two-hand carrier contract survives PLAY encoding");
        check(h, !WeaponReloadPresentation.active(decoded) && !WeaponReloadPresentation.active(s.copy()),
                "Decoded carrier and component-exact copy never acquire live identity authority");
        check(h, s.is(WeaponCombatItem.INSTANCE) && ItemStack.matches(before, s)
                        && base(s).equals(s.get(DataComponents.ITEM_MODEL)) && PacketContext.get() == null,
                "Transport preserves server components/ammo/canonical identity and releases recipient context");
    }
    private static void full(GameTestHelper h, InventoryWireW92 w, Identifier model) {
        var before = w.player.getMainHandItem().copy();
        carrier(h, w, selected(h, w, w.full(), true), model, before);
    }
    private static void both(GameTestHelper h, InventoryWireW92 w, Identifier model) {
        var before = w.player.getMainHandItem().copy();
        carrier(h, w, selected(h, w, w.incremental(), false), model, before);
        full(h, w, model);
        check(h, w.incremental().stream().noneMatch(ClientboundContainerSetSlotPacket.class::isInstance),
                "Unchanged native RemoteSlot suppresses duplicate slot frames");
    }
    private static Reload start(GameTestHelper h, InventoryWireW92 w, ItemStack s) {
        float previous = progress(s);
        check(h, WeaponRuntime.reload(w.player), "Actual gameplay reload is accepted");
        var r = new Reload(w, s, duration(s), credit(s), previous == 0 ? .001f : 0);
        check(h, WeaponReloadPresentation.PROGRESS_INDEX == 1 && WeaponReloadPresentation.supports(entry(s))
                        && reloadModel(s).equals(WeaponReloadPresentation.model(entry(s))), "Existing float1 helper routes this weapon correctly");
        live(h, r, 0); both(h, w, reloadModel(s));
        return r;
    }
    private static ItemDisplayHud node(ServerPlayer p, String suffix) {
        return (ItemDisplayHud) DisplayHud.getHud(p, AmmoHud.PREFIX + suffix);
    }
    private static void hud(GameTestHelper h, InventoryWireW92 w, boolean reloading) {
        var p = w.player; AmmoHud.update(p);
        var state = WeaponRuntime.ammunition(p).orElseThrow();
        check(h, AmmoHud.current(p).orElseThrow().equals(state) && state.reloading() == reloading
                        && (node(p, "reload_track") != null) == reloading, "HUD observes authoritative phase and retires its track");
        String text = Integer.toString(state.rounds());
        for (int i = 0; i < text.length(); i++) {
            var glyph = node(p, "rounds_" + i);
            check(h, glyph != null && Identifier.parse("destiny:gui/hud/ammo_digit_" + text.charAt(i))
                    .equals(glyph.getItem().get(DataComponents.ITEM_MODEL)), "HUD digit follows authoritative ammunition");
        }
        check(h, node(p, "rounds_" + text.length()) == null, "No stale trailing ammo digit");
        if (state.infiniteReserve()) check(h, node(p, "infinity") != null && node(p, "reserve_0") == null,
                "Primary infinity is retained without fabricated reserve digits");
        float width = reloading ? 276 * (float)Math.floor(state.reloadProgress() * 8) / 8 : 0;
        var fill = node(p, "reload");
        check(h, width == 0 ? fill == null : fill != null && Math.abs(fill.getScale().x - width) < EPS,
                "HUD keeps its existing eight-step full-phase fill");
    }
    private static void live(GameTestHelper h, Reload r, int elapsed) {
        var p = r.wire.player; var s = r.stack;
        var state = WeaponRuntime.ammunition(p).orElseThrow();
        check(h, WeaponRuntime.reloading(p) && WeaponRuntime.reloadOwnedBy(p, s)
                        && WeaponReloadPresentation.ownedBy(p, s) && state.reloadDuration() == r.duration
                        && state.reloadRemaining() == r.duration - elapsed, "Exact owner retains the original real reload deadline");
        near(h, state.reloadProgress(), elapsed / (float)r.duration, "HUD raw progress uses real elapsed server ticks");
        near(h, progress(s), (float)Math.floor(elapsed / (float)r.duration * 60 + 1e-6f) / 60 + r.offset,
                "Live float1 keeps 61 samples and the existing acquisition offset");
        independent(h, s);
        hud(h, r.wire, true);
    }
    private static void independent(GameTestHelper h, ItemStack s) {
        var a = data(s);
        check(h, a.floats().size() == SENTINEL.floats().size(), "Reload never grows or truncates independent float data");
        for (int i = 0; i < SENTINEL.floats().size(); i++) if (i != 1)
            near(h, a.getFloat(i), SENTINEL.getFloat(i), "Independent float " + i + " is preserved");
        check(h, a.flags().equals(SENTINEL.flags()) && a.strings().equals(SENTINEL.strings())
                        && a.colors().equals(SENTINEL.colors()), "Independent server CMD flags/pose/strings/colors are preserved");
    }
    private static void retired(GameTestHelper h, Reload r) {
        check(h, !WeaponRuntime.reloading(r.wire.player) && !WeaponRuntime.reloadOwnedBy(r.wire.player, r.stack)
                        && !WeaponReloadPresentation.active(r.stack) && progress(r.stack) == -1,
                "Retirement clears runtime ownership, ACTIVE identity and float1 selector");
        independent(h, r.stack);
        hud(h, r.wire, false);
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = ISOLATED)
    public void acceptedProfileKeepsCurrentCatalogCapacityAndTiming(GameTestHelper h) {
        var e = WeaponCatalog.find(RECLUSE).orElseThrow(); var p = WeaponProfile.forEntry(e); var t = WeaponTiming.forEntry(e);
        var stack = WeaponItems.create(e);
        check(h, p.magazine() == t.magazine().orElseThrow()
                        && WeaponItems.magazine(stack, p).rounds() == p.magazine(),
                "Accepted Recluse item and profile retain current catalog capacity=" + t.magazine().orElseThrow());
        check(h, p.infiniteReserve() && p.reserve() == 0 && !p.shellReload() && p.roundsPerInsert() == 0
                        && p.reloadTicks() == t.reloadTicks().orElseThrow() && p.firstReloadTicks() == p.reloadTicks(),
                "Recluse keeps existing Primary whole-magazine policy and current WeaponTiming deadline");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 160, environment = ISOLATED)
    public void acceptedReloadEncodesInitialMiddleCompletionAndAuthoritativeHudForBothGrips(GameTestHelper h) {
        var f = new Fixture(h); var cases = new ArrayList<Reload>();
        for (var grip : WeaponModels.Grip.values()) {
            var w = f.player(); var s = f.equip(w, RECLUSE, grip, 2, 0, grip == WeaponModels.Grip.NATIVE ? -1 : 0);
            w.player.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.EMERALD, 4));
            var r = start(h, w, s); cases.add(r);
            check(h, r.credit == r.duration, "Current Recluse profile credits only at its full unchanged deadline");
        }
        int end = cases.getFirst().duration + 2; check(h, end < 160, "Current deadline fits test timeout");
        for (int t = 1; t <= end; t++) {
            int elapsed = t;
            f.at(t, () -> {
                for (var r : cases) {
                    if (elapsed < r.duration) {
                        live(h, r, elapsed); amounts(h, r.stack, 2, 0);
                        if (elapsed == r.duration / 2) {
                            both(h, r.wire, reloadModel(r.stack)); var before = r.stack.copy();
                            for (int i = 0; i < 3; i++) {
                                check(h, !WeaponRuntime.reload(r.wire.player), "Duplicate gameplay reload cannot restart the clock");
                                AmmoHud.current(r.wire.player); full(h, r.wire, reloadModel(r.stack));
                            }
                            check(h, ItemStack.matches(before, r.stack), "Denied duplicates/HUD/packet reads preserve exact ammo and selectors");
                        }
                        if (elapsed == r.duration - 1) {
                            var before = r.stack.copy();
                            check(h, !WeaponRuntime.beginUse(r.wire.player), "Fire is denied one real tick before completion");
                            WeaponRuntime.releaseUse(r.wire.player, r.stack);
                            check(h, ItemStack.matches(before, r.stack), "Denied fire grants no ammunition or early retirement");
                            both(h, r.wire, reloadModel(r.stack));
                        }
                    } else {
                        retired(h, r); amounts(h, r.stack, profile(r.stack).magazine(), 0);
                        if (elapsed == r.duration) both(h, r.wire, base(r.stack));
                        if (elapsed == end) {
                            full(h, r.wire, base(r.stack));
                            check(h, WeaponRuntime.beginUse(r.wire.player), "Firing is available after the original full deadline");
                            WeaponRuntime.releaseUse(r.wire.player, r.stack);
                            amounts(h, r.stack, profile(r.stack).magazine() - 1, 0);
                        }
                    }
                    check(h, r.wire.player.getOffhandItem().is(Items.EMERALD)
                                    && r.wire.player.getOffhandItem().getCount() == 4
                                    && !r.stack.has(DataComponents.CHARGED_PROJECTILES),
                            "Two-hand heartbeat ammo stays client-only and the real offhand remains unchanged");
                }
                if (elapsed == end) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 160, environment = ISOLATED)
    public void sameTickQDuplicateAndSkillCancellationInvalidateEncodedFrameWithoutGhostCredit(GameTestHelper h) {
        var f = new Fixture(h); var cases = new ArrayList<Reload>();
        for (var grip : WeaponModels.Grip.values()) {
            var w = f.player(); var s = f.equip(w, RECLUSE, grip, 2, 0, 0);
            w.player.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                    ServerboundPlayerActionPacket.Action.DROP_ITEM, BlockPos.ZERO, Direction.UP));
            var r = new Reload(w, s, duration(s), credit(s), .001f); cases.add(r);
            live(h, r, 0); both(h, w, reloadModel(s)); var before = s.copy();
            w.player.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                    ServerboundPlayerActionPacket.Action.DROP_ALL_ITEMS, BlockPos.ZERO, Direction.UP));
            check(h, w.player.getMainHandItem() == s && s.getCount() == 1 && ItemStack.matches(before, s),
                    "Real Q/Ctrl-Q duplicate consumes input without dropping or restarting the weapon");
            WeaponRuntime.cancelUseForSkill(w.player);
            check(h, h.getLevel().getServer().getTickCount() == f.created && !ItemStack.matches(before, s),
                    "Same-tick cancellation invalidates even a saved-zero RemoteSlot baseline");
            retired(h, r); amounts(h, s, 2, 0); both(h, w, base(s));
        }
        int end = cases.getFirst().duration + 2; check(h, end < 160, "Cancelled deadline fits timeout");
        for (int t = 1; t <= end; t++) {
            int elapsed = t;
            f.at(t, () -> {
                for (var r : cases) { retired(h, r); amounts(h, r.stack, 2, 0); }
                if (elapsed == end) { for (var r : cases) full(h, r.wire, base(r.stack)); h.succeed(); }
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 160, environment = ISOLATED)
    public void validatedSlotReturnAndRepeatedCleanupCancelRealReloadsBeyondTheirOldDeadlines(GameTestHelper h) {
        var f = new Fixture(h); var swapped = new ArrayList<Reload>(); var cleaned = new ArrayList<Reload>();
        for (var grip : WeaponModels.Grip.values()) {
            var a = f.player(); swapped.add(start(h, a, f.equip(a, RECLUSE, grip, 2, 0, -1)));
            var b = f.player(); cleaned.add(start(h, b, f.equip(b, RECLUSE, grip, 2, 0, -1)));
        }
        int d = swapped.getFirst().duration; check(h, d + 2 < 160, "Current cancelled deadlines fit timeout");
        for (int t = 1; t <= d + 2; t++) {
            int elapsed = t;
            f.at(t, () -> {
                if (elapsed == 1) for (var r : swapped) {
                    var p = r.wire.player; p.getInventory().setItem(7, new ItemStack(Items.STONE));
                    p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(7));
                    p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));
                    check(h, p.getMainHandItem() == r.stack && WeaponHandling.remaining(p) > 0 && !WeaponRuntime.reload(p),
                            "Validated away/back retires exact reload and preserves the existing handling lock");
                    both(h, r.wire, base(r.stack));
                }
                if (elapsed == d / 2) for (var r : cleaned) {
                    live(h, r, elapsed); both(h, r.wire, reloadModel(r.stack));
                    WeaponRuntime.cleanup(r.wire.player); WeaponRuntime.cleanup(r.wire.player);
                    retired(h, r); both(h, r.wire, base(r.stack));
                }
                for (var r : swapped) { retired(h, r); amounts(h, r.stack, 2, 0); }
                for (var r : cleaned) {
                    if (elapsed < d / 2) live(h, r, elapsed); else retired(h, r);
                    amounts(h, r.stack, 2, 0);
                }
                if (elapsed == d + 2) {
                    for (var r : swapped) full(h, r.wire, base(r.stack));
                    for (var r : cleaned) full(h, r.wire, base(r.stack));
                    h.succeed();
                }
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 160, environment = ISOLATED)
    public void copiedAndNbtPersistedMidReloadSelectorsCannotAcquireAmmoHudOrEncodedAuthority(GameTestHelper h) {
        var f = new Fixture(h); var owners = new ArrayList<Reload>(); var replicas = new ArrayList<InventoryWireW92>();
        for (var grip : WeaponModels.Grip.values()) {
            var w = f.player(); owners.add(start(h, w, f.equip(w, RECLUSE, grip, 2, 0, -1)));
        }
        int d = owners.getFirst().duration; check(h, d + 2 < 160, "Persistence deadline fits timeout");
        for (int t = 1; t <= d + 2; t++) {
            int elapsed = t;
            f.at(t, () -> {
                if (elapsed == d / 2) for (var r : owners) {
                    live(h, r, elapsed); both(h, r.wire, reloadModel(r.stack));
                    var ops = h.getLevel().registryAccess().createSerializationContext(NbtOps.INSTANCE);
                    var encoded = ItemStack.CODEC.encodeStart(ops, r.stack).getOrThrow();
                    var saved = ItemStack.CODEC.parse(ops, encoded).getOrThrow();
                    for (var replica : List.of(r.stack.copy(), saved)) {
                        check(h, ItemStack.matches(replica, r.stack) && progress(replica) > 0
                                        && !WeaponReloadPresentation.active(replica), "Real copy/NBT roundtrip keeps components but no ACTIVE identity");
                        var other = f.player(); replicas.add(other); hold(other, replica);
                        var before = replica.copy(); WeaponRuntime.tickPlayer(other.player); hud(h, other, false);
                        check(h, !WeaponRuntime.reloading(other.player) && !WeaponReloadPresentation.ownedBy(other.player, replica)
                                        && ItemStack.matches(before, replica), "Actually held saved/copy cannot schedule reload or mutate selectors/ammo");
                        full(h, other, base(replica));
                    }
                }
                for (var r : owners) {
                    if (elapsed < d) live(h, r, elapsed); else retired(h, r);
                    amounts(h, r.stack, elapsed < d ? 2 : profile(r.stack).magazine(), 0);
                }
                for (var other : replicas) {
                    var s = other.player.getMainHandItem(); hud(h, other, false); amounts(h, s, 2, 0);
                    check(h, !WeaponRuntime.reloading(other.player) && !WeaponReloadPresentation.active(s),
                            "Old original deadline grants neither ghost ammo nor copied presentation authority");
                }
                if (elapsed == d + 2) {
                    check(h, replicas.size() == 4, "Both copy and actual persistence were exercised for both grip modes");
                    for (var r : owners) full(h, r.wire, base(r.stack));
                    for (var other : replicas) full(h, other, base(other.player.getMainHandItem()));
                    h.succeed();
                }
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 160, environment = ISOLATED)
    public void foreignRecipientHoldingExactLiveOriginalCannotBorrowDonorReloadRoute(GameTestHelper h) {
        var f = new Fixture(h); var donors = new ArrayList<Reload>(); var recipients = new ArrayList<InventoryWireW92>();
        for (var grip : WeaponModels.Grip.values()) {
            var donor = f.player(); var r = start(h, donor, f.equip(donor, RECLUSE, grip, 2, 0, -1)); donors.add(r);
            var recipient = f.player(); recipients.add(recipient); hold(recipient, r.stack);
            check(h, recipient.player.getMainHandItem() == r.stack && WeaponReloadPresentation.active(r.stack)
                            && WeaponReloadPresentation.ownedBy(donor.player, r.stack)
                            && !WeaponReloadPresentation.ownedBy(recipient.player, r.stack),
                    "Adversarial exact-object recipient cannot borrow the live donor binding");
            hud(h, recipient, false); full(h, recipient, base(r.stack)); full(h, donor, reloadModel(r.stack));
        }
        int d = donors.getFirst().duration; check(h, d + 1 < 160, "Foreign-recipient deadline fits timeout");
        for (int t = 1; t <= d + 1; t++) {
            int elapsed = t;
            f.at(t, () -> {
                for (int i = 0; i < donors.size(); i++) {
                    var r = donors.get(i); var other = recipients.get(i);
                    check(h, other.player.getMainHandItem() == r.stack && !WeaponRuntime.reloading(other.player)
                                    && !WeaponReloadPresentation.ownedBy(other.player, r.stack), "Foreign recipient never owns the donor's gameplay cycle");
                    hud(h, other, false);
                    if (elapsed < d) live(h, r, elapsed); else retired(h, r);
                    if (elapsed == d / 2 || elapsed == d) {
                        both(h, other, base(r.stack)); both(h, r.wire, elapsed < d ? reloadModel(r.stack) : base(r.stack));
                    }
                }
                if (elapsed == d + 1) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 180, environment = ISOLATED)
    public void recluseCoexistsWithAmmitDukeAndBelovedAtTheirOwnCreditAndCompletionDeadlines(GameTestHelper h) {
        var f = new Fixture(h); var cases = new ArrayList<Reload>();
        for (String id : List.of(RECLUSE, "ammit_ar2", "duke_mk_44", "beloved")) for (var grip : WeaponModels.Grip.values()) {
            var w = f.player(); cases.add(start(h, w, f.equip(w, id, grip, 1, 5, -1)));
        }
        int end = cases.stream().mapToInt(Reload::duration).max().orElseThrow() + 1;
        check(h, end < 180, "All independent current profile deadlines fit timeout");
        for (int t = 1; t <= end; t++) {
            int elapsed = t;
            f.at(t, () -> {
                for (var r : cases) {
                    var p = profile(r.stack); int moved = p.infiniteReserve() ? p.magazine() - 1 : Math.min(p.magazine() - 1, 5);
                    boolean paid = elapsed >= r.credit;
                    amounts(h, r.stack, 1 + (paid ? moved : 0), p.infiniteReserve() ? 0 : 5 - (paid ? moved : 0));
                    if (elapsed < r.duration) live(h, r, elapsed); else retired(h, r);
                    if (elapsed == r.duration / 2 || elapsed == r.credit - 1 || elapsed == r.credit || elapsed == r.duration) {
                        // Adjacent checkpoints may share one quantized sample: full always proves the current route.
                        full(h, r.wire, elapsed < r.duration ? reloadModel(r.stack) : base(r.stack));
                    }
                }
                if (elapsed == end) h.succeed();
            });
        }
    }
}
