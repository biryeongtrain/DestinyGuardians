package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponScopeHud;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.camera.api.CameraEffects;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Real server ticks and Polymer output; no synthetic clock or presentation activation.
 * These assertions establish server ownership/selectors, not native rendering evidence.
 */
public final class WeaponAimPresentationW70GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final CustomModelData SENTINEL = new CustomModelData(
            List.of(7.25f, .375f, 47f, -1f, 99f), List.of(true, false, true),
            List.of("hip", "w70_keep", "w70_extra"), List.of(0x123456, 0xABCDEF));

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static void near(GameTestHelper h, float actual, float expected, String message) {
        check(h, Math.abs(actual - expected) < .00001f, message + ": " + actual + " != " + expected);
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()));
    }
    private static ServerPlayer player(GameTestHelper h, String id) {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), -90, -80);
        var stack = WeaponItems.create(entry(id));
        int slot = WeaponCharacteristics.of(entry(id)).slot().hotbar();
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.getInventory().setItem(slot, stack);
        p.getInventory().setSelectedSlot(slot);
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.EMERALD, 4));
        TestCleanup.register(h, () -> {
            p.setServerLevel(h.getLevel());
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            WeaponScopeHud.remove(p);
            for (String node : List.copyOf(DisplayHud.getHuds(p).keySet())) DisplayHud.removeHud(p, node);
            CameraEffects.resetFov(p);
            TestPlayers.remove(p);
        });
        return p;
    }
    private static void tick(ServerPlayer p) {
        WeaponRuntime.tickPlayer(p);
        TestPlayers.drain(p);
    }
    private static ItemStack wire(ServerPlayer p, ItemStack stack) {
        var context = ((PacketContextProvider) (Object) p.connection).getPacketContext();
        return PolymerItemUtils.getPolymerItemStack(stack, context, p.level().registryAccess());
    }
    private static Identifier aimModel(String id, boolean bow) {
        return aimRoute(id, bow);
    }
    private static float sample(float progress) { return (float)Math.floor(progress * 20 + 1e-6f) / 20; }
    private static float selector(ItemStack stack) { return stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(3); }
    private static void selector(ItemStack stack, float value) {
        var data = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        var floats = new ArrayList<>(data.floats());
        while (floats.size() < 4) floats.add(0f);
        floats.set(3, value);
        stack.set(DataComponents.CUSTOM_MODEL_DATA,
                new CustomModelData(floats, data.flags(), data.strings(), data.colors()));
    }
    private static void aiming(GameTestHelper h, ServerPlayer p, float expected, float offset) {
        var stack = p.getMainHandItem();
        near(h, WeaponAiming.progress(p), expected, "Raw ADS follows actual input ticks");
        check(h, WeaponAimPresentation.active(stack), "Matching live owner authorizes W70");
        near(h, selector(stack), sample(expected) + offset, "Float3 quantizes raw progress with stable binding offset");
        String id = WeaponItems.entry(stack).orElseThrow().id();
        var model = aimModel(id, WeaponBowPresentation.active(stack));
        check(h, WeaponAimPresentation.model(stack).equals(model), "Exact W70 model and actual-bow suffix");
        var before = stack.copy();
        check(h, wire(p, stack).get(DataComponents.ITEM_MODEL).equals(projected(model)), "Polymer routes intermediate ADS");
        check(h, ItemStack.matches(before, stack)
                        && Identifier.parse(entry(id).item_model()).equals(stack.get(DataComponents.ITEM_MODEL)),
                "Wire reads keep authoritative model and every real component");
    }
    private static void restored(GameTestHelper h, ItemStack stack, CustomModelData original) {
        restored(h, stack, original, 0);
    }
    private static void restored(GameTestHelper h, ItemStack stack, CustomModelData original, int independentLength) {
        var actual = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        check(h, !WeaponAimPresentation.active(stack)
                        && Objects.equals(actual.getFloat(3), original.getFloat(3))
                        && actual.floats().size() == Math.max(original.floats().size(), independentLength),
                "Retired binding restores original float3/length, retaining independent renderer slots");
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void intermediateAmmitUsesRawSevenTickProgressAndPureSampledWireReads(GameTestHelper h) {
        check(h, WeaponAimPresentation.PROGRESS_INDEX == 3 && WeaponAimPresentation.STEPS == 20,
                "W70 selector contract");
        var p = player(h, "ammit_ar2"); var stack = p.getMainHandItem();
        stack.set(DataComponents.CUSTOM_MODEL_DATA, SENTINEL);
        tick(p); ads(p, true);
        int rounds = ammo(stack).rounds();
        for (int i = 1; i <= 7; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                tick(p); aiming(h, p, Math.min(1, elapsed / (float)WeaponAiming.fast(7)), 0);
                var saved = stack.copy(); var fov = CameraEffects.getFov(p);
                var ballistics = WeaponAiming.ballistics(p, entry("ammit_ar2"));
                for (int read = 0; read < 3; read++) {
                    wire(p, stack); WeaponAimPresentation.active(stack); WeaponAimPresentation.model(stack);
                    CombatHud.update(p); WeaponAiming.tick(p);
                }
                check(h, ItemStack.matches(saved, stack) && Objects.equals(fov, CameraEffects.getFov(p))
                                && ballistics.equals(WeaponAiming.ballistics(p, entry("ammit_ar2")))
                                && ammo(stack).rounds() == rounds && WeaponRuntime.activeProjectiles(p) == 0,
                        "Repeated same-tick reads/HUD leave progress, FOV, ballistics, ammo and shots unchanged");
                if (elapsed == 7) ads(p, false);
            });
        }
        for (int i = 1; i <= 9; i++) {
            int elapsed = i;
            h.runAfterDelay(7 + i, () -> {
                tick(p);
                float raw = WeaponAiming.progress(p);
                near(h, raw, Math.max(0, 1 - elapsed / (float)WeaponAiming.fast(7)), "Release retains base seven-tick exit");
                if (raw > 0) aiming(h, p, raw, 0); else restored(h, stack, SENTINEL);
                if (elapsed == 9) {
                    check(h, projected(stack.get(DataComponents.ITEM_MODEL)).equals(wire(p, stack).get(DataComponents.ITEM_MODEL)),
                            "Zero progress restores base wire model");
                    h.succeed();
                }
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void reversingSnapshotEntryKeepsBaseExitAndActualNineTickShotCadence(GameTestHelper h) {
        var normal = player(h, "austringer"); var fast = player(h, "austringer");
        try {
            check(h, h.getLevel().getServer().getCommands().getDispatcher().execute(
                    "destiny perk select snapshot_sights", fast.createCommandSourceStack()) == 1,
                    "Registered command selects real Snapshot socket");
        } catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) { throw new AssertionError(e); }
        var actors = List.of(normal, fast);
        var rounds = actors.stream().map(p -> ammo(p.getMainHandItem()).rounds()).toList();
        for (var p : actors) {
            tick(p);
            check(h, WeaponRuntime.beginUse(p), "Initial paid shot accepted");
            WeaponRuntime.releaseUse(p, p.getMainHandItem()); ads(p, true);
        }
        float[] expected = {0, 0};
        for (int i = 1; i <= 9; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                for (int j = 0; j < actors.size(); j++) {
                    var p = actors.get(j);
                    // Toggle off after four ticks; three quiet ticks permit a fresh click, with base-speed exit throughout.
                    expected[j] = Math.clamp(expected[j] + (elapsed >= 5 && elapsed <= 7 ? -1f / WeaponAiming.fast(6) : 1f / WeaponAiming.fast(j == 0 ? 6 : 3)), 0, 1);
                    tick(p); aiming(h, p, expected[j], 0);
                    check(h, WeaponRuntime.beginUse(p) == (elapsed == 9), "Original nine-tick fire deadline");
                    WeaponRuntime.releaseUse(p, p.getMainHandItem());
                    check(h, ammo(p.getMainHandItem()).rounds() == rounds.get(j) - (elapsed == 9 ? 2 : 1),
                            "ADS reversal and Snapshot never grant an extra shot");
                    if (elapsed == 4) ads(p, false);
                    if (elapsed == 7) ads(p, true);
                }
                if (elapsed == 9) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void cancellationAndLateOldOwnerCleanupPreserveExactStackRecipient(GameTestHelper h) {
        var actors = new ArrayList<ServerPlayer>();
        for (int i = 0; i < 7; i++) { var p = player(h, "ammit_ar2"); tick(p); ads(p, true); actors.add(p); }
        var originals = actors.stream().map(ServerPlayer::getMainHandItem).toList();
        var originalCmd = originals.stream().map(s -> s.get(DataComponents.CUSTOM_MODEL_DATA)).toList();
        WeaponItems.save(originals.getFirst(), new WeaponMagazine(WeaponProfile.forEntry(entry("ammit_ar2")), 1, 0));
        var donor = player(h, "ammit_ar2"); var transferred = donor.getMainHandItem();
        // Do not create a WeaponRuntime.State for the donor: automatic runtime iteration
        // would eagerly retire its old Aiming session before the deliberately late cleanup.
        WeaponAiming.tick(donor); ads(donor, true);
        var recipient = player(h, "ammit_ar2");
        for (int i = 1; i <= 7; i++) h.runAfterDelay(i, () -> {
            for (var p : actors) tick(p);
            WeaponAiming.tick(donor);
        });
        h.runAfterDelay(8, () -> {
            check(h, InputRouter.onPlayerAction(actors.get(0), ServerboundPlayerActionPacket.Action.DROP_ITEM)
                            && WeaponRuntime.reloading(actors.get(0)), "Actual Q reload cancels ADS");
            check(h, projected(WeaponReloadPresentation.model(entry("ammit_ar2"))).equals(
                    wire(actors.get(0), originals.get(0)).get(DataComponents.ITEM_MODEL)), "Actual reload wins over ADS");
            WeaponRuntime.cancelUseForSkill(actors.get(1));
            actors.get(2).connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(4)); tick(actors.get(2));
            ads(actors.get(3), false); WeaponRuntime.cleanup(actors.get(3));
            var other = java.util.stream.StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                    .filter(level -> level != h.getLevel()).findFirst().orElseThrow();
            var dimension = actors.get(4); ads(dimension, false); dimension.setServerLevel(other);
            check(h, !WeaponAimPresentation.active(originals.get(4)), "Level mismatch immediately loses authorization");
            tick(dimension); dimension.setServerLevel(h.getLevel());
            actors.get(5).setGameMode(GameType.SPECTATOR);
            check(h, !WeaponAimPresentation.active(originals.get(5)), "Actual ineligible owner loses authorization");
            tick(actors.get(5));
            for (int i = 0; i < 6; i++) restored(h, originals.get(i), originalCmd.get(i), i == 0 ? 2 : 0);
            donor.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            check(h, !WeaponAimPresentation.active(transferred), "Stack detached from donor has no authority");
            recipient.setItemInHand(InteractionHand.MAIN_HAND, transferred); ads(recipient, true);
            tick(recipient); aiming(h, recipient, Math.min(1f, 1f / WeaponAiming.fast(7)), .001f);
        });
        for (int i = 9; i <= 12; i++) h.runAfterDelay(i, () -> {
            tick(recipient); tick(actors.get(0)); tick(actors.get(1));
            restored(h, originals.get(0), originalCmd.get(0), 2);
            restored(h, originals.get(1), originalCmd.get(1));
        });
        h.runAfterDelay(13, () -> {
            check(h, recipient.getMainHandItem() == transferred, "Transferred object is the exact ItemStack");
            check(h, "ads".equals(transferred.get(DataComponents.CUSTOM_MODEL_DATA).getString(0)),
                    "New owner advances past half before old owner's cleanup");
            var before = transferred.copy(); float progress = WeaponAiming.progress(recipient);
            WeaponRuntime.cleanup(donor); WeaponRuntime.cleanup(donor);
            check(h, ItemStack.matches(before, transferred), "Late old session cannot clear new float3 or overwrite its ADS pose");
            aiming(h, recipient, progress, .001f);
            aiming(h, actors.get(6), 1, 0);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 15, environment = "destiny-test:w90_isolated")
    public void repeatedExactStackHandoffsRestorePreDonorComponentsAndInvalidateEqualSamples(GameTestHelper h) {
        var first = player(h, "ammit_ar2"); var second = player(h, "ammit_ar2"); var third = player(h, "ammit_ar2");
        var stack = first.getMainHandItem(); selector(stack, .4f); var original = stack.copy();
        // Direct actual Aiming sessions deliberately avoid Runtime eagerly retiring donors.
        WeaponAiming.tick(first); ads(first, true);
        h.runAfterDelay(1, () -> {
            WeaponAiming.tick(first); aiming(h, first, Math.min(1f, 1f / WeaponAiming.fast(7)), .001f);
            var before = stack.copy(); first.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            second.setItemInHand(InteractionHand.MAIN_HAND, stack); ads(second, true);
            WeaponAiming.tick(second); aiming(h, second, Math.min(1f, 1f / WeaponAiming.fast(7)), .002f);
            check(h, !ItemStack.matches(before, stack), "Second owner cannot reuse identical donor sample");
            var current = stack.copy(); WeaponAiming.cleanup(first);
            check(h, ItemStack.matches(current, stack), "First donor cleanup leaves second owner intact");
        });
        h.runAfterDelay(2, () -> {
            WeaponAiming.tick(second); var before = stack.copy();
            second.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            third.setItemInHand(InteractionHand.MAIN_HAND, stack); ads(third, true);
            WeaponAiming.tick(third); aiming(h, third, Math.min(1f, 1f / WeaponAiming.fast(7)), .001f);
            check(h, !ItemStack.matches(before, stack), "Third owner acquisition changes selector");
            var current = stack.copy(); WeaponAiming.cleanup(second);
            check(h, ItemStack.matches(current, stack), "Second donor cleanup leaves third owner intact");
        });
        h.runAfterDelay(3, () -> {
            WeaponAiming.cleanup(third);
            check(h, ItemStack.matches(original, stack), "Final retirement restores pre-donor complete components, not live donor float3");
            check(h, projected(original.get(DataComponents.ITEM_MODEL)).equals(wire(third, stack).get(DataComponents.ITEM_MODEL)),
                    "Retired chain has no cached W70 route");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 15, environment = "destiny-test:w90_isolated")
    public void bothGripsPreserveIndependentCmdOffhandAndPolymerRoundTrip(GameTestHelper h) {
        var actors = new ArrayList<ServerPlayer>(); var saved = new ArrayList<ItemStack>();
        for (var grip : WeaponModels.Grip.values()) for (var floats : List.<List<Float>>of(
                SENTINEL.floats(), List.of(), List.of(7.25f), List.of(7.25f, .375f),
                List.of(7.25f, .375f, 47f), List.of(7.25f, .375f, 47f, Float.NaN, 99f),
                List.of(7.25f, .375f, 47f, Float.POSITIVE_INFINITY, 99f))) {
            var p = player(h, "ammit_ar2");
            var stack = WeaponModels.withGrip(p.getMainHandItem(), grip).orElseThrow();
            stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(floats,
                    List.of(grip == WeaponModels.Grip.TWO_HAND, false, true), SENTINEL.strings(), SENTINEL.colors()));
            stack.set(DataComponents.CUSTOM_NAME, Component.literal("W70 retained " + grip));
            p.setItemInHand(InteractionHand.MAIN_HAND, stack); saved.add(stack.copy()); actors.add(p);
            tick(p); ads(p, true);
        }
        for (int i = 1; i <= 7; i++) h.runAfterDelay(i, () -> {
            for (int j = 0; j < actors.size(); j++) {
                var p = actors.get(j); tick(p); var stack = p.getMainHandItem();
                var data = stack.get(DataComponents.CUSTOM_MODEL_DATA); var original = saved.get(j);
                var old = original.get(DataComponents.CUSTOM_MODEL_DATA);
                for (int index = 0; index < old.floats().size(); index++) if (index != 3)
                    check(h, data.floats().get(index).equals(old.floats().get(index)), "Independent CMD float " + index);
                check(h, data.flags().equals(old.flags()) && data.colors().equals(old.colors())
                                && data.strings().subList(1, data.strings().size()).equals(old.strings().subList(1, old.strings().size()))
                                && Objects.equals(stack.get(DataComponents.CUSTOM_DATA), original.get(DataComponents.CUSTOM_DATA))
                                && Objects.equals(stack.get(DataComponents.CUSTOM_NAME), original.get(DataComponents.CUSTOM_NAME))
                                && Objects.equals(stack.get(DataComponents.LORE), original.get(DataComponents.LORE)),
                        "Aim preserves grip, unrelated lists, ammo NBT, name and lore");
                var before = stack.copy(); var out = wire(p, stack); boolean two = WeaponModels.twoHanded(stack);
                check(h, out.is(two ? Items.CROSSBOW : Items.STICK) && CrossbowItem.isCharged(out) == two
                                && out.get(DataComponents.CUSTOM_MODEL_DATA).floats().equals(data.floats())
                                && out.get(DataComponents.CUSTOM_MODEL_DATA).flags().equals(wireFlags(stack)),
                        "W70 retains native carrier, charge marker and independent wire selectors");
                var context = ((PacketContextProvider) (Object)p.connection).getPacketContext();
                check(h, ItemStack.matches(before, PolymerItemUtils.getRealItemStack(out, context, h.getLevel().registryAccess()))
                                && ItemStack.matches(before, stack) && p.getOffhandItem().is(Items.EMERALD)
                                && p.getOffhandItem().getCount() == 4, "Round trip and offhand stay authoritative");
            }
        });
        h.runAfterDelay(8, () -> {
            for (int j = 0; j < actors.size(); j++) {
                var p = actors.get(j); WeaponRuntime.cleanup(p);
                restored(h, p.getMainHandItem(), saved.get(j).get(DataComponents.CUSTOM_MODEL_DATA));
                check(h, ItemStack.matches(saved.get(j), p.getMainHandItem()),
                        "Cleanup restores complete original components, including absent/short float3 and nonfinite saved data");
            }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 15, environment = "destiny-test:w90_isolated")
    public void copiedNbtAndFakeBowSelectorsCannotAuthorizeAndEqualSampleAcquisitionDiffs(GameTestHelper h) {
        var p = player(h, "ammit_ar2"); var stack = p.getMainHandItem();
        tick(p); selector(stack, .1f); var saved = stack.copy(); ads(p, true);
        var later = player(h, "ammit_ar2"); var laterStack = later.getMainHandItem();
        tick(later); selector(laterStack, .4f); var laterSaved = laterStack.copy(); ads(later, true);
        var loaded = player(h, "ammit_ar2");
        var fakeBow = player(h, "biting_winds"); var bowStack = fakeBow.getMainHandItem();
        bowStack.set(DataComponents.CUSTOM_MODEL_DATA, SENTINEL); ads(fakeBow, true);
        // An actual Aiming tick is enough to test the base bow wrapper independently
        // of Runtime's real W50 binding; stored float2=47 is deliberately not authority.
        h.runAfterDelay(1, () -> {
            tick(p); aiming(h, p, Math.min(1f, 1f / WeaponAiming.fast(7)), .001f);
            tick(later); aiming(h, later, Math.min(1f, 1f / WeaponAiming.fast(7)), .001f);
            check(h, !ItemStack.matches(saved, stack), "Saved first sample .1 must change to .101 on acquisition");
            var ops = h.getLevel().registryAccess().createSerializationContext(NbtOps.INSTANCE);
            var decoded = ItemStack.CODEC.parse(ops, ItemStack.CODEC.encodeStart(ops, stack).getOrThrow()).getOrThrow();
            var preview = WeaponModels.create(entry("ammit_ar2"));
            preview.set(DataComponents.CUSTOM_MODEL_DATA, stack.get(DataComponents.CUSTOM_MODEL_DATA));
            for (var unowned : List.of(stack.copy(), decoded, preview)) {
                var before = unowned.copy();
                check(h, !WeaponAimPresentation.active(unowned)
                                && projected(unowned, unowned.get(DataComponents.ITEM_MODEL)).equals(wire(p, unowned).get(DataComponents.ITEM_MODEL))
                                && ItemStack.matches(before, unowned), "Copy/NBT/preview cannot authorize W70 or mutate on read");
            }
            loaded.setItemInHand(InteractionHand.MAIN_HAND, decoded);
            check(h, !WeaponAimPresentation.active(decoded), "Equipping NBT-loaded stack still grants no authority");
            tick(loaded);
            check(h, !WeaponAimPresentation.active(decoded) && WeaponAiming.progress(loaded) == 0,
                    "A loaded selector cannot aim without actual crouch input");
            ads(loaded, true);
            WeaponAiming.tick(fakeBow);
            check(h, !WeaponBowPresentation.active(bowStack), "Stored draw/nock selector grants no W50 binding");
            aiming(h, fakeBow, Math.min(1f, 1f / WeaponAiming.fast(9)), 0);
            check(h, WeaponAimPresentation.model(bowStack).equals(aimModel("biting_winds", false))
                            && bowStack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2) == 47,
                    "Actual aim with fake saved bow keeps base W70 variant and float2");
        });
        h.runAfterDelay(2, () -> {
            tick(p); aiming(h, p, Math.min(1f, 2f / WeaponAiming.fast(7)), .001f);
            tick(later); aiming(h, later, Math.min(1f, 2f / WeaponAiming.fast(7)), .001f);
            WeaponCombatItem.INSTANCE.use(h.getLevel(), fakeBow, InteractionHand.MAIN_HAND);
            check(h, fakeBow.isUsingItem() && fakeBow.getUseItem() == bowStack, "Real bow use acquires Runtime ownership");
            tick(fakeBow); aiming(h, fakeBow, Math.min(1f, 2f / WeaponAiming.fast(9)), 0);
            check(h, WeaponBowPresentation.active(bowStack)
                            && WeaponAimPresentation.model(bowStack).equals(aimModel("biting_winds", true))
                            && (int)Math.floor(bowStack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2)) == 2,
                    "Only real Runtime bow binding enables _bow");
            tick(loaded); aiming(h, loaded, Math.min(1f, 1f / WeaponAiming.fast(7)), 0);
            WeaponRuntime.cleanup(p); restored(h, stack, saved.get(DataComponents.CUSTOM_MODEL_DATA));
            check(h, ItemStack.matches(saved, stack), "Cleanup restores all original saved components");
        });
        h.runAfterDelay(3, () -> {
            tick(later); aiming(h, later, Math.min(1f, 3f / WeaponAiming.fast(7)), .001f);
            var active = laterStack.copy();
            WeaponRuntime.cancelUseForSkill(later);
            restored(h, laterStack, laterSaved.get(DataComponents.CUSTOM_MODEL_DATA));
            check(h, !ItemStack.matches(active, laterStack) && ItemStack.matches(laterSaved, laterStack),
                    "Later matching .4 sample still differs on suspension and restores every original component");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void all57RangedEntriesAuthorizeWhileSixSwordAndGlaiveEntriesStayExcluded(GameTestHelper h) {
        WeaponModelGameTests.assertCatalogExpansion(h);
        check(h, WeaponModelGameTests.originalW30Entries().stream().filter(WeaponAimProfile::supports).count() == 57
                        && WeaponModelGameTests.originalW30Entries().stream().filter(e -> !WeaponAimProfile.supports(e)).count() == 6,
                "Original W30 57/6 ADS support preserved");
        var actors = new ArrayList<ServerPlayer>();
        for (var e : WeaponCatalog.all()) {
            var p = player(h, e.id()); selector(p.getMainHandItem(), -1);
            tick(p); ads(p, true); actors.add(p);
        }
        h.runAfterDelay(1, () -> {
            int supported = 0, excluded = 0;
            for (var p : actors) {
                tick(p); var stack = p.getMainHandItem(); var e = WeaponItems.entry(stack).orElseThrow();
                boolean ranged = WeaponAimProfile.supports(e);
                check(h, WeaponAimPresentation.active(stack) == ranged, "Exact ranged authorization: " + e.id());
                if (ranged) { supported++; aiming(h, p, 1f / WeaponAiming.fast(WeaponAimProfile.of(e).transitionTicks()), 0); }
                else {
                    excluded++;
                    check(h, (e.family().equals("sword") || e.family().equals("glaive"))
                                    && WeaponAiming.progress(p) == 0 && selector(stack) == -1,
                            "Melee families never acquire or write ADS progress");
                }
            }
            check(h, supported == 59 && excluded == 6, "Complete 59/6 catalog coverage including Ace and Izanagi"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void sniperHalfThresholdRetainsExactW45WhileLfrKeepsW70AndActualScopeHud(GameTestHelper h) {
        var actors = new ArrayList<ServerPlayer>();
        for (String id : List.of("bite_of_the_fox", "beloved", "apostate", "line_in_the_sand", "stormchaser")) {
            var p = player(h, id); tick(p); ads(p, true); actors.add(p);
        }
        for (int i = 1; i <= 11; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                for (var p : actors) {
                    tick(p); CombatHud.update(p); var stack = p.getMainHandItem();
                    var e = WeaponItems.entry(stack).orElseThrow(); float progress = WeaponAiming.progress(p);
                    boolean scoped = progress >= .5f, sniper = e.family().equals("sniper_rifle");
                    check(h, WeaponAimPresentation.active(stack) && WeaponAiming.scoped(p) == scoped,
                            "Live W70 session preserves real half-progress scope authorization");
                    near(h, selector(stack), sample(progress), "Scope pose does not replace ADS selector");
                    var expected = scoped && sniper ? WeaponScopes.model(e) : sniper ? aimModel(e.id(), false)
                            : Identifier.parse("destiny:weapon_sight_w150/" + e.id());
                    check(h, projected(expected).equals(wire(p, stack).get(DataComponents.ITEM_MODEL)),
                            "Sniper exact W45 priority versus current continuously moving LFR W150");
                    var center = DisplayHud.getHud(p, WeaponScopeHud.CENTER_ID);
                    var frame = DisplayHud.getHud(p, WeaponScopeHud.FRAME_ID);
                    if (scoped) {
                        check(h, center instanceof ItemDisplayHud && !center.isRemoved()
                                        && center.isAboveHand() && center.getLocation().z() == 6
                                        && (sniper ? frame instanceof ItemDisplayHud && !frame.isRemoved() : frame == null),
                                "Actual W45 HUD retains sniper aperture/center and LFR center only");
                        check(h, Identifier.parse("destiny:gui/hud/scope_w45_" + e.id() + "_reticle").equals(
                                ((ItemDisplayHud)center).getItem().get(DataComponents.ITEM_MODEL)), "Weapon-specific live scope reticle");
                    } else check(h, center == null && frame == null, "No early scope HUD before half");
                }
                if (elapsed == 11) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void bothActualBowDrawsSelectCompositeThenReleaseNocksWithoutChangingAimTiming(GameTestHelper h) {
        var actors = new ArrayList<ServerPlayer>();
        var originals = new ArrayList<CustomModelData>();
        for (String id : List.of("biting_winds", "whispering_slab")) {
            var p = player(h, id); tick(p); ads(p, true); actors.add(p);
            WeaponCombatItem.INSTANCE.use(h.getLevel(), p, InteractionHand.MAIN_HAND);
            check(h, p.isUsingItem() && p.getUseItem() == p.getMainHandItem(), "Actual native bow hold");
            var original = p.getMainHandItem().get(DataComponents.CUSTOM_MODEL_DATA);
            check(h, Float.valueOf(0).equals(original.getFloat(1)),
                    "Bow float2 padding supplies saved reload sample0; later acquisition must distinguish this cache key");
            originals.add(original);
        }
        long started = h.getLevel().getServer().getTickCount();
        int shotAt = actors.stream().mapToInt(p -> WeaponProfile.forEntry(WeaponItems.entry(p.getMainHandItem()).orElseThrow()).chargeTicks()).max().orElseThrow() + 2;
        int end = shotAt + actors.stream().mapToInt(p -> WeaponProfile.forEntry(WeaponItems.entry(p.getMainHandItem()).orElseThrow()).firstReloadTicks()).max().orElseThrow() + 3;
        for (int i = 1; i <= end; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                for (var p : actors) {
                    tick(p); var stack = p.getMainHandItem(); var e = WeaponItems.entry(stack).orElseThrow();
                    var profile = WeaponProfile.forEntry(e);
                    int frame = (int)Math.floor(stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2));
                    if (elapsed < shotAt) {
                        long held = Math.min(profile.chargeTicks(), p.level().getServer().getTickCount() - started);
                        check(h, frame == 2 + (int)(held * 20 / profile.chargeTicks()), "Real charge controls current float2 draw sample");
                        aiming(h, p, Math.min(1, elapsed / (float)WeaponAiming.fast(9)), 0);
                        check(h, ammo(stack).rounds() == 1 && WeaponRuntime.activeProjectiles(p) == 0,
                                "ADS/draw never fires before real release");
                    } else if (elapsed == shotAt) {
                        check(h, frame == 22, "Both bows reach their own real full draw deadline");
                        p.releaseUsingItem();
                        check(h, ammo(stack).rounds() == 0 && WeaponRuntime.activeProjectiles(p) == 1,
                                "Actual release spends one arrow and emits exactly one shot");
                        tick(p);
                        check(h, WeaponRuntime.reloading(p) && WeaponReloadPresentation.ownedBy(p, stack),
                                "Actual automatic nock acquires reload authority on the paid shot tick");
                        near(h, stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(1), .001f,
                                "Saved sample0 collision requires the authored .001 activation offset");
                    }
                    if (elapsed >= shotAt && WeaponRuntime.reloading(p)) {
                        var status = WeaponRuntime.ammunition(p).orElseThrow();
                        restored(h, stack, originals.get(actors.indexOf(p)));
                        check(h, !WeaponAimPresentation.active(stack)
                                        && (int)Math.floor(stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(2))
                                        == 32 + (int)Math.floor(status.reloadProgress() * 20 + 1e-6f)
                                        && WeaponReloadPresentation.ownedBy(p, stack)
                                        && projected(Identifier.parse("destiny:weapon_reload_w222_" + e.id() + "/" + e.id()))
                                                .equals(wire(p, stack).get(DataComponents.ITEM_MODEL)),
                                "Automatic nock suspends ADS; W222 reload route wins while W50 float2 continues");
                        near(h, stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(1),
                                (float)Math.floor(status.reloadProgress() * 60 + 1e-6f) / 60 + .001f,
                                "Actual nock clock advances 60-interval float1 while retaining its saved-sample collision offset");
                    }
                    if (elapsed == end) {
                        check(h, ammo(stack).rounds() == 1 && !WeaponRuntime.reloading(p) && !p.isUsingItem(),
                                "Real nock completes once without ghost draw or extra shot");
                        check(h, !WeaponReloadPresentation.active(stack)
                                        && stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(1) == -1
                                        && projected(Identifier.parse("destiny:weapon_bow_w50/" + e.id())).equals(wire(p, stack).get(DataComponents.ITEM_MODEL)),
                                "Nock deadline retires float1 and restores owned loaded-bow wire");
                        restored(h, stack, originals.get(actors.indexOf(p))); ads(p, false);
                    }
                }
            });
        }
        h.runAfterDelay(end + 1, () -> { for (var p : actors) { tick(p); ads(p, true); } });
        h.runAfterDelay(end + 2, () -> {
            for (var p : actors) { tick(p); aiming(h, p, Math.min(1f, 1f / WeaponAiming.fast(9)), 0); }
            h.succeed();
        });
    }
}
