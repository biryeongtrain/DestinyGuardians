package kim.biryeong.destiny.compat.pack;

/**
 * Serializes startup pack decisions. Callers perform the returned action outside this policy.
 * A new instance represents a new startup; stopped and failed instances cannot be restarted.
 */
public final class StartupPackOrder {
    public enum Action { NONE, START, BLOCK }

    private enum State { STARTING, READY, FAILED, STOPPED }

    private State state = State.STARTING;
    private boolean pending;
    private boolean latestReloadSuccessful;

    /** Coalesces startup requests; every request after readiness may start a normal reinit. */
    public synchronized Action request() {
        return switch (state) {
            case STARTING -> {
                pending = true;
                yield Action.NONE;
            }
            case READY -> Action.START;
            case FAILED, STOPPED -> Action.BLOCK;
        };
    }

    /** Only the last reload result observed before startup finishes affects readiness. */
    public synchronized void observeReload(boolean successful) {
        if (state == State.STARTING) {
            latestReloadSuccessful = successful;
        }
    }

    /** Resolves startup once, treating an absent reload result as failure. */
    public synchronized Action finishStartup() {
        if (state != State.STARTING) {
            return Action.NONE;
        }
        state = latestReloadSuccessful ? State.READY : State.FAILED;
        boolean requested = pending;
        pending = false;
        return requested ? (state == State.READY ? Action.START : Action.BLOCK) : Action.NONE;
    }

    /** Permanently blocks this instance, including any pending startup request. */
    public synchronized void stop() {
        state = State.STOPPED;
        pending = false;
    }
}
