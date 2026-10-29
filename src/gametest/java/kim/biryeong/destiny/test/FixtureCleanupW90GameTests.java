package kim.biryeong.destiny.test;

import io.netty.buffer.Unpooled;
import io.netty.channel.embedded.EmbeddedChannel;
import kim.biryeong.destiny.test.mixin.GameTestHelperAccessor;
import kim.biryeong.destiny.test.mixin.GameTestInfoAccessor;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.gametest.framework.GameTestInfo;
import net.minecraft.gametest.framework.GameTestListener;
import net.minecraft.gametest.framework.GameTestRunner;
import net.minecraft.gametest.framework.GameTestTimeoutException;
import net.minecraft.gametest.framework.RetryOptions;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.block.Rotation;

import java.util.ArrayList;
import java.util.List;

/** W90 lifecycle regressions use detached attempts, never a nested runner or structure. */
public final class FixtureCleanupW90GameTests {
    private static final String FLOOR = "destiny-test:floor";

    private record Attempt(GameTestInfo info, GameTestHelper helper) {}

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static Attempt detached(GameTestHelper h) {
        var source = ((GameTestHelperAccessor) h).destiny$testInfo();
        var info = new GameTestInfo(source.getTestHolder(), Rotation.NONE, h.getLevel(),
                RetryOptions.noRetries());
        // Native succeed queries the host's existing bounds and clears nonplayer entities.
        // These tests create no gameplay entities and never prepare or place another structure.
        info.setTestBlockPos(source.getTestBlockPos());
        return new Attempt(info, new GameTestHelper(info));
    }

    private static void finish(GameTestInfo info) {
        ((GameTestInfoAccessor) info).destiny$finish();
    }

    private static TestCleanup.Scope scope(GameTestInfo info) {
        return ((TestCleanup.Owner) info).destiny$cleanup();
    }

    private static void failed(GameTestHelper h, GameTestInfo info) {
        check(h, info.isDone() && info.hasFailed() && !info.hasSucceeded()
                        && info.getError() != null,
                "Detached attempt finishes as an actual native failure");
    }

    private static void suppressedExactly(GameTestHelper h, Throwable owner, Throwable... expected) {
        var actual = owner.getSuppressed();
        check(h, actual.length == expected.length, "Every cleanup failure is suppressed exactly once");
        for (int i = 0; i < expected.length; i++) {
            check(h, actual[i] == expected[i], "Suppressed cleanup failures retain identity and LIFO order");
        }
    }

    private static void record(GameTestInfo info, List<String> order, List<Boolean> done,
                               String label) {
        order.add(label);
        done.add(info.isDone());
    }

    private static void readyForNativeTick(GameTestInfo info) {
        // Reuse only the existing native block entity; do not place, prepare, or start the host test.
        info.getTestInstanceBlockEntity();
        var access = (GameTestInfoAccessor) info;
        access.destiny$placedStructure(true);
        access.destiny$chunksLoaded(true);
        access.destiny$started(true);
        access.destiny$tick(0);
    }

    private static final class OutcomeListener implements GameTestListener {
        private final List<String> trace;
        private int calls;
        private GameTestInfo observed;
        private Throwable error;
        private boolean done;
        private boolean registrationRejected;

        private OutcomeListener(List<String> trace) {
            this.trace = trace;
        }

        private void observe(GameTestInfo info, String branch) {
            calls++;
            observed = info;
            error = info.getError();
            done = info.isDone();
            trace.add(branch);
            try {
                TestCleanup.register(new GameTestHelper(info), () -> trace.add("unexpected listener cleanup"));
            } catch (IllegalStateException expected) {
                registrationRejected = true;
            }
        }

        @Override
        public void testStructureLoaded(GameTestInfo info) {
            throw new AssertionError("Detached attempt must not load another structure");
        }

        @Override
        public void testPassed(GameTestInfo info, GameTestRunner runner) {
            observe(info, "passed");
        }

        @Override
        public void testFailed(GameTestInfo info, GameTestRunner runner) {
            observe(info, "failed");
        }

