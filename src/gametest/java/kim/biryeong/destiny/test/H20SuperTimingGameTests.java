package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.Tasks;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.fx.SuperAttackTiming;
import kim.biryeong.destiny.fx.SuperVfx;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.input.GuardianAction;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.IntConsumer;

/**
 * Real equipped abilities, sessions, combat targets and normal global FX/projectile/animation ticks.
 * Embedded owners are NOT in PlayerList: advance tickPlayer exactly once per actual server tick.
 * This is not native client-input or pixel/contact-pose verification. No global tuning mutations.
 */
public final class H20SuperTimingGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final float HEALTH = 400;

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static void loaded(GameTestHelper h, Runnable test) {
        h.startSequence().thenWaitUntil(() -> check(h,
                BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(), "Waiting for versioned H20 limb"))
                .thenExecute(test);
    }

    private static int deploy(Element element) {
        return element == Element.ARC ? SuperAttackTiming.ARC_DEPLOY : SuperAttackTiming.SOLAR_DEPLOY;
    }

    private static int contact(Element element) {
        return element == Element.ARC ? SuperAttackTiming.ARC_CONTACT : SuperAttackTiming.SOLAR_CONTACT;
    }

    private static int recovery(Element element) {
        return element == Element.ARC ? SuperAttackTiming.ARC_RECOVERY : SuperAttackTiming.SOLAR_RECOVERY;
    }

    private static final class Fixture {
        final GameTestHelper h;
        final Element element;
        final ServerPlayer player;
        final Husk target;
        final Vec3 targetPosition;
        final float damage;

        Fixture(GameTestHelper h, Element element) {
            this.h = h;
            this.element = element;
            player = TestPlayers.hunter(h, element, new Vec3(2.5, 1, 6.5), -90, 0);
            TestCleanup.register(h, () -> TestPlayers.remove(player));
            check(h, !h.getLevel().getServer().getPlayerList().getPlayers().contains(player),
                    "Embedded fixture must not also receive the PlayerList ability tick");
            player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK, 2));
            player.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.DIAMOND, 3));
            target = h.spawn(EntityTypes.HUSK, new Vec3(5.5, 1, 6.5));
            TestCleanup.register(h, () -> { Statuses.forget(target); target.discard(); });
            target.setNoAi(true);
            target.setNoGravity(true);
            target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HEALTH);
            target.getAttribute(Attributes.ARMOR).setBaseValue(0);
            target.setHealth(HEALTH);
            // Isolate direct cast damage from vanilla fire/custom scorch pulses, not from weapon hits.
            target.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 1200, 0, false, false));
            targetPosition = target.position();
            damage = (float) AbilityService.equipped(player, AbilitySlot.SUPER).orElseThrow()
                    .param("damage", element == Element.ARC ? 16 : 80);
            var renderer = BetterModel.limb(HunterModelAssets.MODEL_NAME).orElseThrow();
            String prefix = "h15_super_" + element.getSerializedName();
            check(h, renderer.animation(prefix + "_start").isPresent()
                    && renderer.animation(prefix + "_attack").isPresent(), "H20 deploy and attack clips must exist");
        }

        void startSuper() {
            Guardians.data(player).setSuperEnergy(1);
            check(h, AbilityService.use(player, AbilitySlot.SUPER) == AbilityService.Result.OK, "Real super activation");
            check(h, AbilityService.inSuper(player) && Guardians.data(player).superEnergy() == 0,
                    "Super activation creates session and consumes energy");
            check(h, PlayerAnimations.isPlaying(player), "Activation has a real limb playback");
            check(h, element != Element.SOLAR || !SuperCamera.active(player), "Solar must not acquire rear camera");
            inventory();
        }

        void primary() {
            check(h, AbilityService.perform(player, GuardianAction.PRIMARY), "Primary routed to active session");
        }

        void health(float expected, String phase) {
            check(h, Math.abs(target.getHealth() - expected) < .01f,
                    phase + ": expected health " + expected + ", got " + target.getHealth());
        }

        void inventory() {
            check(h, player.getMainHandItem().is(Items.STICK) && player.getMainHandItem().getCount() == 2
                    && player.getOffhandItem().is(Items.DIAMOND) && player.getOffhandItem().getCount() == 3,
                    "Visual equipment must not mutate either real hand");
        }

        void step() {
            // Keep fixture geometry fixed after knockback; never reset target health between contacts.
            target.setPos(targetPosition);
            target.setDeltaMovement(Vec3.ZERO);
            AbilityService.tickPlayer(player);
        }

        void cancelled() {
            check(h, !AbilityService.inSuper(player), "Cancelled session stays absent");
            check(h, !PlayerAnimations.isPlaying(player) && !SuperCamera.active(player),
                    "Cancellation immediately releases limb, equipment and owned camera");
            check(h, SuperVfx.activeCount(player) == 0 && SuperVfx.lifecycleCount(player) == 0,
                    "Cancellation cannot leave owned super effects");
            inventory();
        }
    }

    /** Assertions run in GameTest callbacks, NOT inside Tasks, whose exception handler swallows failures. */
    private static void ticks(GameTestHelper h, List<Fixture> fixtures, int total, IntConsumer afterTick) {
        int start = h.getLevel().getServer().getTickCount();
        // Pre-register the whole sequence; never insert callbacks while fastutil is iterating.
        var sequence = h.startSequence();
        for (int elapsed = 1; elapsed <= total; elapsed++) {
            final int age = elapsed;
            sequence.thenExecuteAfter(1, () -> {
                check(h, h.getLevel().getServer().getTickCount() - start == age,
                        "Fixture must advance only once per real server tick: T+" + age);
                fixtures.forEach(Fixture::step);
                afterTick.accept(age);
                if (age == total) h.succeed();
            });
        }
    }

    private static void queuedDeploy(GameTestHelper h, Element element) {
        loaded(h, () -> {
            Fixture f = new Fixture(h, element);
            f.startSuper();
            for (int i = 0; i < 6; i++) f.primary();
            f.health(HEALTH, "Deploy input is not contact");
            int hitAt = deploy(element) + contact(element);
            ticks(h, List.of(f), hitAt, elapsed -> {
                if (elapsed < hitAt) f.health(HEALTH, "No damage during deploy/windup tick " + elapsed);
                else f.health(HEALTH - f.damage, "Exactly one coalesced queued contact");
                if (elapsed < deploy(element)) f.primary();
                if (element == Element.SOLAR) {
                    float remaining = Guardians.runtime(f.player).superSession.remaining();
                    if (elapsed <= deploy(element)) check(h, remaining > .9f, "Queued deploy input cannot spend a round early");
                    else check(h, Math.abs(remaining - 2f / 3) < .001f, "Repeated queued input consumes only one round");
                }
                f.inventory();
            });
        });
    }

    private static void assertBusy(Fixture f) {
        var runtime = Guardians.runtime(f.player);
        var session = runtime.superSession;
        Vec3 velocity = f.player.getDeltaMovement();
        int invulnerability = runtime.invulnerableTicks;
        int tasks = Tasks.count(f.player), projectiles = SimProjectile.activeCount(f.player);
        for (AbilitySlot slot : new AbilitySlot[]{AbilitySlot.GRENADE, AbilitySlot.MELEE, AbilitySlot.CLASS_ABILITY}) {
            check(f.h, Guardians.data(f.player).cooldown(slot) == 0, "BUSY test begins with ready " + slot);
            check(f.h, AbilityService.use(f.player, slot) == AbilityService.Result.BUSY, "Super rejects ordinary " + slot);
            check(f.h, Guardians.data(f.player).cooldown(slot) == 0, "BUSY cannot consume " + slot + " cooldown");
        }
        check(f.h, runtime.superSession == session && PlayerAnimations.isPlaying(f.player), "BUSY cannot replace active playback/session");
        check(f.h, Tasks.count(f.player) == tasks && SimProjectile.activeCount(f.player) == projectiles,
                "BUSY cannot enqueue ordinary side effects");
        check(f.h, f.player.getDeltaMovement().equals(velocity) && runtime.invulnerableTicks == invulnerability,
                "Rejected dodge cannot change physics or invulnerability");
        f.inventory();
    }

    private static void postDeployContact(GameTestHelper h, Element element, boolean busy) {
        loaded(h, () -> {
            Fixture f = new Fixture(h, element);
            f.startSuper();
            if (busy) {
                assertBusy(f);
                f.player.setOnGround(false);
                boolean deployingArc = element == Element.ARC;
                check(h, AbilityService.use(f.player, AbilitySlot.JUMP) == (deployingArc
                                ? AbilityService.Result.BUSY : AbilityService.Result.OK),
                        "H23 Arc deploy gates air jump; Solar remains immediately available");
                check(h, Guardians.runtime(f.player).airJumpsUsed == (deployingArc ? 0 : 1),
                        "Only an available JUMP consumes an air jump");
            }
            int hitAt = deploy(element) + contact(element);
            int until = deploy(element) + recovery(element) - 1;
            ticks(h, List.of(f), until, elapsed -> {
                f.health(elapsed < hitAt ? HEALTH : HEALTH - f.damage, "Contact/recovery tick " + elapsed);
                if (elapsed >= deploy(element)) {
                    if (busy && element == Element.ARC && elapsed == deploy(element)) {
                        f.player.setOnGround(false);
                        check(h, AbilityService.use(f.player, AbilitySlot.JUMP) == AbilityService.Result.OK,
                                "Air jump becomes available at H23 Arc deployment boundary");
                        check(h, Guardians.runtime(f.player).airJumpsUsed == 1, "Unlocked JUMP executes once");
                    }
                    // Input follows this tick's service advance. First contact advance is NEXT tick.
                    for (int i = 0; i < 4; i++) f.primary();
                    if (busy) assertBusy(f);
                }
                if (element == Element.SOLAR && elapsed >= deploy(element)) check(h,
                        Math.abs(Guardians.runtime(f.player).superSession.remaining() - 2f / 3) < .001f,
                        "Contact/recovery spam cannot consume another round");
                check(h, AbilityService.inSuper(f.player), "First attack returns to active ready session");
                f.inventory();
            });
        });
    }

    private static void recoveryBoundary(GameTestHelper h, Element element) {
        loaded(h, () -> {
            Fixture f = new Fixture(h, element);
            f.startSuper();
            int first = deploy(element) + contact(element);
            // Honor configured intervals without changing global tuning for parallel tests.
            int interval = Math.max(recovery(element), (int) AbilityService.equipped(f.player, AbilitySlot.SUPER)
                    .orElseThrow().param(element == Element.ARC ? "strike_interval_ticks" : "shot_interval_ticks", recovery(element)));
            int secondRequest = deploy(element) + interval;
            int second = secondRequest + contact(element);
            ticks(h, List.of(f), second, elapsed -> {
                int hits = elapsed < first ? 0 : elapsed < second ? 1 : 2;
                f.health(HEALTH - hits * f.damage, "Exact recovery boundary tick " + elapsed);
                if (elapsed == deploy(element) || elapsed == secondRequest) f.primary();
                if (element == Element.SOLAR && elapsed == second) check(h,
                        Math.abs(Guardians.runtime(f.player).superSession.remaining() - 1f / 3) < .001f,
                        "Exactly two accepted rounds after recovery");
            });
        });
    }

    private static void cancellation(GameTestHelper h, Element element, int mode) {
        loaded(h, () -> {
            Fixture f = new Fixture(h, element);
            f.startSuper();
            if (mode == 0) f.primary(); // Cancel an input queued during deploy.
            int cancelAt = mode == 0 ? deploy(element) - 1 : deploy(element) + contact(element) - 1;
            ticks(h, List.of(f), deploy(element) + contact(element) + 3, elapsed -> {
                f.health(HEALTH, "Cancelled deploy/contact cannot deal late damage, tick " + elapsed);
                if (mode != 0 && elapsed == deploy(element)) f.primary();
                if (elapsed == cancelAt) {
                    if (mode == 0) AbilityService.endSuper(f.player);
                    else if (mode == 1) AbilityService.cleanup(f.player);
                    else f.player.setHealth(0); // Do not invoke cleanup: tickPlayer must detect death itself.
                }
                if (elapsed > cancelAt || elapsed == cancelAt && mode != 2) f.cancelled();
            });
        });
    }

    private static void ordinaryIntoSuper(GameTestHelper h, Element element) {
        loaded(h, () -> {
            List<Fixture> fixtures = new ArrayList<>();
            List<SimProjectile> existing = new ArrayList<>();
            List<AtomicInteger> unrelated = new ArrayList<>();
            for (AbilitySlot slot : new AbilitySlot[]{AbilitySlot.GRENADE, AbilitySlot.MELEE, AbilitySlot.CLASS_ABILITY}) {
                Fixture f = new Fixture(h, element);
                fixtures.add(f);
                AtomicInteger calls = new AtomicInteger();
                unrelated.add(calls);
                existing.add(SimProjectile.launch(f.player, f.player.position().add(0, 12, 0), Vec3.ZERO, 0, 80,
                        new ItemStack(Items.SNOWBALL), .2f, element.color(), hit -> {}));
                Tasks.run(f.player, h.getLevel(), age -> { calls.incrementAndGet(); return true; });
                check(h, AbilityService.use(f.player, slot) == AbilityService.Result.OK, "Ordinary " + slot + " accepted before super");
                check(h, slot == AbilitySlot.GRENADE
                                ? kim.biryeong.destiny.ability.GrenadeThrow.active(f.player)
                                    && !kim.biryeong.destiny.ability.GrenadeThrow.prop(f.player).isEmpty()
                                    && Tasks.count(f.player) == 1
                                : Tasks.count(f.player) > 1,
                        "Ordinary contact is pending in its actual owner (throw timeline or contact task)");
                f.startSuper(); // Exercise the actual startSuper cancellation hook, not cancelPending directly.
            }
            ticks(h, fixtures, 8, elapsed -> {
                for (int i = 0; i < fixtures.size(); i++) {
                    Fixture f = fixtures.get(i);
                    f.health(HEALTH, "Super entry cancels old ordinary contact");
                    check(h, !existing.get(i).isDone() && SimProjectile.activeCount(f.player) == 1,
                            "No late ordinary projectile; pre-existing projectile survives");
                    check(h, AbilityService.inSuper(f.player) && PlayerAnimations.isPlaying(f.player),
                            "Old ordinary callbacks cannot stop the new super");
                    if (elapsed >= 2) check(h, unrelated.get(i).get() > 0 && Tasks.count(f.player) == 1,
                            "Only pending ordinary tasks are dropped; unrelated task survives");
                    f.inventory();
                }
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void arcQueuedDeployInputWaitsAndCoalesces(GameTestHelper h) { queuedDeploy(h, Element.ARC); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void solarQueuedDeployInputWaitsAndConsumesOneRound(GameTestHelper h) { queuedDeploy(h, Element.SOLAR); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void arcContactAndRecoveryRejectPrimarySpam(GameTestHelper h) { postDeployContact(h, Element.ARC, false); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void solarContactAndRecoveryRejectPrimarySpam(GameTestHelper h) { postDeployContact(h, Element.SOLAR, false); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void arcNextContactRequiresRecoveryBoundary(GameTestHelper h) { recoveryBoundary(h, Element.ARC); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void solarNextContactRequiresRecoveryBoundary(GameTestHelper h) { recoveryBoundary(h, Element.SOLAR); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void arcExplicitEndCancelsQueuedDeploy(GameTestHelper h) { cancellation(h, Element.ARC, 0); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void solarExplicitEndCancelsQueuedDeploy(GameTestHelper h) { cancellation(h, Element.SOLAR, 0); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void arcCleanupOneTickBeforeContactCancelsDamage(GameTestHelper h) { cancellation(h, Element.ARC, 1); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void solarCleanupOneTickBeforeContactCancelsDamage(GameTestHelper h) { cancellation(h, Element.SOLAR, 1); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void arcDeathOneTickBeforeContactCancelsDamage(GameTestHelper h) { cancellation(h, Element.ARC, 2); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void solarDeathOneTickBeforeContactCancelsDamage(GameTestHelper h) { cancellation(h, Element.SOLAR, 2); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void arcSuperRejectsOrdinarySkillsButAllowsJump(GameTestHelper h) { postDeployContact(h, Element.ARC, true); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void solarSuperRejectsOrdinarySkillsButAllowsJump(GameTestHelper h) { postDeployContact(h, Element.SOLAR, true); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void arcEntryCancelsAllThreeOrdinaryWindupsWithoutBroadCleanup(GameTestHelper h) { ordinaryIntoSuper(h, Element.ARC); }

    @GameTest(structure = FLOOR, maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void solarEntryCancelsAllThreeOrdinaryWindupsWithoutBroadCleanup(GameTestHelper h) { ordinaryIntoSuper(h, Element.SOLAR); }
}
