package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.hunter.HunterDodge;
import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.SuperVisuals;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** Register this class in fabric-gametest. Uses real renderers and normal AbilityService ticks. */
public final class HunterAnimationH15GameTests {
    private static final String FLOOR = "destiny-test:floor";

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static void loaded(GameTestHelper h, Runnable action) {
        h.startSequence().thenWaitUntil(() -> check(h, BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),
                "Waiting for H15 player limb")).thenExecute(action);
    }

    private static ServerPlayer owner(GameTestHelper h) {
        ServerPlayer p = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), -90, 12);
        p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.DIAMOND_SWORD));
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.TORCH));
        h.runBeforeTestEnd(() -> TestPlayers.remove(p));
        return p;
    }

    private static void inventory(GameTestHelper h, ServerPlayer p) {
        check(h, p.getMainHandItem().is(Items.DIAMOND_SWORD) && p.getOffhandItem().is(Items.TORCH),
                "Visual equipment must never change real inventory");
    }

    private static void ready(GameTestHelper h, ServerPlayer p, Element e) {
        check(h, PlayerAnimations.loop(p, "super_" + e.getSerializedName()), "Ready loop starts");
        PlayerAnimations.superItem(p, SuperVisuals.item(e));
    }

    private static void release(GameTestHelper h, Element element) {
        loaded(h, () -> {
            ServerPlayer p = owner(h);
            ready(h, p, element);
            check(h, PlayerAnimations.superAttack(p, element), "Accepted shot starts one-shot");
            PlayerAnimations.finishSuper(p);
            PlayerAnimations.finishSuper(p);
            check(h, PlayerAnimations.isPlaying(p), "Final release survives gameplay session end");
            check(h, !PlayerAnimations.superAttack(p, element), "Closing playback rejects new attacks");
            int start = h.getLevel().getServer().getTickCount();
            h.runAfterDelay(2, () -> check(h, PlayerAnimations.isPlaying(p), "Do not truncate final shot on next tick"));
            h.runAfterDelay(25, () -> {
                check(h, h.getLevel().getServer().getTickCount() - start == 25, "Only normal server ticks");
                check(h, !PlayerAnimations.isPlaying(p), "Final shot and equipment expire after recovery");
                inventory(h, p);
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void voidReleaseFinishesAfterGameplaySessionEnds(GameTestHelper h) { release(h, Element.VOID); }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void solarLastShotFinishesAfterGameplaySessionEnds(GameTestHelper h) { release(h, Element.SOLAR); }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void attackReturnsToReadyAndCanAttackAgain(GameTestHelper h) {
        loaded(h, () -> {
            ServerPlayer p = owner(h);
            ready(h, p, Element.ARC);
            check(h, PlayerAnimations.superAttack(p, Element.ARC), "First sweep");
            h.runAfterDelay(22, () -> {
                check(h, PlayerAnimations.isPlaying(p), "Attack completion retains ready loop");
                check(h, PlayerAnimations.superAttack(p, Element.ARC), "Ready loop accepts another sweep");
                inventory(h, p);
                PlayerAnimations.stop(p);
                check(h, !PlayerAnimations.isPlaying(p), "Explicit cancellation is immediate");
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void cardinalDodgesPreserveAimPhysicsAndRestoreVanilla(GameTestHelper h) {
        loaded(h, () -> {
            List<ServerPlayer> owners = new ArrayList<>();
            Input[] inputs = {
                    new Input(true, false, false, false, false, false, false),
                    new Input(false, true, false, false, false, false, false),
                    new Input(false, false, true, false, false, false, false),
                    new Input(false, false, false, true, false, false, false)};
            Vec3[] expected = {new Vec3(1.15, .18, 0), new Vec3(-1.15, .18, 0),
                    new Vec3(0, .18, -1.15), new Vec3(0, .18, 1.15)};
            HunterDodge dodge = new HunterDodge(Identifier.parse("destiny:h15_test_dodge"),
                    "H15 test dodge", HunterDodge.Variant.MARKSMAN, 12);
            for (int i = 0; i < inputs.length; i++) {
                ServerPlayer p = owner(h);
                owners.add(p);
                Guardians.runtime(p).lastInput = inputs[i];
                check(h, dodge.activate(p), "Dodge activates");
                check(h, p.getDeltaMovement().distanceTo(expected[i]) < 1.0e-5, "Original input-relative velocity");
                check(h, Guardians.runtime(p).invulnerableTicks == 6, "Original six invulnerable ticks");
                check(h, p.getYRot() == -90 && p.getXRot() == 12, "Dodge never rotates player aim");
                check(h, PlayerAnimations.isPlaying(p), "Directional roll starts");
            }
            h.runAfterDelay(25, () -> {
                for (ServerPlayer p : owners) {
                    check(h, !PlayerAnimations.isPlaying(p), "Roll releases the limb after normal ticks");
                    inventory(h, p);
                }
                h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 1200)
    public void cleanupOverridesFinalReleaseAndPreservesOtherOwner(GameTestHelper h) {
        loaded(h, () -> {
            ServerPlayer p = owner(h), other = owner(h);
            ready(h, p, Element.VOID);
            ready(h, other, Element.ARC);
            check(h, PlayerAnimations.superAttack(p, Element.VOID), "Release starts");
            PlayerAnimations.finishSuper(p);
            AbilityService.cleanup(p);
            check(h, !PlayerAnimations.isPlaying(p), "Death/logout/class cleanup overrides graceful finish");
            check(h, PlayerAnimations.isPlaying(other), "Other owner stays ready");
            h.runAfterDelay(25, () -> {
                check(h, !PlayerAnimations.isPlaying(p), "No late callback resurrects a cleaned playback");
                check(h, PlayerAnimations.isPlaying(other), "Cleanup remains owner-local");
                inventory(h, p);
                h.succeed();
            });
        });
    }
}
