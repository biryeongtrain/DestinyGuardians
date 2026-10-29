package kim.biryeong.destiny.test;

import com.mojang.serialization.JsonOps;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.AceReticleCounter;
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

/** Paid production Ace emissions on the existing 48x12x32 W78 raised deck.
 * All GameTest callbacks are registered during fixture initialization. Late targets only join
 * the fixture's already-registered bounds/cleanup lists; no callback installs another callback.
 * Reload deadlines use actual server ticks. No synthetic kill events, direct cycle grants,
 * reflected clocks or persisted Mori counters. PvE targeting deliberately excludes players.
 */
public final class WeaponAceW83GameTests {
    private static final String FLOOR = "destiny-test:w78_floor", ACE = "ace_of_spades";
    private static final float HP = 1000, EPS = .004f;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static void hp(GameTestHelper h, LivingEntity target, float expected, String message) {
        check(h, Math.abs(target.getHealth() - expected) < EPS,
                message + "; expected=" + expected + ", actual=" + target.getHealth());
    }
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static WeaponCatalog.Entry ace() { return WeaponCatalog.find(ACE).orElseThrow(); }
    private static WeaponProfile profile(ItemStack gun) {
        return WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());
    }
    private static WeaponMagazine ammo(ItemStack gun) { return WeaponItems.magazine(gun, profile(gun)); }
    private static WeaponReloadPolicy.Plan basePlan() { return new WeaponReloadPolicy.Plan(55, 55, 0); }
    private static void bounded(GameTestHelper h, Entity entity) {
        var o = h.absoluteVec(Vec3.ZERO); var b = entity.getBoundingBox();
        check(h, b.minX > o.x && b.maxX < o.x + 48 && b.minY > o.y && b.maxY < o.y + 12
                        && b.minZ > o.z && b.maxZ < o.z + 32,
                "Whole W83 entity AABB remains inside its own 48x12x32 fixture: " + entity.getUUID());
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
                    "W83_" + UUID.randomUUID().toString().substring(0, 8));
            players.add(p); p.setNoGravity(true); p.setOnGround(true);
            p.setAttached(WeaponLoadout.ENABLED, false); bounded(h, p);
            return p;
        }
        ItemStack equip(ServerPlayer p) {
            var gun = WeaponItems.create(ace());
            gun.set(DataComponents.CUSTOM_NAME, Component.literal("W83_" + UUID.randomUUID()));
            p.getInventory().setItem(0, gun); p.getInventory().setSelectedSlot(0);
            WeaponRuntime.tickPlayer(p); TestPlayers.drain(p);
            check(h, p.getMainHandItem() == gun && WeaponExotics.ace(WeaponItems.entry(gun).orElseThrow())
                            && !WeaponModels.twoHanded(gun) && ammo(gun).rounds() == 13 && ammo(gun).reserve() == 0
                            && profile(gun).infiniteReserve() && profile(gun).mode() == WeaponProfile.Mode.HITSCAN
                            && profile(gun).burst() == 1 && profile(gun).pellets() == 1 && profile(gun).chargeTicks() == 0,
                    "Canonical native-grip Ace is exactly one paid primary hitscan per trigger");
            return gun;
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
            check(h, WeaponPrecision.critical(t, from, hit, WeaponBallistics.of(ace()).precision()) == precision
                            && Combat.isEnemy(p, t) && !p.isAlliedTo(t),
                    "Production precision classifier and hostile admission match the intended victim");
            var wall = p.level().clip(new ClipContext(from, hit, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
            check(h, wall.getType() == HitResult.Type.MISS, "Direct paid shot has clear positive fixture LOS");
            return t;
        }
        void kill(ServerPlayer p, boolean precision) {
            var t = primary(p, 10, precision, 1); shot(h, p, false);
            check(h, t.isDeadOrDying() && t.getHealth() == 0, "One actual paid direct shot caused the final blow");
            t.discard();
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

    private static void shot(GameTestHelper h, ServerPlayer p, boolean miss) {
        shot(h,p,miss,null);
    }
    private static void shot(GameTestHelper h, ServerPlayer p, boolean miss, LivingEntity expected) {
        WeaponAiming.cleanup(p); p.setShiftKeyDown(false);
        p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(miss ? 90 : 0); WeaponAiming.tick(p);
        // Preflight and paid emission must use the same deterministic dispersion sample.
        p.getRandom().setSeed(0x5DEECE66DL);
        var firingDirection = WeaponAiming.direction(p);
        var gun = p.getMainHandItem(); int before = ammo(gun).rounds(), reserve = ammo(gun).reserve();
        check(h, before > 0 && !WeaponHandling.blocked(p), "Paid trigger fixture has ammunition and completed handling");
        if (miss) {
            var floor = p.level().clip(new ClipContext(p.getEyePosition(), p.getEyePosition().add(0, -4, 0),
                    ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
            check(h, floor.getType() == HitResult.Type.BLOCK, "Miss points straight down into the raised stone deck");
        } else {
            var from=p.getEyePosition(); var to=from.add(firingDirection.scale(30));
            var first=net.minecraft.world.entity.projectile.ProjectileUtil.getEntityHitResult(p.level(),p,from,to,
                    new net.minecraft.world.phys.AABB(from,to).inflate(.23), e -> Combat.isEnemy(p,e) && !p.isAlliedTo(e), .03f);
            check(h, first != null, "Positive native entity-query preflight before paid hit; eye="+from
                    +", direction="+firingDirection+", candidates="+p.level().getEntities(p,
                    new net.minecraft.world.phys.AABB(from,to).inflate(.23),e->Combat.isEnemy(p,e)));
        }
        if(expected!=null) {
            // W87: observe the exact normalized ray AFTER the helper's aim reset, and use
            // production block clipping/wall-tie policy, not a different raw entity ray.
            var from=p.getEyePosition();var direction=firingDirection;
            var fullEnd=from.add(direction.scale(WeaponBallistics.traceRange(profile(gun))));
            try {
                var guard=WeaponRuntime.class.getDeclaredMethod("loadedEnd",net.minecraft.server.level.ServerLevel.class,Vec3.class,Vec3.class);
                guard.setAccessible(true);var guardedEnd=(Vec3)guard.invoke(null,p.level(),from,fullEnd);
                var trace=WeaponRuntime.class.getDeclaredMethod("trace",ServerPlayer.class,Vec3.class,Vec3.class,float.class);
                trace.setAccessible(true);var result=(HitResult)trace.invoke(null,p,from,guardedEnd,.03f);
                String detail="; eye="+from+", direction="+direction+", fullEnd="+fullEnd+", guardedEnd="+guardedEnd
                        +", hitType="+result.getType()+", hitPoint="+result.getLocation()+", expected="+expected.getUUID()+", expectedBox="+expected.getBoundingBox()
                        +", selected="+(result instanceof net.minecraft.world.phys.EntityHitResult entity?entity.getEntity().getUUID()+"/"+entity.getEntity().getType()+"/"+entity.getEntity().position()+"/"+entity.getEntity().getBoundingBox():"none")
                        +", corridorCandidates="+p.level().getEntities(p,new net.minecraft.world.phys.AABB(from,guardedEnd).inflate(.23), e->Combat.isEnemy(p,e)).stream()
                        .map(e->e.getUUID()+"/"+e.getType()+"/"+e.position()+"/"+e.getBoundingBox()).toList();
                check(h,result instanceof net.minecraft.world.phys.EntityHitResult entity&&entity.getEntity()==expected,
                        "Normalized production trace selects exact paid witness"+detail);
            } catch(ReflectiveOperationException ex) {throw new IllegalStateException("Read-only exact production trace diagnostic",ex);}
        }
        p.getRandom().setSeed(0x5DEECE66DL); // Replay the inspected ray for the actual paid shot.
        check(h, WeaponRuntime.beginUse(p), "Real WeaponRuntime beginUse accepts this paid emission");
        WeaponRuntime.releaseUse(p, gun); p.stopUsingItem();
        check(h, ammo(gun).rounds() == before - 1 && ammo(gun).reserve() == reserve
                        && WeaponRuntime.activeProjectiles(p) == 0,
                "Exactly one loaded round is paid by this hitscan, including a miss");
    }
    private static void reload(GameTestHelper h, ServerPlayer p, int ticks) {
        check(h, WeaponAce.plan(p, ace(), basePlan()).equals(new WeaponReloadPolicy.Plan(ticks, ticks, 0)),
                "Reload captures the exact base/Firefly full recovery plan");
        var gun = p.getMainHandItem(); int before = ammo(gun).rounds();
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.DROP_ITEM, BlockPos.ZERO, Direction.UP));
        check(h, WeaponRuntime.reloading(p) && p.getMainHandItem() == gun && ammo(gun).rounds() == before,
                "Actual Q packet starts reload without dropping, replacing or instantly refilling the gun");
    }
    private static void hud(GameTestHelper h, ServerPlayer p, int count) {
        var gun = p.getMainHandItem(); var saved = gun.copy(); int before = WeaponAce.rounds(p);
        CombatHud.update(p);
        WeaponPerkHud.update(p); WeaponPerkHud.update(p);
        AceReticleCounter.update(p); AceReticleCounter.update(p);
        String key = WeaponPerkHud.PREFIX + "memento_mori_";
        var keys = DisplayHud.getHuds(p).keySet().stream().filter(k -> k.startsWith(key)).collect(Collectors.toSet());
        var expected = count == 0 ? Set.<String>of() : Set.of(key + "marker", key + "label", key + "x", key + "count");
        check(h, keys.equals(expected), "Mori HUD is exactly four count nodes, never a countdown or stale row");
        if (count > 0) {
            var digit = (ItemDisplayHud) DisplayHud.getHud(p, key + "count");
            check(h, Identifier.fromNamespaceAndPath("destiny", "gui/hud/ammo_digit_" + count)
                            .equals(digit.getItem().get(DataComponents.ITEM_MODEL)), "HUD shows actual remaining paid emissions " + count);
        }
        var pips = DisplayHud.getHuds(p).keySet().stream()
                .filter(k -> k.startsWith(AceReticleCounter.PREFIX)).collect(Collectors.toSet());
        check(h, pips.size() == (count == 0 ? 0 : AceReticleCounter.MAX_NODES),
                "Reticle counter has six bounded slots only while earned Mori remains");
        if (count > 0) {
            long bright = pips.stream().map(k -> (ItemDisplayHud) DisplayHud.getHud(p, k))
                    .filter(node -> node.getItem().get(DataComponents.CUSTOM_MODEL_DATA).colors().getFirst() == 0xF1F3F5)
                    .count();
            check(h, bright == count, "Lit reticle pips follow remaining paid emissions " + count);
        }
        check(h, before == count && WeaponAce.rounds(p) == before && ItemStack.matches(saved, gun),
                "Repeated HUD reads neither spend rounds nor mutate the authoritative stack");
    }
    private static void hotbarRoundTrip(GameTestHelper h, ServerPlayer p) {
        var gun = p.getMainHandItem(); int rounds = ammo(gun).rounds(); long tick = now(p);
        p.getInventory().setItem(1, new ItemStack(Items.STONE));
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
        check(h, p.getMainHandItem().is(Items.STONE), "First validated packet genuinely stows Ace");
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));
        check(h, now(p) == tick && p.getMainHandItem() == gun && ammo(gun).rounds() == rounds,
                "Same-tick native slot round trip returns the identical paid stack");
        WeaponAce.update(p);
    }
    private static void offhandRoundTrip(GameTestHelper h, ServerPlayer p) {
        var gun = p.getMainHandItem(); int rounds = ammo(gun).rounds(); long tick = now(p);
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.STONE));
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND, BlockPos.ZERO, Direction.UP));
        check(h, p.getOffhandItem() == gun && p.getMainHandItem().is(Items.STONE), "Actual non-Guardian packet stows exact Ace in offhand");
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND, BlockPos.ZERO, Direction.UP));
        check(h, now(p) == tick && p.getMainHandItem() == gun && p.getOffhandItem().is(Items.STONE)
                        && ammo(gun).rounds() == rounds, "Actual same-tick offhand return preserves exact identity and paid ammo");
        WeaponAce.update(p);
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
    public void exactFirstExoticAndAllOriginalSixtyThreeKeepIdentityGripAndRegistrySerialization(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(16); var gun = f.equip(p);
        WeaponModelGameTests.assertCatalogExpansion(h);
        for (var legacy : WeaponModelGameTests.originalW30Entries()) check(h,
                !WeaponExotics.ace(legacy) && !WeaponCharacteristics.of(legacy).exotic(), "Every original W30 weapon stays ineligible for Ace: " + legacy.id());
        var m = WeaponCharacteristics.of(ace());
        check(h, m.bungieHash() == 347366834L && m.slot() == WeaponSlot.KINETIC && m.ammo() == WeaponAmmoType.PRIMARY
                        && m.damage() == WeaponCharacteristics.Damage.KINETIC && m.stats().get("1240592695") == 85
                        && m.stats().get("155624089") == 50 && m.stats().get("943549884") == 50
                        && WeaponAimProfile.of(ace()).transitionTicks() == 5 && profile(gun).reloadTicks() == 55,
                "Exact kinetic primary Ace and effective fixed-plug 85/50/50 stats, five-tick ADS, base reload 55");
        check(h, !WeaponExotics.ace(null) && !WeaponExotics.ace(new WeaponCatalog.Entry(ACE, "auto_rifle", "exotic",
                        ace().name(), ace().source_frame_label(), ace().item_model())), "Unknown or forged identity cannot borrow Ace mechanics");
        var ops = h.getLevel().registryAccess().createSerializationContext(JsonOps.INSTANCE);
        var context = ((PacketContextProvider) (Object) p.connection).getPacketContext();
        for (var grip : WeaponModels.Grip.values()) for (var pose : WeaponModels.Pose.values()) {
            var live = WeaponModels.withGrip(gun, grip).orElseThrow(); WeaponModels.setPose(live, pose);
            var decoded = ItemStack.CODEC.parse(ops, ItemStack.CODEC.encodeStart(ops, live).getOrThrow()).getOrThrow();
            check(h, WeaponItems.entry(decoded).orElseThrow().equals(ace()) && ammo(decoded).rounds() == 13,
                    "Registry stack codec retains exact exotic identity, every pose, grip and finite magazine");
            var wire = PolymerItemUtils.getPolymerItemStack(decoded, context, h.getLevel().registryAccess());
            boolean two = grip == WeaponModels.Grip.TWO_HAND;
            check(h, wire.is(two ? Items.CROSSBOW : Items.STICK) && CrossbowItem.isCharged(wire) == two,
                    "Ace explicitly supports both existing safe carrier protocols");
            check(h, ItemStack.matches(decoded, PolymerItemUtils.getRealItemStack(wire, context, h.getLevel().registryAccess())),
                    "Actual Polymer wire round trip preserves authoritative exotic components");
        }
        hud(h, p, 0); h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void paidBodyKillGrantsSixOnlyAtFullReloadRecoveryAfterEarlyAmmoCredit(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(16); var gun = f.equip(p);
        f.kill(p, false); check(h, WeaponAce.fireflyRemaining(p) == 0, "Body final blow never grants Firefly"); reload(h, p, 55);
        f.at(39, () -> { check(h, ammo(gun).rounds() == 12 && WeaponAce.rounds(p) == 0, "Before ceil(55*.71)=40, no ammo transfer or Mori"); hud(h, p, 0); });
        f.at(40, () -> check(h, ammo(gun).rounds() == 13 && WeaponRuntime.reloading(p) && WeaponAce.rounds(p) == 0,
                "W65 credits real ammunition at 40 while full recovery still owns Mori authorization"));
        f.at(54, () -> check(h, WeaponRuntime.reloading(p) && WeaponAce.rounds(p) == 0, "No activation one tick before full recovery"));
        f.at(55, () -> {
            check(h, !WeaponRuntime.reloading(p) && WeaponAce.rounds(p) == 6 && ammo(gun).rounds() == 13,
                    "Full paid reload recovery grants exactly six, with no extra ammunition"); hud(h, p, 6); h.succeed();
        });
    }

    /** W158: genuine earned buff, cosmetic visibility and strictly prefix-local cleanup. */
    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void earnedReticleCounterHidesOnIneligibleHandAndDoesNotTouchForeignHud(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(16); var gun = f.equip(p);
        f.kill(p, false); reload(h, p, 55);
        f.at(55, () -> {
            hud(h, p, 6);
            // W160: observing a genuinely earned six-shot state cannot consume or render it.
            var beforeStatus = gun.copy();
            var nodesBefore = java.util.Map.copyOf(DisplayHud.getHuds(p));
            try {
                var server = p.level().getServer();
                for (int i = 0; i < 3; i++) check(h, server.getCommands().getDispatcher().execute(
                        "destiny debug weapon-presentation-status @s", server.createCommandSourceStack().withEntity(p)) == 1,
                        "Permission-guarded status reads the real earned buff");
            } catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) { throw new AssertionError(e); }
            check(h, WeaponAce.rounds(p) == 6 && ItemStack.matches(beforeStatus, gun)
                            && nodesBefore.equals(DisplayHud.getHuds(p)),
                    "Repeated status leaves earned rounds, item components and the existing HUD objects untouched");
            String sentinel = "destiny:w158_foreign_sentinel";
            var foreign = new ItemDisplayHud(); foreign.setItem(new ItemStack(Items.PAPER));
            foreign.spawn(p, sentinel);
            try {
                int rounds = ammo(gun).rounds();
                p.setShiftKeyDown(true); AceReticleCounter.update(p);
                check(h, DisplayHud.getHuds(p).keySet().stream().filter(k -> k.startsWith(AceReticleCounter.PREFIX)).count() == 6,
                        "Earned counter remains available with ADS intent; no generic ring reinstated");
                p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STONE));
                AceReticleCounter.update(p); AceReticleCounter.remove(p);
                check(h, DisplayHud.getHuds(p).keySet().stream().noneMatch(k -> k.startsWith(AceReticleCounter.PREFIX))
                                && DisplayHud.getHud(p, sentinel) == foreign,
                        "Swap/ineligible cleanup removes only its own pips");
                check(h, ammo(gun).rounds() == rounds, "Counter cleanup cannot change ammunition");
                p.setItemInHand(InteractionHand.MAIN_HAND, gun); p.setShiftKeyDown(false);
                AceReticleCounter.update(p); CombatHud.remove(p);
                check(h, DisplayHud.getHuds(p).keySet().stream().noneMatch(k -> k.startsWith(AceReticleCounter.PREFIX))
                                && DisplayHud.getHud(p, sentinel) == foreign,
                        "CombatHud lifecycle cleanup retires counter without foreign HUD deletion");
            } finally { DisplayHud.removeHud(p, sentinel); }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 135, environment = "destiny-test:w90_isolated")
    public void sixPaidEmissionsIncludingMissesSpendMoriAndSeventhReturnsToBaseDamage(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(16); var gun = f.equip(p); f.kill(p, false); reload(h, p, 55);
        f.at(55, () -> { check(h, WeaponAce.rounds(p) == 6, "Real kill/reload positively armed six rounds"); hud(h, p, 6); });
        for (int i = 0; i < 7; i++) {
            int index = i;
            f.at(65 + 9 * i, () -> {
                boolean miss = index > 0 && index < 5;
                Husk victim = miss ? null : f.primary(p, 10, false, HP);
                shot(h, p, miss);
                if (victim != null) { hp(h, victim, HP - profile(gun).damage() * (index < 6 ? 1.68f : 1), "Paid body damage uses Mori for six emissions only"); victim.discard(); }
                check(h, WeaponAce.rounds(p) == Math.max(0, 5 - index) && ammo(gun).rounds() == 12 - index,
                        "Every accepted emission spends exactly one loaded bullet and one available Mori round");
                hud(h, p, Math.max(0, 5 - index));
                if (index == 6) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void empoweredPaidBodyShotUsesFifteenPercentShorterFalloffDistance(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(16); var gun = f.equip(p); f.kill(p, false); reload(h, p, 55);
        f.at(65, () -> {
            check(h, WeaponAce.rounds(p) == 6, "Falloff comparison starts from a real qualifying full reload");
            var victim = f.primary(p, 29, false, HP); var from = p.getEyePosition();
            double distance = from.distanceTo(victim.getBoundingBox().inflate(.03).clip(from, from.add(40, 0, 0)).orElseThrow());
            double start = (16 + .09 * 85) * .85, end = (29 + .03 * 85) * .85;
            check(h, distance > start && distance < end, "Witness lies strictly inside reduced Mori falloff segment");
            double falloff = 1 - (1 - .33) * (distance - start) / (end - start);
            shot(h, p, false, victim); hp(h, victim, HP - profile(gun).damage() * 1.68f * (float) falloff,
                    "Actual paid HP loss scales distance by .85 independently of the 1.68 damage multiplier");
            check(h, WeaponAce.rounds(p) == 5, "Falloff hit consumes one of six actual rounds"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 85, environment = "destiny-test:w90_isolated")
    public void fullRecoveryAtSeventyTwoQualifiesAndAtSeventyThreeExpires(GameTestHelper h) {
        var f = new Fixture(h); var edge = f.player(8); var late = f.player(24);
        f.equip(edge); f.equip(late); f.kill(edge, false); f.kill(late, false);
        f.at(17, () -> reload(h, edge, 55)); f.at(18, () -> reload(h, late, 55));
        f.at(71, () -> check(h, WeaponRuntime.reloading(edge) && WeaponAce.rounds(edge) == 0 && WeaponAce.rounds(late) == 0,
                "Starting within the kill window alone cannot grant Mori"));
        f.at(72, () -> check(h, !WeaponRuntime.reloading(edge) && WeaponAce.rounds(edge) == 6
                        && WeaponRuntime.reloading(late) && WeaponAce.rounds(late) == 0,
                "Completion at the exact local 72-server-tick boundary qualifies"));
        f.at(73, () -> { check(h, !WeaponRuntime.reloading(late) && ammo(late.getMainHandItem()).rounds() == 13
                        && WeaponAce.rounds(late) == 0, "Completion one tick late still reloads paid ammo but grants no Mori"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 135, environment = "destiny-test:w90_isolated")
    public void paidPrecisionFireflyUsesCoreOuterFloorLosAndThirtyNineTickReload(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(16); var gun = f.equip(p);
        var corpse = f.primary(p, 10, true, 1);
        var core = f.target(10, 4, 18, HP); var outer = f.target(10, 4, 22, HP);
        var edge = f.target(10, 4, 23.5, HP); var outside = f.target(10, 4, 24, HP); var blocked = f.target(10, 4, 12, HP);
        for (int x = 9; x <= 11; x++) for (int y = 4; y <= 7; y++) h.setBlock(x, y, 14, Blocks.STONE);
        var center = corpse.getBoundingBox().getCenter();
        for (var t : List.of(core, outer, edge, outside, blocked)) check(h, Combat.isEnemy(p, t) && !p.isAlliedTo(t), "Blast witnesses are eligible living hostiles");
        check(h, center.distanceTo(core.getBoundingBox().getCenter()) <= 3.75
                        && center.distanceTo(edge.getBoundingBox().getCenter()) == 7.5
                        && center.distanceTo(outside.getBoundingBox().getCenter()) > 7.5,
                "Positive core, exact spherical edge and outside geometry preflights");
        check(h, p.level().clip(new ClipContext(center, blocked.getBoundingBox().getCenter(), ClipContext.Block.COLLIDER,
                        ClipContext.Fluid.NONE, p)).getType() == HitResult.Type.BLOCK, "Blocked witness has a real intervening stone LOS barrier");
        shot(h, p, false); check(h, corpse.isDeadOrDying(), "Actual paid precision final blow is the sole Firefly trigger");
        hp(h, core, HP - 15, "Authored 15 HP full core"); hp(h, outer, HP - 15 * (1 - .8f * (6 - 3.75f) / 3.75f), "Authored linear outer attenuation");
        hp(h, edge, HP - 3, "Sourced .2 endpoint floor at 7.5m"); hp(h, outside, HP, "Outside sphere untouched"); hp(h, blocked, HP, "Stone LOS blocks Firefly");
        check(h, WeaponAce.fireflyRemaining(p) == 120 && WeaponAce.rounds(p) == 0
                        && WeaponCharacteristics.of(ace()).stats().get("4188031367") + 50 == 92,
                "Precision kill starts exactly 120 server ticks of +50 reload stat, without prematurely loading Mori");
        reload(h, p, 39);
        f.at(27, () -> check(h, ammo(gun).rounds() == 12 && WeaponAce.rounds(p) == 0, "Before boosted W65 credit there is no transfer"));
        f.at(28, () -> check(h, ammo(gun).rounds() == 13 && WeaponRuntime.reloading(p) && WeaponAce.rounds(p) == 0, "Boosted early ammo credit still cannot grant Mori"));
        f.at(38, () -> check(h, WeaponRuntime.reloading(p) && WeaponAce.rounds(p) == 0, "Thirty-eight is still recovery"));
        f.at(39, () -> { check(h, !WeaponRuntime.reloading(p) && WeaponAce.rounds(p) == 6, "Actual boosted full recovery completes at39"); hud(h, p, 6); });
        f.at(119, () -> check(h, WeaponAce.fireflyRemaining(p) == 1, "Last Firefly tick has one real server tick remaining"));
        f.at(120, () -> { check(h, WeaponAce.fireflyRemaining(p) == 0 && WeaponAce.plan(p, ace(), basePlan()).equals(basePlan())
                        && WeaponAce.rounds(p) == 6, "Firefly expires exactly at120; loaded Mori has no fabricated time expiry"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void secondaryFireflyKillNeverRecursesOrGrantsExtraMoriRounds(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(16); f.equip(p);
        var corpse = f.primary(p, 10, true, 1); var secondary = f.target(14, 4, 16, 1); var chainOnly = f.target(20, 4, 16, HP);
        var center = corpse.getBoundingBox().getCenter();
        check(h, center.distanceTo(secondary.getBoundingBox().getCenter()) < 7.5
                        && center.distanceTo(chainOnly.getBoundingBox().getCenter()) > 7.5
                        && secondary.getBoundingBox().getCenter().distanceTo(chainOnly.getBoundingBox().getCenter()) < 7.5,
                "Secondary is killed by the first blast; chain-only witness could be hit only by a forbidden recursive blast");
        shot(h, p, false);
        check(h, corpse.isDeadOrDying() && secondary.isDeadOrDying() && WeaponAce.rounds(p) == 0,
                "One paid direct precision kill and one real secondary blast kill grant no immediate free rounds");
        hp(h, chainOnly, HP, "Secondary final blow never recursively emits Firefly"); reload(h, p, 39);
        f.at(39, () -> { check(h, WeaponAce.rounds(p) == 6, "Multiple real kills from one trigger grant exactly one six-round load"); hp(h, chainOnly, HP, "No deferred recursive blast"); });
        f.at(49, () -> { shot(h, p, true); check(h, WeaponAce.rounds(p) == 5, "One paid miss after the secondary kill spends one round, with no extra kill refund"); hud(h, p, 5); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void sameTickHotbarStowDropsLoadedMoriButRetainsPendingKillAndFirefly(GameTestHelper h) {
        var f = new Fixture(h); var loaded = f.player(8); var pending = f.player(24);
        f.equip(loaded); f.equip(pending); f.kill(loaded, false); reload(h, loaded, 55);
        f.kill(pending, true); hotbarRoundTrip(h, pending);
        check(h, WeaponAce.rounds(pending) == 0 && WeaponAce.fireflyRemaining(pending) == 120,
                "Same exact stack keeps Firefly and its pending kill trigger across stow");
        // Eight-tick stow plus seven-tick ready are real handling, never bypassed by the fixture.
        f.at(17, () -> reload(h, pending, 39));
        f.at(55, () -> check(h, WeaponAce.rounds(loaded) == 6 && WeaponAce.rounds(pending) == 0, "Independent loaded and still-recovering owners"));
        f.at(56, () -> {
            check(h, WeaponAce.rounds(pending) == 6, "Pending trigger survived stow and qualified at full recovery within72");
            hotbarRoundTrip(h, loaded); hotbarRoundTrip(h, pending);
            check(h, WeaponAce.rounds(loaded) == 0 && WeaponAce.rounds(pending) == 0 && WeaponAce.fireflyRemaining(pending) == 64,
                    "Validated away/back packets in one server tick clear loaded Mori only, retaining the exact stack Firefly timer");
            hud(h, loaded, 0); hud(h, pending, 0); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void sameTickVanillaOffhandRoundTripKeepsPendingEffectsButClearsLoadedHud(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(16); f.equip(p); f.kill(p, true); offhandRoundTrip(h, p);
        check(h, WeaponAce.fireflyRemaining(p) == 120 && WeaponAce.rounds(p) == 0, "Offhand stow retains pending Firefly and kill eligibility");
        f.at(1, () -> reload(h, p, 39));
        f.at(40, () -> { check(h, WeaponAce.rounds(p) == 6, "Exact returned stack qualifies only through a real full reload"); hud(h, p, 6); });
        f.at(41, () -> {
            offhandRoundTrip(h, p);
            check(h, WeaponAce.rounds(p) == 0 && WeaponAce.fireflyRemaining(p) == 79,
                    "Same-tick vanilla offhand round trip clears six loaded rounds while retaining Firefly"); hud(h, p, 0); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void sameTickContainerNumberKeyRoundTripClearsLoadedMoriRetainsPendingEffectsAndRetiresReloadGeneration(GameTestHelper h) {
        var f = new Fixture(h); var loaded = f.player(8); var pending = f.player(16); var interrupted = f.player(24);
        var loadedGun = f.equip(loaded); f.equip(pending); var interruptedGun = f.equip(interrupted);
        f.kill(loaded, true); reload(h, loaded, 39);
        f.kill(pending, true); containerRoundTrip(h, pending);
        check(h, WeaponAce.rounds(pending) == 0 && WeaponAce.fireflyRemaining(pending) == 120,
                "Accepted same-tick container stow preserves the same owned stack pending kill and Firefly");
        f.kill(interrupted, true); reload(h, interrupted, 39);
        f.at(1, () -> reload(h, pending, 39));
        f.at(28, () -> {
            check(h, ammo(interruptedGun).rounds() == 13 && WeaponRuntime.reloading(interrupted)
                            && WeaponAce.rounds(interrupted) == 0,
                    "Interrupted-generation witness positively received early paid ammo, but not full recovery");
            containerRoundTrip(h, interrupted);
            check(h, WeaponAce.rounds(interrupted) == 0 && WeaponAce.fireflyRemaining(interrupted) == 92,
                    "Container stow retires reload authorization without destroying pending Firefly or paid ammunition");
        });
        f.at(39, () -> {
            check(h, WeaponAce.rounds(loaded) == 6 && !WeaponRuntime.reloading(loaded),
                    "Loaded witness positively earned six through the real full reload path");
            hud(h, loaded, 6);
            check(h, !WeaponRuntime.reloading(interrupted) && ammo(interruptedGun).rounds() == 13
                            && WeaponAce.rounds(interrupted) == 0 && WeaponAce.fireflyRemaining(interrupted) == 81,
                    "Old full recovery deadline cannot grant Mori after a transient container stow invalidated that reload generation");
        });
        f.at(40, () -> {
            check(h, WeaponAce.rounds(pending) == 6 && !WeaponRuntime.reloading(pending)
                            && WeaponAce.fireflyRemaining(pending) == 80,
                    "Pending trigger retained through container stow qualifies only at its own full recovery");
            hud(h, pending, 6);
            containerRoundTrip(h, loaded);
            check(h, WeaponAce.rounds(loaded) == 0 && WeaponAce.fireflyRemaining(loaded) == 80,
                    "Two real container clicks in one tick clear loaded Mori while preserving same-stack Firefly");
            hud(h, loaded, 0);
        });
        f.at(49, () -> {
            var victim = f.primary(loaded, 10, false, HP); shot(h, loaded, false);
            hp(h, victim, HP - profile(loadedGun).damage(),
                    "First paid body hit after same-tick container round trip is base damage, never retained Mori");
            check(h, ammo(loadedGun).rounds() == 12 && WeaponAce.rounds(loaded) == 0
                            && WeaponAce.rounds(interrupted) == 0,
                    "Real post-stow shot pays exactly one bullet; neither stale loaded state nor reload generation revives");
            hud(h, loaded, 0); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 75, environment = "destiny-test:w90_isolated")
    public void canceledReloadAndClonedOrTransferredStackCannotBorrowAnotherOwnersMori(GameTestHelper h) {
        var f = new Fixture(h); var canceled = f.player(8); var source = f.player(24); var recipient = f.player(28);
        var canceledGun = f.equip(canceled); var sourceGun = f.equip(source);
        f.kill(canceled, false); reload(h, canceled, 55); f.kill(source, true); reload(h, source, 39);
        f.at(41, () -> {
            check(h, WeaponRuntime.reloading(canceled) && ammo(canceledGun).rounds() == 13 && WeaponAce.rounds(canceled) == 0,
                    "Cancellation fixture has positively transferred early W65 ammo while full recovery is still pending");
            WeaponRuntime.cancelUseForSkill(canceled);
            check(h, !WeaponRuntime.reloading(canceled) && ammo(canceledGun).rounds() == 13 && WeaponAce.rounds(canceled) == 0,
                    "Cancel after actual ammo credit preserves ammunition but cannot authorize Mori");
        });
        f.at(40, () -> {
            check(h, WeaponAce.rounds(source) == 6 && WeaponAce.fireflyRemaining(source) == 80, "Clone/owner attack starts from positively armed real runtime state");
            var copy = sourceGun.copy(); source.getInventory().setItem(0, copy); WeaponRuntime.tickPlayer(source);
            check(h, WeaponAce.rounds(source) == 0 && WeaponAce.fireflyRemaining(source) == 0,
                    "Identical component/NBT clone is a different stack session and cannot borrow loaded or pending effects");
            recipient.getInventory().setItem(0, sourceGun); recipient.getInventory().setSelectedSlot(0); WeaponRuntime.tickPlayer(recipient);
            check(h, recipient.getMainHandItem() == sourceGun && WeaponAce.rounds(recipient) == 0 && WeaponAce.fireflyRemaining(recipient) == 0
                            && ammo(sourceGun).rounds() == 13 && ammo(copy).rounds() == 13,
                    "Ownership transfer preserves actual ammunition but grants no foreign stack-session effects");
            hud(h, source, 0); hud(h, recipient, 0);
        });
        f.at(56, () -> { check(h, ammo(canceledGun).rounds() == 13 && WeaponAce.rounds(canceled) == 0
                        && !WeaponRuntime.reloading(canceled), "Old full recovery deadline cannot revive a canceled reload or grant Mori from early ammunition credit"); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void deathAndLevelChangeRetireLoadedAndPendingOwnerSessions(GameTestHelper h) {
        var f = new Fixture(h); var dying = f.player(8); var traveler = f.player(24);
        var pendingDeath = f.player(16); var pendingLevel = f.player(28);
        f.equip(pendingDeath); f.equip(pendingLevel);
        f.equip(dying); f.equip(traveler); f.kill(dying, true); f.kill(traveler, true); reload(h, dying, 39); reload(h, traveler, 39);
        var other = h.getLevel().getServer().getLevel(h.getLevel().dimension().equals(Level.NETHER) ? Level.OVERWORLD : Level.NETHER);
        check(h, other != null && other != h.getLevel(), "Lifecycle fixture has a real distinct server level");
        f.at(40, () -> {
            check(h, WeaponAce.rounds(dying) == 6 && WeaponAce.rounds(traveler) == 6
                            && WeaponAce.fireflyRemaining(dying) == 80 && WeaponAce.fireflyRemaining(traveler) == 80,
                    "Both invalidation fixtures begin with actual loaded Mori and live Firefly");
            dying.setHealth(0); WeaponRuntime.tickPlayer(dying); dying.setHealth(20); WeaponRuntime.tickPlayer(dying);
            traveler.setServerLevel(other); WeaponRuntime.tickPlayer(traveler); traveler.setServerLevel(h.getLevel()); WeaponRuntime.tickPlayer(traveler);
            check(h, WeaponAce.rounds(dying) == 0 && WeaponAce.fireflyRemaining(dying) == 0
                            && WeaponAce.rounds(traveler) == 0 && WeaponAce.fireflyRemaining(traveler) == 0,
                    "Death and real level identity change clear both loaded and pending session memory after return");
            hud(h, dying, 0); hud(h, traveler, 0);
            // Fresh real kills at40 keep the later full recovery at95 inside their original 72-tick window.
            // Thus a zero result proves lifecycle invalidation, not ordinary kill-trigger expiry.
            f.kill(pendingDeath, true); f.kill(pendingLevel, true);
            check(h, WeaponAce.fireflyRemaining(pendingDeath) == 120 && WeaponAce.fireflyRemaining(pendingLevel) == 120
                            && ammo(pendingDeath.getMainHandItem()).rounds() == 12 && ammo(pendingLevel.getMainHandItem()).rounds() == 12,
                    "Pending lifecycle witnesses positively earned real precision final blows without reloading");
            pendingDeath.setHealth(0); WeaponRuntime.tickPlayer(pendingDeath); pendingDeath.setHealth(20); WeaponRuntime.tickPlayer(pendingDeath);
            pendingLevel.setServerLevel(other); WeaponRuntime.tickPlayer(pendingLevel); pendingLevel.setServerLevel(h.getLevel()); WeaponRuntime.tickPlayer(pendingLevel);
            check(h, WeaponAce.fireflyRemaining(pendingDeath) == 0 && WeaponAce.fireflyRemaining(pendingLevel) == 0,
                    "Death and level change also retire the fresh unconsumed kill and Firefly session");
            reload(h, pendingDeath, 55); reload(h, pendingLevel, 55);
        });
        f.at(95, () -> {
            for (var p : List.of(pendingDeath, pendingLevel)) {
                check(h, !WeaponRuntime.reloading(p) && ammo(p.getMainHandItem()).rounds() == 13 && WeaponAce.rounds(p) == 0,
                        "Paid full recovery 55 ticks after a real kill cannot revive a retired owner-session trigger");
                hud(h, p, 0);
            }
            h.succeed();
        });
    }

    /** W87 controlled earlier-hostile admission: not a claim that Gate2 contained this mob. */
    @GameTest(structure=FLOOR,maxTicks=80, environment = "destiny-test:w90_isolated")
    public void w87PaidMoriFullRaySelectsNearerHostileAndDoesNotInventFarDamage(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player(16);var gun=f.equip(p);f.kill(p,false);reload(h,p,55);
        f.at(65,()->{
            var far=f.primary(p,29,false,HP);var nearer=f.primary(p,10,false,HP);
            check(h,WeaponAce.rounds(p)==6,"Controlled witness starts from actual kill/full reload");
            shot(h,p,false,nearer);
            hp(h,nearer,HP-profile(gun).damage()*1.68f,"Real paid Mori hits the nearest eligible body");
            hp(h,far,HP,"Far body remains untouched because production selected the nearer hostile");
            check(h,WeaponAce.rounds(p)==5,"Exactly one real Mori bullet consumed, never retry until far damage");h.succeed();
        });
    }
    /** W87 four independent clear corridors, without forcing chunks or widening hit margins. */
    @GameTest(structure=FLOOR,maxTicks=80, environment = "destiny-test:w90_isolated")
    public void w87FourPaidFarCorridorsUseNormalizedProductionTraceAndOriginalFalloff(GameTestHelper h) {
        var f=new Fixture(h);var players=new ArrayList<ServerPlayer>();
        for(double z:new double[]{6,12,20,26}) {var p=f.player(z);players.add(p);f.equip(p);f.kill(p,false);reload(h,p,55);}
        f.at(65,()->{
            for(var p:players) {
                var gun=p.getMainHandItem();var victim=f.primary(p,29,false,HP);var from=p.getEyePosition();
                double distance=from.distanceTo(victim.getBoundingBox().inflate(.03).clip(from,from.add(40,0,0)).orElseThrow());
                double start=(16+.09*85)*.85,end=(29+.03*85)*.85;
                check(h,distance>start&&distance<end&&WeaponAce.rounds(p)==6,"Independent clear corridor remains inside original Mori falloff segment with actual6rounds");
                double falloff=1-(1-.33)*(distance-start)/(end-start);
                shot(h,p,false,victim);hp(h,victim,HP-profile(gun).damage()*1.68f*(float)falloff,"Original paid far body formula at each independent native corridor");
                check(h,WeaponAce.rounds(p)==5,"Each own source pays one round with no retries");victim.discard();
            }
            h.succeed();
        });
    }
}
