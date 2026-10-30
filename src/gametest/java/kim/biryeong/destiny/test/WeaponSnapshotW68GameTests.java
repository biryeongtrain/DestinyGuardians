package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponScopeHud;
import kim.biryeong.destiny.hud.WeaponReticleHud;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.camera.api.CameraEffects;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import kim.biryeong.minigamelib.shaderfx.impl.ModConfig;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

/** W68 real ServerPlayer/production-runtime tests, driven on delayed server ticks.
 * Literal sockets were independently enumerated from cached W30 Bungie items and W60 plug sets
 * at the exact W40 item hashes. Fifteen official rows include TWO unsupported Heavy rows.
 * Literal timing rows come from W44 raw seconds, scaling BEFORE ceil(seconds * 20).
 * Policy: Primary .5, Special .8; historical official 2022 .75 conflicts with the pinned
 * source-tier policy and is not silently substituted. Enhanced 4116820839 is excluded.
 * Only the last test toggles the shader flag or asserts FOV; every toggle restores in finally.
 * These assert server selectors, real DisplayHud nodes and the FOV API, not native rendering/audio.
 * Registration is intentionally left to the coordinating agent.
 */
public final class WeaponSnapshotW68GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String SNAPSHOT = "snapshot_sights";
    private static final long HASH = 957782887L;
    private static final long ENHANCED = 4116820839L;
    private static final Set<WeaponPerks.Roll> ROWS = Set.of(
            new WeaponPerks.Roll("austringer", 3055790362L, 3, 957782887L, 2750499928L),
            new WeaponPerks.Roll("blast_furnace", 3843477312L, 3, 957782887L, 1976101165L),
            new WeaponPerks.Roll("claws_of_the_wolf", 1280933460L, 3, 957782887L, 206409262L),
            new WeaponPerks.Roll("high_albedo", 1197486957L, 4, 957782887L, 718633408L),
            new WeaponPerks.Roll("biting_winds", 1621657423L, 4, 957782887L, 2763203653L),
            new WeaponPerks.Roll("bite_of_the_fox", 1403800851L, 3, 957782887L, 563442205L),
            new WeaponPerks.Roll("beloved", 3107853529L, 3, 957782887L, 1196545279L),
            new WeaponPerks.Roll("apostate", 2164448701L, 4, 957782887L, 2826016044L),
            new WeaponPerks.Roll("mindbender_s_ambition_adept", 912150785L, 3, 957782887L, 1732284294L),
            new WeaponPerks.Roll("dust_rock_blues", 636912560L, 4, 957782887L, 1624251370L),
            new WeaponPerks.Roll("parcel_of_stardust_fell_to_earth", 2217366863L, 3, 957782887L, 2514419370L),
            new WeaponPerks.Roll("dream_breaker", 2931957300L, 3, 957782887L, 3785896921L),
            new WeaponPerks.Roll("deafening_whisper", 981718087L, 4, 957782887L, 3588287812L));
    // Official availability is distinct from supported runtime policy: no measured Heavy scalar.
    private static final Set<WeaponPerks.Roll> HEAVY_OFFICIAL = Set.of(
            new WeaponPerks.Roll("edge_transit", 218335759L, 3, 957782887L, 447678063L),
            new WeaponPerks.Roll("bad_omens", 991314988L, 3, 957782887L, 457210958L));
    private static final List<SnapshotAimProfile.Timing> TIMINGS = List.of(
            new SnapshotAimProfile.Timing("duke_mk_44", 6, 3, 1, 0.28166666669),
            new SnapshotAimProfile.Timing("austringer", 6, 3, 1, 0.253333333351),
            new SnapshotAimProfile.Timing("seventh_seraph_officer_revolver", 6, 3, 1, 0.28166666669),
            new SnapshotAimProfile.Timing("halfdan_d", 7, 4, 1, 0.316625),
            new SnapshotAimProfile.Timing("ammit_ar2", 7, 4, 1, 0.3035),
            new SnapshotAimProfile.Timing("gnawing_hunger", 6, 3, 1, 0.271625),
            new SnapshotAimProfile.Timing("steelfeather_repeater", 7, 4, 1, 0.3185),
            new SnapshotAimProfile.Timing("cold_denial", 9, 5, 1, 0.41037878),
            new SnapshotAimProfile.Timing("bygones", 8, 4, 1, 0.36721302),
            new SnapshotAimProfile.Timing("chattering_bone", 7, 4, 1, 0.3201231),
            new SnapshotAimProfile.Timing("blast_furnace", 9, 5, 1, 0.41037878),
            new SnapshotAimProfile.Timing("claws_of_the_wolf", 9, 5, 1, 0.41626502),
            new SnapshotAimProfile.Timing("frontier_justice", 8, 4, 1, 0.37077895195599997),
            new SnapshotAimProfile.Timing("distant_relation", 7, 4, 1, 0.34368251866),
            new SnapshotAimProfile.Timing("patron_of_lost_causes", 7, 4, 1, 0.304731395797),
            new SnapshotAimProfile.Timing("aishas_embrace", 8, 4, 1, 0.367391897794),
            new SnapshotAimProfile.Timing("long_arm", 7, 4, 1, 0.321666666607),
            new SnapshotAimProfile.Timing("antiope_d", 7, 4, 1, 0.324440027404),
            new SnapshotAimProfile.Timing("bug_out_bag", 6, 3, 1, 0.270117203566),
            new SnapshotAimProfile.Timing("ikelos_smg_v1_0_1", 5, 3, 1, 0.22703358466),
            new SnapshotAimProfile.Timing("the_recluse", 5, 3, 1, 0.24014599041400003),
            new SnapshotAimProfile.Timing("allied_demand", 5, 3, 1, 0.23656868149999996),
            new SnapshotAimProfile.Timing("farewell", 5, 3, 1, 0.20089835189999997),
            new SnapshotAimProfile.Timing("lonesome", 6, 3, 1, 0.27000961549999997),
            new SnapshotAimProfile.Timing("dead_man_walking_xx7463", 5, 3, 1, 0.23433928589999997),
            new SnapshotAimProfile.Timing("high_albedo", 5, 3, 1, 0.22988049469999997),
            new SnapshotAimProfile.Timing("brass_attacks", 6, 3, 1, 0.26332142869999997),
            new SnapshotAimProfile.Timing("biting_winds", 9, 5, 1, 0.43845057734899995),
            new SnapshotAimProfile.Timing("whispering_slab", 9, 5, 1, 0.408760046165),
            new SnapshotAimProfile.Timing("bite_of_the_fox", 10, 8, 2, 0.45338293215),
            new SnapshotAimProfile.Timing("beloved", 9, 7, 2, 0.41048327600999995),
            new SnapshotAimProfile.Timing("apostate", 8, 7, 2, 0.37538355734999995),
            new SnapshotAimProfile.Timing("mindbender_s_ambition_adept", 8, 7, 2, 0.37871457492),
            new SnapshotAimProfile.Timing("dust_rock_blues", 8, 6, 2, 0.37170040488),
            new SnapshotAimProfile.Timing("first_in_last_out", 7, 5, 2, 0.31091093119999996),
            new SnapshotAimProfile.Timing("parcel_of_stardust_fell_to_earth", 6, 5, 2, 0.29220647775999997),
            new SnapshotAimProfile.Timing("ikelos_sg_v1_0_1", 7, 6, 2, 0.34831983808),
            new SnapshotAimProfile.Timing("erentil_fr4", 8, 7, 2, 0.380745672396),
            new SnapshotAimProfile.Timing("hollow_words", 8, 6, 2, 0.37227696400599997),
            new SnapshotAimProfile.Timing("dream_breaker", 8, 6, 2, 0.365501997294),
            new SnapshotAimProfile.Timing("null_composure", 7, 6, 2, 0.316383488632),
            new SnapshotAimProfile.Timing("coriolis_force", 8, 6, 2, 0.367195738972),
            new SnapshotAimProfile.Timing("line_in_the_sand", 8, 8, 3, 0.367195738972),
            new SnapshotAimProfile.Timing("stormchaser", 8, 8, 3, 0.36042077226),
            new SnapshotAimProfile.Timing("retraced_path", 7, 5, 2, 0.3035),
            new SnapshotAimProfile.Timing("salvager_s_salvo", 8, 6, 2, 0.36924088),
            new SnapshotAimProfile.Timing("deafening_whisper", 8, 6, 2, 0.36549944),
            new SnapshotAimProfile.Timing("edge_transit", 9, 9, 3, 0.42162104),
            new SnapshotAimProfile.Timing("canis_major", 10, 10, 3, 0.46277688),
            new SnapshotAimProfile.Timing("dimensional_hypotrochoid", 9, 9, 3, 0.42162104),
            new SnapshotAimProfile.Timing("bad_omens", 10, 10, 3, 0.48619899248),
            new SnapshotAimProfile.Timing("bellowing_giant", 9, 9, 3, 0.43485678305599995),
            new SnapshotAimProfile.Timing("code_duello", 8, 8, 3, 0.38137531490599996),
            new SnapshotAimProfile.Timing("pyroclastic_flow", 9, 9, 3, 0.44127455923399994),
            new SnapshotAimProfile.Timing("fixed_odds", 9, 9, 3, 0.42043437659),
            new SnapshotAimProfile.Timing("hammerhead", 8, 8, 3, 0.39574482585000004),
            new SnapshotAimProfile.Timing("retrofit_escapade", 8, 8, 3, 0.388337960628));

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static void near(GameTestHelper h, float actual, float expected, String message) {
        check(h, Math.abs(actual - expected) < .00001f, message + ": expected " + expected + ", got " + actual);
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static SnapshotAimProfile.Timing timing(String id) {
        return TIMINGS.stream().filter(t -> t.id().equals(id)).findFirst().orElseThrow();
    }
    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()));
    }
    private static int slot(ItemStack stack) {
        return WeaponCharacteristics.of(WeaponItems.entry(stack).orElseThrow()).slot().hotbar();
    }
    private static String pose(ItemStack stack) {
        var data = stack.get(DataComponents.CUSTOM_MODEL_DATA);
        return data == null ? null : data.getString(0);
    }
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), -90, -80);
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.EMERALD, 4));
        TestCleanup.register(h, () -> {
            p.setServerLevel(h.getLevel());
            WeaponRuntime.cleanup(p);
            WeaponScopeHud.remove(p);
            CombatHud.remove(p);
            for (String id : List.copyOf(DisplayHud.getHuds(p).keySet())) DisplayHud.removeHud(p, id);
            CameraEffects.resetFov(p);
            TestPlayers.remove(p);
        });
        return p;
    }
    private static ItemStack equip(GameTestHelper h, ServerPlayer p, String id, boolean selected) {
        var stack = WeaponItems.create(entry(id));
        p.getInventory().setItem(slot(stack), stack);
        p.getInventory().setSelectedSlot(slot(stack));
        if (selected) check(h, command(h, p, "select " + SNAPSHOT) == 1, "Real player selects " + id);
        tick(p);
        return stack;
    }
    private static int command(GameTestHelper h, ServerPlayer p, String tail) {
        try {
            return h.getLevel().getServer().getCommands().getDispatcher()
                    .execute("destiny perk " + tail, p.createCommandSourceStack());
        } catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) {
            throw new AssertionError("Registered owned-stack perk command: " + tail, e);
        }
    }
    private static void tick(ServerPlayer p) {
        // TestPlayers are not in the server player list. Never fabricate a clock or aim state.
        WeaponRuntime.tickPlayer(p);
        CombatHud.update(p);
        TestPlayers.drain(p);
    }
    private static ItemStack withoutTraits(ItemStack stack) {
        var copy = stack.copy();
        var tag = copy.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.remove(WeaponPerks.SLOTS_KEY); tag.remove(WeaponPerks.HASH_KEY); tag.remove(WeaponPerks.SOCKET_KEY);
        copy.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        return copy;
    }
    private static void edit(GameTestHelper h, ServerPlayer p, String tail) {
        var stack = p.getMainHandItem(); var before = withoutTraits(stack);
        float progress = WeaponAiming.progress(p); long handling = WeaponHandling.remaining(p);
        check(h, command(h, p, tail) == 1, "Actual edit " + tail);
        check(h, p.getMainHandItem() == stack && ItemStack.matches(before, withoutTraits(stack)),
                "Edit retains identity, ammo, lore, grip, model and every non-trait component");
        near(h, WeaponAiming.progress(p), progress, "Edit has no immediate ADS jump/reset");
        check(h, WeaponHandling.remaining(p) == handling, "Edit preserves existing handling deadline");
    }
    private static void forged(ItemStack stack, int socket, long hash) {
        var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        var sockets = new CompoundTag(); sockets.putLong(Integer.toString(socket), hash);
        tag.put(WeaponPerks.SLOTS_KEY, sockets); stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
    }
    private static void absent(GameTestHelper h, ServerPlayer p) {
        check(h, !WeaponAiming.scoped(p) && DisplayHud.getHuds(p).keySet().stream()
                .noneMatch(id -> id.startsWith(WeaponScopeHud.PREFIX)), "No authorized scope or stale scope nodes");
    }
    private static void scoped(GameTestHelper h, ServerPlayer p) {
        check(h, WeaponAiming.scoped(p) && "scope".equals(pose(p.getMainHandItem())), "Actual scoped selector/session");
        String id = WeaponItems.entry(p.getMainHandItem()).orElseThrow().id();
        for (String nodeId : List.of(WeaponScopeHud.CENTER_ID, WeaponScopeHud.FRAME_ID)) {
            var node = DisplayHud.getHud(p, nodeId);
            check(h, node instanceof ItemDisplayHud && !node.isRemoved(), "Real live scope node " + nodeId);
            var item = (ItemDisplayHud) node;
            boolean center = nodeId.equals(WeaponScopeHud.CENTER_ID);
            check(h, Identifier.fromNamespaceAndPath("destiny", "gui/hud/scope_w45_" + id
                            + (center ? "_reticle" : "_frame")).equals(item.getItem().get(DataComponents.ITEM_MODEL)),
                    "Actual node uses this weapon's scope sprite");
            check(h, node.isAboveHand() == center && node.getLocation().z() == (center ? 6 : 0)
                            && node.getAlignment() == DisplayHud.HudAlignment.CENTER
                            && node.getLocation().x() == 960 && node.getLocation().y() == 540,
                    "Real centered frame/center nodes keep their distinct depths");
        }
        check(h, DisplayHud.getHuds(p).keySet().stream().filter(id2 -> id2.startsWith(WeaponScopeHud.PREFIX)).count() == 2
                        && DisplayHud.getHuds(p).keySet().stream().noneMatch(id2 -> id2.startsWith(WeaponReticleHud.PREFIX)),
                "Exactly two sniper scope nodes and no duplicate generic sight");
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void exactThirteenSelectableOfficialRowsAndTwoHeavyExclusionsAcrossAll63Commands(GameTestHelper h) {
        WeaponModelGameTests.assertCatalogExpansion(h);
        check(h, SnapshotAimProfile.ID.equals(SNAPSHOT) && SnapshotAimProfile.HASH == HASH
                        && WeaponCatalog.all().size() == 65 && SnapshotAimProfile.rolls().size() == 13
                        && Set.copyOf(SnapshotAimProfile.rolls()).equals(ROWS)
                        && ROWS.size() + HEAVY_OFFICIAL.size() == 15, "Independent complete official/subset contract");
        var p = player(h); int allowed = 0, heavyDenied = 0;
        for (var e : WeaponCatalog.all()) {
            p.getInventory().clearContent(); var stack = equip(h, p, e.id(), false); var before = stack.copy();
            var expected = ROWS.stream().filter(r -> r.id().equals(e.id())).toList();
            check(h, WeaponPerks.available(stack, SNAPSHOT).equals(expected)
                            && WeaponPerks.selected(stack, SNAPSHOT).isEmpty(), "Exact socket availability/no default: " + e.id());
            check(h, command(h, p, "list") == 1 && command(h, p, "status") == 1
                            && ItemStack.matches(before, stack), "Real read-only list/status: " + e.id());
            boolean legal = !expected.isEmpty();
            check(h, command(h, p, "select " + SNAPSHOT) == (legal ? 1 : 0), "All-65 actual command allow/deny: " + e.id());
            if (legal) {
                allowed++;
                check(h, WeaponPerks.selected(stack, SNAPSHOT).orElseThrow().equals(expected.getFirst())
                                && SnapshotAimProfile.enterTicks(stack) == timing(e.id()).snapshotTicks(), "Exact selected official row");
                var selected = stack.copy();
                check(h, command(h, p, "select " + SNAPSHOT) == 1 && ItemStack.matches(selected, stack), "Idempotent real select");
                check(h, command(h, p, "clear") == 1 && ItemStack.matches(before, stack), "Clear returns every original component");
            } else {
                check(h, ItemStack.matches(before, stack) && WeaponPerks.selected(stack, SNAPSHOT).isEmpty(),
                        "Rejected trait grants no ammo/components: " + e.id());
                if (HEAVY_OFFICIAL.stream().anyMatch(r -> r.id().equals(e.id()))) {
                    heavyDenied++;
                    check(h, WeaponCharacteristics.of(e).ammo() == WeaponAmmoType.HEAVY
                                    && SnapshotAimProfile.enterTicks(stack) == timing(e.id()).baseTicks(),
                            "Official Heavy socket is explicitly unsupported and retains base ADS");
                }
            }
        }
        check(h, allowed == 13 && heavyDenied == 2, "Exactly 13 supported selections and both official Heavy denials");
        p.setItemInHand(InteractionHand.MAIN_HAND, WeaponModels.create(entry("beloved")));
        var preview = p.getMainHandItem().copy();
        check(h, command(h, p, "select " + SNAPSHOT) == 0 && ItemStack.matches(preview, p.getMainHandItem()),
                "Inert preview cannot select runtime Snapshot");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void literal57RawTimingRowsAndForgedEnhancedWrongSocketOrHeavyNeverAccelerate(GameTestHelper h) {
        check(h, TIMINGS.size() == 57 && TIMINGS.stream().map(SnapshotAimProfile.Timing::id).distinct().count() == 57,
                "Complete independent W44 ranged timing contract");
        check(h, WeaponModelGameTests.originalW30Entries().stream().filter(WeaponAimProfile::supports).map(WeaponCatalog.Entry::id)
                        .collect(Collectors.toSet()).equals(TIMINGS.stream().map(SnapshotAimProfile.Timing::id).collect(Collectors.toSet())),
                "57 ranged and six excluded sword/glaive entries");
        for (var expected : TIMINGS) {
            check(h, SnapshotAimProfile.timing(entry(expected.id())).equals(expected), "Literal raw/base/Snapshot/ammo tuple: " + expected.id());
            var stack = WeaponItems.create(entry(expected.id())); var saved = stack.copy();
            for (int i = 0; i < 4; i++) check(h, SnapshotAimProfile.enterTicks(stack) == expected.baseTicks(), "Unselected base entry");
            check(h, ItemStack.matches(saved, stack), "Timing/selection reads are pure");
        }
        check(h, timing("austringer").snapshotTicks() == 3 && timing("beloved").baseTicks() == 9
                        && timing("beloved").snapshotTicks() == 7 && timing("dust_rock_blues").snapshotTicks() == 6,
                "Pre-ceiling Primary .5 and Special .8; never scale the already-ceiled base ticks");
        var players = new ArrayList<ServerPlayer>(); var durations = new ArrayList<Integer>();
        for (int kind = 0; kind < 8; kind++) {
            String id = kind == 5 ? "duke_mk_44" : kind == 6 ? "edge_transit" : kind == 7 ? "bad_omens" : "beloved";
            var p = player(h); var stack = equip(h, p, id, false);
            forged(stack, kind == 1 ? 4 : 3, kind == 0 ? ENHANCED : HASH);
            if (kind >= 2 && kind <= 4) {
                var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
                if (kind == 2) { var sockets = new CompoundTag(); sockets.putDouble("3", (double)HASH);
                    tag.put(WeaponPerks.SLOTS_KEY, sockets); }
                if (kind == 3) tag.putString(WeaponPerks.SLOTS_KEY, "3:957782887");
                if (kind == 4) { tag.remove(WeaponPerks.SLOTS_KEY); tag.putLong(WeaponPerks.SOCKET_KEY, 3L);
                    tag.putLong(WeaponPerks.HASH_KEY, HASH); }
                stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
            }
            var saved = stack.copy();
            check(h, WeaponPerks.selected(stack, SNAPSHOT).isEmpty() && SnapshotAimProfile.enterTicks(stack) == timing(id).baseTicks()
                            && ItemStack.matches(saved, stack), "Strict exact weapon/socket/LongTag selection, case " + kind);
            ads(p, true); players.add(p); durations.add(timing(id).baseTicks());
        }
        for (int i = 1; i <= 10; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                for (int j = 0; j < players.size(); j++) {
                    var p = players.get(j); tick(p);
                    near(h, WeaponAiming.progress(p), Math.min(1f, elapsed / (float)WeaponAiming.fast(durations.get(j))), "Forged selection uses actual base crouch timing");
                    check(h, WeaponPerks.selected(p.getMainHandItem(), SNAPSHOT).isEmpty(), "Runtime never blesses forged selection");
                }
                if (elapsed == 10) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void realPrimaryAndSpecialCrouchAcceleratesEntryButReleaseKeepsBaseExit(GameTestHelper h) {
        var players = new ArrayList<ServerPlayer>();
        for (String id : List.of("austringer", "beloved")) for (boolean selected : List.of(true, false)) {
            var p = player(h); equip(h, p, id, selected); ads(p, true); players.add(p);
        }
        int[] enters = {3, 6, 7, 9}; int[] exits = {6, 6, 9, 9};
        for (int i = 1; i <= 10; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                for (int j = 0; j < players.size(); j++) {
                    var p = players.get(j); tick(p);
                    near(h, WeaponAiming.progress(p), Math.min(1f, elapsed / (float)WeaponAiming.fast(enters[j])), "Actual selected/unselected crouch entry " + j);
                    check(h, !WeaponRuntime.reloading(p), "Crouch never starts reload");
                }
                if (elapsed == 10) for (var p : players) ads(p, false);
            });
        }
        for (int i = 1; i <= 10; i++) {
            int elapsed = i;
            h.runAfterDelay(10 + i, () -> {
                for (int j = 0; j < players.size(); j++) {
                    var p = players.get(j); tick(p);
                    near(h, WeaponAiming.progress(p), Math.max(0f, 1 - elapsed / (float)WeaponAiming.fast(exits[j])), "Actual release retains base exit " + j);
                }
                if (elapsed == 10) {
                    for (var p : players) { absent(h, p); check(h, "hip".equals(pose(p.getMainHandItem())), "Release restores hip selector"); }
                    h.succeed();
                }
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void exactHalfProgressChangesRealSelectorAndBothScopeHudNodes(GameTestHelper h) {
        var fast = player(h); var normal = player(h);
        var fastStack = equip(h, fast, "bite_of_the_fox", true);
        var normalStack = equip(h, normal, "bite_of_the_fox", false);
        var fastSaved = fastStack.copy(); var normalSaved = normalStack.copy();
        for (var p : List.of(fast, normal)) { absent(h, p); ads(p, true); }
        for (int i = 1; i <= 11; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                for (var p : List.of(fast, normal)) {
                    tick(p); boolean half = WeaponAiming.progress(p) >= .5f;
                    near(h, WeaponAiming.progress(p), Math.min(1f, elapsed / (float)WeaponAiming.fast(
                            p == fast ? SnapshotAimProfile.enterTicks(fastStack) : SnapshotAimProfile.enterTicks(normalStack))), "Real accelerated entry progress");
                    check(h, (half ? "scope" : "hip").equals(pose(p.getMainHandItem())), "Selector changes at half, not only at full ADS");
                    if (half) scoped(h, p); else absent(h, p);
                }
                // W277: faster ADS moves the exact crossing tick; assert the ordering wherever it occurs.
                if (WeaponAiming.progress(fast) >= .5f && WeaponAiming.progress(normal) < .5f)
                    check(h, WeaponAiming.scoped(fast) && !WeaponAiming.scoped(normal), "Snapshot scopes before the unselected sniper");
                if (elapsed == 11) {
                    var center = DisplayHud.getHud(fast, WeaponScopeHud.CENTER_ID);
                    var frame = DisplayHud.getHud(fast, WeaponScopeHud.FRAME_ID);
                    var saved = fastStack.copy();
                    for (int n = 0; n < 4; n++) CombatHud.update(fast);
                    check(h, DisplayHud.getHud(fast, WeaponScopeHud.CENTER_ID) == center
                                    && DisplayHud.getHud(fast, WeaponScopeHud.FRAME_ID) == frame && ItemStack.matches(saved, fastStack),
                            "Repeated real HUD updates reuse nodes and preserve all weapon components");
                    ads(fast, false); ads(normal, false);
                }
            });
        }
        for (int i = 1; i <= 11; i++) h.runAfterDelay(11 + i, () -> { tick(fast); tick(normal); });
        h.runAfterDelay(23, () -> {
            absent(h, fast); absent(h, normal);
            check(h, ItemStack.matches(fastSaved, fastStack) && ItemStack.matches(normalSaved, normalStack)
                            && fast.getOffhandItem().is(Items.EMERALD) && fast.getOffhandItem().getCount() == 4,
                    "Full aim/release/HUD cycle preserves serialized selection, ammunition, identity and offhand");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void actualMidAdsCommandsKeepProgressAmmoCadenceHandlingAndExactSocketRules(GameTestHelper h) {
        var p = player(h); var stack = equip(h, p, "austringer", false);
        check(h, WeaponProfile.forEntry(entry("austringer")).infiniteReserve(), "Primary reserve is infinite, not a finite nine-round pool");
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry("austringer")), 7, 0));
        edit(h, p, "select rampage");
        check(h, WeaponPerks.selected(stack, "rampage").orElseThrow().equals(
                new WeaponPerks.Roll("austringer", 3055790362L, 4, 3425386926L, 785215120L)), "Independent official Rampage socket 4");
        check(h, WeaponRuntime.beginUse(p) && ammo(stack).rounds() == 6, "Real first shot spends one round");
        WeaponRuntime.releaseUse(p, stack); ads(p, true);
        var handling = player(h); equip(h, handling, "beloved", false);
        var incoming = WeaponItems.create(entry("austringer"));
        handling.getInventory().setItem(0, incoming);
        handling.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0)); tick(handling);
        check(h, WeaponHandling.remaining(handling) == 14, "Real native slot change has seven stow plus seven ready ticks");
        edit(h, handling, "select " + SNAPSHOT);
        for (int i = 1; i <= 14; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                tick(p); tick(handling);
                if (elapsed == 1) {
                    near(h, WeaponAiming.progress(p), 1f / WeaponAiming.fast(6), "One unselected ADS tick");
                    edit(h, p, "select " + SNAPSHOT);
                    check(h, WeaponPerks.selected(stack, SNAPSHOT).orElseThrow().equals(
                                    new WeaponPerks.Roll("austringer", 3055790362L, 3, HASH, 2750499928L))
                                    && WeaponPerks.selected(stack, "rampage").isPresent(), "Snapshot 3 coexists with Rampage 4");
                    float before = WeaponAiming.progress(p); WeaponAiming.tick(p);
                    near(h, WeaponAiming.progress(p), before, "Repeated same-server-tick runtime call cannot jump ADS");
                    edit(h, handling, "clear"); edit(h, handling, "select " + SNAPSHOT);
                }
                if (elapsed == 2) {
                    near(h, WeaponAiming.progress(p), Math.min(1f, 1f / WeaponAiming.fast(6) + 1f / WeaponAiming.fast(3)), "Next real tick uses newly selected three-tick entry rate");
                    edit(h, p, "select outlaw");
                    check(h, WeaponPerks.selected(stack, SNAPSHOT).isEmpty()
                                    && WeaponPerks.selected(stack, "outlaw").orElseThrow().equals(
                                    new WeaponPerks.Roll("austringer", 3055790362L, 3, 1168162263L, 2750499928L))
                                    && WeaponPerks.selected(stack, "rampage").isPresent(), "Same socket replaces only Snapshot");
                }
                if (elapsed == 3) {
                    near(h, WeaponAiming.progress(p), Math.min(1f, 1f / WeaponAiming.fast(6) + 1f / WeaponAiming.fast(3) + 1f / WeaponAiming.fast(6)), "Next tick returns to base rate without resetting existing progress");
                    edit(h, p, "select " + SNAPSHOT); edit(h, p, "select " + SNAPSHOT);
                    check(h, WeaponPerks.selected(stack, "outlaw").isEmpty(), "Snapshot replaces same-socket Outlaw");
                }
                if (elapsed == 4) { near(h, WeaponAiming.progress(p), 1, "Selected next tick reaches full ADS"); edit(h, p, "clear"); }
                if (elapsed < 9) {
                    check(h, !WeaponRuntime.beginUse(p) && ammo(stack).rounds() == 6 && ammo(stack).reserve() == 0,
                            "Real trigger remains blocked by original nine-tick cadence despite edits");
                    WeaponRuntime.releaseUse(p, stack);
                }
                if (elapsed == 9) {
                    check(h, WeaponRuntime.beginUse(p) && ammo(stack).rounds() == 5 && ammo(stack).reserve() == 0,
                            "Original cadence deadline accepts exactly one next paid shot"); WeaponRuntime.releaseUse(p, stack);
                }
                check(h, WeaponHandling.remaining(handling) == Math.max(0, 14 - elapsed), "Commands never shorten or restart real handling");
                if (elapsed == 14) {
                    int before = ammo(incoming).rounds();
                    check(h, WeaponRuntime.beginUse(handling) && ammo(incoming).rounds() == before - 1,
                            "Actual shot accepted at unchanged switch deadline"); WeaponRuntime.releaseUse(handling, incoming); h.succeed();
                }
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void stowCopyTransferDimensionSpectatorAndCleanupRetireOnlyTheirOwnAimSession(GameTestHelper h) {
        var actors = new ArrayList<ServerPlayer>();
        for (int i = 0; i < 7; i++) { var p = player(h); equip(h, p, "beloved", true); ads(p, true); actors.add(p); }
        var recipient = player(h); equip(h, recipient, "beloved", false);
        var originals = actors.stream().map(ServerPlayer::getMainHandItem).toList();
        for (int i = 1; i <= 10; i++) h.runAfterDelay(i, () -> { for (var p : actors) tick(p); });
        h.runAfterDelay(11, () -> {
            for (var p : actors) scoped(h, p);
            var keeper = actors.get(6); var frame = DisplayHud.getHud(keeper, WeaponScopeHud.FRAME_ID);
            var center = DisplayHud.getHud(keeper, WeaponScopeHud.CENTER_ID);
            // Native stow to an empty building slot; retain the actual inventory weapon.
            var stow = actors.get(0); stow.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(4)); tick(stow);
            // A component-identical copy is still a new identity and must shed its saved scope selector.
            var copyOwner = actors.get(1); var copy = originals.get(1).copy();
            copyOwner.getInventory().setItem(1, copy);
            near(h, WeaponAiming.progress(copyOwner), 0, "Copy cannot inherit previous identity's progress"); tick(copyOwner);
            var donor = actors.get(2); var transferred = originals.get(2);
            donor.getInventory().setItem(1, ItemStack.EMPTY); tick(donor);
            recipient.getInventory().setItem(1, transferred);
            near(h, WeaponAiming.progress(recipient), 0, "Different owner cannot inherit saved scope progress"); tick(recipient);
            var dimension = actors.get(3); ads(dimension, false);
            var other = java.util.stream.StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                    .filter(level -> level != h.getLevel()).findFirst().orElseThrow();
            dimension.setServerLevel(other); tick(dimension); dimension.setServerLevel(h.getLevel());
            var spectator = actors.get(4); spectator.setGameMode(GameType.SPECTATOR); tick(spectator);
            var cleaned = actors.get(5); WeaponRuntime.cleanup(cleaned); WeaponRuntime.cleanup(cleaned);
            for (int i = 0; i < 6; i++) {
                var p = actors.get(i); absent(h, p); near(h, WeaponAiming.progress(p), 0, "Invalidated session cannot retain ADS");
                check(h, "hip".equals(pose(originals.get(i))) && WeaponPerks.selected(originals.get(i), SNAPSHOT).isPresent(),
                        "Invalidation restores old selector but preserves serialized Snapshot selection");
            }
            absent(h, recipient); check(h, "hip".equals(pose(copy)) && "hip".equals(pose(transferred)), "Copy and transfer repair persisted scope");
            check(h, DisplayHud.getHud(keeper, WeaponScopeHud.FRAME_ID) == frame && !frame.isRemoved()
                            && DisplayHud.getHud(keeper, WeaponScopeHud.CENTER_ID) == center && !center.isRemoved(),
                    "Other owners' cleanup leaves keeper's real HUD nodes intact");
        });
        h.runAfterDelay(12, () -> {
            var cleaned = actors.get(5);
            check(h,!WeaponAiming.requested(cleaned)&&WeaponAiming.progress(cleaned)==0,"Cleanup discards the old toggle");
            ads(cleaned, true); tick(cleaned);
            near(h, WeaponAiming.progress(cleaned), 1f / WeaponAiming.fast(7), "A fresh click starts a new Snapshot session, never old full progress");
            if (WeaponAiming.progress(cleaned) >= .5f) scoped(h, cleaned); else absent(h, cleaned);
            scoped(h, actors.get(6)); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void realReloadAndSuspendLatchHeldCrouchUntilReleaseThenStartFresh(GameTestHelper h) {
        var reload = player(h); var suspended = player(h);
        var stack = equip(h, reload, "beloved", true); equip(h, suspended, "beloved", true);
        var profile = WeaponProfile.forEntry(entry("beloved")); WeaponItems.save(stack, new WeaponMagazine(profile, 1, 6));
        ads(reload, true); ads(suspended, true);
        int done = 10 + profile.firstReloadTicks();
        check(h, ReloadCreditProfile.find(entry("beloved")).isEmpty(), "Beloved is excluded from the W65 early-credit profile");
        check(h, done + 10 < 110, "Actual reload fits bounded fixture");
        for (int i = 1; i <= done + 9; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                if (elapsed == done + 1) { ads(reload, false); ads(suspended, false); }
                if (elapsed == done + 2) { ads(reload, true); ads(suspended, true); }
                tick(reload); tick(suspended);
                if (elapsed == 10) {
                    scoped(h, reload); scoped(h, suspended);
                    check(h, InputRouter.onPlayerAction(reload, ServerboundPlayerActionPacket.Action.DROP_ITEM)
                                    && WeaponRuntime.reloading(reload), "Real Q starts production reload");
                    WeaponAiming.suspend(suspended);
                    check(h, ammo(stack).rounds() == 1 && ammo(stack).reserve() == 6, "No early reload transfer");
                }
                if (elapsed >= 10 && elapsed <= done + 1) {
                    for (var p : List.of(reload, suspended)) {
                        absent(h, p); near(h, WeaponAiming.progress(p), 0, "Cancelled toggle cannot re-enter ADS without a fresh click");
                        check(h, "hip".equals(pose(p.getMainHandItem())), "Cancel immediately restores hip selector");
                    }
                }
                if (elapsed > 10 && elapsed < done) {
                    check(h, WeaponRuntime.reloading(reload) && ammo(stack).rounds() == 1 && ammo(stack).reserve() == 6,
                            "Excluded Beloved cannot credit ammunition before full recovery, even with Snapshot");
                    if (elapsed == done - 1)
                        check(h, !WeaponRuntime.beginUse(reload), "Last recovery tick still blocks a paid shot");
                }
                if (elapsed == done) check(h, !WeaponRuntime.reloading(reload) && ammo(stack).rounds() == profile.magazine()
                                && ammo(stack).reserve() == 6 - (profile.magazine() - 1), "Only real Beloved full deadline transfers reserve");
                if (elapsed == done + 2) for (var p : List.of(reload, suspended))
                    near(h, WeaponAiming.progress(p), 1f / WeaponAiming.fast(7), "Fresh left-click starts first real Snapshot tick");
                if (elapsed == done + 9) {
                    scoped(h, reload); scoped(h, suspended);
                    check(h, WeaponPerks.selected(stack, SNAPSHOT).isPresent(), "Reload/suspend preserve selected socket"); h.succeed();
                }
            });
        }
    }

    // This is the ONLY W68 test that toggles global shader configuration or asserts FOV.
    // Toggles surround synchronous calls only, so asynchronous GameTests never inherit a flag.
    private static void tickWithShader(ServerPlayer p, boolean enabled) {
        var config = ModConfig.getInstance(); boolean previous = config.dynamicFovShader;
        try { config.dynamicFovShader = enabled; tick(p); }
        finally { config.dynamicFovShader = previous; }
    }
    private static void fov(GameTestHelper h, ServerPlayer p, Float prior, float zoom) {
        check(h, Objects.equals(CameraEffects.getFov(p), prior),
                "ADS never acquires or overwrites shader FOV, including prior/null and both feature flags");
        float progress = WeaponAiming.aimInput(p) ? 1 : 0; // W277: full native target on accept
        var speed = p.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MOVEMENT_SPEED);
        var modifier = speed.getModifier(Identifier.parse("destiny:weapon_ads_movement_w75"));
        if (WeaponAiming.requested(p)) {
            // Beloved: .75 base ADS movement, 4x zoom. Independent native-zoom equation.
            double scalar = (1 - (double)progress) + progress * (.75 / Math.max(1, zoom));
            check(h, modifier != null && Math.abs(modifier.amount() - (scalar - 1)) < 1e-7,
                    "Actual native speed encodes the same ADS progress independently of the shader toggle");
        } else check(h, modifier == null, "Toggle-off immediately releases native speed while visual ADS exits");
    }

    @GameTest(structure = FLOOR, maxTicks = 45, environment = "destiny-test:w90_isolated")
    public void perspectiveFovOwnershipRestorationAndShaderDisabledStillUseRealAdsAndHud(GameTestHelper h) {
        boolean originalFlag = ModConfig.getInstance().dynamicFovShader;
        var prior = player(h); var noPrior = player(h); var foreign = player(h);
        var disabled = player(h); var disabledNoPrior = player(h);
        var enabled = List.of(prior, noPrior, foreign); var off = List.of(disabled, disabledNoPrior);
        for (var p : List.of(prior, noPrior, foreign, disabled, disabledNoPrior)) {
            equip(h, p, "beloved", true); ads(p, true);
        }
        CameraEffects.setFov(prior, 83); CameraEffects.setFov(foreign, 80); CameraEffects.setFov(disabled, 87);
        for (int i = 1; i <= 10; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                for (var p : enabled) tickWithShader(p, true);
                for (var p : off) tickWithShader(p, false);
                fov(h, prior, 83f, 4); fov(h, noPrior, null, 4); fov(h, foreign, 80f, 4);
                for (var p : off) {
                    near(h, WeaponAiming.progress(p), Math.min(1f, elapsed / (float)WeaponAiming.fast(7)), "Disabled shader keeps actual Snapshot timing");
                    if (WeaponAiming.progress(p) >= .5f) scoped(h, p); else absent(h, p);
                }
                check(h, Objects.equals(CameraEffects.getFov(disabled), 87f) && CameraEffects.getFov(disabledNoPrior) == null,
                        "Disabled shader preserves prior override/null while ADS and HUD work");
                check(h, ModConfig.getInstance().dynamicFovShader == originalFlag, "Per-tick flag restored immediately");
            });
        }
        h.runAfterDelay(11, () -> {
            CameraEffects.setFov(foreign, 55); tickWithShader(foreign, true);
            near(h, WeaponAiming.progress(foreign), 1, "Foreign shader projection does not cancel native ADS"); scoped(h, foreign);
            check(h, CameraEffects.getFov(foreign).equals(55f), "Foreign FOV never overwritten on detection");
            for (var p : off) { tickWithShader(p, true); fov(h, p, p == disabled ? 87f : null, 4); scoped(h, p); }
            ads(prior, false); ads(noPrior, false);
        });
        for (int i = 12; i <= 22; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                tickWithShader(prior, true); tickWithShader(noPrior, true); tickWithShader(foreign, true);
                fov(h, prior, 83f, 4); fov(h, noPrior, null, 4);
                near(h, WeaponAiming.progress(foreign), 1, "Shader projection stays independent of the live toggle"); scoped(h, foreign);
                check(h, CameraEffects.getFov(foreign).equals(55f), "Old ADS session cannot reclaim external FOV");
                for (var p : off) { tickWithShader(p, false); scoped(h, p); }
                check(h, Objects.equals(CameraEffects.getFov(disabled), 87f) && CameraEffects.getFov(disabledNoPrior) == null,
                        "Disabling an owned projection restores exact previous override/null without cancelling HUD/ADS");
                if (elapsed == 22) {
                    absent(h, prior); absent(h, noPrior);
                    WeaponRuntime.cleanup(foreign); WeaponRuntime.cleanup(foreign);
                    check(h, CameraEffects.getFov(foreign).equals(55f), "Idempotent cleanup preserves foreign camera owner");
                    check(h, ModConfig.getInstance().dynamicFovShader == originalFlag, "Global shader flag restored on completion");
                    h.succeed();
                }
            });
        }
    }
}
