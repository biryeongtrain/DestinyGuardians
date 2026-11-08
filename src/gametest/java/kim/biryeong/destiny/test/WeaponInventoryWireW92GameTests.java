package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundContainerSetContentPacket;
import net.minecraft.network.protocol.game.ClientboundContainerSetSlotPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.inventory.ContainerListener;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemStackTemplate;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.ChargedProjectiles;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Actual native outbound bytes with client decode; no direct Polymer getter as the model oracle.
 * Server packet inputs are fixtures, not native keyboard, framebuffer or audio evidence.
 */
public final class WeaponInventoryWireW92GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final Identifier IZANAGI = Identifier.parse("destiny:weapon_izanagi_w91/izanagis_burden");
    private static final CustomModelData SENTINEL = new CustomModelData(
            List.of(17f, .375f, 47f, -1f, 99f, 91.125f, 96.125f, 73f),
            List.of(true, false, true), List.of("hip", "w92_keep", "extra"), List.of(0x123456, 0xABCDEF));

    private static void check(GameTestHelper h, boolean yes, String reason) {
        h.assertTrue(yes, Component.literal(reason));
    }
    private static CustomModelData data(ItemStack stack) {
        return stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
    }
    private static WeaponCatalog.Entry entry(ItemStack stack) { return WeaponItems.entry(stack).orElseThrow(); }
    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, WeaponProfile.forEntry(entry(stack)));
    }
    private static Identifier canonical(ItemStack stack) { return Identifier.parse(entry(stack).item_model()); }
    private static int menuSlot(ServerPlayer player) {
        return player.inventoryMenu.findSlot(player.getInventory(), player.getInventory().getSelectedSlot()).orElseThrow();
    }
    private static void state(GameTestHelper h, ItemStack stack, int loaded, int reserve, int charge) {
        var a = ammo(stack);
        check(h, a.rounds() == loaded && a.reserve() == reserve && a.overflow() == 0
                && WeaponIzanagi.charge(stack) == charge, "Actual magazine/reserve/charge: " + loaded + "/" + reserve + " x" + charge);
    }
    private static void request(GameTestHelper h, ServerPlayer player, boolean honed) {
        boolean wasShift = player.isShiftKeyDown();
        player.setShiftKeyDown(honed);
        try {
            player.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                    ServerboundPlayerActionPacket.Action.DROP_ITEM, BlockPos.ZERO, Direction.UP));
        } finally {
            player.setShiftKeyDown(wasShift);
        }
        check(h, WeaponRuntime.reloading(player) && WeaponIzanagi.honing(player) == honed,
                "Production Q/ShiftQ packet starts the intended reload transaction");
    }

    private static final class Fixture {
        final GameTestHelper h;
        final long created;
        final List<InventoryWireW92> wires = new ArrayList<>();

        Fixture(GameTestHelper h) {
            this.h = h; created = h.getLevel().getServer().getTickCount();
            for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
            h.onEachTick(() -> {
                var origin = h.absoluteVec(Vec3.ZERO);
                for (var w : wires) {
                    var p = w.player; var b = p.getBoundingBox();
                    check(h, p.level() == h.getLevel() && b.minX > origin.x && b.maxX < origin.x + 48
                            && b.minY > origin.y && b.maxY < origin.y + 12
                            && b.minZ > origin.z && b.maxZ < origin.z + 32,
                            "Entire owned player AABB stays in the W90 isolated fixture");
                }
            });
        }
        InventoryWireW92 player() {
            var w = new InventoryWireW92(h, new Vec3(4 + 6 * wires.size(), 4, 8));
            wires.add(w); w.player.setAttached(WeaponLoadout.ENABLED, false);
            // Observe the ordinary server-listener copy as well as outgoing client bytes.
            var listener = new ContainerListener() {
                @Override public void slotChanged(AbstractContainerMenu menu, int slot, ItemStack stack) {
                    if (stack.is(WeaponCombatItem.INSTANCE))
                        check(h, canonical(stack).equals(stack.get(DataComponents.ITEM_MODEL)),
                                "Server slot-listener retains canonical combat snapshot");
                    check(h, !(stack.is(Items.CROSSBOW) || stack.is(Items.STICK))
                                    || !stack.has(DataComponents.ITEM_MODEL),
                            "Outbound vanilla carrier never contaminates server slot listeners");
                }
                @Override public void dataChanged(AbstractContainerMenu menu, int index, int value) {}
            };
            w.player.inventoryMenu.addSlotListener(listener);
            TestCleanup.register(h, () -> w.player.inventoryMenu.removeSlotListener(listener));
            return w;
        }
        ItemStack item(String id, int loaded, int reserve, WeaponModels.Grip grip) {
            var e = WeaponCatalog.find(id).orElseThrow();
            var stack = WeaponModels.withGrip(WeaponItems.create(e), grip).orElseThrow();
            stack.set(DataComponents.CUSTOM_NAME, Component.literal("W92_" + java.util.UUID.randomUUID()));
            stack.set(DataComponents.CUSTOM_MODEL_DATA, SENTINEL);
            stack.set(DataComponents.CHARGED_PROJECTILES, ChargedProjectiles.of(new ItemStackTemplate(Items.SPECTRAL_ARROW)));
            WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(e), loaded, reserve));
            return stack;
        }
        ItemStack equip(InventoryWireW92 w, int loaded, int reserve) {
            var stack = item("izanagis_burden", loaded, reserve, WeaponModels.Grip.TWO_HAND);
            w.player.getInventory().setItem(0, stack); w.player.getInventory().setSelectedSlot(0);
            WeaponRuntime.tickPlayer(w.player);
            full(h, w, canonical(stack)); // Prime native RemoteSlot baseline before any live transaction.
            return stack;
        }
        void at(int tick, Runnable action) {
            check(h, h.getLevel().getServer().getTickCount() == created,
                    "Register all deadlines at initialization, never nested callbacks");
            h.runAfterDelay(tick, () -> {
                check(h, h.getLevel().getServer().getTickCount() - created == tick, "Actual server deadline " + tick);
                for (var w : wires) WeaponRuntime.tickPlayer(w.player);
                action.run();
            });
        }
    }

    private static ItemStack selectedSlot(GameTestHelper h, InventoryWireW92 w, List<Packet<?>> packets) {
        var p = w.player;
        var found = packets.stream().filter(ClientboundContainerSetSlotPacket.class::isInstance)
                .map(ClientboundContainerSetSlotPacket.class::cast)
                .filter(packet -> packet.getContainerId() == p.inventoryMenu.containerId && packet.getSlot() == menuSlot(p)).toList();
        check(h, found.size() == 1, "Native broadcastChanges emits exactly one selected-slot frame; actual " + found.size());
        var packet = found.getFirst();
        check(h, packet.getStateId() > 0 && packet.getStateId() <= p.inventoryMenu.getStateId(),
                "Incremental frame has a native stateId within this fresh menu's ordered updates");
        return packet.getItem();
    }
    private static ItemStack selectedContent(GameTestHelper h, InventoryWireW92 w, List<Packet<?>> packets) {
        var p = w.player;
        var found = packets.stream().filter(ClientboundContainerSetContentPacket.class::isInstance)
                .map(ClientboundContainerSetContentPacket.class::cast)
                .filter(packet -> packet.containerId() == p.inventoryMenu.containerId).toList();
        check(h, found.size() == 1, "Native sendAllDataToRemote emits exactly one full-content frame");
        var packet = found.getFirst();
        check(h, packet.stateId() == p.inventoryMenu.getStateId() && packet.items().size() == p.inventoryMenu.slots.size()
                        && packet.carriedItem().isEmpty(), "Full frame retains native stateId, slot count and empty carried stack");
        return packet.items().get(menuSlot(p));
    }
    private static void carrier(GameTestHelper h, InventoryWireW92 w, ItemStack live, ItemStack decoded, Identifier model) {
        boolean two = WeaponModels.twoHanded(live);
        check(h, decoded != live && decoded.is(two ? Items.CROSSBOW : Items.STICK)
                        && !decoded.is(WeaponCombatItem.INSTANCE), "Client decoder sees vanilla carrier, never Polymer-restored server combat item");
        check(h, projected(model).equals(decoded.get(DataComponents.ITEM_MODEL)),
                "Encoded client ITEM_MODEL must be " + model + "; actual " + decoded.get(DataComponents.ITEM_MODEL));
        var source = data(live); var wire = data(decoded);
        check(h, wire.floats().equals(source.floats()) && wire.strings().equals(source.strings())
                        && wire.colors().equals(source.colors()) && wire.flags().equals(wireFlags(live)),
                "Actual wire preserves float3 ADS, float5/6 selectors, every other float, pose string0, strings/colors; flag0 is canonical grip");
        check(h, two ? Objects.equals(decoded.get(DataComponents.CHARGED_PROJECTILES),
                        ChargedProjectiles.of(new ItemStackTemplate(Items.ARROW))) : !decoded.has(DataComponents.CHARGED_PROJECTILES),
                "Native crossbow heartbeat charge/native grip removal survives actual packet encoding");
        check(h, !WeaponSwapPresentation.active(decoded) && !WeaponIzanagiPresentation.active(decoded)
                        && !WeaponSwapPresentation.active(live.copy()) && !WeaponIzanagiPresentation.active(live.copy()),
                "Neither decoded carrier nor equal-component copy acquires exact-source helper authority");
        var context = ((PacketContextProvider) (Object) w.player.connection).getPacketContext();
        var restored = PolymerItemUtils.getRealItemStack(decoded, context, w.player.registryAccess());
        check(h, restored != decoded && ItemStack.matches(restored, live)
                        && canonical(live).equals(restored.get(DataComponents.ITEM_MODEL)),
                "Separate Polymer server restoration retains the exact canonical real-item components and ammo snapshot");
    }
    private static void unchanged(GameTestHelper h, InventoryWireW92 w, ItemStack source, ItemStack before) {
        check(h, w.player.getMainHandItem() == source && ItemStack.matches(source, before)
                        && source.is(WeaponCombatItem.INSTANCE) && canonical(source).equals(source.get(DataComponents.ITEM_MODEL)),
                "Transport preserves exact selected server identity, canonical ITEM_MODEL, all components/ammo/charge");
        check(h, PacketContext.get() == null, "Native encoder and client decoder leave no recipient scope");
    }
    private static void full(GameTestHelper h, InventoryWireW92 w, Identifier model) {
        var source = w.player.getMainHandItem(); var before = source.copy();
        carrier(h, w, source, selectedContent(h, w, w.full()), model);
        unchanged(h, w, source, before);
    }
    private static void both(GameTestHelper h, InventoryWireW92 w, Identifier model) {
        var source = w.player.getMainHandItem(); var before = source.copy();
        var packets = w.incremental();
        carrier(h, w, source, selectedSlot(h, w, packets), model);
        var nativeUpdates = packets.stream().filter(ClientboundContainerSetSlotPacket.class::isInstance)
                .map(ClientboundContainerSetSlotPacket.class::cast)
                .filter(packet -> packet.getContainerId() == w.player.inventoryMenu.containerId).toList();
        check(h, nativeUpdates.getLast().getStateId() == w.player.inventoryMenu.getStateId(),
                "Final native slot update reaches the authoritative menu stateId");
        for (int i = 1; i < nativeUpdates.size(); i++)
            check(h, nativeUpdates.get(i - 1).getStateId() < nativeUpdates.get(i).getStateId(),
                    "Native incremental stateIds strictly follow packet order within the fresh menu");
        unchanged(h, w, source, before);
        full(h, w, model);
        check(h, w.incremental().stream().noneMatch(ClientboundContainerSetSlotPacket.class::isInstance),
                "Unchanged native RemoteSlot emits no duplicate incremental update after full sync");
    }
    private static void sample(GameTestHelper h, ItemStack stack, float low, float high) {
        float value = data(stack).getFloat(6);
        check(h, WeaponIzanagiPresentation.active(stack) && value >= low && value < high,
                "Actual owned Izanagi selector lies in " + low + ".." + high + "; actual " + value);
    }

    

    

    private record Pair(InventoryWireW92 wire, ItemStack outgoing, ItemStack incoming, int target, int stow, int ready) {}
    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void bothSwapDirectionsAndCarriersReachWireAsOutgoingStowThenIncomingReady(GameTestHelper h) {
        var f = new Fixture(h); var pairs = new ArrayList<Pair>();
        for (String from : List.of("austringer", "beloved")) for (var grip : WeaponModels.Grip.values()) {
            var w = f.player(); var p = w.player;
            var a = f.item(from, from.equals("beloved") ? 2 : 5, 5, WeaponModels.Grip.NATIVE);
            var b = f.item(from.equals("austringer") ? "beloved" : "austringer", from.equals("austringer") ? 2 : 5, 5, grip);
            int start = WeaponCharacteristics.of(entry(a)).slot().hotbar();
            int target = WeaponCharacteristics.of(entry(b)).slot().hotbar();
            p.setAttached(WeaponLoadout.ENABLED, true);
            p.getInventory().setItem(start, a); p.getInventory().setItem(target, b);
            p.getInventory().setSelectedSlot(start); WeaponRuntime.tickPlayer(p); full(h, w, canonical(a));
            var pair = new Pair(w, a, b, target, WeaponHandlingProfile.of(entry(a)).stowTicks(),
                    WeaponHandlingProfile.of(entry(b)).readyTicks());
            pairs.add(pair);
            p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(target)); WeaponRuntime.tickPlayer(p);
            swap(h, pair, WeaponSwapCycle.Phase.STOW); both(h, w, swapModel(pair));
            check(h, !WeaponRuntime.beginUse(p) && !WeaponRuntime.reload(p), "Actual Handling gates fire and reload during STOW");
        }
        for (int tick = 1; tick <= 18; tick++) {
            int elapsed = tick;
            f.at(tick, () -> {
                for (var pair : pairs) {
                    if (elapsed == pair.stow) {
                        swap(h, pair, WeaponSwapCycle.Phase.READY); both(h, pair.wire, swapModel(pair));
                        check(h, !WeaponRuntime.beginUse(pair.wire.player) && !WeaponRuntime.reload(pair.wire.player),
                                "Actual Handling still gates fire/reload during READY");
                    }
                    if (elapsed == pair.stow + pair.ready) {
                        check(h, !WeaponSwapPresentation.active(pair.incoming) && !WeaponHandling.blocked(pair.wire.player)
                                        && WeaponHandling.presentation(pair.wire.player).isEmpty(), "Original Handling deadline retires presentation");
                        both(h, pair.wire, canonical(pair.incoming));
                    }
                }
                if (elapsed == 18) {
                    check(h, pairs.stream().allMatch(pair -> pair.stow + pair.ready <= 18), "Every tested pair reached its real deadline");
                    h.succeed();
                }
            });
        }
    }
    private static Identifier swapModel(Pair pair) {
        return Identifier.parse("destiny:weapon_swap_w91/" + entry(pair.outgoing).id() + "_to_" + entry(pair.incoming).id());
    }
    private static void swap(GameTestHelper h, Pair pair, WeaponSwapCycle.Phase phase) {
        var view = WeaponHandling.presentation(pair.wire.player).orElseThrow();
        check(h, view.outgoing().equals(entry(pair.outgoing)) && pair.wire.player.getMainHandItem() == pair.incoming
                        && view.phase() == phase && WeaponSwapPresentation.active(pair.incoming), "Actual selected pair and Handling phase authorize route");
        float value = data(pair.incoming).getFloat(5);
        check(h, value >= (phase == WeaponSwapCycle.Phase.STOW ? 0 : 2)
                        && value < (phase == WeaponSwapCycle.Phase.STOW ? 1.01f : 3.01f), "Native float5 encodes outgoing STOW / incoming READY");
        check(h, ammo(pair.outgoing).rounds() == (entry(pair.outgoing).id().equals("beloved") ? 2 : 5)
                        && ammo(pair.incoming).rounds() == (entry(pair.incoming).id().equals("beloved") ? 2 : 5)
                        && ammo(pair.outgoing).reserve() == (WeaponProfile.forEntry(entry(pair.outgoing)).infiniteReserve() ? 0 : 5)
                        && ammo(pair.incoming).reserve() == (WeaponProfile.forEntry(entry(pair.incoming)).infiniteReserve() ? 0 : 5)
                        && ammo(pair.outgoing).overflow() == 0 && ammo(pair.incoming).overflow() == 0,
                "Real swap preserves loaded rounds, exact Primary0/Special5 reserves and zero overflow");
    }

    @GameTest(structure = FLOOR, maxTicks = 15, environment = "destiny-test:w90_isolated")
    public void queuedNativeSnapshotPrecedesOrderedCancellationAndNeverRebinds(GameTestHelper h) {
        var f = new Fixture(h); var w = f.player(); var s = f.equip(w, 2, 2);
        request(h, w.player, true);
        w.discard();
        w.player.inventoryMenu.broadcastChanges(); // Freeze a valid send-time carrier into actual queued bytes.
        var frozen = s.copy();
        WeaponRuntime.cancelUseForSkill(w.player);
        check(h, !WeaponIzanagiPresentation.active(s), "Production cancellation retires the pending binding");
        w.player.inventoryMenu.sendAllDataToRemote(); // Later native full state follows the already encoded snapshot.
        var packets = w.capture();
        var old = selectedSlot(h, w, packets);
        carrier(h, w, frozen, old, IZANAGI);
        carrier(h, w, s, selectedContent(h, w, packets), canonical(s));
        var queuedSlot = packets.stream().filter(ClientboundContainerSetSlotPacket.class::isInstance)
                .map(ClientboundContainerSetSlotPacket.class::cast).filter(packet -> packet.getSlot() == menuSlot(w.player)).findFirst().orElseThrow();
        var cleanupContent = packets.stream().filter(ClientboundContainerSetContentPacket.class::isInstance)
                .map(ClientboundContainerSetContentPacket.class::cast).findFirst().orElseThrow();
        check(h, queuedSlot.getStateId() < cleanupContent.stateId(), "Cancellation stateId follows the already queued send-time stateId");
        int slotAt = -1; int contentAt = -1;
        for (int i = 0; i < packets.size(); i++) {
            if (packets.get(i) instanceof ClientboundContainerSetSlotPacket packet && packet.getSlot() == menuSlot(w.player)) slotAt = i;
            if (packets.get(i) instanceof ClientboundContainerSetContentPacket) contentAt = i;
        }
        check(h, slotAt >= 0 && contentAt > slotAt && !WeaponIzanagiPresentation.active(frozen),
                "Ordered native frames preserve valid old send then cleanup; frozen copies cannot revive a binding");
        state(h, s, 2, 2, 0);
        f.at(5, () -> { full(h, w, canonical(s)); state(h, s, 2, 2, 0); h.succeed(); });
    }
}
