package kim.biryeong.destiny.test;

import kim.biryeong.destiny.fx.WeaponDamageNumbers;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponReticleHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerInputPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Paid real hits, independent plane-coordinate oracle, committed fixture bounds and natural server ticks.
 * No reflected emit/tokens, injected damage, sacrificial shots or manual runtime/aiming tick calls.
 * Numerical coordinates and retained ADS factor are local tuning, not exact original engine physics. */
public final class ShotgunPatternW105GameTests {
    private static final String FLOOR = "destiny-test:w78_floor", ENV = "destiny-test:w90_isolated";
    private static final Map<String, Double> BUDGETS = Map.of(
            "mindbender_s_ambition_adept", 18.4, "dust_rock_blues", 16.,
            "parcel_of_stardust_fell_to_earth", 15.2, "ikelos_sg_v1_0_1", 13.6);
    private static final Input ADS = new Input(false, false, false, false, false, true, false);
    private record Point(double x, double y) {}
    private record Actor(ServerPlayer player, ItemStack gun) {}
    private record Hits(int body, int precision) {
        int count() { return body + precision; }
        double damage(double budget) { return budget/12*(body + precision*1.107843137254902); }
    }

    // Independent, image-informed local contract; never call production offsets() to choose witnesses.
    private static List<Point> points(String id) {
        return switch (id) {
            case "mindbender_s_ambition_adept" -> xy(0, 0, -.35, .35, .35, .35, .35, -.35, -.35, -.35,
                    0, 1, .78, .62, .97, -.22, .43, -.90, -.43, -.90, -.97, -.22, -.78, .62);
            case "dust_rock_blues" -> xy(-.22, 1, .22, 1, .48, .48, .61, 0, .48, -.48,
                    .22, -1, -.22, -1, -.48, -.48, -.61, 0, -.48, .48, 0, .32, 0, -.32);
            case "parcel_of_stardust_fell_to_earth" -> xy(0, .85, 1, 0, 0, -.85, -1, 0,
                    .49, .49, .49, -.49, -.49, -.49, -.49, .49, 0, .38, .38, 0, 0, -.38, -.38, 0);
            case "ikelos_sg_v1_0_1" -> xy(-.60, .60, 0, .60, .60, .60, .60, 0, .60, -.60,
                    0, -.60, -.60, -.60, -.60, 0, -.32, .32, .32, .32, .32, -.32, -.32, -.32);
            case "first_in_last_out" -> xy(0, 0);
            default -> throw new AssertionError("Not an independent W105 fixture weapon: " + id);
        };
    }

    private static List<Point> xy(double... coordinates) {
        var result = new ArrayList<Point>();
        for (int i = 0; i < coordinates.length; i += 2) result.add(new Point(coordinates[i], coordinates[i+1]));
        return List.copyOf(result);
    }

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static WeaponMagazine ammo(Actor a) {
        return WeaponItems.magazine(a.gun(), WeaponProfile.forEntry(WeaponItems.entry(a.gun()).orElseThrow()));
    }

    private static void close(Actor a) {
        a.player().setShiftKeyDown(false);
        a.player().stopUsingItem();
        WeaponRuntime.cleanup(a.player());
        CombatHud.remove(a.player());
        WeaponReticleHud.remove(a.player());
        TestPlayers.remove(a.player());
    }

    private static final class Fixture {
        final GameTestHelper h;
        final long started;
        final List<Actor> actors = new ArrayList<>();
        final List<Husk> targets = new ArrayList<>();

