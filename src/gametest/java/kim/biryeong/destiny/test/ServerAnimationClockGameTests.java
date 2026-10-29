package kim.biryeong.destiny.test;

import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.ServerAnimationClock;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.TrackerModifier;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.phys.Vec3;

/** Real BetterModel mixin + pipeline. Pixel interpolation has a separate live Vision gate. */
public final class ServerAnimationClockGameTests {
    private static org.joml.Vector3f nockOffset(int stage) {
        var stack = kim.biryeong.destiny.fx.SuperVisuals.bowStage(stage);
        var id = java.util.Objects.requireNonNull(stack.get(net.minecraft.core.component.DataComponents.ITEM_MODEL));
        try (var stream = ServerAnimationClockGameTests.class.getResourceAsStream(
                "/assets/" + id.getNamespace() + "/models/item/" + id.getPath() + ".json")) {
            var model = com.google.gson.JsonParser.parseReader(new java.io.InputStreamReader(
                    java.util.Objects.requireNonNull(stream), java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
            var display = model.getAsJsonObject("display").getAsJsonObject("thirdperson_lefthand");
            float yaw = -display.getAsJsonArray("rotation").get(1).getAsFloat(); // native left-hand sign
            var shaft = java.util.stream.StreamSupport.stream(model.getAsJsonArray("elements").spliterator(), false)
                    .map(com.google.gson.JsonElement::getAsJsonObject)
                    .filter(e -> e.has("name") && e.get("name").getAsString().endsWith("nocked_shaft"))
                    .findFirst().orElseThrow();
            float x = shaft.getAsJsonArray("to").get(0).getAsFloat() - 8;
            return new org.joml.Vector3f(x / 16, 0, 0).rotateY((float) Math.toRadians(yaw))
                    .add(0, display.getAsJsonArray("translation").get(1).getAsFloat() / 16, 0)
                    .rotateY((float) Math.PI); // DisplayRenderer.ItemDisplayRenderer.submitInner
        } catch (java.io.IOException e) { throw new AssertionError(e); }
    }

    private static kr.toxicity.model.api.bone.BoneMovement sent(kr.toxicity.model.api.bone.RenderedBone bone) {
        try {
            var global = bone.getClass().getDeclaredField("globalState"); global.setAccessible(true);
            Object handler = global.get(bone);
            var current = handler.getClass().getDeclaredField("current"); current.setAccessible(true);
            return new kr.toxicity.model.api.bone.BoneMovement().set((kr.toxicity.model.api.bone.BoneMovement) current.get(handler));
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void realPipelineReachesEveryDrawStageAndReleaseWhileAimingUpAndDown(GameTestHelper h) {
        h.startSequence().thenWaitUntil(() -> h.assertTrue(BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),
                Component.literal("Versioned limb loaded"))).thenExecute(() -> {
            float maxReachGap = 0;
            float maxDrawGap = 0;
            for (int pitch : new int[]{-30, 0, 30}) {
            int yaw = pitch == -30 ? 70 : pitch == 30 ? -150 : 0;
            var p = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), yaw, pitch);
            p.yBodyRot = yaw + 55; // Deliberately disagree with view: aim may not use body smoothing.
            TestCleanup.register(h, () -> TestPlayers.remove(p));
            h.assertTrue(PlayerAnimations.loop(p, "super_void"), Component.literal("Ready loop"));
            PlayerAnimations.superItem(p, kim.biryeong.destiny.fx.SuperVisuals.bowStage(0), true);
            var tracker = BetterModel.limb(HunterModelAssets.MODEL_NAME).orElseThrow()
                    .getOrCreate(ModPlayer.of(p.connection), TrackerModifier.DEFAULT);
            var clock = (ServerAnimationClock) (Object) tracker;
            var left = tracker.bone(b -> b.name().rawName().equals("pli_left_item"));
            var right = tracker.bone(b -> b.name().rawName().equals("pri_right_item"));
            h.assertTrue(PlayerAnimations.superAttack(p, kim.biryeong.destiny.guardian.Element.VOID),
                    Component.literal("Draw starts"));
            for (int tick = 1; tick <= 7; tick++) {
                clock.destiny$advanceServerTick();
                // worldPosition() rebuilds a LOCAL Euler quaternion while lerping its cached
                // WORLD movement; it is not the transmitted display transform. Inspect the
                // actual snapshot used by sendTransformation before equipment offset conversion.
                var leftSent = sent(left);
                int stage = tick < 4 ? 0 : tick == 4 ? 1 : tick == 5 ? 2 : 3;
                PlayerAnimations.superItem(p, kim.biryeong.destiny.fx.SuperVisuals.bowStage(stage), true);
                var nock = nockOffset(stage).rotate(leftSent.rotation()).add(leftSent.position());
                var hand = sent(right).position();
                System.out.println("Selected bow sent contact pitch=" + pitch + " tick=" + tick + " stage=" + stage
                        + " hand=" + hand + " nock=" + nock + " gap=" + hand.distance(nock));
                if (tick == 1) maxReachGap = Math.max(maxReachGap, hand.distance(nock));
                else maxDrawGap = Math.max(maxDrawGap, hand.distance(nock));
                if (tick == 6 || tick == 7) {
                    var emitted = tracker.getPipeline().getRotation();
                    var arrow = new org.joml.Vector3f(0, 0, 1).rotate(leftSent.rotation())
                            .rotateY(-(float) Math.toRadians(emitted.y()));
                    var look = p.getLookAngle();
                    double dot = arrow.dot(new org.joml.Vector3f((float) look.x, (float) look.y, (float) look.z));
                    h.assertTrue(dot > .9999, Component.literal("Actual display arrow follows gameplay aim, pitch="
                            + pitch + " yaw=" + yaw + " emitted=" + emitted + " dot=" + dot));
                }
            }
            PlayerAnimations.stop(p);
            }
            // H22 is predrawn even in ready. Retain the original strict contact bounds;
            // inspect the selected item's real geometry, not the old H20 stage fixture.
            h.assertTrue(maxReachGap < .04, Component.literal("Initial reach gap=" + maxReachGap));
            h.assertTrue(maxDrawGap < .005, Component.literal("Held/draw/release gap=" + maxDrawGap));
            h.succeed();
        });
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void ownedClockCannotAdvanceOnWallTimeAndClosedTrackerCannotRestart(GameTestHelper h) {
        h.startSequence().thenWaitUntil(() -> h.assertTrue(BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),
                Component.literal("Versioned limb loaded"))).thenExecute(() -> {
            var p = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), 0, 0);
            TestCleanup.register(h, () -> TestPlayers.remove(p));
            h.assertTrue(PlayerAnimations.loop(p, "super_void"), Component.literal("Ready loop"));
            var tracker = BetterModel.limb(HunterModelAssets.MODEL_NAME).orElseThrow()
                    .getOrCreate(ModPlayer.of(p.connection), TrackerModifier.DEFAULT);
            var clock = (ServerAnimationClock) (Object) tracker;
            long initial = clock.destiny$serverFrames();
            h.assertTrue(PlayerAnimations.superAttack(p, kim.biryeong.destiny.guardian.Element.VOID),
                    Component.literal("Draw starts"));
            clock.destiny$advanceServerTick();
            var hand = tracker.bone(b -> b.name().rawName().equals("pri_right_item"));
            h.assertTrue(hand != null, Component.literal("Draw equipment bone exists: " + tracker.bones()));
            var before = new org.joml.Vector3f(hand.worldPosition());
            try { Thread.sleep(225); } catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new RuntimeException(e); }
            h.assertTrue(clock.destiny$serverFrames() == initial + 2,
                    Component.literal("A 225ms server stall cannot advance the owned clock"));
            h.assertTrue(before.distance(hand.worldPosition()) < .00001,
                    Component.literal("Actual draw hand does not advance during a server stall"));
            clock.destiny$advanceServerTick();
            h.assertTrue(clock.destiny$serverFrames() == initial + 4,
                    Component.literal("Exactly two BetterModel 25ms frames per authoritative tick"));
            PlayerAnimations.stop(p);
            clock.destiny$advanceServerTick();
            h.assertTrue(clock.destiny$serverFrames() == initial + 4,
                    Component.literal("Closed tracker cannot advance or resurrect"));
            h.succeed();
        });
    }
}
