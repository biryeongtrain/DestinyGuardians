package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.ability.warlock.*;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.AmmoGeneration;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.AABB;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;

/** Actual healing, finite automatic damage, geometry and lifecycle checks; no per-stat assertions. */
public final class WarlockW230GameTests {
    private static final String FLOOR = "destiny-test:floor", ENV = "destiny-test:w90_isolated";
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static ServerPlayer player(GameTestHelper h, Identifier superId, Vec3 position) {
        for (int x = 0; x < 16; x++) for (int z = 0; z < 14; z++) h.setBlock(x, 0, z, Blocks.STONE);
        ServerPlayer p = TestPlayers.create(h, position, -90, 0, "W230" + UUID.randomUUID().toString().substring(0, 7));
        Guardians.data(p).setGuardianClass(GuardianClass.WARLOCK);
        Guardians.data(p).setLoadout(GuardianClass.WARLOCK,
                WarlockAbilities.preset(Element.SOLAR).with(AbilitySlot.SUPER, superId));
        Guardians.runtime(p); p.setNoGravity(true); p.setOnGround(true);
        TestCleanup.register(h, () -> { WarlockExpandedSupers.cleanup(p); TestPlayers.remove(p); });
        h.onEachTick(() -> {
            TestPlayers.drain(p);
            if (AbilityService.inSuper(p)) {
                int rotations = SuperCamera.rotations(p);
                p.connection.handleMovePlayer(new ServerboundMovePlayerPacket.Rot(p.getYRot(), p.getXRot(), false, false));
                check(h, SuperCamera.active(p) && SuperCamera.rotations(p) == rotations + 1,
                        "Native rotation heartbeat, watchdog retained " + WarlockExpandedSupers.status(p));
                AbilityService.tickPlayer(p);
            }
            WarlockExpandedSupers.tick(h.getLevel().getServer());
        });
        return p;
    }
    private static ServerPlayer player(GameTestHelper h, Identifier id) {
        return player(h, id, new Vec3(2.5, 1, 6.5));
    }
    private static ServerPlayer resident(GameTestHelper h, Vec3 pos) {
        ServerPlayer p = player(h, WarlockExpandedSupers.WELL_OF_RADIANCE, pos);
        h.getLevel().addNewPlayer(p);
        TestCleanup.register(h, () -> h.getLevel().removePlayerImmediately(p, Entity.RemovalReason.DISCARDED));
        p.setHealth(4);
        return p;
    }
    private static void allied(GameTestHelper h, ServerPlayer owner, ServerPlayer friend) {
        var board = h.getLevel().getScoreboard();
        var team = board.addPlayerTeam("well" + UUID.randomUUID().toString().substring(0, 8));
        board.addPlayerToTeam(owner.getScoreboardName(), team);
        board.addPlayerToTeam(friend.getScoreboardName(), team);
        TestCleanup.register(h, () -> board.removePlayerTeam(team));
    }
    private static void use(GameTestHelper h, ServerPlayer p) {
        Guardians.data(p).setSuperEnergy(1);
        var result = AbilityService.use(p, AbilitySlot.SUPER);
        check(h, result == AbilityService.Result.OK, "Accepted equipped super: " + result);
    }
    private static Husk enemy(GameTestHelper h, Vec3 position) {
        Husk e = h.spawn(EntityTypes.HUSK, position);
        e.setNoAi(true); e.setNoGravity(true); e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1); e.setHealth(1000);
        TestCleanup.register(h, e::discard);
        return e;
    }
    private static void aimAt(ServerPlayer p, LivingEntity target) {
        Vec3 d = target.position().add(0, target.getBbHeight() / 2, 0).subtract(p.getEyePosition());
        float yaw = (float)Math.toDegrees(Math.atan2(-d.x, d.z));
        p.setYRot(yaw); p.setYHeadRot(yaw);
        p.setXRot((float)-Math.toDegrees(Math.atan2(d.y, Math.hypot(d.x, d.z))));
    }
    private static void wall(GameTestHelper h, int x, int minZ, int maxZ) {
        for (int y = 1; y <= 5; y++) for (int z = minZ; z <= maxZ; z++) h.setBlock(new BlockPos(x, y, z), Blocks.STONE);
    }
    private static String blinkDiagnostic(GameTestHelper h, ServerPlayer p) {
        AABB box = p.getBoundingBox();
        StringBuilder out = new StringBuilder(" [testTick=").append(h.getTick())
                .append(" gameTime=").append(p.level().getGameTime()).append(" serverTick=")
                .append(p.level().getServer().getTickCount()).append(' ').append(WarlockExpandedSupers.status(p))
                .append(" feet=").append(p.position()).append(" look=").append(p.getLookAngle())
                .append(" bbox=").append(box).append(" bodyClear=").append(p.level().noCollision(p, box))
                .append(" shift=").append(p.isShiftKeyDown()).append(" inputShift=").append(p.getLastClientInput().shift());
        // Diagnostics mirror the actual swept full-body checks, including large randomized test coordinates.
        Vec3 from = p.position(), last = from;
        for (double distance = .25; distance <= 4; distance += .25) {
            Vec3 at = from.add(p.getLookAngle().normalize().scale(distance));
            AABB destination = box.move(at.subtract(from)), swept = box.move(last.subtract(from)).minmax(destination);
            boolean loaded = p.level().hasChunkAt(BlockPos.containing(swept.minX, swept.minY, swept.minZ))
                    && p.level().hasChunkAt(BlockPos.containing(swept.maxX, swept.minY, swept.minZ))
                    && p.level().hasChunkAt(BlockPos.containing(swept.minX, swept.minY, swept.maxZ))
                    && p.level().hasChunkAt(BlockPos.containing(swept.maxX, swept.minY, swept.maxZ));
            boolean bounds = p.level().isInWorldBounds(BlockPos.containing(at));
            boolean border = p.level().getWorldBorder().isWithinBounds(destination);
            boolean clear = loaded && bounds && border && p.level().noCollision(p, swept);
            out.append(" step=").append(distance).append(" at=").append(at).append(" swept=").append(swept)
                    .append(" loaded=").append(loaded).append(" bounds=").append(bounds)
                    .append(" border=").append(border).append(" clear=").append(clear);
            if (!clear) break;
            last = at;
        }
        return out.append("]").toString();
    }
    private static SuperSession currentTickSession(GameTestHelper h, ServerPlayer p) {
        SuperSession session = Guardians.runtime(p).superSession;
        check(h, session != null && session.tick(), "Nova fixture advances this exact gameTime once" + blinkDiagnostic(h, p));
        return session;
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 700, skyAccess = true)
    public void wellHealsOnlyOwnerAndAlliesAndOutlivesCameraThenExpires(GameTestHelper h) {
        ServerPlayer p = player(h, WarlockExpandedSupers.WELL_OF_RADIANCE); p.setHealth(4);
        ServerPlayer friend = resident(h, new Vec3(3.5, 1, 6.5));
        ServerPlayer stranger = resident(h, new Vec3(3.5, 1, 8.5)); allied(h, p, friend);
        use(h, p);
        h.runAfterDelay(10, () -> check(h, p.getHealth() == 4 && friend.getHealth() == 4,
                "Preparation is not an already active healing field"));
        h.runAfterDelay(48, () -> {
            check(h, !AbilityService.inSuper(p) && !SuperCamera.active(p), "Completed cast releases player/camera for weapons");
            check(h, p.getHealth() > 4 && friend.getHealth() > 4 && stranger.getHealth() == 4,
                    "Real health changed for owner/team only");
            check(h, WarlockExpandedSupers.outgoingDamageMultiplier(p) > 1
                    && WarlockExpandedSupers.outgoingDamageMultiplier(friend) > 1
                    && WarlockExpandedSupers.outgoingDamageMultiplier(stranger) == 1, "Actual membership gates weapon empowerment");
            // Exercise the shared damage hook itself: getter membership alone cannot detect a missing
            // hook, double application, or accidentally empowering abilities. Fresh targets isolate
            // vanilla armor/invulnerability and keep healing/expiry assertions independent of combat.
            Husk primaryTarget = enemy(h, new Vec3(10.5, 1, 3.5));
            Husk abilityTarget = enemy(h, new Vec3(11.5, 1, 9.5));
            primaryTarget.setAbsorptionAmount(0); abilityTarget.setAbsorptionAmount(0);
            float primaryBefore = primaryTarget.getHealth(), abilityBefore = abilityTarget.getHealth();
            Combat.damage(h.getLevel(), p, primaryTarget, 10f, Element.KINETIC,
                    new AmmoGeneration(AmmoGeneration.Kind.PRIMARY, 0));
            Combat.damage(h.getLevel(), p, abilityTarget, 10f, Element.SOLAR, AmmoGeneration.ABILITY);
            float primaryLoss = primaryBefore - primaryTarget.getHealth();
            float abilityLoss = abilityBefore - abilityTarget.getHealth();
            check(h, Math.abs(primaryLoss - 12.5f) < .001f && Math.abs(abilityLoss - 10f) < .001f,
                    "Combat hook applies Well once to PRIMARY and excludes ABILITY; actual hp loss primary="
                            + primaryLoss + " ability=" + abilityLoss);
            friend.setPos(h.absoluteVec(new Vec3(13.5, 1, 6.5)));
            check(h, WarlockExpandedSupers.outgoingDamageMultiplier(friend) == 1, "Exiting volume revokes this field's modifier immediately");
            float owner = p.getHealth();
            WarlockExpandedSupers.tick(h.getLevel().getServer()); WarlockExpandedSupers.tick(h.getLevel().getServer());
            check(h, p.getHealth() == owner, "Duplicate same-gameTime lifecycle ticks cannot duplicate healing");
        });
        h.runAfterDelay(650, () -> {
            check(h, WarlockExpandedSupers.outgoingDamageMultiplier(p) == 1
                    && WarlockExpandedSupers.status(p).contains("well=false"), "Finite construct lifetime expires independently");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 125, skyAccess = true)
    public void wellAirCastWaitsForRealSupportAndSeparateLanding(GameTestHelper h) {
        ServerPlayer p = player(h, WarlockExpandedSupers.WELL_OF_RADIANCE, new Vec3(2.5, 4, 6.5));
        p.setOnGround(false); use(h, p);
        h.runAfterDelay(20, () -> {
            check(h, AbilityService.inSuper(p) && WarlockExpandedSupers.outgoingDamageMultiplier(p) == 1,
                    "Air entry never creates floating field from onGround claims");
            p.setPos(h.absoluteVec(new Vec3(2.5, 1, 6.5))); p.setOnGround(true);
        });
        h.runAfterDelay(30, () -> check(h, AbilityService.inSuper(p), "Real landing plays its own finite source clip"));
        h.runAfterDelay(50, () -> {
            check(h, !AbilityService.inSuper(p) && !SuperCamera.active(p)
                    && WarlockExpandedSupers.outgoingDamageMultiplier(p) > 1, "Grounded landing completes field then releases weapons");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 180, skyAccess = true)
    public void wellEpochRevokesLoadoutRuntimeAndDeathWithoutResurrection(GameTestHelper h) {
        ServerPlayer p = player(h, WarlockExpandedSupers.WELL_OF_RADIANCE);
        AtomicReference<Loadout> old = new AtomicReference<>(Guardians.data(p).loadout().orElseThrow()); use(h, p);
        h.runAfterDelay(45, () -> {
            check(h, WarlockExpandedSupers.outgoingDamageMultiplier(p) > 1, "Field exists after cast");
            Guardians.data(p).setLoadout(GuardianClass.WARLOCK, old.get().with(AbilitySlot.SUPER, WarlockExpandedSupers.NOVA_WARP));
            check(h, WarlockExpandedSupers.outgoingDamageMultiplier(p) == 1, "Changed loadout immediately invalidates buff");
        });
        h.runAfterDelay(48, () -> {
            Guardians.data(p).setLoadout(GuardianClass.WARLOCK, old.get());
            check(h, WarlockExpandedSupers.outgoingDamageMultiplier(p) == 1, "Returning to old class/loadout cannot resurrect removed field");
            use(h, p);
        });
        h.runAfterDelay(90, () -> {
            check(h, WarlockExpandedSupers.outgoingDamageMultiplier(p) > 1, "Fresh epoch can create a fresh field");
            Guardians.forget(p);
            check(h, WarlockExpandedSupers.outgoingDamageMultiplier(p) == 1, "Runtime replacement invalidates retained field");
            WarlockExpandedSupers.cleanup(p); WarlockExpandedSupers.cleanup(p);
            Guardians.runtime(p); use(h, p);
        });
        h.runAfterDelay(133, () -> {
            check(h, WarlockExpandedSupers.outgoingDamageMultiplier(p) > 1, "Third fresh cast starts correctly");
            p.setHealth(0);
            check(h, WarlockExpandedSupers.outgoingDamageMultiplier(p) == 1, "Owner death revokes field synchronously");
        });
        h.runAfterDelay(136, () -> {
            check(h, WarlockExpandedSupers.status(p).contains("well=false"), "Dead owner's displays/field cleared");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 120, skyAccess = true)
    public void chaosIsAutomaticNearestOnlyAndFollowsCurrentAimWithoutWallDamage(GameTestHelper h) {
        ServerPlayer p = player(h, WarlockExpandedSupers.CHAOS_REACH);
        Husk near = enemy(h, new Vec3(5.5, 1, 6.5)), behind = enemy(h, new Vec3(8.5, 1, 6.5));
        Husk hidden = enemy(h, new Vec3(6.6, 1, 10.5)); wall(h, 5, 9, 12);
        aimAt(p, near); use(h, p);
        h.runAfterDelay(10, () -> check(h, near.getHealth() == 1000, "Windup cannot damage without channel timing"));
        h.runAfterDelay(27, () -> {
            check(h, near.getHealth() < 1000 && behind.getHealth() == 1000,
                    "Automatic beam damages nearest collinear target, no primary required");
            aimAt(p, hidden);
        });
        h.runAfterDelay(43, () -> {
            check(h, hidden.getHealth() == 1000, "Changed current view is clipped by block, not cached target lock");
            near.setPos(h.absoluteVec(new Vec3(4.5, 1, 3.5))); aimAt(p, behind);
        });
        h.runAfterDelay(65, () -> check(h, behind.getHealth() < 1000, "Current unobstructed target takes periodic channel damage"));
        h.runAfterDelay(96, () -> {
            check(h, !AbilityService.inSuper(p) && !SuperCamera.active(p), "Finite channel and original exit finish without input");
            float before = behind.getHealth();
            h.runAfterDelay(8, () -> {
                check(h, behind.getHealth() == before, "Finished channel cannot emit late pulses");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 130, skyAccess = true)
    public void novaChargeIsDelayedSingleBurstAndBlinkUsesCollisionVolume(GameTestHelper h) {
        ServerPlayer p = player(h, WarlockExpandedSupers.NOVA_WARP);
        Husk near = enemy(h, new Vec3(4.5, 1, 6.5)), hidden = enemy(h, new Vec3(4.5, 1, 9.5));
        wall(h, 3, 8, 11); use(h, p);
        h.runAfterDelay(50, () -> {
            // onEachTick/runAfterDelay share an Object2LongOpenHashMap, not an ordered queue.
            // At both exact cooldown-boundary inputs advance the idempotent session first, so
            // callback identity/hash iteration cannot leave age one tick behind the other input.
            var session = currentTickSession(h, p);
            session.primary(); session.primary(); session.primary();
            check(h, near.getHealth() == 1000, "Primary queues charge without instant damage or repeated emissions");
        });
        h.runAfterDelay(56, () -> check(h, near.getHealth() == 1000, "Charge has real windup"));
        h.runAfterDelay(68, () -> {
            var session = currentTickSession(h, p);
            check(h, near.getHealth() < 1000 && hidden.getHealth() == 1000, "One charged radial burst respects wall LOS");
            check(h, WarlockExpandedSupers.status(p).contains("bursts=1"), "Held/repeated primary does not duplicate charge");
            p.setYRot(-90); p.setXRot(0); wall(h, 5, 4, 7); p.setShiftKeyDown(true);
            Vec3 before = p.position();
            String beforeDiagnostic = blinkDiagnostic(h, p);
            session.primary();
            check(h, p.getX() < h.absoluteVec(new Vec3(5, 1, 6.5)).x && p.level().noCollision(p, p.getBoundingBox()),
                    "Blink ends before wall with full player bounding box clear; before=" + beforeDiagnostic
                            + " after=" + blinkDiagnostic(h, p));
            check(h, p.position().distanceToSqr(before) >= .25 && WarlockExpandedSupers.status(p).contains("blinks=1"),
                    "Short safe blink actually moves and is accepted once; before=" + beforeDiagnostic
                            + " after=" + blinkDiagnostic(h, p));
            Vec3 position = p.position(); session.primary();
            check(h, p.position().equals(position), "Immediate blink spam is gated");
            WarlockExpandedSupers.cleanup(p); WarlockExpandedSupers.cleanup(p);
        });
        h.runAfterDelay(80, () -> {
            check(h, !AbilityService.inSuper(p) && !SuperCamera.active(p), "Idempotent cleanup releases roam/camera and pending payload");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, environment = ENV, maxTicks = 85, skyAccess = true)
    public void novaRevocationCancelsChargedPayloadBeforeItCanDamage(GameTestHelper h) {
        ServerPlayer p = player(h, WarlockExpandedSupers.NOVA_WARP);
        Husk near = enemy(h, new Vec3(4.5, 1, 6.5)); use(h, p);
        h.runAfterDelay(48, () -> {
            Guardians.runtime(p).superSession.primary();
            Guardians.data(p).setGuardianClass(GuardianClass.HUNTER);
        });
        h.runAfterDelay(70, () -> {
            check(h, near.getHealth() == 1000 && !AbilityService.inSuper(p) && !SuperCamera.active(p),
                    "Class epoch revocation removes delayed charged damage and camera");
            h.succeed();
        });
    }
}