        Fixture(GameTestHelper h) {
            this.h = h;
            started = h.getLevel().getServer().getTickCount();
            // The committed template is air. A local raised floor and complete backstop contain every ray.
            for (int x = 0; x <= 16; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
            for (int y = 4; y <= 10; y++) for (int z = 0; z < 32; z++) h.setBlock(16, y, z, Blocks.STONE);
            TestCleanup.register(h, () -> {
                for (var a : List.copyOf(actors)) close(a);
                targets.forEach(Entity::discard);
            });
            h.onEachTick(() -> {
                for (var a : actors) { bounded(a.player()); TestPlayers.drain(a.player()); }
                for (var t : targets) if (!t.isRemoved()) bounded(t);
            });
        }

        void bounded(Entity entity) {
            var origin = h.absoluteVec(Vec3.ZERO);
            var b = entity.getBoundingBox();
            check(h, b.minX > origin.x && b.maxX < origin.x+48
                            && b.minY > origin.y+3 && b.maxY < origin.y+12
                            && b.minZ > origin.z && b.maxZ < origin.z+32,
                    "Complete actor/target AABB remains in committed 48x12x32 raised fixture");
        }

        Actor actor(String id, double z, int rounds, int reserve, boolean ads) {
            var p = TestPlayers.create(h, new Vec3(3, 4, z), -90, 0,
                    "W105_"+UUID.randomUUID().toString().substring(0, 8));
            p.setAttached(WeaponLoadout.ENABLED, false);
            p.setNoGravity(true);
            p.setOnGround(true);
            var entry = WeaponCatalog.find(id).orElseThrow();
            var gun = WeaponItems.create(entry);
            WeaponItems.save(gun, new WeaponMagazine(WeaponProfile.forEntry(entry), rounds, reserve));
            p.setItemInHand(InteractionHand.MAIN_HAND, gun);
            var a = new Actor(p, gun);
            actors.add(a);
            if (ads) {
                check(h, WeaponAiming.toggle(p), "Actual left-click ADS toggle accepted");
                // A rejected full-mag reload binds the real state without a shot or a manual clock advance.
                check(h, !WeaponRuntime.reload(p) && !WeaponRuntime.reloading(p), "Full magazine cannot start reload");
            }
            bounded(p);
            return a;
        }

        Actor fresh(String id, double z, boolean ads) {
            return actor(id, z, WeaponProfile.forEntry(WeaponCatalog.find(id).orElseThrow()).magazine(), 0, ads);
        }

        void retire(Actor actor) {
            actors.remove(actor);
            close(actor);
        }

        Husk target(double x, double y, double z, double scale) {
            var t = h.spawn(EntityTypes.HUSK, new Vec3(x, y, z));
            targets.add(t);
            t.setNoAi(true);
            t.setNoGravity(true);
            t.setPersistenceRequired();
            t.getAttribute(Attributes.SCALE).setBaseValue(scale);
            t.refreshDimensions();
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
            t.setHealth(1000);
            bounded(t);
            return t;
        }

        void at(int elapsed, Runnable action) {
            h.runAfterDelay(elapsed, () -> {
                check(h, h.getLevel().getServer().getTickCount()-started == elapsed, "Actual server deadline " + elapsed);
                action.run();
            });
        }

        void paid(Actor actor) {
            var before = ammo(actor);
            actor.player().getRandom().setSeed(DISPERSION_SEED);
            check(h, WeaponRuntime.beginUse(actor.player()), "Production trigger admitted");
            WeaponRuntime.releaseUse(actor.player(), actor.gun());
            var after = ammo(actor);
            check(h, after.rounds() == before.rounds()-1 && after.reserve() == before.reserve()
                            && after.total() == before.total()-1,
                    "One actual trigger consumes exactly one finite magazine unit regardless of pellet count");
        }

        void sample(Husk target, Actor actor, Point point, double spread, boolean hit, String label, Runnable after) {
            sample(target, actor, point, spread, hit, label, 6, after);
        }
        void sample(Husk target, Actor actor, Point point, double spread, boolean hit, String label) {
            sample(target, actor, point, spread, hit, label, 0, () -> {});
        }
        private void sample(Husk target, Actor actor, Point point, double spread, boolean hit, String label, int settleTicks, Runnable after) {
            var eye = actor.player().getEyePosition();
            // W241 rotates the entire authored pellet pattern around one stochastic axis.
            // Predict from a fixed RNG seed, never from observed impacts or production offsets().
            Vec3 ray = ray(sampledAxis(actor), point, spread);
            Vec3 center = eye.add(ray.scale(10 / ray.x));
            target.setPos(center.x, center.y-target.getBbHeight()/2, center.z);
            target.setHealth(1000);
            bounded(target);
            check(h, WeaponDamageNumbers.active(actor.player()) == 0, "Independent owner starts without feedback");
            // Publish the fixture's new stationary position beyond the bounded render-history window.
            // The geometry/ammo/feedback oracles are unchanged; this test is not a moving-target test.
            Runnable verify = () -> {
                paid(actor);
                check(h, (target.getHealth() < 1000) == hit, label + " actual fixed footprint at " + point);
                check(h, WeaponDamageNumbers.active(actor.player()) == (hit ? 1 : 0), label + " confirmed feedback matches actual hit");
                after.run();
            };
            if (settleTicks == 0) verify.run(); else h.runAfterDelay(settleTicks, verify);
        }
    }

