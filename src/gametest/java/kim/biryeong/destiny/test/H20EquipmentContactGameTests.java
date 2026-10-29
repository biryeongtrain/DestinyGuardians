package kim.biryeong.destiny.test;

import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.Element;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.bone.RenderedBone;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.TrackerModifier;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.phys.Vec3;
import net.minecraft.core.component.DataComponents;
import net.minecraft.world.entity.Display;
import kim.biryeong.destiny.DestinyGuardians;
import org.joml.Vector3f;

/** Native display geometry against actual transmitted BM poses, including inter-key samples. */
public final class H20EquipmentContactGameTests {
    private record DisplayPose(Vector3f position, Vector3f scale, org.joml.Quaternionf rotation) { }

    private static DisplayPose sent(GameTestHelper h, RenderedBone bone) {
        // W255 publishes only the second 25ms evaluation. globalState.current is an
        // internal cache, not the display transform sent by DisplayTransformer.transform.
        try {
            var sample = EquipmentDisplaySamples.class.getDeclaredMethod("sample", RenderedBone.class);
            sample.setAccessible(true);
            Object value = sample.invoke(null, bone);
            h.assertTrue(value != null, Component.literal("No published native equipment transform: " + bone.name()));
            var position = value.getClass().getDeclaredMethod("position"); position.setAccessible(true);
            var scale = value.getClass().getDeclaredMethod("scale"); scale.setAccessible(true);
            var rotation = value.getClass().getDeclaredMethod("rotation"); rotation.setAccessible(true);
            return new DisplayPose(new Vector3f((Vector3f) position.invoke(value)),
                    new Vector3f((Vector3f) scale.invoke(value)),
                    new org.joml.Quaternionf((org.joml.Quaternionf) rotation.invoke(value)));
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void arcSupportStaysOnStaffBetweenContactKeys(GameTestHelper h) {
        h.startSequence().thenWaitUntil(() -> h.assertTrue(BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),
                Component.literal("Versioned limb loaded"))).thenExecute(() -> {
            var p = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), 0, 0);
            TestCleanup.register(h, () -> TestPlayers.remove(p));
            h.assertTrue(PlayerAnimations.loop(p, "super_arc"), Component.literal("Arc ready"));
            PlayerAnimations.superItem(p, SuperVisuals.item(Element.ARC));
            var tracker = BetterModel.limb(HunterModelAssets.MODEL_NAME).orElseThrow()
                    .getOrCreate(ModPlayer.of(p.connection), TrackerModifier.DEFAULT);
            var clock = (ServerAnimationClock) (Object) tracker;
            for (int i = 0; i < 12; i++) clock.destiny$advanceServerTick();
            var left = tracker.bone(b -> b.name().rawName().equals("pli_left_item"));
            var right = tracker.bone(b -> b.name().rawName().equals("pri_right_item"));
            // Verify the native rendered stack, not merely the requested equipment value.
            try {
                var field = right.getDisplay().getClass().getDeclaredField("display");
                field.setAccessible(true);
                var nativeDisplay = (Display.ItemDisplay) field.get(right.getDisplay());
                h.assertTrue(DestinyGuardians.id("arc_staff_h28").equals(
                        nativeDisplay.getItemStack().get(DataComponents.ITEM_MODEL)),
                        Component.literal("Actual Arc equipment selects the H24 staff"));
            } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
            float max = 0;
            h.assertTrue(PlayerAnimations.superAttack(p, Element.ARC), Component.literal("Arc strike"));
            for (int i = 0; i < 13; i++) {
                clock.destiny$advanceServerTick();
                var r = sent(h, right);
                var support = new Vector3f(0, 6f / 16, 0).mul(r.scale()).rotate(r.rotation()).add(r.position());
                float gap = support.distance(sent(h, left).position());
                max = Math.max(max, gap);
                System.out.println("H20 completed tick=" + (i+1) + " gap=" + gap);
            }
            PlayerAnimations.stop(p);
            h.assertTrue(max < .025, Component.literal("Staff support inter-key maximum gap=" + max));
            h.succeed();
        });
    }
    private static void powerSweep(GameTestHelper h, boolean deploy) {
        h.startSequence().thenWaitUntil(() -> h.assertTrue(BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),
                Component.literal("H26 loaded"))).thenExecute(() -> {
            var p = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), 0, 0);
            TestCleanup.register(h, () -> TestPlayers.remove(p));
            h.assertTrue(PlayerAnimations.loop(p, "super_arc"), Component.literal("Arc ready"));
            PlayerAnimations.superItem(p, SuperVisuals.item(Element.ARC));
            var tracker = BetterModel.limb(HunterModelAssets.MODEL_NAME).orElseThrow()
                    .getOrCreate(ModPlayer.of(p.connection), TrackerModifier.DEFAULT);
            var clock = (ServerAnimationClock) (Object) tracker;
            for (int i=0;i<12;i++) clock.destiny$advanceServerTick();
            var right = tracker.bone(b -> b.name().rawName().equals("pri_right_item"));
            var initial = new Vector3f(0,1,0).rotate(sent(h, right).rotation());
            h.assertTrue(deploy ? PlayerAnimations.play(p,"super_arc_start") : PlayerAnimations.superAttack(p,Element.ARC),
                    Component.literal("Requested one-shot"));
            var axes = new java.util.ArrayList<Vector3f>();
            int duration = deploy ? SuperAttackTiming.ARC_DEPLOY : SuperAttackTiming.ARC_RECOVERY;
            long startFrames = clock.destiny$serverFrames();
            var playback = h.startSequence();
            for (int elapsed = 1; elapsed <= duration + 2; elapsed++) {
                final int tick = elapsed;
                playback.thenExecuteAfter(1, () -> {
                    // Observe the previous completed END_SERVER_TICK. Let the production
                    // lifecycle retire the one-shot instead of advancing BM at fixed world time.
                    axes.add(new Vector3f(0,1,0).rotate(sent(h, right).rotation()));
                    h.assertTrue(clock.destiny$serverFrames() == startFrames + 2L*tick,
                            Component.literal("Exactly two evaluations per real server tick: actual="+clock.destiny$serverFrames()+" expected="+(startFrames+2L*tick)+" closed="+tracker.isClosed()+" alive="+p.isAlive()+" removed="+p.isRemoved()+" disconnected="+p.hasDisconnected()+" clip="+PlayerAnimations.activeClip(p)));
                    if (tick == duration + 1)
                        h.assertTrue("h15_super_arc".equals(PlayerAnimations.activeClip(p)),
                                Component.literal("Nominal deadline retires one-shot and restores the ready loop"));
                });
            }
            playback.thenExecute(() -> {
                // Imported W197/W199 motion moved the attack peak away from H26 .05/.10.
                // Keep the one-tick power requirement and inspect the complete source window.
                double maxAngle = 0;
                for (int i=1;i<duration;i++)
                    maxAngle = Math.max(maxAngle, Math.toDegrees(axes.get(i-1).angle(axes.get(i))));
                System.out.println("H20 source sweep deploy="+deploy+" maximum="+maxAngle+" axes="+axes);
                h.assertTrue(maxAngle > (deploy ? 90 : 60), Component.literal("Source-window native power sweep: "+maxAngle));
                h.assertTrue(initial.distance(axes.getLast()) < .001,
                        Component.literal("Ready orientation restored after the completed lifecycle tick"));
                PlayerAnimations.stop(p);h.succeed();
            });
        });
    }
    @GameTest(structure="destiny-test:floor", maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void h26AttackNativeStaffSweepsOverSixtyDegreesInOneTick(GameTestHelper h) { powerSweep(h,false); }
    @GameTest(structure="destiny-test:floor", maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void h26DeployNativeStaffPowerFlourishThenRecovers(GameTestHelper h) { powerSweep(h,true); }

}
