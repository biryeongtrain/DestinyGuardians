package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundContainerSetContentPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** Actual Runtime-owned handoffs, not aliases retained in the donor's hand.
 * The late donor is cleaned twice synchronously before the recipient's first tick.
 * Uses W92's unchanged native encoder/client decoder; no fabricated State or clock.
 */
public final class WeaponLegacyRetirementW93GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final String ISOLATED = "destiny-test:w90_isolated";
    private static final CustomModelData SENTINEL = new CustomModelData(
            List.of(17f, .375f, 47f, -1f, 99f, 91.125f, 96.125f, 73f),
            List.of(true, false, true), List.of("hip", "w93_retirement", "extra"), List.of(0x123456));

    private static void check(GameTestHelper h, boolean yes, String why) {
        h.assertTrue(yes, Component.literal(why));
    }
    private static WeaponCatalog.Entry entry(ItemStack s) { return WeaponItems.entry(s).orElseThrow(); }
    private static WeaponProfile profile(ItemStack s) { return WeaponProfile.forEntry(entry(s)); }
    private static WeaponMagazine ammo(ItemStack s) { return WeaponItems.magazine(s, profile(s)); }
    private static CustomModelData data(ItemStack s) { return s.get(DataComponents.CUSTOM_MODEL_DATA); }
    private static Identifier canonical(ItemStack s) { return Identifier.parse(entry(s).item_model()); }
    private static Identifier reloadModel(ItemStack s) {
        return Identifier.parse("destiny:" + switch (entry(s).id()) {
            case "beloved" -> "weapon_reload_w208_beloved/beloved";
            case "duke_mk_44" -> "weapon_reload_w215_duke_mk_44/duke_mk_44";
            case "ammit_ar2" -> "weapon_reload_w207_ammit_ar2/ammit_ar2";
            default -> throw new IllegalArgumentException("Unexpected reload fixture");
        });
    }
    private static Identifier bowModel(ItemStack s) {
        return Identifier.parse("destiny:weapon_bow_w50/" + entry(s).id());
    }
    private static void amounts(GameTestHelper h, ItemStack s, int rounds, int reserve) {
        var a = ammo(s);
        check(h, a.rounds() == rounds && a.reserve() == reserve && a.overflow() == 0,
                "Actual transferred original has magazine/reserve/overflow " + rounds + "/" + reserve + "/0");
    }
    private static void reload(GameTestHelper h, InventoryWireW92 w) {
        w.player.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.DROP_ITEM, BlockPos.ZERO, Direction.UP));
        check(h, WeaponRuntime.reloading(w.player)
                        && WeaponReloadPresentation.ownedBy(w.player, w.player.getMainHandItem()),
                "Production Q acquired an actual Runtime cycle and owner-bound reload presentation");
    }
    private static void useBow(GameTestHelper h, InventoryWireW92 w) {
        WeaponCombatItem.INSTANCE.use(w.player.level(), w.player, InteractionHand.MAIN_HAND);
        check(h, w.player.isUsingItem() && w.player.getUseItem() == w.player.getMainHandItem()
                        && WeaponBowPresentation.ownedBy(w.player, w.player.getMainHandItem())
                        && WeaponRuntime.bowDrawState(w.player).phase() == WeaponBowWindow.Phase.DRAWING,
                "Production native use acquired real Runtime draw and exact bow ownership");
    }
    private static void transfer(GameTestHelper h, InventoryWireW92 a, InventoryWireW92 b, ItemStack s) {
        a.player.stopUsingItem();
        a.player.getInventory().setItem(0, ItemStack.EMPTY);
        b.player.getInventory().setItem(0, s); b.player.getInventory().setSelectedSlot(0);
        check(h, a.player.getMainHandItem().isEmpty() && b.player.getMainHandItem() == s,
                "Exact original leaves A's inventory and becomes B's selected source; no donor hand alias");
    }
    private static void full(GameTestHelper h, InventoryWireW92 w, Identifier model) {
        var s = w.player.getMainHandItem(); var before = s.copy();
        var frames = w.full().stream().filter(ClientboundContainerSetContentPacket.class::isInstance)
                .map(ClientboundContainerSetContentPacket.class::cast)
                .filter(p -> p.containerId() == w.player.inventoryMenu.containerId).toList();
        check(h, frames.size() == 1, "Native full sync emits exactly one recipient inventory frame");
        var frame = frames.getFirst();
        int slot = w.player.inventoryMenu.findSlot(w.player.getInventory(), w.player.getInventory().getSelectedSlot()).orElseThrow();
        var decoded = frame.items().get(slot); boolean two = WeaponModels.twoHanded(s);
        check(h, frame.stateId() == w.player.inventoryMenu.getStateId()
                        && frame.items().size() == w.player.inventoryMenu.slots.size() && frame.carriedItem().isEmpty()
                        && decoded.is(two ? Items.CROSSBOW : Items.STICK) && projected(model).equals(decoded.get(DataComponents.ITEM_MODEL)),
                "Context-free native bytes retain recipient layout/state and the expected owned model/carrier");
        var wire = data(decoded); var source = data(s);
        check(h, wire.floats().equals(source.floats()) && wire.strings().equals(source.strings())
                        && wire.colors().equals(source.colors()) && wire.flags().equals(wireFlags(s)),
                "Actual bytes preserve selectors/unrelated data with existing grip normalization");
        check(h, w.player.getMainHandItem() == s && ItemStack.matches(s, before)
                        && canonical(s).equals(s.get(DataComponents.ITEM_MODEL)) && PacketContext.get() == null,
                "Transport leaves exact canonical server source, ammo, all components and context unchanged");
        check(h, !WeaponReloadPresentation.active(s.copy()) && !WeaponBowPresentation.active(s.copy())
                        && !WeaponReloadPresentation.active(decoded) && !WeaponBowPresentation.active(decoded),
                "Copied and decoded components do not gain recipient authority");
    }

    private static final class Fixture {
        final GameTestHelper h;
        final long created;
        final List<InventoryWireW92> wires = new ArrayList<>();
        Fixture(GameTestHelper h) {
            this.h = h; created = h.getLevel().getServer().getTickCount();
            check(h, !h.getLevel().getGameRules().get(GameRules.SPAWN_MOBS), "W90 natural spawning is disabled before setup");
            for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
            h.onEachTick(() -> {
                var o = h.absoluteVec(Vec3.ZERO);
                for (var w : wires) {
                    var b = w.player.getBoundingBox();
                    check(h, w.player.level() == h.getLevel() && b.minX > o.x && b.maxX < o.x + 48
                                    && b.minY > o.y && b.maxY < o.y + 12 && b.minZ > o.z && b.maxZ < o.z + 32,
                            "Whole owned-player AABB stays inside the W90 isolated structure");
                }
            });
        }
        InventoryWireW92 player() {
            int i = wires.size();
            var w = new InventoryWireW92(h, new Vec3(4 + 6 * (i % 7), 4, 8 + 8 * (i / 7)));
            wires.add(w); w.player.setAttached(WeaponLoadout.ENABLED, false);
            return w; // InventoryWireW92 registers TestCleanup before channel/listener setup.
        }
        ItemStack equip(InventoryWireW92 a, String id, WeaponModels.Grip grip) {
            var e = WeaponCatalog.find(id).orElseThrow();
            var s = WeaponModels.withGrip(WeaponItems.create(e), grip).orElseThrow();
            s.set(DataComponents.CUSTOM_MODEL_DATA, SENTINEL);
            WeaponItems.save(s, new WeaponMagazine(WeaponProfile.forEntry(e), 1, 5));
            a.player.getInventory().setItem(0, s); a.player.getInventory().setSelectedSlot(0);
            WeaponRuntime.tickPlayer(a.player); full(h, a, canonical(s));
            return s;
        }
        void at(int tick, Runnable action) {
            check(h, h.getLevel().getServer().getTickCount() == created, "Register every deadline upfront");
            h.runAfterDelay(tick, () -> {
                check(h, h.getLevel().getServer().getTickCount() - created == tick, "Actual server deadline " + tick);
                action.run(); // Deliberately never tick B implicitly before the cleanup assertions.
            });
        }
    }

    private record Handoff(InventoryWireW92 donor, InventoryWireW92 recipient, ItemStack stack, int duration, int credit) {}
    @GameTest(structure = FLOOR, maxTicks = 140, environment = ISOLATED)
    public void lateRuntimeDonorCleanupCannotRetireRecipientsActualReloadOrChangeItsDeadline(GameTestHelper h) {
        var f = new Fixture(h); var cases = new ArrayList<Handoff>();
        for (String id : List.of("beloved", "duke_mk_44", "ammit_ar2")) for (var grip : WeaponModels.Grip.values()) {
            var a = f.player(); var b = f.player(); var s = f.equip(a, id, grip); reload(h, a);
            var p = profile(s); int duration = WeaponRuntime.ammunition(a.player).orElseThrow().reloadDuration();
            int credit = ReloadCreditProfile.ammoTicks(entry(s),
                    new WeaponReloadPolicy.Plan(p.firstReloadTicks(), p.reloadTicks(), p.roundsPerInsert()));
            cases.add(new Handoff(a, b, s, duration, credit));
        }
        f.at(1, () -> {
            for (var c : cases) {
                WeaponRuntime.tickPlayer(c.donor.player);
                check(h, WeaponReloadPresentation.ownedBy(c.donor.player, c.stack), "A still owns its actual Runtime reload before transfer");
                transfer(h, c.donor, c.recipient, c.stack); reload(h, c.recipient);
                var before = c.stack.copy(); var cycle = WeaponRuntime.ammunition(c.recipient.player).orElseThrow();
                check(h, cycle.reloadDuration() == c.duration && cycle.reloadRemaining() == c.duration,
                        "B input captures a new full deadline one tick after A input");
                full(h, c.recipient, reloadModel(c.stack));
                WeaponRuntime.cleanup(c.donor.player); WeaponRuntime.cleanup(c.donor.player);
                check(h, ItemStack.matches(before, c.stack) && cycle.equals(WeaponRuntime.ammunition(c.recipient.player).orElseThrow())
                                && WeaponReloadPresentation.ownedBy(c.recipient.player, c.stack)
                                && !WeaponReloadPresentation.ownedBy(c.donor.player, c.stack),
                        "Before any B tick, two late A cleanups preserve B selector, all components, cycle and ammo");
                full(h, c.recipient, reloadModel(c.stack));
            }
        });
        int end = cases.stream().mapToInt(Handoff::duration).max().orElseThrow() + 2;
        check(h, end < 140, "Every new recipient deadline fits the test");
        for (int t = 2; t <= end; t++) {
            int elapsed = t - 1;
            f.at(t, () -> {
                for (var c : cases) {
                    WeaponRuntime.tickPlayer(c.recipient.player);
                    var p = profile(c.stack); int moved = p.infiniteReserve() ? p.magazine() - 1 : Math.min(p.magazine() - 1, 5);
                    boolean paid = elapsed >= c.credit;
                    amounts(h, c.stack, paid ? 1 + moved : 1, p.infiniteReserve() ? 0 : 5 - (paid ? moved : 0));
                    check(h, WeaponRuntime.reloading(c.recipient.player) == (elapsed < c.duration)
                                    && WeaponReloadPresentation.ownedBy(c.recipient.player, c.stack) == (elapsed < c.duration),
                            "Only B's accepted deadline controls remaining cycle and route");
                    if (elapsed < c.duration)
                        check(h, WeaponRuntime.ammunition(c.recipient.player).orElseThrow().reloadRemaining() == c.duration - elapsed,
                                "Late cleanup never reset or advanced B recovery deadline");
                    if (elapsed == c.credit || elapsed == c.duration - 1 || elapsed == c.duration)
                        full(h, c.recipient, elapsed < c.duration ? reloadModel(c.stack) : canonical(c.stack));
                }
                if (elapsed == end - 1) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 45, environment = ISOLATED)
    public void lateRuntimeDonorCleanupCannotRetireRecipientsActualBowDrawOrAgeItsClock(GameTestHelper h) {
        var f = new Fixture(h); var cases = new ArrayList<Handoff>();
        for (String id : List.of("biting_winds", "whispering_slab")) {
            var a = f.player(); var b = f.player(); var s = f.equip(a, id, WeaponModels.Grip.NATIVE); useBow(h, a);
            cases.add(new Handoff(a, b, s, profile(s).chargeTicks(), 0));
        }
        f.at(1, () -> {
            for (var c : cases) {
                WeaponRuntime.tickPlayer(c.donor.player);
                check(h, WeaponBowPresentation.ownedBy(c.donor.player, c.stack), "A owns Runtime bow state before actual transfer");
                transfer(h, c.donor, c.recipient, c.stack); useBow(h, c.recipient);
                var before = c.stack.copy(); var cycle = WeaponRuntime.ammunition(c.recipient.player).orElseThrow();
                var draw = WeaponRuntime.bowDrawState(c.recipient.player);
                check(h, draw.phase() == WeaponBowWindow.Phase.DRAWING && draw.progress() == 0 && draw.fullDrawAge() == -1,
                        "B's accepted draw starts at zero rather than inheriting donor elapsed time");
                full(h, c.recipient, bowModel(c.stack));
                WeaponRuntime.cleanup(c.donor.player); WeaponRuntime.cleanup(c.donor.player);
                check(h, ItemStack.matches(before, c.stack) && cycle.equals(WeaponRuntime.ammunition(c.recipient.player).orElseThrow())
                                && draw.equals(WeaponRuntime.bowDrawState(c.recipient.player))
                                && WeaponBowPresentation.ownedBy(c.recipient.player, c.stack)
                                && !WeaponBowPresentation.ownedBy(c.donor.player, c.stack)
                                && c.recipient.player.isUsingItem() && c.recipient.player.getUseItem() == c.stack,
                        "Before any B tick, two late A cleanups preserve B bow selector, draw clock, hold, cycle and ammo");
                full(h, c.recipient, bowModel(c.stack));
            }
        });
        int end = cases.stream().mapToInt(Handoff::duration).max().orElseThrow() + 3;
        check(h, end < 45, "Every recipient full-draw deadline fits the test");
        for (int t = 2; t <= end; t++) {
            int elapsed = t - 1;
            f.at(t, () -> {
                for (var c : cases) {
                    WeaponRuntime.tickPlayer(c.recipient.player); amounts(h, c.stack, 1, 0);
                    int expected = 2 + (int)Math.floor(Math.min(1, elapsed / (float)c.duration) * 20 + 1e-6f);
                    var draw = WeaponRuntime.bowDrawState(c.recipient.player);
                    check(h, WeaponBowPresentation.ownedBy(c.recipient.player, c.stack)
                                    && Math.floor(data(c.stack).getFloat(2)) == expected
                                    && Math.abs(draw.progress() - Math.min(1, elapsed / (float)c.duration)) < .00001f
                                    && draw.fullDrawAge() == (elapsed < c.duration ? -1 : elapsed - c.duration)
                                    && draw.phase() == (elapsed < c.duration ? WeaponBowWindow.Phase.DRAWING
                                        : elapsed - c.duration < draw.windowTicks() ? WeaponBowWindow.Phase.PERFECT : WeaponBowWindow.Phase.LATE)
                                    && !WeaponRuntime.reloading(c.recipient.player) && WeaponRuntime.activeProjectiles(c.recipient.player) == 0,
                            "B draw advances only on its real clock and never fires or nocks from donor cleanup");
                    if (elapsed == c.duration - 1 || elapsed == c.duration || elapsed == end - 1) full(h, c.recipient, bowModel(c.stack));
                    if (elapsed == end - 1) {
                        c.recipient.player.stopUsingItem(); WeaponRuntime.cleanup(c.recipient.player);
                        check(h, !WeaponBowPresentation.active(c.stack), "B's own cleanup still retires B's acquisition");
                        amounts(h, c.stack, 1, 0); full(h, c.recipient, canonical(c.stack));
                    }
                }
                if (elapsed == end - 1) h.succeed();
            });
        }
    }
}