    private static final long DISPERSION_SEED = 0x105241L;

    /** Independent disk sampler for the current cone; keep the real nonzero hip spread. */
    private static Vec3 sampledAxis(Actor actor) {
        var p = actor.player();
        p.getRandom().setSeed(DISPERSION_SEED);
        double u = p.getRandom().nextDouble(), v = p.getRandom().nextDouble();
        p.getRandom().setSeed(DISPERSION_SEED); // The paid path receives exactly the same two inputs.
        Vec3 forward = p.getLookAngle().normalize();
        Vec3 right = forward.cross(Vec3.Y_AXIS).normalize(), up = right.cross(forward);
        double radius = Math.sqrt(u) * Math.tan(Math.toRadians(WeaponAiming.coneDegrees(p)));
        double angle = v * 2 * Math.PI;
        return forward.add(right.scale(radius*Math.cos(angle))).add(up.scale(radius*Math.sin(angle))).normalize();
    }

    private static Vec3 ray(Vec3 axis, Point point, double spread) {
        Vec3 right = axis.cross(Vec3.Y_AXIS).normalize(), up = right.cross(axis).normalize();
        return axis.add(right.scale(point.x()*spread)).add(up.scale(point.y()*spread)).normalize();
    }

    private static void footprint(GameTestHelper h, String id, double z) {
        var f = new Fixture(h);
        var target = f.target(13, 5, z, .1);
        var witnesses = new ArrayList<>(points(id));
        int positives = witnesses.size();
        // Empty locations include the obsolete ring/grid and a safe exterior witness.
        witnesses.addAll(xy(1, 0, 0, -1, 1, 1, 1.3, 0));
        // Those first two may be occupied by the diamond/oval: choose empty points independently per frame.
        if (id.equals("parcel_of_stardust_fell_to_earth")) {
            witnesses.set(positives, new Point(0, 1.2));
            witnesses.set(positives+1, new Point(0, -1.2));
        }
        if (id.equals("dust_rock_blues")) witnesses.set(positives+1, new Point(0, 0));
        witnesses.add(points(id).getFirst()); // Repeat a real coordinate with independent paid owners.
        Actor[] aiming = new Actor[1];
        for (int i = 0; i < witnesses.size(); i++) {
            int index = i, time = 1+i*40;
            Point point = witnesses.get(i);
            boolean shouldHit = i < positives || i == witnesses.size()-1;
            f.at(time, () -> {
                var hip = f.fresh(id, z, false);
                f.sample(target, hip, point, .12, shouldHit, id+" hip sample "+index, () -> f.retire(hip));
                aiming[0] = f.fresh(id, z, true);
            });
            f.at(time+30, () -> {
                var ads = aiming[0];
                check(h, WeaponAiming.progress(ads.player()) >= .999f && WeaponAiming.bloom(ads.player()) == 0,
                        "Natural production ticks completed ADS without dummy shots or duplicate ticks");
                f.sample(target, ads, point, .078, shouldHit, id+" ADS sample "+index, () -> {
                    f.retire(ads);
                    if (index == witnesses.size()-1) h.succeed();
                });
            });
        }
    }

