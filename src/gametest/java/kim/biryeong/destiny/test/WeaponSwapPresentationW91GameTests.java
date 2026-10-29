package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponScopeHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.camera.api.CameraEffects;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemStackTemplate;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.ChargedProjectiles;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Production selection/Handling/runtime/Polymer pathways; no synthetic presentation activation.
 * Slot packets here are server fixtures, not evidence of supported Vision native slot input.
 */
public final class WeaponSwapPresentationW91GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final CustomModelData SENTINEL = new CustomModelData(
            List.of(17f, .375f, 47f, -1f, 99f, 91.125f, 64f, 73f),
            List.of(true, false, true), List.of("hip", "w91_keep", "extra"), List.of(0x123456, 0xABCDEF));
    private record Pair(ServerPlayer owner, ItemStack outgoing, ItemStack incoming, int targetSlot) {}

    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static WeaponCatalog.Entry entry(ItemStack stack) { return WeaponItems.entry(stack).orElseThrow(); }
    private static WeaponMagazine ammo(ItemStack stack) { return WeaponItems.magazine(stack, WeaponProfile.forEntry(entry(stack))); }
    private static int slot(ItemStack stack) { return WeaponCharacteristics.of(entry(stack)).slot().hotbar(); }
    private static int stow(ItemStack stack) { return WeaponHandlingProfile.of(entry(stack)).stowTicks(); }
    private static int ready(ItemStack stack) { return WeaponHandlingProfile.of(entry(stack)).readyTicks(); }
    private static ItemStack item(String id) {
        var stack = WeaponItems.create(entry(id));
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry(id)), id.equals("beloved") ? 2 : 5, 5));
        stack.set(DataComponents.CUSTOM_MODEL_DATA, SENTINEL);
        stack.set(DataComponents.CHARGED_PROJECTILES, ChargedProjectiles.of(new ItemStackTemplate(Items.SPECTRAL_ARROW)));
        return stack;
    }
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), -90, -80);
        TestCleanup.register(h, () -> {
            p.setServerLevel(h.getLevel()); ads(p, false); p.stopUsingItem();
            if (AbilityService.inSuper(p)) AbilityService.endSuper(p);
            WeaponRuntime.cleanup(p); AbilityService.cleanup(p);
            CombatHud.remove(p); WeaponScopeHud.remove(p);
            for (String node : List.copyOf(DisplayHud.getHuds(p).keySet())) DisplayHud.removeHud(p, node);
            CameraEffects.resetFov(p); TestPlayers.remove(p);
        });
        return p;
    }
    private static Pair pair(GameTestHelper h, String from, WeaponModels.Grip incomingGrip) {
        var p = player(h);
        var a = item(from); var b = WeaponModels.withGrip(item(from.equals("austringer") ? "beloved" : "austringer"), incomingGrip).orElseThrow();
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.getInventory().setItem(slot(a), a); p.getInventory().setItem(slot(b), b);
        p.getInventory().setSelectedSlot(slot(a)); tick(p);
        return new Pair(p, a, b, slot(b));
    }
    private static void tick(ServerPlayer p) { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); }
    private static void select(ServerPlayer p, int slot) {
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot)); tick(p);
    }
    private static ItemStack wire(ServerPlayer p, ItemStack stack) {
        var context = ((PacketContextProvider) (Object) p.connection).getPacketContext();
        return PolymerItemUtils.getPolymerItemStack(stack, context, p.level().registryAccess());
    }
    private static float active(GameTestHelper h, ServerPlayer p, String from, WeaponSwapCycle.Phase phase) {
        var stack = p.getMainHandItem(); var saved = stack.copy();
        var view = WeaponHandling.presentation(p).orElseThrow();
        check(h, view.outgoing().equals(entry(from)) && view.phase() == phase, "Actual Handling outgoing and phase");
        check(h, WeaponSwapPresentation.active(stack), "Actual owned transition authorizes presentation");
        var model = Identifier.parse("destiny:weapon_swap_w91/" + from + "_to_" + entry(stack).id());
        check(h, model.equals(WeaponSwapPresentation.model(stack)), "Exact pair item definition");
        float expected = (phase == WeaponSwapCycle.Phase.READY ? 2 : 0)
                + (float) Math.floor(view.progress() * 20 + 1e-6f) / 20;
        float offset = stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(5) - expected;
        check(h, offset > 0 && offset < .001f,
                "Slot5 follows existing server phase sample with positive sub-.001 cache offset");
        for (int read = 0; read < 3; read++) {
            var out = wire(p, stack);
            check(h, projected(model).equals(out.get(DataComponents.ITEM_MODEL)), "Highest Polymer route selects live swap");
            boolean twohand = WeaponModels.twoHanded(stack);
            check(h, out.is(twohand ? Items.CROSSBOW : Items.STICK), "Current incoming carrier identity");
            check(h, out.get(DataComponents.CUSTOM_MODEL_DATA).flags().equals(wireFlags(stack)),
                    "Wire flag0 represents incoming carrier, not outgoing default grip");
            check(h, twohand ? Objects.equals(out.get(DataComponents.CHARGED_PROJECTILES),
                    ChargedProjectiles.of(new ItemStackTemplate(Items.ARROW))) : !out.has(DataComponents.CHARGED_PROJECTILES),
                    "Existing crossbow heartbeat charge/native removal is exact");
            WeaponSwapPresentation.active(stack); WeaponSwapPresentation.model(stack); WeaponHandling.presentation(p);
        }
        check(h, ItemStack.matches(saved, stack), "Repeated queries and wire encoding never mutate authoritative components");
        check(h, Identifier.parse(entry(stack).item_model()).equals(stack.get(DataComponents.ITEM_MODEL)),
                "Authoritative model identity remains base model");
        return offset;
    }
    private static void preserved(GameTestHelper h, ItemStack stack, ItemStack original) {
        check(h, Objects.equals(stack.get(DataComponents.CUSTOM_DATA), original.get(DataComponents.CUSTOM_DATA))
                        && Objects.equals(stack.get(DataComponents.CHARGED_PROJECTILES), original.get(DataComponents.CHARGED_PROJECTILES))
                        && Objects.equals(stack.get(DataComponents.LORE), original.get(DataComponents.LORE)),
                "Exact ammunition/custom data, charged sentinel and lore survive presentation");
        var cmd = stack.get(DataComponents.CUSTOM_MODEL_DATA);
        var old = original.get(DataComponents.CUSTOM_MODEL_DATA);
        for (int i = 0; i < old.floats().size(); i++) if (i != 5)
            check(h, Objects.equals(cmd.getFloat(i), old.getFloat(i)), "Unowned float" + i + " preserved");
        check(h, cmd.flags().equals(old.flags()) && cmd.strings().equals(old.strings()) && cmd.colors().equals(old.colors()),
                "Unowned flags/strings/colors preserved");
    }
    private static void restored(GameTestHelper h, ItemStack stack) {
        check(h, !WeaponSwapPresentation.active(stack)
                && Objects.equals(stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(5), SENTINEL.getFloat(5)),
                "Retired exact binding restores original slot5");
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void bothDirectionsBothCarriersFollowExistingClockKeepExactAmmoHudAndChargedState(GameTestHelper h) {
        var pairs = new ArrayList<Pair>();
        for (String from : List.of("austringer", "beloved")) for (var grip : WeaponModels.Grip.values()) {
            var f = pair(h, from, grip); pairs.add(f);
            check(h, WeaponHandling.presentation(f.owner).isEmpty() && !WeaponSwapPresentation.active(f.outgoing),
                    "Initial observation is already equipped, with no manufactured swap");
            select(f.owner, f.targetSlot); active(h, f.owner, from, WeaponSwapCycle.Phase.STOW);
            check(h, f.incoming.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(5) < .001f,
                    "STOW starts at outgoing HIP sample plus cache offset");
        }
        var outgoing = pairs.stream().map(f -> f.outgoing.copy()).toList();
        var incoming = pairs.stream().map(f -> f.incoming.copy()).toList();
        var offsets = pairs.stream().map(f -> f.incoming.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(5)).toList();
        for (int i = 1; i <= 18; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                for (int j = 0; j < pairs.size(); j++) {
                    var f = pairs.get(j); var p = f.owner; tick(p);
                    int deadline = stow(f.outgoing) + ready(f.incoming);
                    if (elapsed < deadline) {
                        float offset = active(h, p, entry(f.outgoing).id(), elapsed < stow(f.outgoing) ? WeaponSwapCycle.Phase.STOW : WeaponSwapCycle.Phase.READY);
                        check(h, Math.abs(offset - offsets.get(j)) < .000001f, "Binding offset stays stable across both phases");
                        if (elapsed == stow(f.outgoing)) check(h, Math.abs(f.incoming.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(5)
                                - (2f + offsets.get(j))) < .000001f, "READY starts at incoming lowered sample plus same offset");
                        check(h, !WeaponRuntime.beginUse(p) && !WeaponRuntime.reload(p), "Existing Handling alone gates actual firing/reload");
                    } else {
                        restored(h, f.incoming);
                        check(h, WeaponHandling.presentation(p).isEmpty() && !WeaponHandling.blocked(p), "Existing deadline ends visual and gameplay block");
                        check(h, wire(p, f.incoming).get(DataComponents.ITEM_MODEL).equals(projected(f.incoming.get(DataComponents.ITEM_MODEL))),
                                "Finished incoming returns to exact original HIP item graph");
                    }
                    preserved(h, f.outgoing, outgoing.get(j)); preserved(h, f.incoming, incoming.get(j));
                    var hud = AmmoHud.current(p).orElseThrow(); CombatHud.update(p);
                    check(h, hud.rounds() == ammo(f.incoming).rounds() && hud.reserve() == ammo(f.incoming).reserve()
                                    && hud.family().equals(entry(f.incoming).family()) && !hud.reloading()
                                    && WeaponRuntime.activeProjectiles(p) == 0 && WeaponAiming.progress(p) == 0,
                            "HUD always describes selected incoming ammo, with no fake reload/shot/ADS");
                }
                if (elapsed == 18) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void sameTickRetargetAndBuildingDetourKeepOriginallyStowedEntryAndDeadline(GameTestHelper h) {
        var f = pair(h, "austringer", WeaponModels.Grip.TWO_HAND); var p = f.owner;
        p.getInventory().setItem(4, new ItemStack(Items.STONE));
        select(p, f.targetSlot); long deadline = WeaponHandling.remaining(p);
        select(p, slot(f.outgoing));
        check(h, WeaponHandling.presentation(p).isEmpty(), "Same-entry return is unsupported cosmetically while original stow remains");
        restored(h, f.incoming);
        select(p, 4); select(p, f.targetSlot);
        active(h, p, "austringer", WeaponSwapCycle.Phase.STOW);
        check(h, WeaponHandling.remaining(p) == deadline, "Same-tick detours retain original stow and latest incoming ready");
        h.runAfterDelay(3, () -> {
            tick(p); float progress = WeaponHandling.presentation(p).orElseThrow().progress();
            select(p, slot(f.outgoing)); select(p, f.targetSlot);
            active(h, p, "austringer", WeaponSwapCycle.Phase.STOW);
            check(h, WeaponHandling.presentation(p).orElseThrow().progress() == progress
                    && WeaponHandling.remaining(p) == deadline - 3, "Retarget preserves original stowAt and remaining time");
        });
        h.runAfterDelay(deadline, () -> { tick(p); restored(h, f.incoming); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void interruptingReadyStowsActualIncomingAndSkillSuspendCannotResetHandling(GameTestHelper h) {
        var f = pair(h, "austringer", WeaponModels.Grip.TWO_HAND); var p = f.owner;
        select(p, f.targetSlot);
        int interruptAt = stow(f.outgoing) + 1, duration = stow(f.incoming) + ready(f.outgoing);
        check(h, interruptAt + duration < 40, "Authored retarget deadline fits the test bound");
        h.runAfterDelay(interruptAt, () -> {
            tick(p); active(h, p, "austringer", WeaponSwapCycle.Phase.READY);
            select(p, slot(f.outgoing)); active(h, p, "beloved", WeaponSwapCycle.Phase.STOW);
            restored(h, f.incoming);
            long left = WeaponHandling.remaining(p);
            check(h, left == stow(f.incoming) + ready(f.outgoing), "Interrupted READY starts actual selected weapon's full stow");
            WeaponRuntime.cancelUseForSkill(p); WeaponAiming.suspend(p);
            active(h, p, "beloved", WeaponSwapCycle.Phase.STOW);
            check(h, WeaponHandling.remaining(p) == left, "Runtime cancel/ADS suspend preserves independent Handling and swap presentation");
        });
        h.runAfterDelay(interruptAt + duration - 1, () -> {
            tick(p);
            check(h, WeaponHandling.remaining(p) == 1, "Skill suspension cannot end the retargeted draw one tick early");
        });
        h.runAfterDelay(interruptAt + duration, () -> {
            tick(p); restored(h, f.outgoing);
            check(h, !WeaponHandling.blocked(p), "Retargeted handling finishes at its original exact deadline");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void currentStackLevelEligibilityAndCleanupAreCheckedByPureQueries(GameTestHelper h) {
        var f = pair(h, "austringer", WeaponModels.Grip.TWO_HAND); var p = f.owner;
        select(p, f.targetSlot); active(h, p, "austringer", WeaponSwapCycle.Phase.STOW);
        var copy = f.incoming.copy(); p.getInventory().setItem(f.targetSlot, copy);
        var saved = f.incoming.copy();
        check(h, !WeaponSwapPresentation.active(copy) && !WeaponSwapPresentation.active(f.incoming)
                && ItemStack.matches(saved, f.incoming), "Exact-stack mismatch rejects equal copy and donor without query mutation");
        p.getInventory().setItem(f.targetSlot, f.incoming);
        var other = java.util.stream.StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                .filter(level -> level != h.getLevel()).findFirst().orElseThrow();
        p.setServerLevel(other);
        check(h, !WeaponSwapPresentation.active(f.incoming), "Level mismatch immediately invalidates query");
        tick(p); restored(h, f.incoming); p.setServerLevel(h.getLevel());
        WeaponRuntime.cleanup(p); p.getInventory().setSelectedSlot(slot(f.outgoing)); tick(p);
        select(p, f.targetSlot);
        active(h, p, "austringer", WeaponSwapCycle.Phase.STOW);
        p.setGameMode(GameType.SPECTATOR);
        check(h, !WeaponSwapPresentation.active(f.incoming), "Spectator eligibility loses authorization before update");
        tick(p); restored(h, f.incoming); p.setGameMode(GameType.SURVIVAL);
        WeaponHandling.cleanup(p); tick(p); select(p, slot(f.outgoing));
        active(h, p, "beloved", WeaponSwapCycle.Phase.STOW);
        WeaponRuntime.cleanup(p); restored(h, f.outgoing);
        check(h, WeaponHandling.presentation(p).isEmpty(), "Production owner cleanup releases observation and model");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void exactStackRecipientKeepsOriginalSlotSnapshotThroughLateDonorCleanup(GameTestHelper h) {
        var donor = pair(h, "austringer", WeaponModels.Grip.TWO_HAND);
        var recipient = pair(h, "austringer", WeaponModels.Grip.TWO_HAND);
        // No shot/reload creates a donor Runtime.State, so its automatic iteration cannot
        // retire the binding before this deliberately late same-tick recipient handoff.
        float originalSelector = .0001f;
        var originalData = donor.incoming.get(DataComponents.CUSTOM_MODEL_DATA);
        var originalFloats = new ArrayList<>(originalData.floats()); originalFloats.set(5, originalSelector);
        donor.incoming.set(DataComponents.CUSTOM_MODEL_DATA,
                new CustomModelData(originalFloats, originalData.flags(), originalData.strings(), originalData.colors()));
        select(donor.owner, donor.targetSlot);
        var transferred = donor.incoming;
        float donorSample = transferred.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(5);
        var viewerContext = ((PacketContextProvider) (Object) donor.owner.connection).getPacketContext();
        float donorWireSample = PolymerItemUtils.getPolymerItemStack(transferred, viewerContext,
                donor.owner.level().registryAccess()).get(DataComponents.CUSTOM_MODEL_DATA).getFloat(5);
        donor.owner.getInventory().setItem(donor.targetSlot, ItemStack.EMPTY);
        recipient.owner.getInventory().setItem(recipient.targetSlot, transferred);
        select(recipient.owner, recipient.targetSlot);
        active(h, recipient.owner, "austringer", WeaponSwapCycle.Phase.STOW);
        float recipientSample = transferred.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(5);
        check(h, Float.compare(originalSelector, donorSample) != 0 && Float.compare(originalSelector, recipientSample) != 0
                        && Float.compare(donorSample, recipientSample) != 0 && Float.compare(donorWireSample, recipientSample) != 0
                        && Float.compare(PolymerItemUtils.getPolymerItemStack(transferred, viewerContext,
                        donor.owner.level().registryAccess()).get(DataComponents.CUSTOM_MODEL_DATA).getFloat(5), recipientSample) == 0,
                "Same-phase same-tick recipient invalidates prior donor sample and real viewer-context Polymer cache");
        var saved = transferred.copy();
        WeaponSwapPresentation.clear(donor.owner, transferred); WeaponHandling.cleanup(donor.owner); WeaponRuntime.cleanup(donor.owner);
        active(h, recipient.owner, "austringer", WeaponSwapCycle.Phase.STOW);
        check(h, ItemStack.matches(saved, transferred), "Late donor clears cannot overwrite recipient selector/component");
        // Other renderers can update any unowned field while slot5 remains bound.
        var d = transferred.get(DataComponents.CUSTOM_MODEL_DATA); var values = new ArrayList<>(d.floats());
        values.set(0, 1001f); values.set(6, 1006f); values.add(1008f);
        var latest = new CustomModelData(values, List.of(false, true), List.of("hip", "recipient"), List.of(0x654321));
        transferred.set(DataComponents.CUSTOM_MODEL_DATA, latest);
        WeaponRuntime.cleanup(recipient.owner);
        var restored = transferred.get(DataComponents.CUSTOM_MODEL_DATA);
        values.set(5, originalSelector);
        check(h, restored.equals(new CustomModelData(values, latest.flags(), latest.strings(), latest.colors())),
                "Recipient restores original pre-donor slot5 only, preserving all newer fields");
        WeaponRuntime.cleanup(recipient.owner);
        check(h, restored.equals(transferred.get(DataComponents.CUSTOM_MODEL_DATA)), "Cleanup is idempotent");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void persistedSelectorAndPreviewNeverAuthorizeSwapOrGameplay(GameTestHelper h) {
        var f = pair(h, "austringer", WeaponModels.Grip.TWO_HAND); select(f.owner, f.targetSlot);
        var ops = f.owner.registryAccess().createSerializationContext(NbtOps.INSTANCE);
        var saved = ItemStack.CODEC.parse(ops, ItemStack.CODEC.encodeStart(ops, f.incoming).getOrThrow()).getOrThrow();
        var preview = WeaponModels.create(entry("beloved"));
        preview.set(DataComponents.CUSTOM_MODEL_DATA, f.incoming.get(DataComponents.CUSTOM_MODEL_DATA));
        check(h, !WeaponSwapPresentation.active(saved) && !WeaponSwapPresentation.active(preview),
                "Real NBT codec selector and preview do not inherit live exact-stack ownership");
        check(h, wire(f.owner, saved).get(DataComponents.ITEM_MODEL).equals(projected(saved.get(DataComponents.ITEM_MODEL))),
                "Saved selector cannot route a swap item graph");
        f.owner.getInventory().setItem(f.targetSlot, saved); tick(f.owner);
        check(h, WeaponHandling.presentation(f.owner).isPresent() && WeaponSwapPresentation.active(saved),
                "A saved stack can render only after an actual eligible selection is observed");
        // The retained original stow is Austringer: this is still a distinct pair, but the
        // real Handling deadline is unchanged and the selector cannot grant an early shot.
        check(h, !WeaponRuntime.beginUse(f.owner) && ammo(saved).rounds() == 2, "Live rendering gives no gameplay rights");
        f.owner.getInventory().setItem(f.targetSlot, preview); tick(f.owner);
        check(h, WeaponHandling.presentation(f.owner).isEmpty() && !WeaponSwapPresentation.active(preview)
                        && !WeaponRuntime.beginUse(f.owner), "Preview stays noncombat even in selected slot");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void savedFirstSampleAndFuturePhaseCollisionsInvalidateRealPolymerContextCache(GameTestHelper h) {
        for (float original : List.of(0f, .0001f, 2f + 1f / 20 + .0001f)) {
            var f = pair(h, "austringer", WeaponModels.Grip.TWO_HAND);
            var d = f.incoming.get(DataComponents.CUSTOM_MODEL_DATA); var floats = new ArrayList<>(d.floats());
            floats.set(5, original);
            f.incoming.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(floats, d.flags(), d.strings(), d.colors()));
            var context = ((PacketContextProvider) (Object) f.owner.connection).getPacketContext();
            // Prime the actual Polymer path on this very stack/context before a live binding.
            var before = f.incoming.copy();
            check(h, PolymerItemUtils.getPolymerItemStack(f.incoming, context, f.owner.level().registryAccess())
                    .get(DataComponents.ITEM_MODEL).equals(projected(f.incoming.get(DataComponents.ITEM_MODEL))), "Saved CMD primes only original model");
            select(f.owner, f.targetSlot);
            float offset = active(h, f.owner, "austringer", WeaponSwapCycle.Phase.STOW);
            check(h, !ItemStack.matches(before, f.incoming), "Binding changes actual components even when original selector is sample zero");
            for (int phase = 0; phase < 2; phase++) for (int sample = 0; sample <= 20; sample++)
                check(h, Float.compare(original, phase * 2 + (float) sample / 20 + offset) != 0,
                        "Offset avoids saved selector across all 42 phase samples");
            var after = PolymerItemUtils.getPolymerItemStack(f.incoming, context, f.owner.level().registryAccess());
            check(h, after.get(DataComponents.ITEM_MODEL).equals(projected(Identifier.parse("destiny:weapon_swap_w91/austringer_to_beloved")))
                            && Float.compare(after.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(5),
                            f.incoming.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(5)) == 0,
                    "Same fake packet context sees new swap route and new sample after cache invalidation");
            WeaponRuntime.cleanup(f.owner);
            check(h, Objects.equals(f.incoming.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(5), original)
                            && PolymerItemUtils.getPolymerItemStack(f.incoming, context, f.owner.level().registryAccess())
                            .get(DataComponents.ITEM_MODEL).equals(projected(f.incoming.get(DataComponents.ITEM_MODEL))),
                    "Cleanup restores exact saved selector and evicts cached live model route");
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void absentSlotCleanupPreservesLowerPaddingAndNewHigherSelector(GameTestHelper h) {
        var f = pair(h, "austringer", WeaponModels.Grip.TWO_HAND);
        var shortPair = pair(h, "austringer", WeaponModels.Grip.NATIVE);
        var original = new CustomModelData(List.of(7f), SENTINEL.flags(), SENTINEL.strings(), SENTINEL.colors());
        f.incoming.set(DataComponents.CUSTOM_MODEL_DATA, original);
        shortPair.incoming.set(DataComponents.CUSTOM_MODEL_DATA, original);
        select(shortPair.owner, shortPair.targetSlot);
        active(h, shortPair.owner, "austringer", WeaponSwapCycle.Phase.STOW);
        WeaponRuntime.cleanup(shortPair.owner);
        check(h, shortPair.incoming.get(DataComponents.CUSTOM_MODEL_DATA).floats().equals(List.of(7f, 0f, 0f, 0f, 0f)),
                "An absent trailing slot5 is removed without restoring or trimming unowned lower slots");
        select(f.owner, f.targetSlot); active(h, f.owner, "austringer", WeaponSwapCycle.Phase.STOW);
        var d = f.incoming.get(DataComponents.CUSTOM_MODEL_DATA); var values = new ArrayList<>(d.floats());
        values.set(4, 404f); values.add(606f);
        f.incoming.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(values, d.flags(), d.strings(), d.colors()));
        WeaponRuntime.cleanup(f.owner);
        var restored = f.incoming.get(DataComponents.CUSTOM_MODEL_DATA);
        check(h, restored.floats().equals(List.of(7f, 0f, 0f, 0f, 404f, 0f, 606f))
                        && restored.flags().equals(original.flags()) && restored.strings().equals(original.strings())
                        && restored.colors().equals(original.colors()),
                "Absent slot5 becomes neutral while newer lower/higher fields retain indices and values");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void superAndDeathSuspendCosmeticsWithoutExtendingOrGrantingTheExistingDeadline(GameTestHelper h) {
        var superPair = pair(h, "austringer", WeaponModels.Grip.TWO_HAND);
        var dyingPair = pair(h, "austringer", WeaponModels.Grip.TWO_HAND);
        for (var f : List.of(superPair, dyingPair)) select(f.owner, f.targetSlot);
        AbilityService.startSuper(superPair.owner, new SuperSession() {
            public boolean tick() { return true; }
            public void primary() {}
            public void end() {}
            public float remaining() { return 1; }
        });
        check(h, AbilityService.inSuper(superPair.owner) && !WeaponSwapPresentation.active(superPair.incoming),
                "Production super session immediately suspends ordinary swap model authorization");
        tick(superPair.owner); restored(h, superPair.incoming);
        AbilityService.endSuper(superPair.owner); tick(superPair.owner);
        dyingPair.owner.setHealth(0);
        check(h, !WeaponSwapPresentation.active(dyingPair.incoming), "Dead owner immediately loses presentation authorization");
        tick(dyingPair.owner); restored(h, dyingPair.incoming);
        dyingPair.owner.setHealth(20); tick(dyingPair.owner);
        for (var f : List.of(superPair, dyingPair))
            check(h, !WeaponRuntime.beginUse(f.owner) && ammo(f.incoming).rounds() == 2,
                    "Transient ineligibility grants neither paid shot nor ammo");
        h.runAfterDelay(stow(superPair.outgoing) + ready(superPair.incoming), () -> {
            for (var f : List.of(superPair, dyingPair)) {
                tick(f.owner); restored(h, f.incoming);
                check(h, !WeaponHandling.blocked(f.owner) && ammo(f.incoming).rounds() == 2
                        && WeaponRuntime.activeProjectiles(f.owner) == 0, "Deadline is never extended and expiration never synthesizes input");
            }
            h.succeed();
        });
    }
}
