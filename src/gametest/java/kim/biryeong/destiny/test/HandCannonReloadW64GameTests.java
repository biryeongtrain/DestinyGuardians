package kim.biryeong.destiny.test;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** Embedded/server runtime evidence only; no native rendering or cylinder-motion claim.
 * Presentation is activated exclusively by accepted WeaponRuntime.reload calls.
 * No synthetic clock, injected kill credit, or direct presentation activation.
 */
public final class HandCannonReloadW64GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String DUKE = "duke_mk_44";
    private static final List<String> SUPPORTED = List.of(DUKE, "beloved");
    private static final float EPS = .0001f;

    private record Reload(ServerPlayer owner, ItemStack gun, WeaponProfile profile,
                          Identifier originalModel, int rounds, int reserve, long total,
                          int duration) {}

    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }

    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 0);
        p.setOnGround(true);
        TestCleanup.register(h, () -> {
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            TestPlayers.remove(p);
        });
        return p;
    }

    private static WeaponCatalog.Entry entry(ItemStack gun) {
        return WeaponItems.entry(gun).orElseThrow();
    }

    private static WeaponProfile profile(ItemStack gun) {
        return WeaponProfile.forEntry(entry(gun));
    }

    private static WeaponMagazine ammo(ItemStack gun) {
        return WeaponItems.magazine(gun, profile(gun));
    }

    private static ItemStack equip(ServerPlayer p, String id, int rounds, int reserve) {
        var e = WeaponCatalog.find(id).orElseThrow();
        var gun = WeaponItems.create(e);
        WeaponItems.save(gun, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, reserve));
        p.setItemInHand(InteractionHand.MAIN_HAND, gun);
        WeaponRuntime.tickPlayer(p);
        TestPlayers.drain(p);
        return gun;
    }

    // Authored W207-W222 reload banks; keep exact routes separate from the outgoing hand projection.
    private static Identifier expectedModel(String id) {
        String path = switch (id) {
            case "ammit_ar2", "blast_furnace", "hammerhead" -> "weapon_reload_w207_" + id + "/" + id;
            case "beloved", "the_recluse", "gnawing_hunger", "austringer" -> "weapon_reload_w208_" + id + "/" + id;
            case "antiope_d", "bug_out_bag", "cold_denial", "bygones" -> "weapon_reload_w212_" + id + "/" + id;
            case "lonesome", "steelfeather_repeater", "aishas_embrace", "chattering_bone" -> "weapon_reload_w213_" + id + "/" + id;
            case "halfdan_d", "claws_of_the_wolf", "bite_of_the_fox", "retrofit_escapade" -> "weapon_reload_w214_" + id + "/" + id;
            case "duke_mk_44", "farewell", "apostate", "fixed_odds" -> "weapon_reload_w215_" + id + "/" + id;
            case "distant_relation", "patron_of_lost_causes", "brass_attacks", "ikelos_smg_v1_0_1" -> "weapon_reload_w216_" + id + "/" + id;
            case "erentil_fr4", "hollow_words", "dream_breaker", "null_composure", "coriolis_force" -> "weapon_reload_w217_" + id + "/" + id;
            case "line_in_the_sand", "stormchaser", "code_duello", "bellowing_giant", "bad_omens" -> "weapon_reload_w218_" + id + "/" + id;
            case "allied_demand", "dead_man_walking_xx7463", "high_albedo", "frontier_justice", "retraced_path" -> "weapon_reload_w219_" + id + "/" + id;
            case "edge_transit", "canis_major", "dimensional_hypotrochoid", "deafening_whisper", "salvager_s_salvo" -> "weapon_reload_w220_" + id + "/" + id;
            case "pyroclastic_flow", "seventh_seraph_officer_revolver" -> "weapon_reload_w221_" + id + "/" + id;
            case "biting_winds", "whispering_slab", "nezarec_s_whisper" -> "weapon_reload_w222_" + id + "/" + id;
            case "ace_of_spades" -> "weapon_reload_w157/ace_of_spades";
            default -> null;
        };
        return path == null ? null : Identifier.fromNamespaceAndPath("destiny", path);
    }

    private static ItemStack wire(ServerPlayer p, ItemStack gun) {
        var context = ((PacketContextProvider) (Object) p.connection).getPacketContext();
        return PolymerItemUtils.getPolymerItemStack(gun, context, p.level().registryAccess());
    }

    private static float progress(ItemStack gun) {
        return gun.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY)
                .getFloat(WeaponReloadPresentation.PROGRESS_INDEX);
    }

    private static ItemDisplayHud node(ServerPlayer p, String suffix) {
        return (ItemDisplayHud) DisplayHud.getHud(p, AmmoHud.PREFIX + suffix);
    }

    private static Reload start(GameTestHelper h, ServerPlayer p, ItemStack gun) {
        var f = profile(gun);
        var original = gun.get(DataComponents.ITEM_MODEL);
        var before = ammo(gun);
        check(h, WeaponRuntime.reload(p), "Actual reload accepted: " + entry(gun).id());
        var state = WeaponRuntime.ammunition(p).orElseThrow();
        check(h, WeaponOutlaw.remaining(p) == 0 && state.reloadDuration() == f.firstReloadTicks(),
                "Base reload uses its actual phase duration without fabricated Outlaw");
        check(h, WeaponReloadPresentation.active(gun) && progress(gun) == 0,
                "Only the accepted live stack starts at progress zero");
        check(h, WeaponFirstPersonHands.model(expectedModel(entry(gun).id())).equals(wire(p, gun).get(DataComponents.ITEM_MODEL)),
                "Polymer sends the exact authored Duke or Beloved route inside the outgoing hand wrapper");
        check(h, original.equals(gun.get(DataComponents.ITEM_MODEL)), "Wrapper never replaces persisted item identity");
        return new Reload(p, gun, f, original, before.rounds(), before.reserve(), before.total(), state.reloadDuration());
    }

    private static void unchangedAmmo(GameTestHelper h, Reload r) {
        var a = ammo(r.gun());
        check(h, a.rounds() == r.rounds() && a.reserve() == r.reserve() && a.total() == r.total(),
                "Unfinished/cancelled reload cannot transfer ammo: " + entry(r.gun()).id());
    }

    private static void inactive(GameTestHelper h, Reload r) {
        check(h, !WeaponReloadPresentation.active(r.gun()) && progress(r.gun()) == -1,
                "Retired live presentation has an inactive cache selector");
        check(h, r.originalModel().equals(r.gun().get(DataComponents.ITEM_MODEL))
                        && WeaponFirstPersonHands.model(r.originalModel()).equals(wire(r.owner(), r.gun()).get(DataComponents.ITEM_MODEL)),
                "Retirement restores the base wire model and preserves stored identity");
    }

    private static void digit(GameTestHelper h, ServerPlayer p, String field, int value) {
        String text = Integer.toString(value);
        for (int i = 0; i < text.length(); i++) {
            var glyph = node(p, field + "_" + i);
            check(h, glyph != null && Identifier.fromNamespaceAndPath("destiny", "gui/hud/ammo_digit_" + text.charAt(i))
                            .equals(glyph.getItem().get(DataComponents.ITEM_MODEL)),
                    "Actual HUD glyph follows authoritative " + field + "=" + text);
        }
        check(h, node(p, field + "_" + text.length()) == null, "No stale trailing ammunition glyph");
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void authoredReloadRoutesCoverExactCurrentCatalogBoundary(GameTestHelper h) {
        check(h, !WeaponReloadPresentation.supports(null), "Null is unsupported");
        for (String id : SUPPORTED) {
            var e = WeaponCatalog.find(id).orElseThrow();
            check(h, WeaponReloadPresentation.supports(e), "Required production presentation: " + id);
            check(h, expectedModel(id).equals(WeaponReloadPresentation.model(e)), "Exact wrapper namespace/path: " + id);
        }
        for (var e : WeaponCatalog.all()) {
            var expected = expectedModel(e.id());
            check(h, WeaponReloadPresentation.supports(e) == (expected != null),
                    "Exact authored reload support boundary: " + e.id());
            if (expected != null) {
                check(h, expected.equals(WeaponReloadPresentation.model(e)), "Exact current route: " + e.id());
                var resource = "/assets/destiny/items/" + expected.getPath() + ".json";
                check(h, HandCannonReloadW64GameTests.class.getResource(resource) != null,
                        "Pinned route has a packaged item graph: " + resource);
            } else {
                var gun = WeaponItems.create(e);
                var before = gun.copy();
                WeaponReloadPresentation.update(gun, true, .5f);
                check(h, !WeaponReloadPresentation.active(gun) && ItemStack.matches(before, gun),
                        "Unsupported update leaves every component untouched: " + e.id());
            }
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 180, environment = "destiny-test:w90_isolated")
    public void dukeAcceptedReloadProgressWireAndHudFollowActualServerDeadline(GameTestHelper h) {
        var p = player(h, 6.5);
        var gun = equip(p, DUKE, 2, 0);
        gun.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(
                List.of(7f, -1f, 13f), List.of(false, true), List.of("hip", "w64-independent"), List.of(0xABCDEF)));
        var independent = gun.get(DataComponents.CUSTOM_MODEL_DATA);
        var r = start(h, p, gun);
        check(h, r.profile().infiniteReserve(), "Duke retains real Primary infinite-reserve policy");
        h.onEachTick(() -> WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(r.duration() / 2, () -> {
            WeaponRuntime.tickPlayer(p);
            var state = AmmoHud.current(p).orElseThrow();
            float expected = (float) Math.floor(state.reloadProgress() * 60 + 1e-6f) / 60;
            check(h, state.reloading() && state.reloadProgress() > .3f && state.reloadProgress() < .7f
                            && Math.abs(progress(gun) - expected) < EPS,
                    "Persisted CMD follows actual elapsed server phase in authored sixty-step samples");
            var sent = wire(p, gun);
            check(h, WeaponFirstPersonHands.model(expectedModel(DUKE)).equals(sent.get(DataComponents.ITEM_MODEL))
                            && Math.abs(progress(sent) - progress(gun)) < EPS,
                    "Actual live Polymer wrapper carries current server progress");
            var data = gun.get(DataComponents.CUSTOM_MODEL_DATA);
            check(h, data.getFloat(0) == 7f && data.getFloat(2) == 13f
                            && data.flags().equals(independent.flags()) && data.strings().equals(independent.strings())
                            && data.colors().equals(independent.colors()), "Reload preserves unrelated CMD slots and grip/pose/color data");
            var before = gun.copy();
            for (int i = 0; i < 12; i++) {
                AmmoHud.current(p); CombatHud.update(p); wire(p, gun);
                check(h, !WeaponRuntime.reload(p), "Duplicate live reload is rejected");
            }
            check(h, ItemStack.matches(before, gun), "HUD/wire reads and denied duplicates cannot advance or mutate reload");
            unchangedAmmo(h, r);
            digit(h, p, "rounds", 2);
            check(h, node(p, "infinity") != null && node(p, "reserve_0") == null && node(p, "reload_track") != null,
                    "Live Primary HUD shows infinity and the real reload phase");
            var fill = node(p, "reload");
            float width = 276 * (float) Math.floor(state.reloadProgress() * 8) / 8;
            check(h, fill != null && Math.abs(fill.getScale().x - width) < EPS, "Rendered HUD fill follows its actual eight-step phase");
        });
        h.runAfterDelay(r.duration() - 1, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, WeaponRuntime.reloading(p) && WeaponReloadPresentation.active(gun)
                            && progress(gun) > .8f && progress(gun) < 1, "Last pre-deadline frame remains active without early completion");
            check(h, ammo(gun).rounds() == r.profile().magazine() && ammo(gun).reserve() == 0,
                    "W65: credit42 already loaded Primary; visual recovery remains active through58");
        });
        h.runAfterDelay(r.duration(), () -> {
            WeaponRuntime.tickPlayer(p); CombatHud.update(p);
            check(h, !WeaponRuntime.reloading(p) && ammo(gun).rounds() == r.profile().magazine()
                            && ammo(gun).reserve() == 0 && ammo(gun).overflow() == 0,
                    "Only the actual Duke deadline fills its magazine without inventing finite reserve");
            inactive(h, r);
            digit(h, p, "rounds", r.profile().magazine());
            check(h, !AmmoHud.current(p).orElseThrow().reloading() && node(p, "reload_track") == null
                            && node(p, "reload") == null && node(p, "infinity") != null,
                    "Completion removes phase HUD while retaining Primary reserve policy");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 180, environment = "destiny-test:w90_isolated")
    public void persistedActiveCmdCopiesAndPreviewCannotAcquireLiveAuthority(GameTestHelper h) {
        var p = player(h, 3.5);
        var gun = equip(p, DUKE, 2, 0);
        var r = start(h, p, gun);
        var replicas = new ArrayList<ItemStack>();
        var replicaOwners = new ArrayList<ServerPlayer>();
        h.onEachTick(() -> {
            WeaponRuntime.tickPlayer(p);
            replicaOwners.forEach(WeaponRuntime::tickPlayer);
        });
        h.runAfterDelay(r.duration() / 2, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, progress(gun) > 0 && WeaponReloadPresentation.active(gun), "Serialize actual in-progress reload CMD");
            var ops = h.getLevel().registryAccess().createSerializationContext(NbtOps.INSTANCE);
            var encoded = ItemStack.CODEC.encodeStart(ops, gun).getOrThrow();
            var decoded = ItemStack.CODEC.parse(ops, encoded).getOrThrow();
            var copy = gun.copy();
            check(h, ItemStack.matches(decoded, gun) && ItemStack.matches(copy, gun),
                    "Real NBT and ordinary copy preserve the persisted selectors and all combat components");
            for (var replica : List.of(copy, decoded)) {
                var other = player(h, 9.5);
                other.setItemInHand(InteractionHand.MAIN_HAND, replica);
                replicaOwners.add(other); replicas.add(replica);
                var before = replica.copy();
                WeaponRuntime.tickPlayer(other); CombatHud.update(other);
                check(h, !WeaponReloadPresentation.active(replica) && !WeaponRuntime.reloading(other)
                                && !AmmoHud.current(other).orElseThrow().reloading()
                                && WeaponFirstPersonHands.model(r.originalModel()).equals(wire(other, replica).get(DataComponents.ITEM_MODEL))
                                && ItemStack.matches(before, replica),
                        "Copied/saved CMD on an actually held live combat item grants neither animation nor reload");
            }
            var preview = WeaponModels.create(entry(gun));
            preview.set(DataComponents.CUSTOM_MODEL_DATA, gun.get(DataComponents.CUSTOM_MODEL_DATA));
            var previewOwner = player(h, 6.5);
            previewOwner.setItemInHand(InteractionHand.MAIN_HAND, preview);
            check(h, WeaponItems.entry(preview).isEmpty() && !WeaponRuntime.reload(previewOwner)
                            && !WeaponReloadPresentation.active(preview)
                            && !WeaponFirstPersonHands.model(expectedModel(DUKE)).equals(wire(previewOwner, preview).get(DataComponents.ITEM_MODEL)),
                    "A preview with genuine saved reload selectors cannot become a live animated weapon");
            check(h, WeaponReloadPresentation.active(gun), "Inspecting replicas leaves original live authority intact");
        });
        h.runAfterDelay(r.duration() + 1, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, replicas.size() == 2 && ammo(gun).rounds() == r.profile().magazine(), "Only the accepted original reload finishes");
            for (int i = 0; i < replicas.size(); i++) {
                var replica = replicas.get(i); var other = replicaOwners.get(i);
                WeaponRuntime.tickPlayer(other);
                check(h, ammo(replica).rounds() == 2 && ammo(replica).reserve() == 0
                                && !WeaponRuntime.reloading(other) && !WeaponReloadPresentation.active(replica)
                                && WeaponFirstPersonHands.model(r.originalModel()).equals(wire(other, replica).get(DataComponents.ITEM_MODEL)),
                        "Persisted selector cannot schedule a ghost transfer at the original owner's deadline");
            }
            inactive(h, r); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 180, environment = "destiny-test:w90_isolated")
    public void sameTickSkillCancellationAndAcceptedSuperRetireDukeWithoutGhostRefill(GameTestHelper h) {
        var a = player(h, 3.5); var b = player(h, 9.5);
        var r = start(h, a, equip(a, DUKE, 2, 0));
        var superReload = start(h, b, equip(b, DUKE, 2, 0));
        var started = r.gun().copy();
        WeaponRuntime.cancelUseForSkill(a);
        check(h, !ItemStack.matches(started, r.gun()) && !WeaponRuntime.reloading(a),
                "Same-tick skill cancellation invalidates the actual item/wire cache key");
        inactive(h, r); unchangedAmmo(h, r);
        Guardians.data(b).setSuperEnergy(1);
        check(h, AbilityService.use(b, AbilitySlot.SUPER) == AbilityService.Result.OK,
                "A real charged equipped Solar super is accepted");
        check(h, !WeaponRuntime.reloading(b), "Accepted actual skill retires its gameplay reload");
        inactive(h, superReload); unchangedAmmo(h, superReload);
        AbilityService.endSuper(b);
        h.onEachTick(() -> { WeaponRuntime.tickPlayer(a); WeaponRuntime.tickPlayer(b); });
        h.runAfterDelay(Math.max(r.duration(), superReload.duration()) + 1, () -> {
            for (var cancelled : List.of(r, superReload)) {
                WeaponRuntime.tickPlayer(cancelled.owner()); CombatHud.update(cancelled.owner());
                inactive(h, cancelled); unchangedAmmo(h, cancelled);
                check(h, !WeaponRuntime.reloading(cancelled.owner()) && node(cancelled.owner(), "reload_track") == null,
                        "Cancelled accepted deadline cannot return animation, phase HUD or ammunition");
            }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 180, environment = "destiny-test:w90_isolated")
    public void replacingWithIdenticalCopyCancelsOldIdentityAndReturningStackCannotResume(GameTestHelper h) {
        var p = player(h, 6.5);
        var r = start(h, p, equip(p, DUKE, 2, 0));
        var replacement = r.gun().copy();
        check(h, ItemStack.matches(replacement, r.gun()) && !WeaponReloadPresentation.active(replacement),
                "Identical replacement components do not carry live identity authority");
        p.setItemInHand(InteractionHand.MAIN_HAND, replacement);
        WeaponRuntime.tickPlayer(p); CombatHud.update(p);
        check(h, !WeaponRuntime.reloading(p) && !WeaponReloadPresentation.active(replacement)
                        && !AmmoHud.current(p).orElseThrow().reloading() && node(p, "reload_track") == null,
                "Actual inventory replacement cancels gameplay and HUD phase");
        inactive(h, r); unchangedAmmo(h, r);
        check(h, WeaponHandling.remaining(p) > 0 && !WeaponRuntime.reload(p), "Replacement must obey real W58 ready time");
        h.onEachTick(() -> WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(r.duration() + 1, () -> {
            check(h, ammo(replacement).rounds() == 2 && ammo(replacement).reserve() == 0
                            && WeaponFirstPersonHands.model(r.originalModel()).equals(wire(p, replacement).get(DataComponents.ITEM_MODEL)),
                    "Replacement never inherits the cancelled deadline or wrapper");
            p.setItemInHand(InteractionHand.MAIN_HAND, r.gun());
            WeaponRuntime.tickPlayer(p); CombatHud.update(p);
            unchangedAmmo(h, r); inactive(h, r);
            check(h, !WeaponRuntime.reloading(p) && node(p, "reload_track") == null,
                    "Returning original after its old deadline cannot resume or silently refill");
        });
        h.runAfterDelay(r.duration() + 20, () -> {
            WeaponRuntime.tickPlayer(p); unchangedAmmo(h, r); inactive(h, r);
            check(h, !WeaponRuntime.reloading(p) && ammo(replacement).rounds() == 2, "Further server ticks cannot resurrect either retired stack");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 180, environment = "destiny-test:w90_isolated")
    public void cleanupAndDeadOwnerCannotRetireAnotherOwnersDukeReload(GameTestHelper h) {
        var a = player(h, 3.5); var b = player(h, 6.5); var c = player(h, 9.5);
        var cleaned = start(h, a, equip(a, DUKE, 2, 0));
        var dead = start(h, b, equip(b, DUKE, 2, 0));
        var survivor = start(h, c, equip(c, DUKE, 2, 0));
        h.onEachTick(() -> { WeaponRuntime.tickPlayer(a); WeaponRuntime.tickPlayer(b); WeaponRuntime.tickPlayer(c); });
        h.runAfterDelay(survivor.duration() / 2, () -> {
            WeaponRuntime.tickPlayer(c);
            var before = survivor.gun().copy();
            WeaponRuntime.cleanup(a); WeaponRuntime.cleanup(a);
            b.setHealth(0); WeaponRuntime.tickPlayer(b); WeaponRuntime.tickPlayer(b);
            inactive(h, cleaned); inactive(h, dead);
            unchangedAmmo(h, cleaned); unchangedAmmo(h, dead);
            check(h, !WeaponRuntime.reloading(a) && !WeaponRuntime.reloading(b) && AmmoHud.current(b).isEmpty(),
                    "Repeated owner cleanup and real dead-owner validation retire only their states");
            check(h, WeaponRuntime.reloading(c) && WeaponReloadPresentation.active(survivor.gun())
                            && ItemStack.matches(before, survivor.gun())
                            && WeaponFirstPersonHands.model(expectedModel(DUKE)).equals(wire(c, survivor.gun()).get(DataComponents.ITEM_MODEL)),
                    "Other owners cannot mutate surviving owner's phase, item or live wire authority");
            unchangedAmmo(h, survivor);
        });
        h.runAfterDelay(survivor.duration() + 1, () -> {
            WeaponRuntime.tickPlayer(c);
            unchangedAmmo(h, cleaned); unchangedAmmo(h, dead);
            inactive(h, cleaned); inactive(h, dead); inactive(h, survivor);
            check(h, ammo(survivor.gun()).rounds() == survivor.profile().magazine()
                            && ammo(survivor.gun()).reserve() == 0 && !WeaponRuntime.reloading(c),
                    "Surviving owner alone completes at its own unchanged deadline");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 180, environment = "destiny-test:w90_isolated")
    public void belovedRetainsW47WireAndPaysOnlyItsFiniteReserveAtCompletion(GameTestHelper h) {
        var p = player(h, 6.5);
        var r = start(h, p, equip(p, "beloved", 1, 2));
        check(h, !r.profile().infiniteReserve() && r.profile().magazine() > 3,
                "Legacy fixture has a real finite short reserve and cannot fill its magazine");
        h.onEachTick(() -> WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(r.duration() - 1, () -> {
            WeaponRuntime.tickPlayer(p); CombatHud.update(p);
            unchangedAmmo(h, r);
            check(h, WeaponRuntime.reloading(p) && WeaponReloadPresentation.active(r.gun())
                            && WeaponFirstPersonHands.model(expectedModel("beloved")).equals(wire(p, r.gun()).get(DataComponents.ITEM_MODEL))
                            && progress(r.gun()) > .8f && progress(r.gun()) < 1,
                    "Beloved keeps its W47 wrapper and actual late-phase progress through the last unfinished tick");
            digit(h, p, "rounds", 1); digit(h, p, "reserve", 2);
        });
        h.runAfterDelay(r.duration(), () -> {
            WeaponRuntime.tickPlayer(p); CombatHud.update(p);
            var a = ammo(r.gun());
            check(h, !WeaponRuntime.reloading(p) && a.rounds() == 3 && a.reserve() == 0 && a.total() == r.total(),
                    "Actual W47 completion transfers exactly two finite rounds and conserves total ammunition");
            inactive(h, r);
            digit(h, p, "rounds", 3); digit(h, p, "reserve", 0);
            check(h, node(p, "reload_track") == null && node(p, "reload") == null
                            && node(p, "infinity") == null && !WeaponRuntime.reload(p),
                    "Legacy completion clears phase HUD and empty reserve cannot start another reload");
            h.succeed();
        });
    }
}