        @Override
        public void testAddedForRerun(GameTestInfo previous, GameTestInfo next, GameTestRunner runner) {
            throw new AssertionError("Detached attempt must not enlist a rerun");
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void nativeEarlySuccessDrainsLifoAndReleasesOutboundBufferOnce(GameTestHelper h) {
        var attempt = detached(h);
        var info = attempt.info();
        var order = new ArrayList<String>();
        var done = new ArrayList<Boolean>();
        var channel = new EmbeddedChannel();
        var buffer = Unpooled.buffer().writeInt(90);
        try {
            check(h, channel.writeOutbound(buffer) && channel.isOpen()
                            && channel.outboundMessages().peek() == buffer && buffer.refCnt() == 1,
                    "Real EmbeddedChannel owns the live outbound reference-counted buffer");
            TestCleanup.register(attempt.helper(), () -> record(info, order, done, "oldest"));
            TestCleanup.register(attempt.helper(), () -> {
                record(info, order, done, "release");
                channel.finishAndReleaseAll();
            });
            TestCleanup.register(attempt.helper(), () -> record(info, order, done, "newest"));
            info.succeed();
            check(h, info.isDone() && info.hasSucceeded() && !info.hasFailed() && info.getError() == null,
                    "Native early succeed completes successfully after cleanup");
            check(h, order.equals(List.of("newest", "release", "oldest"))
                            && done.equals(List.of(false, false, false)),
                    "Direct native finish drains LIFO before publishing done");
            check(h, !channel.isOpen() && channel.outboundMessages().isEmpty() && buffer.refCnt() == 0,
                    "Native success closes the real channel and releases its queued buffer");
            finish(info);
            finish(info);
            check(h, order.size() == 3 && info.hasSucceeded() && buffer.refCnt() == 0,
                    "Repeated native finish neither reruns callbacks nor releases twice");
        } finally {
            channel.finishAndReleaseAll();
            if (buffer.refCnt() > 0) buffer.release();
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void cleanupAssertionAndRuntimeErrorsTurnNativeSuccessIntoFailure(GameTestHelper h) {
        var attempt = detached(h);
        var order = new ArrayList<String>();
        var assertion = new AssertionError("W90 cleanup assertion");
        var runtime = new RuntimeException("W90 cleanup runtime");
        TestCleanup.register(attempt.helper(), () -> order.add("oldest"));
        TestCleanup.register(attempt.helper(), () -> {
            order.add("runtime");
            throw runtime;
        });
        TestCleanup.register(attempt.helper(), () -> {
            order.add("assertion");
            throw assertion;
        });
        attempt.info().succeed();
        failed(h, attempt.info());
        check(h, order.equals(List.of("assertion", "runtime", "oldest")),
                "AssertionError and RuntimeException both allow older callbacks to run");
        check(h, attempt.info().getError() instanceof GameTestAssertException
                        && attempt.info().getError().getDescription().getString().contains("(2 error(s))"),
                "Both thrown cleanup failures are counted in the actual native failure");
        suppressedExactly(h, attempt.info().getError(), assertion, runtime);
        var failure = attempt.info().getError();
        finish(attempt.info());
        check(h, attempt.info().getError() == failure && order.size() == 3,
                "Repeated native finish preserves the aggregate failure without rerunning cleanup");
        suppressedExactly(h, failure, assertion, runtime);
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void originalAssertionIdentitySurvivesThrownCleanupErrors(GameTestHelper h) {
        var attempt = detached(h);
        var original = new GameTestAssertException(Component.literal("W90 original assertion"), 0);
        var assertion = new AssertionError("W90 secondary assertion");
        var runtime = new RuntimeException("W90 secondary runtime");
        var order = new ArrayList<String>();
        TestCleanup.register(attempt.helper(), () -> order.add("oldest"));
        TestCleanup.register(attempt.helper(), () -> {
            order.add("runtime");
            throw runtime;
        });
        TestCleanup.register(attempt.helper(), () -> {
            order.add("assertion");
            throw assertion;
        });
        attempt.info().fail(original);
        check(h, !attempt.info().isDone() && attempt.info().getError() == original && order.isEmpty(),
                "Native fail records the original assertion before native finish drains anything");
        finish(attempt.info());
        failed(h, attempt.info());
        check(h, attempt.info().getError() == original
                        && order.equals(List.of("assertion", "runtime", "oldest")),
                "Cleanup preserves the original assertion identity and drains every callback");
        suppressedExactly(h, original, assertion, runtime);
        finish(attempt.info());
        check(h, attempt.info().getError() == original && order.size() == 3,
                "Repeat finish preserves the original failure and callback count");
        suppressedExactly(h, original, assertion, runtime);
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void directFailDuringCleanupIsCountedAgainstNativeSuccess(GameTestHelper h) {
        var attempt = detached(h);
        var direct = new GameTestAssertException(Component.literal("W90 direct cleanup fail"), 0);
        var runtime = new RuntimeException("W90 thrown alongside direct fail");
        var order = new ArrayList<String>();
        TestCleanup.register(attempt.helper(), () -> order.add("oldest"));
        TestCleanup.register(attempt.helper(), () -> {
            order.add("throw");
            throw runtime;
        });
        TestCleanup.register(attempt.helper(), () -> {
            order.add("fail");
            attempt.info().fail(direct);
        });
        attempt.info().succeed();
        failed(h, attempt.info());
        check(h, order.equals(List.of("fail", "throw", "oldest"))
                        && attempt.info().getError() != direct
                        && attempt.info().getError() instanceof GameTestAssertException
                        && attempt.info().getError().getDescription().getString().contains("(2 error(s))"),
                "A nonthrowing native fail callback is counted alongside a thrown cleanup error");
        suppressedExactly(h, attempt.info().getError(), direct, runtime);
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void directFailDuringCleanupCannotReplaceOriginalAssertion(GameTestHelper h) {
        var attempt = detached(h);
        var original = new GameTestAssertException(Component.literal("W90 original before direct fail"), 0);
        var direct = new GameTestAssertException(Component.literal("W90 attempted replacement"), 0);
        var runtime = new RuntimeException("W90 thrown after direct fail");
        var order = new ArrayList<String>();
        TestCleanup.register(attempt.helper(), () -> order.add("oldest"));
        TestCleanup.register(attempt.helper(), () -> {
            order.add("throw");
            throw runtime;
        });
        TestCleanup.register(attempt.helper(), () -> {
            order.add("fail");
            attempt.info().fail(direct);
        });
        attempt.info().fail(original);
        finish(attempt.info());
        failed(h, attempt.info());
        check(h, attempt.info().getError() == original
                        && order.equals(List.of("fail", "throw", "oldest")),
                "Direct cleanup fail cannot overwrite the original native assertion");
        suppressedExactly(h, original, direct, runtime);
        finish(attempt.info());
        suppressedExactly(h, original, direct, runtime);
        check(h, order.size() == 3, "Direct-fail callbacks are not repeated on second finish");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void nativeTimeoutIdentitySurvivesCleanupFailure(GameTestHelper h) {
        var attempt = detached(h);
        var cleanupFailure = new AssertionError("W90 timeout cleanup");
        var order = new ArrayList<String>();
        TestCleanup.register(attempt.helper(), () -> order.add("oldest"));
        TestCleanup.register(attempt.helper(), () -> {
            order.add("throw");
            throw cleanupFailure;
        });
        var access = (GameTestInfoAccessor) attempt.info();
        access.destiny$started(true);
        access.destiny$tick(attempt.info().getTimeoutTicks());
        access.destiny$tickInternal();
        var timeout = attempt.info().getError();
        check(h, timeout instanceof GameTestTimeoutException
                        && attempt.info().getTick() == attempt.info().getTimeoutTicks() + 1
                        && attempt.info().hasStarted() && !attempt.info().isDone() && order.isEmpty(),
                "Native tickInternal detects a real timeout before native finish drains cleanup");
        suppressedExactly(h, timeout);
        finish(attempt.info());
        failed(h, attempt.info());
        check(h, attempt.info().getError() == timeout && order.equals(List.of("throw", "oldest")),
                "Native finish keeps the exact timeout while draining every cleanup callback");
        suppressedExactly(h, timeout, cleanupFailure);
        finish(attempt.info());
        suppressedExactly(h, timeout, cleanupFailure);
        check(h, order.size() == 2, "Repeated timeout finish does not rerun cleanup");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void nativeCopyResetOwnsFreshIndependentAttemptScopes(GameTestHelper h) {
        var original = detached(h);
        var calls = new int[2];
        TestCleanup.register(original.helper(), () -> calls[0]++);
        var copy = original.info().copyReset();
        check(h, copy != original.info() && scope(copy) != scope(original.info())
                        && !copy.isDone() && copy.getError() == null
                        && copy.getTestHolder() == original.info().getTestHolder()
                        && copy.getTestBlockPos().equals(original.info().getTestBlockPos()),
                "Native copyReset retains only shared test metadata with a fresh attempt scope");
        TestCleanup.register(new GameTestHelper(copy), () -> calls[1]++);
        finish(copy);
        check(h, copy.hasSucceeded() && calls[0] == 0 && calls[1] == 1 && !original.info().isDone(),
                "Finishing the copy runs its callback without copying or consuming original cleanup");
        var originalFailure = new GameTestAssertException(Component.literal("W90 attempt being retried"), 0);
        original.info().fail(originalFailure);
        finish(original.info());
        failed(h, original.info());
        check(h, original.info().getError() == originalFailure && calls[0] == 1 && calls[1] == 1,
                "Original attempt still drains its own callback exactly once");
        var retry = original.info().copyReset();
        check(h, scope(retry) != scope(original.info()) && scope(retry) != scope(copy)
                        && !retry.isDone() && retry.getError() == null,
                "Resetting a finished failed attempt creates another empty independent scope");
        finish(retry);
        finish(retry);
        finish(copy);
        finish(original.info());
        check(h, retry.hasSucceeded() && calls[0] == 1 && calls[1] == 1
                        && original.info().getError() == originalFailure,
                "Empty retry and repeated native finishes never rerun callbacks from prior attempts");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void recursiveNativeFinishDefersDoneAndDrainsDynamicRegistrationsLifo(GameTestHelper h) {
        var attempt = detached(h);
        var info = attempt.info();
        var order = new ArrayList<String>();
        var done = new ArrayList<Boolean>();
        TestCleanup.register(attempt.helper(), () -> record(info, order, done, "oldest"));
        TestCleanup.register(attempt.helper(), () -> record(info, order, done, "older"));
        TestCleanup.register(attempt.helper(), () -> {
            record(info, order, done, "enter");
            finish(info);
            record(info, order, done, "after recursive finish");
            TestCleanup.register(attempt.helper(), () -> record(info, order, done, "dynamic first"));
            TestCleanup.register(attempt.helper(), () -> {
                record(info, order, done, "dynamic second");
                finish(info);
                TestCleanup.register(attempt.helper(), () -> record(info, order, done, "dynamic third"));
            });
        });
        info.succeed();
        var expected = List.of("enter", "after recursive finish", "dynamic second", "dynamic third",
                "dynamic first", "older", "oldest");
        check(h, info.isDone() && info.hasSucceeded() && info.getError() == null && order.equals(expected),
                "Recursive native finish drains new registrations before older callbacks in LIFO order");
        check(h, done.size() == expected.size() && done.stream().noneMatch(Boolean::booleanValue),
                "Neither recursive native finish publishes done before direct teardown completes");
        finish(info);
        check(h, order.equals(expected), "Dynamic and original callbacks all execute only once");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void terminalTickDrainsAfterTrailingWorkBeforeNativePassListener(GameTestHelper h) {
        var attempt = detached(h);
        readyForNativeTick(attempt.info());
        var trace = new ArrayList<String>();
        var fixtureActive = new boolean[]{true};
        var listener = new OutcomeListener(trace);
        attempt.info().addListener(listener);
        TestCleanup.register(attempt.helper(), () -> {
            trace.add("older cleanup");
            fixtureActive[0] = false;
        });
        attempt.info().setRunAtTickTime(1, () -> {
            attempt.info().succeed();
            trace.add("after succeed");
            fixtureActive[0] = true;
            TestCleanup.register(attempt.helper(), () -> trace.add("late cleanup"));
        });
        attempt.info().tick(null);
        var expected = List.of("after succeed", "late cleanup", "older cleanup", "passed");
        check(h, trace.equals(expected) && !fixtureActive[0] && attempt.info().hasSucceeded(),
                "Native terminal tick retains trailing work, then drains LIFO before choosing pass");
        check(h, listener.calls == 1 && listener.observed == attempt.info() && listener.error == null
                        && listener.done && listener.registrationRejected,
                "Native pass listener observes the completed attempt with cleanup registration closed");
        attempt.info().tick(null);
        finish(attempt.info());
        check(h, trace.equals(expected) && listener.calls == 1,
                "Subsequent native ticks and finish do not rerun cleanup or report a second result");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void terminalTickCleanupFailureChoosesNativeFailListener(GameTestHelper h) {
        var attempt = detached(h);
        readyForNativeTick(attempt.info());
        var trace = new ArrayList<String>();
        var fixtureActive = new boolean[]{true};
        var cleanupFailure = new AssertionError("W90 terminal tick cleanup");
        var listener = new OutcomeListener(trace);
        attempt.info().addListener(listener);
        TestCleanup.register(attempt.helper(), () -> {
            trace.add("older cleanup");
            fixtureActive[0] = false;
        });
        attempt.info().setRunAtTickTime(1, () -> {
            attempt.info().succeed();
            trace.add("after succeed");
            fixtureActive[0] = true;
            TestCleanup.register(attempt.helper(), () -> {
                trace.add("late cleanup");
                throw cleanupFailure;
            });
        });
        attempt.info().tick(null);
        failed(h, attempt.info());
        var expected = List.of("after succeed", "late cleanup", "older cleanup", "failed");
        check(h, trace.equals(expected) && !fixtureActive[0]
                        && attempt.info().getError() instanceof GameTestAssertException,
                "Cleanup error after trailing terminal work still drains older cleanup and selects native fail");
        suppressedExactly(h, attempt.info().getError(), cleanupFailure);
        check(h, listener.calls == 1 && listener.observed == attempt.info()
                        && listener.error == attempt.info().getError() && listener.done
                        && listener.registrationRejected,
                "Native failure listener sees the cleanup failure and closed scope before reporting");
        attempt.info().tick(null);
        finish(attempt.info());
        check(h, trace.equals(expected) && listener.calls == 1,
                "Failed terminal attempt never reruns cleanup or emits a later pass");
        suppressedExactly(h, attempt.info().getError(), cleanupFailure);
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void registrationAfterNativeFinishIsRejected(GameTestHelper h) {
        var attempt = detached(h);
        var calls = new int[1];
        TestCleanup.register(attempt.helper(), () -> calls[0]++);
        attempt.info().succeed();
        check(h, attempt.info().hasSucceeded() && calls[0] == 1,
                "Native success has completed the original cleanup before late registration");
        boolean helperRejected = false;
        try {
            TestCleanup.register(attempt.helper(), () -> calls[0]++);
        } catch (IllegalStateException expected) {
            helperRejected = true;
        }
        boolean scopeRejected = false;
        try {
            scope(attempt.info()).register(() -> calls[0]++);
        } catch (IllegalStateException expected) {
            scopeRejected = true;
        }
        finish(attempt.info());
        check(h, helperRejected && scopeRejected && calls[0] == 1 && attempt.info().hasSucceeded(),
                "Helper API and completed per-attempt scope both reject late callbacks without rerunning any");
        h.succeed();
    }
}
