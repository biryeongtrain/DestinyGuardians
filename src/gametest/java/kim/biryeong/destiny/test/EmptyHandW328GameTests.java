package kim.biryeong.destiny.test;

import kim.biryeong.destiny.weapon.WeaponOutboundPresentation;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundContainerSetSlotPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

public final class EmptyHandW328GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2, 1, 6), 0, 0);
        p.getInventory().clearContent(); p.getInventory().setSelectedSlot(0);
        TestCleanup.register(h, () -> {
            p.containerMenu = ChestMenu.threeRows(99, p.getInventory());
            kim.biryeong.destiny.inventory.InventoryMenuRedirect.externalMenu(p);
            WeaponOutboundPresentation.refreshEmptyHand(p);
            TestPlayers.remove(p);
        });
        return p;
    }
    private static boolean invisible(ItemStack stack) {
        var model = stack.get(DataComponents.ITEM_MODEL);
        return stack.is(Items.STICK) && model != null
                && model.toString().equals("destiny:weapon_sword_hand_empty")
                && stack.getHoverName().getString().isEmpty();
    }
    private static List<ClientboundContainerSetSlotPacket> slots(ServerPlayer p) {
        return TestPlayers.outbound(p).stream().filter(ClientboundContainerSetSlotPacket.class::isInstance)
                .map(ClientboundContainerSetSlotPacket.class::cast).toList();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=30, environment="destiny-test:w90_isolated")
    public void selectedEmptyHandIsWireOnlyAndOtherSlotsRemainEmpty(GameTestHelper h) {
        var p = player(h);
        var projected = WeaponOutboundPresentation.projectSlot(p, p.inventoryMenu, 36, ItemStack.EMPTY);
        check(h, invisible(projected), "Selected empty weapon bucket receives only an invisible wire carrier");
        check(h, p.getMainHandItem().isEmpty() && p.getInventory().isEmpty(), "No authoritative item was created");
        for (int slot : new int[]{9, 35, 37, 38, 39, 44, 45})
            check(h, WeaponOutboundPresentation.projectSlot(p, p.inventoryMenu, slot, ItemStack.EMPTY).isEmpty(),
                    "Unselected, stored and offhand slots remain genuinely empty: " + slot);
        var stale = new ItemStack(Items.DIAMOND);
        check(h, WeaponOutboundPresentation.projectSlot(p, p.inventoryMenu, 36, stale) == stale,
                "A stale nonempty snapshot cannot mint a carrier");
        var snapshots = new ArrayList<ItemStack>();
        for (int i=0; i<p.inventoryMenu.slots.size(); i++) snapshots.add(ItemStack.EMPTY);
        var result = WeaponOutboundPresentation.projectContent(p, p.inventoryMenu, snapshots);
        check(h, snapshots.stream().allMatch(ItemStack::isEmpty), "Source snapshots stay unchanged");
        check(h, result.stream().filter(s -> !s.isEmpty()).count() == 1 && invisible(result.get(36)),
                "Content projection affects exactly the selected empty hand");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=30, environment="destiny-test:w90_isolated")
    public void externalMenusForeignOwnersAndNonWeaponBucketsAreNeverProjected(GameTestHelper h) {
        var p = player(h); var other = player(h);
        check(h, WeaponOutboundPresentation.projectSlot(p, other.inventoryMenu, 36, ItemStack.EMPTY).isEmpty(),
                "Foreign inventory cannot borrow the recipient's empty-hand authority");
        p.containerMenu = ChestMenu.threeRows(7, p.getInventory());
        check(h, !WeaponOutboundPresentation.emptyHandCarrier(p)
                        && WeaponOutboundPresentation.projectSlot(p, p.inventoryMenu, 36, ItemStack.EMPTY).isEmpty(),
                "An external GUI retains actual empty slots");
        p.containerMenu = p.inventoryMenu;
        for (int selected=3; selected<9; selected++) {
            p.getInventory().setSelectedSlot(selected);
            check(h, !WeaponOutboundPresentation.emptyHandCarrier(p), "No carrier outside buckets 1-3");
        }
        p.getInventory().setSelectedSlot(0);
        var real = new ItemStack(Items.DIAMOND); p.getInventory().setItem(0, real);
        check(h, !WeaponOutboundPresentation.emptyHandCarrier(p)
                        && WeaponOutboundPresentation.projectSlot(p, p.inventoryMenu, 36, real) == real,
                "Ordinary real items retain their actual projection and ownership");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=30, environment="destiny-test:w90_isolated")
    public void selectionAndGuiTransitionsClearTheOldCarrierWithoutPerTickSpam(GameTestHelper h) {
        var p = player(h); TestPlayers.drain(p);
        WeaponOutboundPresentation.refreshEmptyHand(p);
        var first = slots(p);
        check(h, first.size()==1 && first.getFirst().getSlot()==36 && invisible(first.getFirst().getItem()),
                "First empty selection is projected through the real recipient listener");
        WeaponOutboundPresentation.refreshEmptyHand(p);
        check(h, slots(p).isEmpty(), "Unchanged empty selection emits no repeated packet");
        p.getInventory().setSelectedSlot(1); WeaponOutboundPresentation.refreshEmptyHand(p);
        var swapped = slots(p);
        check(h, swapped.size()==2 && swapped.get(0).getSlot()==36 && swapped.get(0).getItem().isEmpty()
                        && swapped.get(1).getSlot()==37 && invisible(swapped.get(1).getItem()),
                "Old wire carrier clears before the new selected empty bucket is projected");
        p.containerMenu = ChestMenu.threeRows(8, p.getInventory());
        WeaponOutboundPresentation.refreshEmptyHand(p);
        var opened = slots(p);
        check(h, opened.size()==1 && opened.getFirst().getSlot()==37 && opened.getFirst().getItem().isEmpty(),
                "Opening a GUI clears the cosmetic hand and keeps its actual slot empty");
        check(h, p.getInventory().isEmpty(), "All transitions preserve the actual empty inventory");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=30, environment="destiny-test:w90_isolated")
    public void rejectedGearOpenLeavesNativeInventoryGenuinelyEmptyUntilClose(GameTestHelper h) {
        var p = player(h);
        WeaponOutboundPresentation.refreshEmptyHand(p); TestPlayers.drain(p);
        kim.biryeong.destiny.inventory.InventoryMenuRedirect.closed(p);
        var beacon = TestPlayers.outbound(p).stream()
                .filter(net.minecraft.network.protocol.game.ClientboundRecipeBookAddPacket.class::isInstance)
                .map(net.minecraft.network.protocol.game.ClientboundRecipeBookAddPacket.class::cast)
                .flatMap(packet -> packet.entries().stream())
                .filter(entry -> entry.contents().id().index() >= 0x3f000000)
                .findFirst().orElseThrow().contents().id();
        // Use the native sleeping state without camera/chunk-tracker side effects.
        // Gear explicitly blocks sleeping, while the ordinary inventory remains usable.
        p.setSleepingPos(p.blockPosition());
        try {
            check(h, p.isSleeping() && kim.biryeong.destiny.inventory.InventoryMenuRedirect.seen(p, beacon)
                            && kim.biryeong.destiny.inventory.InventoryMenuRedirect.nativeOpen(p),
                    "Sleeping rejects Gear and leaves the native E inventory tracked as open");
        } finally {
            p.clearSleepingPos();
        }
        WeaponOutboundPresentation.refreshEmptyHand(p);
        check(h, !WeaponOutboundPresentation.emptyHandCarrier(p)
                        && WeaponOutboundPresentation.projectSlot(p, p.inventoryMenu, 36, ItemStack.EMPTY).isEmpty(),
                "Native inventory GUI never contains the cosmetic empty-hand carrier");
        var cleared = slots(p);
        check(h, cleared.stream().anyMatch(packet -> packet.getSlot()==36 && packet.getItem().isEmpty()),
                "Existing carrier is explicitly cleared on rejected Gear-open transition");
        kim.biryeong.destiny.inventory.InventoryMenuRedirect.closed(p);
        WeaponOutboundPresentation.refreshEmptyHand(p);
        check(h, WeaponOutboundPresentation.emptyHandCarrier(p) && p.getInventory().isEmpty(),
                "Closing native inventory restores presentation only, never ownership");
        h.succeed();
    }
}
