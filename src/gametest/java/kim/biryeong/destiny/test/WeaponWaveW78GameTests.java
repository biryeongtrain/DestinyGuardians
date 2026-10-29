package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.UUID;
import java.util.stream.StreamSupport;

/** W78 paid shots through beginUse/releaseUse and actual END_SERVER_TICK progression.
 * The dedicated 48x12x32 empty structure bounds an explicit stone deck at y=3 (standing feet y=4).
 * Raised deck, half-block stairs, crest height and gap depth are explicit Minecraft geometry
 * fixtures, not claims about Destiny's original terrain mesh. No reflection, direct wave calls,
 * manually advanced server clocks, client coverage, or changes to inherited tests/players.
 */
public final class WeaponWaveW78GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final String WHISPER = "deafening_whisper";
    private static final String HYPO = "dimensional_hypotrochoid";
    private static final float HP = 1000, EPS = .004f;
    // x=3, eye height ~1.62, downward 35 degrees: ballistic floor contact is near x=5.3.
    // All positive wave witnesses start after x=7: none intercepts the initial grenade.
    private static final double IMPACT_X = 5.3;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static void hp(GameTestHelper h, LivingEntity target, float expected, String message) {
        check(h, Math.abs(target.getHealth() - expected) < EPS,
                message + ": expected HP " + expected + ", got " + target.getHealth());
    }

    private static void bounded(GameTestHelper h, LivingEntity entity) {
        var origin = h.absoluteVec(Vec3.ZERO);
        var b = entity.getBoundingBox();
        check(h, b.minX > origin.x && b.maxX < origin.x + 48
                        && b.minY > origin.y && b.maxY < origin.y + 12
                        && b.minZ > origin.z && b.maxZ < origin.z + 32,
                "Whole W78 entity AABB remains strictly inside the dedicated 48x12x32 structure");
    }

    private static WeaponProfile profile(ItemStack stack) {
        return WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow());
    }

    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, profile(stack));
    }

    private static void deck(GameTestHelper h) {
        // The structure supplies the full 48x12x32 test bounds. Materialize the raised
        // gameplay deck explicitly before any wall/slab/gap edits, independent of SNBT conversion.
        // No players or mobs exist yet, so an assertion here cannot leak an entity fixture.
        for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) {
            h.setBlock(x, 3, z, Blocks.STONE);
            var position = h.absolutePos(new BlockPos(x, 3, z));
            var state = h.getLevel().getBlockState(position);
            check(h, state.is(Blocks.STONE),
                    "Explicit W78 deck setup must place stone at local (" + x + ",3," + z
                            + "); actual=" + state + ", absolute=" + position);
        }
    }

    private static ServerPlayer player(GameTestHelper h, double z) {
        deck(h);
        var p = TestPlayers.hunter(h, Element.VOID, new Vec3(3, 4, z), -90, 35,
                "W78_" + UUID.randomUUID().toString().substring(0, 8));
        TestCleanup.register(h, () -> {
            // These embedded players are intentionally not world/player-list registered.
            p.setServerLevel(h.getLevel());
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            TestPlayers.remove(p);
        });
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setOnGround(true);
        bounded(h, p);
        h.onEachTick(() -> { TestPlayers.drain(p); bounded(h, p); });
        return p;
    }

    private static ItemStack equip(GameTestHelper h, ServerPlayer p, String id, int rounds, int reserve) {
        var entry = WeaponCatalog.find(id).orElseThrow();
        var f = WeaponProfile.forEntry(entry);
        check(h, f.mode() == WeaponProfile.Mode.PROJECTILE && f.chargeTicks() == 0
                        && f.burst() == 1 && f.pellets() == 1 && !f.infiniteReserve(),
                id + " is an immediate finite-ammunition projectile fixture");
        var stack = WeaponItems.create(entry);
        WeaponItems.save(stack, new WeaponMagazine(f, rounds < 0 ? f.magazine() : rounds, reserve));
        int slot = WeaponCharacteristics.of(entry).slot().hotbar();
        p.getInventory().setItem(slot, stack);
        p.getInventory().setSelectedSlot(slot);
        kim.biryeong.destiny.weapon.WeaponAccuracy.setAirborneBonus(stack, 100);
        WeaponRuntime.tickPlayer(p); // Bind once; projectile progression only uses the real server event.
        TestPlayers.drain(p);
        return stack;
    }

    private static Husk target(GameTestHelper h, double x, double y, double z) {
        var target = h.spawn(EntityTypes.HUSK, new Vec3(x, y, z));
        TestCleanup.register(h, target::discard);
        target.setNoAi(true);
        target.setNoGravity(true);
        target.setPersistenceRequired();
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP);
        target.getAttribute(Attributes.ARMOR).setBaseValue(0);
        target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        target.setHealth(HP);
        bounded(h, target);
        h.onEachTick(() -> bounded(h, target));
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
        var stack = p.getMainHandItem();
        int rounds = ammo(stack).rounds(), reserve = ammo(stack).reserve();
        p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(35);
        WeaponAiming.tick(p);
        floorPath(h, p);
        check(h, WeaponRuntime.beginUse(p), "Production beginUse accepts the real paid grenade shot");
        check(h, ammo(stack).rounds() == rounds - 1 && ammo(stack).reserve() == reserve,
                "Acceptance spends exactly one loaded round and no reserve before automatic reload");
        WeaponRuntime.releaseUse(p, stack);
        check(h, WeaponRuntime.activeProjectiles(p) == 1,
                "Accepted shot has one owned in-flight projectile before any real server tick");
    }

    /** Independent fixture preflight only: it never creates/advances a runtime projectile.
     * Check the actual world collision shapes and hostile boxes along each free-flight segment.
     */
    private static void floorPath(GameTestHelper h, ServerPlayer p) {
        var f = profile(p.getMainHandItem());
        var from = p.getEyePosition();
        var initialEye = from;
        var origin = h.absoluteVec(Vec3.ZERO);
        var velocity = p.getLookAngle().normalize().scale(f.speed());
        for (int tick = 0; tick < 8; tick++) {
            var to = from.add(velocity);
            var block = h.getLevel().clip(new ClipContext(from, to,
                    ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
            var end = block.getType() == HitResult.Type.MISS ? to : block.getLocation();
            for (var target : h.getLevel().getEntitiesOfClass(LivingEntity.class,
                    new AABB(from, end).inflate(.3), e -> Combat.isEnemy(p, e) && !p.isAlliedTo(e))) {
                var box = target.getBoundingBox().inflate(.08);
                check(h, !box.contains(from) && box.clip(from, end).isEmpty(),
                        "No hostile witness intercepts the initial paid ballistic flight to the floor");
            }
            if (block.getType() == HitResult.Type.BLOCK) {
                var local = block.getLocation().subtract(origin);
                check(h, block.getDirection() == Direction.UP
                                && local.x > 5 && local.x < 5.6 && Math.abs(local.y - 4) < .001,
                        "First ballistic collider is the explicit deck's upper face near x=5.3, y=4"
                                + "; flightTick=" + tick + ", local=" + local
                                + ", from=" + from + ", fromLocal=" + from.subtract(origin)
                                + ", velocity=" + velocity + ", toLocal=" + to.subtract(origin)
                                + ", face=" + block.getDirection() + ", inside=" + block.isInside()
                                + ", hitBlock=" + block.getBlockPos()
                                + ", hitState=" + h.getLevel().getBlockState(block.getBlockPos())
                                + ", origin=" + origin + ", playerLocal=" + p.position().subtract(origin)
                                + ", initialEyeLocal=" + initialEye.subtract(origin)
                                + ", eyeHeight=" + p.getEyeHeight() + ", pose=" + p.getPose()
                                + ", yaw=" + p.getYRot() + ", pitch=" + p.getXRot());
                return;
            }
            from = to;
            velocity = velocity.add(0, -f.gravity(), 0);
        }
        check(h, false, "Bounded downward fixture must reach the floor within eight free-flight ticks");
    }

    private record Fixture(GameTestHelper h, ServerPlayer owner, ItemStack gun,
                           WaveFrameProfile.Profile wave, double z) {
        int finish() { return (int) Math.ceil(wave.length() / wave.speed()) + 16; }
        float damage() { return profile(gun).damage() * wave.waveMultiplier(); }
        Husk target(double x, double y) { return WeaponWaveW78GameTests.target(h, x, y, z); }
        void hitOnce(LivingEntity target, String message) { hp(h, target, HP - damage(), message); }
    }

    private static Fixture fixture(GameTestHelper h, String id, double z) {
        var p = player(h, z);
        var gun = equip(h, p, id, -1, 3);
        var wave = WaveFrameProfile.of(WeaponItems.entry(gun).orElseThrow()).orElseThrow();
        check(h, wave.length() > 6 && IMPACT_X + wave.length() < 47
                        && z - wave.width() / 2 > 1 && z + wave.width() / 2 < 31,
                "Complete wave travel and width fit strictly inside the bounded floor");
        return new Fixture(h, p, gun, wave, z);
    }

    private static final class Observation {
        private final LivingEntity target;
        private float previous = HP;
        private int first = -1, changes;
        Observation(GameTestHelper h, LivingEntity target) {
            this.target = target;
            h.onEachTick(this::sample);
        }
        void sample() {
            float current = target.getHealth();
            if (current < previous - EPS) {
                if (first < 0) first = target.level().getServer().getTickCount();
                changes++;
            }
            previous = current;
        }
    }

    private static void progression(GameTestHelper h, String id) {
        var f = fixture(h, id, 16);
        var near = f.target(7.6, 4);
        var far = f.target(IMPACT_X + f.wave.length() * .8, 4);
        var beyondEnd = f.target(IMPACT_X + f.wave.length() + 1.5, 4);
        // Offset the behind-impact witness sideways so it cannot intercept the descending grenade.
        var behind = target(h, 3.8, 4, 16.9);
        var side = target(h, 6, 4, 16 + f.wave.width() / 2 + .8);
        var airborne = f.target(7.6, 4 + f.wave.height() + .6);
        var nearSeen = new Observation(h, near);
        var farSeen = new Observation(h, far);
        final boolean[] delayed = {false};
        check(h, far.getX() - h.absoluteVec(new Vec3(IMPACT_X, 4, 16)).x > 3.5,
                "Forward witness lies beyond the old 3-block radial explosion");
        h.onEachTick(() -> {
            if (near.getHealth() < HP - EPS && far.getHealth() == HP) {
                delayed[0] = true;
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 1,
                        "In-flight wave retains its one projectile-budget slot after floor impact");
            }
        });
        exactAim(h, java.util.List.of(f.owner), () -> {
            shot(h, f.owner);
            for (var target : new LivingEntity[]{near, far, beyondEnd, behind, side, airborne})
                hp(h, target, HP, "No synchronous radial blast or direct target hit at acceptance");
            h.runAfterDelay(f.finish(), () -> {
                nearSeen.sample(); farSeen.sample();
                check(h, delayed[0] && nearSeen.first >= 0 && farSeen.first > nearSeen.first,
                        "Natural ticks hit the near enemy before the far enemy, with a safe far interval");
                f.hitOnce(near, "Overlapping terrain substeps and lateral lanes damage near target exactly once");
                f.hitOnce(far, "Forward wave damages distant target exactly once without radial falloff");
                check(h, nearSeen.changes == 1 && farSeen.changes == 1,
                        "Neither overlapping segments nor later real ticks repeat target HP loss");
                hp(h, beyondEnd, HP, "Finite wave length leaves the beyond-end target safe");
                hp(h, behind, HP, "Nearby enemy behind the impact receives no ordinary radial explosion");
                hp(h, side, HP, "Enemy outside the wave's full width receives no side blast");
                hp(h, airborne, HP, "Airborne AABB above the authored crest is safe");
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0, "Expired wave releases its budget slot");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void whisperPaidFloorShotPropagatesInOrderOnceAndSparesOutsideTargets(GameTestHelper h) {
        progression(h, WHISPER);
    }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void hypotrochoidPaidFloorShotPropagatesInOrderOnceAndSparesOutsideTargets(GameTestHelper h) {
        progression(h, HYPO);
    }

    private static void barrier(GameTestHelper h, String id, boolean gap) {
        var f = fixture(h, id, 16);
        var before = f.target(7.3, 4);
        var after = f.target(11.5, 4);
        check(h, f.wave.length() > 7 && f.wave.stepDown() < 3,
                "Beyond-barrier target is within wave reach; missing deck is deeper than admitted drop");
        // Full-width obstruction crosses every independent lane, with clearance on both sides.
        for (int z = 10; z <= 22; z++) {
            if (gap) {
                for (int y = 0; y <= 3; y++) h.setBlock(9, y, z, Blocks.AIR);
            } else {
                for (int y = 4; y <= 9; y++) h.setBlock(9, y, z, Blocks.STONE);
            }
        }
        check(h, h.getLevel().noCollision(after, after.getBoundingBox()),
                "Shielded enemy does not intersect the fixture wall");
        exactAim(h, java.util.List.of(f.owner), () -> {
            shot(h, f.owner);
            h.runAfterDelay(f.finish(), () -> {
                f.hitOnce(before, "Paid floor impact produces a wave before the barrier");
                hp(h, after, HP, gap
                        ? "One-block unsupported void stops all lanes without speed/substep tunneling to the far deck"
                        : "Solid wall shields the enemy and stops all forward lanes");
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0,
                        "Fully stopped wave removes its active projectile slot");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void whisperSolidWallStopsGroundWave(GameTestHelper h) { barrier(h, WHISPER, false); }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void hypotrochoidSolidWallStopsGroundWave(GameTestHelper h) { barrier(h, HYPO, false); }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void whisperOneBlockVoidCannotBeSkipped(GameTestHelper h) { barrier(h, WHISPER, true); }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void hypotrochoidOneBlockVoidCannotBeSkipped(GameTestHelper h) { barrier(h, HYPO, true); }

    private static void lateralBarrier(GameTestHelper h, boolean gap) {
        var f = fixture(h, HYPO, 16);
        check(h, f.wave.width() == 5 && f.wave.stepDown() < 3
                        && IMPACT_X > 4 && IMPACT_X + f.wave.length() < 22,
                "Five-block heavy wave spans the lateral barrier; barrier extends past all forward travel");
        // Parallel to flight: impact z=16, obstruction z=[17,18), far lane center z=18.25.
        // Independent lane seeding could previously create that far lane beyond the obstruction.
        // Start before impact and end beyond the wave, so no forward path can go around either end.
        for (int x = 4; x <= 22; x++) {
            if (gap) {
                for (int y = 0; y <= 3; y++) h.setBlock(x, y, 17, Blocks.AIR);
            } else {
                for (int y = 4; y <= 9; y++) h.setBlock(x, y, 17, Blocks.STONE);
            }
        }
        var nearSide = target(h, 11, 4, 15.5);
        var farSide = target(h, 11, 4, 18.4);
        var origin = h.absoluteVec(Vec3.ZERO);
        check(h, farSide.getBoundingBox().minZ > origin.z + 18
                        && farSide.getBoundingBox().minZ < origin.z + 18.5,
                "Far-side target is wholly beyond the one-block barrier but overlaps the old outer lane");
        for (var target : new LivingEntity[]{nearSide, farSide}) {
            check(h, h.getLevel().noCollision(target, target.getBoundingBox()),
                    "Lateral witnesses are clear of the wall and stand on their respective intact decks");
            var under = BlockPos.containing(target.position().add(0, -.1, 0));
            check(h, h.getLevel().getBlockState(under).is(Blocks.STONE),
                    "Both witnesses have real stone support; far-side safety is not caused by missing target support");
        }
        exactAim(h, java.util.List.of(f.owner), () -> {
            shot(h, f.owner);
            h.runAfterDelay(f.finish(), () -> {
                f.hitOnce(nearSide, "Paid heavy floor wave advances on the reachable side of a parallel barrier");
                hp(h, farSide, HP, gap
                        ? "Lateral lane initialization cannot seed a wave across a one-block unsupported gap"
                        : "Lateral lane initialization cannot seed a wave across a tall parallel wall");
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0,
                        "Reachable lanes expire and blocked outer lanes leave no active projectile");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void hypotrochoidCannotSeedLanesAcrossParallelWall(GameTestHelper h) { lateralBarrier(h, false); }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void hypotrochoidCannotSeedLanesAcrossParallelGap(GameTestHelper h) { lateralBarrier(h, true); }

    private static void steps(GameTestHelper h, String id) {
        var f = fixture(h, id, 16);
        check(h, f.wave.stepUp() >= .5 && f.wave.stepDown() >= .5 && f.wave.length() > 10,
                "Authored local terrain adaptation admits half-block up/down transitions and this bounded course");
        for (int x = 8; x <= 13; x++) for (int z = 10; z <= 22; z++)
            h.setBlock(x, 4, z, x == 10 || x == 11 ? Blocks.STONE : Blocks.STONE_SLAB);
        var firstSlab = f.target(8.8, 4.5);
        var raised = f.target(10.8, 5);
        var lastSlab = f.target(12.8, 4.5);
        var down = f.target(14.8, 4);
        for (var target : new LivingEntity[]{firstSlab, raised, lastSlab, down})
            check(h, h.getLevel().noCollision(target, target.getBoundingBox()),
                    "Terrain-following witness stands on its collision-shape surface without suffocation");
        exactAim(h, java.util.List.of(f.owner), () -> {
            shot(h, f.owner);
            h.runAfterDelay(f.finish(), () -> {
                f.hitOnce(firstSlab, "Wave follows a real bottom half-slab collision surface upward");
                f.hitOnce(raised, "Two admitted half steps reach a full-block raised deck");
                f.hitOnce(lastSlab, "Wave descends onto the next half-slab surface");
                f.hitOnce(down, "Wave returns to the original deck and continues forward");
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0, "Terrain-following wave eventually expires");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void whisperFollowsHalfSlabsUpAndDown(GameTestHelper h) { steps(h, WHISPER); }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void hypotrochoidFollowsHalfSlabsUpAndDown(GameTestHelper h) { steps(h, HYPO); }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void cleanupRemovesOnlyOwnersLiveWaveAndPreventsLaterDamage(GameTestHelper h) {
        var removed = fixture(h, WHISPER, 8);
        var keeper = fixture(h, HYPO, 24);
        var first = removed.target(7.6, 4);
        var untouched = removed.target(IMPACT_X + removed.wave.length() * .85, 4);
        var kept = keeper.target(IMPACT_X + keeper.wave.length() * .85, 4);
        final boolean[] cleaned = {false};
        h.onEachTick(() -> {
            if (cleaned[0] || first.getHealth() == HP) return;
            check(h, untouched.getHealth() == HP && WeaponRuntime.activeProjectiles(removed.owner) == 1
                            && WeaponRuntime.activeProjectiles(keeper.owner) == 1,
                    "Both real shots have become live waves before the distant witnesses are reached");
            WeaponRuntime.cleanup(removed.owner);
            cleaned[0] = true;
            check(h, WeaponRuntime.activeProjectiles(removed.owner) == 0
                            && WeaponRuntime.activeProjectiles(keeper.owner) == 1,
                    "Cleanup removes only its owner's active wave immediately");
        });
        exactAim(h, java.util.List.of(removed.owner, keeper.owner), () -> {
            shot(h, removed.owner); shot(h, keeper.owner);
            h.runAfterDelay(Math.max(removed.finish(), keeper.finish()), () -> {
                check(h, cleaned[0], "Cleanup was exercised after a real floor wave dealt near damage");
                removed.hitOnce(first, "Near enemy was hit before cleanup");
                hp(h, untouched, HP, "Cleaned live wave cannot resume or damage a distant enemy");
                keeper.hitOnce(kept, "Other owner's wave continues to its distant enemy");
                check(h, WeaponRuntime.activeProjectiles(removed.owner) == 0
                                && WeaponRuntime.activeProjectiles(keeper.owner) == 0,
                        "Neither completed nor cleaned wave leaks a projectile slot");
                h.succeed();
            });
        });
    }

    private static void dimension(GameTestHelper h, String id) {
        var f = fixture(h, id, 16);
        var first = f.target(7.6, 4);
        var far = f.target(IMPACT_X + f.wave.length() * .85, 4);
        var other = StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                .filter(level -> level != h.getLevel()).findFirst().orElseThrow();
        final int[] changed = {-1};
        final boolean[] invalidated = {false};
        h.onEachTick(() -> {
            if (changed[0] < 0 && first.getHealth() < HP) {
                check(h, far.getHealth() == HP && WeaponRuntime.activeProjectiles(f.owner) == 1,
                        "Dimension change starts with a live wave and untouched far witness");
                // Embedded fixture is unregistered: prove persistent level mismatch validation,
                // not the Fabric real-player teleport event. Leave mismatch through a real server tick.
                f.owner.setServerLevel(other);
                changed[0] = h.getLevel().getServer().getTickCount();
            } else if (!invalidated[0] && changed[0] >= 0
                    && h.getLevel().getServer().getTickCount() >= changed[0] + 2) {
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0,
                        "Real server progression discards the wave whose owner changed level");
                f.owner.setServerLevel(h.getLevel());
                invalidated[0] = true;
            }
        });
        exactAim(h, java.util.List.of(f.owner), () -> {
            shot(h, f.owner);
            h.runAfterDelay(f.finish(), () -> {
                check(h, invalidated[0], "Persistent cross-dimension mismatch was observed and owner returned");
                hp(h, far, HP, "Returning owner to the original dimension cannot revive the discarded wave");
                check(h, WeaponRuntime.activeProjectiles(f.owner) == 0, "Dimension invalidation leaks no budget slot");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void whisperLiveWaveCannotCrossDimensionsOrRevive(GameTestHelper h) { dimension(h, WHISPER); }

    @GameTest(structure = FLOOR, maxTicks = 205, environment = "destiny-test:w90_isolated")
    public void hypotrochoidLiveWaveCannotCrossDimensionsOrRevive(GameTestHelper h) { dimension(h, HYPO); }

    private static void reloadDeadline(GameTestHelper h, String id) {
        var p = player(h, 16);
        var gun = equip(h, p, id, 1, 3);
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p);
            hp(h, p, p.getMaxHealth(), "Paid floor shot does not synchronously damage its owner");
            check(h, ammo(gun).rounds() == 0 && ammo(gun).reserve() == 3,
                    "Initial payment is asserted independently of later legitimate automatic reload");
            h.startSequence().thenExecuteAfter(2, () -> {
                var state = WeaponRuntime.ammunition(p).orElseThrow();
                check(h, WeaponRuntime.reloading(p) && state.reloadRemaining() > 1,
                        "Last paid round starts an automatic reload with a future server deadline");
                int remaining = state.reloadRemaining();
                h.runAfterDelay(remaining - 1L, () -> {
                    check(h, ammo(gun).rounds() == 0 && ammo(gun).reserve() == 3 && WeaponRuntime.reloading(p),
                            "No ammunition transfer occurs before the actual reload deadline");
                });
                h.startSequence().thenExecuteAfter(remaining + 2, () -> {
                    int loaded = Math.min(3, profile(gun).magazine());
                    check(h, !WeaponRuntime.reloading(p) && ammo(gun).rounds() == loaded
                                    && ammo(gun).reserve() == 3 - loaded,
                            "Automatic reload transfers finite reserve only after its original deadline");
                    check(h, ammo(gun).rounds() + ammo(gun).reserve() == 3,
                            "Wave plus automatic reload conserves the original four rounds minus the one paid shot");
                    h.runAfterDelay(8, () -> {
                        check(h, ammo(gun).rounds() == loaded && ammo(gun).reserve() == 3 - loaded,
                                "Released input queues no additional shot after reload completion");
                        h.succeed();
                    });
                });
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 285, environment = "destiny-test:w90_isolated")
    public void whisperInitialPaymentAndAutomaticReloadHaveSeparateDeadlines(GameTestHelper h) { reloadDeadline(h, WHISPER); }

    @GameTest(structure = FLOOR, maxTicks = 285, environment = "destiny-test:w90_isolated")
    public void hypotrochoidInitialPaymentAndAutomaticReloadHaveSeparateDeadlines(GameTestHelper h) { reloadDeadline(h, HYPO); }

    private static void ordinary(GameTestHelper h, String id) {
        var p = player(h, 16);
        var gun = equip(h, p, id, -1, 3);
        check(h, WaveFrameProfile.of(WeaponItems.entry(gun).orElseThrow()).isEmpty()
                        && profile(gun).blastRadius() > 0,
                "Ordinary projectile keeps its radial profile and has no W78 wave intrinsic");
        var behind = target(h, 4.4, 4, 17);
        var side = target(h, 5.5, 4, 17.5);
        var distant = target(h, 13, 4, 16);
        boolean breach=BreachGrenade.supports(WeaponItems.entry(gun).orElseThrow());
        exactAim(h, java.util.List.of(p), () -> {
            if(breach) {
                // W82 deliberately replaces Salvo's obsolete floor-impact characterization:
                // native lightweight grenades ricochet on terrain, but character impact still
                // produces the same radial (not forward-wave) damage, even before arming.
                var direct=target(h,4.4,4,16);
                var from=p.getEyePosition();
                check(h,direct.getBoundingBox().inflate(.08).clip(from,from.add(p.getLookAngle().scale(profile(gun).speed()))).isPresent(),
                        "Salvo has a real first-segment hostile collision before reaching the deck");
                int before=ammo(gun).rounds();
                check(h,WeaponRuntime.beginUse(p),"Accept paid Salvo direct-impact shot");
                WeaponRuntime.releaseUse(p,gun);
                check(h,ammo(gun).rounds()==before-1&&ammo(gun).reserve()==3,"Spend exactly one round before any impact");
            } else shot(h, p);
            h.runAfterDelay(8, () -> {
                check(h, behind.getHealth() < HP && side.getHealth() < HP,
                        "Paid impact retains backward and lateral radial HP damage");
                hp(h, distant, HP, "Ordinary grenade/rocket does not create a forward ground wave");
                check(h, WeaponRuntime.activeProjectiles(p) == 0, "Ordinary projectile ends at its explosive impact");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 75, environment = "destiny-test:w90_isolated")
    public void ordinarySalvagersSalvoStillExplodesRadially(GameTestHelper h) { ordinary(h, "salvager_s_salvo"); }

    @GameTest(structure = FLOOR, maxTicks = 75, environment = "destiny-test:w90_isolated")
    public void ordinaryBadOmensStillExplodesRadially(GameTestHelper h) { ordinary(h, "bad_omens"); }

    @GameTest(structure = FLOOR, environment = "destiny-test:w90_allied_isolated", maxTicks = 205)
    public void paidWaveSparesAlliedHostileAndOwnerWhileHittingLegalEnemy(GameTestHelper h) {
        var f = fixture(h, WHISPER, 16);
        var ally = f.target(8, 4);
        var enemy = f.target(11, 4);
        var scoreboard = h.getLevel().getScoreboard();
        String name = "w78_" + UUID.randomUUID().toString().substring(0, 8);
        var previous = scoreboard.getPlayersTeam(f.owner.getScoreboardName());
        var team = scoreboard.addPlayerTeam(name);
        TestCleanup.register(h, () -> {
            if (scoreboard.getPlayerTeam(name) == team) scoreboard.removePlayerTeam(team);
            if (previous != null && scoreboard.getPlayerTeam(previous.getName()) == previous)
                scoreboard.addPlayerToTeam(f.owner.getScoreboardName(), previous);
        });
        scoreboard.addPlayerToTeam(f.owner.getScoreboardName(), team);
        scoreboard.addPlayerToTeam(ally.getScoreboardName(), team);
        check(h, !Combat.isEnemy(f.owner, ally) && f.owner.isAlliedTo(ally)
                        && Combat.isEnemy(f.owner, enemy) && !f.owner.isAlliedTo(enemy),
                "Combat rejects the scoreboard ally and accepts the unallied forward witness");
        float ownerHp = f.owner.getHealth();
        exactAim(h, java.util.List.of(f.owner), () -> {
            shot(h, f.owner);
            h.runAfterDelay(f.finish(), () -> {
                hp(h, ally, HP, "Actual paid forward wave spares the allied hostile");
                hp(h, f.owner, ownerHp, "Actual paid wave spares its owner");
                f.hitOnce(enemy, "Same shot damages a legal hostile after passing the ally");
                h.succeed();
            });
        });
    }
}
