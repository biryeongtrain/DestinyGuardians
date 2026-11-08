package kim.biryeong.destiny.test;

import kim.biryeong.destiny.inventory.WeaponPerkSelection;
import kim.biryeong.destiny.inventory.WeaponTestArmory;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;

import static kim.biryeong.destiny.inventory.WeaponPerkSelection.Group.DAMAGE;
import static kim.biryeong.destiny.inventory.WeaponPerkSelection.Group.UTILITY;

/** New armory ownership and paired socket transactions only; no individual perk balance matrix. */
public final class WeaponArmoryW228GameTests {
    private static final String FLOOR = "destiny-test:floor", ENV = "destiny-test:w90_isolated";
    private static final String PROPERTY = "destiny.testArmory";

    private static void check(GameTestHelper h, boolean ok, String why) {
        h.assertTrue(ok, Component.literal(why));
    }

    private static void restoreProperty(String value) {
        if (value == null) System.clearProperty(PROPERTY); else System.setProperty(PROPERTY, value);
    }

    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2, 1, 6), 0, -85);
        p.setNoGravity(true);
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); TestPlayers.remove(p); });
        return p;
    }

    private static ItemStack item(String id) {
        var entry = WeaponCatalog.find(id).orElseThrow();
        var stack = WeaponItems.create(entry);
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry), 1, 2, 123));
        stack.set(DataComponents.CUSTOM_NAME, Component.literal("W228 owned sentinel"));
        var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putString("w228_unrelated", "preserve");
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        return stack;
    }

    private record Before(List<ItemStack> references, List<ItemStack> contents, int selected,
                          boolean enabled, Optional<WeaponHandling.Readiness> readiness, boolean reloading) {}

    private static Before before(ServerPlayer p) {
        var references = new ArrayList<ItemStack>();
        var contents = new ArrayList<ItemStack>();
        for (int i = 0; i < p.getInventory().getContainerSize(); i++) {
            var stack = p.getInventory().getItem(i);
            references.add(stack); contents.add(stack.copy());
        }
        TestPlayers.drain(p);
        return new Before(references, contents, p.getInventory().getSelectedSlot(), WeaponLoadout.enabled(p),
                WeaponHandling.readiness(p), WeaponRuntime.reloading(p));
    }

    private static void unchanged(GameTestHelper h, ServerPlayer p, Before b) {
        for (int i = 0; i < b.references().size(); i++)
            check(h, p.getInventory().getItem(i) == b.references().get(i)
                    && ItemStack.matches(p.getInventory().getItem(i), b.contents().get(i)), "Unchanged inventory " + i);
        check(h, p.getInventory().getSelectedSlot() == b.selected() && WeaponLoadout.enabled(p) == b.enabled()
                && WeaponHandling.readiness(p).equals(b.readiness()) && WeaponRuntime.reloading(p) == b.reloading(),
                "Rejection/no-op preserves selection, attachment and pending lifecycle");
        check(h, TestPlayers.outbound(p).isEmpty(), "Rejection/no-op sends no equipment packets");
    }

    private static void nonPerkComponentsUnchanged(GameTestHelper h, ItemStack stack, ItemStack saved) {
        var actual = stack.copy();
        var original = saved.copy();
        for (var copy : List.of(actual, original)) {
            var tag = copy.get(DataComponents.CUSTOM_DATA).copyTag();
            tag.remove(WeaponPerks.HASH_KEY); tag.remove(WeaponPerks.SOCKET_KEY); tag.remove(WeaponPerks.SLOTS_KEY);
            copy.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        }
        check(h, ItemStack.matches(actual, original), "All ammunition NBT, name, lore and unrelated components survive edits");
    }

    public void w228PropertyDefaultsOnFalseRejectsAndCatalogIsExactSorted65(GameTestHelper h) {
        String previous = System.getProperty(PROPERTY);
        var p = player(h);
        try {
            System.clearProperty(PROPERTY);
            check(h, WeaponTestArmory.enabled(), "Test stage defaults on");
            var b = before(p);
            var ids = new HashSet<String>();
            for (var slot : WeaponSlot.values()) {
                var rows = WeaponTestArmory.catalog(slot);
                var names = rows.stream().map(WeaponCatalog.Entry::id).toList();
                check(h, names.equals(names.stream().sorted().toList()), "Catalog order is explicitly by ID");
                for (var entry : rows) check(h, WeaponCharacteristics.of(entry).slot() == slot && ids.add(entry.id()),
                        "Each exact catalog tuple belongs to one actual category");
            }
            check(h, ids.size() == 65 && ids.equals(new HashSet<>(WeaponCatalog.all().stream().map(WeaponCatalog.Entry::id).toList())),
                    "All 65 real weapons offered exactly once without minting");
            System.setProperty(PROPERTY, "false");
            check(h, !WeaponTestArmory.enabled() && WeaponTestArmory.prepare(p) != null
                    && WeaponTestArmory.equip(p, "austringer") != null
                    && WeaponTestArmory.add(p, "ammit_ar2", "gutshot_straight", "surplus") != null,
                    "False disables prepare, equip and final wizard grant");
            unchanged(h, p, b);
        } finally { restoreProperty(previous); }
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 30)
    public void w228PrepareFillsOnlyEmptyCategoriesWithDefaultsAndKeepsOwnedComponents(GameTestHelper h) {
        var p = player(h);
        check(h, WeaponTestArmory.prepare(p) == null && WeaponLoadout.enabled(p), "Preparation enables real loadout");
        var defaults = List.of("austringer", "ammit_ar2", "bad_omens");
        for (var slot : WeaponSlot.values()) {
            var stack = p.getInventory().getItem(slot.hotbar());
            var entry = WeaponItems.entry(stack).orElseThrow();
            var profile = WeaponProfile.forEntry(entry);
            var ammo = WeaponItems.magazine(stack, profile);
            check(h, entry.id().equals(defaults.get(slot.hotbar())) && WeaponCharacteristics.of(entry).slot() == slot
                    && p.getUUID().toString().equals(stack.get(DataComponents.CUSTOM_DATA).copyTag().getStringOr(WeaponTestArmory.OWNER_KEY, ""))
                    && ammo.rounds() == profile.magazine() && ammo.reserve() == profile.reserve()
                    && WeaponPerks.ids().stream().noneMatch(id -> WeaponPerks.selected(stack, id).isPresent()),
                    "Correct actual default slot, owner, fresh ammo and no chosen perks");
        }
        var owned = item("ammit_ar2");
        check(h, WeaponPerks.select(owned, "surplus"), "Supported owned roll");
        p.getInventory().setItem(1, owned);
        p.getInventory().setItem(2, ItemStack.EMPTY);
        var sentinel = new ItemStack(Items.DIAMOND, 7); p.getInventory().setItem(35, sentinel);
        var saved = owned.copy();
        check(h, WeaponTestArmory.prepare(p) == null && p.getInventory().getItem(1) == owned
                && ItemStack.matches(owned, saved) && p.getInventory().getItem(35) == sentinel,
                "Existing categorized owned weapon and unrelated inventory survive preparation");
        verifyPrepareRejections(h);
        h.succeed();
    }

    private static void verifyPrepareRejections(GameTestHelper h) {
        var p = player(h);
        for (var invalid : List.of(new ItemStack(Items.DIAMOND), item("austringer"),
                WeaponModels.create(WeaponCatalog.find("bad_omens").orElseThrow()))) {
            p.getInventory().setItem(2, invalid);
            var b = before(p);
            check(h, WeaponTestArmory.prepare(p) != null, "Late blocked bucket rejects before filling earlier empty buckets");
            unchanged(h, p, b);
        }
        p.getInventory().setItem(2, ItemStack.EMPTY);
        var b = before(p);
        check(h, CompletableFuture.supplyAsync(() -> WeaponTestArmory.prepare(p)).join() != null
                && CompletableFuture.supplyAsync(() -> WeaponTestArmory.equip(p, "austringer")).join() != null
                && CompletableFuture.supplyAsync(() -> WeaponTestArmory.add(p, "ammit_ar2", "gutshot_straight", "surplus")).join() != null,
                "Off-thread grants rejected");
        check(h, WeaponTestArmory.equip(p, "not_a_weapon") != null, "Unknown exact ID rejected");
        unchanged(h, p, b);
        p.setHealth(0); b = before(p);
        check(h, WeaponTestArmory.add(p, "ammit_ar2", "gutshot_straight", "surplus") != null,
                "Unavailable player cannot finalize a valid pair");
        unchanged(h, p, b);
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 30)
    public void w228FinalAddPreservesNormalDisplacementAndReusesOwnedAmmoWithChosenPair(GameTestHelper h) {
        var p = player(h);
        var normal = item("ammit_ar2");
        check(h, WeaponPerks.select(normal, "gutshot_straight") && WeaponPerks.select(normal, "surplus"),
                "Supported normal weapon pair");
        var saved = normal.copy();
        var sentinel = new ItemStack(Items.DIAMOND, 8);
        p.getInventory().setItem(1, normal); p.getInventory().setItem(35, sentinel);
        check(h, WeaponTestArmory.add(p, "gnawing_hunger", "", "") == null, "Final confirmation mints missing weapon");
        var minted = p.getInventory().getItem(1);
        check(h, p.getInventory().getItem(3) == normal && ItemStack.matches(normal, saved)
                && p.getInventory().getItem(35) == sentinel && p.getMainHandItem() == minted && WeaponLoadout.enabled(p),
                "Normal displaced object preserved before selecting actual target hotbar");
        check(h, WeaponTestArmory.add(p, "ammit_ar2", "one_for_all", "surplus") == null
                && p.getInventory().getItem(1) == normal && p.getMainHandItem() == normal
                && p.getInventory().getItem(3) == minted && WeaponPerks.selected(normal, "one_for_all").isPresent()
                && WeaponPerks.selected(normal, "surplus").isPresent() && WeaponPerks.selected(normal, "gutshot_straight").isEmpty(),
                "Final add reuses exact stored source and applies the requested pair in actual category slot");
        nonPerkComponentsUnchanged(h, normal, saved);
        check(h, WeaponTestArmory.add(p, "ammit_ar2", "", "") == null
                && WeaponPerkSelection.selected(normal, DAMAGE).isEmpty()
                && WeaponPerkSelection.selected(normal, UTILITY).isEmpty(),
                "Final add with none explicitly clears prior owned selections");
        nonPerkComponentsUnchanged(h, normal, saved);
        p.getInventory().setItem(1, ItemStack.EMPTY); p.getInventory().setItem(0, normal);
        var b = before(p);
        check(h, WeaponTestArmory.add(p, "ammit_ar2", "gutshot_straight", "surplus") != null,
                "Misplaced owned weapon cannot mint a duplicate or change chosen rolls");
        unchanged(h, p, b);
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 30)
    public void w228FullInventoryRejectsNormalAndForeignOwnerButDisposesOwnTestWeapon(GameTestHelper h) {
        var p = player(h);
        var normal = item("austringer");
        p.getInventory().setItem(0, normal);
        for (int i = 3; i < 36; i++) p.getInventory().setItem(i, new ItemStack(Items.STONE, 64));
        var b = before(p);
        check(h, WeaponTestArmory.add(p, "ammit_ar2", "gutshot_straight", "tap_the_trigger") != null
                && WeaponTestArmory.add(p, "ammit_ar2", "surplus", "") != null
                && WeaponTestArmory.add(p, "ammit_ar2", "rampage", "surplus") != null
                && WeaponTestArmory.add(p, "ammit_ar2", null, "") != null
                && WeaponTestArmory.add(p, "not_a_weapon", "", "") != null,
                "Invalid pair, category, exact pool, null and weapon ID reject before any actual mutation");
        unchanged(h, p, b);
        check(h, WeaponTestArmory.add(p, "duke_mk_44", "", "") != null,
                "Valid final choice with full inventory rejects before any displacement or grant");
        unchanged(h, p, b);
        var tag = normal.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putString(WeaponTestArmory.OWNER_KEY, java.util.UUID.randomUUID().toString());
        normal.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        b = before(p);
        check(h, WeaponTestArmory.add(p, "duke_mk_44", "", "") != null, "Foreign marked test object remains protected");
        unchanged(h, p, b);
        p.getInventory().setItem(35, ItemStack.EMPTY);
        var saved = normal.copy();
        check(h, WeaponTestArmory.add(p, "duke_mk_44", "", "") == null && p.getInventory().getItem(35) == normal
                && ItemStack.matches(normal, saved), "Foreign object retained intact in last free storage slot");
        var own = p.getInventory().getItem(0); b = before(p);
        check(h, WeaponTestArmory.add(p, "seventh_seraph_officer_revolver", "", "") == null
                && p.getInventory().getItem(0) != own && p.getInventory().getItem(35) == normal,
                "Own marked test weapon can be directly replaced with storage full");
        for (int i = 3; i < 36; i++) check(h, p.getInventory().getItem(i) == b.references().get(i), "No storage changed " + i);
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 30)
    public void w228SameWeaponAndSamePerkAreNoOpsKeepingPendingReload(GameTestHelper h) {
        var p = player(h);
        check(h, WeaponTestArmory.prepare(p) == null, "Default fixture prepared");
        var gun = p.getInventory().getItem(0);
        var entry = WeaponItems.entry(gun).orElseThrow();
        WeaponItems.save(gun, new WeaponMagazine(WeaponProfile.forEntry(entry), 1, 0));
        check(h, WeaponPerkSelection.edit(p, gun, DAMAGE, "rampage") == null, "Supported damage selection");
        p.getInventory().setSelectedSlot(0); WeaponRuntime.tickPlayer(p);
        // prepare() observes the real empty-hand -> weapon transition. Reload is correctly
        // blocked until that Handling deadline; do not reset lifecycle state to bypass it.
        h.runAfterDelay(WeaponHandling.remaining(p), () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, !WeaponHandling.blocked(p), "Preparation's actual ready deadline elapsed");
            check(h, WeaponRuntime.reload(p) && WeaponRuntime.reloading(p), "Actual reload pending after readying");
            var b = before(p);
            check(h, WeaponTestArmory.equip(p, "austringer") == null
                    && WeaponTestArmory.add(p, "austringer", "rampage", "") == null
                    && WeaponPerkSelection.edit(p, gun, DAMAGE, "rampage") == null, "Identical clicks succeed without edits");
            unchanged(h, p, b);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 30)
    public void w228DetachedDraftThenFinalMintAndPairedClearConflictPreserveActualInventory(GameTestHelper h) {
        var p = player(h);
        var owned = item("gnawing_hunger"); p.getInventory().setItem(1, owned);
        var draft = WeaponItems.create(WeaponCatalog.find("ammit_ar2").orElseThrow());
        var b = before(p);
        check(h, WeaponPerkSelection.configure(draft, "gutshot_straight", "surplus") == null,
                "Detached draft accepts an exact compatible pair");
        var draftBefore = draft.copy();
        check(h, WeaponPerkSelection.configure(draft, "gutshot_straight", "tap_the_trigger") != null
                && WeaponPerkSelection.configure(draft, "surplus", "") != null
                && WeaponPerkSelection.configure(draft, "rampage", "surplus") != null
                && ItemStack.matches(draft, draftBefore), "Invalid draft pairs reject atomically");
        check(h, WeaponPerkSelection.options(draft, UTILITY).stream()
                .anyMatch(o -> o.id().equals("tap_the_trigger") && !o.enabled() && !o.reason().isBlank()),
                "Existing options projects detached pair socket incompatibility");
        unchanged(h, p, b);
        check(h, WeaponPerkSelection.configure(draft, "", "") == null
                && WeaponPerkSelection.selected(draft, DAMAGE).isEmpty()
                && WeaponPerkSelection.selected(draft, UTILITY).isEmpty(), "Draft none clears both groups");
        unchanged(h, p, b);
        check(h, WeaponTestArmory.add(p, "ammit_ar2", "gutshot_straight", "surplus") == null,
                "Only final add mints and equips the selected pair");
        var gun = p.getInventory().getItem(1);
        var entry = WeaponItems.entry(gun).orElseThrow();
        var profile = WeaponProfile.forEntry(entry);
        var ammo = WeaponItems.magazine(gun, profile);
        check(h, gun != draft && entry.id().equals("ammit_ar2") && p.getMainHandItem() == gun
                && p.getInventory().getItem(3) == owned && p.getInventory().getItem(0).isEmpty()
                && p.getInventory().getItem(2).isEmpty() && WeaponLoadout.enabled(p)
                && p.getUUID().toString().equals(gun.get(DataComponents.CUSTOM_DATA).copyTag().getStringOr(WeaponTestArmory.OWNER_KEY, ""))
                && WeaponPerks.selected(gun, "gutshot_straight").isPresent() && WeaponPerks.selected(gun, "surplus").isPresent()
                && ammo.rounds() == profile.magazine() && ammo.reserve() == profile.reserve(),
                "Final mint is a distinct real owned item in its exact slot with default ammo and no auto-fill");
        var saved = gun.copy();
        check(h, WeaponPerkSelection.edit(p, gun, DAMAGE, "gutshot_straight") == null
                && WeaponPerkSelection.edit(p, gun, UTILITY, "surplus") == null, "Actual exact sockets 4 and 3 coexist");
        check(h, WeaponPerkSelection.selected(gun, DAMAGE).equals("gutshot_straight")
                && WeaponPerkSelection.selected(gun, UTILITY).equals("surplus"), "One canonical choice per group");
        b = before(p);
        var options = WeaponPerkSelection.options(gun, UTILITY);
        var conflict = options.stream().filter(o -> o.id().equals("tap_the_trigger")).findFirst().orElseThrow();
        check(h, options.getFirst().id().isEmpty() && !conflict.enabled() && !conflict.reason().isBlank()
                && options.stream().skip(1).allMatch(o -> WeaponPerks.choices(gun).contains(o.id())),
                "None first, exact implemented pool only, same-socket pair explicitly disabled with reason");
        check(h, WeaponPerkSelection.edit(p, gun, UTILITY, "tap_the_trigger") != null, "Conflict cannot silently drop damage");
        unchanged(h, p, b);
        check(h, WeaponPerkSelection.edit(p, gun, DAMAGE, "one_for_all") == null
                && WeaponPerks.selected(gun, "gutshot_straight").isEmpty() && WeaponPerks.selected(gun, "surplus").isPresent(),
                "Changing damage replaces only damage");
        check(h, WeaponPerkSelection.edit(p, gun, DAMAGE, "") == null
                && WeaponPerkSelection.selected(gun, DAMAGE).isEmpty() && WeaponPerks.selected(gun, "surplus").isPresent(),
                "Clearing damage preserves utility");
        check(h, WeaponPerkSelection.edit(p, gun, UTILITY, "tap_the_trigger") == null
                && WeaponPerks.selected(gun, "surplus").isEmpty(), "Freed socket now accepts utility, replacing old utility");
        check(h, WeaponPerkSelection.edit(p, gun, UTILITY, "") == null
                && WeaponPerkSelection.selected(gun, UTILITY).isEmpty(), "Utility clear supported");
        nonPerkComponentsUnchanged(h, gun, saved);
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 30)
    public void w228PerkOwnershipRejectsPreviewStaleStorageWrongCategoryCountAndUnsupportedId(GameTestHelper h) {
        var p = player(h); var gun = item("ammit_ar2"); p.getInventory().setItem(1, gun);
        var b = before(p);
        for (var token : List.of(gun.copy(), WeaponModels.create(WeaponCatalog.find("ammit_ar2").orElseThrow())))
            check(h, WeaponPerkSelection.edit(p, token, DAMAGE, "gutshot_straight") != null, "Copy/preview token rejected");
        check(h, WeaponPerkSelection.edit(p, gun, UTILITY, "gutshot_straight") != null
                && WeaponPerkSelection.edit(p, gun, DAMAGE, "rampage") != null
                && WeaponPerkSelection.edit(p, gun, DAMAGE, "unknown") != null
                && CompletableFuture.supplyAsync(() -> WeaponPerkSelection.edit(p, gun, DAMAGE, "gutshot_straight")).join() != null,
                "Wrong group, unsupported exact weapon pool, unknown ID and off-thread edits rejected");
        unchanged(h, p, b);
        p.getInventory().setItem(1, gun.copy()); b = before(p);
        check(h, WeaponPerkSelection.edit(p, gun, DAMAGE, "gutshot_straight") != null, "Stale original rejected");
        unchanged(h, p, b);
        p.getInventory().setItem(1, ItemStack.EMPTY);
        for (int wrong : List.of(0, 9)) {
            p.getInventory().setItem(wrong, gun); b = before(p);
            check(h, WeaponPerkSelection.edit(p, gun, DAMAGE, "gutshot_straight") != null, "Wrong bucket/storage cannot be edited");
            unchanged(h, p, b); p.getInventory().setItem(wrong, ItemStack.EMPTY);
        }
        p.getInventory().setItem(1, gun); gun.setCount(2); b = before(p);
        check(h, WeaponPerkSelection.edit(p, gun, DAMAGE, "gutshot_straight") != null, "Count-two object rejected");
        unchanged(h, p, b);
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 30)
    public void w228ReplacementRejectsUnsupportedExactTuplesAndDuplicateSocketsAtomically(GameTestHelper h) {
        var gun = item("ammit_ar2");
        var damage = WeaponPerks.available(gun, "gutshot_straight").getFirst();
        var utility = WeaponPerks.available(gun, "surplus").getFirst();
        var conflict = WeaponPerks.available(gun, "tap_the_trigger").getFirst();
        check(h, WeaponPerks.replaceSelection(gun, List.of(damage, utility)), "Exact supported pair accepted");
        var saved = gun.copy();
        var invalid = List.of(
                new WeaponPerks.Roll("austringer", damage.hash(), damage.socket(), damage.perkHash(), damage.plugSetHash()),
                new WeaponPerks.Roll(damage.id(), damage.hash() + 1, damage.socket(), damage.perkHash(), damage.plugSetHash()),
                new WeaponPerks.Roll(damage.id(), damage.hash(), 63, damage.perkHash(), damage.plugSetHash()),
                new WeaponPerks.Roll(damage.id(), damage.hash(), damage.socket(), damage.perkHash() + 1, damage.plugSetHash()),
                new WeaponPerks.Roll(damage.id(), damage.hash(), damage.socket(), damage.perkHash(), damage.plugSetHash() + 1));
        for (var bad : invalid) {
            check(h, !WeaponPerks.replaceSelection(gun, List.of(utility, bad)) && ItemStack.matches(gun, saved),
                    "Invalid tuple after a valid roll must reject before clearing/writing");
        }
        check(h, !WeaponPerks.replaceSelection(gun, List.of(damage, damage))
                && !WeaponPerks.replaceSelection(gun, List.of(damage, conflict)) && ItemStack.matches(gun, saved),
                "Duplicate trait or socket rejected atomically");
        check(h, WeaponPerks.replaceSelection(gun, List.of()), "Empty canonical selection clears both");
        nonPerkComponentsUnchanged(h, gun, saved);
        var exotic = item("ace_of_spades"); var intrinsic = exotic.copy();
        check(h, !WeaponPerks.replaceSelection(exotic, List.of(damage)) && ItemStack.matches(exotic, intrinsic),
                "Foreign trait tuple cannot replace exotic intrinsic");
        h.succeed();
    }
}
