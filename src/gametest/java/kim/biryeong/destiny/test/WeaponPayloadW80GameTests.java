package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.WeaponDamageNumbers;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.TextColor;
import net.minecraft.network.protocol.BundlePacket;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundSetEntityDataPacket;
import net.minecraft.network.protocol.game.ClientboundAddEntityPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Set;
import java.util.UUID;

/** W80 uses paid production input inside the existing 48x12x32 W78 structure.
 * Explicit raised deck, whole-AABB bounds, unique names and per-owner cleanup.
 * No reflected runtime state, altered clocks, manual projectile progression or foreign arenas.
 * Sourced fractions: half body damage converted, explosion 1.30 PvE multiplier and 3m radius.
 * Nearest-AABB distance, LOS, radial max(.25,1-d/3) and targeting exclusions are local policy.
 */
public final class WeaponPayloadW80GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final String ID = "explosive_payload";
    private static final long HASH = 3038247973L;
    private static final float HP = 1000, EPS = .004f;
    private static final Set<WeaponPerks.Roll> EXPECTED = Set.of(
            new WeaponPerks.Roll("distant_relation", 2034817450L, 4, HASH, 3824767299L),
            new WeaponPerks.Roll("patron_of_lost_causes", 2723241847L, 4, HASH, 120674550L),
            new WeaponPerks.Roll("long_arm", 8293111L, 4, HASH, 619833418L),
            new WeaponPerks.Roll("bite_of_the_fox", 1403800851L, 4, HASH, 2442672691L),
            new WeaponPerks.Roll("apostate", 2164448701L, 4, HASH, 2826016044L));

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static void hp(GameTestHelper h, LivingEntity target, float expected, String message) {
        check(h, Math.abs(target.getHealth() - expected) < EPS,
                message + ": expected HP " + expected + ", got " + target.getHealth());
    }

    private static void bounded(GameTestHelper h, Entity entity) {
        var origin = h.absoluteVec(Vec3.ZERO);
        var b = entity.getBoundingBox();
        check(h, b.minX > origin.x && b.maxX < origin.x + 48
                        && b.minY > origin.y && b.maxY < origin.y + 12
                        && b.minZ > origin.z && b.maxZ < origin.z + 32,
                "Whole W80 entity AABB stays strictly inside its 48x12x32 fixture: " + entity.getUUID());
    }

    private static void deck(GameTestHelper h) {
        for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++)
            h.setBlock(x, 3, z, Blocks.STONE);
    }

    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(3, 4, z), -90, 0,
                "W80_" + UUID.randomUUID().toString().substring(0, 8));
        TestCleanup.register(h, () -> {
            p.setServerLevel(h.getLevel());
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            if (p.level().players().contains(p))
                p.level().removePlayerImmediately(p, Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(p);
        });
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setOnGround(true);
        bounded(h, p);
        h.onEachTick(() -> bounded(h, p));
        return p;
    }

    private static WeaponProfile profile(ItemStack stack) {
        return WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow());
    }

    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, profile(stack));
    }

    private static ItemStack stack(String id) {
        var gun = WeaponItems.create(WeaponCatalog.find(id).orElseThrow());
        gun.set(DataComponents.CUSTOM_NAME, Component.literal("W80_" + UUID.randomUUID()));
        var f = profile(gun);
        WeaponItems.save(gun, new WeaponMagazine(f, f.magazine() - 1, f.infiniteReserve() ? 0 : 3));
        return gun;
    }

    private static ItemStack equip(GameTestHelper h, ServerPlayer p, String id, boolean selected) {
        var gun = stack(id);
        var entry = WeaponItems.entry(gun).orElseThrow();
        var f = profile(gun);
        check(h, f.mode() == WeaponProfile.Mode.HITSCAN && f.chargeTicks() == 0
                        && f.burst() == 1 && f.pellets() == 1,
                "Fixture is exactly one immediate hitscan round: " + id);
        var before = ammo(gun);
        check(h, WeaponPerks.selected(gun, ID).isEmpty(), "New stack never implicitly selects Payload");
        if (selected) check(h, WeaponPerks.select(gun, ID), "Explicit selection from official pool");
        check(h, WeaponPerks.selected(gun, ID).isPresent() == selected
                        && ammo(gun).rounds() == before.rounds() && ammo(gun).reserve() == before.reserve(),
                "Selection status is explicit and preserves ammunition");
        int slot = WeaponCharacteristics.of(entry).slot().hotbar();
        p.getInventory().setItem(slot, gun);
        p.getInventory().setSelectedSlot(slot);
        kim.biryeong.destiny.weapon.WeaponAccuracy.setAirborneBonus(gun, 100);
        WeaponRuntime.tickPlayer(p);
        TestPlayers.drain(p);
        return gun;
    }

    private static Husk target(GameTestHelper h, double x, double y, double z, float health) {
        var target = h.spawn(EntityTypes.HUSK, new Vec3(x, y, z));
        TestCleanup.register(h, target::discard);
        target.setNoAi(true);
        target.setNoGravity(true);
        target.setPersistenceRequired();
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP);
        target.getAttribute(Attributes.ARMOR).setBaseValue(0);
        target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        target.setHealth(health);
        bounded(h, target);
        h.onEachTick(() -> bounded(h, target));
        return target;
    }

    private static Husk primary(GameTestHelper h, ServerPlayer p, double z, boolean precision, float health) {
        var target = target(h, 10, precision ? 4 : 4.8, z, health);
        var from = p.getEyePosition();
        var box = target.getBoundingBox();
        var point = box.clip(from, from.add(20, 0, 0)).orElseThrow();
        check(h, precision ? from.y >= box.maxY - box.getYsize() * .25 && from.y < box.maxY
                        : from.y > box.minY && from.y < box.maxY - box.getYsize() * .25,
                "Real horizontal ray intersects requested head/body region");
        check(h, WeaponPrecision.critical(target, from, point,
                        WeaponAiming.ballistics(p, WeaponItems.entry(p.getMainHandItem()).orElseThrow()).precision()) == precision,
                "Production precision classifier agrees with geometric preflight");
        check(h, Combat.isEnemy(p, target) && !p.isAlliedTo(target), "Primary is a legal hostile target");
        return target;
    }

    /** W241 exact-impact fixture: earn ADS on real ticks, with explicit per-stack AE.
     * No RNG replacement, production tuning change, or synthetic server clock. */
    private static void exactAim(GameTestHelper h, java.util.List<ServerPlayer> owners, Runnable action) {
        for (var p : owners) {
            var gun = p.getMainHandItem();
            check(h, kim.biryeong.destiny.weapon.WeaponAccuracy.airborne(WeaponItems.entry(gun).orElseThrow(), gun) == 100, "Fixture explicitly equips AE100");
            WeaponRuntime.tickPlayer(p);
            if (!WeaponAiming.requested(p)) check(h, WeaponAiming.toggle(p), "Real ADS toggle accepted");
        }
        // GameTestInfo executes sequences after iterating its fastutil callback map.
        // The final action may register follow-up deadlines, so it must run here.
        var sequence = h.startSequence();
        for (int tick = 1; tick <= 40; tick++) {
            final int age = tick;
            sequence.thenExecuteAfter(1, () -> {
                for (var p : owners) {
                    WeaponRuntime.tickPlayer(p);
                    // Initial handling can consume ADS. A later actual click earns it after ready.
                    if (!WeaponAiming.requested(p) && age % 4 == 0) WeaponAiming.toggle(p);
                }
                if (age == 40) {
                    for (var p : owners) check(h, WeaponAiming.progress(p) == 1
                                    && WeaponAiming.coneDegrees(p) == 0,
                            "Fully earned ADS and AE100 give an exact ray before any paid shot");
                    action.run();
                }
            });
        }
    }

    private static void shot(GameTestHelper h, ServerPlayer p) {
        shot(h, p, 0);
    }

    private static void shot(GameTestHelper h, ServerPlayer p, float pitch) {
        p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(pitch);
        WeaponAiming.tick(p);
        var gun = p.getMainHandItem();
        int rounds = ammo(gun).rounds(), reserve = ammo(gun).reserve();
        check(h, WeaponRuntime.beginUse(p), "Real production beginUse accepts this paid shot");
        WeaponRuntime.releaseUse(p, gun);
        check(h, ammo(gun).rounds() == rounds - 1 && ammo(gun).reserve() == reserve,
                "One accepted shot spends one loaded round and no reserve");
    }

    private static CompoundTag withoutTraits(ItemStack gun) {
        var tag = gun.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.remove(WeaponPerks.HASH_KEY);
        tag.remove(WeaponPerks.SOCKET_KEY);
        tag.remove(WeaponPerks.SLOTS_KEY);
        return tag;
    }

    private static Vec3 origin(ServerPlayer p, LivingEntity primary) {
        // Independent native ray/box entry preflight, with the public .03 hitscan margin.
        return primary.getBoundingBox().inflate(.03f).clip(p.getEyePosition(), p.getEyePosition().add(p.getLookAngle().normalize().scale(30))).orElseThrow();
    }

    private static double nearestDistance(Vec3 origin, LivingEntity target) {
        var b = target.getBoundingBox();
        double x = Math.max(b.minX, Math.min(b.maxX, origin.x));
        double y = Math.max(b.minY, Math.min(b.maxY, origin.y));
        double z = Math.max(b.minZ, Math.min(b.maxZ, origin.z));
        return origin.distanceTo(new Vec3(x, y, z));
    }

    private static float splash(ItemStack gun, Vec3 origin, LivingEntity target) {
        double d = nearestDistance(origin, target);
        return d > 3 ? 0 : (float) (profile(gun).damage() * .65 * Math.max(.25, 1 - d / 3));
    }

    private static void blasted(GameTestHelper h, ItemStack gun, Vec3 origin, LivingEntity target) {
        float expected = splash(gun, origin, target);
        check(h, expected > 0, "Positive witness has an actual AABB point within 3 blocks");
        hp(h, target, HP - expected, "Observed splash uses independent .65B and local nearest-AABB radial curve");
    }

    private static void flatten(Packet<?> packet, List<Packet<?>> result) {
        if (packet instanceof BundlePacket<?> bundle) for (var child : bundle.subPackets()) flatten(child, result);
        else result.add(packet);
    }

    private record Feedback(List<Component> numbers, String diagnostic) {}

    private static Feedback feedback(ServerPlayer p) {
        var packets = new ArrayList<Packet<?>>();
        for (var packet : TestPlayers.outbound(p)) flatten(packet, packets);
        var displays = new LinkedHashMap<Integer, Display.TextDisplay>();
        var diagnostics = new StringBuilder("active=").append(WeaponDamageNumbers.active(p)).append("; packets=");
        var classes = new LinkedHashMap<String, Integer>();
        for (var packet : packets) classes.merge(packet.getClass().getSimpleName(), 1, Integer::sum);
        diagnostics.append(classes);
        for (var packet : packets) {
            if (packet instanceof ClientboundAddEntityPacket spawn && spawn.getType() == EntityTypes.TEXT_DISPLAY) {
                // Reconstruct client metadata only; this display is never added to the world.
                var display = new Display.TextDisplay(EntityTypes.TEXT_DISPLAY, p.level());
                display.setPos(p.getEyePosition());
                displays.put(spawn.getId(), display);
            } else if (packet instanceof ClientboundSetEntityDataPacket data) {
                diagnostics.append("; data[").append(data.id()).append("]=");
                for (var value : data.packedItems()) diagnostics.append(value.id()).append(':')
                        .append(value.value().getClass().getName()).append('=').append(value.value()).append(',');
                var display = displays.get(data.id());
                if (display != null) display.getEntityData().assignValues(data.packedItems());
            }
        }
        var text = displays.values().stream().map(Display.TextDisplay::getText).toList();
        diagnostics.append("; distinctTextDisplayIds=").append(displays.keySet()).append("; text=").append(text);
        return new Feedback(text, diagnostics.toString());
    }

    private static void number(GameTestHelper h, Component number, float damage, boolean precision) {
        check(h, number.getString().equals(Integer.toString(Math.max(1, Math.round(damage))))
                        && (precision ? TextColor.YELLOW : TextColor.WHITE).equals(number.getStyle().getColor()),
                "Actual owner packet shows rounded observed HP and expected precision color: " + number);
    }

    private static void selectedDamage(GameTestHelper h, boolean precision) {
        deck(h);
        var owners = new java.util.ArrayList<ServerPlayer>();
        var shots = new java.util.ArrayList<Runnable>();
        int lane = 0;
        for (String id : List.of("distant_relation", "patron_of_lost_causes", "long_arm", "bite_of_the_fox", "apostate")) {
            double z = 4 + 6 * lane++;
            var p = player(h, z); var gun = equip(h, p, id, true);
            var primary = primary(h, p, z, precision, HP);
            var entry = WeaponItems.entry(gun).orElseThrow();
            var ballistics = WeaponAiming.ballistics(p, entry);
            check(h, origin(p, primary).distanceTo(p.getEyePosition()) < ballistics.start(),
                    "All selected fixture impacts are inside original damage falloff start");
            float impact = (float) (profile(gun).damage() * ((precision ? ballistics.precision() : 1) - .5));
            float explosion = profile(gun).damage() * .65f;
            TestPlayers.drain(p);
            owners.add(p);
            shots.add(() -> {
                shot(h, p);
                hp(h, primary, HP - impact - explosion, "Paid " + id + " splits impact then full explosion exactly once");
                var feedback = feedback(p);
                check(h, WeaponDamageNumbers.active(p) == 2,
                        "Real paid damage has exactly two active owner displays: " + id + "; " + feedback.diagnostic());
                check(h, feedback.numbers().size() == 2,
                        "Real paid damage spawns two distinct owner text-display IDs: " + id + "; " + feedback.diagnostic());
                number(h, feedback.numbers().get(0), impact, precision);
                number(h, feedback.numbers().get(1), explosion, false);
            });
        }
        exactAim(h, owners, () -> { shots.forEach(Runnable::run); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void paidSelectedBodyDamageSplitsIntoPhysicalAndWhiteExplosionForEveryEligibleWeapon(GameTestHelper h) {
        selectedDamage(h, false);
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void paidSelectedPrecisionPreservesUnconvertedCritBonusAndWhiteExplosionForEveryEligibleWeapon(GameTestHelper h) {
        selectedDamage(h, true);
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void paidBodyContactSplashesNearestBoxesWithLinearInteriorQuarterFloorAndSphericalRadius(GameTestHelper h) {
        deck(h); var p = player(h, 16); var gun = equip(h, p, "distant_relation", true);
        var primary = primary(h, p, 16, false, HP); var origin = origin(p, primary);
        var near = target(h, 10, 4, 17.2, HP);
        var middle = target(h, 10, 4, 18, HP);
        var floor = target(h, 10, 4, 18.9, HP);
        var inside = target(h, 10, 4, 19.29, HP);
        var outside = target(h, 10, 4, 19.31, HP);
        var above = target(h, 10, 8.5, 16, HP);
        var diagonal = target(h, 10, 7.6, 18.8, HP);
        check(h, nearestDistance(origin, inside) < 3 && origin.distanceTo(inside.getBoundingBox().getCenter()) > 3,
                "Inside witness distinguishes nearest box from center-distance selection");
        check(h, nearestDistance(origin, outside) > 3 && nearestDistance(origin, diagonal) > 3,
                "Outside and diagonal witnesses distinguish sphere from broad-phase cube");
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p);
            for (var target : List.of(near, middle, floor, inside, above)) blasted(h, gun, origin, target);
            check(h, near.getHealth() < middle.getHealth() && middle.getHealth() < floor.getHealth(),
                    "Actual HP separates linear interior and local floor");
            hp(h, floor, HP - profile(gun).damage() * .1625f, "Quarter splash floor applies only to .65B explosion");
            hp(h, outside, HP, "Nearest point outside 3m is safe");
            hp(h, diagonal, HP, "Diagonal outside spherical radius is safe");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void exactThreeMetreTangentIsAdmittedButNextRepresentableWorldCoordinateOutsideIsRejected(GameTestHelper h) {
        deck(h); var p = player(h, 16); var gun = equip(h, p, "distant_relation", true);
        var primary = primary(h, p, 16, false, HP); var origin = origin(p, primary);
        var tangent = target(h, 10, 4, 19.3, HP);
        var outside = target(h, 10, 4, 19.3, HP);
        double face = origin.z + 3;
        tangent.setPos(origin.x, tangent.getY(), face + tangent.getBbWidth() / 2d);
        outside.setPos(origin.x, outside.getY(), Math.nextUp(face) + outside.getBbWidth() / 2d);
        bounded(h, tangent); bounded(h, outside);
        check(h, tangent.getBoundingBox().minZ == face && nearestDistance(origin, tangent) == 3,
                "Actual native entity AABB is exactly tangent to the sourced radius");
        check(h, outside.getBoundingBox().minZ == Math.nextUp(face) && nearestDistance(origin, outside) > 3,
                "Outside box face is the next representable world coordinate; no tolerance widens the radius");
        check(h, !AABB.ofSize(origin, 6, 6, 6).intersects(tangent.getBoundingBox()),
                "Exact tangent exercises the native strict broadphase boundary");
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p);
            hp(h, tangent, HP - profile(gun).damage() * .1625f, "Inclusive 3m tangent receives local quarter-floor splash");
            hp(h, outside, HP, "Next representable world coordinate outside radius receives zero damage");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void immunePrimaryStillResolvesBodyContactAndNearbySplash(GameTestHelper h) {
        deck(h); var p = player(h, 16); var gun = equip(h, p, "distant_relation", true);
        var primary = primary(h, p, 16, false, HP); primary.setPermanentlyInvulnerable(true);
        var witness = target(h, 10, 4, 17.5, HP); var origin = origin(p, primary);
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p);
            hp(h, primary, HP, "Actual primary protection rejects both transactions");
            blasted(h, gun, origin, witness);
            var feedback = feedback(p);
            check(h, WeaponDamageNumbers.active(p) == 1 && feedback.numbers().size() == 1,
                    "Only confirmed nearby damage creates one active/distinct display; primary rejected: " + feedback.diagnostic());
            number(h, feedback.numbers().getFirst(), splash(gun, origin, witness), false);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void paidBlockContactSplashesExposedEnemyAcrossGapButSolidWallProtectsBehind(GameTestHelper h) {
        deck(h); var p = player(h, 16); var gun = equip(h, p, "distant_relation", true);
        for (int y = 4; y <= 8; y++) for (int z = 14; z <= 18; z++) h.setBlock(10, y, z, Blocks.STONE);
        for (int x = 7; x <= 9; x++) for (int z = 17; z <= 18; z++) h.setBlock(x, 3, z, Blocks.AIR);
        var exposed = target(h, 8.5, 4, 18.5, HP);
        var hidden = target(h, 11.5, 4, 16, HP);
        var hit = h.getLevel().clip(new ClipContext(p.getEyePosition(), p.getEyePosition().add(p.getLookAngle().normalize().scale(30)),
                ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
        check(h, hit.getType() == HitResult.Type.BLOCK, "Real horizontal ray first hits the fixture wall");
        var origin = hit.getLocation().add(-1d / 64, 0, 0);
        check(h, nearestDistance(origin, exposed) < 3 && nearestDistance(origin, hidden) < 3
                        && h.getLevel().noCollision(hidden, hidden.getBoundingBox()),
                "Both enemies are in radius and hidden enemy does not overlap suffocating blocks");
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p);
            blasted(h, gun, origin, exposed);
            hp(h, hidden, HP, "A real solid wall blocks splash behind the resolved impact face");
            check(h, h.getBlockState(new BlockPos(10, 5, 16)).is(Blocks.STONE) && h.getBlockState(new BlockPos(8, 3, 17)).isAir(),
                    "Payload preserves the solid wall and does not fill the fixture gap");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void solidSideWallStopsEntityContactSplashWhileOpenSideIsDamaged(GameTestHelper h) {
        deck(h); var p = player(h, 16); var gun = equip(h, p, "distant_relation", true);
        var primary = primary(h, p, 16, false, HP); var origin = origin(p, primary);
        var hidden = target(h, 10, 4, 18.5, HP); var open = target(h, 10, 4, 13.5, HP);
        for (int x = 8; x <= 11; x++) for (int y = 4; y <= 8; y++) h.setBlock(x, y, 17, Blocks.STONE);
        check(h, nearestDistance(origin, hidden) < 3 && h.getLevel().noCollision(hidden, hidden.getBoundingBox()),
                "Protected in-range enemy stays clear of wall collision");
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p);
            hp(h, hidden, HP, "Body-contact explosion cannot damage through side wall");
            blasted(h, gun, origin, open);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void nearerOccludedCrowdCannotExhaustCapBeforeFartherExposedEnemy(GameTestHelper h) {
        deck(h); var p = player(h, 16); var gun = equip(h, p, "distant_relation", true);
        var primary = primary(h, p, 16, false, HP); var origin = origin(p, primary);
        for (int x = 8; x <= 11; x++) for (int y = 4; y <= 8; y++) h.setBlock(x, y, 17, Blocks.STONE);
        var exposed = target(h, 10, 4, 13.2, HP);
        exactAim(h, java.util.List.of(p), () -> {
            // Spawn after ADS preparation: 130 overlapping bodies must not spend 40
            // native ticks taking cramming damage before the payload under test.
            var hidden = new ArrayList<Husk>();
            for (int i = 0; i < 130; i++) {
                var mob = target(h, 10, 4, 18.5, HP); hidden.add(mob);
                check(h, nearestDistance(origin, mob) < nearestDistance(origin, exposed),
                        "Every occluded crowd member sorts before exposed witness by actual box distance");
                hp(h, mob, HP, "Occluded candidate enters the paid shot at full health");
                check(h, h.getLevel().noCollision(mob, mob.getBoundingBox()),
                        "Occluded candidate body does not intersect the wall");
            }
            shot(h, p);
            for (var mob : hidden) hp(h, mob, HP, "Occluded candidate neither takes damage nor consumes admission cap");
            blasted(h, gun, origin, exposed);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void onePaidRoundHitsEachSecondaryOnceWithoutRecursiveExplosionOrDelayedRepeat(GameTestHelper h) {
        deck(h); var p = player(h, 16); var gun = equip(h, p, "distant_relation", true);
        var primary = primary(h, p, 16, false, HP); var origin = origin(p, primary);
        var secondary = target(h, 10, 4, 18.5, .5f);
        var outside = target(h, 10, 4, 20.5, HP);
        var other = target(h, 10, 4, 14.5, HP);
        check(h, splash(gun, origin, secondary) > secondary.getHealth() && splash(gun, origin, outside) == 0
                        && nearestDistance(secondary.getBoundingBox().getCenter(), outside) < 3,
                "Secondary dies in first explosion; outside enemy lies only within hypothetical recursive explosion"
                        + "; splash=" + splash(gun, origin, secondary) + "; secondaryHP=" + secondary.getHealth()
                        + "; outsideDistance=" + nearestDistance(origin, outside));
        int rounds = ammo(gun).rounds(), reserve = ammo(gun).reserve();
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p);
            check(h, secondary.isDeadOrDying(), "Real first explosion kills secondary");
            blasted(h, gun, origin, other); hp(h, outside, HP, "Secondary final blow never recursively explodes");
            var paid = gun.copy(); float once = other.getHealth();
            check(h, !WeaponRuntime.beginUse(p), "Same-tick duplicate input is rejected by real cadence");
            WeaponRuntime.releaseUse(p, gun);
            h.onEachTick(() -> { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); });
            h.runAfterDelay(3, () -> {
                hp(h, other, once, "No second target damage repeats on later server ticks");
                hp(h, outside, HP, "No delayed recursive blast");
                check(h, ammo(gun).rounds() == rounds - 1 && ammo(gun).reserve() == reserve && ItemStack.matches(paid, gun),
                        "Several victims and denied input cost exactly one round with no extra item mutation");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void explosionFinalBlowAfterPrecisionImpactCannotProcOutlawOrReplacedDragonfly(GameTestHelper h) {
        deck(h); var p = player(h, 16); var gun = equip(h, p, "distant_relation", true);
        check(h, WeaponPerks.select(gun, "outlaw") && WeaponPerks.select(gun, "dragonfly")
                        && WeaponPerks.select(gun, ID) && WeaponPerks.selected(gun, "outlaw").isPresent()
                        && WeaponPerks.selected(gun, "dragonfly").isEmpty(),
                "Legal Outlaw3/Payload4 coexist; explicit Payload4 replaces Dragonfly4");
        var ballistics = WeaponAiming.ballistics(p, WeaponItems.entry(gun).orElseThrow());
        float impact = (float) (profile(gun).damage() * (ballistics.precision() - .5));
        var primary = primary(h, p, 16, true, impact + 1);
        var outside = target(h, 10, 4, 20, HP);
        check(h, splash(gun, origin(p, primary), outside) == 0
                        && primary.getBoundingBox().getCenter().distanceTo(outside.getBoundingBox().getCenter()) < 4.5,
                "Outside witness is safe from Payload but would expose an erroneous Dragonfly explosion");
        var control = player(h, 6); var controlGun = equip(h, control, "distant_relation", false);
        check(h, WeaponPerks.select(controlGun, "outlaw"), "Control legally selects Outlaw3");
        var corpse = primary(h, control, 6, true, 1);
        exactAim(h, java.util.List.of(p, control), () -> {
            shot(h, p);
            check(h, primary.isDeadOrDying() && WeaponOutlaw.remaining(p) == 0,
                    "Precision impact survives; actual nonprecision explosion final blow earns no Outlaw");
            hp(h, outside, HP, "Explosion final blow produces no Dragonfly chain");
            shot(h, control);
            check(h, corpse.isDeadOrDying() && WeaponOutlaw.remaining(control) > 0,
                    "Independent paid precision final blow positively exercises Outlaw");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void explosionOnlyDamageCannotCreditPrecisionRefundWhilePhysicalPrecisionCreditsExactlyOnce(GameTestHelper h) {
        deck(h);
        var owners = new java.util.ArrayList<ServerPlayer>();
        var shots = new java.util.ArrayList<Runnable>();
        for (boolean immune : new boolean[]{false, true}) {
            double z = immune ? 22 : 8;
            var p = player(h, z); var gun = equip(h, p, "distant_relation", true);
            check(h, WeaponPerks.select(gun, "triple_tap"), "Legal Triple Tap3/Payload4 coexist");
            var primary = primary(h, p, z, true, HP); primary.setPermanentlyInvulnerable(immune);
            var witness = target(h, 10, 4, z + 1.5, HP); var origin = origin(p, primary);
            owners.add(p);
            shots.add(() -> {
                shot(h, p); blasted(h, gun, origin, witness);
                check(h, WeaponPrecisionReturn.progress(p, "triple_tap") == (immune ? 0 : 1),
                        "Only confirmed physical precision, never nearby explosion damage, credits one refund hit");
                if (immune) hp(h, primary, HP, "Protected precision primary takes no fabricated HP loss");
            });
        }
        exactAim(h, owners, () -> { shots.forEach(Runnable::run); h.succeed(); });
    }

    @GameTest(structure = FLOOR, environment = "destiny-test:w90_allied_isolated", maxTicks = 55)
    public void bodyExplosionSparesShooterWorldPresentPlayerAlliedHostileAndUnownedTame(GameTestHelper h) {
        deck(h); var p = player(h, 16); p.setPos(h.absoluteVec(new Vec3(8, 4, 16)));
        var gun = equip(h, p, "distant_relation", true);
        var primary = primary(h, p, 16, false, HP); var origin = origin(p, primary);
        var ally = target(h, 10, 4, 18, HP); var enemy = target(h, 10, 4, 14, HP);
        var tame = h.spawn(EntityTypes.WOLF, new Vec3(11.5, 4, 16));
        TestCleanup.register(h, tame::discard);
        tame.setNoAi(true); tame.setNoGravity(true); tame.setTame(true, false);
        tame.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP); tame.setHealth(HP); bounded(h, tame);
        var victim = player(h, 17.5); victim.setPos(h.absoluteVec(new Vec3(11.5, 4, 17.5)));
        h.getLevel().addNewPlayer(victim);
        var scoreboard = h.getLevel().getScoreboard();
        String name = "w80_" + UUID.randomUUID().toString().substring(0, 8);
        var team = scoreboard.addPlayerTeam(name);
        TestCleanup.register(h, () -> { if (scoreboard.getPlayerTeam(name) == team) scoreboard.removePlayerTeam(team); });
        scoreboard.addPlayerToTeam(p.getScoreboardName(), team);
        scoreboard.addPlayerToTeam(ally.getScoreboardName(), team);
        check(h, p.isAlliedTo(ally) && !Combat.isEnemy(p, ally) && tame.isTame()
                        && !Combat.isEnemy(p, tame) && !p.isAlliedTo(tame) && !p.isAlliedTo(victim),
                "Excluded hostile, independently tame mob and unallied player exercise distinct targeting rules");
        for (var entity : List.of(p, ally, tame, victim)) check(h, nearestDistance(origin, entity) < 3,
                "Excluded candidate really lies within local splash radius");
        check(h, h.getLevel().getEntitiesOfClass(LivingEntity.class, AABB.ofSize(origin, 6, 6, 6)).contains(victim),
                "Player is a native world-indexed query candidate");
        float ownerHp = p.getHealth(), victimHp = victim.getHealth();
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); blasted(h, gun, origin, enemy);
            hp(h, p, ownerHp, "Shooter takes no self-damage"); hp(h, victim, victimHp, "World-present survival player is spared");
            hp(h, ally, HP, "Scoreboard-allied hostile is spared"); hp(h, tame, HP, "Unowned tame is independently spared");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, skyAccess = true, environment = "destiny-test:w90_isolated")
    public void paidUpwardMissDoesNotExplodeOntoNearbyEnemy(GameTestHelper h) {
        deck(h); var p = player(h, 16); p.setPos(h.absoluteVec(new Vec3(3, 8, 16)));
        var gun = equip(h, p, "distant_relation", true); var witness = target(h, 4.5, 8, 16, HP);
        // Native skyAccess omits only this fixture's enclosure roof. Materialize its local corridor.
        for (int y = 9; y < 12; y++) h.setBlock(3, y, 16, Blocks.AIR);
        var from = p.getEyePosition(); var to = from.add(0, 96, 0);
        var preflight = h.getLevel().clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
        boolean loaded = true;
        for (int step = 0; step <= 96; step++) loaded &= h.getLevel().hasChunkAt(BlockPos.containing(from.add(0, step, 0)));
        check(h, preflight.getType() == HitResult.Type.MISS && loaded,
                "Full loaded 96-block vertical trace is a native MISS; every actor stays inside own fixture"
                        + "; type=" + preflight.getType() + "; local=" + preflight.getLocation().subtract(h.absoluteVec(Vec3.ZERO))
                        + "; block=" + preflight.getBlockPos() + "; state=" + h.getLevel().getBlockState(preflight.getBlockPos())
                        + "; face=" + preflight.getDirection() + "; eyeLocal=" + from.subtract(h.absoluteVec(Vec3.ZERO)));
        check(h, h.getLevel().getEntitiesOfClass(LivingEntity.class, new AABB(from, to).inflate(.23),
                        e -> Combat.isEnemy(p, e)).isEmpty(), "No hostile AABB intercepts the paid upward ray");
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p, -90);
            hp(h, witness, HP, "Nearby enemy receives no explosion from a real paid miss");
            var feedback = feedback(p);
            check(h, WeaponDamageNumbers.active(p) == 0 && feedback.numbers().isEmpty(),
                    "Miss produces no confirmed damage feedback: " + feedback.diagnostic());
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void exactFiveOfficialSelectionsAreExplicitReadOnlyAndPreserveAmmo(GameTestHelper h) {
        WeaponModelGameTests.assertCatalogExpansion(h);
        check(h, WeaponCatalog.all().size() == 65, "Original63 catalog plus Ace and Izanagi");
        int accepted = 0;
        for (var entry : WeaponCatalog.all()) {
            var gun = stack(entry.id());
            var expected = EXPECTED.stream().filter(r -> r.id().equals(entry.id())).toList();
            var saved = gun.copy();
            var nonTraits = withoutTraits(gun);
            var initial = ammo(gun);
            check(h, WeaponPerks.available(gun, ID).equals(expected)
                            && WeaponPerks.selected(gun, ID).isEmpty() && ItemStack.matches(saved, gun),
                    "Exact official availability and pure reads: " + entry.id());
            boolean selected = WeaponPerks.select(gun, ID);
            check(h, selected == !expected.isEmpty(), "No family/name-wide grant: " + entry.id());
            if (!selected) check(h, ItemStack.matches(saved, gun), "Rejected selection preserves entire stack");
            else {
                accepted++;
                check(h, WeaponPerks.selected(gun, ID).orElseThrow().equals(expected.getFirst())
                                && nonTraits.equals(withoutTraits(gun))
                                && ammo(gun).rounds() == initial.rounds() && ammo(gun).reserve() == initial.reserve(),
                        "Exact socket selection preserves identity, unrelated NBT and ammo");
                var selectedCopy = gun.copy();
                check(h, WeaponPerks.select(gun, ID) && ItemStack.matches(selectedCopy, gun),
                        "Repeated selection is serialized-state idempotent");
            }
        }
        check(h, accepted == 5, "Exactly five base Payload weapons accepted");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void distantRelationPayloadReplacesDragonflyButPreservesCompatibleHolsterAndAmmo(GameTestHelper h) {
        for (boolean reverse : new boolean[]{false, true}) {
            var gun = stack("distant_relation");
            var before = ammo(gun);
            var nonTraits = withoutTraits(gun);
            check(h, WeaponPerks.select(gun, reverse ? ID : WeaponPerks.ID)
                            && WeaponPerks.select(gun, reverse ? WeaponPerks.ID : ID),
                    "Both edit orders support Holster3 and Payload4");
            check(h, WeaponPerks.selected(gun, ID).orElseThrow().socket() == 4
                            && WeaponPerks.selected(gun, WeaponPerks.ID).orElseThrow().socket() == 3,
                    "Compatible traits occupy distinct official sockets");
            check(h, WeaponPerks.select(gun, "dragonfly") && WeaponPerks.selected(gun, ID).isEmpty()
                            && WeaponPerks.selected(gun, "dragonfly").orElseThrow().socket() == 4
                            && WeaponPerks.selected(gun, WeaponPerks.ID).isPresent(),
                    "Dragonfly4 replaces Payload4 and retains Holster3");
            check(h, WeaponPerks.select(gun, ID) && WeaponPerks.selected(gun, "dragonfly").isEmpty()
                            && WeaponPerks.selected(gun, WeaponPerks.ID).isPresent()
                            && nonTraits.equals(withoutTraits(gun))
                            && ammo(gun).rounds() == before.rounds() && ammo(gun).reserve() == before.reserve(),
                    "Payload4 replaces Dragonfly4 without changing compatible selection or ammunition");
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void strictModernAndLegacyTraitNbtRejectsWrongSocketsHashesAndNumericTypesWithoutMutation(GameTestHelper h) {
        for (String malformed : List.of("socket3", "enhanced", "timed", "enhanced_timed", "int_hash", "double_hash",
                "string_hash", "string_container", "legacy_float_socket", "legacy_int_hash", "legacy_string_socket",
                "modern_overrides_legacy")) {
            var gun = stack("distant_relation");
            var tag = withoutTraits(gun);
            var slots = new CompoundTag();
            slots.putLong("4", HASH);
            switch (malformed) {
                case "socket3" -> { slots.remove("4"); slots.putLong("3", HASH); }
                case "enhanced" -> slots.putLong("4", 64866129L);
                case "timed" -> slots.putLong("4", 1954620775L);
                case "enhanced_timed" -> slots.putLong("4", 1562897767L);
                case "int_hash" -> slots.putInt("4", (int) HASH);
                case "double_hash" -> slots.putDouble("4", HASH);
                case "string_hash" -> slots.putString("4", Long.toString(HASH));
                case "modern_overrides_legacy" -> {
                    slots.putLong("4", 64866129L);
                    tag.putInt(WeaponPerks.SOCKET_KEY, 4); tag.putLong(WeaponPerks.HASH_KEY, HASH);
                }
                default -> { }
            }
            if (malformed.startsWith("legacy_")) {
                tag.putInt(WeaponPerks.SOCKET_KEY, 4); tag.putLong(WeaponPerks.HASH_KEY, HASH);
                if (malformed.equals("legacy_float_socket")) tag.putFloat(WeaponPerks.SOCKET_KEY, 4);
                if (malformed.equals("legacy_int_hash")) tag.putInt(WeaponPerks.HASH_KEY, (int) HASH);
                if (malformed.equals("legacy_string_socket")) tag.putString(WeaponPerks.SOCKET_KEY, "4");
            } else if (malformed.equals("string_container")) tag.putString(WeaponPerks.SLOTS_KEY, "4:" + HASH);
            else tag.put(WeaponPerks.SLOTS_KEY, slots);
            gun.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
            var before = gun.copy();
            check(h, WeaponPerks.selected(gun, ID).isEmpty() && ItemStack.matches(before, gun),
                    "Malformed Payload selection is inert and read-only: " + malformed);
        }
        for (boolean legacy : new boolean[]{false, true}) {
            var gun = stack("distant_relation");
            var tag = withoutTraits(gun);
            if (legacy) { tag.putInt(WeaponPerks.SOCKET_KEY, 4); tag.putLong(WeaponPerks.HASH_KEY, HASH); }
            else { var slots = new CompoundTag(); slots.putLong("4", HASH); tag.put(WeaponPerks.SLOTS_KEY, slots); }
            gun.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
            var before = gun.copy();
            check(h, WeaponPerks.selected(gun, ID).orElseThrow().equals(EXPECTED.stream()
                            .filter(r -> r.id().equals("distant_relation")).findFirst().orElseThrow())
                            && ItemStack.matches(before, gun),
                    "Exact long hash and integral socket select read-only in supported NBT format");
        }
        for (String ineligible : List.of("frontier_justice", "seventh_seraph_officer_revolver", "whispering_slab")) {
            var gun = stack(ineligible);
            var tag = withoutTraits(gun);
            var slots = new CompoundTag(); slots.putLong("4", HASH);
            tag.put(WeaponPerks.SLOTS_KEY, slots);
            gun.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
            var before = gun.copy();
            check(h, WeaponPerks.selected(gun, ID).isEmpty() && !WeaponPerks.select(gun, ID)
                            && ItemStack.matches(before, gun),
                    "Forged correct hash/socket cannot authorize a different official weapon: " + ineligible);
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void paidUnselectedBodyAndPrecisionHitsOnAllFiveEligibleWeaponsNeverSplash(GameTestHelper h) {
        deck(h);
        var owners = new java.util.ArrayList<ServerPlayer>();
        var shots = new java.util.ArrayList<Runnable>();
        int lane = 0;
        for (String id : List.of("distant_relation", "patron_of_lost_causes", "long_arm", "bite_of_the_fox", "apostate")) {
            double z = 4 + 6 * lane++;
            var p = player(h, z);
            var gun = equip(h, p, id, false);
            boolean precision = lane % 2 == 0;
            var primary = primary(h, p, z, precision, HP);
            var witness = target(h, 10, 4, z + 1.5, HP);
            owners.add(p);
            shots.add(() -> {
                shot(h, p);
                check(h, primary.isAlive() && primary.getHealth() < HP && WeaponPerks.selected(gun, ID).isEmpty(),
                        "Real paid unselected ray causes positive nonlethal HP damage: " + id);
                hp(h, witness, HP, "Eligibility alone never grants splash: " + id);
                check(h, WeaponRuntime.activeProjectiles(p) == 0, "Single hitscan leaves no owned projectile");
            });
        }
        exactAim(h, owners, () -> { shots.forEach(Runnable::run); h.succeed(); });
    }
}
