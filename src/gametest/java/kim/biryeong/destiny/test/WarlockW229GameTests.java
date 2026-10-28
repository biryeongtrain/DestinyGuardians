package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.ability.warlock.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import kim.biryeong.destiny.camera.SuperCamera;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.*;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.*;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Behavioral server regressions, not source-token or per-number perk tests. */
public final class WarlockW229GameTests {
    private static void check(GameTestHelper h, boolean value, String message) { h.assertTrue(value, Component.literal(message)); }
    private static ServerPlayer player(GameTestHelper h, Element e, Vec3 position) {
        // 26.3's running floor fixture can expose air at relative y=0 (H18 camera regression).
        // Own an explicit support surface; the product must still reject genuinely unsupported casts.
        for (int x = 0; x < 16; x++) for (int z = 0; z < 14; z++) h.setBlock(x, 0, z, Blocks.STONE);
        ServerPlayer p = TestPlayers.create(h, position, -90, 0, "Warlock" + UUID.randomUUID().toString().substring(0, 7));
        Guardians.data(p).setGuardianClass(GuardianClass.WARLOCK);
        Guardians.data(p).setLoadout(GuardianClass.WARLOCK, WarlockAbilities.preset(e));
        Guardians.runtime(p);
        p.setOnGround(true);
        TestCleanup.register(h, () -> { WarlockAbilities.cleanup(p); TestPlayers.remove(p); });
        h.onEachTick(() -> TestPlayers.drain(p));
        return p;
    }
    private static ServerPlayer player(GameTestHelper h, Element e) { return player(h, e, new Vec3(2.5, 1, 6.5)); }
    private static ServerPlayer ally(GameTestHelper h, Vec3 pos) {
        ServerPlayer p = player(h, Element.ARC, pos);
        p.setNoGravity(true); p.setHealth(5);
        h.getLevel().addNewPlayer(p);
        TestCleanup.register(h, () -> h.getLevel().removePlayerImmediately(p, Entity.RemovalReason.DISCARDED));
        return p;
    }
    private static Husk enemy(GameTestHelper h, Vec3 pos, float health) {
        Husk target = h.spawn(EntityTypes.HUSK, pos);
        target.setNoAi(true); target.setNoGravity(true); target.setPersistenceRequired();
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(health);
        target.getAttribute(Attributes.ARMOR).setBaseValue(0);
        target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        target.setHealth(health);
        TestCleanup.register(h, () -> { kim.biryeong.destiny.combat.Statuses.forget(target); target.discard(); });
        return target;
    }
    private static void wall(GameTestHelper h, int x, int minZ, int maxZ) {
        for (int y = 1; y <= 4; y++) for (int z = minZ; z <= maxZ; z++) h.setBlock(new BlockPos(x, y, z), Blocks.STONE);
    }
    private static void pumpSuper(GameTestHelper h, ServerPlayer p) {
        // TestPlayers aren't in PlayerList: pump only their session, like the Hunter HUD tests.
        h.onEachTick(() -> {
            if (!AbilityService.inSuper(p)) return;
            int rotations = SuperCamera.rotations(p);
            p.connection.handleMovePlayer(new ServerboundMovePlayerPacket.Rot(p.getYRot(), p.getXRot(), false, false));
            check(h, SuperCamera.active(p) && SuperCamera.rotations(p) == rotations + 1,
                    "Fake client sends native rotation heartbeat without disabling watchdog" + diagnostic(h, p));
            AbilityService.tickPlayer(p);
        });
    }
    private static void aimAt(ServerPlayer p, Vec3 target) {
        Vec3 d = target.subtract(p.getEyePosition());
        float yaw = (float) Math.toDegrees(Math.atan2(-d.x, d.z));
        p.setYRot(yaw); p.setYHeadRot(yaw);
        p.setXRot((float) -Math.toDegrees(Math.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z))));
    }
    private static Vec3 center(LivingEntity e) { return e.position().add(0, e.getBbHeight() / 2, 0); }
    private static HitResult ray(ServerPlayer p, Vec3 target) { return ray(p, p.getEyePosition(), target); }
    private static HitResult ray(ServerPlayer p, Vec3 from, Vec3 target) {
        return p.level().clip(new ClipContext(from, target, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
    }
    private static String diagnostic(GameTestHelper h, ServerPlayer p, LivingEntity... targets) {
        StringBuilder d = new StringBuilder(" [testTick=").append(h.getTick()).append(" serverTick=")
                .append(p.level().getServer().getTickCount()).append(" gameTime=").append(p.level().getGameTime())
                .append(" feet=").append(p.position()).append(" eye=").append(p.getEyePosition())
                .append(" look=").append(p.getLookAngle()).append(" support=")
                .append(p.level().getBlockState(BlockPos.containing(p.position().add(0, -.05, 0))))
                .append(" camera=").append(SuperCamera.active(p)).append(" rotations=").append(SuperCamera.rotations(p))
                .append(" fields=").append(WarlockGrenade.fields(p)).append(" flights=").append(SimProjectile.activeCount(p));
        for (LivingEntity target : targets) d.append(" target=").append(target.getUUID()).append(" pos=").append(target.position())
                .append(" center=").append(center(target)).append(" hp=").append(target.getHealth()).append(" max=").append(target.getMaxHealth())
                .append(" ray=").append(ray(p, center(target)).getType())
                .append(" bodyClear=").append(target.level().noCollision(target, target.getBoundingBox()));
        return d.append(']').toString();
    }
    private static void use(GameTestHelper h, ServerPlayer p, AbilitySlot slot) {
        AbilityService.Result result = AbilityService.use(p, slot);
        check(h, result == AbilityService.Result.OK, "Accepted " + slot + " result=" + result + diagnostic(h, p));
    }
    private static void rearmRift(GameTestHelper h, ServerPlayer p) {
        Guardians.data(p).setGuardianClass(GuardianClass.WARLOCK);
        Guardians.data(p).setLoadout(GuardianClass.WARLOCK, WarlockAbilities.preset(Element.ARC));
        Guardians.data(p).setCooldown(AbilitySlot.CLASS_ABILITY, 0);
        p.setOnGround(true);
        use(h, p, AbilitySlot.CLASS_ABILITY);
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void elevenRegisteredAbilitiesAndThreeCompletePresets(GameTestHelper h) {
        var all = AbilityRegistry.all().stream().filter(a -> a.guardianClass() == GuardianClass.WARLOCK).toList();
        check(h, all.size() == 11, "Exactly eleven class-owned abilities registered by initializer");
        for (Element e : List.of(Element.ARC, Element.SOLAR, Element.VOID)) {
            Loadout loadout = WarlockAbilities.preset(e);
            check(h, loadout.abilities().size() == 5, "Five slots in each elemental preset");
            for (AbilitySlot slot : AbilitySlot.values()) {
                Ability a = AbilityRegistry.get(loadout.get(slot)).orElseThrow();
                check(h, a.slot() == slot && a.guardianClass() == GuardianClass.WARLOCK, "Correct class and slot");
                check(h, slot == AbilitySlot.JUMP || slot == AbilitySlot.CLASS_ABILITY || a.element() == e, "Correct element");
            }
        }
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void invalidRiftDoesNotSpendCooldownOrChangeBlocks(GameTestHelper h) {
        ServerPlayer p = player(h, Element.ARC);
        p.setOnGround(false);
        check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.FAILED, "Air cast rejected");
        check(h, Guardians.data(p).cooldown(AbilitySlot.CLASS_ABILITY) == 0, "Rejected air cast is free");
        p.setPos(h.absoluteVec(new Vec3(2.5, 4, 6.5))); p.setOnGround(true);
        check(h, AbilityService.use(p, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.FAILED, "Fake grounded state without support rejected");
        check(h, Guardians.data(p).cooldown(AbilitySlot.CLASS_ABILITY) == 0, "Unsupported cast is free");
        p.setPos(h.absoluteVec(new Vec3(2.5, 1, 6.5)));
        var floor = h.getBlockState(new BlockPos(2, 0, 6));
        use(h, p, AbilitySlot.CLASS_ABILITY);
        check(h, Guardians.data(p).cooldown(AbilitySlot.CLASS_ABILITY) > 0 && WarlockClassAbility.active(p), "Valid supported cast consumes cooldown");
        check(h, h.getBlockState(new BlockPos(2, 0, 6)).equals(floor), "Rift preserves the player's floor block");
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 340, environment = "destiny-test:w90_isolated")
    public void riftHealsOnlyVisibleNearbyPlayersAndStaysAtItsOrigin(GameTestHelper h) {
        ServerPlayer owner = player(h, Element.ARC);
        ServerPlayer near = ally(h, new Vec3(3.5, 1, 6.5));
        ServerPlayer blocked = ally(h, new Vec3(2.5, 1, 9.5));
        ServerPlayer outside = ally(h, new Vec3(8.5, 1, 6.5));
        ServerPlayer above = ally(h, new Vec3(3.5, 4, 6.5));
        for (int y = 1; y <= 4; y++) for (int x = 0; x <= 5; x++) h.setBlock(new BlockPos(x, y, 8), Blocks.STONE);
        Husk mob = enemy(h, new Vec3(3.5, 1, 5.5), 20); mob.setHealth(5);
        use(h, owner, AbilitySlot.CLASS_ABILITY);
        Vec3 origin = WarlockClassAbility.origin(owner);
        boolean modelExpected = kim.biryeong.destiny.fx.ClassAbilityEffects.item("warlock/class_ability")
                .has(net.minecraft.core.component.DataComponents.ITEM_MODEL)
                && AbilityRegistry.get(WarlockAbilities.CLASS_ABILITY).orElseThrow().param("model_diameter_pixels", 0) > 0;
        check(h, WarlockClassAbility.visualCount(owner) == (modelExpected ? 1 : 0), "One supplied ring display or explicit particle fallback");
        if (modelExpected) check(h, Math.abs(WarlockClassAbility.visualRadius(owner) - 4) < .001, "Visible ring radius matches healing radius");
        owner.setPos(h.absoluteVec(new Vec3(12.5, 1, 6.5))); owner.setHealth(5);
        h.runAfterDelay(24, () -> {
            check(h, WarlockClassAbility.origin(owner).equals(origin), "Owner walking away does not move or cancel rift");
            check(h, near.getHealth() > 5 && mob.getHealth() == 5, "Only friendly Player healed, never PvE Mob");
            check(h, blocked.getHealth() == 5 && outside.getHealth() == 5 && above.getHealth() == 5 && owner.getHealth() == 5,
                    "Walls, radius, height and owner distance respected");
        });
        h.runAfterDelay(310, () -> {
            check(h, !WarlockClassAbility.active(owner) && WarlockClassAbility.visualCount(owner) == 0,
                    "Stationary field and optional ring holder expire together");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 90, environment = "destiny-test:w90_isolated")
    public void glideBoundsDescentCancelsAndCannotRefreshItsAirBudget(GameTestHelper h) {
        ServerPlayer p = player(h, Element.ARC, new Vec3(2.5, 8, 6.5));
        p.setOnGround(false); p.setDeltaMovement(new Vec3(.2, -1, .1));
        boolean flying = p.getAbilities().flying, gravity = p.isNoGravity();
        use(h, p, AbilitySlot.JUMP);
        h.runAfterDelay(2, () -> {
            check(h, WarlockJump.active(p) && p.getDeltaMovement().y >= -.13 && p.getDeltaMovement().y <= 0, "Bounded descent without upward hovering");
            use(h, p, AbilitySlot.JUMP);
            check(h, !WarlockJump.active(p), "Airborne second press cancels");
            p.setDeltaMovement(0, -1, 0);
            check(h, AbilityService.use(p, AbilitySlot.JUMP) == AbilityService.Result.FAILED, "Repeated presses cannot renew air budget");
        });
        h.runAfterDelay(4, () -> {
            check(h, p.getDeltaMovement().y == -1, "Cancelled glide no longer changes velocity");
            p.setOnGround(true); AbilityService.tickPlayer(p);
        });
        h.runAfterDelay(6, () -> { p.setOnGround(false); use(h, p, AbilitySlot.JUMP); });
        h.runAfterDelay(73, () -> {
            check(h, !WarlockJump.active(p), "Glide expires while still airborne");
            check(h, p.getAbilities().flying == flying && p.isNoGravity() == gravity, "Physics flags preserved");
            check(h, AbilityService.use(p, AbilitySlot.JUMP) == AbilityService.Result.FAILED, "Expired budget stays spent until landing");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 180, environment = "destiny-test:w90_isolated")
    public void grenadeCollidesCreatesFiniteFieldAndCannotDamageThroughWall(GameTestHelper h) {
        ServerPlayer p = player(h, Element.ARC);
        // Keep the occluded control's entire body outside the wall, yet inside the real field radius.
        Husk front = enemy(h, new Vec3(5.75, 1, 6.5), 100);
        Husk blocked = enemy(h, new Vec3(8.5, 1, 6.5), 100);
        wall(h, 7, 3, 10);
        check(h, h.getLevel().noCollision(blocked, blocked.getBoundingBox()), "Occluded grenade control does not intersect wall or suffocate");
        aimAt(p, center(front));
        check(h, ray(p, center(front)).getType() == HitResult.Type.MISS && ray(p, center(blocked)).getType() == HitResult.Type.BLOCK,
                "Grenade fixture has a visible body target and an occluded control" + diagnostic(h, p, front, blocked));
        use(h, p, AbilitySlot.GRENADE);
        check(h, SimProjectile.activeCount(p) == 1, "Real grenade projectile emitted");
        check(h, AbilityService.use(p, AbilitySlot.GRENADE) == AbilityService.Result.COOLDOWN, "Repeat input cannot duplicate grenade");
        h.runAfterDelay(25, () -> {
            var fields = WarlockGrenade.fields(p);
            check(h, fields.size() == 1, "One actual collision field exists" + diagnostic(h, p, front, blocked));
            Vec3 origin = fields.getFirst().origin();
            double radius = AbilityRegistry.get(WarlockAbilities.ARC_GRENADE).orElseThrow().param("radius", 3.5);
            String fieldRay = " fieldOrigin=" + origin + " blockedDistance=" + origin.distanceTo(center(blocked))
                    + " fieldRay=" + ray(p, origin, center(blocked)).getType();
            check(h, origin.distanceTo(center(blocked)) < radius,
                    "Occluded control remains inside actual field radius, so distance alone cannot protect it" + fieldRay);
            check(h, ray(p, origin, center(front)).getType() == HitResult.Type.MISS
                            && ray(p, origin, center(blocked)).getType() == HitResult.Type.BLOCK,
                    "Actual field-origin collider ray separates visible and occluded targets" + fieldRay);
            check(h, h.getLevel().noCollision(blocked, blocked.getBoundingBox()), "Control body stays clear of wall" + fieldRay);
            check(h, front.getHealth() < 100, "Visible body actually takes field damage" + diagnostic(h, p, front, blocked));
            check(h, blocked.getHealth() == 100, "Actual field damage cannot cross wall" + diagnostic(h, p, front, blocked));
            check(h, WarlockGrenade.fieldCount(p) == 1 && SimProjectile.activeCount(p) == 0, "Flight transitions into one field");
        });
        h.runAfterDelay(150, () -> {
            check(h, WarlockGrenade.fieldCount(p) == 0 && SimProjectile.activeCount(p) == 0, "Field and projectile both expire");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 50, environment = "destiny-test:w90_isolated")
    public void threePoweredMeleesMakeRealContactsWithoutHittingThroughWalls(GameTestHelper h) {
        ServerPlayer arc = player(h, Element.ARC, new Vec3(2.5, 1, 3.5));
        ServerPlayer solar = player(h, Element.SOLAR, new Vec3(2.5, 1, 7.5));
        ServerPlayer singularity = player(h, Element.VOID, new Vec3(2.5, 1, 11.5));
        Husk a = enemy(h, new Vec3(4.5, 1, 3.5), 100);
        Husk s = enemy(h, new Vec3(5.5, 1, 7.5), 100);
        Husk v = enemy(h, new Vec3(5.5, 1, 11.5), 100);
        Husk hidden = enemy(h, new Vec3(8.5, 1, 7.5), 100);
        wall(h, 7, 1, 13);
        use(h, arc, AbilitySlot.MELEE); use(h, solar, AbilitySlot.MELEE); use(h, singularity, AbilitySlot.MELEE);
        check(h, a.getHealth() < 100 && SimProjectile.activeCount(solar) == 5 && SimProjectile.activeCount(singularity) == 1,
                "Chain contacts, snap sparks and singularity are actual attacks");
        h.runAfterDelay(20, () -> {
            check(h, s.getHealth() < 100 && v.getHealth() < 100 && hidden.getHealth() == 100, "Sparks and singularity hit only their accessible enemies");
            check(h, v.getDeltaMovement().lengthSqr() > 0, "Singularity imparts bounded knockback");
        });
        h.runAfterDelay(42, () -> {
            check(h, SimProjectile.activeCount(solar) == 0 && SimProjectile.activeCount(singularity) == 0, "Finite powered projectile lifetimes");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 310, environment = "destiny-test:w90_isolated")
    public void novaAutomaticallyPreparesReleasesOnceAndCreditsSuperAtWallImpact(GameTestHelper h) {
        ServerPlayer p = player(h, Element.VOID); pumpSuper(h, p);
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.getInventory().setItem(0, WeaponItems.create(WeaponCatalog.find("austringer").orElseThrow()));
        p.getInventory().setItem(1, WeaponItems.create(WeaponCatalog.find("nezarec_s_whisper").orElseThrow()));
        p.getInventory().setItem(2, WeaponItems.create(WeaponCatalog.find("bad_omens").orElseThrow()));
        p.setAttached(AmmoEconomy.METERS, AmmoMeters.EMPTY);
        Husk visible = enemy(h, new Vec3(6, 1, 8.5), 1);
        Husk blocked = enemy(h, new Vec3(8.5, 1, 6.5), 100);
        wall(h, 7, 4, 10);
        Guardians.data(p).setSuperEnergy(1); use(h, p, AbilitySlot.SUPER);
        h.onEachTick(() -> { var session = Guardians.runtime(p).superSession; if (session != null) for (int i = 0; i < 12; i++) session.primary(); });
        h.runAfterDelay(5, () -> check(h, SimProjectile.activeCount(p) == 0 && WarlockSuper.emitted(p) == 0, "Clicks cannot shorten automatic windup"));
        h.runAfterDelay(17, () -> check(h, WarlockSuper.emitted(p) == 1 && SimProjectile.activeCount(p) == 1, "Automatic single release despite repeated primary"));
        h.runAfterDelay(42, () -> {
            check(h, !visible.isAlive() && blocked.getHealth() == 100, "Wall impact blast damages near side only");
            check(h, AmmoEconomy.meters(p).equals(AmmoGeneration.SUPER.gains(false)), "Real final blow recorded as SUPER, not generic ABILITY");
            check(h, !AbilityService.inSuper(p) && SimProjectile.activeCount(p) == 0, "Nova completes automatically after its one blast");
            check(h, WarlockSuper.vortexCount(p) == 1 && !SuperCamera.active(p), "Post-impact Vortex survives the one-shot cast without roaming camera");
            Husk late = enemy(h, new Vec3(5.5, 1, 7.5), 100);
            h.runAfterDelay(22, () -> {
                check(h, late.getHealth() < 100 && blocked.getHealth() == 100,
                        "Independent Vortex damages a late arrival with collider LOS after Nova session ends" + diagnostic(h, p, late, blocked));
            });
        });
        h.runAfterDelay(250, () -> {
            check(h, WarlockSuper.vortexCount(p) == 0 && !AbilityService.inSuper(p), "Post-impact Vortex expires independently and never becomes a roaming super");
            Guardians.data(p).setCooldown(AbilitySlot.SUPER, 0);
            Guardians.data(p).setSuperEnergy(1); use(h, p, AbilitySlot.SUPER);
        });
        h.runAfterDelay(292, () -> {
            check(h, WarlockSuper.vortexCount(p) == 1 && !AbilityService.inSuper(p), "Second post-impact field exists after its cast ends");
            Guardians.data(p).setLoadout(GuardianClass.WARLOCK, WarlockAbilities.preset(Element.ARC));
        });
        h.runAfterDelay(295, () -> {
            check(h, WarlockSuper.vortexCount(p) == 0, "Subclass epoch change revokes a detached post-impact Vortex");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void stormtranceChainHasTargetCapLosAndFiniteChannelWindow(GameTestHelper h) {
        ServerPlayer p = player(h, Element.ARC); pumpSuper(h, p);
        Husk first = enemy(h, new Vec3(4.5, 1, 6.5), 100);
        Husk second = enemy(h, new Vec3(4.5, 1, 8), 100);
        Husk third = enemy(h, new Vec3(4.5, 1, 9.5), 100);
        Husk fourth = enemy(h, new Vec3(4.5, 1, 11), 100);
        Husk blocked = enemy(h, new Vec3(6.5, 1, 6.5), 100);
        wall(h, 5, 2, 13);
        aimAt(p, center(first));
        check(h, ray(p, center(first)).getType() == HitResult.Type.MISS && ray(p, center(blocked)).getType() == HitResult.Type.BLOCK,
                "Storm fixture aim and occlusion are native collider facts" + diagnostic(h, p, first, blocked));
        Guardians.data(p).setSuperEnergy(1); use(h, p, AbilitySlot.SUPER);
        check(h, kim.biryeong.destiny.camera.SuperCamera.movementBlocked(p), "Cast locks preparation movement");
        check(h, AbilityService.use(p, AbilitySlot.JUMP) == AbilityService.Result.BUSY, "Cast locks air-jump ability input");
        h.runAfterDelay(38, () -> {
            check(h, first.getHealth() == 100 && second.getHealth() == 100 && third.getHealth() == 100,
                    "Stormtrance does not attack before primary input");
            for (int i = 0; i < 20; i++) Guardians.runtime(p).superSession.primary();
        });
        h.runAfterDelay(65, () -> {
            check(h, first.getHealth() < 100 && second.getHealth() < 100 && third.getHealth() < 100, "Channel makes a real three-enemy chain" + diagnostic(h, p, first, second, third, fourth, blocked));
            check(h, fourth.getHealth() == 100 && blocked.getHealth() == 100, "Hop count and per-hop LOS enforced" + diagnostic(h, p, first, second, third, fourth, blocked));
            float before = first.getHealth();
            h.runAfterDelay(8, () -> { check(h, first.getHealth() == before, "No indefinitely running channel without renewed input"); h.succeed(); });
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 85, environment = "destiny-test:w90_isolated")
    public void daybreakUsesDelayedCollidingProjectileAndRejectsDuplicateClicks(GameTestHelper h) {
        ServerPlayer p = player(h, Element.SOLAR); pumpSuper(h, p);
        Husk front = enemy(h, new Vec3(7, 1, 8), 100);
        Husk blocked = enemy(h, new Vec3(9.5, 1, 6.5), 100);
        wall(h, 8, 3, 10);
        check(h, h.getLevel().noCollision(blocked, blocked.getBoundingBox()), "Occluded sword control does not intersect wall or suffocate");
        aimAt(p, center(blocked));
        check(h, ray(p, center(blocked)).getType() == HitResult.Type.BLOCK,
                "Daybreak aims into the actual wall rather than above the control" + diagnostic(h, p, front, blocked));
        // Zero-gravity sword follows this ray; derive the near-side contact independently of product impactPoint().
        var wallHit = (net.minecraft.world.phys.BlockHitResult) ray(p, center(blocked));
        var face = wallHit.getDirection();
        Vec3 splashOrigin = wallHit.getLocation().add(face.getStepX() * .06, face.getStepY() * .06, face.getStepZ() * .06);
        double radius = AbilityRegistry.get(WarlockAbilities.SOLAR_SUPER).orElseThrow().param("radius", 2.5);
        check(h, splashOrigin.distanceTo(center(front)) < radius && splashOrigin.distanceTo(center(blocked)) < radius,
                "Both controls lie within near-side sword splash radius; occlusion is the protection");
        check(h, ray(p, splashOrigin, center(front)).getType() == HitResult.Type.MISS
                        && ray(p, splashOrigin, center(blocked)).getType() == HitResult.Type.BLOCK,
                "Near-side sword contact ray is clear to front, blocked to control");
        Guardians.data(p).setSuperEnergy(1); use(h, p, AbilitySlot.SUPER);
        h.runAfterDelay(10, () -> {
            for (int i = 0; i < 20; i++) Guardians.runtime(p).superSession.primary();
            check(h, WarlockSuper.emitted(p) == 0, "Cast cannot be interrupted by early attacks");
        });
        h.runAfterDelay(35, () -> { for (int i = 0; i < 20; i++) Guardians.runtime(p).superSession.primary(); });
        h.runAfterDelay(36, () -> check(h, SimProjectile.activeCount(p) == 0, "Source attack windup precedes sword contact"));
        h.runAfterDelay(60, () -> {
            check(h, WarlockSuper.emitted(p) == 1 && front.getHealth() < 100 && blocked.getHealth() == 100,
                    "One real sword hits wall and respects splash LOS despite repeated clicks splashOrigin=" + splashOrigin
                            + " blockedDistance=" + splashOrigin.distanceTo(center(blocked))
                            + " splashRay=" + ray(p, splashOrigin, center(blocked)).getType() + diagnostic(h, p, front, blocked));
            check(h, h.getLevel().noCollision(blocked, blocked.getBoundingBox()), "Sword control body stays clear of wall");
            check(h, SimProjectile.activeCount(p) == 0, "Impacted sword is destroyed");
            // Exercise real session natural expiry while its second sword is still in flight.
            // Only this fake session advances; do not double-tick global projectiles or other fixtures.
            SimProjectile ordinary = SimProjectile.launch(p, p.position().add(0, 5, 0), Vec3.ZERO, 0, 80,
                    new ItemStack(Items.SNOWBALL), .2f, Element.KINETIC.color(), hit -> {});
            Guardians.runtime(p).superSession.primary();
            for (int i = 0; i < 12; i++) AbilityService.tickPlayer(p);
            check(h, SimProjectile.activeCount(p) == 2 && !ordinary.isDone(), "Second real sword and unrelated ordinary flight coexist");
            for (int i = 0; i < 620 && AbilityService.inSuper(p); i++) AbilityService.tickPlayer(p);
            check(h, !AbilityService.inSuper(p) && SimProjectile.activeCount(p) == 1 && !ordinary.isDone(),
                    "Natural super end cancels its sword visual without deleting same-owner ordinary emission");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 35, environment = "destiny-test:w90_isolated")
    public void lifecycleRevokesEpochsAndCleanupPreservesOtherOwnersEffectsAndInventory(GameTestHelper h) {
        ServerPlayer a = player(h, Element.ARC), b = player(h, Element.SOLAR, new Vec3(10.5, 1, 6.5));
        a.setNoGravity(true);
        a.addEffect(new MobEffectInstance(MobEffects.SPEED, 1000, 1));
        a.getInventory().setItem(0, new ItemStack(Items.DIAMOND, 3));
        rearmRift(h, a); rearmRift(h, b);
        // Real visual holders for both owners: cleanup must detach only the retired owner.
        AbilityRegistry.get(WarlockAbilities.ARC_GRENADE).orElseThrow().activate(a);
        AbilityRegistry.get(WarlockAbilities.ARC_GRENADE).orElseThrow().activate(b);
        SimProjectile ordinary = SimProjectile.launch(a, a.position().add(0, 5, 0), Vec3.ZERO, 0, 80,
                new ItemStack(Items.SNOWBALL), .2f, Element.KINETIC.color(), hit -> {});
        check(h, SimProjectile.activeCount(a) == 2 && SimProjectile.activeCount(b) == 1, "Owned and unrelated projectile visuals allocated");
        WarlockAbilities.cleanup(a); WarlockAbilities.cleanup(a);
        check(h, WarlockClassAbility.visualCount(a) == 0, "Owned rift display removed by cleanup");
        check(h, SimProjectile.activeCount(a) == 1 && !ordinary.isDone() && SimProjectile.activeCount(b) == 1,
                "Idempotent cleanup discards only its owned visual, preserves same-owner ordinary emission and other owner");
        rearmRift(h, a);
        h.runAfterDelay(1, () -> Guardians.data(a).setGuardianClass(GuardianClass.HUNTER));
        h.runAfterDelay(3, () -> {
            check(h, !WarlockClassAbility.active(a) && WarlockClassAbility.active(b), "Class change revokes only that owner");
            rearmRift(h, a);
            Guardians.data(a).setLoadout(GuardianClass.WARLOCK, WarlockAbilities.preset(Element.VOID));
        });
        h.runAfterDelay(5, () -> {
            check(h, !WarlockClassAbility.active(a), "Subclass change revokes stationary field");
            rearmRift(h, a);
            var other = h.getLevel().getServer().getLevel(h.getLevel().dimension().equals(Level.NETHER) ? Level.OVERWORLD : Level.NETHER);
            check(h, other != null, "Dimension fixture available"); a.setServerLevel(other);
        });
        h.runAfterDelay(7, () -> {
            check(h, !WarlockClassAbility.active(a), "Dimension change revokes old-world field");
            a.setServerLevel(h.getLevel()); rearmRift(h, a); a.setHealth(0);
        });
        h.runAfterDelay(9, () -> {
            check(h, !WarlockClassAbility.active(a) && WarlockClassAbility.active(b), "Death and prior revocations preserve other owner's rift");
            WarlockAbilities.cleanup(a); WarlockAbilities.cleanup(a);
            WarlockAbilities.cleanup(b); WarlockAbilities.cleanup(b);
            check(h, !WarlockClassAbility.active(b) && a.isNoGravity() && !a.getAbilities().flying, "Cleanup is idempotent and does not own physics flags");
            check(h, a.hasEffect(MobEffects.SPEED) && a.getInventory().getItem(0).is(Items.DIAMOND)
                    && a.getInventory().getItem(0).getCount() == 3, "Unrelated potion and inventory retained");
            h.succeed();
        });
    }
}
