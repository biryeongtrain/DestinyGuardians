package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.UUID;

/** W77 paid production hitscan final blows on W66's existing 16x8x12 floor.
 * No registration, injected deaths, reflection, native-client claims or rewritten clocks.
 * Token API contract tests use real paid precision corpses; they do not claim in-flight native coverage.
 */
public final class WeaponDragonflyW77GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String GLOBAL = "destiny-test:w90_w77_global";
    private static final String GUN = "distant_relation";
    private static final float HP = 1000;
    private static final float EPS = .003f;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static void hp(GameTestHelper h, LivingEntity target, float expected, String message) {
        check(h, Math.abs(target.getHealth() - expected) < EPS,
                message + ": expected HP " + expected + ", got " + target.getHealth());
    }

    private static void bounded(GameTestHelper h, Entity entity) {
        var o = h.absoluteVec(Vec3.ZERO);
        var b = entity.getBoundingBox();
        check(h, b.minX > o.x && b.maxX < o.x + 16 && b.minY > o.y && b.maxY < o.y + 8
                        && b.minZ > o.z && b.maxZ < o.z + 12,
                "Whole entity AABB stays strictly inside the existing 16x8x12 floor");
    }

    private static ServerPlayer player(GameTestHelper h, Vec3 position) {
        var p = TestPlayers.hunter(h, Element.SOLAR, position, -90, 0, "W77_" + UUID.randomUUID().toString().substring(0,8));
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setOnGround(true);
        bounded(h, p);
        TestCleanup.register(h, () -> {
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            if (p.level().players().contains(p))
                p.level().removePlayerImmediately(p, Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(p);
        });
        return p;
    }

    private static ServerPlayer player(GameTestHelper h) {
        return player(h, new Vec3(2.5, 1, 6));
    }

    private static WeaponProfile profile(ItemStack stack) {
        return WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow());
    }

    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, profile(stack));
    }

    private static ItemStack equip(GameTestHelper h, ServerPlayer p, boolean selected) {
        var e = WeaponCatalog.find(GUN).orElseThrow();
        var f = WeaponProfile.forEntry(e);
        check(h, f.mode() == WeaponProfile.Mode.HITSCAN && f.chargeTicks() == 0
                        && f.burst() == 1 && f.pellets() == 1,
                "Official Distant Relation fixture is one immediate hitscan round");
        var gun = WeaponItems.create(e);
        WeaponItems.save(gun, new WeaponMagazine(f, f.magazine(), f.infiniteReserve() ? 0 : 3));
        var before = ammo(gun);
        check(h, DragonflyProfile.rolls().stream().anyMatch(r -> r.id().equals(GUN)
                        && r.hash() == 2034817450L && r.socket() == 4
                        && r.perkHash() == DragonflyProfile.HASH && r.plugSetHash() == 3824767299L),
                "Distant Relation uses its exact official Dragonfly socket");
        if (selected) check(h, WeaponPerks.select(gun, "dragonfly"), "Select Dragonfly through the official pool");
        check(h, WeaponPerks.selected(gun, DragonflyProfile.ID).isPresent() == selected
                        && ammo(gun).rounds() == before.rounds() && ammo(gun).reserve() == before.reserve(),
                "Only explicit official selection enables Dragonfly and selection preserves ammunition");
        int slot = WeaponCharacteristics.of(e).slot().hotbar();
        p.getInventory().setItem(slot, gun);
        p.getInventory().setSelectedSlot(slot);
        kim.biryeong.destiny.weapon.WeaponAccuracy.setAirborneBonus(gun, 100);
        WeaponRuntime.tickPlayer(p);
        TestPlayers.drain(p);
        return gun;
    }

    private static <T extends Mob> T stationary(GameTestHelper h, T mob, float health) {
        mob.setNoAi(true);
        mob.setNoGravity(true);
        mob.setPersistenceRequired();
        mob.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP);
        mob.getAttribute(Attributes.ARMOR).setBaseValue(0);
        mob.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        mob.setHealth(health);
        TestCleanup.register(h, mob::discard);
        bounded(h, mob);
        return mob;
    }

    private static Husk target(GameTestHelper h, double x, double y, double z, float health) {
        return stationary(h, h.spawn(EntityTypes.HUSK, new Vec3(x, y, z)), health);
    }

    private static Husk primary(GameTestHelper h, ServerPlayer p, boolean precision, float health) {
        var target = target(h, 8.5, precision ? 1 : 1.8, 6, health);
        var b = target.getBoundingBox();
        var from = p.getEyePosition();
        var hit = b.clip(from, from.add(20, 0, 0)).orElseThrow();
        check(h, precision ? from.y >= b.maxY - b.getYsize() * .25 && from.y < b.maxY
                        : from.y > b.minY && from.y < b.maxY - b.getYsize() * .25,
                "Horizontal ray crosses the intended real precision/body geometry");
        check(h, WeaponPrecision.critical(target, from, hit,
                        WeaponAiming.ballistics(p, WeaponItems.entry(p.getMainHandItem()).orElseThrow()).precision()) == precision,
                "Production weakspot classifier agrees with the primary fixture");
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
        p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0);
        WeaponAiming.tick(p);
        var gun = p.getMainHandItem();
        int rounds = ammo(gun).rounds(), reserve = ammo(gun).reserve();
        check(h, WeaponRuntime.beginUse(p) && ammo(gun).rounds() == rounds - 1
                        && ammo(gun).reserve() == reserve,
                "Accepted production shot pays exactly one loaded round, with no reserve cost or reward");
        WeaponRuntime.releaseUse(p, gun);
    }

    private static void dead(GameTestHelper h, LivingEntity target) {
        check(h, target.isDeadOrDying() && target.getHealth() == 0,
                "Actual paid production hit caused the primary final blow synchronously");
    }

    /** Independent contract oracle; intentionally does not call WeaponDragonfly.damageAt. */
    private static float expected(Vec3 center, LivingEntity target) {
        double distance = center.distanceTo(target.getBoundingBox().getCenter());
        return distance > 4.5 ? 0 : 10 * (float) Math.max(.3, 1 - distance / 4.5);
    }

    private static void blasted(GameTestHelper h, Vec3 center, LivingEntity target) {
        float amount = expected(center, target);
        check(h, amount > 0, "Positive witness is within the 4.5-block center radius");
        hp(h, target, HP - amount, "Real area HP damage follows fixed 10 HP linear falloff with a .3 floor");
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void paidPrecisionFinalBlowImmediatelyDamagesAreaWithExactFalloffAndRadius(GameTestHelper h) {
        var p = player(h); equip(h, p, true);
        check(h, DragonflyProfile.ID.equals("dragonfly") && DragonflyProfile.HASH == 2848615171L
                        && DragonflyProfile.radius() == 4.5 && DragonflyProfile.damage() == 10
                        && Math.abs(DragonflyProfile.falloffFloor() - .3f) < .00001f,
                "Pinned perk identity and explicit local Minecraft HP tuning");
        var corpse = primary(h, p, true, 1);
        var near = target(h, 8.5, 1, 7.5, HP);
        var middle = target(h, 8.5, 1, 9, HP);
        var edge = target(h, 12.9, 1, 6, HP);
        var outside = target(h, 13.1, 1, 6, HP);
        var aboveInside = target(h, 8.5, 4, 8.5, HP);
        var aboveOutside = target(h, 11, 5, 6, HP);
        var center = corpse.getBoundingBox().getCenter();
        check(h, expected(center, outside) == 0 && expected(center, aboveOutside) == 0,
                "Outside witnesses test spherical distance even when their boxes/horizontal distance enter the broad phase");
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); dead(h, corpse);
            check(h, center.distanceToSqr(corpse.getBoundingBox().getCenter()) < 1e-10,
                    "Final blow preserves the measured corpse bounding-box center");
            blasted(h, center, near); blasted(h, center, middle); blasted(h, center, edge);
            blasted(h, center, aboveInside);
            check(h, near.getHealth() < middle.getHealth() && middle.getHealth() < edge.getHealth(),
                    "Observed HP separates near, linear-middle and floor damage");
            hp(h, edge, HP - 3, "In-radius edge retains the authored 3 HP floor");
            hp(h, outside, HP, "Just-outside center is safe despite an intersecting entity AABB");
            hp(h, aboveOutside, HP, "Vertical distance also excludes entities outside the sphere");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void paidBodyFinalBlowDoesNotExplode(GameTestHelper h) {
        var p = player(h); equip(h, p, true);
        var corpse = primary(h, p, false, 1);
        var witness = target(h, 8.5, 1.8, 8, HP);
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); dead(h, corpse);
            hp(h, witness, HP, "Selected Dragonfly gives no area HP damage on an actual body kill");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void paidNonlethalPrecisionHitDoesNotExplode(GameTestHelper h) {
        var p = player(h); equip(h, p, true);
        var primary = primary(h, p, true, HP);
        var witness = target(h, 8.5, 1, 8, HP);
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p);
            check(h, primary.isAlive() && primary.getHealth() < HP, "Production precision ray causes positive nonlethal HP loss");
            hp(h, witness, HP, "Precision damage without a final blow gives no explosion");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void paidPrecisionFinalBlowWithoutSelectedPerkDoesNotExplode(GameTestHelper h) {
        var p = player(h); equip(h, p, false);
        var corpse = primary(h, p, true, 1);
        var witness = target(h, 8.5, 1, 8, HP);
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); dead(h, corpse);
            hp(h, witness, HP, "Official eligibility alone does not enable an unselected perk");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void solidWallStopsAreaDamageWhileUnobstructedEnemyLosesHp(GameTestHelper h) {
        var p = player(h); equip(h, p, true);
        var corpse = primary(h, p, true, 1);
        var hidden = target(h, 8.5, 1, 8.5, HP);
        var open = target(h, 8.5, 1, 3.5, HP);
        for (int x = 7; x <= 9; x++)
            for (int y = 1; y <= 4; y++) h.setBlock(x, y, 7, Blocks.STONE);
        check(h, h.getLevel().noCollision(hidden, hidden.getBoundingBox()), "Hidden enemy is clear of suffocating wall blocks");
        var center = corpse.getBoundingBox().getCenter();
        var wall = h.getLevel().clip(new ClipContext(center, hidden.getBoundingBox().getCenter(),
                ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
        check(h, wall.getType() == HitResult.Type.BLOCK, "Actual collider separates explosion center and hidden enemy");
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); dead(h, corpse);
            hp(h, hidden, HP, "Explosion does not damage through a solid collider");
            blasted(h, center, open);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, environment = GLOBAL, maxTicks = 55)
    public void worldIndexedUnalliedPlayerAndNearbyShooterAreSpared(GameTestHelper h) {
        var p = player(h, new Vec3(5, 1, 6)); equip(h, p, true);
        var victim = player(h, new Vec3(8.5, 1, 8));
        h.getLevel().addNewPlayer(victim);
        var corpse = primary(h, p, true, 1);
        var enemy = target(h, 8.5, 1, 4, HP);
        var center = corpse.getBoundingBox().getCenter();
        check(h, !p.isAlliedTo(victim) && !Combat.isEnemy(p, victim)
                        && center.distanceTo(p.getBoundingBox().getCenter()) < 4.5
                        && center.distanceTo(victim.getBoundingBox().getCenter()) < 4.5,
                "Both survival players are in blast range and PvP witness is independently unallied");
        check(h, h.getLevel().getEntitiesOfClass(LivingEntity.class,
                        corpse.getBoundingBox().inflate(4.5)).contains(victim),
                "Player exclusion is exercised by a real world-indexed spatial-query candidate");
        float ownerHp = p.getHealth(), victimHp = victim.getHealth();
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); dead(h, corpse);
            blasted(h, center, enemy);
            hp(h, p, ownerHp, "Shooter receives no self-damage");
            hp(h, victim, victimHp, "Unallied world-present survival player receives no area damage");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, environment = "destiny-test:w90_w77_allied", maxTicks = 55)
    public void alliedHostileAndUnownedTameAreSparedWhileLegalEnemyIsDamaged(GameTestHelper h) {
        var p = player(h); equip(h, p, true);
        var corpse = primary(h, p, true, 1);
        var ally = target(h, 8.5, 1, 8, HP);
        var enemy = target(h, 8.5, 1, 4, HP);
        var tame = stationary(h, h.spawn(EntityTypes.WOLF, new Vec3(10.5, 1, 6)), HP);
        tame.setTame(true, false);
        var scoreboard = h.getLevel().getScoreboard();
        String name = "w77_" + UUID.randomUUID().toString().substring(0, 8);
        var previousTeam = scoreboard.getPlayersTeam(p.getScoreboardName());
        var team = scoreboard.addPlayerTeam(name);
        TestCleanup.register(h, () -> {
            if (scoreboard.getPlayerTeam(name) == team) scoreboard.removePlayerTeam(team);
            if (previousTeam != null && scoreboard.getPlayerTeam(previousTeam.getName()) == previousTeam)
                scoreboard.addPlayerToTeam(p.getScoreboardName(), previousTeam);
        });
        scoreboard.addPlayerToTeam(p.getScoreboardName(), team);
        scoreboard.addPlayerToTeam(ally.getScoreboardName(), team);
        check(h, !Combat.isEnemy(p, ally) && !Combat.isEnemy(p, tame) && p.isAlliedTo(ally)
                        && tame.isTame() && !p.isAlliedTo(tame) && !p.isAlliedTo(enemy),
                "Combat excludes the allied hostile and independently tamed mob before weapon-specific filtering");
        var center = corpse.getBoundingBox().getCenter();
        check(h, expected(center, ally) > 0 && expected(center, tame) > 0, "Excluded mobs are in real blast range");
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); dead(h, corpse);
            blasted(h, center, enemy);
            hp(h, ally, HP, "Scoreboard-allied hostile is spared");
            hp(h, tame, HP, "Unowned tame is spared independently of scoreboard alliance");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void explosionAndDeniedDuplicateInputSpendOnlyTheOriginalPaidRound(GameTestHelper h) {
        var p = player(h); var gun = equip(h, p, true);
        h.onEachTick(() -> { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); });
        var corpse = primary(h, p, true, 1);
        var first = target(h, 8.5, 1, 8, HP);
        var second = target(h, 8.5, 1, 4, HP);
        int rounds = ammo(gun).rounds(), reserve = ammo(gun).reserve();
        var center = corpse.getBoundingBox().getCenter();
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); dead(h, corpse);
            blasted(h, center, first); blasted(h, center, second);
            var paid = gun.copy();
            check(h, !WeaponRuntime.beginUse(p), "Same-tick duplicate trigger cannot bypass the paid shot cadence");
            WeaponRuntime.releaseUse(p, gun);
            check(h, ItemStack.matches(paid, gun), "Denied input changes no serialized ammunition or trait state");
            float firstHp = first.getHealth(), secondHp = second.getHealth();
            h.runAfterDelay(3, () -> {
                hp(h, first, firstHp, "No timer repeats the synchronous area damage");
                hp(h, second, secondHp, "No deferred extra blast hits another witness");
                check(h, ammo(gun).rounds() == rounds - 1 && ammo(gun).reserve() == reserve
                                && ItemStack.matches(paid, gun),
                        "One shot with several blast victims spends one round total and grants no free ammunition");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 65, environment = "destiny-test:w90_isolated")
    public void secondaryFinalBlowCannotRecursivelyExplodeIntoAnOutsideWitness(GameTestHelper h) {
        var p = player(h); var gun = equip(h, p, true);
        h.onEachTick(() -> { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); });
        var corpse = primary(h, p, true, 1);
        var secondary = target(h, 11.5, 1, 6, 1);
        var outside = target(h, 14, 1, 6, HP);
        var center = corpse.getBoundingBox().getCenter();
        check(h, expected(center, secondary) > 1 && expected(center, outside) == 0
                        && expected(secondary.getBoundingBox().getCenter(), outside) > 0,
                "Blast kills secondary; outside witness is only in a hypothetical recursive blast's range");
        int rounds = ammo(gun).rounds(), reserve = ammo(gun).reserve();
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); dead(h, corpse); dead(h, secondary);
            hp(h, outside, HP, "Actual secondary final blow does not recursively detonate");
            h.runAfterDelay(3, () -> {
                hp(h, outside, HP, "No deferred chain follows the secondary death");
                check(h, ammo(gun).rounds() == rounds - 1 && ammo(gun).reserve() == reserve,
                        "Two real final blows still cost only the one accepted round");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void repeatedCallbackForOneTokenAndRealPrecisionCorpseDetonatesOnlyOnce(GameTestHelper h) {
        var p = player(h); var gun = equip(h, p, true);
        // A separate emission-token contract fixture. Production captures its own token internally.
        var token = WeaponDragonfly.capture(p);
        check(h, token != WeaponDragonfly.Token.NONE, "Selected official weapon captures a valid source token");
        var corpse = primary(h, p, true, 1);
        var productionWitness = target(h, 8.5, 1, 8, HP);
        var center = corpse.getBoundingBox().getCenter();
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); dead(h, corpse);
            blasted(h, center, productionWitness);
            // Create this witness AFTER production's immediate blast, so only this explicit token can hit it.
            var callbackWitness = target(h, 8.5, 1, 4, HP);
            var paid = gun.copy();
            WeaponDragonfly.killed(p, token, corpse, true);
            blasted(h, center, callbackWitness);
            float once = callbackWitness.getHealth(), otherOnce = productionWitness.getHealth();
            WeaponDragonfly.killed(p, token, corpse, true);
            WeaponDragonfly.killed(p, token, corpse, true);
            hp(h, callbackWitness, once, "Same token and real corpse consume at most one detonation");
            hp(h, productionWitness, otherOnce, "Duplicate callbacks cannot damage any prior blast witness again");
            check(h, ItemStack.matches(paid, gun), "Token callback deduplication never mints or spends ammunition");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 150, environment = "destiny-test:w90_isolated")
    public void capturedTokenRejectsRemovedTraitDroppedSourceAndEqualStackReplacement(GameTestHelper h) {
        invalidTokenCase(h, 0);
    }

    private static void invalidTokenCase(GameTestHelper h, int index) {
        String reason = new String[]{"trait", "dropped", "replaced"}[index];
        var p = player(h); var gun = equip(h, p, true);
        var token = WeaponDragonfly.capture(p);
        check(h, token != WeaponDragonfly.Token.NONE, "Capture selected original source before the paid shot: " + reason);
        var corpse = primary(h, p, true, 1);
        var productionWitness = target(h, 8.5, 1, 8, HP);
        var center = corpse.getBoundingBox().getCenter();
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); dead(h, corpse);
            blasted(h, center, productionWitness);
            // This witness was absent from the real blast. Only an incorrectly accepted callback can damage it.
            var fresh = target(h, 8.5, 1, 4, HP);
            int rounds = ammo(gun).rounds(), reserve = ammo(gun).reserve();
            int slot = p.getInventory().getSelectedSlot();
            ItemStack replacement = ItemStack.EMPTY;
            if (reason.equals("trait")) {
                check(h, WeaponPerks.clear(gun) && WeaponPerks.selected(gun, DragonflyProfile.ID).isEmpty(),
                        "Remove the captured original's selected trait");
            } else if (reason.equals("dropped")) {
                p.getInventory().setItem(slot, ItemStack.EMPTY);
                var dropped = new ItemEntity(h.getLevel(), p.getX(), p.getY(), p.getZ(), gun);
                TestCleanup.register(h, dropped::discard);
                check(h, h.getLevel().addFreshEntity(dropped), "Original source becomes a real world item outside its owner's inventory");
                bounded(h, dropped);
                check(h, dropped.getItem() == gun, "Dropped entity retains the original source stack identity");
            } else {
                // Inventory stow clears ADS/fire presentation on the outgoing stack. Copy
                // only after that real transition so equality isolates identity, not cosmetics.
                p.getInventory().setItem(slot, ItemStack.EMPTY);
                replacement = gun.copy();
                p.getInventory().setItem(slot, replacement);
                check(h, p.getMainHandItem() != gun && ItemStack.matches(gun, p.getMainHandItem())
                                && WeaponPerks.selected(p.getMainHandItem(), DragonflyProfile.ID).isPresent(),
                        "Equal serialized replacement retains the perk but is not the captured source object");
            }
            if (!reason.equals("trait")) {
                for (int i = 0; i < p.getInventory().getContainerSize(); i++)
                    check(h, p.getInventory().getItem(i) != gun, "Original source is no longer owned: " + reason);
            }
            var unchangedSource = gun.copy();
            var unchangedReplacement = replacement.copy();
            float previousHp = productionWitness.getHealth();
            WeaponDragonfly.killed(p, token, corpse, true);
            WeaponDragonfly.killed(p, token, corpse, true);
            hp(h, fresh, HP, "Invalid original source cannot splash a fresh witness: " + reason);
            hp(h, productionWitness, previousHp, "Invalid callback cannot hit a prior production witness: " + reason);
            check(h, ammo(gun).rounds() == rounds && ammo(gun).reserve() == reserve
                            && ItemStack.matches(unchangedSource, gun)
                            && ItemStack.matches(unchangedReplacement, replacement),
                    "Denied attribution callbacks preserve both source and replacement ammunition: " + reason);
            corpse.discard(); productionWitness.discard(); fresh.discard();
            if (index == 2) h.succeed();
            else invalidTokenCase(h, index + 1);
        });
    }

    @GameTest(structure = FLOOR, environment = GLOBAL, maxTicks = 55)
    public void stowedOriginalTokenKeepsSolarSplashAndAmmoWithArcWeaponHeld(GameTestHelper h) {
        var p = player(h); var gun = equip(h, p, true);
        var ear = player(h, new Vec3(2.5, 1, 3));
        h.getLevel().addNewPlayer(ear);
        var token = WeaponDragonfly.capture(p);
        check(h, token != WeaponDragonfly.Token.NONE, "Capture original Solar source before the real paid shot");
        var corpse = primary(h, p, true, 1);
        var productionWitness = target(h, 8.5, 1, 8, HP);
        var center = corpse.getBoundingBox().getCenter();
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); dead(h, corpse);
            blasted(h, center, productionWitness);
            var fresh = target(h, 8.5, 1, 4, HP);
            int sourceRounds = ammo(gun).rounds(), sourceReserve = ammo(gun).reserve();
            int slot = p.getInventory().getSelectedSlot();
            p.getInventory().setItem(slot, ItemStack.EMPTY);
            p.getInventory().setItem(9, gun);
            var arcEntry = WeaponCatalog.find("long_arm").orElseThrow();
            var arc = WeaponItems.create(arcEntry);
            var arcProfile = WeaponProfile.forEntry(arcEntry);
            WeaponItems.save(arc, new WeaponMagazine(arcProfile, arcProfile.magazine(), 0));
            check(h, WeaponPerks.select(arc, DragonflyProfile.ID), "Held Arc comparison weapon also has official Dragonfly");
            p.getInventory().setItem(slot, arc);
            WeaponRuntime.tickPlayer(p);
            check(h, p.getInventory().getItem(9) == gun && p.getMainHandItem() == arc
                            && WeaponCharacteristics.of(WeaponItems.entry(gun).orElseThrow()).damage() == WeaponCharacteristics.Damage.SOLAR
                            && WeaponCharacteristics.of(arcEntry).damage() == WeaponCharacteristics.Damage.ARC,
                    "Original source stays owned by identity while a different selected Arc weapon is held");
            var savedSource = gun.copy(); var savedArc = arc.copy();
            TestPlayers.drain(ear); // Exclude the real shot's first blast and weapon/handling sounds.
            WeaponDragonfly.killed(p, token, corpse, true);
            blasted(h, center, fresh);
            var sounds = TestPlayers.outbound(ear).stream().filter(ClientboundSoundPacket.class::isInstance)
                    .map(ClientboundSoundPacket.class::cast).toList();
            check(h, sounds.stream().filter(sound -> sound.getSound().value().location().toString()
                                    .equals("destiny:hunter.solar.grenade.impact")).count() == 1
                            && sounds.stream().noneMatch(sound -> sound.getSound().value().location().toString()
                                    .equals("destiny:hunter.arc.grenade.impact")
                                    || sound.getSound().value().location().toString().equals("destiny:hunter.void.grenade.impact")),
                    "Fresh callback queues original Solar splash audio rather than adopting the currently held Arc element");
            float once = fresh.getHealth(), previousOnce = productionWitness.getHealth();
            WeaponDragonfly.killed(p, token, corpse, true);
            hp(h, fresh, once, "Stowing retains attribution but cannot detonate the same corpse twice");
            hp(h, productionWitness, previousOnce, "Duplicate stowed callback cannot repeat damage on any witness");
            check(h, TestPlayers.outbound(ear).stream().noneMatch(packet -> packet instanceof ClientboundSoundPacket sound
                            && sound.getSound().value().location().toString().equals("destiny:hunter.solar.grenade.impact")),
                    "Consumed source/corpse pair cannot replay its Solar splash sound");
            check(h, ammo(gun).rounds() == sourceRounds && ammo(gun).reserve() == sourceReserve
                            && ItemStack.matches(savedSource, gun) && ItemStack.matches(savedArc, arc),
                    "Stowed source callback and its duplicate preserve the paid original and held weapon ammo/traits");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 85, environment = "destiny-test:w90_isolated")
    public void openSideAttachedShulkerUsesActualBoxCenterInsideBlastRadius(GameTestHelper h) {
        var p = player(h); var gun = equip(h, p, true);
        h.onEachTick(() -> { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); });
        var corpse = primary(h, p, true, 1);
        var center = corpse.getBoundingBox().getCenter();
        // Attach east, opening west toward the blast. The support lies beyond the target, clear of blast LOS.
        h.setBlock(13, 1, 8, Blocks.STONE);
        var shulker = stationary(h, h.spawn(EntityTypes.SHULKER, new Vec3(12.5, 1, 8.5)), HP);
        try {
            var server = h.getLevel().getServer();
            // Verified in cached 26.3 javap: setRawPeekAmount(int) is private; save-data keys are Peek/AttachFace.
            // Loading Peek changes synced data; normal world ticks settle the expanding physical AABB.
            check(h, server.getCommands().getDispatcher().execute(
                            "data merge entity " + shulker.getUUID() + " {Peek:100b,AttachFace:5b}",
                            server.createCommandSourceStack().withEntity(shulker)) == 1,
                    "Vanilla save-data command opens the real east-attached Shulker without reflection");
        } catch (com.mojang.brigadier.exceptions.CommandSyntaxException failure) {
            throw new AssertionError("26.3 Shulker open fixture command", failure);
        }
        h.runAfterDelay(24, () -> {
            bounded(h, shulker);
            check(h, shulker.getAttachFace() == Direction.EAST && shulker.getClientPeekAmount(1) > .99f
                            && shulker.getBoundingBox().getXsize() > 1.9,
                    "Normal world ticks settle the real fully open horizontal Shulker bounding box");
            var actual = shulker.getBoundingBox().getCenter();
            var oldMidpoint = shulker.position().add(0, shulker.getBbHeight() / 2, 0);
            check(h, center.distanceTo(actual) < 4.5 && center.distanceTo(oldMidpoint) > 4.5
                            && actual.distanceTo(oldMidpoint) > .45,
                    "Independent geometry puts actual box center inside radius but position-plus-half-height outside");
            check(h, h.getLevel().noCollision(shulker, shulker.getBoundingBox().deflate(1e-6))
                            && shulker.getArmorValue() == 0 && Combat.isEnemy(p, shulker),
                    "Open enemy has no suffocation, armor reduction or enemy-filter ambiguity");
            var wall = h.getLevel().clip(new ClipContext(center, actual,
                    ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
            check(h, wall.getType() == HitResult.Type.MISS, "Support does not obstruct blast-to-box-center sight line");
            hp(h, shulker, HP, "World settling alone causes no damage");
            int rounds = ammo(gun).rounds(), reserve = ammo(gun).reserve();
            exactAim(h, java.util.List.of(p), () -> {
                shot(h, p); dead(h, corpse);
                blasted(h, center, shulker);
                check(h, ammo(gun).rounds() == rounds - 1 && ammo(gun).reserve() == reserve,
                        "Real precision final blow reaches shifted-box enemy for only the original paid round");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void sameOwnedStackEditedToAnotherEligibleEntryCannotReuseCapturedToken(GameTestHelper h) {
        var p = player(h); var gun = equip(h, p, true);
        var originalEntry = WeaponItems.entry(gun).orElseThrow();
        var token = WeaponDragonfly.capture(p);
        check(h, token != WeaponDragonfly.Token.NONE, "Capture original Distant Relation before its paid precision shot");
        var corpse = primary(h, p, true, 1);
        var productionWitness = target(h, 8.5, 1, 8, HP);
        var center = corpse.getBoundingBox().getCenter();
        exactAim(h, java.util.List.of(p), () -> {
            shot(h, p); dead(h, corpse);
            blasted(h, center, productionWitness);
            var fresh = target(h, 8.5, 1, 4, HP);
            int rounds = ammo(gun).rounds(), reserve = ammo(gun).reserve();
            var replacementEntry = WeaponCatalog.find("brass_attacks").orElseThrow();
            var tag = gun.get(DataComponents.CUSTOM_DATA).copyTag();
            // WeaponItems.entry delegates to WeaponModels: the catalog ID and matching ITEM_MODEL are both required.
            tag.putString(WeaponModels.TAG, replacementEntry.id());
            gun.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
            gun.set(DataComponents.ITEM_MODEL, Identifier.parse(replacementEntry.item_model()));
            var editedEntry = WeaponItems.entry(gun).orElseThrow();
            var trait = WeaponPerks.selected(gun, DragonflyProfile.ID).orElseThrow();
            check(h, p.getMainHandItem() == gun
                            && p.getInventory().getItem(p.getInventory().getSelectedSlot()) == gun
                            && editedEntry.equals(replacementEntry) && !editedEntry.equals(originalEntry)
                            && trait.socket() == 4 && trait.perkHash() == DragonflyProfile.HASH,
                    "Same original object remains owned and eligible in socket 4, while its actual catalog entry changes");
            var edited = gun.copy();
            float previousHp = productionWitness.getHealth();
            WeaponDragonfly.killed(p, token, corpse, true);
            WeaponDragonfly.killed(p, token, corpse, true);
            hp(h, fresh, HP, "Captured source entry mismatch refuses damage on a witness created after the real blast");
            hp(h, productionWitness, previousHp, "Edited original cannot repeat splash on a prior production witness");
            check(h, ItemStack.matches(edited, gun) && ammo(gun).rounds() == rounds && ammo(gun).reserve() == reserve,
                    "Refused same-object entry substitution changes no edited item components or paid ammunition");
            h.succeed();
        });
    }
}