    @GameTest(structure=FLOOR, maxTicks=740, environment=ENV)
    public void aggressiveConePaidHipAndAdsFootprintsMatchIndependentWitnesses(GameTestHelper h) {
        footprint(h, "mindbender_s_ambition_adept", 5);
    }

    @GameTest(structure=FLOOR, maxTicks=740, environment=ENV)
    public void precisionOvalPaidHipAndAdsFootprintsMatchIndependentWitnesses(GameTestHelper h) {
        footprint(h, "dust_rock_blues", 12);
    }

    @GameTest(structure=FLOOR, maxTicks=740, environment=ENV)
    public void lightweightDiamondPaidHipAndAdsFootprintsMatchIndependentWitnesses(GameTestHelper h) {
        footprint(h, "parcel_of_stardust_fell_to_earth", 20);
    }

    @GameTest(structure=FLOOR, maxTicks=740, environment=ENV)
    public void rapidSquarePaidHipAndAdsFootprintsMatchIndependentWitnesses(GameTestHelper h) {
        footprint(h, "ikelos_sg_v1_0_1", 27);
    }

    /** Independent ray/AABB oracle from literal offsets, never production pattern/trace/precision helpers. */
    private static Hits[] expected(Actor actor, String id, List<Husk> targets) {
        int[] body = new int[targets.size()], precision = new int[targets.size()];
        Vec3 from = actor.player().getEyePosition();
        for (var point : points(id)) {
            Vec3 end = from.add(ray(sampledAxis(actor), point, .12).scale(12));
            int first = -1;
            double distance = Double.POSITIVE_INFINITY;
            for (int i = 0; i < targets.size(); i++) {
                var hit = targets.get(i).getBoundingBox().inflate(.03).clip(from, end);
                if (hit.isPresent() && from.distanceToSqr(hit.get()) < distance) {
                    first = i;
                    distance = from.distanceToSqr(hit.get());
                }
            }
            if (first >= 0) {
                var box = targets.get(first).getBoundingBox();
                var surface = box.clip(from, end);
                if (surface.isPresent() && surface.get().y >= box.maxY-box.getYsize()*.25) precision[first]++;
                else body[first]++;
            }
        }
        var result = new Hits[targets.size()];
        for (int i = 0; i < result.length; i++) result[i] = new Hits(body[i], precision[i]);
        return result;
    }

    private static void loss(GameTestHelper h, Husk target, double expected, String message) {
        check(h, Math.abs(1000-target.getHealth()-expected) < .005, message+" expected "+expected+" observed "+(1000-target.getHealth()));
    }

    @GameTest(structure=FLOOR, maxTicks=10, environment=ENV)
    public void allTwelveBodyPelletsAggregateOnceAndPreserveEachLegacyLocalBudget(GameTestHelper h) {
        var f = new Fixture(h);
        var target = f.target(5, 4.8, 16, 1);
        for (var entry : BUDGETS.entrySet()) {
            target.setHealth(1000);
            var actor = f.fresh(entry.getKey(), 16, false);
            var hits = expected(actor, entry.getKey(), List.of(target))[0];
            check(h, hits.body() == 12 && hits.precision() == 0, "Independent fixture covers twelve body rays");
            f.paid(actor);
            loss(h, target, entry.getValue(), "Full local body budget "+entry.getKey());
            check(h, WeaponDamageNumbers.active(actor.player()) == 1, "One actual body damage transaction, not twelve calls");
            f.retire(actor);
        }
        h.succeed();
    }

