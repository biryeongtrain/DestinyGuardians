package kim.biryeong.destiny.test;

import kim.biryeong.destiny.inventory.*;
import kim.biryeong.destiny.inventory.gear.*;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.item.*;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Real server objects/packet handlers. Master runs centrally; no claim of native-client keyboard coverage. */
public final class WeaponStorageW328GameTests {
    private static final String FLOOR = "destiny-test:floor", ENV = "destiny-test:w90_isolated";
    private static void check(GameTestHelper h, boolean ok, String why) { h.assertTrue(ok, Component.literal(why)); }
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2, 1, 6), 0, 0); p.setNoGravity(true); p.setOnGround(true);
        TestCleanup.register(h, () -> { WeaponScreen.close(p); WeaponRuntime.cleanup(p); TestPlayers.remove(p); }); return p;
    }
    private static ItemStack item(String id, int rounds) {
        var e = WeaponCatalog.find(id).orElseThrow(); var stack = WeaponItems.create(e);
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, 5, 7)); return stack;
    }
    private static int token(ServerPlayer p, ItemStack stack) {
        return WeaponStorage.entries(p).stream().filter(e -> e.stack() == stack).findFirst().orElseThrow().token();
    }
    @GameTest(structure=FLOOR, environment=ENV, maxTicks=40)
    public void migrationMovesExactSpareObjectsAndPreservesEquipmentItemsComponentsAndRepeatSafety(GameTestHelper h) {
        var p = player(h); var equipped = item("austringer", 3); var spare = item("eyasluna", 4);
        check(h, WeaponPerks.select(spare, "headstone"), "Eyasluna exact manifest Headstone roll selected before migration");
        var selectedRoll = WeaponPerks.selected(spare, "headstone").orElseThrow();
        spare.set(DataComponents.CUSTOM_NAME, Component.literal("Original spare")); var before = spare.copy();
        var other = new ItemStack(Items.DIAMOND, 17);
        p.getInventory().setItem(0, equipped); p.getInventory().setItem(8, spare); p.getInventory().setItem(12, other);
        p.getInventory().setSelectedSlot(0); WeaponStorage.migrate(p);
        check(h, p.getInventory().getItem(0) == equipped && p.getInventory().getItem(8).isEmpty() && p.getInventory().getItem(12) == other,
                "Only spare weapon removed; equipped and unrelated objects unchanged");
        check(h, WeaponStorage.entries(p).size() == 1 && WeaponStorage.get(p, token(p, spare)) == spare
                && ItemStack.matches(spare, before)
                && WeaponPerks.selected(WeaponStorage.get(p, token(p, spare)), "headstone").filter(selectedRoll::equals).isPresent(),
                "Canonical spare object, exact Headstone socket roll and every component preserved");
        int next = WeaponStorage.data(p).nextId(); WeaponStorage.migrate(p);
        check(h, WeaponStorage.entries(p).size() == 1 && WeaponStorage.data(p).nextId() == next, "Repeated migration does not duplicate or remint tokens");
        h.succeed();
    }
    @GameTest(structure=FLOOR, environment=ENV, maxTicks=40)
    public void rewardEntersSystemStorageAndEExchangePreservesObjectsAndRejectsStaleOwnership(GameTestHelper h) {
        var p = player(h); var old = item("austringer", 3); var next = item("eyasluna", 4);
        p.getInventory().setItem(0, old); p.getInventory().setSelectedSlot(0);
        check(h, GearAcquisition.store(p, next) == null, "Reward accepted directly into attachment");
        for (int i = 3; i < 36; i++) check(h, p.getInventory().getItem(i).isEmpty(), "Reward consumes no vanilla storage slot");
        int id = token(p, next); var oldCopy = old.copy(); var nextCopy = next.copy();
        check(h, WeaponEquipmentService.equip(p, id, next.copy()) != null, "Equal copied preview cannot borrow ownership");
        check(h, WeaponEquipmentService.equip(p, id, next) == null, "Owned E token equips");
        check(h, p.getMainHandItem() == next && WeaponStorage.entries(p).size() == 1 && WeaponStorage.get(p, token(p, old)) == old,
                "Exact old and new objects exchanged between equipment and system storage");
        check(h, ItemStack.matches(old, oldCopy) && ItemStack.matches(next, nextCopy), "Ammo/overflow/custom data conserved");
        check(h, WeaponEquipmentService.equip(p, id, next) != null, "Consumed stale token cannot duplicate equipped object");
        h.succeed();
    }
    @GameTest(structure=FLOOR, environment=ENV, maxTicks=100)
    public void rejectedCombatSlotsPreservePendingReloadAndReturnAuthoritativeHeldSlotOnWire(GameTestHelper h) {
        var wire = new InventoryWireW92(h, new Vec3(2, 1, 6)); var p = wire.player;
        var held = item("austringer", 3); p.getInventory().setItem(0, held); p.getInventory().setSelectedSlot(0);
        p.setAttached(WeaponLoadout.ENABLED, false); WeaponRuntime.tickPlayer(p);
        check(h, WeaponRuntime.reload(p), "Real reload started even for legacy disabled loadout");
        var ready = WeaponHandling.readiness(p); var before = held.copy(); wire.discard();
        for (int i = 3; i < 9; i++) p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(i));
        check(h, p.getInventory().getSelectedSlot() == 0 && p.getMainHandItem() == held && WeaponRuntime.reloading(p), "All stray4-9 packets preserve held object and pending reload");
        check(h, ItemStack.matches(held, before) && WeaponHandling.readiness(p).equals(ready), "Rejection cannot mutate ammo or restart handling");
        var corrections = wire.capture().stream().filter(v -> v instanceof ClientboundSetHeldSlotPacket).map(v -> (ClientboundSetHeldSlotPacket)v).toList();
        check(h, corrections.size() == 6 && corrections.stream().allMatch(v -> v.slot() == 0), "Six genuine encoded slot corrections sent");
        h.runAfterDelay(WeaponProfile.forEntry(WeaponItems.entry(held).orElseThrow()).reloadTicks()+1, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, !WeaponRuntime.reloading(p) && WeaponRuntime.beginUse(p), "Original reload completes and weapon still fires"); h.succeed();
        });
    }
    @GameTest(structure=FLOOR, environment=ENV, maxTicks=40)
    public void guiAllowsOtherSlotsAndCloseRestoresCombatSelectionWithoutMovingEquipment(GameTestHelper h) {
        var p = player(h); var first = item("austringer", 3); var second = item("beloved", 2);
        p.getInventory().setItem(0, first); p.getInventory().setItem(1, second); p.getInventory().setSelectedSlot(0);
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
        check(h, p.getMainHandItem() == second, "Ordinary1-3 selection remains accepted"); WeaponHotbarGuard.observe(p);
        p.openMenu(new SimpleMenuProvider((id, inv, pl) -> ChestMenu.threeRows(id, inv), Component.literal("W328 fixture")));
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(8));
        check(h, p.getInventory().getSelectedSlot() == 8 && WeaponHotbarGuard.guiOpen(p), "External GUI slot9 is not blocked");
        p.connection.handleContainerClose(new ServerboundContainerClosePacket(p.containerMenu.containerId));
        check(h, p.getInventory().getSelectedSlot() == 1 && p.getMainHandItem() == second
                && p.getInventory().getItem(0) == first, "Closing GUI restores last valid equipped slot with exact ownership"); h.succeed();
    }
    @GameTest(structure=FLOOR, environment=ENV, maxTicks=40)
    public void codecRoundTripPersistsOwnedComponentsTokensAndIsolatesPlayers(GameTestHelper h) {
        var p = player(h); var other = player(h); var spare = item("eyasluna", 6);
        spare.set(DataComponents.CUSTOM_NAME, Component.literal("Persisted spare"));
        check(h, GearAcquisition.store(p, spare) == null, "Stored before save");
        var ops = p.registryAccess().createSerializationContext(NbtOps.INSTANCE);
        var serialized = WeaponStorage.Data.CODEC.encodeStart(ops, WeaponStorage.data(p)).getOrThrow();
        var restored = WeaponStorage.Data.CODEC.parse(ops, serialized).getOrThrow();
        var row = restored.entries().getFirst();
        check(h, row.token() == token(p, spare) && row.stack() != spare && ItemStack.matches(row.stack(), spare), "Save/load retains token and full components with independent deserialized object");
        other.setAttached(WeaponStorage.DATA, restored); WeaponStorage.remove(p, token(p, spare), spare);
        check(h, WeaponStorage.entries(p).isEmpty() && WeaponStorage.entries(other).size() == 1
                && ItemStack.matches(WeaponStorage.entries(other).getFirst().stack(), spare), "One player consumption never alters another attachment"); h.succeed();
    }
    @GameTest(structure=FLOOR, environment=ENV, maxTicks=40)
    public void gearScreenShowsAndEquipsStoredWeaponsWithNoVanillaSpareStacks(GameTestHelper h) {
        var p = player(h); var old = item("austringer", 3); var spare = item("eyasluna", 4);
        p.getInventory().setItem(0, old); p.getInventory().setSelectedSlot(0); GearAcquisition.store(p, spare);
        check(h, GearScreen.open(p), "Player E gear screen opens");
        var view = GearScreen.snapshot(p).orElseThrow();
        check(h, view.bucket(WeaponSlot.KINETIC).equipped().stack() == old
                && view.bucket(WeaponSlot.KINETIC).stored().getFirst().stack() == spare, "E includes equipped and attachment-owned spare");
        var box = GearLayout.slot(GearSlot.KINETIC); GearScreen.qaPoint(p, box.x(), box.y());
        box = GearLayout.storage(GearSlot.KINETIC, 0); GearScreen.qaPoint(p, box.x(), box.y());
        GearScreen.click(p, false);
        check(h, p.getMainHandItem() == spare && WeaponStorage.entries(p).stream().anyMatch(e -> e.stack() == old), "Actual E pointer click exchanges owned references");
        for (int i = 3; i < 36; i++) check(h, p.getInventory().getItem(i).isEmpty(), "E equip leaves no physical spare");
        GearScreen.close(p); h.succeed();
    }
    @GameTest(structure=FLOOR, environment=ENV, maxTicks=40)
    public void migrationRetainsOverCapWeaponsAndECanReachNextPage(GameTestHelper h) {
        var p = player(h); p.getInventory().setItem(0, item("austringer", 3));
        for (int i = 3; i < 15; i++) p.getInventory().setItem(i, item("eyasluna", i));
        WeaponStorage.migrate(p);
        check(h, WeaponStorage.entries(p).size() == 12, "Legacy over-cap ownership retained in full");
        check(h, GearAcquisition.store(p, item("eyasluna", 1)) != null, "New rewards respect existing bucket capacity");
        check(h, GearScreen.open(p), "E opens on over-cap bucket");
        var box = GearLayout.slot(GearSlot.KINETIC); GearScreen.qaPoint(p, box.x(), box.y()); GearScreen.click(p, false);
        var visible = GearScreen.snapshot(p).orElseThrow().bucket(WeaponSlot.KINETIC).stored();
        check(h, visible.size() == 3 && visible.getFirst().stack() == WeaponStorage.entries(p).get(9).stack(), "Equipped-tile click exposes overflow page without losing weapons");
        GearScreen.close(p); h.succeed();
    }
}
