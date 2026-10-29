package kim.biryeong.destiny.test;

import com.mojang.math.Transformation;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.WeaponDamageNumbers;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.TextColor;
import net.minecraft.network.protocol.BundlePacket;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundAddEntityPacket;
import net.minecraft.network.protocol.game.ClientboundRemoveEntitiesPacket;
import net.minecraft.network.protocol.game.ClientboundSetEntityDataPacket;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;
import org.joml.Vector3fc;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/** W81 paid input/real END_SERVER_TICK regressions in the existing 48x12x32 fixture.
 * Packet scenes reconstruct distinct native TextDisplays with assignValues, never world entities.
 * Methods prefixed directConfirm are separately scoped cosmetic API tests, not paid-hit evidence.
 * No reflected holders/clocks, manual runtime progression, new assets or inherited-test changes.
 */
public final class DamageFeedbackW81GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final float HP = 1000;
    private static final double EPS = .00025;
    // Conservative native font envelope: 10 vertical pixels, 1/40 plane scale, display scale .65.
    private static final double BODY_GAP = 10d / 40 * .65 + .035;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static void near(GameTestHelper h, double actual, double expected, String message) {
        check(h, Math.abs(actual - expected) < EPS, message + ": expected=" + expected + ", actual=" + actual);
    }

    private static void bounded(GameTestHelper h, Entity entity) {
        var origin = h.absoluteVec(Vec3.ZERO);
        var b = entity.getBoundingBox();
        check(h, b.minX > origin.x && b.maxX < origin.x + 48
                        && b.minY > origin.y && b.maxY < origin.y + 12
                        && b.minZ > origin.z && b.maxZ < origin.z + 32,
                "Whole W81 entity AABB remains strictly inside 48x12x32: " + entity.getUUID());
    }

    private static void deck(GameTestHelper h) {
        for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
    }

    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(3, 4, z), -90, 0,
                "W81_" + UUID.randomUUID().toString().substring(0, 8));
        TestCleanup.register(h, () -> {
            p.setServerLevel(h.getLevel());
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            if (p.level().players().contains(p)) p.level().removePlayerImmediately(p, Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(p);
        });
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setOnGround(true);
        bounded(h, p);
        h.onEachTick(() -> bounded(h, p));
        return p;
    }

    private static WeaponProfile profile(ItemStack gun) {
        return WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());
    }

    private static WeaponMagazine ammo(ItemStack gun) {
        return WeaponItems.magazine(gun, profile(gun));
    }

    private static ItemStack equip(GameTestHelper h, ServerPlayer p, String id, boolean payload) {
        var entry = WeaponCatalog.find(id).orElseThrow();
        var gun = WeaponItems.create(entry);
        gun.set(DataComponents.CUSTOM_NAME, Component.literal("W81_" + UUID.randomUUID()));
        var f = profile(gun);
        check(h, f.mode() == WeaponProfile.Mode.HITSCAN && f.chargeTicks() == 0 && f.burst() == 1 && f.pellets() == 1,
                "One immediate hitscan round per emission: " + id);
        WeaponItems.save(gun, new WeaponMagazine(f, f.magazine() - 1, f.infiniteReserve() ? 0 : 3));
        check(h, WeaponPerks.selected(gun, "explosive_payload").isEmpty(), "New stack has no implicit Payload selection");
        if (payload) check(h, WeaponPerks.select(gun, "explosive_payload"), "Select official Explosive Payload roll");
        int slot = WeaponCharacteristics.of(entry).slot().hotbar();
        p.getInventory().setItem(slot, gun);
        p.getInventory().setSelectedSlot(slot);
        WeaponAccuracy.setAirborneBonus(gun, 100);
        WeaponRuntime.tickPlayer(p); // One initial bind only; subsequent progression belongs to the real server.
        TestPlayers.drain(p);
        return gun;
    }

    private static Husk target(GameTestHelper h, ServerPlayer p, boolean precision) {
        var t = h.spawn(EntityTypes.HUSK, new Vec3(10, precision ? 4 : 4.8, h.relativeVec(p.position()).z));
        TestCleanup.register(h, t::discard);
        t.setNoAi(true);
        t.setNoGravity(true);
        t.setPersistenceRequired();
        t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP);
        t.getAttribute(Attributes.ARMOR).setBaseValue(0);
        t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        t.setHealth(HP);
        bounded(h, t);
        h.onEachTick(() -> bounded(h, t));
        var from = p.getEyePosition();
        var point = t.getBoundingBox().clip(from, from.add(20, 0, 0)).orElseThrow();
        check(h, Combat.isEnemy(p, t) && WeaponPrecision.critical(t, from, point,
                        WeaponAiming.ballistics(p, WeaponItems.entry(p.getMainHandItem()).orElseThrow()).precision()) == precision,
                "Native horizontal ray reaches a legal hostile in the requested body/head region");
        check(h, from.distanceTo(point) < WeaponAiming.ballistics(p, WeaponItems.entry(p.getMainHandItem()).orElseThrow()).start(),
                "Fixture is before damage falloff");
        return t;
    }

    private static void aim(ServerPlayer p) {
        p.setYRot(-90);
        p.setYHeadRot(-90);
        p.setXRot(0);
    }

    private static void paidShot(GameTestHelper h, ServerPlayer p) {
        aim(p);
        var gun = p.getMainHandItem();
        var before = ammo(gun);
        check(h, WeaponRuntime.beginUse(p), "Paid production beginUse accepted");
        WeaponRuntime.releaseUse(p, gun);
        check(h, ammo(gun).rounds() == before.rounds() - 1 && ammo(gun).reserve() == before.reserve(),
                "Paid shot spends exactly one loaded round and preserves reserve");
    }

    private static void flatten(Packet<?> packet, List<Packet<?>> out) {
        if (packet instanceof BundlePacket<?> bundle) for (var child : bundle.subPackets()) flatten(child, out);
        else out.add(packet);
    }

    private static List<Packet<?>> packets(ServerPlayer p) {
        var out = new ArrayList<Packet<?>>();
        for (var packet : TestPlayers.outbound(p)) flatten(packet, out);
        return out;
    }

    /** Discover native metadata descriptors via public setTransformation, with no numeric ID guesses.
     * Rendering state is client-tick-only; server-side TextDisplay.renderState() is not a metadata getter.
     */
    private static EntityDataAccessor<Vector3fc> vectorAccessor(Display.TextDisplay probe, Vector3fc marker) {
        return probe.getEntityData().getNonDefaultValues().stream()
                .filter(v -> v.serializer() == EntityDataSerializers.VECTOR3 && v.value() instanceof Vector3fc value
                        && value.x() == marker.x() && value.y() == marker.y() && value.z() == marker.z())
                .map(v -> new EntityDataAccessor<Vector3fc>(v.id(), EntityDataSerializers.VECTOR3)).findFirst().orElseThrow();
    }

    private static final class Scene {
        final ServerPlayer owner;
        final EntityDataAccessor<Vector3fc> translation, scale;
        final LinkedHashMap<Integer, Display.TextDisplay> spawned = new LinkedHashMap<>();
        final Set<Integer> removed = new LinkedHashSet<>();

        Scene(ServerPlayer owner) {
            this.owner = owner;
            var probe = new Display.TextDisplay(EntityTypes.TEXT_DISPLAY, owner.level());
            var t = new Vector3f(1.25f, 2.5f, 3.75f);
            var s = new Vector3f(4, 5, 6);
            probe.setTransformation(new Transformation(t, null, s, null));
            translation = vectorAccessor(probe, t);
            scale = vectorAccessor(probe, s);
        }

        void read() {
            for (var packet : packets(owner)) {
                if (packet instanceof ClientboundAddEntityPacket add && add.getType() == EntityTypes.TEXT_DISPLAY) {
                    var display = new Display.TextDisplay(EntityTypes.TEXT_DISPLAY, owner.level());
                    display.setPos(add.getX(), add.getY(), add.getZ());
                    if (spawned.putIfAbsent(add.getId(), display) != null) throw new AssertionError("Reused private display ID " + add.getId());
                } else if (packet instanceof ClientboundSetEntityDataPacket data) {
                    var display = spawned.get(data.id());
                    if (display != null) display.getEntityData().assignValues(data.packedItems());
                } else if (packet instanceof ClientboundRemoveEntitiesPacket remove) {
                    remove.entityIds().intStream().filter(spawned::containsKey).forEach(id -> removed.add(id));
                }
            }
        }

        List<Display.TextDisplay> live() {
            return spawned.entrySet().stream().filter(e -> !removed.contains(e.getKey())).map(e -> e.getValue()).toList();
        }

        Vector3fc translation(Display.TextDisplay d) { return d.getEntityData().get(translation); }
        Vector3fc scale(Display.TextDisplay d) { return d.getEntityData().get(scale); }
        String diagnostic() { return "spawned=" + spawned.keySet() + "; removed=" + removed + "; texts=" + live().stream().map(Display.TextDisplay::getText).toList(); }
    }

    private static double distanceScale(ServerPlayer p, Display.TextDisplay d) {
        return Math.clamp(p.getEyePosition().distanceTo(d.position()), 4, 96) / 7;
    }

    private static void number(GameTestHelper h, Display.TextDisplay d, float damage, boolean precision) {
        check(h, d.getText().getString().equals(Integer.toString(Math.max(1, Math.round(damage))))
                        && (precision ? TextColor.YELLOW : TextColor.WHITE).equals(d.getText().getStyle().getColor()),
                "Native owner metadata preserves rounding and precision color: " + d.getText());
    }

    private static void appearance(GameTestHelper h, Scene scene, Display.TextDisplay d, boolean precision) {
        double ds = distanceScale(scene.owner, d);
        var t = scene.translation(d);
        var s = scene.scale(d);
        near(h, t.x(), (precision ? .18 : -.18) * ds, "Existing screen-local X offset");
        near(h, t.z(), 0, "No depth translation");
        for (double component : new double[]{s.x(), s.y(), s.z()}) near(h, component, .65 * ds, "Existing uniform distance scale");
        check(h, d.getBillboardConstraints() == Display.BillboardConstraints.CENTER && d.getBackgroundColor() == 0
                        && (d.getFlags() & Display.TextDisplay.FLAG_SHADOW) != 0
                        && (d.getFlags() & (Display.TextDisplay.FLAG_SEE_THROUGH | Display.TextDisplay.FLAG_USE_DEFAULT_BACKGROUND)) == 0,
                "Native centered billboard, transparent background, shadow and occlusion policy remain");
    }

    private static void pairGap(GameTestHelper h, Scene scene) {
        check(h, scene.live().size() == 2, "Two distinct live text-display IDs; " + scene.diagnostic());
        var first = scene.live().getFirst();
        var second = scene.live().getLast();
        double gap = Math.abs(scene.translation(second).y() - scene.translation(first).y());
        check(h, gap + EPS >= BODY_GAP * Math.min(distanceScale(scene.owner, first), distanceScale(scene.owner, second)),
                "Equal white strings have DIFFERENT Y and full font-height plus padding gap; actual=" + gap);
    }

    private static void selected(GameTestHelper h, boolean precision) {
        deck(h);
        var p = player(h, 16);
        var gun = equip(h, p, "distant_relation", true);
        var t = target(h, p, precision);
        var scene = new Scene(p);
        float impact = (float)(profile(gun).damage() * ((precision ? WeaponBallistics.of(WeaponItems.entry(gun).orElseThrow()).precision() : 1) - .5));
        float explosion = profile(gun).damage() * .65f;
        paidShot(h, p);
        near(h, t.getHealth(), HP - impact - explosion, "Exact paid impact plus explosion HP");
        scene.read();
        check(h, scene.live().size() == 2 && WeaponDamageNumbers.active(p) == 2, "One paid EP shot retains both transactions; " + scene.diagnostic());
        var first = scene.live().getFirst();
        var second = scene.live().getLast();
        number(h, first, impact, precision);
        number(h, second, explosion, false);
        check(h, first.getText().getString().equals(precision ? "5" : "3") && second.getText().getString().equals("3"),
                "Pinned paid EP regression is yellow5/white3 or white3/white3");
        appearance(h, scene, first, precision);
        appearance(h, scene, second, false);
        near(h, scene.translation(first).y(), .12 * distanceScale(p, first), "First number needs no lift");
        if (precision) near(h, scene.translation(second).y(), .12 * distanceScale(p, second), "Separated crit/body columns need no unnecessary lift");
        else pairGap(h, scene);
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void paidSelectedPayloadEqualWhiteThreeAndThreeHaveDistinctReadableY(GameTestHelper h) { selected(h, false); }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void paidSelectedPayloadYellowFiveAndWhiteThreeKeepUnliftedBaseGeometry(GameTestHelper h) { selected(h, true); }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void paidUnselectedBodyKeepsOneWhiteNumberOriginalHpAndNoLift(GameTestHelper h) {
        deck(h);
        var p = player(h, 16);
        var gun = equip(h, p, "distant_relation", false);
        var t = target(h, p, false);
        var scene = new Scene(p);
        paidShot(h, p);
        near(h, t.getHealth(), HP - profile(gun).damage(), "Unselected body HP");
        scene.read();
        check(h, scene.live().size() == 1 && WeaponDamageNumbers.active(p) == 1, "Unselected shot has exactly one display");
        var d = scene.live().getFirst();
        number(h, d, profile(gun).damage(), false);
        appearance(h, scene, d, false);
        near(h, scene.translation(d).y(), .12 * distanceScale(p, d), "Collision-free number retains original Y");
        h.succeed();
    }

    private static void noPrivatePackets(GameTestHelper h, ServerPlayer bystander, Set<Integer> ids) {
        for (var packet : packets(bystander)) {
            check(h, !(packet instanceof ClientboundAddEntityPacket add && ids.contains(add.getId()))
                            && !(packet instanceof ClientboundSetEntityDataPacket data && ids.contains(data.id()))
                            && !(packet instanceof ClientboundRemoveEntitiesPacket remove && remove.entityIds().intStream().anyMatch(ids::contains)),
                    "Nearby world-registered bystander receives no private spawn/metadata/removal packets");
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void paidPayloadSpawnAnimationAndExpiryPacketsExcludeNearbyBystander(GameTestHelper h) {
        deck(h);
        var p = player(h, 16);
        var bystander = player(h, 18);
        h.getLevel().addNewPlayer(bystander);
        equip(h, p, "distant_relation", true);
        target(h, p, false);
        TestPlayers.drain(bystander);
        var scene = new Scene(p);
        paidShot(h, p);
        scene.read();
        check(h, scene.spawned.size() == 2, "Positive owner packet witness");
        var ids = Set.copyOf(scene.spawned.keySet());
        noPrivatePackets(h, bystander, ids);
        h.runAfterDelay(5, () -> {
            scene.read();
            check(h, scene.live().size() == 2, "Owner retains animated pair");
            noPrivatePackets(h, bystander, ids);
        });
        h.runAfterDelay(17, () -> {
            scene.read();
            check(h, scene.removed.equals(ids), "Owner actually receives both lifetime removals");
            noPrivatePackets(h, bystander, ids);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void paidPayloadExpiresAtRealEndTickSixteenWithoutActiveQueryPruning(GameTestHelper h) {
        deck(h);
        var p = player(h, 16);
        var gun = equip(h, p, "distant_relation", true);
        var t = target(h, p, false);
        var scene = new Scene(p);
        paidShot(h, p);
        int start = p.level().getServer().getTickCount();
        int remaining = ammo(gun).rounds();
        float health = t.getHealth();
        scene.read();
        pairGap(h, scene);
        var ids = Set.copyOf(scene.spawned.keySet());
        double originalY = scene.translation(scene.live().getFirst()).y();
        h.runAfterDelay(5, () -> {
            scene.read();
            check(h, scene.translation(scene.live().getFirst()).y() > originalY, "Real END ticks produce rise metadata");
            pairGap(h, scene);
        });
        // GameTest callbacks run before this server tick's END listener. Check age 15 rather
        // than pre-END age 16: another parallel test may legitimately prune at age 16.
        // Do not call active(), confirm() or cleanup() before observing removal packets.
        h.runAfterDelay(15, () -> {
            check(h, p.level().getServer().getTickCount() - start == 15, "Fifteen real server ticks elapsed");
            scene.read();
            check(h, scene.removed.isEmpty() && scene.live().size() == 2, "Pair remains alive at age fifteen");
        });
        h.runAfterDelay(17, () -> {
            scene.read();
            check(h, scene.removed.equals(ids) && scene.live().isEmpty(), "END tick sixteen sent removal of both exact IDs");
            check(h, WeaponDamageNumbers.active(p) == 0 && ammo(gun).rounds() == remaining && t.getHealth() == health,
                    "Expiry leaves no feedback and changes neither ammunition nor target HP");
            h.succeed();
        });
    }

    /** Independently project packet transformations into the horizontal fixture's font plane.
     * We read actual packet translation/scale, not DamageNumberLayout's output under test.
     */
    private static void readableRapid(GameTestHelper h, Scene scene) {
        var eye = scene.owner.getEyePosition();
        var live = scene.live();
        for (int i = 0; i < live.size(); i++) for (int j = i + 1; j < live.size(); j++) {
            var a = live.get(i);
            var b = live.get(j);
            double da = a.getX() - eye.x, db = b.getX() - eye.x;
            check(h, da > 0 && db > 0, "All rapid feedback lies in front of the horizontal owner");
            double sa = scene.scale(a).y(), sb = scene.scale(b).y();
            // Native font center includes its +4px vertical offset; envelope is 10px tall.
            double ya = (a.getY() - eye.y + scene.translation(a).y() + 4d / 40 * sa) / da;
            double yb = (b.getY() - eye.y + scene.translation(b).y() + 4d / 40 * sb) / db;
            double required = 5d / 40 * (sa / da + sb / db)
                    + .035 * Math.min(distanceScale(scene.owner, a) / da, distanceScale(scene.owner, b) / db);
            check(h, Math.abs(ya - yb) + EPS / 7 >= required,
                    "Rapid live pair keeps distinct readable native transforms: pair=" + i + "," + j + "; " + scene.diagnostic());
        }
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

    private static void rapid(GameTestHelper h, boolean precision) {
        deck(h);
        var p = player(h, 16);
        var gun = equip(h, p, "the_recluse", false);
        var f = profile(gun);
        check(h, f.automatic() && Math.abs(f.cadenceTicks() - 4d / 3) < 1e-6, "Pinned 900 RPM automatic fixture");
        var t = target(h, p, precision);
        int initial = ammo(gun).rounds(), reserve = ammo(gun).reserve();
        float perHit = (float)(f.damage() * (precision ? WeaponBallistics.of(WeaponItems.entry(gun).orElseThrow()).precision() : 1));
        var scene = new Scene(p);
        // Model the player's aim correction, not weapon progression; real END ticks fire the held lease.
        h.onEachTick(() -> aim(p));
        aim(p);
        exactAim(h, java.util.List.of(p), () -> {
            check(h, WeaponRuntime.beginUse(p), "Real paid automatic trigger starts");
            check(h, WeaponRuntime.heartbeatUse(p), "Native held-use heartbeat grants its bounded lease");
            scene.read();
            check(h, ammo(gun).rounds() == initial - 1, "Trigger spends exactly one initial round");
            for (int delay = 1; delay <= 9; delay++) {
                int age = delay;
                h.runAfterDelay(delay, () -> {
                    aim(p);
                    if (age == 4) check(h, WeaponRuntime.heartbeatUse(p), "Real native four-tick heartbeat renews held input");
                    scene.read();
                    int spent = initial - ammo(gun).rounds();
                    near(h, t.getHealth(), HP - spent * perHit, "Every loaded round causes exactly one real body/critical HP transaction");
                    check(h, ammo(gun).reserve() == reserve && scene.live().size() == spent, "Ammo and distinct spawned IDs agree each server tick");
                    for (var display : scene.live()) { number(h, display, perHit, precision); appearance(h, scene, display, precision); }
                    readableRapid(h, scene);
                });
            }
            h.runAfterDelay(10, () -> {
                WeaponRuntime.releaseUse(p, gun);
                // The last four-tick heartbeat was at age 4. Its real six-tick native lease
                // ends now, so release cannot leave an authorized lease that starts another shot.
                scene.read();
                check(h, initial - ammo(gun).rounds() == 7 && scene.live().size() == 7 && WeaponDamageNumbers.active(p) == 7,
                        "Real ticks at ages 0,2,3,4,6,7,8 retain seven paid hits");
                near(h, t.getHealth(), HP - 7 * perHit, "Exact seven-hit HP");
                readableRapid(h, scene);
            });
            h.runAfterDelay(12, () -> {
                scene.read();
                check(h, ammo(gun).rounds() == initial - 7 && ammo(gun).reserve() == reserve && scene.live().size() == 7,
                        "Released input produces no latent extra round or coalesced feedback");
                near(h, t.getHealth(), HP - 7 * perHit, "Post-release HP stays exact");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void paidRapidAutomaticBodyHitsRetainDistinctReadableTransformsAndExactHpAmmo(GameTestHelper h) { rapid(h, false); }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void paidRapidAutomaticCriticalHitsRetainYellowTransformsAndExactHpAmmo(GameTestHelper h) { rapid(h, true); }

    @GameTest(structure = FLOOR, maxTicks = 15, environment = "destiny-test:w90_isolated")
    public void directConfirmImmutableLiftRisesWithoutRepackingExistingDisplays(GameTestHelper h) {
        deck(h);
        var p = player(h, 16);
        var scene = new Scene(p);
        var point = p.getEyePosition().add(7, 0, 0);
        WeaponDamageNumbers.confirm(p, h.getLevel(), point, 3, false);
        WeaponDamageNumbers.confirm(p, h.getLevel(), point, 3, false);
        scene.read();
        pairGap(h, scene);
        var first = scene.live().getFirst();
        var lifted = scene.live().getLast();
        double initialY = scene.translation(first).y();
        double liftGap = scene.translation(lifted).y() - initialY;
        h.runAfterDelay(5, () -> {
            scene.read();
            check(h, scene.translation(first).y() > initialY, "Existing holder rises on actual END ticks");
            near(h, scene.translation(lifted).y() - scene.translation(first).y(), liftGap, "Chosen lift remains immutable across animation");
            double before = scene.translation(lifted).y();
            WeaponDamageNumbers.confirm(p, h.getLevel(), point, 3, false);
            scene.read();
            check(h, scene.live().size() == 3, "Third cosmetic confirmation retains three distinct IDs");
            near(h, scene.translation(lifted).y(), before, "New confirmation never moves an existing lifted number");
            readableRapid(h, scene);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void directConfirmOwnerCapRetainsNewestTwentyFourAndOtherOwnersIds(GameTestHelper h) {
        deck(h);
        var p = player(h, 16);
        var other = player(h, 22);
        var scene = new Scene(p);
        var otherScene = new Scene(other);
        WeaponDamageNumbers.confirm(other, h.getLevel(), other.getEyePosition().add(7, 0, 0), 7, true);
        otherScene.read();
        for (int i = 0; i < 27; i++) WeaponDamageNumbers.confirm(p, h.getLevel(), p.getEyePosition().add(7, 0, 0), 3, false);
        scene.read();
        var ids = new ArrayList<>(scene.spawned.keySet());
        check(h, ids.size() == 27 && scene.live().size() == 24 && WeaponDamageNumbers.active(p) == 24,
                "27 confirmations spawn 27 distinct IDs and retain exactly 24");
        check(h, scene.removed.equals(new LinkedHashSet<>(ids.subList(0, 3))), "Only oldest three IDs receive FIFO eviction packets");
        check(h, scene.spawned.keySet().stream().filter(id -> !scene.removed.contains(id)).toList().equals(ids.subList(3, 27)),
                "Newest 24 distinct IDs remain in order");
        otherScene.read();
        check(h, otherScene.live().size() == 1 && otherScene.removed.isEmpty() && WeaponDamageNumbers.active(other) == 1,
                "Owner overflow leaves unrelated owner feedback intact");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void directConfirmExpiredReservationDoesNotLiftNextNumberOrAnotherOwner(GameTestHelper h) {
        deck(h);
        var p = player(h, 16);
        var other = player(h, 16);
        var scene = new Scene(p);
        var otherScene = new Scene(other);
        var point = p.getEyePosition().add(7, 0, 0);
        WeaponDamageNumbers.confirm(p, h.getLevel(), point, 3, false);
        WeaponDamageNumbers.confirm(p, h.getLevel(), point, 3, false);
        WeaponDamageNumbers.confirm(other, h.getLevel(), point, 3, false);
        scene.read();
        otherScene.read();
        pairGap(h, scene);
        check(h, otherScene.live().size() == 1, "Second owner has its own independent display");
        near(h, otherScene.translation(otherScene.live().getFirst()).y(), .12, "Other owner's same-anchor number needs no lift");
        h.runAfterDelay(17, () -> {
            scene.read();
            check(h, scene.live().isEmpty() && scene.removed.size() == 2, "Real expiry releases prior owner reservations");
            WeaponDamageNumbers.confirm(p, h.getLevel(), point, 3, false);
            scene.read();
            check(h, scene.live().size() == 1, "New cosmetic confirmation has one live fresh ID");
            near(h, scene.translation(scene.live().getFirst()).y(), .12, "Expired boxes leave no stale lift reservation");
            h.succeed();
        });
    }
    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void directConfirmNearClampedNumberCannotCatchLaterFarNumberBeforeRealExpiry(GameTestHelper h) {
        deck(h);
        var p=player(h,16);
        var scene=new Scene(p);
        WeaponDamageNumbers.confirm(p,h.getLevel(),p.getEyePosition().add(2,0,0),3,false);
        scene.read();
        check(h,scene.live().size()==1,"Near cosmetic confirmation spawns one private ID");
        int first=scene.spawned.keySet().iterator().next();
        h.runAfterDelay(1,()->{
            WeaponDamageNumbers.confirm(p,h.getLevel(),p.getEyePosition().add(7,0,0),3,false);
            scene.read();
            check(h,scene.live().size()==2,"Second range spawns independent feedback");
            readableRapid(h,scene);
        });
        for(int delay=2;delay<=15;delay++)h.runAfterDelay(delay,()->{
            scene.read();check(h,scene.live().size()==2,"Both ranges remain live before older expiry");
            readableRapid(h,scene);
        });
        h.runAfterDelay(18,()->{
            scene.read();check(h,scene.removed.size()==2&&scene.removed.contains(first)&&scene.live().isEmpty(),"Both mixed-range IDs expire after their real lifetimes");
            h.succeed();
        });
    }

}