    @GameTest(structure=FLOOR, maxTicks=10, environment=ENV)
    public void twoOrdinaryTargetsReceiveOnlyTheirIndependentPelletSubsets(GameTestHelper h) {
        var f = new Fixture(h);
        var left = f.target(5, 4.8, 15.62, 1);
        var right = f.target(5, 4.8, 16.38, 1);
        check(h, !left.getBoundingBox().inflate(.03).intersects(right.getBoundingBox().inflate(.03)), "Disjoint inflated targets");
        for (var entry : BUDGETS.entrySet()) {
            left.setHealth(1000); right.setHealth(1000);
            var actor = f.fresh(entry.getKey(), 16, false);
            var hits = expected(actor, entry.getKey(), List.of(left, right));
            for (var hit : hits) check(h, hit.body() > 0 && hit.body() < 12 && hit.precision() == 0, "Each target owns a strict body subset");
            check(h, hits[0].count()+hits[1].count() <= 12, "No ray can pay both targets");
            f.paid(actor);
            loss(h, left, hits[0].damage(entry.getValue()), "Left subset "+entry.getKey());
            loss(h, right, hits[1].damage(entry.getValue()), "Right subset "+entry.getKey());
            check(h, 2000-left.getHealth()-right.getHealth() <= entry.getValue()+.005, "Combined loss cannot exceed one body budget");
            check(h, WeaponDamageNumbers.active(actor.player()) == 2, "One observed body transaction per exact target");
            f.retire(actor);
        }
        h.succeed();
    }

    @GameTest(structure=FLOOR, maxTicks=10, environment=ENV)
    public void mixedHeadAndBodyPelletsApplyPrecisionOnlyToTheIndependentHeadSubset(GameTestHelper h) {
        var f = new Fixture(h);
        var target = f.target(5, 4.1, 16, 1);
        for (var entry : BUDGETS.entrySet()) {
            target.setHealth(1000);
            var actor = f.fresh(entry.getKey(), 16, false);
            var hits = expected(actor, entry.getKey(), List.of(target))[0];
            check(h, hits.body() > 0 && hits.precision() > 0 && hits.count() == 12, "Fixture contains body and exact head surfaces");
            f.paid(actor);
            loss(h, target, hits.damage(entry.getValue()), "Precision only on independently intersected head rays");
            check(h, WeaponDamageNumbers.active(actor.player()) == 2, "One actual body and one actual precision feedback category");
            f.retire(actor);
        }
        h.succeed();
    }

    @GameTest(structure=FLOOR, maxTicks=10, environment=ENV)
    public void solidWallBlocksEveryPelletButStillCostsOneRoundAndVisibleControlHits(GameTestHelper h) {
        var f = new Fixture(h);
        var target = f.target(5, 4.8, 16, 1);
        for (int y = 4; y <= 8; y++) for (int z = 14; z <= 18; z++) h.setBlock(4, y, z, Blocks.STONE);
        for (String id : BUDGETS.keySet()) {
            var actor = f.fresh(id, 16, false);
            f.paid(actor);
            loss(h, target, 0, "Wall preserves HP for every pellet frame");
            check(h, WeaponDamageNumbers.active(actor.player()) == 0, "No confirmed damage through wall");
            f.retire(actor);
        }
        for (int y = 4; y <= 8; y++) for (int z = 14; z <= 18; z++) h.setBlock(4, y, z, Blocks.AIR);
        var visible = f.fresh("dust_rock_blues", 16, false);
        f.paid(visible);
        loss(h, target, 16, "Same unobstructed fixture is a real hit control");
        h.succeed();
    }

    @GameTest(structure=FLOOR, maxTicks=10, environment=ENV)
    public void slugHasSingleCenterHitNoFanAndItsOriginalPrecisionMultiplier(GameTestHelper h) {
        var f = new Fixture(h);
        var target = f.target(13, 5, 16, .1);
        var center = f.fresh("first_in_last_out", 16, false);
        f.sample(target, center, new Point(0, 0), 0, true, "Slug center");
        f.retire(center);
        var side = f.fresh("first_in_last_out", 16, false);
        f.sample(target, side, new Point(1, 0), .12, false, "Slug cannot inherit pellet fan");
        f.retire(side);
        target.discard();
        var head = f.target(5, 4, 16, 1);
        var actor = f.fresh("first_in_last_out", 16, false);
        f.paid(actor);
        loss(h, head, 13*1.7549019607843137, "Single slug retains decoded original multiplier");
        check(h, WeaponDamageNumbers.active(actor.player()) == 1, "Only one slug feedback category");
        h.succeed();
    }

