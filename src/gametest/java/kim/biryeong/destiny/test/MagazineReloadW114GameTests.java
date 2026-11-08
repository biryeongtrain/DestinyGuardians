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

/** W114 real gameplay reloads for Blast Furnace/Hammerhead, using unchanged W92 PLAY encoding/client decoding.
 * Packet inputs are fixtures; these tests do not establish native rendering, keyboard or audio output.
 * Capacity and deadlines follow the current catalog/WeaponTiming without a W100 gameplay rebalance.
 */
public final class MagazineReloadW114GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final String ISOLATED = "destiny-test:w90_isolated";
    private static final List<String> NEW = List.of("blast_furnace", "hammerhead");
    private static final float EPS = .00001f;
    private static final CustomModelData SENTINEL = new CustomModelData(
            List.of(17f, -1f, 47f, -1f, 99f, 91.125f, 96.125f, 73f),
            List.of(true, false, true), List.of("hip", "w114_keep", "extra"), List.of(0x123456, 0xABCDEF));

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
    /** Expected authored 61-pose routes (W207-W222), independent of the production selector. */
    static Identifier expectedReloadRoute(String id) {
        String bank = switch (id) {
            case "ace_of_spades" -> "weapon_reload_w157";
            case "ammit_ar2", "blast_furnace", "hammerhead" -> "weapon_reload_w207_" + id;
            case "beloved", "the_recluse", "gnawing_hunger", "austringer" -> "weapon_reload_w208_" + id;
            case "antiope_d", "bug_out_bag", "cold_denial", "bygones" -> "weapon_reload_w212_" + id;
            case "lonesome", "steelfeather_repeater", "aishas_embrace", "chattering_bone" -> "weapon_reload_w213_" + id;
            case "halfdan_d", "claws_of_the_wolf", "bite_of_the_fox", "retrofit_escapade" -> "weapon_reload_w214_" + id;
            case "duke_mk_44", "farewell", "apostate", "fixed_odds" -> "weapon_reload_w215_" + id;
            case "distant_relation", "patron_of_lost_causes", "brass_attacks", "ikelos_smg_v1_0_1" -> "weapon_reload_w216_" + id;
            case "erentil_fr4", "hollow_words", "dream_breaker", "null_composure", "coriolis_force" -> "weapon_reload_w217_" + id;
            case "line_in_the_sand", "stormchaser", "code_duello", "bellowing_giant", "bad_omens" -> "weapon_reload_w218_" + id;
            case "allied_demand", "dead_man_walking_xx7463", "high_albedo", "frontier_justice", "retraced_path" -> "weapon_reload_w219_" + id;
            case "edge_transit", "canis_major", "dimensional_hypotrochoid", "deafening_whisper", "salvager_s_salvo" -> "weapon_reload_w220_" + id;
            case "pyroclastic_flow", "seventh_seraph_officer_revolver" -> "weapon_reload_w221_" + id;
            case "biting_winds", "whispering_slab", "nezarec_s_whisper" -> "weapon_reload_w222_" + id;
            default -> throw new IllegalArgumentException("Unexpected reload fixture: " + id);
        };
        return Identifier.parse("destiny:" + bank + "/" + id);
    }
    private static Identifier reloadModel(ItemStack s) { return expectedReloadRoute(entry(s).id()); }
    /** w46-timing.json baseline; wire animation migration must not retime these six reloads. */
    private static int duration(ItemStack s) {
        return switch (entry(s).id()) {
            case "blast_furnace", "the_recluse" -> 43;
            case "hammerhead" -> 91;
            case "beloved" -> 62;
            case "duke_mk_44" -> 59;
            case "ammit_ar2" -> 41;
            default -> throw new IllegalArgumentException("Unexpected timing fixture");
        };
    }
    private static int credit(ItemStack s) {
        // w65-reload-credit.json: only Duke/Hammerhead in this fixture have early credit.
        double fraction = switch (entry(s).id()) {
            case "duke_mk_44" -> .71;
            case "hammerhead" -> .65;
            default -> 1;
        };
        return (int)Math.ceil(duration(s) * fraction);
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
                        && !decoded.is(WeaponCombatItem.INSTANCE) && WeaponGripGameTests.projected(model).equals(decoded.get(DataComponents.ITEM_MODEL)),
                "Context-free PLAY decode has expected vanilla carrier and model " + model);
        var a = data(s); var b = data(decoded);
        check(h, b.floats().equals(a.floats()) && b.strings().equals(a.strings()) && b.colors().equals(a.colors())
                        && b.flags().equals(WeaponGripGameTests.wireFlags(s)), "Encoded selectors and independent CMD survive; flags express client grip");
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
                "Live float1 keeps the authored 61 samples and the existing acquisition offset");
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

    private static List<Reload> cases(GameTestHelper h, Fixture f, List<String> ids, int rounds, int reserve) {
        var result = new ArrayList<Reload>();
        for (String id : ids) for (var grip : WeaponModels.Grip.values()) {
            var w = f.player();
            result.add(start(h, w, f.equip(w, id, grip, rounds, reserve,
                    grip == WeaponModels.Grip.NATIVE ? -1 : 0)));
        }
        return result;
    }
    private static int end(GameTestHelper h, List<Reload> cases) {
        int end = cases.stream().mapToInt(Reload::duration).max().orElseThrow() + 2;
        check(h, end < 180, "Current real catalog deadlines fit test timeout"); return end;
    }
    private static void accounting(GameTestHelper h, Reload r, int elapsed, int rounds, int reserve) {
        var p = profile(r.stack); int moved = p.infiniteReserve() ? p.magazine() - rounds : Math.min(p.magazine() - rounds, reserve);
        boolean paid = elapsed >= r.credit;
        amounts(h, r.stack, rounds + (paid ? moved : 0), p.infiniteReserve() ? 0 : reserve - (paid ? moved : 0));
    }

    

    

    @GameTest(structure = FLOOR, maxTicks = 180, environment = ISOLATED)
    public void sameTickQAndSkillCancellationNeverCreditGhostAmmo(GameTestHelper h) {
        var f = new Fixture(h); var rs = new ArrayList<Reload>();
        for (String id : NEW) for (var grip : WeaponModels.Grip.values()) {
            var w = f.player(); var s = f.equip(w, id, grip, 2, 9, 0);
            w.player.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                    ServerboundPlayerActionPacket.Action.DROP_ITEM, BlockPos.ZERO, Direction.UP));
            var r = new Reload(w, s, duration(s), credit(s), .001f); rs.add(r);
            live(h, r, 0); both(h, w, reloadModel(s)); var before = s.copy();
            w.player.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                    ServerboundPlayerActionPacket.Action.DROP_ALL_ITEMS, BlockPos.ZERO, Direction.UP));
            check(h, ItemStack.matches(before, s) && w.player.getMainHandItem() == s, "Q duplicate consumed, no drop/restart");
            WeaponRuntime.cancelUseForSkill(w.player); retired(h, r); both(h, w, base(s));
        }
        int end = end(h, rs);
        for (int tick = 1; tick <= end; tick++) {
            int elapsed = tick; f.at(tick, () -> {
                for (var r : rs) { retired(h, r); accounting(h, r, 0, 2, 9); }
                if (elapsed == end) { for (var r : rs) full(h, r.wire, base(r.stack)); h.succeed(); }
            });
        }
    }

    

    

    

    @GameTest(structure = FLOOR, maxTicks = 10, environment = ISOLATED)
    public void deniedFullMagazineOrEmptyHeavyReserveNeverActivatesSavedSelectors(GameTestHelper h) {
        var f = new Fixture(h);
        for (String id : NEW) for (var grip : WeaponModels.Grip.values()) {
            var w = f.player(); var p = WeaponProfile.forEntry(WeaponCatalog.find(id).orElseThrow());
            var s = f.equip(w, id, grip, p.magazine(), 0, .5f); var before = s.copy();
            check(h, !WeaponRuntime.reload(w.player) && !WeaponRuntime.reloading(w.player)
                    && !WeaponReloadPresentation.active(s), "Full magazine denies reload despite saved selector");
            full(h, w, base(s)); check(h, ItemStack.matches(before, s), "Denied full reload preserves exact saved components");
            if (!p.infiniteReserve()) {
                WeaponItems.save(s, new WeaponMagazine(p, 1, 0)); before = s.copy();
                check(h, !WeaponRuntime.reload(w.player) && !WeaponRuntime.reloading(w.player)
                        && !WeaponReloadPresentation.active(s), "Heavy zero reserve denies reload and graph authority");
                full(h, w, base(s)); check(h, ItemStack.matches(before, s), "Denied empty-reserve reload grants no ammo or selector mutation");
                amounts(h, s, 1, 0);
            }
            hud(h, w, false);
        }
        h.succeed();
    }

    
}
