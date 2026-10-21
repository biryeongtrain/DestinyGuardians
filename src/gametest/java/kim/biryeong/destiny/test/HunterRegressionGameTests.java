package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.Tasks;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.combat.Keyword;
import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianData;
import kim.biryeong.destiny.guardian.Guardians;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerInputPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.cow.Cow;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

/** Regressions exercised through server damage, packet handlers and normal server ticks. */
public final class HunterRegressionGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final Vec3 PLAYER_POS = new Vec3(2.5, 1, 6.5);
    private static final Input SHIFT = new Input(false, false, false, false, false, true, false);

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static ServerPlayer hunter(GameTestHelper h, Element element) {
        return TestPlayers.hunter(h, element, PLAYER_POS, -90, 0);
    }

    private static ServerLevel otherLevel(GameTestHelper h) {
        ServerLevel level = h.getLevel().getServer().getLevel(
                h.getLevel().dimension().equals(Level.NETHER) ? Level.OVERWORLD : Level.NETHER);
        check(h, level != null && level != h.getLevel(), "A second dimension is required");
        return level;
    }

    /** Cleanup runs both on setup failure and after the single delayed assertion, including failures. */
    private static void delayed(GameTestHelper h, int ticks, Runnable setup, Runnable assertions, Runnable cleanup) {
        boolean scheduled = false;
        try {
            setup.run();
            h.runAfterDelay(ticks, () -> {
                try {
                    assertions.run();
                    h.succeed();
                } finally {
                    cleanup.run();
                }
            });
            scheduled = true;
        } finally {
            if (!scheduled) {
                cleanup.run();
            }
        }
    }

    private static void swapPacket(ServerPlayer player) {
        player.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND, BlockPos.ZERO, Direction.UP));
    }

    private static void inputPacket(ServerPlayer player, Input input) {
        player.connection.handlePlayerInput(new ServerboundPlayerInputPacket(input));
    }

    private static void equipHandMarkers(ServerPlayer player) {
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK, 2));
        player.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.DIAMOND, 3));
    }

    private static void assertHandsUnchanged(GameTestHelper h, ServerPlayer player) {
        ItemStack main = player.getMainHandItem();
        ItemStack off = player.getOffhandItem();
        check(h, main.is(Items.STICK) && main.getCount() == 2
                && off.is(Items.DIAMOND) && off.getCount() == 3, "Guardian packet must cancel the vanilla hand swap");
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void combatRejectsOwnerAndTargetDimensionMismatch(GameTestHelper h) {
        ServerPlayer player = hunter(h, Element.ARC);
        Husk target = null;
        try {
            target = h.spawn(EntityTypes.HUSK, new Vec3(5.5, 1, 6.5));
            target.setNoAi(true);
            ServerLevel original = h.getLevel();
            ServerLevel other = otherLevel(h);
            Vec3 center = target.position().add(0, target.getBbHeight() / 2, 0);
            check(h, Combat.enemiesNear(original, player, center, 2).contains(target),
                    "Same-dimension control must find the enemy");
            float health = target.getHealth();
            Guardians.data(player).setSuperEnergy(0.25f);
            target.damageCooldownTime = 9;

            // These fake players are not registered in the world's entity list; no teleport is needed.
            player.setServerLevel(other);
            check(h, Combat.enemiesNear(original, player, center, 2).isEmpty(),
                    "An effect in the old dimension must not select enemies after its owner leaves");
            check(h, !Combat.damage(original, player, target, 100f, Element.ARC),
                    "Damage must reject an owner outside the effect dimension");
            check(h, !Combat.damage(other, player, target, 100f, Element.ARC),
                    "Damage must reject a target outside the effect dimension");
            check(h, target.getHealth() == health && target.getLastHurtByPlayer() == null
                    && target.damageCooldownTime == 9, "Rejected damage must leave health, attribution and immunity unchanged");
            check(h, Guardians.data(player).superEnergy() == 0.25f, "Rejected damage must not grant kill energy");

            player.setServerLevel(original);
            check(h, Combat.damage(original, player, target, 100f, Element.ARC),
                    "Same-dimension control must still deal lethal damage");
            check(h, Math.abs(Guardians.data(player).superEnergy() - (0.25f + AbilityService.killSuperEnergy)) < 1e-4,
                    "A valid kill must credit the owner exactly once");
            h.succeed();
        } finally {
            TestPlayers.remove(player);
            if (target != null) {
                Statuses.forget(target);
                target.discard();
            }
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void projectileDimensionChangeCancelsWithoutImpact(GameTestHelper h) {
        ServerPlayer player = hunter(h, Element.ARC);
        AtomicInteger impacts = new AtomicInteger();
        SimProjectile[] projectile = new SimProjectile[1];
        Vec3 origin = player.getEyePosition();
        delayed(h, 2, () -> {
            // A one-tick lifetime guarantees an impact if cancellation fails, even in empty space.
            projectile[0] = SimProjectile.launch(player, origin, new Vec3(1, 0, 0), 0, 1,
                    new ItemStack(Items.SNOWBALL), 0.25f, Element.ARC.color(), hit -> impacts.incrementAndGet());
            check(h, SimProjectile.activeCount(player) == 1 && !projectile[0].isDone(), "Projectile must start active");
            player.setServerLevel(otherLevel(h));
        }, () -> {
            check(h, projectile[0].isDone() && SimProjectile.activeCount(player) == 0,
                    "Leaving the launch dimension must discard the projectile");
            check(h, impacts.get() == 0, "Cancelled projectile must never invoke its impact callback");
            check(h, projectile[0].position().equals(origin), "Cancelled projectile must not advance in its old dimension");
        }, () -> TestPlayers.remove(player));
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void ownerTaskRunsWhileOwnerIsValid(GameTestHelper h) {
        ServerPlayer player = hunter(h, Element.VOID);
        AtomicInteger calls = new AtomicInteger();
        delayed(h, 2, () -> Tasks.run(player, h.getLevel(), age -> {
            calls.incrementAndGet();
            return true;
        }), () -> {
            check(h, calls.get() > 0, "Normal server ticks must execute a valid owner's task");
            check(h, Tasks.count(player) == 1, "A continuing valid task must remain registered");
        }, () -> TestPlayers.remove(player));
    }

    private static void taskCancellation(GameTestHelper h, Consumer<ServerPlayer> invalidate) {
        ServerPlayer player = hunter(h, Element.VOID);
        AtomicInteger calls = new AtomicInteger();
        delayed(h, 2, () -> {
            Tasks.run(player, h.getLevel(), age -> {
                calls.incrementAndGet();
                return true;
            });
            check(h, Tasks.count(player) == 1, "Owned task must start registered");
            invalidate.accept(player);
        }, () -> {
            check(h, Tasks.count(player) == 0, "Invalid owner's task must be automatically removed");
            check(h, calls.get() == 0, "Invalid owner's callback must not execute");
        }, () -> TestPlayers.remove(player));
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void ownerTaskCancelsWhenOwnerDies(GameTestHelper h) {
        // Set health directly so AFTER_DEATH cleanup cannot mask a missing scheduler guard.
        taskCancellation(h, player -> player.setHealth(0));
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void ownerTaskCancelsWhenOwnerIsRemoved(GameTestHelper h) {
        taskCancellation(h, ServerPlayer::discard);
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void ownerTaskCancelsWhenOwnerChangesDimension(GameTestHelper h) {
        taskCancellation(h, player -> player.setServerLevel(otherLevel(h)));
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void weakenedHurtServerDealsThirteenForTen(GameTestHelper h) {
        Cow target = h.spawn(EntityTypes.COW, new Vec3(5.5, 1, 6.5));
        try {
            target.setNoAi(true);
            target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(40);
            target.setHealth(40f);
            check(h, target.getArmorValue() == 0, "Damage fixture must have no armor");
            float health = target.getHealth();
            check(h, target.hurtServer(h.getLevel(), target.damageSources().generic(), 10f), "Control damage must apply");
            check(h, Math.abs(health - target.getHealth() - 10f) < 1e-4, "Unweakened control must take exactly 10 damage");
            target.setHealth(health);
            target.damageCooldownTime = 0;
            Statuses.apply(target, Keyword.WEAKENED, 40);
            check(h, target.hurtServer(h.getLevel(), target.damageSources().generic(), 10f), "Weakened damage must apply");
            check(h, Math.abs(health - target.getHealth() - 13f) < 1e-4,
                    "LivingEntity damage mixin must turn 10 incoming damage into exactly 13, got " + (health - target.getHealth()));
            h.succeed();
        } finally {
            Statuses.forget(target);
            target.discard();
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void fPacketCancelsSwapAndStartsGrenadeCooldown(GameTestHelper h) {
        ServerPlayer player = hunter(h, Element.ARC);
        try {
            equipHandMarkers(player);
            inputPacket(player, Input.EMPTY);
            GuardianData data = Guardians.data(player);
            check(h, data.cooldown(AbilitySlot.GRENADE) == 0 && SimProjectile.activeCount(player) == 0,
                    "Grenade fixture must start ready");
            swapPacket(player);
            assertHandsUnchanged(h, player);
            int cooldown = data.cooldown(AbilitySlot.GRENADE);
            check(h, cooldown > 0 && SimProjectile.activeCount(player) == 1,
                    "F packet must launch one grenade and start its cooldown");
            swapPacket(player);
            assertHandsUnchanged(h, player);
            check(h, data.cooldown(AbilitySlot.GRENADE) == cooldown && SimProjectile.activeCount(player) == 1,
                    "Repeated F packet must not bypass cooldown or duplicate the grenade");
            check(h, !AbilityService.inSuper(player), "Unshifted F must not start a super");
            h.succeed();
        } finally {
            TestPlayers.remove(player);
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void shiftFPacketRequiresAndConsumesFullSuperEnergy(GameTestHelper h) {
        ServerPlayer player = hunter(h, Element.ARC);
        try {
            equipHandMarkers(player);
            inputPacket(player, SHIFT);
            check(h, player.isShiftKeyDown(), "Input packet must update the server's shift state");
            GuardianData data = Guardians.data(player);
            data.setSuperEnergy(0.99f);
            swapPacket(player);
            assertHandsUnchanged(h, player);
            check(h, !AbilityService.inSuper(player) && data.superEnergy() == 0.99f,
                    "Shift+F below full energy must cancel swap without spending energy");
            data.setSuperEnergy(1f);
            swapPacket(player);
            assertHandsUnchanged(h, player);
            check(h, AbilityService.inSuper(player) && data.superEnergy() == 0f,
                    "Shift+F packet at full energy must start super and consume all energy");
            check(h, data.cooldown(AbilitySlot.GRENADE) == 0 && SimProjectile.activeCount(player) == 0,
                    "Shift+F must not also throw a grenade");
            h.succeed();
        } finally {
            TestPlayers.remove(player);
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void nonGuardianFPacketStillSwapsHands(GameTestHelper h) {
        ServerPlayer player = TestPlayers.create(h, PLAYER_POS, -90, 0);
        try {
            equipHandMarkers(player);
            swapPacket(player);
            check(h, player.getMainHandItem().is(Items.DIAMOND) && player.getMainHandItem().getCount() == 3
                    && player.getOffhandItem().is(Items.STICK) && player.getOffhandItem().getCount() == 2,
                    "Non-guardian control must reach the vanilla hand-swap handler");
            h.succeed();
        } finally {
            TestPlayers.remove(player);
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 40)
    public void scorchDotDeathCreditsOwnerOnce(GameTestHelper h) {
        ServerPlayer player = hunter(h, Element.SOLAR);
        Cow[] target = new Cow[1];
        delayed(h, 21, () -> {
            target[0] = h.spawn(EntityTypes.COW, new Vec3(5.5, 1, 6.5));
            target[0].setNoAi(true);
            target[0].setHealth(2f);
            Guardians.data(player).setSuperEnergy(0.25f);
            Statuses.scorch(player, target[0], 100);
            check(h, Statuses.has(target[0], Keyword.SCORCHED), "Scorch must be active before ticking");
        }, () -> {
            check(h, !target[0].isAlive(), "Normal scorch/fire ticks must kill the low-health target");
            check(h, target[0].getLastHurtByPlayer() == player, "DoT kill attribution must retain the scorch owner");
            check(h, Math.abs(Guardians.data(player).superEnergy() - (0.25f + AbilityService.killSuperEnergy)) < 1e-4,
                    "DoT death must grant exactly one kill's energy to its owner");
        }, () -> {
            TestPlayers.remove(player);
            if (target[0] != null) {
                Statuses.forget(target[0]);
                target[0].discard();
            }
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void vanillaFireDeathCreditsScorchOwnerOnce(GameTestHelper h) {
        ServerPlayer player = hunter(h, Element.SOLAR);
        Cow target = null;
        try {
            target = h.spawn(EntityTypes.COW, new Vec3(5.5, 1, 6.5));
            target.setNoAi(true);
            target.setHealth(1f);
            Guardians.data(player).setSuperEnergy(0.25f);
            Statuses.scorch(player, target, 100);
            check(h, target.hurtServer(h.getLevel(), target.damageSources().onFire(), 1f) && !target.isAlive(),
                    "Vanilla fire damage must kill the scorched target");
            check(h, target.getLastHurtByPlayer() == player, "Vanilla fire death must retain scorch attribution");
            check(h, Math.abs(Guardians.data(player).superEnergy() - (0.25f + AbilityService.killSuperEnergy)) < 1e-4,
                    "AFTER_DEATH must credit vanilla fire without waiting for a scorch pulse");
            h.succeed();
        } finally {
            TestPlayers.remove(player);
            if (target != null) {
                Statuses.forget(target);
                target.discard();
            }
        }
    }

    private static void doubleTapBoundary(GameTestHelper h, int gap, boolean shouldDodge) {
        ServerPlayer player = hunter(h, Element.ARC);
        int firstTick = h.getLevel().getServer().getTickCount();
        delayed(h, gap, () -> {
            inputPacket(player, SHIFT);
            inputPacket(player, SHIFT);
            check(h, Guardians.data(player).cooldown(AbilitySlot.CLASS_ABILITY) == 0,
                    "A first shift press or a held shift packet must not dodge");
            inputPacket(player, Input.EMPTY);
        }, () -> {
            check(h, h.getLevel().getServer().getTickCount() - firstTick == gap,
                    "Second press must occur exactly " + gap + " server ticks after the first");
            inputPacket(player, SHIFT);
            check(h, (Guardians.data(player).cooldown(AbilitySlot.CLASS_ABILITY) > 0) == shouldDodge,
                    "A " + gap + "-tick double tap must " + (shouldDodge ? "dodge" : "remain outside the dodge window"));
            check(h, (Guardians.runtime(player).invulnerableTicks > 0) == shouldDodge,
                    "Dodge i-frames must agree with the double-tap boundary");
        }, () -> TestPlayers.remove(player));
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void doubleTapAtSevenTicksDodges(GameTestHelper h) {
        doubleTapBoundary(h, 7, true);
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void doubleTapAtEightTicksDoesNotDodge(GameTestHelper h) {
        doubleTapBoundary(h, 8, false);
    }
}