    @GameTest(structure=FLOOR, maxTicks=10, environment=ENV)
    public void unrelatedHandCannonAndAutoRiflePaidShotsRetainSingleRayFootprints(GameTestHelper h) {
        var f = new Fixture(h);
        var target = f.target(13, 5, 16, .1);
        for (String id : List.of("austringer", "ammit_ar2")) {
            var center = f.fresh(id, 16, false);
            f.sample(target, center, new Point(0, 0), 0, true, id+" unchanged center ray");
            f.retire(center);
            var side = f.fresh(id, 16, false);
            f.sample(target, side, new Point(.6, .6), .12, false, id+" cannot inherit shotgun pattern");
            f.retire(side);
        }
        h.succeed();
    }

    @GameTest(structure=FLOOR, maxTicks=80, environment=ENV)
    public void immediateRepressCannotBypassRealCadenceOrMultiplyAmmoCost(GameTestHelper h) {
        var f = new Fixture(h);
        var target = f.target(5, 4.8, 16, 1);
        var actor = f.actor("dust_rock_blues", 16, 3, 0, false);
        int deadline = (int)Math.ceil(WeaponProfile.forEntry(WeaponCatalog.find("dust_rock_blues").orElseThrow()).cadenceTicks());
        f.paid(actor);
        loss(h, target, 16, "First real trigger");
        check(h, !WeaponRuntime.beginUse(actor.player()), "Immediate fresh press is denied by cadence");
        check(h, ammo(actor).rounds() == 2, "Denied trigger costs nothing");
        f.at(deadline-1, () -> {
            check(h, !WeaponRuntime.beginUse(actor.player()) && ammo(actor).rounds() == 2, "One tick before real cadence remains denied");
            loss(h, target, 16, "No repeated damage before deadline");
        });
        f.at(deadline+1, () -> {
            f.paid(actor);
            check(h, ammo(actor).rounds() == 1 && ammo(actor).reserve() == 0, "Second admitted shot has one cost");
            loss(h, target, 32, "Exactly two actual full-budget shots after natural recovery");
            h.succeed();
        });
    }

    @GameTest(structure=FLOOR, maxTicks=160, environment=ENV)
    public void realFirstShellInsertMovesFiniteReserveOnceAndFreshShotSpendsThatShell(GameTestHelper h) {
        var f = new Fixture(h);
        var target = f.target(5, 4.8, 16, 1);
        var actor = f.actor("dust_rock_blues", 16, 0, 2, false);
        var profile = WeaponProfile.forEntry(WeaponCatalog.find("dust_rock_blues").orElseThrow());
        check(h, profile.shellReload() && profile.roundsPerInsert() == 1, "Existing shotgun shell policy");
        check(h, WeaponRuntime.reload(actor.player()), "Actual empty finite reload starts");
        f.at(profile.firstReloadTicks()-1, () -> {
            check(h, ammo(actor).rounds() == 0 && ammo(actor).reserve() == 2, "No shell before actual first deadline");
            loss(h, target, 0, "Reload cannot produce latent shots");
        });
        f.at(profile.firstReloadTicks()+1, () -> {
            check(h, ammo(actor).rounds() == 1 && ammo(actor).reserve() == 1 && ammo(actor).total() == 2,
                    "Natural runtime transferred exactly one reserve shell");
            f.paid(actor);
            check(h, ammo(actor).rounds() == 0 && ammo(actor).reserve() == 1 && !WeaponRuntime.reloading(actor.player()),
                    "Fresh admitted input interrupts reload and spends only the inserted shell");
            loss(h, target, 16, "Inserted shell produces one full pellet transaction");
            h.succeed();
        });
    }

    private static ItemDisplayHud node(ServerPlayer player, String id) {
        return (ItemDisplayHud)DisplayHud.getHud(player, id);
    }

    private static String model(ItemDisplayHud hud) {
        return hud.getItemDisplay().getItemStack().get(DataComponents.ITEM_MODEL).toString();
    }

