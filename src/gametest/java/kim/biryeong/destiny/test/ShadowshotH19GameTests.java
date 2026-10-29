package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.ShadowshotTiming;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

/** Embedded fixtures explicitly advance ability ticks; live native input is a separate QA gate. */
public final class ShadowshotH19GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static void loaded(GameTestHelper h, Runnable test) {
        h.startSequence().thenWaitUntil(() -> check(h, BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),
                "H19 limb loaded")).thenExecute(test);
    }
    private static ServerPlayer start(GameTestHelper h) {
        ServerPlayer p = TestPlayers.hunter(h, Element.VOID, new Vec3(2.5, 1, 6.5), -90, 0);
        TestCleanup.register(h, () -> TestPlayers.remove(p));
        Guardians.data(p).setSuperEnergy(1);
        check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK, "Void starts");
        return p;
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void bowDrawDelaysArrowAndRepeatedPrimaryCannotDuplicate(GameTestHelper h) {
        loaded(h, () -> {
            ServerPlayer p = start(h);
            AbilityService.perform(p, GuardianAction.PRIMARY);
            check(h, SimProjectile.activeCount(p) == 0, "Button press is not the arrow contact");
            for (int i = 1; i < ShadowshotTiming.RELEASE_TICKS; i++) {
                AbilityService.perform(p, GuardianAction.PRIMARY);
                AbilityService.tickPlayer(p);
                check(h, SimProjectile.activeCount(p) == 0 && AbilityService.inSuper(p), "Draw retains session without arrow");
            }
            AbilityService.tickPlayer(p);
            check(h, SimProjectile.activeCount(p) == 1, "Exactly one arrow on release tick");
            check(h, !AbilityService.inSuper(p), "Gameplay ends after contact");
            check(h, PlayerAnimations.isPlaying(p), "Bow follow-through survives session end");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void activationAloneDrawsAndReleasesExactlyOneArrow(GameTestHelper h) {
        loaded(h, () -> {
            ServerPlayer p = start(h);
            check(h, Guardians.data(p).superEnergy() == 0f, "Activation consumes the charge once");
            check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.BUSY,
                    "Repeated activation cannot restart the automatic cast");
            for (int i = 1; i < ShadowshotTiming.RELEASE_TICKS; i++) {
                AbilityService.tickPlayer(p);
                check(h, AbilityService.inSuper(p) && SimProjectile.activeCount(p) == 0,
                        "Automatic windup has no early projectile at tick " + i);
            }
            AbilityService.tickPlayer(p);
            check(h, SimProjectile.activeCount(p) == 1 && !AbilityService.inSuper(p),
                    "Without any PRIMARY, activation releases once at tick seven");
            check(h, PlayerAnimations.isPlaying(p), "Automatic shot retains recovery animation");
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void cancelledDrawDoesNotLaunchLateArrow(GameTestHelper h) {
        loaded(h, () -> {
            ServerPlayer p = start(h);
            for (int i = 0; i < ShadowshotTiming.DRAW_TICKS; i++) AbilityService.tickPlayer(p);
            AbilityService.cleanup(p);
            for (int i = 0; i < 20; i++) AbilityService.tickPlayer(p);
            check(h, SimProjectile.activeCount(p) == 0, "Cleanup invalidates pending release");
            check(h, !PlayerAnimations.isPlaying(p), "Limb/equipment also release");
            h.succeed();
        });
    }
}
