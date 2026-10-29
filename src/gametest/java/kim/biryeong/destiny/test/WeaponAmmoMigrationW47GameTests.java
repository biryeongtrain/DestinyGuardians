package kim.biryeong.destiny.test;

import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.phys.Vec3;
import java.util.List;

/** Register this NEW class in the main task; this sidecar does not edit entrypoints. */
public final class WeaponAmmoMigrationW47GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), -90, 0);
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); CombatHud.remove(p); TestPlayers.remove(p); });
        return p;
    }
    private static WeaponProfile profile(ItemStack s) {
        return WeaponProfile.forEntry(WeaponItems.entry(s).orElseThrow());
    }
    private static WeaponMagazine ammo(ItemStack s) { return WeaponItems.magazine(s, profile(s)); }
    private static ItemStack legacy(String id, int rounds, int reserve) {
        var s = WeaponItems.create(WeaponCatalog.find(id).orElseThrow());
        var tag = s.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putInt(WeaponItems.ROUNDS, rounds); tag.putInt(WeaponItems.RESERVE, reserve);
        tag.remove(WeaponItems.OVERFLOW);
        s.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        return s;
    }

    @GameTest(structure="destiny-test:floor", maxTicks=30, environment = "destiny-test:w90_isolated")
    public void all63LegacyHudReadsAreConservativeWithoutSavingMigration(GameTestHelper h) {
        var p = player(h);
        for (var entry : WeaponCatalog.all()) {
            var f = WeaponProfile.forEntry(entry);
            var stack = legacy(entry.id(), f.magazine() + 7, f.infiniteReserve() ? Integer.MAX_VALUE : f.reserve());
            p.setItemInHand(InteractionHand.MAIN_HAND, stack);
            var before = stack.copy();
            long expected = (long) f.magazine() + 7 + (f.infiniteReserve() ? 0 : f.reserve());
            for (int i = 0; i < 3; i++) {
                var projected = ammo(stack);
                check(h, projected.total() == expected && projected.overflow() == 7, "All excess retained: " + entry.id());
                var state = AmmoHud.current(p).orElseThrow();
                check(h, state.rounds() == f.magazine() && state.reserve() == (f.infiniteReserve() ? 0 : f.reserve()), "Bounded read-only HUD projection: " + entry.id());
                CombatHud.update(p);
                check(h, ItemStack.matches(before, stack), "HUD/get never writes/migrates ammo or components: " + entry.id());
            }
            check(h, !stack.get(DataComponents.CUSTOM_DATA).copyTag().contains(WeaponItems.OVERFLOW), "Migration deferred to mutation boundary");
        }
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=25, environment = "destiny-test:w90_isolated")
    public void fullReserveMigrationAndRepeatedSavesPreserveAllIdentityComponents(GameTestHelper h) {
        var e = WeaponCatalog.find("bite_of_the_fox").orElseThrow();
        var f = WeaponProfile.forEntry(e);
        var stack = legacy(e.id(), f.magazine() + 9, f.reserve());
        stack.set(DataComponents.CUSTOM_NAME, Component.literal("W47 owner-kept name"));
        stack.set(DataComponents.LORE, new ItemLore(List.of(Component.literal("User lore, do not replace"), Component.literal("Second user line"))));
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(.25f, .75f),
                List.of(true, false), List.of("hip", "unrelated selector"), List.of(0x123456, 0xABCDEF)));
        var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putString("w47_owner", "original");
        tag.putLong("unrelated_long", Long.MAX_VALUE);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        var before = stack.copy();
        long total = (long) f.magazine() + 9 + f.reserve();
        for (int i = 0; i < 10; i++) {
            WeaponItems.save(stack, ammo(stack));
            check(h, ammo(stack).total() == total && ammo(stack).overflow() == 9, "Repeated save cannot re-add excess");
            var expected = before.copy();
            expected.set(DataComponents.CUSTOM_DATA, stack.get(DataComponents.CUSTOM_DATA));
            check(h, ItemStack.matches(expected, stack), "Only ammo custom-data changes, no lore/model/grip/pose/name loss");
            var actual = stack.get(DataComponents.CUSTOM_DATA).copyTag();
            check(h, actual.getLongOr(WeaponItems.OVERFLOW, -1) == 9, "Explicit serialized long overflow");
            for (var key : List.of(WeaponItems.ROUNDS, WeaponItems.RESERVE, WeaponItems.OVERFLOW)) actual.remove(key);
            var original = before.get(DataComponents.CUSTOM_DATA).copyTag();
            for (var key : List.of(WeaponItems.ROUNDS, WeaponItems.RESERVE, WeaponItems.OVERFLOW)) original.remove(key);
            check(h, original.equals(actual) && WeaponItems.entry(stack).orElseThrow().equals(e), "Unrelated NBT and combat identity retained");
        }
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=30, environment = "destiny-test:w90_isolated")
    public void overflowRoundTripsRealRegistryNbtAndJsonWithoutPrecisionLoss(GameTestHelper h) {
        var stack = legacy("bite_of_the_fox", Integer.MAX_VALUE, Integer.MAX_VALUE);
        WeaponItems.save(stack, ammo(stack));
        var nbtOps = h.getLevel().registryAccess().createSerializationContext(NbtOps.INSTANCE);
        var jsonOps = h.getLevel().registryAccess().createSerializationContext(com.mojang.serialization.JsonOps.INSTANCE);
        for (int i = 0; i < 4; i++) {
            stack = ItemStack.CODEC.parse(nbtOps, ItemStack.CODEC.encodeStart(nbtOps, stack).getOrThrow()).getOrThrow();
            stack = ItemStack.CODEC.parse(jsonOps, ItemStack.CODEC.encodeStart(jsonOps, stack).getOrThrow()).getOrThrow();
            check(h, ammo(stack).total() == 2L * Integer.MAX_VALUE, "Full legacy int pair survives actual item codecs");
            WeaponItems.save(stack, ammo(stack));
        }
        var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putLong(WeaponItems.OVERFLOW, Long.MAX_VALUE);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        WeaponItems.save(stack, ammo(stack));
        check(h, ammo(stack).total() == Long.MAX_VALUE, "Deliberately saturated representable long total");
        var decoded = ItemStack.CODEC.parse(nbtOps, ItemStack.CODEC.encodeStart(nbtOps, stack).getOrThrow()).getOrThrow();
        check(h, ammo(decoded).total() == Long.MAX_VALUE, "Long ceiling remains exact after binary NBT codec");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=30, environment = "destiny-test:w90_isolated")
    public void actualShotMigratesOnceAndSpendsExactlyOneWithFullReserves(GameTestHelper h) {
        var p = player(h);
        var e = WeaponCatalog.find("bite_of_the_fox").orElseThrow();
        var f = WeaponProfile.forEntry(e);
        var stack = legacy(e.id(), f.magazine() + 8, f.reserve());
        p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        long total = ammo(stack).total();
        check(h, WeaponRuntime.beginUse(p), "Real runtime fires legacy stack");
        check(h, ammo(stack).total() == total - 1, "Only one shot reduces finite total");
        check(h, ammo(stack).rounds() == f.magazine() - 1 && ammo(stack).overflow() == 8, "Overflow not silently loaded or deleted");
        check(h, stack.get(DataComponents.CUSTOM_DATA).copyTag().getLongOr(WeaponItems.OVERFLOW, -1) == 8, "Mutation persisted migration");
        var before = stack.copy();
        CombatHud.update(p); AmmoHud.current(p);
        check(h, ItemStack.matches(before, stack), "Subsequent HUD remains read-only");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=180, environment = "destiny-test:w90_isolated")
    public void reloadSwapCancellationDoesNotSpendOverflowOrCompleteLater(GameTestHelper h) {
        var p = player(h);
        var stack = legacy("bite_of_the_fox", 0, 100);
        p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        var original = stack.copy();
        check(h, WeaponRuntime.reload(p), "Finite reload starts from saved excess reserve");
        check(h, ammo(stack).total() == 100 && ammo(stack).rounds() == 0, "Pending reload transfers nothing");
        // Presentation can change model floats, but may not migrate/persist ammo just for starting a timer.
        check(h, original.get(DataComponents.CUSTOM_DATA).equals(stack.get(DataComponents.CUSTOM_DATA)), "Starting reload does not save normalized ammo");
        p.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        WeaponRuntime.tickPlayer(p);
        h.runAfterDelay(profile(stack).reloadTicks() + 3, () -> {
            p.setItemInHand(InteractionHand.MAIN_HAND, stack);
            WeaponRuntime.tickPlayer(p);
            check(h, !WeaponRuntime.reloading(p) && ammo(stack).rounds() == 0 && ammo(stack).total() == 100, "Stale cancelled reload cannot transfer or duplicate ammo");
            WeaponItems.save(stack, ammo(stack));
            check(h, ammo(stack).total() == 100, "Later explicit mutation preserves all legacy reserves");
            h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor", maxTicks=25, environment = "destiny-test:w90_isolated")
    public void primaryAndMalformedAmmoNeverInventFiniteReserveOrRefill(GameTestHelper h) {
        var primary = legacy("duke_mk_44", 14, Integer.MAX_VALUE);
        var f = profile(primary);
        long total = ammo(primary).total();
        check(h, ammo(primary).reserve() == 0 && total == 14, "Primary sentinel ignored, actual loaded excess retained");
        WeaponItems.save(primary, ammo(primary));
        check(h, primary.get(DataComponents.CUSTOM_DATA).copyTag().getIntOr(WeaponItems.RESERVE, -1) == 0, "Primary serializes zero, not MAX reserve");
        check(h, ammo(primary).rounds() == f.magazine() && ammo(primary).total() == total, "Save cannot grant or destroy primary loaded excess");
        var broken = legacy("bite_of_the_fox", 0, 0);
        var tag = broken.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putDouble(WeaponItems.ROUNDS, Double.NaN);
        tag.putString(WeaponItems.RESERVE, "2147483647");
        tag.putLong(WeaponItems.OVERFLOW, -5);
        broken.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        check(h, ammo(broken).total() == 0 && !ammo(broken).canReload(), "Malformed numbers cannot grant ammo");
        var before = broken.copy(); ammo(broken);
        check(h, ItemStack.matches(before, broken), "Malformed read is also side-effect-free");
        WeaponItems.save(broken, ammo(broken));
        check(h, ammo(broken).total() == 0, "Mutation canonicalizes corrupt data without refilling");
        h.succeed();
    }
}