    @GameTest(structure=FLOOR, maxTicks=10, environment=ENV)
    public void actualFrameItemModelsSwapWithExactlyTwoStableCenteredHudNodes(GameTestHelper h) {
        var f = new Fixture(h);
        var actor = f.fresh("dust_rock_blues", 16, false);
        var player = actor.player();
        WeaponReticleHud.update(player, 0, 0, false);
        var frame = node(player, WeaponReticleHud.FRAME_ID);
        var center = node(player, WeaponReticleHud.CENTER_ID);
        int frameEntity = frame.getEntityId(), centerEntity = center.getEntityId();
        for (var entry : WeaponCatalog.family("shotgun")) {
            var gun = WeaponItems.create(entry);
            player.setItemInHand(InteractionHand.MAIN_HAND, gun);
            var before = gun.copy();
            String expected = entry.frame().equals("pinpoint_slug") ? "destiny:gui/hud/reticle_w44_shotgun_slug"
                    : "destiny:gui/hud/reticle_w105_shotgun_"+entry.frame();
            for (float progress : new float[]{0, .5f, .94f}) {
                WeaponReticleHud.update(player, progress, progress, false);
                check(h, model(node(player, WeaponReticleHud.FRAME_ID)).equals(expected), "Actual equipped frame item model "+entry.id());
                check(h, node(player, WeaponReticleHud.FRAME_ID) == frame && node(player, WeaponReticleHud.CENTER_ID) == center
                                && frame.getEntityId() == frameEntity && center.getEntityId() == centerEntity,
                        "Frame swap, ADS and bloom reuse both actual HUD identities");
                check(h, DisplayHud.getHuds(player).keySet().stream().filter(id -> id.startsWith(WeaponReticleHud.PREFIX)).count() == 2,
                        "Exactly the original two reticle nodes");
                check(h, frame.isAboveHand() && center.isAboveHand() && frame.getLocation().x() == 960
                                && frame.getLocation().y() == 540 && center.getLocation().x() == 960 && center.getLocation().y() == 540,
                        "Centered above-hand frame and aim point");
                check(h, model(center).equals("destiny:gui/hud/reticle_w44_dot") && center.getScale().x() == 4 && center.getScale().y() == 4,
                        "Fixed original center dot");
                check(h, ItemStack.matches(before, gun), "HUD cannot change equipped weapon identity or ammunition");
            }
        }
        player.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(WeaponCatalog.find("austringer").orElseThrow()));
        WeaponReticleHud.update(player, 0, 0, false);
        check(h, model(frame).equals("destiny:gui/hud/reticle_w44_hand_cannon"), "Other families retain their actual W44 model");
        WeaponReticleHud.update(player, 0, 0, true);
        check(h, DisplayHud.getHuds(player).keySet().stream().noneMatch(id -> id.startsWith(WeaponReticleHud.PREFIX)), "Reload hides only reticle nodes");
        for (var entry : WeaponCatalog.family("shotgun")) {
            var gun = WeaponItems.create(entry); player.setItemInHand(InteractionHand.MAIN_HAND, gun);
            var saved = gun.copy();
            WeaponReticleHud.update(player, 1, 0, false);
            check(h, DisplayHud.getHuds(player).keySet().stream().noneMatch(id -> id.startsWith(WeaponReticleHud.PREFIX)),
                    "Raised physical shotgun sight replaces the hip ring and dot: " + entry.id());
            check(h, ItemStack.matches(saved, gun), "Full ADS HUD read preserves actual shotgun");
            WeaponReticleHud.update(player, 0, 0, false);
            check(h, model(node(player, WeaponReticleHud.FRAME_ID)).equals(entry.frame().equals("pinpoint_slug")
                            ? "destiny:gui/hud/reticle_w44_shotgun_slug" : "destiny:gui/hud/reticle_w105_shotgun_"+entry.frame()),
                    "Hip release restores exact frame-dependent reticle");
        }
        h.succeed();
    }
}
