package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.weapon.AmmoEconomy;
import kim.biryeong.destiny.weapon.SwordCycle;
import kim.biryeong.destiny.weapon.SwordItems;
import kim.biryeong.destiny.weapon.SwordProfile;
import kim.biryeong.destiny.weapon.SwordTiming;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponMagazine;
import kim.biryeong.destiny.weapon.WeaponProfile;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/** Authored W52 start/end cleave and targeted lunge; server fixtures, not native client proof.
 * Every delayed callback and cleanup is registered during test setup, never inside another callback.
 */
public final class SwordCleaveW52GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String SWORD = "abide_the_return";
    private static final float HP = 100;
    private static final double EPS = 1.0e-5;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, z), -90, 0);
        p.setOnGround(true);
        MeleeNativeTestFrames.prepareGround(h,p);
        MeleeNativeTestFrames.track(h,()->{WeaponRuntime.tickPlayer(p);MeleeNativeTestFrames.cameraFrame(p);});
        TestCleanup.register(h, () -> {
            AbilityService.cleanup(p);
            WeaponRuntime.cleanup(p);
            AmmoEconomy.cleanup(p);
            CombatHud.remove(p);
            if (p.level().players().contains(p)) {
                p.level().removePlayerImmediately(p, Entity.RemovalReason.DISCARDED);
            }
            TestPlayers.remove(p);
        });
        return p;
    }

    private static ItemStack equip(ServerPlayer p, int rounds) {
        var entry = WeaponCatalog.find(SWORD).orElseThrow();
        var stack = WeaponItems.create(entry);
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry), rounds, 0));
        SwordItems.save(stack, SwordCycle.CAPACITY, 13);
        p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        WeaponRuntime.tickPlayer(p);
        return stack;
    }

    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()));
    }

    private static <T extends Mob> T stationary(GameTestHelper h, T mob) {
        mob.setNoAi(true);
        mob.setNoGravity(true);
        mob.setPersistenceRequired();
        mob.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP);
        mob.getAttribute(Attributes.ARMOR).setBaseValue(0);
        mob.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        mob.setHealth(HP);
        TestCleanup.register(h, mob::discard);
        return mob;
    }

    private static Husk target(GameTestHelper h, double x, double y, double z) {
        return stationary(h, h.spawn(EntityTypes.HUSK, new Vec3(x, y, z)));
    }

    private static Husk target(GameTestHelper h, double x, double z) {
        return target(h, x, 1, z);
    }

    private static double horizontal(Vec3 a, Vec3 b) {
        return Math.hypot(a.x - b.x, a.z - b.z);
    }

    private static void unchanged(GameTestHelper h, ServerPlayer p, Vec3 before, String message) {
        check(h, p.position().distanceToSqr(before) < EPS * EPS, message);
    }

    private static int lightContact() {
        return SwordTiming.contactTicks(SwordProfile.Shape.UPPERCUT, false, 1);
    }

    private static void windup(GameTestHelper h, ServerPlayer p, Vec3 before, Mob... enemies) {
        unchanged(h, p, before, "Accepted wind-up cannot lunge before contact");
        for (var enemy : enemies) check(h, enemy.getHealth() == HP,
                "Actual enemy HP remains unchanged before contact: " + enemy.getUUID());
    }

    /** Register while constructing the test, never from another scheduled callback. */
    private static void beforeLightContact(GameTestHelper h, ServerPlayer p, Vec3 before, Mob... enemies) {
        windup(h, p, before, enemies);
        h.runAfterDelay(lightContact() - 1, () -> windup(h, p, before, enemies));
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void preLungeSidesAndOverlappingContactsCleaveOnceForOneAmmo(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var p = player(h, 6.5);
        var stack = equip(p, 12);
        var left = target(h, 3.3, 5);
        var right = target(h, 3.3, 8);
        var overlapA = target(h, 4.6, 6.5);
        var overlapB = target(h, 4.6, 6.5);
        var postOnly = target(h, 6.7, 6.5);
        var start = p.position();
        check(h, horizontal(start, postOnly.position()) > 3.5, "Post-only enemy starts outside authored cleave reach");
        InputRouter.onPunch(p);
        beforeLightContact(h, p, start, left, right, overlapA, overlapB, postOnly);
        check(h, ammo(stack).rounds() == 11, "Multi-target light pays once before contact");
        h.runAfterDelay(lightContact() + 7, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, p.getX() > left.getX() && p.getX() > right.getX(),
                    "Accepted targeted lunge passes the nearby lateral contacts");
            float damage = HP - left.getHealth();
            check(h, damage > 0 && damage < HP, "Pre-lunge side contact changes actual HP without killing the fixture");
            for (var enemy : List.of(right, overlapA, overlapB, postOnly)) {
                check(h, Math.abs((HP - enemy.getHealth()) - damage) < .001f,
                        "Both poses include each legal enemy once, even overlapping bodies: " + enemy.getUUID());
            }
            check(h, ammo(stack).rounds() == 11 && ammo(stack).reserve() == 0,
                    "One accepted multi-target light costs one total ammo, not one per pose or victim");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void sixteenTargetCapAppliesAcrossPreAndPostLungeHpTransactions(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var p = player(h, 6.5);
        var stack = equip(p, 12);
        List<Husk> pre = new ArrayList<>();
        List<Husk> post = new ArrayList<>();
        for (int i = 0; i < 12; i++) {
            pre.add(target(h, 3.3, i % 2 == 0 ? 5 : 8));
            post.add(target(h, 6.7, 6.5));
        }
        var start = p.position();
        WeaponRuntime.onPunch(p);
        beforeLightContact(h, p, start, java.util.stream.Stream.concat(pre.stream(), post.stream()).toArray(Husk[]::new));
        check(h, ammo(stack).rounds() == 11, "Capped cleave pays once at acceptance");
        h.runAfterDelay(lightContact() + 7, () -> {
            WeaponRuntime.tickPlayer(p);
            long preHurt = pre.stream().filter(e -> e.getHealth() < HP).count();
            long postHurt = post.stream().filter(e -> e.getHealth() < HP).count();
            check(h, p.getX() > pre.getFirst().getX() && preHurt > 0 && postHurt > 0,
                    "Fixture observes real HP contacts on both sides of the lunge, not one stationary candidate list");
            check(h, preHurt + postHurt == 16 && ammo(stack).rounds() == 11,
                    "Combined start/end union damages at most sixteen legal victims for a single payment");
            float oneHit = HP - pre.stream().filter(e -> e.getHealth() < HP).findFirst().orElseThrow().getHealth();
            for (var enemy : java.util.stream.Stream.concat(pre.stream(), post.stream()).toList()) {
                float lost = HP - enemy.getHealth();
                check(h, lost == 0 || Math.abs(lost - oneHit) < .001f,
                        "Each selected victim loses one real hit and excluded victims retain full HP");
            }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void alliesTamesAndWorldIndexedPlayersAreExcludedFromHpAndAcquisition(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var p = player(h, 2.5);
        var stack = equip(p, 12);
        var ally = target(h, 3.8, 2.5);
        var legal = target(h, 3.5, 1);
        var wolf = stationary(h, h.spawn(EntityTypes.WOLF, new Vec3(4, 1, 3)));
        wolf.setTame(true, false);
        var scoreboard = h.getLevel().getScoreboard();
        String name = "w52_" + UUID.randomUUID().toString().substring(0, 8);
        var previousTeam = scoreboard.getPlayersTeam(p.getScoreboardName());
        var team = scoreboard.addPlayerTeam(name);
        scoreboard.addPlayerToTeam(p.getScoreboardName(), team);
        scoreboard.addPlayerToTeam(ally.getScoreboardName(), team);
        TestCleanup.register(h, () -> {
            if (scoreboard.getPlayerTeam(name) == team) scoreboard.removePlayerTeam(team);
            if (previousTeam != null && scoreboard.getPlayerTeam(previousTeam.getName()) == previousTeam) {
                scoreboard.addPlayerToTeam(p.getScoreboardName(), previousTeam);
            }
        });
        check(h, p.isAlliedTo(ally) && wolf.isTame(), "Excluded mobs have real team/tame state");
        var start = p.position();
        InputRouter.onPunch(p);
        beforeLightContact(h, p, start, ally, legal, wolf);

        var attacker = player(h, 9.5);
        var paid = equip(attacker, 12);
        var victim = player(h, 9.5);
        victim.setPos(h.absoluteVec(new Vec3(4, 1, 9.5)));
        h.getLevel().addNewPlayer(victim);
        check(h, h.getLevel().getEntitiesOfClass(ServerPlayer.class, attacker.getBoundingBox().inflate(4)).contains(victim),
                "PvP fixture is world-indexed and really discoverable by the runtime spatial query");
        var enemy = target(h, 3.5, 8);
        float victimHp = victim.getHealth();
        var before = attacker.position();
        h.startSequence().thenIdle(lightContact() + 7).thenExecute(() -> {
            WeaponRuntime.tickPlayer(p);
            check(h, legal.getHealth() < HP && ally.getHealth() == HP && wolf.getHealth() == HP
                            && ammo(stack).rounds() == 11,
                    "Legal side enemy loses HP while allied hostile and unowned tame remain unharmed");
            check(h,horizontal(start,p.position())<=2+EPS,"Excluded mobs cannot extend the authored forward step");
            // TestPlayers share a profile name: remove this team before exercising actual PvP exclusion.
            scoreboard.removePlayerTeam(team);
            check(h, !attacker.isAlliedTo(victim), "PvP victim is not filtered merely as a team ally");
            WeaponRuntime.onPunch(attacker);
            windup(h, attacker, before, enemy);
            check(h, victim.getHealth() == victimHp && ammo(paid).rounds() == 11,
                    "World-present player and PvE enemy have no early HP transaction; acceptance costs one ammo");
        }).thenIdle(lightContact() - 1).thenExecute(() -> {
            windup(h, attacker, before, enemy);
            check(h, victim.getHealth() == victimHp, "Player HP is unchanged throughout the wind-up");
        }).thenIdle(2).thenExecute(() -> {
            WeaponRuntime.tickPlayer(attacker);
            check(h, victim.getHealth() == victimHp && enemy.getHealth() < HP && ammo(paid).rounds() == 11,
                    "World-present player retains real HP while a legal side PvE victim is cleaved");
            check(h,horizontal(before,attacker.position())<=2+EPS,"Excluded players cannot extend the authored forward step");
        }).thenSucceed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void solidLosAndLowBodyWallStopLungeAndPreventThroughWallHp(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var blocked = player(h, 2.5);
        var a = equip(blocked, 12);
        // Keep the full mob box outside the wall. A delayed test must not confuse
        // native suffocation from an overlapping fixture with early sword damage.
        var hidden = target(h, 5.5, 2.5);
        for (int z = 1; z <= 4; z++) {
            for (int y = 1; y <= 3; y++) h.setBlock(4, y, z, Blocks.STONE);
        }
        var before = blocked.position();
        check(h, h.getLevel().noCollision(hidden, hidden.getBoundingBox()), "Blocked target starts clear of stone suffocation");
        InputRouter.onPunch(blocked);
        beforeLightContact(h, blocked, before, hidden);
        var body = player(h, 9.5);
        var b = equip(body, 12);
        var beyond = target(h, 7, 9.5);
        h.setBlock(3, 1, 9, Blocks.STONE);
        var start = body.position();
        WeaponRuntime.onPunch(body);
        beforeLightContact(h, body, start, beyond);
        check(h, ammo(a).rounds() == 11 && ammo(b).rounds() == 11, "Both blocked swings pay on acceptance");
        h.runAfterDelay(lightContact() + 7, () -> {
            WeaponRuntime.tickPlayer(blocked);
            WeaponRuntime.tickPlayer(body);
            check(h,blocked.getBoundingBox().maxX<=h.absoluteVec(new Vec3(4,1,2)).x+EPS,"Blocked target cannot pull the native dash through a wall");
            check(h, hidden.getHealth() == HP && ammo(a).rounds() == 11,
                    "Accepted blocked swing pays once but cannot cleave through the wall");
            check(h, body.getX() >= start.x - EPS && body.getBoundingBox().maxX <= h.absoluteVec(new Vec3(3, 1, 9)).x + EPS
                            && h.getLevel().noCollision(body, body.getBoundingBox()),
                    "Eye-visible acquisition still obeys the moving player's complete body collision box");
            check(h, beyond.getHealth() == HP && ammo(b).rounds() == 11,
                    "A collision-shortened lunge cannot grant remote damage beyond actual cleave reach");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void closeEnemyContactHitsWithoutMovementOrCameraChange(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var p = player(h, 6.5);
        var stack = equip(p, 12);
        p.setXRot(23);
        var enemy = target(h, 2.9, 6.5);
        var before = p.position();
        float yaw = p.getYRot(), pitch = p.getXRot();
        check(h, enemy.getBoundingBox().inflate(.15).contains(p.getEyePosition()),
                "Contact fixture includes the former ray-start-inside-body regression");
        WeaponRuntime.onPunch(p);
        beforeLightContact(h, p, before, enemy);
        h.runAfterDelay(lightContact() + 7, () -> {
            WeaponRuntime.tickPlayer(p);
            unchanged(h, p, before, "Contact inside the 1.1 authored stop distance never lunges or separates the player");
            check(h, enemy.getHealth() < HP && ammo(stack).rounds() == 11
                            && p.getYRot() == yaw && p.getXRot() == pitch,
                    "Point-blank actual HP hit remains yaw-based and does not force the camera");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void closestVisibleFrontEnemyGuidesBoundedHorizontalLungeAndStopDistance(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var p = player(h, 6.5);
        var stack = equip(p, 12);
        p.setXRot(31);
        var closest = target(h, 6.2, 7.5);
        var farther = target(h, 7.8, 6.5);
        var start = p.position();
        float yaw = p.getYRot(), pitch = p.getXRot();
        check(h, horizontal(start, closest.position()) > 3.5, "Closest enemy initially requires a lunge to reach");
        InputRouter.onPunch(p);
        var shortStep = player(h, 2.5);
        var shortAmmo = equip(shortStep, 12);
        var near = target(h, 5, 2.5);
        var far = target(h, 7, 2.5);
        var origin = shortStep.position();
        WeaponRuntime.onPunch(shortStep);
        beforeLightContact(h, p, start, closest, farther);
        beforeLightContact(h, shortStep, origin, near, far);
        h.runAfterDelay(lightContact() + 7, () -> {
            WeaponRuntime.tickPlayer(p);
            WeaponRuntime.tickPlayer(shortStep);
            double moved = horizontal(start, p.position());
            check(h, moved > 0 && moved <= 2 + EPS && p.getZ() > start.z
                            && Math.abs(p.getY()-start.y)<EPS && p.onGround() && p.getYRot() == yaw && p.getXRot() == pitch,
                    "Closest visible off-axis enemy guides a bounded native displacement: delta="+p.position().subtract(start)+" view="+p.getYRot()+"/"+p.getXRot()+" expected="+yaw+"/"+pitch);
            check(h, closest.getHealth() < HP && farther.getHealth() < HP && ammo(stack).rounds() == 11,
                    "Both enemies reached by the finite native swept path lose real HP");
            check(h, h.getLevel().noCollision(p, p.getBoundingBox())
                            && h.getLevel().getWorldBorder().isWithinBounds(p.getBoundingBox()),
                    "Lunge endpoint body remains collision-free and inside the world border");

            check(h, horizontal(origin, shortStep.position()) > 0 && horizontal(origin, shortStep.position()) < 1.8
                            && horizontal(shortStep.position(), near.position()) >= 1.1 - EPS,
                    "Closest target shortens movement to leave the authored 1.1 stop separation");
            check(h, near.getHealth() < HP && far.getHealth() < HP && ammo(shortAmmo).rounds() == 11,
                    "Short lunge still cleaves both reachable front enemies for one payment");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void rearOffAcquisitionConeAndBeyondRangeCannotAutoMovePlayer(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var p = player(h, 6.5);
        var stack = equip(p, 12);
        var rear = target(h, .8, 6.5);
        var wide = target(h, 4, 9);
        var tooFar = target(h, 7.9, 6.5); // 5.4 horizontal: beyond the tightened authored 5.3 acquisition.
        var start = p.position();
        InputRouter.onPunch(p);
        var miss = player(h, 2.5);
        var drySwing = equip(miss, 12);
        var before = miss.position();
        WeaponRuntime.onPunch(miss);
        beforeLightContact(h, p, start, rear, wide, tooFar);
        beforeLightContact(h, miss, before);
        h.runAfterDelay(lightContact() + 7, () -> {
            WeaponRuntime.tickPlayer(p);
            WeaponRuntime.tickPlayer(miss);
            check(h,p.getZ()==start.z&&horizontal(start,p.position())<=2+EPS,"Excluded acquisition targets cannot turn or extend the two-block fallback");
            check(h, rear.getHealth() == HP && tooFar.getHealth() < HP && wide.getHealth() < HP
                            && ammo(stack).rounds() == 11,
                    "Wider light cleave can hurt a legal side enemy without turning it into a narrow-cone lunge target");
            check(h,Math.abs(horizontal(before,miss.position())-2)<.02,"A targetless powered contact advances two native blocks");
            check(h, ammo(drySwing).rounds() == 11, "Stationary accepted miss still costs one ammo");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void bodyHeightAllowsLocalCleaveButRejectsHighDamageAndLungeTargets(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var p = player(h, 6.5);
        var stack = equip(p, 12);
        // Husk body midpoint is .975 above feet: y=2.35 is 1.425 above player body origin at y=1.9.
        var local = target(h, 4.5, 2.35, 6.5);
        var high = target(h, 4.5, 3.2, 6.5);
        var elevatedDistant = target(h, 7, 2.35, 6.5);
        var origin = p.position().add(0, .9, 0);
        double dy = local.getY() + local.getBbHeight() * .5 - origin.y;
        check(h, dy > 1.25 && dy < 1.5, "Fixture lies inside cleave height but outside lunge height");
        var start = p.position();
        WeaponRuntime.onPunch(p);
        beforeLightContact(h, p, start, local, high, elevatedDistant);
        h.runAfterDelay(lightContact() + 7, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h,Math.abs(p.getY()-start.y)<EPS&&p.onGround()&&horizontal(start,p.position())<=2+EPS,"High targets cannot boost or extend grounded native step: delta="+p.position().subtract(start));
            check(h, local.getHealth() < HP && high.getHealth() == HP && elevatedDistant.getHealth() < HP
                            && ammo(stack).rounds() == 11,
                    "Body-height bounds exclude the high foe while actual swept path reaches the lower far foe");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void emptyLightWeaklyCleavesBothSidesWithoutLungeOrAmmoGrant(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var paid = player(h, 2.5);
        var empty = player(h, 9.5);
        var poweredStack = equip(paid, 12);
        var emptyStack = equip(empty, 0);
        var poweredA = target(h, 3.5, 1);
        var poweredB = target(h, 3.5, 4);
        var weakA = target(h, 3.5, 8);
        var weakB = target(h, 3.5, 11);
        var distant = target(h, 7, 9.5);
        var start = empty.position();
        var paidStart = paid.position();
        InputRouter.onPunch(paid);
        InputRouter.onPunch(empty);
        beforeLightContact(h, paid, paidStart, poweredA, poweredB);
        beforeLightContact(h, empty, start, weakA, weakB, distant);
        h.runAfterDelay(lightContact() + 7, () -> {
            WeaponRuntime.tickPlayer(paid);
            WeaponRuntime.tickPlayer(empty);
            float strong = HP - poweredA.getHealth(), weak = HP - weakA.getHealth();
            check(h, strong > weak && weak > 0 && Math.abs(poweredB.getHealth() - poweredA.getHealth()) < .001f
                            && Math.abs(weakB.getHealth() - weakA.getHealth()) < .001f,
                    "Empty light still cleaves both legal side bodies, each at weaker actual HP damage");
            check(h,horizontal(start,empty.position())<=2+EPS,"Empty weak contact retains the bounded two-block step");
            check(h, distant.getHealth() < HP && ammo(emptyStack).total() == 0 && ammo(poweredStack).rounds() == 11
                            && !WeaponRuntime.reloading(empty),
                    "Weak swept contact cannot create ammo or begin reload");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void airborneLightKeepsVerticalMomentumAndViewAcrossAllFiveFrames(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        // Historical aggressive/lightweight air actions are sourced; shared geometry is authored.
        var ids = List.of("abide_the_return", "goldtusk", "crown_splitter", "falling_guillotine", "temptation_s_hook");
        for (int i = 0; i < ids.size(); i++) {
            String id = ids.get(i);
            int startTick = 1 + i * 12;
            boolean last = i == ids.size() - 1;
            ServerPlayer[] owner = new ServerPlayer[1];
            ItemStack[] held = new ItemStack[1];
            Husk[] target = new Husk[1];
            Vec3[] origin = new Vec3[1], motion = new Vec3[1];
            h.runAfterDelay(startTick, () -> {
                var p = player(h, 6.5);
                var stack = WeaponItems.create(WeaponCatalog.find(id).orElseThrow());
                WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()), 12, 0));
                p.setPos(p.getX(), p.getY() + 11.1, p.getZ());
                p.setOnGround(false);
                p.setItemInHand(InteractionHand.MAIN_HAND, stack);
                WeaponRuntime.tickPlayer(p);
                p.setXRot(19);
                p.setDeltaMovement(new Vec3(.2, -.35, .1));
                var velocity = p.getDeltaMovement();
                var start = p.position();
                var enemy = target(h, 6.7, 12.1, 6.5);
                TestPlayers.drain(p);
                owner[0] = p; held[0] = stack; target[0] = enemy; origin[0] = start; motion[0] = velocity;
                InputRouter.onPunch(p);
                windup(h, p, start, enemy);
                check(h, ammo(stack).rounds() == 11 && p.getDeltaMovement().equals(velocity),
                        id + ": airborne acceptance pays once without moving or changing velocity");
            });
            h.runAfterDelay(startTick + lightContact() - 1, () -> {
                windup(h, owner[0], origin[0], target[0]);
                check(h, owner[0].getDeltaMovement().equals(motion[0]), id + ": wind-up preserves air velocity");
                check(h, TestPlayers.outbound(owner[0]).stream().noneMatch(
                                net.minecraft.network.protocol.game.ClientboundPlayerPositionPacket.class::isInstance),
                        id + ": no lunge correction is queued before contact");
            });
            h.runAfterDelay(startTick + lightContact() + 7, () -> {
                var p = owner[0]; var stack = held[0]; var enemy = target[0];
                var start = origin[0]; var velocity = motion[0];
                WeaponRuntime.tickPlayer(p);
                check(h, horizontal(start, p.position()) > 0 && horizontal(start, p.position()) <= 5 + EPS
                                && p.getY() < start.y && !p.onGround() && p.getXRot() == 19 && p.getYRot() == -90
                                && p.getDeltaMovement().y < 0,
                        id + ": airborne light lunge preserves air motion; start=" + start + ", end=" + p.position()
                                + ", grounded=" + p.onGround() + ", yaw=" + p.getYRot() + ", pitch=" + p.getXRot()
                                + ", beforeVelocity=" + velocity + ", afterVelocity=" + p.getDeltaMovement());
                check(h, enemy.getHealth() < HP && ammo(stack).rounds() == 11 && !WeaponRuntime.reloading(p),
                        id + ": an accepted airborne light changes actual HP and pays once");
                var packets=TestPlayers.outbound(p);
                check(h,packets.stream().noneMatch(net.minecraft.network.protocol.game.ClientboundPlayerPositionPacket.class::isInstance),
                        id+": dash never queues a teleport correction");
                check(h,packets.stream().anyMatch(net.minecraft.network.protocol.game.ClientboundSetEntityMotionPacket.class::isInstance),
                        id+": actual native velocity packets drive the finite dash");
                enemy.discard();
                if (last) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void aggressiveAirborneHeavyAcceptsAnyPositiveEnergyAndStartsRechargeDelay(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var enemies = new ArrayList<Husk>();
        var owners = new ArrayList<ServerPlayer>();
        var stacks = new ArrayList<ItemStack>();
        var origins = new ArrayList<Vec3>();
        int i = 0;
        int contact = SwordTiming.contactTicks(SwordProfile.Shape.SLAM, true, 0);
        for (int energy : new int[] {1, SwordCycle.CAPACITY}) {
            double z = i++ == 0 ? 2.5 : 9.5;
            var p = player(h, z);
            var stack = WeaponItems.create(WeaponCatalog.find("crown_splitter").orElseThrow());
            WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()), 12, 0));
            SwordItems.save(stack, energy, 0);
            p.setPos(p.getX(), p.getY() + 11.1, p.getZ());
            p.setOnGround(false);
            p.setItemInHand(InteractionHand.MAIN_HAND, stack);
            WeaponRuntime.tickPlayer(p);
            var enemy = target(h, 4.5, 12.1, z);
            owners.add(p); stacks.add(stack); enemies.add(enemy); origins.add(p.position());
            var before = p.position();
            p.gameMode.useItem(p, h.getLevel(), stack, InteractionHand.MAIN_HAND);
            windup(h, p, before, enemy);
            check(h, ammo(stack).rounds() == 8 && SwordItems.energy(stack) == 0
                            && SwordItems.delay(stack) == SwordCycle.RECHARGE_DELAY && !p.onGround(),
                    "Aggressive airborne heavy accepts positive energy, pays once and immediately starts recharge delay");
        }
        h.runAfterDelay(contact - 1, () -> {
            for (int n = 0; n < owners.size(); n++) windup(h, owners.get(n), origins.get(n), enemies.get(n));
        });
        h.runAfterDelay(contact + 1, () -> {
            for (int n = 0; n < owners.size(); n++) {
                WeaponRuntime.tickPlayer(owners.get(n));
                check(h, enemies.get(n).getHealth() < HP && ammo(stacks.get(n)).rounds() == 8
                                && SwordItems.energy(stacks.get(n)) == 0 && !owners.get(n).onGround(),
                        "Accepted aggressive airborne heavy changes actual HP at contact without another payment or grounding");
            }
            check(h, Math.abs(enemies.get(0).getHealth() - enemies.get(1).getHealth()) < .001f,
                    "One positive energy has the same actual HP power as full energy, including in air");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void duplicateCooldownSwapGuardAndUnavailableInputsCannotMoveSpendOrRepeatHp(GameTestHelper h) {
        MeleeNativeTestFrames.install(h);
        var p = player(h, 6.5);
        var first = equip(p, 12);
        var enemy = target(h, 7, 6.5);
        var start = p.position();
        InputRouter.onPunch(p);
        beforeLightContact(h, p, start, enemy);
        check(h, ammo(first).rounds() == 11, "Accepted light immediately establishes paid owner cadence");
        InputRouter.onPunch(p);
        WeaponRuntime.onPunch(p);
        unchanged(h, p, start, "Same-tick duplicate paths cannot trigger early lunge");
        check(h, enemy.getHealth() == HP && ammo(first).rounds() == 11, "Duplicates repeat neither HP loss nor ammo cost");
        p.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        WeaponRuntime.tickPlayer(p);
        var replacement = equip(p, 12);
        WeaponRuntime.onPunch(p);
        unchanged(h, p, start, "Item replacement cannot bypass shared owner movement cadence");
        check(h, enemy.getHealth() == HP && ammo(replacement).rounds() == 12 && ammo(first).rounds() == 11,
                "Pre-contact swap cancels damage without refunding or paying from the replacement");
        var guarded = player(h, 2.5);
        var guardStack = equip(guarded, 12);
        var guardEnemy = target(h, 7, 2.5);
        guarded.setShiftKeyDown(true);
        var guardStart = guarded.position();
        var unavailable = player(h, 9.5);
        var unavailableStack = equip(unavailable, 12);
        var unavailableEnemy = target(h, 7, 9.5);
        unavailable.setGameMode(GameType.SPECTATOR);
        var unavailableStart = unavailable.position();
        h.runAfterDelay(2, () -> {
            WeaponRuntime.onPunch(p);
            InputRouter.onPunch(p);
            unchanged(h, p, start, "Next-tick owner cooldown cannot advance a lunge");
            check(h, enemy.getHealth() == HP && ammo(replacement).rounds() == 12,
                    "Cooldown denial preserves HP and replacement ammo across server ticks");
            WeaponRuntime.tickPlayer(guarded);
            check(h, WeaponRuntime.swordStatus(guarded).orElseThrow().guarding(), "Guard fixture is actually active");
            WeaponRuntime.onPunch(guarded);
            InputRouter.onPunch(guarded);
            unchanged(h, guarded, guardStart, "Guard-denied light has no movement");
            check(h, guardEnemy.getHealth() == HP && ammo(guardStack).rounds() == 12,
                    "Guard-denied light has no HP or ammo transaction");
            WeaponRuntime.onPunch(unavailable);
            InputRouter.onPunch(unavailable);
            unchanged(h, unavailable, unavailableStart, "Unavailable spectator cannot lunge");
            check(h, unavailableEnemy.getHealth() == HP && ammo(unavailableStack).rounds() == 12,
                    "Unavailable input has no HP or ammo transaction");
        });
        h.runAfterDelay(lightContact() + 7, () -> {
            WeaponRuntime.tickPlayer(p);
            WeaponRuntime.tickPlayer(guarded);
            WeaponRuntime.tickPlayer(unavailable);
            windup(h, p, start, enemy);
            unchanged(h, guarded, guardStart, "Guard denial remains stationary after the contact deadline");
            unchanged(h, unavailable, unavailableStart, "Unavailable denial remains stationary after the contact deadline");
            check(h, guardEnemy.getHealth() == HP && unavailableEnemy.getHealth() == HP
                            && ammo(first).rounds() == 11 && ammo(replacement).rounds() == 12
                            && ammo(guardStack).rounds() == 12 && ammo(unavailableStack).rounds() == 12,
                    "Canceled and denied inputs never apply deferred HP or movement and never refund or repeat cost");
            h.succeed();
        });
    }

}
