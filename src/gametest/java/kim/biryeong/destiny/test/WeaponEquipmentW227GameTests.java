package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.inventory.WeaponEquipmentService;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetHeldSlotPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;

/** Prepared for central registration/execution. Fixtures use actual owned inventory objects. */
public final class WeaponEquipmentW227GameTests {
    private static final String FLOOR = "destiny-test:floor", ENV = "destiny-test:w90_isolated";

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2, 1, 6), 0, -85);
        p.setNoGravity(true);
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); TestPlayers.remove(p); });
        return p;
    }

    private static ItemStack item(String id, int rounds, int reserve, long overflow) {
        var entry = WeaponCatalog.find(id).orElseThrow();
        var stack = WeaponItems.create(entry);
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry), rounds, reserve, overflow));
        return stack;
    }

    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()));
    }

    private record Before(List<ItemStack> references, List<ItemStack> contents, int selected,
                          boolean enabled, Optional<WeaponHandling.Readiness> readiness, boolean reloading) {}

    private static Before before(ServerPlayer p) {
        var references = new ArrayList<ItemStack>();
        var contents = new ArrayList<ItemStack>();
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            var stack = p.getInventory().getItem(i);
            references.add(stack);
            contents.add(stack.copy());
        }
        TestPlayers.drain(p);
        return new Before(references, contents, p.getInventory().getSelectedSlot(), WeaponLoadout.enabled(p),
                WeaponHandling.readiness(p), WeaponRuntime.reloading(p));
    }

    private static void unchanged(GameTestHelper h, ServerPlayer p, Before b) {
        for (int i = 0; i < b.references().size(); i++)
            check(h, p.getInventory().getItem(i) == b.references().get(i)
                    && ItemStack.matches(p.getInventory().getItem(i), b.contents().get(i)),
                    "No reference/count/component mutation at inventory index " + i);
        check(h, p.getInventory().getSelectedSlot() == b.selected()
                && WeaponLoadout.enabled(p) == b.enabled(), "Selection and enabled attachment preserved");
        check(h, WeaponHandling.readiness(p).equals(b.readiness()) && WeaponRuntime.reloading(p) == b.reloading(),
                "Readiness and pending reload unchanged");
        check(h, TestPlayers.outbound(p).isEmpty(), "Read/rejection sends no equipment packets");
    }

    private static void rejected(GameTestHelper h, ServerPlayer p, int index, ItemStack expected) {
        var b = before(p);
        check(h, WeaponEquipmentService.equip(p, index, expected) != null, "Invalid/stale equip rejected");
        unchanged(h, p, b);
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 40)
    public void storageSwapKeepsExactReferencesFiniteAmmoOverflowRollsAndComponents(GameTestHelper h) {
        var p = player(h);
        var old = item("mindbender_s_ambition_adept", 2, 6, 500);
        var incoming = item("first_in_last_out", 1, 2, 400);
        check(h, WeaponPerks.select(old) && WeaponPerks.select(incoming), "Real pinned socket rolls selected");
        old.set(DataComponents.CUSTOM_NAME, Component.literal("owned old"));
        incoming.set(DataComponents.CUSTOM_NAME, Component.literal("owned incoming"));
        var sentinel = new ItemStack(Items.DIAMOND, 7);
        p.getInventory().setItem(1, old);
        p.getInventory().setItem(35, incoming);
        p.getInventory().setItem(12, sentinel);
        p.getInventory().setSelectedSlot(1);
        WeaponHandling.update(p);
        var b = before(p);
        long total = ammo(old).total() + ammo(incoming).total();
        check(h, WeaponEquipmentService.equip(p, 35, incoming) == null, "Storage index35 accepted");
        check(h, p.getInventory().getItem(1) == incoming && p.getInventory().getItem(35) == old,
                "Only the two original objects swap");
        check(h, ItemStack.matches(old, b.contents().get(1)) && ItemStack.matches(incoming, b.contents().get(35)),
                "All item components, saved ammunition, overflow and selected rolls survive");
        for (int i = 0; i < b.references().size(); i++) if (i != 1 && i != 35)
            check(h, p.getInventory().getItem(i) == b.references().get(i)
                    && ItemStack.matches(p.getInventory().getItem(i), b.contents().get(i)), "Unrelated slot preserved " + i);
        check(h, ammo(old).total() + ammo(incoming).total() == total
                && ammo(old).overflow() > 0 && ammo(incoming).overflow() > 0, "Finite ammo and overflow conserved");
        check(h, WeaponLoadout.enabled(p) && p.getInventory().getSelectedSlot() == 1 && p.getMainHandItem() == incoming,
                "Loadout enabled and target category held");
        check(h, WeaponHandling.remaining(p) == WeaponHandlingProfile.of(WeaponItems.entry(old).orElseThrow()).stowTicks()
                + WeaponHandlingProfile.of(WeaponItems.entry(incoming).orElseThrow()).readyTicks(),
                "Inventory replacement uses existing Handling clock");
        check(h, TestPlayers.outbound(p).stream().anyMatch(packet -> packet instanceof ClientboundSetHeldSlotPacket),
                "Actual held-selection packet sent");
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 40)
    public void aceAtStorageNineDisplacesOwnedKineticWithoutLosingItsAmmo(GameTestHelper h) {
        var p = player(h);
        var old = item("austringer", 7, 0, 11);
        var ace = item("ace_of_spades", 4, 0, 3);
        p.getInventory().setItem(0, old);
        p.getInventory().setItem(9, ace);
        p.getInventory().setSelectedSlot(0);
        var oldBefore = old.copy();
        var aceBefore = ace.copy();
        check(h, WeaponEquipmentService.equip(p, 9, ace) == null, "Owned Ace from index9 accepted");
        check(h, p.getMainHandItem() == ace && p.getInventory().getItem(9) == old
                && p.getInventory().getItem(0) == ace, "Ace/original references preserved");
        check(h, ItemStack.matches(old, oldBefore) && ItemStack.matches(ace, aceBefore)
                && ammo(old).rounds() == 7 && ammo(ace).rounds() == 4, "Original and exotic ammo/components retained");
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 40)
    public void previewStaleEqualCopyCountTwoAndOutOfRangeArePureRejections(GameTestHelper h) {
        var p = player(h);
        var old = item("austringer", 4, 0, 0);
        p.getInventory().setItem(0, old);
        p.getInventory().setSelectedSlot(0);
        WeaponRuntime.tickPlayer(p);
        check(h, WeaponRuntime.reload(p), "Rejection fixture has a real pending reload");
        for (boolean enabled : List.of(false, true)) {
            p.setAttached(WeaponLoadout.ENABLED, enabled);
            var preview = WeaponModels.create(WeaponCatalog.find("austringer").orElseThrow());
            p.getInventory().setItem(9, preview);
            rejected(h, p, 9, preview);
            var live = item("duke_mk_44", 3, 0, 0);
            p.getInventory().setItem(9, live);
            rejected(h, p, 9, live.copy()); // Equal components cannot act as the click token.
            var stale = live;
            p.getInventory().setItem(9, live.copy());
            rejected(h, p, 9, stale); // Slot changed after the UI captured its Owned record.
            var doubled = item("duke_mk_44", 2, 0, 0);
            doubled.setCount(2);
            p.getInventory().setItem(9, doubled);
            rejected(h, p, 9, doubled);
            rejected(h, p, -1, old);
            rejected(h, p, 36, old);
            rejected(h, p, 9, null);
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 40)
    public void invalidDestinationAndWrongEquipmentBucketCannotBeOverwrittenOrStolen(GameTestHelper h) {
        var p = player(h);
        var candidate = item("beloved", 2, 5, 6);
        p.getInventory().setItem(9, candidate);
        for (var target : List.of(new ItemStack(Items.DIAMOND),
                WeaponModels.create(WeaponCatalog.find("beloved").orElseThrow()), item("austringer", 3, 0, 0))) {
            p.getInventory().setItem(1, target);
            rejected(h, p, 9, candidate);
        }
        var doubled = item("beloved", 1, 2, 3);
        doubled.setCount(2);
        p.getInventory().setItem(1, doubled);
        rejected(h, p, 9, candidate);
        for (int wrong : List.of(0, 2)) {
            p.getInventory().setItem(wrong, candidate);
            p.getInventory().setItem(1, ItemStack.EMPTY);
            rejected(h, p, wrong, candidate); // Even an empty target cannot steal another bucket.
            p.getInventory().setItem(1, item("beloved", 1, 3, 0));
            rejected(h, p, wrong, candidate);
            p.getInventory().setItem(wrong, ItemStack.EMPTY);
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 40)
    public void ownedProjectionUsesOnlyCountOneLiveMainInventoryAndNeverObservesRuntime(GameTestHelper h) {
        var p = player(h);
        var equipped = item("austringer", 3, 0, 0);
        var misplaced = item("duke_mk_44", 2, 0, 0);
        var stored = item("austringer", 1, 0, 0);
        var legacy = stored.get(DataComponents.CUSTOM_DATA).copyTag();
        legacy.putLong(WeaponItems.ROUNDS, 1234);
        legacy.putLong(WeaponItems.RESERVE, 2345);
        legacy.putLong(WeaponItems.OVERFLOW, 3456);
        stored.set(DataComponents.CUSTOM_DATA, CustomData.of(legacy));
        p.getInventory().setItem(0, equipped);
        p.getInventory().setItem(1, misplaced);
        p.getInventory().setItem(8, item("duke_mk_44", 2, 0, 0));
        p.getInventory().setItem(9, WeaponModels.create(WeaponCatalog.find("austringer").orElseThrow()));
        var doubled = item("austringer", 1, 0, 0);
        doubled.setCount(2);
        p.getInventory().setItem(10, doubled);
        p.getInventory().setItem(11, item("beloved", 2, 4, 0));
        p.getInventory().setItem(35, stored);
        var offhand = item("austringer", 1, 0, 0);
        var helmet = item("austringer", 1, 0, 0);
        p.setItemSlot(EquipmentSlot.OFFHAND, offhand);
        p.setItemSlot(EquipmentSlot.HEAD, helmet);
        p.setAttached(WeaponLoadout.ENABLED, false);
        var b = before(p);
        check(h, b.readiness().isEmpty(), "No prior Handling observation");
        for (int i = 0; i < 3; i++) {
            var rows = WeaponEquipmentService.owned(p, WeaponSlot.KINETIC);
            check(h, rows.stream().map(WeaponEquipmentService.Owned::inventoryIndex).toList().equals(List.of(0, 1, 8, 35)),
                    "Actual main indices in ascending order; previews/count2/equipment excluded");
            check(h, rows.getFirst().equipped() && rows.stream().skip(1).noneMatch(WeaponEquipmentService.Owned::equipped),
                    "Equipped means matching category index, independently of attachment");
            for (var row : rows) check(h, row.stack() == p.getInventory().getItem(row.inventoryIndex())
                    && row.weapon().equals(WeaponItems.entry(row.stack()).orElseThrow()), "Projection retains exact click token and catalog entry");
            var energy = WeaponEquipmentService.owned(p, WeaponSlot.ENERGY);
            check(h, energy.size() == 1 && energy.getFirst().inventoryIndex() == 11 && !energy.getFirst().equipped(),
                    "Category filter follows characteristics, not ammo class or misplaced slot");
            check(h, WeaponEquipmentService.owned(p, WeaponSlot.POWER).isEmpty(), "No fabricated empty choices");
        }
        unchanged(h, p, b);
        check(h, p.getItemBySlot(EquipmentSlot.OFFHAND) == offhand && p.getItemBySlot(EquipmentSlot.HEAD) == helmet,
                "Non-main equipment untouched");
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 40)
    public void sameSlotNoOpEnablesLoadoutWithoutResettingCooldownOrCancellingReload(GameTestHelper h) {
        var p = player(h);
        var gun = item("austringer", 5, 0, 0);
        p.getInventory().setItem(0, gun);
        p.getInventory().setSelectedSlot(0);
        WeaponRuntime.tickPlayer(p);
        check(h, WeaponRuntime.beginUse(p) && ammo(gun).rounds() == 4, "Actual paid shot establishes firing cooldown");
        var afterShot = gun.copy();
        check(h, !WeaponLoadout.enabled(p) && WeaponEquipmentService.equip(p, 0, gun) == null && WeaponLoadout.enabled(p),
                "Valid current equipment safely opts into real loadout");
        // beginUse accepts an already-held logical use without attempting another shot.
        // Observe paid ammo, then remove that duplicate-input guard with a real release.
        WeaponRuntime.beginUse(p);
        check(h, ammo(gun).rounds() == 4 && ItemStack.matches(gun, afterShot), "No-op duplicate use cannot spend another round");
        WeaponRuntime.releaseUse(p, gun);
        WeaponRuntime.beginUse(p);
        check(h, ammo(gun).rounds() == 4 && ItemStack.matches(gun, afterShot),
                "Fresh press after no-op cannot bypass the paid shot cooldown in the same tick");
        check(h, WeaponRuntime.reload(p), "Pending reload fixture accepted");
        var b = before(p);
        check(h, WeaponEquipmentService.equip(p, 0, gun) == null, "Repeated no-op succeeds");
        unchanged(h, p, b);
        check(h, WeaponRuntime.reloading(p), "No-op retains pending work as well as cooldown");
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 40)
    public void stowedCurrentEquipmentSelectsCategoryAndHeldSourceDoesNotInventASwap(GameTestHelper h) {
        var p = player(h);
        var gun = item("austringer", 5, 0, 0);
        p.getInventory().setItem(4, gun);
        p.getInventory().setSelectedSlot(4);
        WeaponRuntime.tickPlayer(p);
        check(h, WeaponRuntime.beginUse(p), "Held storage weapon already has a real cooldown");
        var afterShot = gun.copy();
        check(h, WeaponEquipmentService.equip(p, 4, gun) == null && p.getInventory().getItem(4).isEmpty()
                && p.getMainHandItem() == gun && p.getInventory().getSelectedSlot() == 0, "Held source moves into category target");
        check(h, WeaponHandling.remaining(p) == 0 && !WeaponRuntime.beginUse(p) && ItemStack.matches(gun, afterShot),
                "Moving same held identity neither fabricates Handling nor clears RPM");
        var energy = item("nezarec_s_whisper", 2, 5, 0);
        p.getInventory().setItem(1, energy);
        TestPlayers.drain(p);
        check(h, WeaponEquipmentService.equip(p, 1, energy) == null && p.getMainHandItem() == energy
                && p.getInventory().getItem(0) == gun, "Already equipped but stowed category is selected");
        check(h, TestPlayers.outbound(p).stream().anyMatch(packet -> packet instanceof ClientboundSetHeldSlotPacket),
                "Client receives canonical category selection");
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 40)
    public void unavailablePlayersAndConcurrentCallerCannotChangeOwnershipOrEnabledState(GameTestHelper h) {
        for (boolean enabled : List.of(false, true)) {
            var p = player(h);
            var gun = item("austringer", 3, 0, 0);
            p.getInventory().setItem(9, gun);
            p.setAttached(WeaponLoadout.ENABLED, enabled);
            var b = before(p);
            String async = CompletableFuture.supplyAsync(() -> WeaponEquipmentService.equip(p, 9, gun)).join();
            check(h, async != null, "Off-thread caller rejected before touching inventory or runtime");
            unchanged(h, p, b);
            p.setGameMode(GameType.SPECTATOR);
            rejected(h, p, 9, gun);
            p.setGameMode(GameType.SURVIVAL);
            p.setHealth(0);
            rejected(h, p, 9, gun);
            p.setHealth(20);
            AbilityService.startSuper(p, new SuperSession() {
                public boolean tick() { return true; }
                public void primary() {}
                public void end() {}
                public float remaining() { return 1; }
            });
            rejected(h, p, 9, gun);
            AbilityService.endSuper(p);
            p.setRemoved(Entity.RemovalReason.DISCARDED);
            rejected(h, p, 9, gun);
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 40)
    public void exoticReplacementAndMisfiledSecondExoticPreserveOwnershipAndAttachments(GameTestHelper h) {
        var p = player(h);
        var ace = item("ace_of_spades", 4, 0, 0);
        var izanagi = item("izanagis_burden", 2, 8, 0);
        p.getInventory().setItem(0, ace);
        p.getInventory().setItem(1, izanagi);
        for (boolean enabled : List.of(false, true)) {
            p.setAttached(WeaponLoadout.ENABLED, enabled);
            rejected(h, p, 1, izanagi); // Cannot steal the wrong equipment category for a second exotic.
        }
        p.getInventory().setItem(1, ItemStack.EMPTY);
        p.getInventory().setItem(9, izanagi);
        check(h, WeaponEquipmentService.equip(p, 9, izanagi) == null && p.getInventory().getItem(0) == izanagi
                && p.getInventory().getItem(9) == ace, "Replacing an exotic in its own category is legal, stored exotic is not equipped");
        var energy = item("nezarec_s_whisper", 2, 5, 0);
        p.getInventory().setItem(10, energy);
        check(h, WeaponEquipmentService.equip(p, 10, energy) == null, "Stored second exotic cannot block other equipment");
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 40)
    public void distinctCategoryExoticsRejectBeforeMutationWhenCatalogProvidesSuchAPair(GameTestHelper h) {
        var exotics = WeaponCatalog.all().stream().filter(e -> WeaponCharacteristics.of(e).exotic()).toList();
        check(h, !exotics.isEmpty(), "Actual exotic catalog loaded");
        for (var first : exotics) for (var second : exotics) {
            if (WeaponCharacteristics.of(first).slot() == WeaponCharacteristics.of(second).slot()) continue;
            for (boolean enabled : List.of(false, true)) {
                var p = player(h);
                var current = WeaponItems.create(first);
                var candidate = WeaponItems.create(second);
                p.getInventory().setItem(WeaponCharacteristics.of(first).slot().hotbar(), current);
                p.getInventory().setItem(9, candidate);
                p.setAttached(WeaponLoadout.ENABLED, enabled);
                rejected(h, p, 9, candidate);
            }
        }
        // Current pinned catalog has Ace and Izanagi, both KINETIC. No distinct-category
        // pair exists: the conflict branch above is prepared, not exercised by these data.
        // Do not forge metadata or mutate global production catalogs to claim coverage.
        h.succeed();
    }
}
