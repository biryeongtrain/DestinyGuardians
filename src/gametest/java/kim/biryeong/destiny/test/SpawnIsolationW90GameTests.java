package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.registries.Registries;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.gametest.framework.TestEnvironmentDefinition;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.gamerules.GameRule;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

/** W90 checks registered spawn isolation before fixture setup and retains paid combat.
 * Lifecycle coverage calls native registered environment activation/teardown synchronously;
 * it does not observe the runner ending one environment batch and starting another.
 */
public final class SpawnIsolationW90GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final String ISOLATED = "destiny-test:w90_isolated";
    private static final String ALLIED_ISOLATED = "destiny-test:w90_allied_isolated";
    private static final String ALLIED = "destiny-test:w78_allied";
    private static final float HP = 1000;

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static void isolatedOnEntry(GameTestHelper h) {
        check(h, !h.getLevel().getGameRules().get(GameRules.SPAWN_MOBS),
                "Registered environment disables spawn_mobs before any fixture setup");
    }

    private static void deck(GameTestHelper h) {
        for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++)
            h.setBlock(x, 3, z, Blocks.STONE);
    }

    private static void bounded(GameTestHelper h, Entity entity) {
        var origin = h.absoluteVec(Vec3.ZERO);
        var box = entity.getBoundingBox();
        check(h, box.minX > origin.x && box.maxX < origin.x + 48
                        && box.minY > origin.y && box.maxY < origin.y + 12
                        && box.minZ > origin.z && box.maxZ < origin.z + 32,
                "Complete W90 actor AABB lies inside the 48x12x32 structure");
    }

    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(3, 4, z), -90, 0,
                "W90_" + UUID.randomUUID().toString().substring(0, 8));
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
        return p;
    }

    private static Husk target(GameTestHelper h, double x, double z) {
        var mob = h.spawn(EntityTypes.HUSK, new Vec3(x, 4, z));
        TestCleanup.register(h, mob::discard);
        mob.setNoAi(true);
        mob.setNoGravity(true);
        mob.setPersistenceRequired();
        mob.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP);
        mob.getAttribute(Attributes.ARMOR).setBaseValue(0);
        mob.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        mob.setHealth(HP);
        bounded(h, mob);
        check(h, mob.isAlive() && !mob.isRemoved(),
                "Explicit hostile spawn remains alive while natural spawning is disabled");
        return mob;
    }

    private static WeaponMagazine ammo(ItemStack gun) {
        return WeaponItems.magazine(gun,
                WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow()));
    }

    private static ItemStack equip(GameTestHelper h, ServerPlayer p) {
        var entry = WeaponCatalog.find("beloved").orElseThrow();
        var profile = WeaponProfile.forEntry(entry);
        check(h, profile.mode() == WeaponProfile.Mode.HITSCAN && profile.chargeTicks() == 0
                        && profile.burst() == 1 && profile.pellets() == 1
                        && !profile.infiniteReserve() && profile.magazine() > 1,
                "Beloved is one immediate hitscan shot with finite ammunition");
        var gun = WeaponItems.create(entry);
        WeaponItems.save(gun, new WeaponMagazine(profile, profile.magazine(), 3));
        int slot = WeaponCharacteristics.of(entry).slot().hotbar();
        p.getInventory().setItem(slot, gun);
        p.getInventory().setSelectedSlot(slot);
        WeaponAccuracy.setAirborneBonus(gun, 100);
        WeaponRuntime.tickPlayer(p);
        TestPlayers.drain(p);
        check(h, p.getMainHandItem() == gun && ammo(gun).rounds() == profile.magazine()
                        && ammo(gun).reserve() == 3,
                "Matching hotbar slot binds the loaded finite-ammo weapon without spending it");
        return gun;
    }

    private static void rayIntersects(GameTestHelper h, ServerPlayer p, Husk mob) {
        var from = p.getEyePosition();
        check(h, mob.getBoundingBox().clip(from, from.add(20, 0, 0)).isPresent(),
                "Real horizontal paid-shot ray crosses the hostile fixture AABB");
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

    private static void paidShot(GameTestHelper h, ServerPlayer p, ItemStack gun, Husk enemy) {
        check(h, WeaponAiming.progress(p) == 1 && WeaponAiming.coneDegrees(p) == 0, "Exact paid filtering ray");
        p.setYRot(-90);
        p.setYHeadRot(-90);
        p.setXRot(0);
        WeaponAiming.tick(p);
        rayIntersects(h, p, enemy);
        float beforeHp = enemy.getHealth();
        int rounds = ammo(gun).rounds(), reserve = ammo(gun).reserve();
        check(h, WeaponRuntime.beginUse(p), "Production beginUse accepts the paid hitscan shot");
        WeaponRuntime.releaseUse(p, gun);
        check(h, ammo(gun).rounds() == rounds - 1 && ammo(gun).reserve() == reserve,
                "Actual paid shot spends exactly one loaded round and no reserve");
        check(h, enemy.getHealth() < beforeHp && enemy.isAlive(),
                "Actual paid ray damages the explicit enemy without a kill side effect");
        bounded(h, enemy);
    }

    private static ResourceKey<TestEnvironmentDefinition<?>> environmentKey(String id) {
        return ResourceKey.create(Registries.TEST_ENVIRONMENT, Identifier.parse(id));
    }

    private static TestEnvironmentDefinition<?> environment(GameTestHelper h, String id) {
        return h.getLevel().registryAccess().lookupOrThrow(Registries.TEST_ENVIRONMENT)
                .getValueOrThrow(environmentKey(id));
    }

    private static void alliedComposition(GameTestHelper h) {
        var registry = h.getLevel().registryAccess().lookupOrThrow(Registries.TEST_ENVIRONMENT);
        var combined = environment(h, ALLIED_ISOLATED);
        check(h, combined instanceof TestEnvironmentDefinition.AllOf,
                "Registered allied isolation environment is an actual native all_of");
        var definitions = ((TestEnvironmentDefinition.AllOf) combined).definitions();
        check(h, definitions.size() == 2
                        && definitions.get(0) == registry.getOrThrow(environmentKey(ISOLATED))
                        && definitions.get(1) == registry.getOrThrow(environmentKey(ALLIED)),
                "Composite preserves the actual registered isolated and w78_allied holders in order");
    }

    @GameTest(structure = FLOOR, environment = ISOLATED, maxTicks = 65)
    public void isolatedEntryRetainsExplicitHostilesAndPaidCombat(GameTestHelper h) {
        isolatedOnEntry(h);
        deck(h);
        var p = player(h, 8);
        var gun = equip(h, p);
        var enemy = target(h, 10, 8);
        var nativeCandidates = h.getLevel().getEntitiesOfClass(Husk.class,
                enemy.getBoundingBox().inflate(.25));
        check(h, nativeCandidates.contains(enemy) && Combat.isEnemy(p, enemy)
                        && !p.isAlliedTo(enemy)
                        && Combat.enemiesNear(p, enemy.position(), 2).contains(enemy),
                "Explicit hostile remains in native queries and production enemy classification/query");
        exactAim(h, java.util.List.of(p), () -> {
            paidShot(h, p, gun, enemy);
            isolatedOnEntry(h);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, environment = ALLIED_ISOLATED, maxTicks = 65)
    public void alliedIsolationPreservesCompositionAndPaidRayFiltering(GameTestHelper h) {
        isolatedOnEntry(h);
        alliedComposition(h);
        deck(h);
        var p = player(h, 16);
        var gun = equip(h, p);
        var ally = target(h, 6, 16);
        var enemy = target(h, 10, 16);
        var scoreboard = h.getLevel().getScoreboard();
        String name = "w90_" + UUID.randomUUID().toString().substring(0, 8);
        check(h, scoreboard.getPlayerTeam(name) == null, "Unique fixture team does not replace another team");
        var team = scoreboard.addPlayerTeam(name);
        TestCleanup.register(h, () -> {
            if (scoreboard.getPlayerTeam(name) == team) scoreboard.removePlayerTeam(team);
        });
        check(h, scoreboard.addPlayerToTeam(p.getScoreboardName(), team)
                        && scoreboard.addPlayerToTeam(ally.getScoreboardName(), team),
                "Native scoreboard accepts both independent fixture identities");
        check(h, p.getTeam() == team && ally.getTeam() == team
                        && p.isAlliedTo(ally) && ally.isAlliedTo(p) && !p.isAlliedTo(enemy),
                "Native team semantics ally only the intervening hostile with the shooter");
        var nativeCandidates = h.getLevel().getEntitiesOfClass(Husk.class,
                new AABB(h.absoluteVec(new Vec3(4, 4, 15)), h.absoluteVec(new Vec3(12, 7, 17))));
        var combatCandidates = Combat.enemiesNear(p, h.absoluteVec(new Vec3(8, 5, 16)), 5);
        check(h, nativeCandidates.contains(ally) && nativeCandidates.contains(enemy)
                        && !Combat.isEnemy(p, ally) && Combat.isEnemy(p, enemy)
                        && !combatCandidates.contains(ally) && combatCandidates.contains(enemy),
                "Both hostiles remain native query candidates; Combat rejects only the scoreboard ally");
        rayIntersects(h, p, ally);
        check(h, ally.getX() < enemy.getX(), "Allied hostile actually intervenes before the enemy");
        float allyHp = ally.getHealth();
        exactAim(h, java.util.List.of(p), () -> {
            paidShot(h, p, gun, enemy);
            check(h, ally.getHealth() == allyHp && ally.isAlive(),
                    "Paid enemy hit passes the intervening allied hostile without damaging it");
            bounded(h, ally);
            isolatedOnEntry(h);
            h.succeed();
        });
    }

    private static Map<GameRule<?>, Object> unrelatedRules(GameRules rules) {
        Map<GameRule<?>, Object> snapshot = new LinkedHashMap<>();
        rules.availableRules().filter(rule -> rule != GameRules.SPAWN_MOBS)
                .forEach(rule -> snapshot.put(rule, rules.get(rule)));
        return snapshot;
    }

    private static void unrelatedUnchanged(GameTestHelper h, Map<GameRule<?>, Object> before) {
        check(h, before.equals(unrelatedRules(h.getLevel().getGameRules())),
                "Every available unrelated gamerule retains its exact value");
    }

    @GameTest(structure = FLOOR, environment = ISOLATED, maxTicks = 65)
    public void registeredEnvironmentLifecycleRestoresBothBaselinesWithoutRuleSpill(GameTestHelper h) {
        isolatedOnEntry(h);
        alliedComposition(h);
        var level = h.getLevel();
        var rules = level.getGameRules();
        boolean original = rules.get(GameRules.SPAWN_MOBS);
        var unrelated = unrelatedRules(rules);
        check(h, !unrelated.isEmpty(), "Unrelated-rule snapshot covers available native gamerules");
        var isolated = environment(h, ISOLATED);
        var allied = environment(h, ALLIED_ISOLATED);
        // Never yield or schedule work while changing the server-wide baseline.
        // Each native activation tears down even if an assertion throws; each case restores entry state.
        for (boolean baseline : new boolean[]{false, true}) {
            try {
                rules.set(GameRules.SPAWN_MOBS, baseline, level.getServer());
                check(h, rules.get(GameRules.SPAWN_MOBS) == baseline,
                        "Selected prior spawn_mobs baseline is observable before activation");
                var outer = TestEnvironmentDefinition.activate(isolated, level);
                try {
                    isolatedOnEntry(h);
                    unrelatedUnchanged(h, unrelated);
                    var nested = TestEnvironmentDefinition.activate(allied, level);
                    try {
                        isolatedOnEntry(h);
                        unrelatedUnchanged(h, unrelated);
                    } finally {
                        nested.teardown();
                    }
                    check(h, !rules.get(GameRules.SPAWN_MOBS),
                            "Nested allied teardown restores the still-active outer isolation");
                    unrelatedUnchanged(h, unrelated);
                } finally {
                    outer.teardown();
                }
                check(h, rules.get(GameRules.SPAWN_MOBS) == baseline,
                        "Native outer teardown restores exact prior spawn_mobs=" + baseline);
                unrelatedUnchanged(h, unrelated);
            } finally {
                rules.set(GameRules.SPAWN_MOBS, original, level.getServer());
            }
            check(h, rules.get(GameRules.SPAWN_MOBS) == original,
                    "Synchronous lifecycle case leaves the runner-owned entry rule intact");
        }
        unrelatedUnchanged(h, unrelated);
        isolatedOnEntry(h);
        h.succeed();
    }
}
