package kim.biryeong.destiny.test;

import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.ServerAnimationClock;
import kim.biryeong.destiny.fx.ServerPoseSampling;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.animation.AnimationProgress;
import kr.toxicity.model.api.animation.AnimationStateHandler;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.tracker.Tracker;
import kr.toxicity.model.api.tracker.TrackerModifier;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.phys.Vec3;

import java.lang.reflect.InvocationTargetException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;

/** Counts real bone-state delay decrements, not the mixin's bookkeeping counter.
 * A long start blend keeps all observations inside one keyframe interval.
 */
public final class H20ClockGuardGameTests {
    private static final String ATTACK = "h15_super_void_attack";
    private static final String READY = "h15_super_void";
    private static final AnimationModifier BACKGROUND = AnimationModifier.builder()
            .start(20).end(0).priority(-100).type(AnimationIterator.Type.LOOP).build();

    private static AnimationModifier foreground(java.util.function.BooleanSupplier predicate) {
        // Builder.predicate() wraps this in BM's 50ms wall-clock cache. Prime would
        // cache true before reentry is armed, making the callback test vacuous when
        // both manual frames run immediately. The public record constructor keeps
        // the real pipeline predicate uncached, without sleeping or changing BM.
        return new AnimationModifier(predicate, 20, 0, 100,
                AnimationIterator.Type.LOOP, null, null, null);
    }

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static void whenLoaded(GameTestHelper h, Runnable action) {
        h.startSequence().thenWaitUntil(() -> check(h,
                BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(), "H20 limb loaded"))
                .thenExecute(() -> {
                    action.run();
                    check(h, !ServerPoseSampling.active(), "Sampling scope must not leak out of clock calls");
                    h.succeed();
                });
    }

