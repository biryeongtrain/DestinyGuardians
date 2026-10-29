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
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
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
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** Real advancing server phases and Polymer/HUD projections; no native rendering claim.
 * Presentation starts only through accepted gameplay reloads, never direct activation or a synthetic clock.
 */
public final class AutoRifleReloadW69GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String AMMIT = "ammit_ar2";
    private static final int DURATION = 41;
    private static final float EPS = .0001f;
    private static final Identifier WRAPPER = Identifier.fromNamespaceAndPath("destiny", "weapon_reload_w207_ammit_ar2/ammit_ar2");
    private record Reload(ServerPlayer owner, ItemStack gun, Identifier base, long started) {}

    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static WeaponCatalog.Entry entry() { return WeaponCatalog.find(AMMIT).orElseThrow(); }
    private static WeaponProfile profile() { return WeaponProfile.forEntry(entry()); }
    private static WeaponMagazine ammo(ItemStack gun) { return WeaponItems.magazine(gun, profile()); }
    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 0);
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setOnGround(true);
        TestCleanup.register(h, () -> {
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            TestPlayers.remove(p);
        });
        return p;
    }
    private static void hold(ServerPlayer p, ItemStack gun) {
        int slot = WeaponCharacteristics.of(entry()).slot().hotbar();
        p.getInventory().setItem(slot, gun);
        p.getInventory().setSelectedSlot(slot);
        WeaponRuntime.tickPlayer(p);
        TestPlayers.drain(p);
    }
    private static ItemStack equip(ServerPlayer p, int rounds) {
        var gun = WeaponItems.create(entry());
        WeaponItems.save(gun, new WeaponMagazine(profile(), rounds, 0));
        hold(p, gun);
        return gun;
    }
    private static Reload start(GameTestHelper h, ServerPlayer p, ItemStack gun) {
        var r = new Reload(p, gun, gun.get(DataComponents.ITEM_MODEL), now(p));
        check(h, WeaponRuntime.reload(p), "Actual Ammit reload is accepted");
        check(h, WeaponReloadPresentation.supports(entry()) && WRAPPER.equals(WeaponReloadPresentation.model(entry()))
                        && WeaponReloadPresentation.PROGRESS_INDEX == 1 && progress(gun) == 0,
                "Accepted Ammit starts its authored reload at float slot 1, sample zero");
        live(h, r, 0);
        return r;
    }
    private static void drive(GameTestHelper h, ServerPlayer... players) {
        h.onEachTick(() -> {
            for (var p : players) { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); }
        });
    }
    private static float progress(ItemStack gun) {
        return gun.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY)
                .getFloat(WeaponReloadPresentation.PROGRESS_INDEX);
    }
    private static ItemStack wire(ServerPlayer p, ItemStack gun) {
        var context = ((PacketContextProvider) (Object) p.connection).getPacketContext();
        return PolymerItemUtils.getPolymerItemStack(gun, context, p.level().registryAccess());
    }
    private static ItemDisplayHud node(ServerPlayer p, String suffix) {
        return (ItemDisplayHud) DisplayHud.getHud(p, AmmoHud.PREFIX + suffix);
    }
    private static void digits(GameTestHelper h, ServerPlayer p, int rounds) {
        String text = Integer.toString(rounds);
        for (int i = 0; i < text.length(); i++) {
            var glyph = node(p, "rounds_" + i);
            check(h, glyph != null && Identifier.fromNamespaceAndPath("destiny", "gui/hud/ammo_digit_" + text.charAt(i))
                    .equals(glyph.getItem().get(DataComponents.ITEM_MODEL)), "HUD digits show authoritative rounds=" + rounds);
        }
        check(h, node(p, "rounds_" + text.length()) == null, "No stale trailing round glyph");
    }
    private static void amounts(GameTestHelper h, ItemStack gun, int rounds) {
        var a = ammo(gun);
        check(h, a.rounds() == rounds && a.reserve() == 0 && a.overflow() == 0,
                "Primary magazine has exactly " + rounds + " rounds and no fabricated reserve/overflow");
    }
    private static void live(GameTestHelper h, Reload r, int elapsed) {
        WeaponRuntime.tickPlayer(r.owner()); CombatHud.update(r.owner());
        var state = WeaponRuntime.ammunition(r.owner()).orElseThrow();
        check(h, now(r.owner()) - r.started() == elapsed && WeaponRuntime.reloading(r.owner())
                        && state.reloading() && state.reloadDuration() == DURATION
                        && state.reloadRemaining() == DURATION - elapsed,
                "Actual server phase retains its original 41-tick deadline");
        float phase = elapsed / (float) DURATION;
        check(h, Math.abs(state.reloadProgress() - phase) < EPS, "HUD progress follows elapsed real server ticks");
        float expected = (float) Math.floor(phase * 60 + 1e-6f) / 60;
        var sent = wire(r.owner(), r.gun());
        check(h, WeaponReloadPresentation.active(r.gun()) && Math.abs(progress(r.gun()) - expected) < EPS
                        && WeaponFirstPersonHands.model(WRAPPER).equals(sent.get(DataComponents.ITEM_MODEL)) && Math.abs(progress(sent) - expected) < EPS
                        && r.base().equals(r.gun().get(DataComponents.ITEM_MODEL)),
                "Live wire uses the authored reload hand wrapper and one of 61 server-progress samples while stored model stays base");
        check(h, AmmoHud.current(r.owner()).orElseThrow().equals(state) && state.infiniteReserve()
                        && node(r.owner(), "infinity") != null && node(r.owner(), "reserve_0") == null
                        && node(r.owner(), "reload_track") != null, "Actual HUD reflects the Primary reload phase");
        digits(h, r.owner(), ammo(r.gun()).rounds());
        float width = 276 * (float) Math.floor(state.reloadProgress() * 8) / 8;
        var fill = node(r.owner(), "reload");
        check(h, width == 0 ? fill == null : fill != null && Math.abs(fill.getScale().x - width) < EPS,
                "HUD fill retains the existing eight-step full-phase progress");
    }
    private static void retired(GameTestHelper h, Reload r) {
        WeaponRuntime.tickPlayer(r.owner()); CombatHud.update(r.owner());
        check(h, !WeaponRuntime.reloading(r.owner()) && !WeaponReloadPresentation.active(r.gun())
                        && progress(r.gun()) == -1 && !AmmoHud.current(r.owner()).orElseThrow().reloading()
                        && node(r.owner(), "reload_track") == null && node(r.owner(), "reload") == null
                        && r.base().equals(r.gun().get(DataComponents.ITEM_MODEL))
                        && WeaponFirstPersonHands.model(r.base()).equals(wire(r.owner(), r.gun()).get(DataComponents.ITEM_MODEL)),
                "Retirement clears ACTIVE, selector, phase HUD and wrapper without replacing stored identity");
    }

    @GameTest(structure = FLOOR, maxTicks = 70, environment = "destiny-test:w90_isolated")
    public void acceptedReloadProjectsActualPhaseWireAndHud(GameTestHelper h) {
        var p = player(h, 6.5);
        var r = start(h, p, equip(p, 2));
        drive(h, p);
        h.runAfterDelay(20, () -> {
            live(h, r, 20); amounts(h, r.gun(), 2);
            var saved = r.gun().copy();
            for (int i = 0; i < 4; i++) {
                AmmoHud.current(p); CombatHud.update(p); wire(p, r.gun());
                check(h, !WeaponRuntime.reload(p), "Duplicate reload cannot restart the accepted phase");
            }
            check(h, ItemStack.matches(saved, r.gun()), "HUD/wire reads and denied duplicates cannot mutate progress or ammo");
            live(h, r, 20);
        });
        h.runAfterDelay(DURATION, () -> {
            retired(h, r); amounts(h, r.gun(), 33); digits(h, p, 33);
            check(h, node(p, "infinity") != null, "Completion retains Primary infinity HUD");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 70, environment = "destiny-test:w90_isolated")
    public void infinitePrimaryCreditsMagazineOnlyAtUnchangedDeadline(GameTestHelper h) {
        var f = profile();
        var plan = new WeaponReloadPolicy.Plan(f.firstReloadTicks(), f.reloadTicks(), f.roundsPerInsert());
        check(h, f.infiniteReserve() && f.magazine() == 33 && !f.shellReload()
                        && f.firstReloadTicks() == DURATION && ReloadCreditProfile.ammoTicks(entry(), plan) == DURATION,
                "Ammit keeps its existing Primary capacity and coincident ammo-credit/full deadline");
        var p = player(h, 6.5);
        var r = start(h, p, equip(p, 2));
        drive(h, p);
        h.runAfterDelay(DURATION - 1, () -> {
            live(h, r, DURATION - 1); amounts(h, r.gun(), 2);
            var saved = r.gun().copy();
            check(h, !WeaponRuntime.beginUse(p) && !WeaponRuntime.reload(p), "Last pre-deadline tick denies firing and duplicate reload");
            WeaponRuntime.releaseUse(p, r.gun());
            check(h, ItemStack.matches(saved, r.gun()), "Denied fire cannot grant early ammunition or retire presentation");
        });
        h.runAfterDelay(DURATION, () -> {
            retired(h, r); amounts(h, r.gun(), 33);
            check(h, WeaponRuntime.beginUse(p), "Firing unlocks at the unchanged actual deadline");
            WeaponRuntime.releaseUse(p, r.gun()); amounts(h, r.gun(), 32);
        });
        h.runAfterDelay(50, () -> {
            retired(h, r); amounts(h, r.gun(), 32); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 70, environment = "destiny-test:w90_isolated")
    public void sameTickQReloadAndSkillCancellationInvalidateWireWithoutGhostCredit(GameTestHelper h) {
        var p = player(h, 6.5);
        var gun = equip(p, 2);
        var r = new Reload(p, gun, gun.get(DataComponents.ITEM_MODEL), now(p));
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.DROP_ITEM, BlockPos.ZERO, Direction.UP));
        live(h, r, 0);
        var started = gun.copy();
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.DROP_ALL_ITEMS, BlockPos.ZERO, Direction.UP));
        check(h, p.getMainHandItem() == gun && gun.getCount() == 1 && ItemStack.matches(started, gun),
                "Q and duplicate Ctrl-Q consume native drop input without dropping or restarting the weapon");
        WeaponRuntime.cancelUseForSkill(p);
        check(h, now(p) == r.started() && !ItemStack.matches(started, gun), "Same-tick cancellation invalidates the wire cache selector");
        retired(h, r); amounts(h, gun, 2);
        drive(h, p);
        h.runAfterDelay(DURATION + 1, () -> {
            retired(h, r); amounts(h, gun, 2); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 70, environment = "destiny-test:w90_isolated")
    public void slotSuperAndOwnerCleanupRetireAcceptedReloads(GameTestHelper h) {
        var a = player(h, 3.5); var b = player(h, 6.5); var c = player(h, 9.5);
        var swapped = start(h, a, equip(a, 2));
        var superseded = start(h, b, equip(b, 2));
        var cleaned = start(h, c, equip(c, 2));
        int slot = a.getInventory().getSelectedSlot();
        a.getInventory().setItem(7, new ItemStack(Items.STONE));
        a.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(7));
        a.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot));
        check(h, now(a) == swapped.started() && a.getMainHandItem() == swapped.gun()
                        && WeaponHandling.remaining(a) > 0 && !WeaponRuntime.reload(a),
                "Validated same-tick away/back cancels reload and retains the existing handling lock");
        Guardians.data(b).setSuperEnergy(1);
        check(h, AbilityService.use(b, AbilitySlot.SUPER) == AbilityService.Result.OK, "Real charged Solar super is accepted");
        check(h, !WeaponRuntime.reloading(b) && !WeaponReloadPresentation.active(superseded.gun()),
                "Accepted super immediately retires reload authority");
        AbilityService.endSuper(b);
        WeaponRuntime.cleanup(c); WeaponRuntime.cleanup(c);
        for (var r : List.of(swapped, superseded, cleaned)) { retired(h, r); amounts(h, r.gun(), 2); }
        drive(h, a, b, c);
        h.runAfterDelay(DURATION + 1, () -> {
            for (var r : List.of(swapped, superseded, cleaned)) { retired(h, r); amounts(h, r.gun(), 2); }
            h.succeed();
        });
    }

    private static void independentData(GameTestHelper h, Reload r, CustomModelData original) {
        var data = r.gun().get(DataComponents.CUSTOM_MODEL_DATA);
        var sent = wire(r.owner(), r.gun());
        var sentData = sent.get(DataComponents.CUSTOM_MODEL_DATA);
        check(h, data.floats().size() == original.floats().size() && data.getFloat(0) == 7f && data.getFloat(2) == 13f
                        && data.flags().equals(original.flags()) && data.strings().equals(original.strings())
                        && data.colors().equals(original.colors()) && sentData.floats().equals(data.floats())
                        && sentData.strings().equals(data.strings()) && sentData.colors().equals(data.colors()),
                "Only progress slot 1 changes; independent server CMD fields and wire float/string/color data survive");
        check(h, WeaponModels.twoHanded(r.gun()) && sent.is(Items.CROSSBOW) && CrossbowItem.isCharged(sent)
                        && Boolean.TRUE.equals(sentData.getBoolean(0)) && r.gun().get(DataComponents.CHARGED_PROJECTILES) == null
                        && r.owner().getOffhandItem().is(Items.EMERALD) && r.owner().getOffhandItem().getCount() == 4,
                "Two-hand grip keeps its client-only charged carrier without server ammunition or offhand changes");
    }

    @GameTest(structure = FLOOR, maxTicks = 70, environment = "destiny-test:w90_isolated")
    public void progressPreservesUnrelatedCmdAndTwoHandGripThroughRetirement(GameTestHelper h) {
        var p = player(h, 6.5);
        var gun = equip(p, 2);
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.EMERALD, 4));
        var independent = new CustomModelData(List.of(7f, -1f, 13f), List.of(true, false),
                List.of("hip", "w69-independent"), List.of(0xABCDEF));
        gun.set(DataComponents.CUSTOM_MODEL_DATA, independent);
        var r = start(h, p, gun);
        independentData(h, r, independent);
        drive(h, p);
        h.runAfterDelay(20, () -> { live(h, r, 20); independentData(h, r, independent); });
        h.runAfterDelay(DURATION, () -> {
            retired(h, r); independentData(h, r, independent); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 70, environment = "destiny-test:w90_isolated")
    public void savedAndCopiedProgressCannotAcquireActiveOrWireAuthority(GameTestHelper h) {
        var p = player(h, 6.5);
        var r = start(h, p, equip(p, 2));
        var replicas = new ArrayList<ItemStack>();
        var owners = new ArrayList<ServerPlayer>();
        drive(h, p);
        h.onEachTick(() -> owners.forEach(other -> { WeaponRuntime.tickPlayer(other); TestPlayers.drain(other); }));
        h.runAfterDelay(20, () -> {
            live(h, r, 20);
            var ops = h.getLevel().registryAccess().createSerializationContext(NbtOps.INSTANCE);
            var encoded = ItemStack.CODEC.encodeStart(ops, r.gun()).getOrThrow();
            var decoded = ItemStack.CODEC.parse(ops, encoded).getOrThrow();
            for (var replica : List.of(r.gun().copy(), decoded)) {
                check(h, ItemStack.matches(replica, r.gun()) && progress(replica) > 0
                                && !WeaponReloadPresentation.active(replica), "Copied/serialized live CMD carries no ACTIVE identity");
                var other = player(h, owners.isEmpty() ? 3.5 : 9.5);
                var before = replica.copy();
                hold(other, replica); CombatHud.update(other);
                replicas.add(replica); owners.add(other);
                check(h, !WeaponRuntime.reloading(other) && !AmmoHud.current(other).orElseThrow().reloading()
                                && !WeaponReloadPresentation.active(replica) && node(other, "reload_track") == null
                                && WeaponFirstPersonHands.model(r.base()).equals(wire(other, replica).get(DataComponents.ITEM_MODEL))
                                && ItemStack.matches(before, replica),
                        "Actually held saved/copy cannot fake a reload, HUD phase or W69 wire wrapper");
            }
            live(h, r, 20);
        });
        h.runAfterDelay(DURATION + 1, () -> {
            retired(h, r); amounts(h, r.gun(), 33);
            check(h, replicas.size() == 2, "Both ordinary copy and real NBT roundtrip were checked");
            for (int i = 0; i < replicas.size(); i++) {
                var replica = replicas.get(i); var other = owners.get(i);
                amounts(h, replica, 2);
                check(h, !WeaponRuntime.reloading(other) && !WeaponReloadPresentation.active(replica)
                                && WeaponFirstPersonHands.model(r.base()).equals(wire(other, replica).get(DataComponents.ITEM_MODEL)),
                        "Original deadline cannot grant ghost ammunition or authority to a saved/copy stack");
            }
            h.succeed();
        });
    }
}
