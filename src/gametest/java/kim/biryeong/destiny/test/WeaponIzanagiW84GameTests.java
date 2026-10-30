package kim.biryeong.destiny.test;

import com.mojang.serialization.JsonOps;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.SuperSession;
import net.minecraft.nbt.LongTag;
import net.minecraft.world.item.component.CustomData;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponPerkHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.HashedStack;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundContainerClickPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/** Real paid W84 transactions on the raised W78 deck. All callbacks install at initialization.
 * No direct started/finishReload/shot calls, forged charge grants, clock reflection or fake damage.
 * Sixty-one-tick replacement deadlines and loaded-first funding are explicit local policies,
 * not claimed exact Destiny animation/refund observations. Real PvP targeting is excluded by Combat.
 */
public final class WeaponIzanagiW84GameTests {
    private static final String FLOOR = "destiny-test:w78_floor", IZA = "izanagis_burden";
    private static final float HP = 1000, EPS = .004f;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static void hp(GameTestHelper h, LivingEntity target, float expected, String message) {
        check(h, Math.abs(target.getHealth() - expected) < EPS,
                message + "; expected=" + expected + ", actual=" + target.getHealth());
    }
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static WeaponCatalog.Entry izanagi() { return WeaponCatalog.find(IZA).orElseThrow(); }
    private static WeaponProfile profile(ItemStack gun) {
        return WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());
    }
    private static WeaponMagazine ammo(ItemStack gun) { return WeaponItems.magazine(gun, profile(gun)); }
    private static void bounded(GameTestHelper h, Entity entity) {
        var o = h.absoluteVec(Vec3.ZERO); var b = entity.getBoundingBox();
        check(h, b.minX > o.x && b.maxX < o.x + 48 && b.minY > o.y && b.maxY < o.y + 12
                        && b.minZ > o.z && b.maxZ < o.z + 32,
                "Whole W84 entity AABB remains inside its own 48x12x32 fixture: " + entity.getUUID());
    }

    private static final class Fixture {
        final GameTestHelper h;
        final long createdAt;
        final List<ServerPlayer> players = new ArrayList<>();
        final List<Husk> targets = new ArrayList<>();
        Fixture(GameTestHelper h) {
            this.h = h; createdAt = h.getLevel().getServer().getTickCount();
            for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
            TestCleanup.register(h, () -> {
                targets.forEach(Entity::discard);
                for (var p : players) {
                    p.setServerLevel(h.getLevel()); p.stopUsingItem();
                    if (AbilityService.inSuper(p)) AbilityService.endSuper(p);
                    WeaponRuntime.cleanup(p); WeaponPerkHud.remove(p); CombatHud.remove(p);
                    if (p.level().players().contains(p)) p.level().removePlayerImmediately(p, Entity.RemovalReason.DISCARDED);
                    TestPlayers.remove(p);
                }
            });
            h.onEachTick(() -> {
                for (var p : players) bounded(h, p);
                for (var t : targets) if (!t.isRemoved()) bounded(h, t);
            });
        }
        ServerPlayer player(double z) {
            // Standalone non-Guardian input also permits the genuine vanilla offhand packet path.
            var p = TestPlayers.create(h, new Vec3(3, 4, z), -90, 0,
                    "W84_" + UUID.randomUUID().toString().substring(0, 8));
            players.add(p); p.setNoGravity(true); p.setOnGround(true);
            p.setAttached(WeaponLoadout.ENABLED, false); bounded(h, p);
            return p;
        }
        ItemStack equip(ServerPlayer p, int loaded, int reserve, long overflow) {
            var gun = WeaponItems.create(izanagi());
            gun.set(DataComponents.CUSTOM_NAME, Component.literal("W84_" + UUID.randomUUID()));
            WeaponItems.save(gun, new WeaponMagazine(profile(gun), loaded, reserve, overflow));
            p.getInventory().setItem(0, gun); p.getInventory().setSelectedSlot(0);
            WeaponRuntime.tickPlayer(p); TestPlayers.drain(p);
            check(h, p.getMainHandItem() == gun && WeaponExotics.izanagi(WeaponItems.entry(gun).orElseThrow())
                            && WeaponModels.twoHanded(gun) && !profile(gun).infiniteReserve()
                            && profile(gun).mode() == WeaponProfile.Mode.HITSCAN
                            && profile(gun).burst() == 1 && profile(gun).pellets() == 1,
                    "Canonical two-hand finite special Izanagi emits one funded hitscan per trigger");
            state(h, gun, loaded, reserve, overflow, 0); return gun;
        }
        Husk target(double x, double y, double z, float health) {
            var t = h.spawn(EntityTypes.HUSK, new Vec3(x, y, z)); targets.add(t);
            t.setNoAi(true); t.setNoGravity(true); t.setPersistenceRequired();
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
            t.setHealth(health); bounded(h, t); return t;
        }
        Husk primary(ServerPlayer p, double x, boolean precision, float health) {
            var t = target(x, precision ? 4 : 4.8, h.relativeVec(p.position()).z, health);
            var from = p.getEyePosition(); var box = t.getBoundingBox();
            var hit = box.clip(from, from.add(40, 0, 0)).orElseThrow();
            check(h, precision ? from.y >= box.maxY - box.getYsize() * .25 && from.y < box.maxY
                            : from.y > box.minY && from.y < box.maxY - box.getYsize() * .25,
                    "Positive horizontal ray preflight intersects the requested head/body region");
            check(h, WeaponPrecision.critical(t, from, hit, WeaponBallistics.of(izanagi()).precision()) == precision
                            && Combat.isEnemy(p, t) && !p.isAlliedTo(t),
                    "Production precision classifier and hostile admission match the intended victim");
            var wall = p.level().clip(new ClipContext(from, hit, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
            check(h, wall.getType() == HitResult.Type.MISS, "Direct paid shot has clear positive fixture LOS");
            return t;
        }
        void at(int delay, Runnable action) {
            check(h, h.getLevel().getServer().getTickCount() == createdAt,
                    "All timed callbacks must be registered at fixture initialization");
            h.runAfterDelay(delay, () -> {
                check(h, h.getLevel().getServer().getTickCount() - createdAt == delay,
                        "Assertion observes the exact actual server-tick deadline " + delay);
                for (var p : players) { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); }
                action.run();
            });
        }
    }

    private static void shot(GameTestHelper h, ServerPlayer p, Husk expected) {
        boolean miss = expected == null;
        WeaponAiming.cleanup(p); p.setShiftKeyDown(false);
        p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(miss ? 90 : 0); WeaponAiming.tick(p);
        // Preflight and paid emission must use the same deterministic dispersion sample.
        p.getRandom().setSeed(0x5DEECE66DL);
        var firingDirection = WeaponAiming.direction(p);
        var gun = p.getMainHandItem(); var before = ammo(gun);
        int loaded = before.rounds(), reserve = before.reserve(); long overflow = before.overflow();
        check(h, loaded > 0 && !WeaponHandling.blocked(p), "Paid trigger has ammunition and completed handling");
        var from = p.getEyePosition(); var to = from.add(firingDirection.scale(30));
        if (miss) {
            var floor = p.level().clip(new ClipContext(from, from.add(0, -4, 0),
                    ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
            check(h, floor.getType() == HitResult.Type.BLOCK, "Miss points into raised stone deck");
        } else {
            var first = net.minecraft.world.entity.projectile.ProjectileUtil.getEntityHitResult(p.level(), p, from, to,
                    new net.minecraft.world.phys.AABB(from, to).inflate(.23),
                    e -> Combat.isEnemy(p, e) && !p.isAlliedTo(e), .03f);
            check(h, first != null && first.getEntity() == expected,
                    "Positive native entity query selects the exact intended hostile victim");
        }
        p.getRandom().setSeed(0x5DEECE66DL); // Replay the inspected ray for the actual paid shot.
        check(h, WeaponRuntime.beginUse(p), "Actual beginUse accepts a paid emission");
        WeaponRuntime.releaseUse(p, gun); p.stopUsingItem();
        state(h, gun, loaded - 1, reserve, overflow, 0);
        check(h, WeaponRuntime.activeProjectiles(p) == 0, "One hitscan, never a second/free projectile");
        var tag = gun.get(DataComponents.CUSTOM_DATA).copyTag();
        check(h, !tag.contains(WeaponIzanagi.CHARGE), "Actual paid emission removes saved Honed charge, including misses");
    }
    private static void request(ServerPlayer p, boolean honed) {
        boolean wasShift = p.isShiftKeyDown();
        p.setShiftKeyDown(honed);
        try {
            p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                    ServerboundPlayerActionPacket.Action.DROP_ITEM, BlockPos.ZERO, Direction.UP));
        } finally {
            p.setShiftKeyDown(wasShift);
        }
    }
    private static void reload(GameTestHelper h, ServerPlayer p, boolean honed) {
        var gun = p.getMainHandItem(); var before = ammo(gun);
        int loaded = before.rounds(), reserve = before.reserve(); long overflow = before.overflow();
        request(p, honed);
        check(h, WeaponRuntime.reloading(p) && p.getMainHandItem() == gun,
                "Actual Q/ShiftQ packet starts reload without dropping or replacing the exact stack");
        state(h, gun, loaded, reserve, overflow, 0);
        if (honed) check(h, !WeaponIzanagi.canStart(p), "Accepted pending Honed transaction rejects duplicate starts");
    }
    private static void state(GameTestHelper h, ItemStack gun, int loaded, int reserve, long overflow, int charge) {
        var a = ammo(gun);
        check(h, a.rounds() == loaded && a.reserve() == reserve && a.overflow() == overflow
                        && WeaponIzanagi.charge(gun) == charge,
                "Exact funded state expected " + loaded + "/" + reserve + "/" + overflow + " x" + charge
                        + ", got " + a.rounds() + "/" + a.reserve() + "/" + a.overflow() + " x" + WeaponIzanagi.charge(gun));
    }
    private static void hud(GameTestHelper h, ServerPlayer p, int count) {
        var gun = p.getMainHandItem(); var saved = gun.copy(); int before = WeaponIzanagi.charge(p);
        WeaponPerkHud.update(p); WeaponPerkHud.update(p);
        String key = WeaponPerkHud.PREFIX + "honed_edge_";
        var keys = DisplayHud.getHuds(p).keySet().stream().filter(k -> k.startsWith(key)).collect(Collectors.toSet());
        var expected = count == 0 ? Set.<String>of() : Set.of(key + "marker", key + "label", key + "x", key + "count");
        check(h, keys.equals(expected), "Honed HUD is exactly four count nodes, never a countdown or stale row");
        if (count > 0) {
            var digit = (ItemDisplayHud) DisplayHud.getHud(p, key + "count");
            check(h, Identifier.fromNamespaceAndPath("destiny", "gui/hud/ammo_digit_" + count)
                            .equals(digit.getItem().get(DataComponents.ITEM_MODEL)), "HUD shows actual funded Honed count " + count);
        }
        check(h, before == count && WeaponIzanagi.charge(p) == before && ItemStack.matches(saved, gun),
                "Repeated HUD reads neither spend rounds nor mutate the authoritative stack");
    }
    private static void hotbarRoundTrip(GameTestHelper h, ServerPlayer p) {
        var gun = p.getMainHandItem(); int rounds = ammo(gun).rounds(); long tick = now(p);
        p.getInventory().setItem(1, new ItemStack(Items.STONE));
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
        check(h, p.getMainHandItem().is(Items.STONE), "First validated packet genuinely stows Izanagi");
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));
        check(h, now(p) == tick && p.getMainHandItem() == gun && ammo(gun).rounds() == rounds,
                "Same-tick native slot round trip returns the identical paid stack");
        WeaponRuntime.tickPlayer(p);
    }
    private static void offhandRoundTrip(GameTestHelper h, ServerPlayer p) {
        var gun = p.getMainHandItem(); int rounds = ammo(gun).rounds(); long tick = now(p);
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.STONE));
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND, BlockPos.ZERO, Direction.UP));
        check(h, p.getOffhandItem() == gun && p.getMainHandItem().is(Items.STONE), "Actual non-Guardian packet stows exact Izanagi in offhand");
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND, BlockPos.ZERO, Direction.UP));
        check(h, now(p) == tick && p.getMainHandItem() == gun && p.getOffhandItem().is(Items.STONE)
                        && ammo(gun).rounds() == rounds, "Actual same-tick offhand return preserves exact identity and paid ammo");
        WeaponRuntime.tickPlayer(p);
    }

    private static void containerRoundTrip(GameTestHelper h, ServerPlayer p) {
        var gun = p.getMainHandItem(); var menu = p.containerMenu;
        int backpack = menu.findSlot(p.getInventory(), 9).orElseThrow();
        int rounds = ammo(gun).rounds(); long tick = now(p);
        check(h, menu == p.inventoryMenu && menu.stillValid(p) && p.getInventory().getSelectedSlot() == 0
                        && menu.getCarried().isEmpty() && menu.getSlot(backpack).getItem().isEmpty()
                        && menu.getSlot(backpack).mayPickup(p) && menu.getSlot(backpack).mayPlace(gun),
                "Positive native player-inventory preflight: selected hotbar0 and an empty ordinary backpack slot");
        // Empty sparse client predictions request no speculative remote-slot updates. Vanilla still
        // executes both validated SWAPs and broadcasts authoritative contents; carried EMPTY is exact.
        // Crucially, no selected-slot/action packet, weapon update or tick occurs between the clicks.
        p.connection.handleContainerClick(new ServerboundContainerClickPacket(menu.containerId, menu.getStateId(),
                (short) backpack, (byte) 0, ContainerInput.SWAP, new Int2ObjectOpenHashMap<>(), HashedStack.EMPTY));
        check(h, p.getMainHandItem().isEmpty() && menu.getSlot(backpack).getItem() == gun
                        && p.getInventory().getSelectedSlot() == 0,
                "Actual accepted container number-key packet moves the original stack out of the selected slot");
        p.connection.handleContainerClick(new ServerboundContainerClickPacket(menu.containerId, menu.getStateId(),
                (short) backpack, (byte) 0, ContainerInput.SWAP, new Int2ObjectOpenHashMap<>(), HashedStack.EMPTY));
        check(h, now(p) == tick && p.containerMenu == menu && p.getMainHandItem() == gun
                        && menu.getSlot(backpack).getItem().isEmpty() && menu.getCarried().isEmpty()
                        && p.getInventory().getSelectedSlot() == 0 && ammo(gun).rounds() == rounds,
                "Second accepted container SWAP returns the exact original object in the same tick without minting ammunition");
    }


    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void exactSecondExoticKeepsOriginalSixtyThreeAceGripAndRegistryWireIdentity(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(16); var gun = f.equip(p, 4, 20, 0);
        WeaponModelGameTests.assertCatalogExpansion(h);
        check(h, WeaponCatalog.all().size() == 65 && WeaponModelGameTests.originalW30Entries().size() == 63,
                "65 current identities retain all exact original 63 plus Ace and Izanagi");
        for (var e : WeaponCatalog.all()) {
            check(h, WeaponExotics.izanagi(e) == e.equals(izanagi()), "All other 64 identities are Honed-ineligible: " + e.id());
            var stack = WeaponItems.create(e);
            check(h, WeaponIzanagi.charge(stack) == 0, "No newly created catalog item arrives charged");
        }
        var c = WeaponCharacteristics.of(izanagi()); var a = WeaponAimProfile.of(izanagi());
        check(h, c.bungieHash() == 3211806999L && c.exotic() && c.slot() == WeaponSlot.KINETIC
                        && c.ammo() == WeaponAmmoType.SPECIAL && izanagi().family().equals("sniper_rifle")
                        && izanagi().frame().equals("exotic") && profile(gun).magazine() == 4 && profile(gun).reserve() == 20
                        && profile(gun).damage() == 16 && WeaponBallistics.of(izanagi()).precision() == 2.5
                        && a.transitionTicks() == 9 && a.zoom() == 4.5f && profile(gun).reloadTicks() == 61
                        && WeaponHandlingProfile.of(izanagi()).readyTicks() == 8
                        && WeaponHandlingProfile.of(izanagi()).stowTicks() == 7 && WeaponScopes.supports(izanagi()),
                "Exact kinetic special profile, sourced fixed-plug stats and W162 scope routing");
        check(h, c.stats().get("1240592695") == 58 && c.stats().get("155624089") == 56
                        && c.stats().get("943549884") == 47 && WeaponPerks.rolls().stream().noneMatch(r -> r.id().equals(IZA)),
                "58/56/47 effective stats do not silently grant legendary sockets or catalyst");
        var ops = h.getLevel().registryAccess().createSerializationContext(JsonOps.INSTANCE);
        var context = ((PacketContextProvider) (Object) p.connection).getPacketContext();
        for (var grip : WeaponModels.Grip.values()) for (var pose : WeaponModels.Pose.values()) {
            var live = WeaponModels.withGrip(gun, grip).orElseThrow(); WeaponModels.setPose(live, pose);
            var decoded = ItemStack.CODEC.parse(ops, ItemStack.CODEC.encodeStart(ops, live).getOrThrow()).getOrThrow();
            check(h, WeaponItems.entry(decoded).orElseThrow().equals(izanagi()), "All native poses/grips preserve exact exotic identity");
            state(h, decoded, 4, 20, 0, 0);
            var wire = PolymerItemUtils.getPolymerItemStack(decoded, context, h.getLevel().registryAccess());
            boolean two = grip == WeaponModels.Grip.TWO_HAND;
            check(h, wire.is(two ? Items.CROSSBOW : Items.STICK) && CrossbowItem.isCharged(wire) == two
                            && ItemStack.matches(decoded, PolymerItemUtils.getRealItemStack(wire, context, h.getLevel().registryAccess())),
                    "Actual Polymer carrier round trip retains all authoritative components");
        }
        hud(h, p, 0); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 75, environment = "destiny-test:w90_isolated")
    public void normalQAndAlternateShiftQBothWaitFullSixtyOneWithoutEarlyCreditOrDuplicateRestart(GameTestHelper h) {
        var f = new Fixture(h); var normal = f.player(8); var honed = f.player(24);
        var ordinaryGun = f.equip(normal, 1, 5, 0); var honedGun = f.equip(honed, 1, 5, 0);
        reload(h, normal, false); reload(h, honed, true);
        f.at(30, () -> { request(honed, true); state(h, honedGun, 1, 5, 0, 0); });
        f.at(60, () -> {
            for (var p : List.of(normal, honed)) {
                check(h, WeaponRuntime.reloading(p) && !WeaponRuntime.beginUse(p), "Tick60 cannot fire or receive early insertion");
                state(h, p.getMainHandItem(), 1, 5, 0, 0); hud(h, p, 0);
            }
        });
        f.at(61, () -> {
            check(h, !WeaponRuntime.reloading(normal) && !WeaponRuntime.reloading(honed), "Both actual timers finish exactly at61");
            state(h, ordinaryGun, 4, 2, 0, 0); state(h, honedGun, 1, 2, 0, 4);
            hud(h, normal, 0); hud(h, honed, 4); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 75, environment = "destiny-test:w90_isolated")
    public void fullEmptyPartialOverflowAndInsufficientPoolsKeepExactAtomicFunding(GameTestHelper h) {
        var f = new Fixture(h);
        int[][] initial = {{4,0,0}, {0,4,0}, {1,2,0}, {2,0,0}, {0,20,11}, {4,20,11}};
        int[][] expected = {{1,0,0,4}, {1,0,0,4}, {1,0,0,3}, {1,0,0,2}, {1,20,7,4}, {1,20,11,4}};
        var guns = new ArrayList<ItemStack>();
        for (int i = 0; i < initial.length; i++) {
            var p = f.player(2 + i * 4); var row = initial[i]; guns.add(f.equip(p, row[0], row[1], row[2])); reload(h, p, true);
        }
        for (int n = 0; n < 2; n++) {
            var p = f.player(26 + n * 4); var gun = f.equip(p, n, 0, 0);
            check(h, !WeaponIzanagi.canStart(p), "Less than two finite cartridges cannot fund Honed"); request(p, true);
            check(h, !WeaponRuntime.reloading(p) && p.getMainHandItem() == gun, "Denied ShiftQ cannot drop or start a timer");
            state(h, gun, n, 0, 0, 0);
        }
        f.at(60, () -> {
            for (int i = 0; i < guns.size(); i++) { var row = initial[i]; state(h, guns.get(i), row[0], row[1], row[2], 0); }
        });
        f.at(61, () -> {
            for (int i = 0; i < guns.size(); i++) {
                var row = expected[i]; state(h, guns.get(i), row[0], row[1], row[2], row[3]);
                long before = (long)initial[i][0] + initial[i][1] + initial[i][2];
                check(h, ammo(guns.get(i)).total() == before - row[3] + 1, "Exactly n cartridges become one funded projectile");
                hud(h, f.players.get(i), row[3]);
            }
            for (int i = 6; i < 8; i++) state(h, f.players.get(i).getMainHandItem(), i - 6, 0, 0, 0);
            h.succeed();
        });
    }

    private static void paidMultipliers(GameTestHelper h, boolean precision) {
        var f = new Fixture(h); float[] multipliers = precision ? new float[]{1.79f,2.31f,3.91f} : new float[]{1.12f,1.25f,2.12f};
        var victims = new ArrayList<Husk>();
        for (int i = 0; i < 3; i++) {
            var p = f.player(6 + i * 10); f.equip(p, i + 2, 0, 0);
            victims.add(f.primary(p, 10, precision, HP)); reload(h, p, true);
        }
        f.at(61, () -> { for (int i = 0; i < 3; i++) { state(h, f.players.get(i).getMainHandItem(), 1, 0, 0, i + 2); hud(h, f.players.get(i), i + 2); } });
        f.at(65, () -> {
            for (int i = 0; i < 3; i++) {
                var p = f.players.get(i); shot(h, p, victims.get(i));
                hp(h, victims.get(i), HP - (precision ? 40 : 16) * multipliers[i], "Actual paid x" + (i + 2) + " " + (precision ? "precision" : "body") + " damage");
                hud(h, p, 0);
            }
            h.succeed();
        });
    }
    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void twoThreeAndFourCartridgesPayExactBodyMultipliers(GameTestHelper h) { paidMultipliers(h, false); }
    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void twoThreeAndFourCartridgesPayExactPrecisionMultipliersWithoutCatalyst(GameTestHelper h) { paidMultipliers(h, true); }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void paidMissConsumesOnlyFundedProjectileAndDryRetryCannotRefundOrDamage(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(16); var gun = f.equip(p, 4, 0, 0);
        var victim = f.primary(p, 10, false, HP); reload(h, p, true);
        f.at(61, () -> { state(h, gun, 1, 0, 0, 4); hud(h, p, 4); });
        f.at(65, () -> { shot(h, p, null); hp(h, victim, HP, "Real downward charged miss does not hit witness"); hud(h, p, 0); });
        f.at(85, () -> {
            check(h, !WeaponRuntime.beginUse(p) && !WeaponRuntime.reloading(p), "Dry empty special cannot emit or start unfunded reload");
            state(h, gun, 0, 0, 0, 0); hp(h, victim, HP, "No late damage, reserve minting or missed-shot refund"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void capturedCountDoesNotUpgradeAndChangedLoadedOrLostFundingRejectWithoutPartialDebit(GameTestHelper h) {
        var f = new Fixture(h); var pickup = f.player(6); var changed = f.player(16); var lost = f.player(26);
        var a = f.equip(pickup, 2, 0, 0); var b = f.equip(changed, 2, 2, 0); var c = f.equip(lost, 1, 3, 0);
        for (var p : f.players) reload(h, p, true);
        f.at(30, () -> {
            // This is an incoming-ammo boundary using the production reserve allocator, not a simulated brick collision.
            var incoming = ammo(a); check(h, incoming.addReserve(4) == 4, "Incoming finite reserve admitted without reloading"); WeaponItems.save(a, incoming);
            WeaponItems.save(b, new WeaponMagazine(profile(b), 1, 2));
            WeaponItems.save(c, new WeaponMagazine(profile(c), 1, 1));
        });
        f.at(61, () -> {
            state(h, a, 1, 4, 0, 2); hud(h, pickup, 2);
            state(h, b, 1, 2, 0, 0); state(h, c, 1, 1, 0, 0);
            check(h, !WeaponRuntime.reloading(changed) && !WeaponRuntime.reloading(lost), "Invalid full-ready commits terminate, never retry or partly debit");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 85, environment = "destiny-test:w90_isolated")
    public void realSameTickHotbarOffhandContainerAndLifecycleCancellationCannotCompletePendingReload(GameTestHelper h) {
        var f = new Fixture(h);
        for (int i = 0; i < 7; i++) { var p = f.player(3 + i * 4); f.equip(p, 2, 2, 0); reload(h, p, true); }
        var other = h.getLevel().getServer().getLevel(h.getLevel().dimension().equals(Level.NETHER) ? Level.OVERWORLD : Level.NETHER);
        check(h, other != null && other != h.getLevel(), "Distinct real server level exists for pending authority witness");
        f.at(30, () -> {
            hotbarRoundTrip(h, f.players.get(0)); offhandRoundTrip(h, f.players.get(1)); containerRoundTrip(h, f.players.get(2));
            WeaponRuntime.cancelUseForSkill(f.players.get(3));
            var dying = f.players.get(4); dying.setHealth(0); WeaponRuntime.tickPlayer(dying); dying.setHealth(20); WeaponRuntime.tickPlayer(dying);
            var traveler = f.players.get(5); traveler.setServerLevel(other); WeaponRuntime.tickPlayer(traveler); traveler.setServerLevel(h.getLevel()); WeaponRuntime.tickPlayer(traveler);
            var superPlayer = f.players.get(6);
            AbilityService.startSuper(superPlayer, new SuperSession() {
                public boolean tick() { return true; } public void primary() {} public void end() {} public float remaining() { return 1; }
            });
            check(h, AbilityService.inSuper(superPlayer), "Actual super eligibility boundary admitted");
            WeaponRuntime.tickPlayer(superPlayer); AbilityService.endSuper(superPlayer); WeaponRuntime.tickPlayer(superPlayer);
            for (var p : f.players) state(h, p.getMainHandItem(), 2, 2, 0, 0);
        });
        f.at(62, () -> {
            for (var p : f.players) {
                check(h, !WeaponRuntime.reloading(p) && WeaponIzanagi.canStart(p), "Retired exact pending generation cannot resurrect after return");
                state(h, p.getMainHandItem(), 2, 2, 0, 0); hud(h, p, 0);
            }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 140, environment = "destiny-test:w90_isolated")
    public void pendingCopyReplacementAndExactStackOwnerTransferRequireFreshAcceptedReload(GameTestHelper h) {
        var f = new Fixture(h); var donor = f.player(8); var recipient = f.player(24);
        var original = f.equip(donor, 2, 2, 0); f.equip(recipient, 0, 0, 0); reload(h, donor, true);
        var copy = new ItemStack[1];
        f.at(30, () -> {
            copy[0] = original.copy(); donor.getInventory().setItem(0, copy[0]); recipient.getInventory().setItem(0, original);
            WeaponRuntime.tickPlayer(donor); WeaponRuntime.tickPlayer(recipient);
            check(h, donor.getMainHandItem() == copy[0] && recipient.getMainHandItem() == original, "Actual inventory replacement and transfer use distinct exact objects");
        });
        f.at(61, () -> { state(h, copy[0], 2, 2, 0, 0); state(h, original, 2, 2, 0, 0); });
        f.at(62, () -> { reload(h, donor, true); reload(h, recipient, true); });
        f.at(122, () -> { state(h, copy[0], 2, 2, 0, 0); state(h, original, 2, 2, 0, 0); });
        f.at(123, () -> {
            state(h, copy[0], 1, 0, 0, 4); state(h, original, 1, 0, 0, 4);
            hud(h, donor, 4); hud(h, recipient, 4); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void completedChargeSurvivesStowSaveAndTransferButStrictMalformedSavedValuesStayIneligible(GameTestHelper h) {
        var f = new Fixture(h); var donor = f.player(8); var recipient = f.player(24);
        var gun = f.equip(donor, 4, 0, 0); f.equip(recipient, 0, 0, 0); reload(h, donor, true);
        f.at(61, () -> {
            state(h, gun, 1, 0, 0, 4);
            hotbarRoundTrip(h, donor);
            check(h,WeaponIzanagi.charge(gun)==4,"Completed charge survives actual hotbar return");
            offhandRoundTrip(h, donor);
            check(h,WeaponIzanagi.charge(gun)==4,"Completed charge survives actual offhand return");
            containerRoundTrip(h, donor);
            check(h,WeaponIzanagi.charge(gun)==4,"Completed charge survives actual container return");
            state(h, gun, 1, 0, 0, 4);
            var ops = h.getLevel().registryAccess().createSerializationContext(JsonOps.INSTANCE);
            var saved = ItemStack.CODEC.parse(ops, ItemStack.CODEC.encodeStart(ops, gun).getOrThrow()).getOrThrow();
            check(h,WeaponIzanagi.charge(saved)==4,"Actual JSON codec saved charge: item="+saved.getItem()+", tag="+saved.get(DataComponents.CUSTOM_DATA)+", numericType="+saved.get(DataComponents.CUSTOM_DATA).copyTag().get(WeaponIzanagi.CHARGE).getClass().getName());
            state(h, saved, 1, 0, 0, 4);
            var nbtOps=h.getLevel().registryAccess().createSerializationContext(net.minecraft.nbt.NbtOps.INSTANCE);
            var nbtSaved=ItemStack.CODEC.parse(nbtOps,ItemStack.CODEC.encodeStart(nbtOps,gun).getOrThrow()).getOrThrow();
            state(h,nbtSaved,1,0,0,4);
            for(var integral:List.of(net.minecraft.nbt.ByteTag.valueOf((byte)4),net.minecraft.nbt.ShortTag.valueOf((short)4),
                    net.minecraft.nbt.IntTag.valueOf(4),net.minecraft.nbt.LongTag.valueOf(4))) {
                var integralSaved=saved.copy();var integralData=integralSaved.get(DataComponents.CUSTOM_DATA).copyTag();
                integralData.put(WeaponIzanagi.CHARGE,integral);integralSaved.set(DataComponents.CUSTOM_DATA,CustomData.of(integralData));
                state(h,integralSaved,1,0,0,4);
            }
            // Copies are observation-only malformed-data witnesses, never used to grant a gameplay shot.
            for (int invalid : new int[]{Integer.MIN_VALUE, -1, 0, 1, 5, Integer.MAX_VALUE}) {
                var copy = saved.copy(); var tag = copy.get(DataComponents.CUSTOM_DATA).copyTag(); tag.putInt(WeaponIzanagi.CHARGE, invalid);
                copy.set(DataComponents.CUSTOM_DATA, CustomData.of(tag)); check(h, WeaponIzanagi.charge(copy) == 0, "Out-of-domain saved charge fails closed");
            }
            var wrongType = saved.copy(); var tag = wrongType.get(DataComponents.CUSTOM_DATA).copyTag(); tag.put(WeaponIzanagi.CHARGE, net.minecraft.nbt.DoubleTag.valueOf(4));
            wrongType.set(DataComponents.CUSTOM_DATA, CustomData.of(tag)); check(h, WeaponIzanagi.charge(wrongType) == 0, "Floating-point coercion cannot grant a saved charge");
            for (int n : new int[]{0,2,3,4}) {
                var copy = saved.copy(); WeaponItems.save(copy, new WeaponMagazine(profile(copy), n, 0));
                check(h, WeaponIzanagi.charge(copy) == 0, "Saved charge needs exactly one funded loaded projectile");
            }
            donor.getInventory().setItem(0, ItemStack.EMPTY); recipient.getInventory().setItem(0, gun);
            WeaponRuntime.tickPlayer(donor); WeaponRuntime.tickPlayer(recipient);
            check(h, recipient.getMainHandItem() == gun, "Actual completed charged object transfers, unlike pending authority");
            state(h, gun, 1, 0, 0, 4); hud(h, donor, 0); hud(h, recipient, 4);
        });
        f.at(82, () -> {
            var victim = f.primary(recipient, 10, false, HP); shot(h, recipient, victim);
            hp(h, victim, HP - 16 * 2.12f, "Recipient spends the original legitimately earned saved x4 shot"); hud(h, recipient, 0); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void alternateReplacesOrdinaryAndShotOrEmptyTriggeredReloadAtFreshSixtyOneDeadlineWithoutFreeAmmo(GameTestHelper h) {
        var f = new Fixture(h);
        var manual = f.player(4); var auto = f.player(12); var empty = f.player(20); var cancel = f.player(28);
        var a = f.equip(manual, 1, 5, 0); var b = f.equip(auto, 1, 5, 0);
        var c = f.equip(empty, 0, 5, 0); var d = f.equip(cancel, 1, 5, 0);
        reload(h, manual, false); shot(h, auto, null);
        // Tick the real last-shot candidate into its ordinary automatic reload, no synthetic cycle access.
        WeaponRuntime.tickPlayer(auto);
        check(h, WeaponRuntime.reloading(auto), "Actual paid last shot starts ordinary auto-empty reload");
        check(h, !WeaponRuntime.beginUse(empty) && WeaponRuntime.reloading(empty), "Actual dry trigger starts ordinary empty reload without emission");
        reload(h, cancel, false);
        f.at(20, () -> {
            for (var p : f.players) reload(h, p, true);
            state(h, a, 1, 5, 0, 0); state(h, b, 0, 5, 0, 0); state(h, c, 0, 5, 0, 0); state(h, d, 1, 5, 0, 0);
        });
        f.at(40, () -> {
            for (var p : List.of(manual, auto, empty)) request(p, true); // must not restart pending61
            containerRoundTrip(h, cancel); // real out/back retires the replacement generation too
        });
        f.at(61, () -> {
            for (var p : List.of(manual, auto, empty)) check(h, WeaponRuntime.reloading(p), "Old ordinary61 deadline cannot credit or finish replacement");
            state(h, a, 1, 5, 0, 0); state(h, b, 0, 5, 0, 0); state(h, c, 0, 5, 0, 0); state(h, d, 1, 5, 0, 0);
        });
        f.at(80, () -> { state(h, a, 1, 5, 0, 0); state(h, b, 0, 5, 0, 0); state(h, c, 0, 5, 0, 0); state(h, d, 1, 5, 0, 0); });
        f.at(81, () -> {
            state(h, a, 1, 2, 0, 4); state(h, b, 1, 1, 0, 4); state(h, c, 1, 1, 0, 4); state(h, d, 1, 5, 0, 0);
            for (var p : f.players) check(h, !WeaponRuntime.reloading(p), "Fresh61 reset policy completes only uncancelled replacements");
            check(h, WeaponIzanagi.canStart(cancel), "Cancelled replacement has no hidden pending lock or free ammo"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void chargedNormalAlternateAndMarksmanReloadDenyWithoutMutationWhileOrdinaryShotKeepsBaseDamage(GameTestHelper h) {
        var f = new Fixture(h); var charged = f.player(8); var ordinary = f.player(24);
        var a = f.equip(charged, 1, 8, 0); var b = f.equip(ordinary, 1, 8, 0);
        reload(h, charged, true); reload(h, ordinary, false);
        f.at(61, () -> {
            state(h, a, 1, 5, 0, 4); state(h, b, 4, 5, 0, 0);
            var before = a.copy(); request(charged, false); request(charged, true);
            check(h, !WeaponRuntime.reload(charged) && !WeaponRuntime.reloadHoned(charged)
                            && WeaponRuntime.reloadFromMarksmanDodge(charged) == 0
                            && !WeaponRuntime.reloading(charged) && ItemStack.matches(before, a),
                    "Explicit local charged-reload/Marksman policy denies all three without erasing funded charge");
            hud(h, charged, 4);
        });
        f.at(65, () -> {
            var honedVictim = f.primary(charged, 10, false, HP); var baseVictim = f.primary(ordinary, 10, false, HP);
            shot(h, charged, honedVictim); shot(h, ordinary, baseVictim);
            hp(h, honedVictim, HP - 16 * 2.12f, "Denied actions do not corrupt saved paid multiplier");
            hp(h, baseVictim, HP - 16, "Ordinary reload and paid emission keep exact uncharged base16HP");
            state(h, a, 0, 5, 0, 0); state(h, b, 3, 5, 0, 0); hud(h, charged, 0); h.succeed();
        });
    }
}
