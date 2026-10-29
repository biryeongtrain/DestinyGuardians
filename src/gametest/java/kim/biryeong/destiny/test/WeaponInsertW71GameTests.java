package kim.biryeong.destiny.test;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.sound.DestinySounds;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Accepted gameplay inputs, advancing server ticks and actual Polymer/HUD/packet projections.
 * No presentation activation, injected clock, native rendering or acoustic-output claim.
 */
public final class WeaponInsertW71GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final Identifier WRAPPER = Identifier.parse("destiny:weapon_insert_w222_long_arm/long_arm");
    private static final java.util.Map<String, String> INSERT_ROUTES = java.util.Map.of(
            "long_arm", "weapon_insert_w222_long_arm/long_arm",
            "dust_rock_blues", "weapon_insert_w207_dust_rock_blues/dust_rock_blues",
            "first_in_last_out", "weapon_insert_w208_first_in_last_out/first_in_last_out",
            "mindbender_s_ambition_adept", "weapon_insert_w221_mindbender_s_ambition_adept/mindbender_s_ambition_adept",
            "ikelos_sg_v1_0_1", "weapon_insert_w221_ikelos_sg_v1_0_1/ikelos_sg_v1_0_1",
            "parcel_of_stardust_fell_to_earth", "weapon_insert_w221_parcel_of_stardust_fell_to_earth/parcel_of_stardust_fell_to_earth");
    private static final CustomModelData SENTINEL = new CustomModelData(
            List.of(7.25f, .375f, 47f, -1f, 99f, 17.5f), List.of(true, false, true),
            List.of("hip", "w71_keep", "independent"), List.of(0x123456, 0xABCDEF));
    private record Reload(ServerPlayer owner, ItemStack gun, ItemStack original, long started) {}

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static void near(GameTestHelper h, float actual, float expected, String message) {
        check(h, Math.abs(actual - expected) < .00001f, message + ": " + actual + " != " + expected);
    }
    private static WeaponCatalog.Entry entry() { return WeaponCatalog.find("long_arm").orElseThrow(); }
    private static WeaponProfile profile() { return WeaponProfile.forEntry(entry()); }
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static WeaponMagazine ammo(ItemStack gun) {
        return WeaponItems.magazine(gun, WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow()));
    }
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, 6.5), -90, -80);
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setOnGround(true);
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.EMERALD, 4));
        TestCleanup.register(h, () -> {
            p.setServerLevel(h.getLevel());
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            for (String id : List.copyOf(DisplayHud.getHuds(p).keySet())) DisplayHud.removeHud(p, id);
            TestPlayers.remove(p);
        });
        return p;
    }
    private static void hold(ServerPlayer p, ItemStack gun, WeaponCatalog.Entry e) {
        int slot = WeaponCharacteristics.of(e).slot().hotbar();
        p.getInventory().setItem(slot, gun);
        p.getInventory().setSelectedSlot(slot);
    }
    private static ItemStack equip(ServerPlayer p, int rounds) {
        var gun = WeaponItems.create(entry());
        WeaponItems.save(gun, new WeaponMagazine(profile(), rounds, 0));
        hold(p, gun, entry());
        tick(p);
        gun.set(DataComponents.CUSTOM_MODEL_DATA, SENTINEL);
        return gun;
    }
    private static void tick(ServerPlayer p) {
        WeaponRuntime.tickPlayer(p);
        TestPlayers.drain(p);
    }
    private static void drive(GameTestHelper h, ServerPlayer... players) {
        h.onEachTick(() -> { for (var p : players) tick(p); });
    }
    private static Reload start(GameTestHelper h, ServerPlayer p, ItemStack gun) {
        var r = new Reload(p, gun, gun.copy(), now(p));
        check(h, WeaponRuntime.reload(p), "Actual Long Arm reload is accepted");
        check(h, WeaponInsertPresentation.active(gun) && WeaponRuntime.reloading(p),
                "Accepted gameplay reload immediately acquires W71");
        return r;
    }
    private static float selector(ItemStack gun) {
        return gun.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(4);
    }
    private static float sample(float progress) { return (float) Math.floor(progress * 60 + 1e-6f) / 60; }
    private static ItemStack wire(ServerPlayer p, ItemStack gun) {
        var context = ((PacketContextProvider) (Object) p.connection).getPacketContext();
        return PolymerItemUtils.getPolymerItemStack(gun, context, p.level().registryAccess());
    }
    private static ItemDisplayHud node(ServerPlayer p, String suffix) {
        return (ItemDisplayHud) DisplayHud.getHud(p, AmmoHud.PREFIX + suffix);
    }
    private static void amounts(GameTestHelper h, ItemStack gun, int rounds) {
        var a = ammo(gun);
        check(h, a.rounds() == rounds && a.reserve() == 0 && a.overflow() == 0,
                "Exactly " + rounds + " real Primary rounds, internal reserve/overflow zero");
    }
    private static void hud(GameTestHelper h, ServerPlayer p, int rounds, int duration, int remaining) {
        CombatHud.update(p);
        var state = WeaponRuntime.ammunition(p).orElseThrow();
        check(h, state.equals(AmmoHud.current(p).orElseThrow()) && state.rounds() == rounds
                        && state.capacity() == 14 && state.infiniteReserve() && state.reserve() == 0
                        && state.reloadRemaining() == remaining && state.reloading() == (remaining > 0),
                "HUD is the authoritative 14-round Primary phase, with infinite rather than finite reserve");
        check(h, node(p, "infinity") != null && node(p, "reserve_0") == null
                        && (node(p, "reload_track") != null) == (remaining > 0), "Actual infinity/reload HUD nodes");
        String text = Integer.toString(rounds);
        for (int i = 0; i < text.length(); i++) {
            var glyph = node(p, "rounds_" + i);
            check(h, glyph != null && Identifier.parse("destiny:gui/hud/ammo_digit_" + text.charAt(i))
                    .equals(glyph.getItem().get(DataComponents.ITEM_MODEL)), "Actual round glyph " + i);
        }
        check(h, node(p, "rounds_" + text.length()) == null, "No stale trailing HUD digit");
        if (remaining > 0) {
            check(h, state.reloadDuration() == duration, "HUD keeps initial20 versus repeat13 duration");
            near(h, state.reloadProgress(), 1 - remaining / (float) duration, "Unchanged phase progress");
            float width = 276 * (float) Math.floor(state.reloadProgress() * 8) / 8;
            var fill = node(p, "reload");
            check(h, width == 0 ? fill == null : fill != null && Math.abs(fill.getScale().x - width) < .0001f,
                    "Existing eight-step HUD fill follows actual insert progress");
        } else check(h, node(p, "reload") == null, "Cosmetic return has no gameplay reload HUD");
    }
    private static void live(GameTestHelper h, Reload r, int elapsed, int rounds, int phase, int duration, int remaining) {
        tick(r.owner());
        check(h, now(r.owner()) - r.started() == elapsed, "Actual server tick equals exact assertion deadline");
        amounts(h, r.gun(), rounds);
        check(h, WeaponRuntime.reloading(r.owner()) == (remaining > 0) && WeaponInsertPresentation.active(r.gun()),
                "Live presentation and gameplay reload have independent lifetimes");
        near(h, selector(r.gun()), phase + sample(1 - remaining / (float) duration), "Current W71 sample");
        var sent = wire(r.owner(), r.gun());
        check(h, WeaponFirstPersonHands.model(WRAPPER).equals(sent.get(DataComponents.ITEM_MODEL))
                        && Objects.equals(r.original().get(DataComponents.ITEM_MODEL), r.gun().get(DataComponents.ITEM_MODEL)),
                "Polymer selects W71 while stored model identity remains original");
        near(h, selector(sent), selector(r.gun()), "Wire carries the real current float4");
        hud(h, r.owner(), rounds, duration, remaining);
    }
    private static void restored(GameTestHelper h, Reload r) {
        check(h, !WeaponInsertPresentation.active(r.gun())
                        && Objects.equals(r.original().get(DataComponents.CUSTOM_MODEL_DATA), r.gun().get(DataComponents.CUSTOM_MODEL_DATA))
                        && Objects.equals(WeaponFirstPersonHands.model(r.original().get(DataComponents.ITEM_MODEL)), wire(r.owner(), r.gun()).get(DataComponents.ITEM_MODEL)),
                "Retirement restores exact original CMD including absent float4, never a -1 tombstone");
    }
    private static ServerPlayer listener(GameTestHelper h) {
        var ear = TestPlayers.create(h, new Vec3(2.5, 1, 4.5), 0, 0);
        ear.setGameMode(GameType.SPECTATOR);
        h.getLevel().players().add(ear);
        TestCleanup.register(h, () -> { h.getLevel().players().remove(ear); TestPlayers.remove(ear); });
        TestPlayers.drain(ear);
        return ear;
    }
    private static List<ClientboundSoundPacket> soundsAt(ServerPlayer ear, ServerPlayer source) {
        var ref = DestinySounds.packet(DestinySounds.weaponKey(entry(), "reload"), source.getEyePosition(), SoundSource.PLAYERS, .8f, 0);
        return TestPlayers.outbound(ear).stream().filter(ClientboundSoundPacket.class::isInstance)
                .map(ClientboundSoundPacket.class::cast)
                .filter(p -> p.getX() == ref.getX() && p.getY() == ref.getY() && p.getZ() == ref.getZ()).toList();
    }
    private static JsonObject model(String name) {
        String path = "/assets/destiny/models/weapon_insert_w222_long_arm/long_arm_" + name + ".json";
        var in = WeaponInsertW71GameTests.class.getResourceAsStream(path);
        if (in == null) throw new AssertionError("Missing current Long Arm resource " + path);
        try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader).getAsJsonObject();
        } catch (IOException e) { throw new AssertionError(e); }
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void acceptedReloadUsesExactFirstAndNextPairDeadlinesWithPureMidLoopReads(GameTestHelper h) {
        check(h, WeaponCharacteristics.of(entry()).bungieHash() == 8293111L && profile().magazine() == 14
                        && profile().infiniteReserve() && profile().shellReload() && profile().firstReloadTicks() == 20
                        && profile().reloadTicks() == 13 && profile().roundsPerInsert() == 2
                        && WeaponInsertPresentation.SELECTOR_INDEX == 4 && WeaponInsertPresentation.STEPS == 20
                        && WeaponInsertPresentation.RETURN_TICKS == 6 && WRAPPER.equals(WeaponInsertPresentation.model()),
                "Canonical Long Arm retains its unchanged gameplay and float4 contract");
        for (String grip : List.of("native", "twohand")) {
            check(h, model("initial_60_body_" + grip).get("display").equals(model("loop_00_body_" + grip).get("display"))
                            && model("loop_60_body_" + grip).get("display").equals(model("loop_00_body_" + grip).get("display")),
                    "Initial end, loop start and repeated loop boundary share the held transform for " + grip);
        }
        var p = player(h); var gun = equip(p, 0); var ear = listener(h); var r = start(h, p, gun);
        var sounds = soundsAt(ear, p);
        check(h, sounds.size() == 1 && sounds.getFirst().getSound().value().location().getPath()
                .equals(DestinySounds.weaponKey(entry(), "reload")), "One existing reload sound at acceptance");
        live(h, r, 0, 0, 0, 20, 20);
        drive(h, p);
        for (int i = 1; i <= 34; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                int rounds = elapsed < 20 ? 0 : elapsed < 33 ? 2 : 4;
                int duration = elapsed < 20 ? 20 : 13;
                int remaining = elapsed < 20 ? 20 - elapsed : elapsed < 33 ? 33 - elapsed : 46 - elapsed;
                live(h, r, elapsed, rounds, elapsed < 20 ? 0 : 2, duration, remaining);
                var before = gun.copy();
                for (int read = 0; read < 4; read++) {
                    WeaponInsertPresentation.active(gun); WeaponInsertPresentation.model(); wire(p, gun);
                    WeaponRuntime.ammunition(p); AmmoHud.current(p); CombatHud.update(p);
                    check(h, !WeaponRuntime.reload(p), "Duplicate reload never resets the deadline");
                }
                check(h, ItemStack.matches(before, gun), "Repeated getters/HUD/wire and denied duplicates are pure");
                if (elapsed == 19) check(h, !WeaponRuntime.beginUse(p), "Empty trigger cannot fire or credit before tick20");
                if (elapsed == 26) {
                    // Safely inside the repeat phase, away from either insert deadline.
                    WeaponAiming.tick(p); WeaponAiming.progress(p); WeaponAiming.ballistics(p, entry());
                    tick(p);
                    check(h, WeaponAiming.progress(p) == 0 && ItemStack.matches(before, gun),
                            "Actual server Aiming read/tick mid-loop cannot retire W71 or mutate insert progress");
                }
                check(h, soundsAt(ear, p).isEmpty() && WeaponRuntime.activeProjectiles(p) == 0,
                        "Insert boundaries and repeated projections produce no extra audio or shots");
                if (elapsed == 34) { WeaponRuntime.cancelUseForSkill(p); restored(h, r); h.succeed(); }
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 115, environment = "destiny-test:w90_isolated")
    public void emptyMagazineFillsOnlyAtSevenActualPairsThenReturnsForExactlySixTicks(GameTestHelper h) {
        var p = player(h); var gun = equip(p, 0); var ear = listener(h); var r = start(h, p, gun);
        check(h, soundsAt(ear, p).size() == 1, "One accepted reload audio event");
        drive(h, p);
        for (int i = 1; i <= 105; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                tick(p);
                int pairs = elapsed < 20 ? 0 : Math.min(7, 1 + (elapsed - 20) / 13);
                amounts(h, gun, pairs * 2);
                check(h, now(p) - r.started() == elapsed, "Full reload uses advancing real server ticks");
                if (elapsed < 98) {
                    int duration = elapsed < 20 ? 20 : 13;
                    int remaining = elapsed < 20 ? 20 - elapsed : 20 + pairs * 13 - elapsed;
                    live(h, r, elapsed, pairs * 2, elapsed < 20 ? 0 : 2, duration, remaining);
                } else {
                    check(h, !WeaponRuntime.reloading(p), "Last actual pair immediately ends gameplay reload at tick98");
                    hud(h, p, 14, 13, 0);
                    if (elapsed < 104) {
                        check(h, WeaponInsertPresentation.active(gun) && WeaponFirstPersonHands.model(WRAPPER).equals(wire(p, gun).get(DataComponents.ITEM_MODEL)),
                                "Cosmetic tail alone retains W71 for ticks0 through5 after last insert");
                        near(h, selector(gun), 4 + sample((elapsed - 98) / 6f), "Six-tick return sample");
                        check(h, !WeaponRuntime.reload(p), "Full-magazine reload is denied without restarting the tail");
                    } else restored(h, r);
                }
                check(h, soundsAt(ear, p).isEmpty() && WeaponRuntime.activeProjectiles(p) == 0,
                        "Seven pairs and cosmetic return never add ammunition, fire or replay audio");
                if (elapsed == 105) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 75, environment = "destiny-test:w90_isolated")
    public void finalOddRoundStopsAtFourteenAndTailCannotBlockSameTickShotOrNewReload(GameTestHelper h) {
        var p = player(h); var gun = equip(p, 11); var ear = listener(h); var r = start(h, p, gun);
        check(h, soundsAt(ear, p).size() == 1, "One initial reload sound");
        drive(h, p);
        h.runAfterDelay(19, () -> live(h, r, 19, 11, 0, 20, 1));
        h.runAfterDelay(20, () -> live(h, r, 20, 13, 2, 13, 13));
        h.runAfterDelay(32, () -> live(h, r, 32, 13, 2, 13, 1));
        h.runAfterDelay(33, () -> {
            tick(p); amounts(h, gun, 14); hud(h, p, 14, 13, 0);
            check(h, WeaponInsertPresentation.active(gun) && !WeaponRuntime.reloading(p), "Final odd insert starts only cosmetic return");
            near(h, selector(gun), 4, "Return starts at actual final-odd transfer tick");
            check(h, soundsAt(ear, p).isEmpty(), "Neither pair nor final odd insert replays audio");
            check(h, WeaponRuntime.heartbeatUse(p), "Fresh actual crossbow-carrier input fires on the same final-insert tick");
            for (int duplicate = 0; duplicate < 8; duplicate++) WeaponRuntime.heartbeatUse(p);
            amounts(h, gun, 13); restored(h, r);
            WeaponRuntime.releaseUse(p, gun);
            check(h, WeaponRuntime.reload(p), "New accepted reload immediately replaces old return despite shot recovery");
            near(h, selector(gun), 0, "New input starts a fresh initial phase immediately");
            for (int duplicate = 0; duplicate < 8; duplicate++) check(h, !WeaponRuntime.reload(p), "Same-tick duplicate reload is denied");
            var sounds = soundsAt(ear, p);
            check(h, sounds.size() == 2 && sounds.stream().filter(s -> s.getSound().value().location().getPath()
                            .equals(DestinySounds.weaponKey(entry(), "fire"))).count() == 1
                            && sounds.stream().filter(s -> s.getSound().value().location().getPath()
                            .equals(DestinySounds.weaponKey(entry(), "reload"))).count() == 1,
                    "Accepted input emits exactly one existing fire and one new reload sound despite duplicates");
        });
        h.runAfterDelay(39, () -> {
            tick(p); amounts(h, gun, 13);
            near(h, selector(gun), sample(6 / 20f), "Old six-tick expiry cannot clear a new accepted reload");
            check(h, WeaponRuntime.reloading(p), "New real reload owns its independent deadline");
        });
        h.runAfterDelay(52, () -> { tick(p); amounts(h, gun, 13); hud(h, p, 13, 20, 1); });
        h.runAfterDelay(53, () -> {
            tick(p); amounts(h, gun, 14); hud(h, p, 14, 20, 0);
            near(h, selector(gun), 4, "Only the new actual insert begins the next return");
        });
        h.runAfterDelay(59, () -> {
            tick(p); amounts(h, gun, 14); restored(h, r);
            check(h, soundsAt(ear, p).isEmpty(), "New insert and old/new return expiries add no sound");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void actualQAndCtrlQKeepWeaponAndAcceptedFSkillCancelsFuturePairImmediately(GameTestHelper h) {
        var p = player(h); var gun = equip(p, 0);
        var r = new Reload(p, gun, gun.copy(), now(p));
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.DROP_ITEM, BlockPos.ZERO, Direction.UP));
        live(h, r, 0, 0, 0, 20, 20);
        var before = gun.copy();
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.DROP_ALL_ITEMS, BlockPos.ZERO, Direction.UP));
        check(h, p.getMainHandItem() == gun && gun.getCount() == 1 && ItemStack.matches(before, gun),
                "Native Q/Ctrl-Q packets never drop, duplicate or restart Long Arm");
        drive(h, p);
        h.runAfterDelay(21, () -> {
            live(h, r, 21, 2, 2, 13, 12);
            check(h, InputRouter.onPlayerAction(p, ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND)
                            && Guardians.data(p).cooldown(AbilitySlot.GRENADE) > 0, "Actual F dispatch accepts the equipped Guardian skill");
            check(h, !WeaponRuntime.reloading(p), "Accepted skill cancels gameplay and W71 in the input tick");
            restored(h, r); amounts(h, gun, 2);
            check(h, p.getOffhandItem().is(Items.EMERALD) && p.getOffhandItem().getCount() == 4,
                    "Skill input consumes offhand-swap action without replacing real offhand");
        });
        h.runAfterDelay(47, () -> { tick(p); amounts(h, gun, 2); restored(h, r); hud(h, p, 2, 13, 0); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void actualSlotLevelSpectatorAndOwnerCleanupRetireWithoutGhostInsert(GameTestHelper h) {
        var actors = new ArrayList<ServerPlayer>(); var reloads = new ArrayList<Reload>();
        for (int i = 0; i < 4; i++) {
            var p = player(h); actors.add(p); reloads.add(start(h, p, equip(p, 0)));
        }
        drive(h, actors.toArray(ServerPlayer[]::new));
        h.runAfterDelay(10, () -> {
            for (var r : reloads) live(h, r, 10, 0, 0, 20, 10);
            var slot = actors.get(0); int selected = slot.getInventory().getSelectedSlot();
            slot.getInventory().setItem(7, new ItemStack(Items.STONE));
            slot.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(7));
            check(h, !WeaponInsertPresentation.active(reloads.get(0).gun()), "Validated slot change immediately invalidates W71");
            slot.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(selected));
            check(h, WeaponHandling.remaining(slot) > 0 && !WeaponRuntime.reload(slot), "Same-tick away/back preserves handling lock");
            var other = java.util.stream.StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                    .filter(level -> level != h.getLevel()).findFirst().orElseThrow();
            var dimension = actors.get(1); dimension.setServerLevel(other);
            check(h, !WeaponInsertPresentation.active(reloads.get(1).gun()), "Actual level mismatch immediately loses authority");
            tick(dimension); dimension.setServerLevel(h.getLevel());
            actors.get(2).setGameMode(GameType.SPECTATOR);
            check(h, !WeaponInsertPresentation.active(reloads.get(2).gun()), "Actual spectator mode immediately loses authority");
            tick(actors.get(2));
            WeaponRuntime.cleanup(actors.get(3)); WeaponRuntime.cleanup(actors.get(3));
            for (var r : reloads) { restored(h, r); amounts(h, r.gun(), 0); }
        });
        h.runAfterDelay(47, () -> {
            for (var r : reloads) {
                tick(r.owner()); restored(h, r); amounts(h, r.gun(), 0);
                check(h, !WeaponRuntime.reloading(r.owner()), "No pending reload survives an actual cleanup cause");
            }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 45, environment = "destiny-test:w90_isolated")
    public void returnToActualAdsRestoresOriginalEmptyShortAndSavedFloatsAndAllComponents(GameTestHelper h) {
        var variants = List.of(CustomModelData.EMPTY,
                new CustomModelData(List.of(7.25f, .375f), SENTINEL.flags(), SENTINEL.strings(), SENTINEL.colors()),
                SENTINEL,
                new CustomModelData(List.of(7.25f, .375f, 47f, -1f, 0f), SENTINEL.flags(), SENTINEL.strings(), SENTINEL.colors()),
                new CustomModelData(List.of(7.25f, .375f, 47f, -1f, .4f), SENTINEL.flags(), SENTINEL.strings(), SENTINEL.colors()),
                new CustomModelData(List.of(7.25f, .375f, 47f, -1f, Float.NaN), SENTINEL.flags(), SENTINEL.strings(), SENTINEL.colors()));
        var reloads = new ArrayList<Reload>();
        for (var data : variants) {
            var p = player(h); var gun = equip(p, 13);
            gun.set(DataComponents.CUSTOM_MODEL_DATA, data);
            gun.set(DataComponents.CUSTOM_NAME, Component.literal("Independent W71 component"));
            reloads.add(start(h, p, gun));
        }
        drive(h, reloads.stream().map(Reload::owner).toArray(ServerPlayer[]::new));
        h.runAfterDelay(10, () -> {
            for (var r : reloads) {
                tick(r.owner()); var before = r.gun().copy();
                var original = r.original().get(DataComponents.CUSTOM_MODEL_DATA);
                var actual = r.gun().get(DataComponents.CUSTOM_MODEL_DATA);
                check(h, actual.floats().size() == Math.max(5, original.floats().size())
                                && actual.flags().equals(original.flags()) && actual.strings().equals(original.strings())
                                && actual.colors().equals(original.colors()), "Float4 owns only its selector/padding and preserves other CMD lists");
                for (int i = 0; i < original.floats().size(); i++) if (i != 4)
                    check(h, Objects.equals(actual.getFloat(i), original.getFloat(i)), "Independent float" + i + " survives");
                var sent = wire(r.owner(), r.gun());
                check(h, sent.is(Items.CROSSBOW) && CrossbowItem.isCharged(sent) && WeaponModels.twoHanded(r.gun())
                                && Boolean.TRUE.equals(sent.get(DataComponents.CUSTOM_MODEL_DATA).getBoolean(0))
                                && sent.get(DataComponents.CUSTOM_MODEL_DATA).floats().equals(actual.floats())
                                && r.gun().get(DataComponents.CHARGED_PROJECTILES) == null
                                && r.owner().getOffhandItem().is(Items.EMERALD) && r.owner().getOffhandItem().getCount() == 4,
                        "Client-only charged two-hand grip never changes real offhand/projectiles");
                var context = ((PacketContextProvider) (Object) r.owner().connection).getPacketContext();
                check(h, ItemStack.matches(before, PolymerItemUtils.getRealItemStack(sent, context, h.getLevel().registryAccess())),
                        "Polymer roundtrip preserves authoritative components");
                for (int read = 0; read < 3; read++) { wire(r.owner(), r.gun()); CombatHud.update(r.owner()); }
                check(h, ItemStack.matches(before, r.gun()), "Independent component projections remain pure");
                WeaponAiming.releasedAim(r.owner());
            }
        });
        h.runAfterDelay(20, () -> {
            for (var r : reloads) {
                tick(r.owner()); amounts(h, r.gun(), 14);
                check(h, !WeaponRuntime.reloading(r.owner()) && WeaponInsertPresentation.active(r.gun())
                                && WeaponAiming.progress(r.owner()) == 0, "Actual last odd round starts return with ADS released");
                check(h, (int) Math.floor(selector(r.gun())) == 4, "Actual return begins at phase4");
            }
        });
        h.runAfterDelay(21, () -> {
            for (var r : reloads) {
                tick(r.owner());
                check(h, WeaponInsertPresentation.active(r.gun()) && selector(r.gun()) > 4.1f && selector(r.gun()) < 4.2f,
                        "Return advances on two actual server ticks before ADS input");
                // Reload cancelled the old ADS toggle; this is a fresh left-click request.
                check(h, WeaponAiming.toggle(r.owner()), "Fresh left-click requests ADS during cosmetic return");
            }
        });
        h.runAfterDelay(22, () -> {
            for (var r : reloads) {
                tick(r.owner());
                var data = r.gun().get(DataComponents.CUSTOM_MODEL_DATA);
                var original = r.original().get(DataComponents.CUSTOM_MODEL_DATA);
                check(h, WeaponAiming.progress(r.owner()) > 0 && WeaponAimPresentation.active(r.gun())
                                && !WeaponInsertPresentation.active(r.gun())
                                && WeaponFirstPersonHands.model(WeaponAimPresentation.model(r.gun())).equals(wire(r.owner(), r.gun()).get(DataComponents.ITEM_MODEL)),
                        "Actual fresh left-click enters W70 inside the still-unexpired W71 return");
                check(h, data.floats().size() == Math.max(4, original.floats().size())
                                && Objects.equals(data.getFloat(4), original.getFloat(4)),
                        "Return padding retires before ADS captures original floats, including absent slot4");
                amounts(h, r.gun(), 14);
                WeaponAiming.releasedAim(r.owner());
                WeaponAiming.cleanup(r.owner());
                restored(h, r);
                var expected = r.original().copy();
                WeaponItems.save(expected, new WeaponMagazine(profile(), 14, 0));
                check(h, ItemStack.matches(expected, r.gun()),
                        "Aiming cleanup restores every original component after real return-to-ADS, with only earned ammo/lore changed");
            }
        });
        h.runAfterDelay(28, () -> {
            for (var r : reloads) { tick(r.owner()); amounts(h, r.gun(), 14); restored(h, r); }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 35, environment = "destiny-test:w90_isolated")
    public void repeatedExactStackTransfersKeepRecipientBindingAndRestoreFirstOwnersOriginalFloats(GameTestHelper h) {
        var first = player(h); var second = player(h); var third = player(h);
        var gun = equip(first, 0);
        var data = new CustomModelData(List.of(7.25f, .375f, 47f, -1f, .4f), SENTINEL.flags(), SENTINEL.strings(), SENTINEL.colors());
        gun.set(DataComponents.CUSTOM_MODEL_DATA, data);
        var r = start(h, first, gun);
        var adsDonor = player(h); var adsRecipient = player(h);
        var shortGun = equip(adsDonor, 0);
        shortGun.set(DataComponents.CUSTOM_MODEL_DATA,
                new CustomModelData(List.of(), SENTINEL.flags(), SENTINEL.strings(), SENTINEL.colors()));
        var oldReload = start(h, adsDonor, shortGun);
        float[] recipientOffset = {0};
        drive(h, first, adsDonor);
        var recipients = new ArrayList<ServerPlayer>();
        // Do not create a handling session for an empty recipient before its initial equip.
        h.onEachTick(() -> recipients.forEach(WeaponInsertW71GameTests::tick));
        h.runAfterDelay(1, () -> {
            float outgoing = selector(gun);
            first.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            check(h, !WeaponInsertPresentation.active(gun), "Detached original stack has no owner authority");
            hold(second, gun, entry());
            check(h, WeaponRuntime.reload(second), "Recipient accepts its own real reload on exact transferred stack");
            recipients.add(second);
            recipientOffset[0] = selector(gun);
            check(h, recipientOffset[0] > 0 && recipientOffset[0] < .05f && recipientOffset[0] != outgoing,
                    "Acquisition has a stable small offset distinct from original .4 and outgoing sample");
            var before = gun.copy();
            WeaponRuntime.cleanup(first); WeaponRuntime.cleanup(first);
            check(h, WeaponInsertPresentation.active(gun) && ItemStack.matches(before, gun)
                            && WeaponFirstPersonHands.model(WRAPPER).equals(wire(second, gun).get(DataComponents.ITEM_MODEL)), "Late old-owner cleanup cannot clear recipient W71");
        });
        h.runAfterDelay(3, () -> {
            tick(second); near(h, selector(gun), sample(2 / 20f) + recipientOffset[0], "Recipient independently advances from its real accepted tick");
            second.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY); hold(third, gun, entry());
            check(h, WeaponRuntime.reload(third), "Third owner accepts another actual reload");
            recipients.add(third);
            var before = gun.copy();
            WeaponRuntime.cleanup(second); WeaponRuntime.cleanup(first);
            check(h, WeaponInsertPresentation.active(gun) && ItemStack.matches(before, gun), "Repeated stale-owner cleanup cannot change newest binding");
        });
        h.runAfterDelay(5, () -> {
            tick(third); var before = gun.copy();
            check(h, WeaponFirstPersonHands.model(WRAPPER).equals(wire(third, gun).get(DataComponents.ITEM_MODEL)) && ItemStack.matches(before, gun), "Newest owner alone controls wire");
            WeaponRuntime.cancelUseForSkill(third); restored(h, r);
            check(h, ItemStack.matches(r.original(), gun), "Final retirement restores pre-first-owner floats through every transfer");
            tick(adsDonor);
            check(h, WeaponRuntime.reloading(adsDonor) && WeaponInsertPresentation.active(shortGun),
                    "Separate donor still owns an actual INITIAL reload before transfer");
            adsDonor.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            hold(adsRecipient, shortGun, entry());
            // No recipient reload: its first actual ADS tick must retire the invalid donor binding.
            check(h, WeaponAiming.toggle(adsRecipient), "Recipient left-click requests ADS on transferred stack");
            tick(adsRecipient);
            check(h, WeaponAiming.progress(adsRecipient) > 0 && WeaponAimPresentation.active(shortGun)
                            && !WeaponRuntime.reloading(adsRecipient) && !WeaponInsertPresentation.active(shortGun)
                            && shortGun.get(DataComponents.CUSTOM_MODEL_DATA).floats().size() == 4
                            && shortGun.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(4) == null,
                    "Recipient ADS clears invalid old INITIAL before capturing original empty floats and W71 padding");
            var adsBefore = shortGun.copy();
            WeaponRuntime.cleanup(adsDonor); WeaponRuntime.cleanup(adsDonor);
            check(h, ItemStack.matches(adsBefore, shortGun) && WeaponAimPresentation.active(shortGun)
                            && WeaponFirstPersonHands.model(WeaponAimPresentation.model(shortGun)).equals(wire(adsRecipient, shortGun).get(DataComponents.ITEM_MODEL)),
                    "Late old reload cleanup cannot clear recipient ADS binding or its components");
            recipients.add(adsRecipient);
        });
        h.runAfterDelay(6, () -> {
            tick(adsRecipient);
            check(h, WeaponAiming.progress(adsRecipient) > 1 / 7f && WeaponAimPresentation.active(shortGun),
                    "Recipient ADS independently advances on its next actual server tick");
            WeaponAiming.releasedAim(adsRecipient);
            WeaponAiming.cleanup(adsRecipient);
            restored(h, oldReload);
            check(h, ItemStack.matches(oldReload.original(), shortGun),
                    "Recipient Aiming cleanup restores full pre-donor stack, including an exactly empty original float list");
        });
        h.runAfterDelay(26, () -> {
            tick(third); tick(adsRecipient); restored(h, r); restored(h, oldReload);
            amounts(h, gun, 0); amounts(h, shortGun, 0); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void liveCopyNbtAndActuallyHeldOpPreviewCannotAuthorizeReloadOrGhostAmmunition(GameTestHelper h) {
        var p = player(h); var gun = equip(p, 0); var r = start(h, p, gun);
        var owners = new ArrayList<ServerPlayer>(); var replicas = new ArrayList<ItemStack>();
        drive(h, p);
        h.onEachTick(() -> owners.forEach(WeaponInsertW71GameTests::tick));
        h.runAfterDelay(10, () -> {
            live(h, r, 10, 0, 0, 20, 10);
            var ops = h.getLevel().registryAccess().createSerializationContext(NbtOps.INSTANCE);
            var decoded = ItemStack.CODEC.parse(ops, ItemStack.CODEC.encodeStart(ops, gun).getOrThrow()).getOrThrow();
            var preview = WeaponModels.create(entry());
            preview.set(DataComponents.CUSTOM_MODEL_DATA, gun.get(DataComponents.CUSTOM_MODEL_DATA));
            for (var replica : List.of(gun.copy(), decoded, preview)) {
                var other = player(h); hold(other, replica, entry()); var before = replica.copy();
                tick(other); CombatHud.update(other); owners.add(other); replicas.add(replica);
                check(h, !WeaponInsertPresentation.active(replica) && !WeaponRuntime.reloading(other)
                                && node(other, "reload_track") == null && ItemStack.matches(before, replica)
                                && WeaponFirstPersonHands.model(replica.get(DataComponents.ITEM_MODEL)).equals(wire(other, replica).get(DataComponents.ITEM_MODEL)),
                        "Actually held copy/NBT/OP preview inherits saved selector but no W71/gameplay/HUD authority");
                if (replica == preview) check(h, !WeaponRuntime.reload(other) && !WeaponRuntime.beginUse(other),
                        "Real OP preview remains noncombat despite copied live presentation data");
            }
        });
        h.runAfterDelay(27, () -> {
            tick(p); amounts(h, gun, 2);
            for (int i = 0; i < owners.size(); i++) {
                var other = owners.get(i); var replica = replicas.get(i); tick(other);
                check(h, !WeaponInsertPresentation.active(replica) && !WeaponRuntime.reloading(other)
                                && WeaponFirstPersonHands.model(replica.get(DataComponents.ITEM_MODEL)).equals(wire(other, replica).get(DataComponents.ITEM_MODEL)),
                        "Original accepted insert deadline cannot authorize any replica");
                if (WeaponItems.entry(replica).isPresent()) amounts(h, replica, 0);
            }
            WeaponRuntime.cancelUseForSkill(p); restored(h, r); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 15, environment = "destiny-test:w90_isolated")
    public void actualAimThenReloadRoutesLongArmAndFirstInLastOutAndExcludesOtherCatalogEntries(GameTestHelper h) {
        WeaponModelGameTests.assertCatalogExpansion(h);
        check(h, WeaponModelGameTests.originalW30Entries().stream().filter(e -> !e.id().equals("long_arm")).count() == 62,
                "Original W30 catalog still contains 62 entries besides Long Arm");
        var actors = new ArrayList<ServerPlayer>();
        for (var e : WeaponCatalog.all()) {
            var p = player(h); var gun = WeaponItems.create(e); var f = WeaponProfile.forEntry(e);
            WeaponItems.save(gun, new WeaponMagazine(f, 0, f.infiniteReserve() ? 0 : f.reserve()));
            hold(p, gun, e); tick(p); gun.set(DataComponents.CUSTOM_MODEL_DATA, SENTINEL);
            if (WeaponAimProfile.supports(e)) check(h, WeaponAiming.toggle(p), "Supported weapon accepts left-click ADS");
            actors.add(p);
        }
        h.runAfterDelay(1, () -> {
            int supported = 0, excluded = 0;
            for (var p : actors) {
                tick(p); var gun = p.getMainHandItem(); var e = WeaponItems.entry(gun).orElseThrow();
                if (WeaponAimProfile.supports(e)) check(h, WeaponAimPresentation.active(gun)
                                && WeaponFirstPersonHands.model(WeaponAimPresentation.model(gun)).equals(wire(p, gun).get(DataComponents.ITEM_MODEL)),
                        "Actual ADS input owns W70 before reload: " + e.id());
                boolean accepted = WeaponRuntime.reload(p);
                check(h, accepted == !e.family().equals("sword"), "Actual reload acceptance retains existing family policy: " + e.id());
                boolean longArm = e.id().equals("long_arm");
                boolean insert = INSERT_ROUTES.containsKey(e.id());
                if (insert) check(h, Identifier.parse("destiny:" + INSERT_ROUTES.get(e.id()))
                        .equals(WeaponInsertPresentation.model(e)), "Exact authored insert route: " + e.id());
                check(h, WeaponInsertPresentation.supports(e) == insert && WeaponInsertPresentation.active(gun) == insert,
                        "Exact W71 catalog authorization: " + e.id());
                if (longArm) {
                    supported++;
                    check(h, accepted && WeaponFirstPersonHands.model(WRAPPER).equals(wire(p, gun).get(DataComponents.ITEM_MODEL))
                                    && !WeaponAimPresentation.active(gun) && !WeaponReloadPresentation.active(gun),
                            "Accepted Long Arm input immediately replaces W70 with higher-priority W71");
                    near(h, selector(gun), 0, "W71 initial phase starts in actual accepted input tick");
                } else if (insert) {
                    supported++;
                    check(h, accepted && WeaponFirstPersonHands.model(WeaponInsertPresentation.model(e)).equals(wire(p, gun).get(DataComponents.ITEM_MODEL))
                            && !WeaponFirstPersonHands.model(WRAPPER).equals(wire(p, gun).get(DataComponents.ITEM_MODEL))
                            && !WeaponAimPresentation.active(gun) && !WeaponReloadPresentation.active(gun),
                            "Single-shell shotguns use their own routes, never Long Arm's graph");
                } else {
                    excluded++;
                    check(h, !WeaponFirstPersonHands.model(WRAPPER).equals(wire(p, gun).get(DataComponents.ITEM_MODEL)) && selector(gun) == 99f,
                            "Other catalog entries never write float4 or use W71");
                    if (WeaponReloadPresentation.active(gun)) check(h,
                            WeaponFirstPersonHands.model(WeaponReloadPresentation.model(e)).equals(wire(p, gun).get(DataComponents.ITEM_MODEL)),
                            "Existing whole-magazine model priority survives: " + e.id());
                }
            }
            check(h, supported == 6 && excluded == 59, "All65 entries cover Long Arm and five authored shotguns;59 exclusions including Ace and Izanagi");
        });
        h.runAfterDelay(2, () -> {
            for (var p : actors) {
                tick(p); var gun = p.getMainHandItem(); var e = WeaponItems.entry(gun).orElseThrow();
                check(h, WeaponInsertPresentation.active(gun) == INSERT_ROUTES.containsKey(e.id()), "Real next server tick preserves exact support boundary");
                WeaponRuntime.cancelUseForSkill(p);
            }
            h.succeed();
        });
    }
}