    /** Hold the same monitor as the scheduler: unclaimed assertions need no sleeps/races.
     * Explicit start ensures animate()/stopAnimation() exercise BM's isScheduled branch
     * even when this fake player has no real viewing client.
     */
    private static void withTracker(GameTestHelper h, boolean owned, Consumer<EntityTracker> action) {
        var player = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), 0, 0);
        EntityTracker tracker = null;
        try {
            tracker = BetterModel.limb(HunterModelAssets.MODEL_NAME).orElseThrow().getOrCreate(
                    ModPlayer.of(player.connection), TrackerModifier.DEFAULT,
                    created -> {
                        if (owned) ((ServerAnimationClock) (Object) created).destiny$claimServerClock();
                    });
            synchronized (tracker) {
                try {
                    if (!tracker.isScheduled()) invoke(Tracker.class, tracker, "start");
                    check(h, tracker.isScheduled(), "Fixture must exercise scheduled implicit animation ticks");
                    action.accept(tracker);
                } finally {
                    tracker.close();
                }
            }
        } finally {
            if (tracker != null) tracker.close();
            TestPlayers.remove(player);
        }
    }

    private static Object handler(EntityTracker tracker) {
        var bone = tracker.bone(b -> b.name().rawName().equals("pri_right_item"));
        if (bone == null) throw new AssertionError("H20 right equipment bone missing");
        return field(bone, "globalState");
    }

    @SuppressWarnings("unchecked")
    private static AnimationStateHandler<AnimationProgress> state(EntityTracker tracker) {
        return (AnimationStateHandler<AnimationProgress>) field(handler(tracker), "state");
    }

    private static Object field(Object receiver, String name) {
        try {
            var field = receiver.getClass().getDeclaredField(name);
            field.setAccessible(true);
            return field.get(receiver);
        } catch (ReflectiveOperationException e) {
            throw new AssertionError("BetterModel 3.5.1 fixture field " + name, e);
        }
    }

    private static Object invoke(Class<?> owner, Object receiver, String name) {
        try {
            var method = owner.getDeclaredMethod(name);
            method.setAccessible(true);
            return method.invoke(receiver);
        } catch (InvocationTargetException e) {
            throw new AssertionError("BetterModel fixture call " + name, e.getCause());
        } catch (ReflectiveOperationException e) {
            throw new AssertionError("BetterModel 3.5.1 fixture method " + name, e);
        }
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void w198PublishesOneReachedPosePerTickWithoutSlowingTheAnimation(GameTestHelper h) {
        whenLoaded(h, () -> withTracker(h, true, tracker -> {
            var clock = (ServerAnimationClock) (Object) tracker;
            check(h, tracker.animate(ATTACK, foreground(() -> true)), "Moving foreground accepted");
            clock.destiny$primeAnimation();
            Object handler = handler(tracker);
            int[] transforms = {0};
            var probe = new kr.toxicity.model.api.nms.DisplayTransformer() {
                @Override public void transform(int duration, org.joml.Vector3f position,
                        org.joml.Vector3f scale, org.joml.Quaternionf rotation,
                        kr.toxicity.model.api.nms.AnimationBundler bundler) {
                    ++transforms[0];
                    check(h, duration == 1, "One-tick interpolation keeps the responsive blend");
                    check(h, ServerPoseSampling.publishing(), "Only the final reached pose is sent");
                    check(h, position.isFinite() && scale.isFinite() && rotation.isFinite(), "Finite actual transform");
                }
                @Override public void sendTransformation(kr.toxicity.model.api.nms.PacketBundler bundler) { }
            };
            try {
                var transformer = handler.getClass().getDeclaredField("transformer");
                transformer.setAccessible(true);
                Object previous = transformer.get(handler);
                transformer.set(handler, probe);
                try {
                    long frames = clock.destiny$serverFrames();
                    for (int tick = 1; tick <= 5; tick++) {
                        int before = transforms[0];
                        clock.destiny$advanceServerTick();
                        check(h, transforms[0] - before == 1,
                                "Exactly one transform publication per authoritative tick, got=" + (transforms[0]-before));
                        check(h, clock.destiny$serverFrames() == frames + 2L * tick,
                                "Both 25ms source evaluations still advance; duration is not stretched");
                    }
                } finally { transformer.set(handler, previous); }
            } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
        }));
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void queuedAnimationMutationsCannotAddHiddenPipelineTicks(GameTestHelper h) {
        whenLoaded(h, () -> withTracker(h, true, tracker -> {
            var clock = (ServerAnimationClock) (Object) tracker;
            check(h, tracker.animate(ATTACK, foreground(() -> true)), "Foreground clip accepted");
            clock.destiny$primeAnimation();
            var state = state(tracker);
            int before = state.getDelay();
            check(h, before > 8, "Long blend must keep the measured interval away from a keyframe boundary");
            var keyframe = state.afterKeyframe();
            int[] observed = {-1, -1, -1, 0};
            boolean[] accepted = new boolean[2];
            tracker.task(() -> {
                ++observed[3];
                observed[0] = state.getDelay();
                accepted[0] = tracker.animate(READY, BACKGROUND);
                observed[1] = state.getDelay();
                accepted[1] = tracker.stopAnimation(READY);
                observed[2] = state.getDelay();
            });
            clock.destiny$advanceServerTick();
            // Tracker.tick catches callback exceptions, so make assertions outside its body.
            check(h, observed[3] == 1 && accepted[0] && accepted[1], "Queued real animate/stop must execute once");
            check(h, observed[0] == observed[1] && observed[1] == observed[2],
                    "Queued animate/stop must not consume animation time");
            check(h, state.afterKeyframe() == keyframe && state.getDelay() == before - 2,
                    "Actual foreground pipeline must advance exactly two frames, not extra implicit frames");
            int reached = state.getDelay();
            invoke(Tracker.class, tracker, "animationTick");
            check(h, state.getDelay() == reached, "Scheduled permit must not leak after returning");
            clock.destiny$primeAnimation();
            check(h, state.getDelay() == reached - 1, "Explicit prime receives exactly one permit");
            invoke(Tracker.class, tracker, "animationTick");
            check(h, state.getDelay() == reached - 1, "Prime permit must also be consumed");
        }));
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void animationPredicateReentryCannotReuseTheScheduledPermit(GameTestHelper h) {
        whenLoaded(h, () -> withTracker(h, true, tracker -> {
            var clock = (ServerAnimationClock) (Object) tracker;
            var armed = new AtomicBoolean();
            int[] observed = {-1, -1, -1, 0};
            boolean[] accepted = new boolean[2];
            check(h, tracker.animate(ATTACK, foreground(() -> {
                if (armed.compareAndSet(true, false)) {
                    ++observed[3];
                    var current = state(tracker);
                    observed[0] = current.getDelay();
                    accepted[0] = tracker.animate(READY, BACKGROUND);
                    observed[1] = current.getDelay();
                    accepted[1] = tracker.stopAnimation(READY);
                    observed[2] = current.getDelay();
                }
                return true;
            })), "Foreground clip with real BM predicate accepted");
            clock.destiny$primeAnimation();
            var state = state(tracker);
            int before = state.getDelay();
            check(h, before > 8, "Long start blend initialized");
            var keyframe = state.afterKeyframe();
            armed.set(true);
            clock.destiny$advanceServerTick();
            check(h, observed[3] == 1 && accepted[0] && accepted[1], "Predicate must reenter the real animation API");
            check(h, observed[0] == observed[1] && observed[1] == observed[2],
                    "Nested animate/stop must not reuse the already-consumed permit");
            check(h, state.afterKeyframe() == keyframe && state.getDelay() == before - 2,
                    "Reentrant callbacks must leave exactly two actual pipeline steps");
        }));
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void unclaimedTrackerKeepsNativeImplicitTicksAndInterpolation(GameTestHelper h) {
        whenLoaded(h, () -> withTracker(h, false, tracker -> {
            check(h, tracker.animate(ATTACK, foreground(() -> true)), "Unclaimed foreground accepted");
            var state = state(tracker);
            int before = state.getDelay();
            check(h, before > 8, "Native immediate animate must initialize the long blend");
            var keyframe = state.afterKeyframe();
            check(h, tracker.animate(READY, BACKGROUND), "Unclaimed background accepted");
            check(h, state.getDelay() == before - 1 && state.afterKeyframe() == keyframe,
                    "Unclaimed animate retains its native immediate pipeline tick");
            check(h, tracker.stopAnimation(READY), "Unclaimed background removed");
            check(h, state.getDelay() == before - 2 && state.afterKeyframe() == keyframe,
                    "Unclaimed stop retains its native immediate pipeline tick");
            int duration = (Integer) invoke(handler(tracker).getClass(), handler(tracker), "interpolationDuration");
            check(h, duration > 1 && duration == Math.round(state.frame() / 2 + .00001f),
                    "Unclaimed interpolation must not become the owned one-tick sampler");
            var clock = (ServerAnimationClock) (Object) tracker;
            clock.destiny$primeAnimation();
            clock.destiny$advanceServerTick();
            check(h, state.getDelay() == before - 2 && clock.destiny$serverFrames() == 0,
                    "Owned-clock entry points cannot claim or step an unrelated tracker");
        }));
    }
}
