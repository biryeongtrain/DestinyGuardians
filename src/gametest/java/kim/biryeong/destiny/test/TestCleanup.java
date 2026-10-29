package kim.biryeong.destiny.test;

import kim.biryeong.destiny.test.mixin.GameTestHelperAccessor;
import net.minecraft.gametest.framework.GameTestAssertException;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.gametest.framework.GameTestInfo;
import net.minecraft.network.chat.Component;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Test-only teardown, owned by one GameTestInfo attempt rather than a timeout tick. */
public final class TestCleanup {
    private TestCleanup() {}

    public static void register(GameTestHelper helper, Runnable cleanup) {
        var info = ((GameTestHelperAccessor) helper).destiny$testInfo();
        ((Owner) info).destiny$cleanup().register(cleanup);
    }

    /** Implemented by the test-only GameTestInfo mixin; no global owner registry to leak. */
    public interface Owner {
        Scope destiny$cleanup();
    }

    /** Called before pass/fail listeners; terminal-tick callbacks finish before teardown. */
    public static void finish(GameTestInfo info, Scope scope) {
        var original = info.getError();
        var failures = scope.close(info);
        if (original != null) {
            for (var failure : failures) if (failure != original) original.addSuppressed(failure);
        } else if (!failures.isEmpty()) {
            var failure = new GameTestAssertException(Component.literal(
                    "Fixture cleanup failed (" + failures.size() + " error(s)); first: "
                            + failures.getFirst().getClass().getName()),
                    info.getTick());
            failures.forEach(failure::addSuppressed);
            info.fail(failure);
        }
    }

    public static final class Scope {
        private final ArrayDeque<Runnable> callbacks = new ArrayDeque<>();
        private boolean draining;
        private boolean closed;

        public void register(Runnable callback) {
            if (closed) throw new IllegalStateException("Cleanup registered after scope completion");
            callbacks.push(Objects.requireNonNull(callback, "cleanup"));
        }

        public boolean isDraining() {
            return draining;
        }

        /** Remove before invoking: repeat/reentrant completion never executes a callback twice. */
        public List<Throwable> close(GameTestInfo info) {
            var failures = new ArrayList<Throwable>();
            if (closed || draining) return failures;
            draining = true;
            try {
                while (!callbacks.isEmpty()) {
                    var original = info.getError();
                    try {
                        callbacks.pop().run();
                    } catch (Throwable failure) {
                        failures.add(failure);
                    } finally {
                        // Record each direct fail, even if another callback also calls fail.
                        // Restore the native error before the next cleanup sees the attempt.
                        var current = info.getError();
                        if (current != original) {
                            if (current != null) failures.add(current);
                            info.fail(original);
                        }
                    }
                }
            } finally {
                closed = true;
                draining = false;
                callbacks.clear();
            }
            return failures;
        }
    }
}
