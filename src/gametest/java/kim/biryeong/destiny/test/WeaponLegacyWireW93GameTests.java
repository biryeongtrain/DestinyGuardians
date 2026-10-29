package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundContainerSetContentPacket;
import net.minecraft.network.protocol.game.ClientboundContainerSetSlotPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerListener;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemStackTemplate;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.ChargedProjectiles;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.item.component.UseEffects;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/** Native menu -> synchronizer -> encoded bytes -> context-free client decode, using W92 unchanged.
 * Production inputs and advancing server ticks establish authority; no fabricated runtime bindings.
 * This is packet evidence, not native client rendering, keyboard, or acoustic-output evidence.
 */
public final class WeaponLegacyWireW93GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final String ISOLATED = "destiny-test:w90_isolated";
    private static final CustomModelData SENTINEL = new CustomModelData(
            List.of(17f, .375f, 47f, -1f, 99f, 91.125f, 96.125f, 73f),
            List.of(true, false, true), List.of("hip", "w93_keep", "extra"), List.of(0x123456, 0xABCDEF));

    private static void check(GameTestHelper h, boolean yes, String why) {
        h.assertTrue(yes, Component.literal(why));
    }
    private static void near(GameTestHelper h, float actual, float expected, String why) {
        check(h, Math.abs(actual - expected) < .00001f, why + ": " + actual + " != " + expected);
    }
    private static CustomModelData data(ItemStack s) {
        return s.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
    }
    private static WeaponCatalog.Entry entry(ItemStack s) { return WeaponItems.entry(s).orElseThrow(); }
    private static WeaponProfile profile(ItemStack s) { return WeaponProfile.forEntry(entry(s)); }
    private static WeaponMagazine ammo(ItemStack s) { return WeaponItems.magazine(s, profile(s)); }
    private static Identifier canonical(ItemStack s) { return Identifier.parse(entry(s).item_model()); }
    private static Identifier route(String path) { return Identifier.parse("destiny:" + path); }
    private static Identifier reloadModel(ItemStack s) {
        return route(switch (entry(s).id()) {
            case "beloved" -> "weapon_reload_w208_beloved/beloved";
            case "duke_mk_44" -> "weapon_reload_w215_duke_mk_44/duke_mk_44";
            case "ammit_ar2" -> "weapon_reload_w207_ammit_ar2/ammit_ar2";
            case "biting_winds", "whispering_slab" -> "weapon_reload_w222_" + entry(s).id() + "/" + entry(s).id();
            default -> throw new IllegalArgumentException("Not a legacy magazine reload");
        });
    }
    private static Identifier aimModel(ItemStack s, boolean bow) {
        return aimRoute(entry(s).id(), bow);
    }
    private static Identifier bowModel(ItemStack s) { return route("weapon_bow_w50/" + entry(s).id()); }
    private static float denseSample(float p) { return (float) Math.floor(p * 60 + 1e-6f) / 60; }
    private static float sample(float p) { return (float) Math.floor(p * 20 + 1e-6f) / 20; }
    private static int menuSlot(ServerPlayer p) {
        return p.inventoryMenu.findSlot(p.getInventory(), p.getInventory().getSelectedSlot()).orElseThrow();
    }
    private static boolean inactive(ItemStack s) {
        return !WeaponReloadPresentation.active(s) && !WeaponInsertPresentation.active(s)
                && !WeaponAimPresentation.active(s) && !WeaponBowPresentation.active(s)
                && !WeaponSwapPresentation.active(s) && !WeaponIzanagiPresentation.active(s);
    }
    private static void amounts(GameTestHelper h, ItemStack s, int rounds, int reserve) {
        var a = ammo(s);
        check(h, a.rounds() == rounds && a.reserve() == reserve && a.overflow() == 0,
                entry(s).id() + " actual magazine/reserve/overflow = " + rounds + "/" + reserve + "/0");
    }
    private static void reload(GameTestHelper h, InventoryWireW92 w) {
        w.player.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.DROP_ITEM, BlockPos.ZERO, Direction.UP));
        check(h, WeaponRuntime.reloading(w.player), "Production Q packet starts a real reload cycle");
    }

    private static final class Fixture {
        final GameTestHelper h;
        final long created;
        final List<InventoryWireW92> wires = new ArrayList<>();

        Fixture(GameTestHelper h) {
            this.h = h; created = h.getLevel().getServer().getTickCount();
            check(h, !h.getLevel().getGameRules().get(GameRules.SPAWN_MOBS),
                    "W90 isolated environment disables natural spawning before setup");
            for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
            h.onEachTick(() -> {
                var o = h.absoluteVec(Vec3.ZERO);
                for (var w : wires) {
                    var b = w.player.getBoundingBox();
                    check(h, w.player.level() == h.getLevel() && b.minX > o.x && b.maxX < o.x + 48
                                    && b.minY > o.y && b.maxY < o.y + 12 && b.minZ > o.z && b.maxZ < o.z + 32,
                            "Entire owned player AABB stays inside the W90 fixture");
                }
            });
        }
        InventoryWireW92 player() {
            int i = wires.size();
            var w = new InventoryWireW92(h, new Vec3(4 + 6 * (i % 7), 4, 8 + 8 * (i / 7)));
            wires.add(w); w.player.setAttached(WeaponLoadout.ENABLED, false);
            var listener = new ContainerListener() {
                @Override public void slotChanged(AbstractContainerMenu menu, int slot, ItemStack s) {
                    if (s.is(WeaponCombatItem.INSTANCE))
                        check(h, canonical(s).equals(s.get(DataComponents.ITEM_MODEL)),
                                "Server slot listeners retain canonical combat snapshots");
                    check(h, !(s.is(Items.STICK) || s.is(Items.CROSSBOW)) || !s.has(DataComponents.ITEM_MODEL),
                            "Wire carriers never replace server listener snapshots");
                }
                @Override public void dataChanged(AbstractContainerMenu menu, int index, int value) {}
            };
            w.player.inventoryMenu.addSlotListener(listener);
            TestCleanup.register(h, () -> w.player.inventoryMenu.removeSlotListener(listener));
            return w; // W92 itself registered its channel/player teardown before construction.
        }
        ItemStack equip(InventoryWireW92 w, String id, int loaded, int reserve, WeaponModels.Grip grip) {
            var e = WeaponCatalog.find(id).orElseThrow();
            var s = WeaponModels.withGrip(WeaponItems.create(e), grip).orElseThrow();
            s.set(DataComponents.CUSTOM_NAME, Component.literal("W93_" + UUID.randomUUID()));
            s.set(DataComponents.CUSTOM_MODEL_DATA, SENTINEL);
            s.set(DataComponents.CHARGED_PROJECTILES, ChargedProjectiles.of(new ItemStackTemplate(Items.SPECTRAL_ARROW)));
            WeaponItems.save(s, new WeaponMagazine(WeaponProfile.forEntry(e), loaded, reserve));
            w.player.getInventory().setItem(0, s); w.player.getInventory().setSelectedSlot(0);
            WeaponRuntime.tickPlayer(w.player);
            full(h, w, canonical(s)); // Prime the real RemoteSlot before changing live components.
            return s;
        }
        void at(int tick, Runnable action) {
            check(h, h.getLevel().getServer().getTickCount() == created,
                    "All deadlines are registered during initialization, never in another deadline");
            h.runAfterDelay(tick, () -> {
                check(h, h.getLevel().getServer().getTickCount() - created == tick, "Actual server deadline " + tick);
                for (var w : wires) WeaponRuntime.tickPlayer(w.player);
                action.run();
            });
        }
    }

    private static ItemStack selectedSlot(GameTestHelper h, InventoryWireW92 w, List<Packet<?>> packets) {
        var p = w.player;
        var frames = packets.stream().filter(ClientboundContainerSetSlotPacket.class::isInstance)
                .map(ClientboundContainerSetSlotPacket.class::cast)
                .filter(f -> f.getContainerId() == p.inventoryMenu.containerId && f.getSlot() == menuSlot(p)).toList();
        check(h, frames.size() == 1, "Native incremental has exactly one selected-slot frame; actual " + frames.size());
        var frame = frames.getFirst();
        check(h, frame.getStateId() > 0 && frame.getStateId() <= p.inventoryMenu.getStateId(),
                "Incremental frame retains a native ordered menu stateId");
        return frame.getItem();
    }
    private static ItemStack selectedContent(GameTestHelper h, InventoryWireW92 w, List<Packet<?>> packets) {
        var p = w.player;
        var frames = packets.stream().filter(ClientboundContainerSetContentPacket.class::isInstance)
                .map(ClientboundContainerSetContentPacket.class::cast)
                .filter(f -> f.containerId() == p.inventoryMenu.containerId).toList();
        check(h, frames.size() == 1, "Native full sync has exactly one inventory-content frame");
        var frame = frames.getFirst();
        check(h, frame.stateId() == p.inventoryMenu.getStateId() && frame.items().size() == p.inventoryMenu.slots.size()
                        && frame.carriedItem().isEmpty(), "Full sync keeps stateId, native slot count and empty carried stack");
        return frame.items().get(menuSlot(p));
    }
    private static void carrier(GameTestHelper h, InventoryWireW92 w, ItemStack source, ItemStack decoded, Identifier model) {
        boolean two = WeaponModels.twoHanded(source);
        check(h, decoded != source && decoded.is(two ? Items.CROSSBOW : Items.STICK)
                        && !decoded.is(WeaponCombatItem.INSTANCE), "Context-free client decode sees the actual vanilla grip carrier");
        check(h, projected(model).equals(decoded.get(DataComponents.ITEM_MODEL)),
                "Encoded ITEM_MODEL = " + model + "; actual " + decoded.get(DataComponents.ITEM_MODEL));
        var a = data(source); var b = data(decoded);
        check(h, b.floats().equals(a.floats()) && b.strings().equals(a.strings()) && b.colors().equals(a.colors())
                        && b.flags().equals(wireFlags(source)), "Bytes preserve all selectors/pose/extra data; only grip flags follow the carrier contract");
        check(h, two ? Objects.equals(decoded.get(DataComponents.CHARGED_PROJECTILES),
                        ChargedProjectiles.of(new ItemStackTemplate(Items.ARROW))) : !decoded.has(DataComponents.CHARGED_PROJECTILES),
                "Crossbow heartbeat arrow / native carrier charge removal survives encoding");
        check(h, !decoded.has(DataComponents.FOOD) && decoded.has(DataComponents.CONSUMABLE) == !two
                        && new UseEffects(true, false, 1f).equals(decoded.get(DataComponents.USE_EFFECTS)),
                "Existing carrier consumable, food-removal and use-effects contract survives encoding");
        check(h, inactive(decoded) && inactive(source.copy()), "Decoded carrier and component-exact copy have no live helper authority");
        var context = ((PacketContextProvider) (Object) w.player.connection).getPacketContext();
        var restored = PolymerItemUtils.getRealItemStack(decoded, context, w.player.registryAccess());
        check(h, restored != decoded && ItemStack.matches(restored, source) && inactive(restored)
                        && canonical(source).equals(restored.get(DataComponents.ITEM_MODEL)),
                "Separate server restoration preserves canonical real components and ammunition without granting authority");
    }
    private static void unchanged(GameTestHelper h, InventoryWireW92 w, ItemStack source, ItemStack before) {
        check(h, w.player.getMainHandItem() == source && source.is(WeaponCombatItem.INSTANCE)
                        && ItemStack.matches(source, before) && canonical(source).equals(source.get(DataComponents.ITEM_MODEL)),
                "Transport preserves exact selected identity, canonical model and every component/ammo value");
        check(h, PacketContext.get() == null, "Native encoding and client decoding leave no recipient context");
    }
    private static void full(GameTestHelper h, InventoryWireW92 w, Identifier model) {
        var s = w.player.getMainHandItem(); var before = s.copy();
        carrier(h, w, s, selectedContent(h, w, w.full()), model);
        unchanged(h, w, s, before);
    }
    private static void both(GameTestHelper h, InventoryWireW92 w, Identifier model) {
        var s = w.player.getMainHandItem(); var before = s.copy(); var packets = w.incremental();
        carrier(h, w, s, selectedSlot(h, w, packets), model);
        unchanged(h, w, s, before);
        full(h, w, model);
        check(h, w.incremental().stream().noneMatch(ClientboundContainerSetSlotPacket.class::isInstance),
                "Unchanged native RemoteSlot emits no duplicate slot frame after full sync");
    }
    private static void changed(GameTestHelper h, InventoryWireW92 w, Identifier model,
                                Map<InventoryWireW92, ItemStack> lastSent) {
        var s = w.player.getMainHandItem();
        if (ItemStack.matches(lastSent.get(w), s)) full(h, w, model);
        else both(h, w, model);
        lastSent.put(w, s.copy());
    }
    private static void bypass(GameTestHelper h, InventoryWireW92 w) {
        var s = w.player.getMainHandItem(); var before = s.copy();
        w.discard();
        // Deliberately omit the trusted native synchronizer. The packet constructor copies s.
        w.connection.send(new ClientboundContainerSetSlotPacket(w.player.inventoryMenu.containerId,
                w.player.inventoryMenu.getStateId(), menuSlot(w.player), s));
        carrier(h, w, s, selectedSlot(h, w, w.capture()), canonical(s));
        unchanged(h, w, s, before);
    }

    private record MagazineCase(InventoryWireW92 wire, ItemStack stack, int duration, int credit) {}
    @GameTest(structure = FLOOR, maxTicks = 140, environment = ISOLATED)
    public void productionMagazineReloadsReachBothCarriersAndRetireAtTheirRealDeadlines(GameTestHelper h) {
        var f = new Fixture(h); var cases = new ArrayList<MagazineCase>();
        for (String id : List.of("beloved", "duke_mk_44", "ammit_ar2")) for (var grip : WeaponModels.Grip.values()) {
            var w = f.player(); var s = f.equip(w, id, 1, 5, grip);
            // Persisted zero supplies no authority. Production acquisition must now
            // distinguish it with a stable .001 offset and send the real frame0 delta.
            var floats = new ArrayList<>(data(s).floats()); floats.set(1, 0f);
            s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(floats,
                    data(s).flags(), data(s).strings(), data(s).colors()));
            full(h, w, canonical(s)); reload(h, w);
            var state = WeaponRuntime.ammunition(w.player).orElseThrow(); var p = profile(s);
            int credit = ReloadCreditProfile.ammoTicks(entry(s),
                    new WeaponReloadPolicy.Plan(p.firstReloadTicks(), p.reloadTicks(), p.roundsPerInsert()));
            check(h, state.reloadDuration() == p.firstReloadTicks() && state.reloadRemaining() == p.firstReloadTicks()
                            && WeaponReloadPresentation.ownedBy(w.player, s), "Real base phase owns legacy reload admission");
            cases.add(new MagazineCase(w, s, state.reloadDuration(), credit));
            bypass(h, w);
            near(h, data(s).getFloat(1), .001f, "Saved zero activation has a distinct frame0 sample");
            both(h, w, reloadModel(s));
        }
        int end = cases.stream().mapToInt(MagazineCase::duration).max().orElseThrow() + 1;
        check(h, end < 140, "Every actual reload deadline fits this test");
        for (int t = 1; t <= end; t++) {
            int elapsed = t;
            f.at(t, () -> {
                for (var c : cases) {
                    var s = c.stack; var p = profile(s); boolean credited = elapsed >= c.credit;
                    int moved = p.infiniteReserve() ? p.magazine() - 1 : Math.min(p.magazine() - 1, 5);
                    amounts(h, s, credited ? 1 + moved : 1, p.infiniteReserve() ? 0 : 5 - (credited ? moved : 0));
                    if (elapsed < c.duration) {
                        check(h, WeaponReloadPresentation.ownedBy(c.wire.player, s), "Recovery retains exact real reload authority");
                        near(h, data(s).getFloat(1), denseSample(1 - (c.duration - elapsed) / (float)c.duration) + .001f,
                                "Actual sampled reload progress keeps its acquisition offset");
                    } else check(h, !WeaponRuntime.reloading(c.wire.player) && !WeaponReloadPresentation.active(s)
                                    && !WeaponRuntime.reloadOwnedBy(c.wire.player, s), "Actual full deadline retires cycle and transport authority");
                    int firstPositive = (c.duration + 59) / 60;
                    if (elapsed == firstPositive - 1)
                        check(h, c.wire.incremental().stream().noneMatch(ClientboundContainerSetSlotPacket.class::isInstance),
                                "Below the first positive sample, equal components still suppress incremental delivery");
                    if (elapsed == firstPositive || elapsed == Math.max(1, c.duration / 2) || elapsed == c.credit - 1 || elapsed == c.credit
                            || elapsed == c.duration - 1 || elapsed == c.duration) {
                        // Adjacent samples can quantize equally. Full at credit-1 primes the
                        // actual paid ammo delta; mid/late/retirement samples still require incremental.
                        if (elapsed == c.credit - 1 && elapsed != c.duration / 2 && elapsed != c.duration - 1)
                            full(h, c.wire, reloadModel(s));
                        else both(h, c.wire, elapsed < c.duration ? reloadModel(s) : canonical(s));
                    }
                }
                if (elapsed == end) { for (var c : cases) full(h, c.wire, canonical(c.stack)); h.succeed(); }
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 50, environment = ISOLATED)
    public void realLongArmPairsEncodeInitialLoopAndSixTickReturnBeforeExactRestoration(GameTestHelper h) {
        var f = new Fixture(h); var actors = new ArrayList<InventoryWireW92>();
        for (var grip : WeaponModels.Grip.values()) {
            var w = f.player(); var s = f.equip(w, "long_arm", 11, 0, grip); actors.add(w);
            check(h, profile(s).firstReloadTicks() == 20 && profile(s).reloadTicks() == 13
                            && profile(s).roundsPerInsert() == 2 && WeaponInsertPresentation.RETURN_TICKS == 6,
                    "Unchanged Long Arm pair and return deadlines");
            reload(h, w); check(h, WeaponInsertPresentation.ownedBy(w.player, s), "Real reload acquired initial insert binding");
            bypass(h, w); both(h, w, route("weapon_insert_w222_long_arm/long_arm"));
        }
        for (int t = 1; t <= 40; t++) {
            int elapsed = t;
            f.at(t, () -> {
                for (var w : actors) {
                    var s = w.player.getMainHandItem(); amounts(h, s, elapsed < 20 ? 11 : elapsed < 33 ? 13 : 14, 0);
                    check(h, WeaponRuntime.reloading(w.player) == (elapsed < 33), "Only real pair transfer ends gameplay reload at tick33");
                    if (elapsed < 39) {
                        check(h, WeaponInsertPresentation.ownedBy(w.player, s), "Cosmetic return retains its own original owner");
                        float expected = elapsed < 20 ? denseSample(1 - (20 - elapsed) / 20f) : elapsed < 33
                                ? 2 + denseSample(1 - (33 - elapsed) / 13f) : 4 + denseSample((elapsed - 33) / 6f);
                        near(h, data(s).getFloat(4), expected, "Initial/loop/return float4 at the actual tick");
                    } else check(h, !WeaponInsertPresentation.active(s) && data(s).equals(SENTINEL),
                            "Tick39 restores exact original CMD, including unrelated padding and selectors");
                    if (List.of(10, 19, 20, 26, 32, 33, 36, 38, 39).contains(elapsed))
                        both(h, w, elapsed < 39 ? route("weapon_insert_w222_long_arm/long_arm") : canonical(s));
                    if (elapsed == 40) full(h, w, canonical(s));
                }
                if (elapsed == 40) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = ISOLATED)
    public void movingAdsAndSniperHalfScopeExceptionSurviveBothNativeCarrierPackets(GameTestHelper h) {
        var f = new Fixture(h); var actors = new ArrayList<InventoryWireW92>();
        var lastSent = new IdentityHashMap<InventoryWireW92, ItemStack>();
        for (String id : List.of("ammit_ar2", "beloved", "line_in_the_sand")) for (var grip : WeaponModels.Grip.values()) {
            var w = f.player(); var s = f.equip(w, id, 1, 2, grip); actors.add(w);
            lastSent.put(w, s.copy()); ads(w.player, true);
        }
        int duration = actors.stream().mapToInt(w -> WeaponAimProfile.of(entry(w.player.getMainHandItem())).transitionTicks()).max().orElseThrow();
        for (int t = 1; t <= 2 * duration + 2; t++) {
            int elapsed = t;
            f.at(t, () -> {
                for (var w : actors) {
                    var s = w.player.getMainHandItem(); var e = entry(s); int n = WeaponAimProfile.of(e).transitionTicks();
                    float expected = elapsed <= duration ? Math.min(1, elapsed / (float)n)
                            : Math.max(0, 1 - (elapsed - duration) / (float)n);
                    float raw = WeaponAiming.progress(w.player);
                    near(h, raw, expected, "Actual ADS enter/exit clock");
                    amounts(h, s, 1, profile(s).infiniteReserve() ? 0 : 2);
                    // Keep the existing float clock: the last mathematical exit step can
                    // leave a positive rounding residue until the next real tick.
                    boolean active = raw > 0, scoped = raw >= .5f && WeaponScopes.supports(e);
                    check(h, WeaponAimPresentation.ownedBy(w.player, s) == active && WeaponAiming.scoped(w.player) == scoped,
                            "Original selected ADS owner and half-progress scope gate");
                    Identifier model = active ? scoped && e.family().equals("sniper_rifle")
                            ? route("weapon_scope_w45/" + e.id()) : aimModel(s, false) : canonical(s);
                    if (active) near(h, data(s).getFloat(3), sample(raw), "Float3 follows live ADS rather than scope route");
                    changed(h, w, model, lastSent);
                    if (elapsed == 1 && e.id().equals("ammit_ar2")) bypass(h, w);
                    if (!active) check(h, data(s).equals(SENTINEL), "Zero ADS restores original selector, pose and unrelated data");
                    if (elapsed == duration) ads(w.player, false);
                }
                if (elapsed == 2 * duration + 2) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 120, environment = ISOLATED)
    public void bothBowsEncodeLoadedDrawAimBowAndPaidNockWithoutLatentDraw(GameTestHelper h) {
        var f = new Fixture(h); var actors = new ArrayList<InventoryWireW92>();
        for (String id : List.of("biting_winds", "whispering_slab")) {
            var w = f.player(); var s = f.equip(w, id, 1, 0, WeaponModels.Grip.NATIVE); actors.add(w);
            WeaponCombatItem.INSTANCE.use(h.getLevel(), w.player, InteractionHand.MAIN_HAND);
            check(h, w.player.isUsingItem() && w.player.getUseItem() == s, "Production native bow use owns real hold");
            w.player.stopUsingItem(); WeaponRuntime.tickPlayer(w.player);
            near(h, (float)Math.floor(data(s).getFloat(2)), 1, "Real released-without-shot hold becomes loaded idle");
            both(h, w, bowModel(s)); bypass(h, w);
            WeaponCombatItem.INSTANCE.use(h.getLevel(), w.player, InteractionHand.MAIN_HAND);
            near(h, (float)Math.floor(data(s).getFloat(2)), 2, "New real hold begins draw at zero elapsed time");
            both(h, w, bowModel(s)); ads(w.player, true);
        }
        int shot = actors.stream().mapToInt(w -> profile(w.player.getMainHandItem()).chargeTicks()).max().orElseThrow() + 2;
        int end = shot + actors.stream().mapToInt(w -> profile(w.player.getMainHandItem()).firstReloadTicks()).max().orElseThrow() + 1;
        check(h, end < 120, "Actual full draw and nock fit the test");
        for (int t = 1; t <= end; t++) {
            int elapsed = t;
            f.at(t, () -> {
                for (var w : actors) {
                    var s = w.player.getMainHandItem(); var p = profile(s);
                    if (elapsed <= shot) {
                        int frame = 2 + (int)Math.floor(Math.min(1, elapsed / (float)p.chargeTicks()) * 20 + 1e-6f);
                        near(h, (float)Math.floor(data(s).getFloat(2)), frame, "Actual draw clock clamps only at its own full deadline");
                        check(h, WeaponBowPresentation.ownedBy(w.player, s) && WeaponAimPresentation.ownedBy(w.player, s),
                                "Actual bow and ADS ownership together select the composite _bow route");
                        amounts(h, s, 1, 0);
                        if (List.of(1, 5, 9, p.chargeTicks() / 2, p.chargeTicks() - 1, p.chargeTicks()).contains(elapsed))
                            both(h, w, aimModel(s, true));
                    }
                    if (elapsed == shot) {
                        w.player.releaseUsingItem(); amounts(h, s, 0, 0);
                        check(h, !w.player.isUsingItem(), "Actual release spends exactly one arrow and releases native hold");
                        near(h, (float)Math.floor(data(s).getFloat(2)), 0, "Paid release first exposes empty bow");
                        both(h, w, aimModel(s, true));
                        WeaponRuntime.tickPlayer(w.player);
                        check(h, WeaponRuntime.reloading(w.player) && !WeaponAimPresentation.active(s),
                                "Real automatic nock suspends ADS immediately");
                        near(h, (float)Math.floor(data(s).getFloat(2)), 32, "Nock begins at its real transfer deadline origin");
                        near(h, data(s).getFloat(1), 0, "W222 nock acquires independent reload float1");
                        check(h, WeaponReloadPresentation.ownedBy(w.player, s), "Actual nock owns the higher-priority reload route");
                        both(h, w, reloadModel(s));
                    }
                    if (elapsed > shot) {
                        int n = elapsed - shot; boolean nocking = n < p.firstReloadTicks();
                        amounts(h, s, nocking ? 0 : 1, 0);
                        check(h, WeaponRuntime.reloading(w.player) == nocking && !WeaponAimPresentation.active(s)
                                        && !w.player.isUsingItem(), "Nock cannot age a buffered draw or re-enter suspended ADS");
                        int frame = nocking ? 32 + (int)Math.floor(n / (float)p.firstReloadTicks() * 20 + 1e-6f) : 1;
                        near(h, (float)Math.floor(data(s).getFloat(2)), frame, "Real nock samples then loaded idle");
                        near(h, data(s).getFloat(1), nocking ? denseSample(1 - (p.firstReloadTicks() - n) / (float)p.firstReloadTicks()) : -1,
                                "Dense reload selector retires independently of the W50 nock selector");
                        check(h, WeaponReloadPresentation.ownedBy(w.player, s) == nocking, "Reload authority ends at the nock deadline");
                        if (n == p.firstReloadTicks() / 2 || n == p.firstReloadTicks() - 1 || n == p.firstReloadTicks())
                            both(h, w, nocking ? reloadModel(s) : bowModel(s));
                        if (elapsed == end) full(h, w, bowModel(s));
                    }
                }
                if (elapsed == end) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 140, environment = ISOLATED)
    public void savedLegacySnapshotsAndDeadlineCleanupRemainCanonicalOnActualWire(GameTestHelper h) {
        var f = new Fixture(h); var owners = new ArrayList<InventoryWireW92>(); var loaded = new ArrayList<InventoryWireW92>();
        for (String id : List.of("ammit_ar2", "long_arm", "austringer", "biting_winds")) {
            var w = f.player(); f.equip(w, id, 1, 0, WeaponModels.Grip.NATIVE); owners.add(w);
            switch (id) {
                case "ammit_ar2", "long_arm" -> reload(h, w);
                case "austringer" -> ads(w.player, true);
                case "biting_winds" -> WeaponCombatItem.INSTANCE.use(h.getLevel(), w.player, InteractionHand.MAIN_HAND);
            }
        }
        for (int t = 1; t <= 105; t++) {
            int elapsed = t;
            f.at(t, () -> {
                if (elapsed == 1) for (var w : owners) {
                    var s = w.player.getMainHandItem(); check(h, !inactive(s), "Production legacy route is live before persistence control");
                    var activeModel = switch (entry(s).id()) {
                        case "ammit_ar2" -> reloadModel(s);
                        case "long_arm" -> route("weapon_insert_w222_long_arm/long_arm");
                        case "austringer" -> aimModel(s, false);
                        case "biting_winds" -> bowModel(s);
                        default -> throw new IllegalStateException("Unexpected legacy fixture");
                    };
                    both(h, w, activeModel); // Prime a real live baseline before the cleanup delta.
                    bypass(h, w);
                    var ops = w.player.registryAccess().createSerializationContext(NbtOps.INSTANCE);
                    var saved = ItemStack.CODEC.parse(ops, ItemStack.CODEC.encodeStart(ops, s).getOrThrow()).getOrThrow();
                    check(h, ItemStack.matches(saved, s) && inactive(saved), "Actual NBT roundtrip keeps selectors/ammo but no authority");
                    var copy = f.player(); loaded.add(copy);
                    copy.player.getInventory().setItem(0, saved); copy.player.getInventory().setSelectedSlot(0);
                    both(h, copy, canonical(saved));
                    ads(w.player, false); w.player.stopUsingItem();
                    WeaponRuntime.cleanup(w.player); WeaponRuntime.cleanup(w.player);
                    check(h, inactive(s), "Repeated production cleanup immediately retires every legacy binding");
                    both(h, w, canonical(s));
                }
                if (elapsed == 105) {
                    for (var w : owners) {
                        var s = w.player.getMainHandItem(); amounts(h, s, 1, 0);
                        check(h, inactive(s) && !WeaponRuntime.reloading(w.player), "Old deadlines cannot restore cleaned animation or ammunition");
                        full(h, w, canonical(s));
                    }
                    for (var w : loaded) {
                        var s = w.player.getMainHandItem(); amounts(h, s, 1, 0);
                        check(h, inactive(s) && !WeaponRuntime.reloading(w.player), "Persisted selectors schedule no ghost cycle after old deadlines");
                        full(h, w, canonical(s));
                    }
                    h.succeed();
                }
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = ISOLATED)
    public void recipientAimCannotAdmitDonorHigherRouteOrCompositeBowOnTheSameOriginal(GameTestHelper h) {
        var f = new Fixture(h); var donors = new ArrayList<InventoryWireW92>(); var recipients = new ArrayList<InventoryWireW92>();
        for (String id : List.of("long_arm", "ammit_ar2")) for (var grip : WeaponModels.Grip.values()) {
            var donor = f.player(); var s = f.equip(donor, id, 11, 0, grip); donors.add(donor); reload(h, donor);
            var recipient = f.player(); recipients.add(recipient);
            recipient.player.getInventory().setItem(0, s); recipient.player.getInventory().setSelectedSlot(0);
            full(h, recipient, canonical(s)); ads(recipient.player, true);
        }
        var bowDonors = new ArrayList<InventoryWireW92>(); var bowRecipients = new ArrayList<InventoryWireW92>();
        for (String id : List.of("biting_winds", "whispering_slab")) {
            var bowDonor = f.player(); var bow = f.equip(bowDonor, id, 1, 0, WeaponModels.Grip.NATIVE);
            bowDonors.add(bowDonor);
            WeaponCombatItem.INSTANCE.use(h.getLevel(), bowDonor.player, InteractionHand.MAIN_HAND);
            bowDonor.player.stopUsingItem(); WeaponRuntime.tickPlayer(bowDonor.player);
            full(h, bowDonor, bowModel(bow));
            var bowRecipient = f.player(); bowRecipients.add(bowRecipient);
            bowRecipient.player.getInventory().setItem(0, bow);
            bowRecipient.player.getInventory().setSelectedSlot(0); full(h, bowRecipient, canonical(bow));
            ads(bowRecipient.player, true);
        }
        f.at(1, () -> {
            for (int i = 0; i < donors.size(); i++) {
                var donor = donors.get(i); var recipient = recipients.get(i); var s = donor.player.getMainHandItem();
                boolean insert = entry(s).id().equals("long_arm");
                check(h, recipient.player.getMainHandItem() == s
                                && (insert ? WeaponInsertPresentation.active(s)
                                    && WeaponInsertPresentation.ownedBy(donor.player, s)
                                    && !WeaponInsertPresentation.ownedBy(recipient.player, s)
                                    : WeaponReloadPresentation.active(s)
                                    && WeaponReloadPresentation.ownedBy(donor.player, s)
                                    && !WeaponReloadPresentation.ownedBy(recipient.player, s))
                                && WeaponAimPresentation.ownedBy(recipient.player, s),
                        "Donor INITIAL insert/reload stays active while exact-object recipient owns lower-priority real ADS");
                amounts(h, s, 11, 0);
                var model = insert ? route("weapon_insert_w222_long_arm/long_arm") : reloadModel(s);
                both(h, donor, model);
                both(h, recipient, canonical(s));
                full(h, donor, model);
            }
            for (int i = 0; i < bowDonors.size(); i++) {
                var bowDonor = bowDonors.get(i); var bowRecipient = bowRecipients.get(i);
                var bow = bowDonor.player.getMainHandItem();
                check(h, bow == bowRecipient.player.getMainHandItem()
                                && WeaponAimPresentation.ownedBy(bowRecipient.player, bow)
                                && WeaponBowPresentation.ownedBy(bowDonor.player, bow)
                                && !WeaponBowPresentation.ownedBy(bowRecipient.player, bow),
                        "Recipient owns ADS while the composite model's active bow dependency belongs to donor");
                amounts(h, bow, 1, 0);
                both(h, bowRecipient, canonical(bow));
                // Donor cannot use its lower bow binding to admit the recipient's higher ADS route either.
                both(h, bowDonor, canonical(bow));
            }
            h.succeed();
        });
    }
}
