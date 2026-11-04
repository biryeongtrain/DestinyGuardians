package kim.biryeong.destiny.compat.pack;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import static kim.biryeong.destiny.compat.pack.StartupPackOrder.Action.*;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class StartupPackOrderW121Test {
    @Test
    void pendingRequestsCoalesceUntilSuccessfulFinish() {
        var order = new StartupPackOrder();
        for (int i = 0; i < 100; i++) assertEquals(NONE, order.request());
        order.observeReload(true);
        assertEquals(NONE, order.request());
        assertEquals(START, order.finishStartup());
        assertEquals(NONE, order.finishStartup());
        for (int i = 0; i < 100; i++) assertEquals(START, order.request());
    }

    @ParameterizedTest
    @ValueSource(booleans = {false, true})
    void finishWithoutPendingRequestReturnsNone(boolean successful) {
        var order = new StartupPackOrder();
        order.observeReload(successful);
        assertEquals(NONE, order.finishStartup());
        for (int i = 0; i < 3; i++) {
            assertEquals(successful ? START : BLOCK, order.request());
            assertEquals(NONE, order.finishStartup());
        }
    }

    @ParameterizedTest
    @ValueSource(booleans = {false, true})
    void absentReloadFailsWithOrWithoutPendingRequest(boolean pending) {
        var order = new StartupPackOrder();
        if (pending) assertEquals(NONE, order.request());
        assertEquals(pending ? BLOCK : NONE, order.finishStartup());
        order.observeReload(true);
        assertEquals(NONE, order.finishStartup());
        assertEquals(BLOCK, order.request());
    }

    @ParameterizedTest
    @CsvSource({"true,true", "true,false", "false,true", "false,false"})
    void latestReloadWinsBeforeFinish(boolean first, boolean last) {
        var order = new StartupPackOrder();
        order.observeReload(first);
        assertEquals(NONE, order.request());
        order.observeReload(last);
        assertEquals(NONE, order.request());
        assertEquals(last ? START : BLOCK, order.finishStartup());
        order.observeReload(!last);
        order.observeReload(!last);
        assertEquals(NONE, order.finishStartup());
        assertEquals(last ? START : BLOCK, order.request());
    }

    @ParameterizedTest
    @CsvSource({"false,false", "false,true", "true,false", "true,true"})
    void stopBeforeFinishIsTerminal(boolean pending, boolean successful) {
        var order = new StartupPackOrder();
        if (pending) assertEquals(NONE, order.request());
        order.observeReload(successful);
        order.stop();
        assertStopped(order);
    }

    @ParameterizedTest
    @ValueSource(booleans = {false, true})
    void stopAfterFinishIsTerminal(boolean successful) {
        var order = new StartupPackOrder();
        assertEquals(NONE, order.request());
        order.observeReload(successful);
        assertEquals(successful ? START : BLOCK, order.finishStartup());
        order.stop();
        assertStopped(order);
    }

    private static void assertStopped(StartupPackOrder order) {
        for (int i = 0; i < 4; i++) {
            order.observeReload(true);
            assertEquals(NONE, order.finishStartup());
            assertEquals(BLOCK, order.request());
            order.observeReload(false);
            order.stop();
        }
    }

    @Test
    void newInstancesHaveIndependentLifecycles() {
        for (int i = 0; i < 100; i++) {
            var order = new StartupPackOrder();
            assertEquals(NONE, order.request());
            order.observeReload(i % 2 == 0);
            assertEquals(i % 2 == 0 ? START : BLOCK, order.finishStartup());
            order.stop();
            assertStopped(order);
        }
    }

    @Test
    void allEventSequencesThroughLengthSixMatchLifecycleContract() {
        // Base-five enumeration includes every prefix and all reorderings, duplicates and stops.
        int sequences = 0;
        int combinations = 1;
        for (int length = 0; length <= 6; length++) {
            for (int encoded = 0; encoded < combinations; encoded++) {
                var order = new StartupPackOrder();
                var model = new Model();
                int events = encoded;
                for (int step = 0; step < length; step++) {
                    int event = events % 5;
                    events /= 5;
                    assertEquals(model.apply(event), apply(order, event),
                            "length=" + length + " sequence=" + encoded + " step=" + step);
                }
                // Probe final state, even when the enumerated sequence ended with a void method.
                assertEquals(model.apply(3), order.finishStartup());
                assertEquals(model.apply(0), order.request());
                sequences++;
            }
            combinations *= 5;
        }
        assertEquals(19_531, sequences);
    }

    private static StartupPackOrder.Action apply(StartupPackOrder order, int event) {
        return switch (event) {
            case 0 -> order.request();
            case 1, 2 -> {
                order.observeReload(event == 1);
                yield NONE;
            }
            case 3 -> order.finishStartup();
            case 4 -> {
                order.stop();
                yield NONE;
            }
            default -> throw new AssertionError(event);
        };
    }

    // Independent contract model uses history flags instead of the production state enum.
    private static final class Model {
        private boolean finished;
        private boolean stopped;
        private boolean requested;
        private Boolean lastResult;

        StartupPackOrder.Action apply(int event) {
            switch (event) {
                case 0:
                    if (stopped) return BLOCK;
                    if (finished) return Boolean.TRUE.equals(lastResult) ? START : BLOCK;
                    requested = true;
                    return NONE;
                case 1, 2:
                    if (!finished && !stopped) lastResult = event == 1;
                    return NONE;
                case 3:
                    if (finished || stopped) return NONE;
                    finished = true;
                    return requested ? (Boolean.TRUE.equals(lastResult) ? START : BLOCK) : NONE;
                case 4:
                    stopped = true;
                    return NONE;
                default:
                    throw new AssertionError(event);
            }
        }
    }

    @ParameterizedTest
    @CsvSource({"true,true", "true,false", "false,true", "false,false"})
    @Timeout(20)
    void concurrentCallersRespectBothForcedRequestFinishOrders(
            boolean requestFirst, boolean successful) throws Exception {
        var order = new StartupPackOrder();
        order.observeReload(successful);
        var ready = new CyclicBarrier(3);
        var firstDone = new CountDownLatch(1);
        var pool = Executors.newFixedThreadPool(2);
        try {
            Future<StartupPackOrder.Action> request = pool.submit(() -> {
                ready.await(5, TimeUnit.SECONDS);
                if (!requestFirst) assertTrue(firstDone.await(5, TimeUnit.SECONDS));
                var action = order.request();
                if (requestFirst) firstDone.countDown();
                return action;
            });
            Future<StartupPackOrder.Action> finish = pool.submit(() -> {
                ready.await(5, TimeUnit.SECONDS);
                if (requestFirst) assertTrue(firstDone.await(5, TimeUnit.SECONDS));
                var action = order.finishStartup();
                if (!requestFirst) firstDone.countDown();
                return action;
            });
            ready.await(5, TimeUnit.SECONDS);
            var terminal = successful ? START : BLOCK;
            assertEquals(requestFirst ? NONE : terminal, request.get(5, TimeUnit.SECONDS));
            assertEquals(requestFirst ? terminal : NONE, finish.get(5, TimeUnit.SECONDS));
            assertEquals(NONE, order.finishStartup());
            assertEquals(terminal, order.request());
        } finally {
            pool.shutdownNow();
        }
    }

    @ParameterizedTest
    @ValueSource(ints = {-1, 0, 1})
    @Timeout(20)
    void simultaneousRequestAndFinishProduceExactlyOneDecision(int observed) throws Exception {
        var pool = Executors.newFixedThreadPool(2);
        try {
            for (int iteration = 0; iteration < 100; iteration++) {
                var order = new StartupPackOrder();
                if (observed >= 0) order.observeReload(observed == 1);
                var ready = new CyclicBarrier(3);
                Future<StartupPackOrder.Action> request = pool.submit(() -> {
                    ready.await(5, TimeUnit.SECONDS);
                    return order.request();
                });
                Future<StartupPackOrder.Action> finish = pool.submit(() -> {
                    ready.await(5, TimeUnit.SECONDS);
                    return order.finishStartup();
                });
                ready.await(5, TimeUnit.SECONDS);
                var requested = request.get(5, TimeUnit.SECONDS);
                var finished = finish.get(5, TimeUnit.SECONDS);
                var terminal = observed == 1 ? START : BLOCK;
                assertTrue((requested == NONE && finished == terminal)
                        || (requested == terminal && finished == NONE));
                assertEquals(NONE, order.finishStartup());
                assertEquals(terminal, order.request());
            }
        } finally {
            pool.shutdownNow();
        }
    }

    @ParameterizedTest
    @ValueSource(booleans = {false, true})
    @Timeout(20)
    void concurrentRequestsCoalesceAndConcurrentFinishesResolveOnce(boolean successful) throws Exception {
        var order = new StartupPackOrder();
        order.observeReload(successful);
        var pool = Executors.newFixedThreadPool(8);
        try {
            var ready = new CyclicBarrier(9);
            List<Future<StartupPackOrder.Action>> requests = new ArrayList<>();
            for (int i = 0; i < 8; i++) requests.add(pool.submit(() -> {
                ready.await(5, TimeUnit.SECONDS);
                return order.request();
            }));
            ready.await(5, TimeUnit.SECONDS);
            for (var request : requests) assertEquals(NONE, request.get(5, TimeUnit.SECONDS));

            var finishReady = new CyclicBarrier(9);
            List<Future<StartupPackOrder.Action>> finishes = new ArrayList<>();
            for (int i = 0; i < 8; i++) finishes.add(pool.submit(() -> {
                finishReady.await(5, TimeUnit.SECONDS);
                return order.finishStartup();
            }));
            finishReady.await(5, TimeUnit.SECONDS);
            List<StartupPackOrder.Action> actions = new ArrayList<>();
            for (var finish : finishes) actions.add(finish.get(5, TimeUnit.SECONDS));
            assertEquals(1L, actions.stream().filter(a -> a == (successful ? START : BLOCK)).count());
            assertEquals(7L, actions.stream().filter(a -> a == NONE).count());
            assertEquals(successful ? START : BLOCK, order.request());
        } finally {
            pool.shutdownNow();
        }
    }
}
