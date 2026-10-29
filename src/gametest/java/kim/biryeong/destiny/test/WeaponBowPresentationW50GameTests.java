package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.Set;

/** Server runtime and Polymer wire assertions only; no native-client/rendering evidence. */
public final class WeaponBowPresentationW50GameTests {
    private static final Set<String> BOWS = Set.of("biting_winds", "whispering_slab");
    private static final CustomModelData SENTINEL = new CustomModelData(
            List.of(7.25f, .375f, 47f, 99f), List.of(true, false, true),
            List.of("hip", "w50_keep_string", "w50_keep_extra"), List.of(0x123456, 0xABCDEF));

    private record Bow(ServerPlayer player, ItemStack stack, WeaponCatalog.Entry entry,
                       WeaponProfile profile, Identifier originalModel, boolean[] nocked) {}

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), -90, -15);
        TestCleanup.register(h, () -> {
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            TestPlayers.remove(p);
        });
        return p;
    }

    private static Bow bow(GameTestHelper h, String id) {
        var p = player(h);
        var entry = WeaponCatalog.find(id).orElseThrow();
        var stack = WeaponItems.create(entry);
        stack.set(DataComponents.CUSTOM_MODEL_DATA, SENTINEL);
        p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        return new Bow(p, stack, entry, WeaponProfile.forEntry(entry), stack.get(DataComponents.ITEM_MODEL), new boolean[1]);
    }

    private static long now(Bow b) {
        return b.player.level().getServer().getTickCount();
    }

    private static int rounds(Bow b) {
        return WeaponItems.magazine(b.stack, b.profile).rounds();
    }

    private static void use(GameTestHelper h, Bow b) {
        WeaponCombatItem.INSTANCE.use(h.getLevel(), b.player, InteractionHand.MAIN_HAND);
        check(h, b.player.isUsingItem() && b.player.getUseItem() == b.stack,
                "Real item use owns the native server hold: " + b.entry.id());
    }

    private static void ticks(GameTestHelper h, int until, Bow... bows) {
        for (int i = 1; i <= until; i++) h.runAfterDelay(i, () -> {
            for (var b : bows) {
                WeaponRuntime.tickPlayer(b.player);
                TestPlayers.drain(b.player);
            }
        });
    }

    private static ItemStack wire(ServerPlayer p, ItemStack stack) {
        var context = ((PacketContextProvider) (Object) p.connection).getPacketContext();
        return PolymerItemUtils.getPolymerItemStack(stack, context, p.level().registryAccess());
    }

    private static void preserved(GameTestHelper h, ItemStack stack) {
        preserved(h, stack, SENTINEL.floats().get(1));
    }

    private static void preserved(GameTestHelper h, ItemStack stack, float reloadSelector) {
        var data = stack.get(DataComponents.CUSTOM_MODEL_DATA);
        check(h, data != null && data.floats().size() == 4
                        && data.floats().get(0).equals(SENTINEL.floats().get(0))
                        && data.floats().get(1).equals(reloadSelector)
                        && data.floats().get(3).equals(SENTINEL.floats().get(3))
                        && data.flags().equals(SENTINEL.flags())
                        && data.strings().equals(SENTINEL.strings())
                        && data.colors().equals(SENTINEL.colors()),
                "W50 preserves unrelated components; reload alone owns float1");
    }

    private static void frame(GameTestHelper h, Bow b, int expected) {
        check(h, WeaponBowPresentation.active(b.stack), "Only the live owned bow has presentation authority");
        check(h, Math.floor(b.stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2)) == expected,
                b.entry.id() + " has actual server frame " + expected);
        boolean nocking = expected >= 32;
        float reloadSelector = b.nocked[0] ? -1 : SENTINEL.floats().get(1);
        if (nocking) {
            var ammo = WeaponRuntime.ammunition(b.player).orElseThrow();
            check(h, ammo.reloading() && ammo.rounds() == 0, "Nock route requires an actual empty reload");
            float progress = 1 - ammo.reloadRemaining() / (float) ammo.reloadDuration();
            reloadSelector = (float)Math.floor(progress * 60 + 1e-6f) / 60;
            b.nocked[0] = true;
        }
        check(h, WeaponReloadPresentation.ownedBy(b.player, b.stack) == nocking,
                "Reload authority exists exactly during nock, independently of bow ownership");
        preserved(h, b.stack, reloadSelector);
        var before = b.stack.copy();
        var out = wire(b.player, b.stack);
        var expectedModel = Identifier.parse("destiny:" + (nocking
                ? "weapon_reload_w222_" + b.entry.id() + "/" : "weapon_bow_w50/") + b.entry.id());
        check(h, projected(expectedModel).equals(out.get(DataComponents.ITEM_MODEL)),
                "Owned W222 reload takes precedence during nock; W50 owns draw/loaded/empty");
        var data = out.get(DataComponents.CUSTOM_MODEL_DATA);
        check(h, data.floats().equals(b.stack.get(DataComponents.CUSTOM_MODEL_DATA).floats())
                        && data.strings().equals(SENTINEL.strings()) && data.colors().equals(SENTINEL.colors())
                        && data.flags().equals(List.of(false)),
                "Wire retains selectors and extra data with the existing native-bow grip flag");
        check(h, ItemStack.matches(before, b.stack) && b.originalModel.equals(b.stack.get(DataComponents.ITEM_MODEL)),
                "Polymer reads never mutate the real model or stack");
    }

    private static void unwrapped(GameTestHelper h, ServerPlayer p, ItemStack stack) {
        var before = stack.copy();
        check(h, !WeaponBowPresentation.active(stack), "Saved selectors cannot authorize a bow wrapper");
        check(h, projected(stack, stack.get(DataComponents.ITEM_MODEL)).equals(wire(p, stack).get(DataComponents.ITEM_MODEL)),
                "Unowned bow/preview uses its original wire model");
        check(h, ItemStack.matches(before, stack), "Inactive presentation reads are pure");
    }

    private static void cleared(GameTestHelper h, Bow b) {
        unwrapped(h, b.player, b.stack);
        check(h, b.stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2) == -1,
                "Cancellation invalidates the old selector with -1 immediately");
        check(h, b.originalModel.equals(b.stack.get(DataComponents.ITEM_MODEL)), "Cancellation keeps real model identity");
        preserved(h, b.stack, b.nocked[0] ? -1 : SENTINEL.floats().get(1));
    }

    private static int drawFrame(Bow b, long started) {
        long elapsed = Math.max(0, Math.min(b.profile.chargeTicks(), now(b) - started));
        return 2 + (int) (elapsed * 20 / b.profile.chargeTicks());
    }

    private static void nockFrame(GameTestHelper h, Bow b) {
        var ammo = WeaponRuntime.ammunition(b.player).orElseThrow();
        check(h, ammo.reloading() && ammo.rounds() == 0, "Nock frame follows an actual empty reload session");
        frame(h, b, 32 + (int) Math.floor(ammo.reloadProgress() * 20 + 1e-6f));
    }

    private static void shootAndNock(GameTestHelper h, Bow b) {
        b.player.releaseUsingItem();
        check(h, rounds(b) == 0 && !b.player.isUsingItem(), "Real release consumes exactly the loaded arrow");
        frame(h, b, 0);
        WeaponRuntime.tickPlayer(b.player);
        check(h, WeaponRuntime.reloading(b.player), "Shot starts automatic nock without another press");
        nockFrame(h, b);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void bothBowsUseActualHoldClockAndClampAtTheirOwnFullDrawFrame(GameTestHelper h) {
        check(h, WeaponBowPresentation.SELECTOR_INDEX == 2 && WeaponBowPresentation.EMPTY == 0
                        && WeaponBowPresentation.LOADED == 1 && WeaponBowPresentation.DRAW_BASE == 2
                        && WeaponBowPresentation.NOCK_BASE == 32 && WeaponBowPresentation.STEPS == 20,
                "W50 public selector contract is fixed");
        var precision = bow(h, "biting_winds");
        var lightweight = bow(h, "whispering_slab");
        for (var b : List.of(precision, lightweight)) {
            check(h, WeaponBowPresentation.supports(b.entry), "Selected bow is supported");
            unwrapped(h, b.player, b.stack);
            use(h, b);
            frame(h, b, 2);
            long started = now(b);
            int full = b.profile.chargeTicks();
            h.runAfterDelay(full / 2, () -> {
                WeaponRuntime.continueUse(b.player);
                frame(h, b, drawFrame(b, started));
                var before = b.stack.copy();
                CombatHud.update(b.player);
                CombatHud.update(b.player);
                check(h, ItemStack.matches(before, b.stack), "HUD cannot advance bow presentation");
            });
            h.runAfterDelay(full, () -> {
                WeaponRuntime.tickPlayer(b.player);
                frame(h, b, 22);
                check(h, rounds(b) == 1 && WeaponRuntime.activeProjectiles(b.player) == 0,
                        "Full draw never automatically fires");
            });
            h.runAfterDelay(full - 1, () -> {
                WeaponRuntime.tickPlayer(b.player);
                frame(h, b, drawFrame(b, started));
                check(h, drawFrame(b, started) < 22, "Full frame cannot arrive before the actual charge deadline");
            });
            h.runAfterDelay(full + 4, () -> {
                WeaponRuntime.tickPlayer(b.player);
                frame(h, b, 22);
                b.player.stopUsingItem();
                WeaponRuntime.tickPlayer(b.player);
                frame(h, b, 1);
                check(h, WeaponRuntime.beginUse(b.player), "A direct runtime begin can be accepted");
                WeaponRuntime.tickPlayer(b.player);
                frame(h, b, 1);
                check(h, !b.player.isUsingItem() && rounds(b) == 1
                                && WeaponRuntime.activeProjectiles(b.player) == 0,
                        "Without actual server hold, begin alone cannot display a draw or fire");
            });
        }
        int end = Math.max(precision.profile.chargeTicks(), lightweight.profile.chargeTicks()) + 5;
        ticks(h, end, precision, lightweight);
        h.runAfterDelay(end + 1, h::succeed);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void releaseShowsEmptyThenRealNockProgressAndLoadedIdleOnBothBows(GameTestHelper h) {
        var precision = bow(h, "biting_winds");
        var lightweight = bow(h, "whispering_slab");
        int shotAt = Math.max(precision.profile.chargeTicks(), lightweight.profile.chargeTicks()) + 2;
        int end = shotAt + Math.max(precision.profile.firstReloadTicks(), lightweight.profile.firstReloadTicks()) + 5;
        ticks(h, end, precision, lightweight);
        for (var b : List.of(precision, lightweight)) {
            use(h, b);
            int n = b.profile.firstReloadTicks();
            h.runAfterDelay(shotAt, () -> {
                shootAndNock(h, b);
                frame(h, b, 32);
                var ammo = WeaponRuntime.ammunition(b.player).orElseThrow();
                check(h, ammo.reloadDuration() == n && ammo.reloadRemaining() == n,
                        "Nock starts from the actual first reload deadline");
            });
            h.runAfterDelay(shotAt + n / 2, () -> {
                WeaponRuntime.tickPlayer(b.player);
                nockFrame(h, b);
            });
            h.runAfterDelay(shotAt + n - 1, () -> {
                WeaponRuntime.tickPlayer(b.player);
                nockFrame(h, b);
                check(h, rounds(b) == 0, "No loaded frame before the real nock deadline");
            });
            h.runAfterDelay(shotAt + n, () -> {
                WeaponRuntime.tickPlayer(b.player);
                frame(h, b, 1);
                check(h, rounds(b) == 1 && !WeaponRuntime.reloading(b.player) && !b.player.isUsingItem(),
                        "Exact nock completion transfers one arrow and leaves it idle");
            });
        }
        h.runAfterDelay(end + 1, () -> {
            frame(h, precision, 1);
            frame(h, lightweight, 1);
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void bufferedDrawStartsAtZeroOnlyAfterNockAndEarlyReleaseUsesThatClock(GameTestHelper h) {
        var b = bow(h, "biting_winds");
        int shotAt = b.profile.chargeTicks() + 2, n = b.profile.firstReloadTicks();
        int end = shotAt + 2 * n + 5;
        ticks(h, end, b);
        use(h, b);
        long[] restarted = {-1};
        h.runAfterDelay(shotAt, () -> shootAndNock(h, b));
        h.runAfterDelay(shotAt + 1, () -> {
            // Same-deadline callbacks have no ordering guarantee. beginUse buffers the hold
            // and updates bow float2; only tickPlayer advances the reload owner's float1.
            WeaponRuntime.tickPlayer(b.player);
            nockFrame(h, b);
            var beforeUse = b.stack.get(DataComponents.CUSTOM_MODEL_DATA);
            use(h, b);
            check(h, beforeUse.equals(b.stack.get(DataComponents.CUSTOM_MODEL_DATA)),
                    "Buffered native use preserves the already-ticked reload and bow selectors exactly");
            var ammo = WeaponRuntime.ammunition(b.player).orElseThrow();
            check(h, ammo.reloadDuration() == n && ammo.reloadRemaining() == n - 1,
                    "Buffered hold retains the original nock deadline; it cannot restart or advance reload");
            check(h, !WeaponAiming.requested(b.player) && !WeaponAiming.aimInput(b.player),
                    "Native bow use buffers draw without a left-click ADS request");
            nockFrame(h, b);
        });
        h.runAfterDelay(shotAt + n - 1, () -> {
            WeaponRuntime.tickPlayer(b.player);
            nockFrame(h, b);
            check(h, rounds(b) == 0, "Buffered hold cannot accelerate nock");
        });
        h.runAfterDelay(shotAt + n, () -> {
            WeaponRuntime.tickPlayer(b.player);
            restarted[0] = now(b);
            frame(h, b, 2);
            check(h, rounds(b) == 1 && b.player.isUsingItem(), "Buffered actual hold starts a fresh draw at completion");
        });
        h.runAfterDelay(shotAt + n + 1, () -> {
            WeaponRuntime.continueUse(b.player);
            int expected = drawFrame(b, restarted[0]);
            check(h, expected > 2 && expected < 22, "One real draw tick is a partial frame");
            frame(h, b, expected);
            shootAndNock(h, b);
        });
        h.runAfterDelay(end + 1, () -> {
            frame(h, b, 1);
            check(h, rounds(b) == 1 && !b.player.isUsingItem(), "Partial release nocks once without a ghost draw");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 70, environment = "destiny-test:w90_isolated")
    public void qLetDownImmediatelyRestoresLoadedWireWithoutShotOrDelayedNock(GameTestHelper h) {
        var b = bow(h, "biting_winds");
        int letDownAt = b.profile.chargeTicks() + 2;
        int end = letDownAt + b.profile.firstReloadTicks() + 3;
        ticks(h, end, b);
        use(h, b);
        h.runAfterDelay(letDownAt, () -> {
            frame(h, b, 22);
            check(h, InputRouter.onPlayerAction(b.player, ServerboundPlayerActionPacket.Action.DROP_ITEM),
                    "The real Q packet is consumed");
            frame(h, b, 1);
            check(h, rounds(b) == 1 && !b.player.isUsingItem() && !WeaponRuntime.reloading(b.player),
                    "Let-down immediately retains loaded ammo and ends hold without reload");
            b.player.releaseUsingItem();
            WeaponRuntime.releaseUse(b.player, b.stack);
            check(h, WeaponRuntime.activeProjectiles(b.player) == 0, "Stale releases after Q cannot shoot");
        });
        h.runAfterDelay(end + 1, () -> {
            frame(h, b, 1);
            check(h, rounds(b) == 1 && WeaponRuntime.activeProjectiles(b.player) == 0
                            && !WeaponRuntime.reloading(b.player), "No delayed shot or nock after Q");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void copiedProgressPreviewAndObservedSwapsNeverInheritLiveOwnership(GameTestHelper h) {
        var fixture = bow(h, "biting_winds");
        var saved = fixture.stack.copy();
        var data = saved.get(DataComponents.CUSTOM_MODEL_DATA);
        var values = new java.util.ArrayList<>(data.floats());
        values.set(WeaponBowPresentation.SELECTOR_INDEX, (float) WeaponBowPresentation.DRAW_BASE);
        saved.set(DataComponents.CUSTOM_MODEL_DATA,
                new CustomModelData(values, data.flags(), data.strings(), data.colors()));
        check(h, WeaponItems.entry(saved).isPresent()
                        && saved.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2) == 2,
                "Copied LIVE stack carries a persisted selector matching the first draw frame");
        unwrapped(h, fixture.player, saved);
        fixture.player.setItemInHand(InteractionHand.MAIN_HAND, saved);
        unwrapped(h, fixture.player, saved);
        var b = new Bow(fixture.player, saved, fixture.entry, fixture.profile, fixture.originalModel, new boolean[1]);
        var beforeActivation = b.stack.copy();
        use(h, b);
        check(h, b.stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2) == 2.5f
                        && !ItemStack.matches(beforeActivation, b.stack),
                "Binding actual use changes matching saved selector 2 to 2.5 and invalidates its wire-cache key");
        frame(h, b, 2);
        long started = now(b);
        h.runAfterDelay(1, () -> {
            WeaponRuntime.tickPlayer(b.player);
            int expected = drawFrame(b, started);
            frame(h, b, expected);
            check(h, b.stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2) == expected + .5f,
                    "The next real draw tick retains the activation's half-frame cache offset");
        });
        var replacements = new ItemStack[2]; // Captured at tick4, consumed by a callback registered now.
        var handling = WeaponHandlingProfile.of(b.entry);
        int duration = handling.stowTicks() + handling.readyTicks(), readyAt = 4 + duration;
        check(h, duration > 1 && readyAt < 80, "Authored copy-replacement handling fits the test bound");
        h.runAfterDelay(4, () -> {
            WeaponRuntime.tickPlayer(b.player);
            int expected = drawFrame(b, started);
            frame(h, b, expected);
            check(h, b.stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2) == expected + .5f,
                    "Later real ticks keep the same offset while the integer draw selector advances");
            var copy = b.stack.copy();
            check(h, ItemStack.matches(copy, b.stack), "Copy carries the exact saved active selector");
            unwrapped(h, b.player, copy);
            var preview = WeaponModels.create(b.entry);
            preview.set(DataComponents.CUSTOM_MODEL_DATA, b.stack.get(DataComponents.CUSTOM_MODEL_DATA));
            unwrapped(h, b.player, preview);
            b.player.setItemInHand(InteractionHand.MAIN_HAND, copy);
            unwrapped(h, b.player, copy);
            unwrapped(h, b.player, b.stack);
            WeaponRuntime.tickPlayer(b.player);
            cleared(h, b);
            check(h, rounds(b) == 1 && WeaponItems.magazine(copy, b.profile).rounds() == 1,
                    "Swap never fires or transfers ammo");
            b.player.stopUsingItem();
            check(h, !WeaponRuntime.beginUse(b.player), "W58: replacement cannot draw during handling");
            check(h, WeaponHandling.remaining(b.player) == duration,
                    "Observed copy replacement captures the authored stow plus ready deadline");
            replacements[0] = copy; replacements[1] = preview;
        });
        h.runAfterDelay(readyAt - 1, () -> {
            WeaponRuntime.tickPlayer(b.player);
            check(h, WeaponHandling.remaining(b.player) == 1 && !WeaponRuntime.beginUse(b.player),
                    "Replacement cannot start a draw on the last handling tick");
        });
        h.runAfterDelay(readyAt, () -> {
            var copy = replacements[0]; var preview = replacements[1];
            check(h, copy != null && preview != null && b.player.getMainHandItem() == copy
                            && !WeaponHandling.blocked(b.player), "Exact copied source reaches its original handling deadline");
            WeaponCombatItem.INSTANCE.use(h.getLevel(), b.player, InteractionHand.MAIN_HAND);
            var current = new Bow(b.player, copy, b.entry, b.profile, b.originalModel, new boolean[1]);
            frame(h, current, 2);
            b.player.setItemInHand(InteractionHand.MAIN_HAND, preview);
            WeaponRuntime.tickPlayer(b.player);
            cleared(h, current);
            unwrapped(h, b.player, preview);
            b.player.stopUsingItem();
            WeaponPreviewItem.INSTANCE.use(h.getLevel(), b.player, InteractionHand.MAIN_HAND);
            check(h, !b.player.isUsingItem() && WeaponRuntime.activeProjectiles(b.player) == 0,
                    "Preview use remains inert despite saved progress");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 90, environment = "destiny-test:w90_isolated")
    public void skillAndSharedLifecycleCleanupClearDrawAndNockWithoutResurrection(GameTestHelper h) {
        var draw = bow(h, "biting_winds");
        var nock = bow(h, "whispering_slab");
        use(h, draw);
        WeaponRuntime.cancelUseForSkill(draw.player);
        cleared(h, draw);
        WeaponRuntime.releaseUse(draw.player, draw.stack);
        check(h, rounds(draw) == 1 && WeaponRuntime.activeProjectiles(draw.player) == 0,
                "Skill cancellation of draw cannot release an arrow");
        use(h, draw);
        frame(h, draw, 2);
        // cleanup is the existing shared death/disconnect teardown entry point.
        WeaponRuntime.cleanup(draw.player);
        cleared(h, draw);
        use(h, nock);
        int shotAt = nock.profile.chargeTicks() + 2;
        int end = shotAt + nock.profile.firstReloadTicks() + 4;
        ticks(h, end, draw, nock);
        h.runAfterDelay(shotAt, () -> {
            shootAndNock(h, nock);
            WeaponRuntime.cancelUseForSkill(nock.player);
            cleared(h, nock);
            check(h, !WeaponRuntime.reloading(nock.player), "Skill cancels the actual nock timer");
            check(h, WeaponRuntime.reload(nock.player), "Explicit reload can bind a fresh nock session");
            frame(h, nock, 32);
            WeaponRuntime.cleanup(nock.player);
            cleared(h, nock);
            check(h, !WeaponRuntime.reloading(nock.player) && WeaponRuntime.activeProjectiles(nock.player) == 0,
                    "Shared lifecycle cleanup removes nock and owned projectiles");
        });
        h.runAfterDelay(end + 1, () -> {
            cleared(h, draw);
            cleared(h, nock);
            check(h, rounds(draw) == 1 && rounds(nock) == 0 && !nock.player.isUsingItem(),
                    "Cancelled deadlines cannot refill, rebind presentation or resurrect a draw");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void allOtherFamiliesKeepComponentsAndExistingScopeAndReloadWireRouting(GameTestHelper h) {
        var p = player(h);
        for (var entry : WeaponCatalog.all()) {
            boolean selected = BOWS.contains(entry.id());
            check(h, WeaponBowPresentation.supports(entry) == selected, "Exact W50 support set: " + entry.id());
            if (selected) continue;
            WeaponRuntime.cleanup(p);
            var stack = WeaponItems.create(entry);
            stack.set(DataComponents.CUSTOM_MODEL_DATA, SENTINEL);
            p.setItemInHand(InteractionHand.MAIN_HAND, stack);
            var before = stack.copy();
            check(h, !WeaponRuntime.reload(p), "Full unsupported weapon binds without reloading: " + entry.id());
            WeaponRuntime.tickPlayer(p);
            check(h, !WeaponBowPresentation.active(stack) && ItemStack.matches(before, stack),
                    "W50 tick leaves every unsupported live stack untouched: " + entry.id());
            check(h, projected(stack, stack.get(DataComponents.ITEM_MODEL)).equals(wire(p, stack).get(DataComponents.ITEM_MODEL)),
                    "Unsupported wire keeps original model: " + entry.id());
            if (WeaponScopes.supports(entry)) {
                WeaponModels.setPose(stack, WeaponModels.Pose.SCOPE);
                check(h, WeaponScopes.model(entry).equals(wire(p, stack).get(DataComponents.ITEM_MODEL)),
                        "Existing W45 scope still wins for its weapon: " + entry.id());
                WeaponModels.setPose(stack, WeaponModels.Pose.HIP);
            }
            WeaponRuntime.cancelUseForSkill(p);
            WeaponRuntime.cleanup(p);
            preserved(h, stack);
            check(h, ItemStack.matches(before, stack), "Unsupported cancellation preserves all components: " + entry.id());
        }
        var entry = WeaponCatalog.find("beloved").orElseThrow();
        var stack = WeaponItems.create(entry);
        stack.set(DataComponents.CUSTOM_MODEL_DATA, SENTINEL);
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry), 0, 3));
        p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        check(h, WeaponRuntime.reload(p) && WeaponReloadPresentation.active(stack), "W47 reload still starts");
        check(h, !WeaponBowPresentation.active(stack)
                        && projected(WeaponReloadPresentation.model(entry)).equals(wire(p, stack).get(DataComponents.ITEM_MODEL))
                        && stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2) == 47,
                "W50 cannot steal W47 reload wire routing or its independent slot");
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void twoPlayersKeepIndependentDrawNockAndCleanupOwnership(GameTestHelper h) {
        var first = bow(h, "biting_winds");
        var second = bow(h, "whispering_slab");
        int shotAt = Math.max(first.profile.chargeTicks(), second.profile.chargeTicks()) + 5;
        int end = shotAt + second.profile.firstReloadTicks() + 5;
        ticks(h, end, first, second);
        use(h, first);
        long firstStart = now(first);
        long[] secondStart = {-1};
        h.runAfterDelay(3, () -> {
            use(h, second);
            secondStart[0] = now(second);
            frame(h, second, 2);
            WeaponRuntime.tickPlayer(first.player);
            frame(h, first, drawFrame(first, firstStart));
        });
        h.runAfterDelay(shotAt, () -> {
            shootAndNock(h, first);
            WeaponRuntime.tickPlayer(second.player);
            frame(h, second, drawFrame(second, secondStart[0]));
            var before = second.stack.copy();
            WeaponRuntime.cleanup(first.player);
            cleared(h, first);
            check(h, ItemStack.matches(before, second.stack) && second.player.isUsingItem(),
                    "One player's cleanup cannot clear the other player's held bow");
            frame(h, second, 22);
            second.player.releaseUsingItem();
            frame(h, second, 0);
            check(h, rounds(second) == 0 && WeaponRuntime.activeProjectiles(second.player) == 1
                            && WeaponRuntime.activeProjectiles(first.player) == 0,
                    "Shots and cleanup remain independently owned");
            WeaponRuntime.tickPlayer(second.player);
            nockFrame(h, second);
        });
        h.runAfterDelay(end + 1, () -> {
            cleared(h, first);
            frame(h, second, 1);
            check(h, rounds(first) == 0 && rounds(second) == 1 && !second.player.isUsingItem(),
                    "Only the uncancelled player's real nock completes");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void absentShortAndNonFiniteStoredSelectorsBindSafelyWithoutTouchingOtherSlots(GameTestHelper h) {
        var player = player(h);
        for (String id : List.of("biting_winds", "whispering_slab")) {
            var entry = WeaponCatalog.find(id).orElseThrow();
            var raw = WeaponItems.create(entry);
            raw.remove(DataComponents.CUSTOM_MODEL_DATA);
            player.setItemInHand(InteractionHand.MAIN_HAND, raw);
            check(h, WeaponRuntime.beginUse(player), "Absent CMD is legal: " + id);
            check(h, WeaponBowPresentation.active(raw)
                    && (int)Math.floor(raw.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2)) == 2,
                    "Missing native getFloat returns null and must not be unboxed");
            WeaponRuntime.cleanup(player);
            for (var floats : List.<List<Float>>of(List.of(), List.of(7.25f), List.of(7.25f,.375f),
                    List.of(7.25f,.375f,Float.NaN,99f), List.of(7.25f,.375f,Float.POSITIVE_INFINITY,99f),
                    List.of(7.25f,.375f,Float.NEGATIVE_INFINITY,99f))) {
                var stack = WeaponItems.create(entry);
                stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(floats,
                        SENTINEL.flags(), SENTINEL.strings(), SENTINEL.colors()));
                player.setItemInHand(InteractionHand.MAIN_HAND, stack);
                check(h, WeaponRuntime.beginUse(player), "Short/nonfinite stored selector is safe: " + id);
                var data = stack.get(DataComponents.CUSTOM_MODEL_DATA);
                check(h, WeaponBowPresentation.active(stack) && Float.isFinite(data.getFloat(2))
                        && (int)Math.floor(data.getFloat(2)) == 2, "Only actual new draw selects a finite pose");
                check(h, data.flags().equals(SENTINEL.flags()) && data.strings().equals(SENTINEL.strings())
                        && data.colors().equals(SENTINEL.colors()), "Other component lists survive normalization");
                for (int i = 0; i < floats.size(); i++) if (i != 2)
                    check(h, data.floats().get(i).equals(floats.get(i)), "Independent float slot survives: " + i);
                WeaponRuntime.cleanup(player);
                check(h, stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2) == -1
                        && WeaponItems.magazine(stack,WeaponProfile.forEntry(entry)).rounds() == 1,
                        "Cleanup invalidates the newly padded selector without firing");
            }
        }
        h.succeed();
    }
}
