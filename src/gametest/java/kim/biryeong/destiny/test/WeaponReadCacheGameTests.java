package kim.biryeong.destiny.test;

import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;

public final class WeaponReadCacheGameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=40)
    public void warmSelectionStillValidatesCurrentItemModelAndLiveComponent(GameTestHelper h) {
        var roll = WeaponPerks.rolls().getFirst();
        var entry = WeaponCatalog.find(roll.id()).orElseThrow();
        var stack = WeaponItems.create(entry);
        check(h, WeaponPerks.select(stack), "Select a real pinned trait");
        var selected = WeaponPerks.selected(stack).orElseThrow();
        var custom = stack.get(DataComponents.CUSTOM_DATA);
        var model = stack.get(DataComponents.ITEM_MODEL);
        for (int i = 0; i < 100; i++) check(h, WeaponPerks.selected(stack).filter(selected::equals).isPresent(), "Warm selection");
        stack.set(DataComponents.ITEM_MODEL, Identifier.withDefaultNamespace("paper"));
        check(h, WeaponItems.entry(stack).isEmpty() && WeaponModels.entry(stack).isEmpty()
                && WeaponPerks.selected(stack).isEmpty(), "A changed model cannot reuse a valid cached result");
        stack.set(DataComponents.ITEM_MODEL, model);
        check(h, WeaponPerks.selected(stack).filter(selected::equals).isPresent(), "Restored unchanged component remains valid");
        var forged = stack.transmuteCopy(Items.PAPER);
        check(h, WeaponItems.entry(forged).isEmpty() && WeaponModels.entry(forged).isEmpty()
                && WeaponPerks.selected(forged).isEmpty(), "Shared cached component on paper never grants a weapon or trait");
        var tag = custom.copyTag(); tag.putBoolean(WeaponItems.LIVE, false);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        check(h, WeaponItems.entry(stack).isEmpty() && WeaponPerks.selected(stack).isEmpty(), "Live marker edit is immediate");
        stack.set(DataComponents.CUSTOM_DATA, custom);
        check(h, WeaponPerks.selected(stack).filter(selected::equals).isPresent(), "Restored immutable component revalidates");
        stack.remove(DataComponents.CUSTOM_DATA);
        check(h, WeaponItems.entry(stack).isEmpty() && WeaponPerks.selected(stack).isEmpty(), "Removal is immediate");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=40)
    public void perkAndAmmoWritesInvalidateImmediatelyWithoutSharingMutableProjection(GameTestHelper h) {
        var roll = WeaponPerks.rolls().getFirst();
        var stack = WeaponItems.create(WeaponCatalog.find(roll.id()).orElseThrow());
        var profile = WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow());
        check(h, WeaponPerks.select(stack) && WeaponPerks.selected(stack).isPresent(), "Selected before clear");
        check(h, WeaponPerks.clear(stack) && WeaponPerks.selected(stack).isEmpty(), "Clear invalidates warmed selection");
        check(h, WeaponPerks.select(stack) && WeaponPerks.selected(stack).isPresent(), "Reselect is immediately visible");
        var first = WeaponItems.magazine(stack, profile);
        var before = first.rounds();
        check(h, first.consume(), "Consume only local projection");
        check(h, WeaponItems.magazine(stack, profile).rounds() == before, "Reads do not share mutable magazines");
        WeaponItems.save(stack, first);
        check(h, WeaponItems.magazine(stack, profile).rounds() == before - 1, "Saved ammo invalidates read snapshot");
        var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putDouble(WeaponItems.ROUNDS, Double.NaN);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        check(h, WeaponItems.magazine(stack, profile).rounds() == 0, "Malformed nonintegral ammo cannot survive cache invalidation");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=40)
    public void malformedModernSocketBlocksLegacyAndMissingSocketPreservesFallback(GameTestHelper h) {
        var roll = WeaponPerks.rolls().getFirst();
        var stack = WeaponItems.create(WeaponCatalog.find(roll.id()).orElseThrow());
        var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putInt(WeaponPerks.SOCKET_KEY, roll.socket()); tag.putLong(WeaponPerks.HASH_KEY, roll.perkHash());
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        check(h, WeaponPerks.selected(stack).isPresent(), "Exact legacy Int/Long pair remains supported");
        var sockets = new CompoundTag(); sockets.putString(Integer.toString(roll.socket()), Long.toString(roll.perkHash()));
        tag.put(WeaponPerks.SLOTS_KEY, sockets);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        check(h, WeaponPerks.selected(stack).isEmpty(), "Explicit malformed modern socket overrides legacy pair");
        tag.put(WeaponPerks.SLOTS_KEY, new CompoundTag());
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        check(h, WeaponPerks.selected(stack).isPresent(), "Absent modern socket retains exact legacy fallback");
        tag.putString(WeaponPerks.SLOTS_KEY, "bad");
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        check(h, WeaponPerks.selected(stack).isEmpty(), "Malformed modern container blocks all fallback");
        h.succeed();
    }
}
