package kim.biryeong.destiny.ability.jump;

/** Pure movement rules. Speeds/fuel are Minecraft tuning, not measured Destiny values. */
public final class JumpPhysics {
    private JumpPhysics() { }
    /** MC tuning: finite upward carry decay in blocks/tick per elapsed server tick. */
    public static final double GLIDE_ASCENT_DECAY = .006;
    public enum Kind { HUNTER, LIFT, GLIDE, BLINK }
    public enum Mode {
        HUNTER_HIGH(Kind.HUNTER, .62, .10, .38, 0, 0, 0),
        HUNTER_STRAFE(Kind.HUNTER, .46, .34, .64, 0, 0, 0),
        HUNTER_TRIPLE(Kind.HUNTER, .45, .17, .46, 0, 0, 0),
        HUNTER_BLINK(Kind.BLINK, 0, 0, 0, 0, 0, 0),
        TITAN_HIGH(Kind.LIFT, .16, .035, .40, .125, .64, 24),
        TITAN_STRAFE(Kind.LIFT, .10, .095, .58, .095, .50, 16),
        TITAN_CATAPULT(Kind.LIFT, .50, .065, .48, .105, .56, 18),
        WARLOCK_STRAFE(Kind.GLIDE, 0, .13, .52, 0, .12, 60),
        WARLOCK_BURST(Kind.GLIDE, 0, .035, .78, 0, .12, 60),
        WARLOCK_BALANCED(Kind.GLIDE, 0, .075, .63, 0, .12, 60),
        WARLOCK_BLINK(Kind.BLINK, 0, 0, 0, 0, 0, 0);
        public final Kind kind;
        public final double impulse, steering, horizontalSpeed, acceleration, verticalLimit;
        public final int duration;
        Mode(Kind kind, double impulse, double steering, double horizontalSpeed,
             double acceleration, double verticalLimit, int duration) {
            this.kind = kind; this.impulse = impulse; this.steering = steering;
            this.horizontalSpeed = horizontalSpeed; this.acceleration = acceleration;
            this.verticalLimit = verticalLimit; this.duration = duration;
        }
        public boolean continuous() { return kind == Kind.LIFT || kind == Kind.GLIDE; }
    }
    public record Velocity(double x, double y, double z) {
        public double horizontalSpeed() { return Math.hypot(x, z); }
    }
    /** Zero sampled Y is missing vertical evidence; ground/ceiling stops have explicit caller paths. */
    public static Velocity observedVelocity(Velocity sampled, boolean sampleValid, Velocity known, Velocity fallback) {
        boolean usableKnown = usable(known) && nonzero(known);
        if (sampleValid) {
            // Position is an average across a packet gap; known movement is the last packet's delta.
            // A measured fall can never be replaced with a stale positive known Y.
            if (sampled.y < -1e-6 && (!usableKnown || known.y > 0)) return sampled;
            double y;
            if (Math.abs(sampled.y) <= 1e-6) y = usableKnown && Math.abs(known.y) > 1e-6 ? known.y : fallback.y;
            else y = !usableKnown || known.y == 0 && sampled.y > 0 ? sampled.y : Math.min(sampled.y, known.y);
            return new Velocity(usableKnown ? known.x : sampled.x, y, usableKnown ? known.z : sampled.z);
        }
        if (usableKnown) return known;
        return fallback;
    }
    private static boolean usable(Velocity velocity) {
        return Double.isFinite(velocity.x) && Double.isFinite(velocity.y) && Double.isFinite(velocity.z)
                && Math.abs(velocity.y) <= 1.5 && velocity.horizontalSpeed() <= 3;
    }
    private static boolean nonzero(Velocity velocity) {
        return velocity.x * velocity.x + velocity.y * velocity.y + velocity.z * velocity.z > 1e-10;
    }
    public static Velocity capHorizontal(Velocity velocity, double cap) {
        double speed = velocity.horizontalSpeed();
        return speed > cap ? new Velocity(velocity.x * cap / speed, velocity.y, velocity.z * cap / speed) : velocity;
    }
    public record MotionEstimate(Velocity velocity, boolean freshVertical) { }

    /** Packet-aware position history. All inputs are observations, never our last velocity command. */
    public static final class MotionTracker {
        private Displacement position, anchor;
        private long frameTick, anchorTick, changedTick, observedTick = Long.MIN_VALUE;
        private long anchorYTick, changedYTick, verticalObservedTick = Long.MIN_VALUE;
        private Velocity velocity = new Velocity(0, 0, 0), previousKnown = velocity;

        public MotionTracker(Displacement position, long tick) {
            this.position = this.anchor = position;
            frameTick = anchorTick = changedTick = tick;
            anchorYTick = changedYTick = tick;
        }

        public MotionEstimate observe(long tick, Displacement next, Velocity known, boolean grounded) {
            if (tick != frameTick) {
                anchor = position; anchorTick = changedTick; anchorYTick = changedYTick; frameTick = tick;
            }
            Velocity delta = new Velocity(next.x - anchor.x, next.y - anchor.y, next.z - anchor.z);
            boolean moved = nonzero(delta);
            long interval = Math.max(1, tick - anchorTick);
            long verticalInterval = Math.max(1, tick - anchorYTick);
            Velocity sampled = new Velocity(delta.x / interval, delta.y / verticalInterval, delta.z / interval);
            boolean sampleValid = moved && interval <= 4 && usable(sampled);
            // A horizontal-only packet delta says nothing about missing vertical motion.
            boolean newKnown = usable(known) && Math.abs(known.y) > 1e-6 && known.y != previousKnown.y;
            boolean verticalSample = sampleValid && verticalInterval <= 4 && Math.abs(delta.y) > 1e-6;
            previousKnown = known;
            position = next;
            if (moved) changedTick = tick;
            if (Math.abs(delta.y) > 1e-6) changedYTick = tick;
            if (grounded) {
                velocity = new Velocity(0, 0, 0); observedTick = verticalObservedTick = tick;
                changedTick = changedYTick = tick; // Standing on ground is an explicit current origin.
                return new MotionEstimate(velocity, true);
            }
            if (sampleValid || newKnown) {
                Velocity combined = observedVelocity(sampled, sampleValid, known, velocity);
                double y = verticalSample || newKnown ? combined.y : velocity.y;
                velocity = new Velocity(combined.x, y, combined.z);
                observedTick = tick;
                if (verticalSample || newKnown) verticalObservedTick = tick;
            } else if (moved) {
                // A teleport/discontinuity is a new origin, never an enormous jump impulse.
                velocity = new Velocity(0, 0, 0); observedTick = verticalObservedTick = tick;
                return new MotionEstimate(velocity, false);
            }
            long age = observedTick == Long.MIN_VALUE ? Long.MAX_VALUE : tick - observedTick;
            long verticalAge = verticalObservedTick == Long.MIN_VALUE ? Long.MAX_VALUE : tick - verticalObservedTick;
            // A bounded two-tick gap retains measured ascent. Longer silence cannot refresh it.
            double horizontalDrag = age <= 2 ? 1 : Math.pow(.91, Math.min(age, 20));
            double y = velocity.y;
            if (verticalAge > 2) {
                for (long i = 0; i < Math.min(verticalAge, 20); i++) y = (y - .08) * .98;
                y = Math.min(0, y);
            }
            return new MotionEstimate(new Velocity(velocity.x * horizontalDrag, y, velocity.z * horizontalDrag), verticalAge == 0);
        }
    }

    /** Active glide owns a finite ascent carry; packet gaps and repeated positive samples cannot refill it. */
    public static final class GlideCarry {
        private double vertical;
        private long lastTick = Long.MIN_VALUE;
        private double lastCommand;
        private boolean falling;

        public double apply(long tick, MotionEstimate observed, double descent, boolean ceilingBlocked) {
            if (tick == lastTick) return lastCommand;
            double measured = observed.velocity.y;
            if (lastTick == Long.MIN_VALUE) {
                vertical = measured;
                falling = measured <= 0;
            } else {
                long skipped = Math.max(0, tick - lastTick - 1);
                if (!falling) vertical = Math.max(0, vertical - GLIDE_ASCENT_DECAY * skipped);
                // After activation, positive packet samples neither refill nor ratchet down carry.
                // Their age/coalescing can differ from the server command's physics phase.
                if (observed.freshVertical && measured <= 0) { vertical = measured; falling = true; }
            }
            if (ceilingBlocked) { vertical = Math.min(0, vertical); falling = true; }
            if (falling) vertical = Math.min(0, vertical);
            lastCommand = glideTick(vertical, descent);
            vertical = (lastCommand - .08) * .98;
            if (vertical <= 0) falling = true;
            lastTick = tick;
            return lastCommand;
        }
    }
    /** Zero direction means no WASD intent, not camera-forward. */
    public static Velocity steer(Velocity velocity, double dx, double dz, double acceleration, double cap) {
        double length = Math.hypot(dx, dz);
        if (length < 1e-7) return velocity;
        double x = velocity.x + dx / length * acceleration;
        double z = velocity.z + dz / length * acceleration;
        double speed = Math.hypot(x, z), limit = Math.max(cap, velocity.horizontalSpeed());
        // Preserve existing external/super speed, but do not accelerate it past that speed.
        if (speed > limit) { x *= limit / speed; z *= limit / speed; }
        return new Velocity(x, velocity.y, z);
    }
    public static Velocity hunter(Mode mode, Velocity velocity, double dx, double dz, double strength) {
        Velocity steered = steer(velocity, dx, dz, mode.steering, mode.horizontalSpeed);
        return new Velocity(steered.x, Math.max(velocity.y, strength), steered.z);
    }
    public static double liftStart(Mode mode, double vy) {
        // Catapult arrests a fall immediately; the other lifts must overcome it over time.
        return mode == Mode.TITAN_CATAPULT ? Math.max(vy, mode.impulse)
                : vy > mode.verticalLimit ? vy : Math.min(mode.verticalLimit, vy + mode.impulse);
    }
    public static double liftTick(double vy, double acceleration, double ceiling) {
        return vy > ceiling ? vy : Math.min(ceiling, vy + acceleration);
    }
    public static double glideTick(double vy, double descent) {
        // Pre-compensate the next vanilla gravity/drag step only during an existing ascent.
        // (result - .08) * .98 = max(0, vy - GLIDE_ASCENT_DECAY): carry, then exhaust ascent.
        if (vy > 0) return Math.max(0, vy - GLIDE_ASCENT_DECAY) / .98 + .08;
        return Math.max(vy, -descent); // Falling can never become a fresh ascent.
    }
    public static Velocity burstGlide(Velocity velocity, double dx, double dz, double speed) {
        return steer(velocity, dx, dz, .32, speed);
    }
    public static double finite(double value, double fallback, double min, double max) {
        return Double.isFinite(value) ? Math.max(min, Math.min(max, value)) : fallback;
    }
    public record Displacement(double x, double y, double z) {
        public double length() { return Math.sqrt(x * x + y * y + z * z); }
        public Displacement scale(double factor) { return new Displacement(x * factor, y * factor, z * factor); }
    }
    public static Displacement blinkVector(double x, double y, double z, double range, double verticalLimit) {
        double length = Math.sqrt(x * x + y * y + z * z);
        if (!Double.isFinite(length) || length < 1e-7) return new Displacement(0, 0, 0);
        return new Displacement(x / length * range,
                Math.max(-verticalLimit, Math.min(verticalLimit, y / length * range)), z / length * range);
    }
    /** The predicate checks the swept player volume from previous to next, not just endpoints. */
    public static Displacement sweepBlink(Displacement displacement,
            java.util.function.BiPredicate<Displacement, Displacement> clear) {
        Displacement safe = new Displacement(0, 0, 0);
        int steps = (int) Math.ceil(displacement.length() / .125);
        for (int step = 1; step <= steps; step++) {
            Displacement next = displacement.scale((double) step / steps);
            if (!clear.test(safe, next)) break;
            safe = next;
        }
        return safe;
    }
    public enum Press { STARTED, STOPPED, REJECTED }
    /** Hunter/Lift/Glide share airborne fuel; Blink has independent timed charges across classes. */
    public static final class Budget {
        private double spent;
        private int starts;
        private Mode active;
        private int duration;
        private long lastTick = Long.MIN_VALUE, lastMotion = Long.MIN_VALUE, lastPress = Long.MIN_VALUE;
        private long lastBlink = Long.MIN_VALUE;
        private int blinkCharges = 2;
        public double remaining() { return Math.max(0, 1 - spent); }
        public int starts() { return starts; }
        public Mode active() { return active; }
        public void cancel() { active = null; }
        /** False for duplicate calls from legacy/common hooks in either order. */
        public boolean observe(long tick, boolean grounded) {
            if (tick == lastTick) return false;
            lastTick = tick;
            rechargeBlink(tick);
            if (grounded) { spent = 0; starts = 0; active = null; }
            return true;
        }
        public Press press(Mode mode, long tick, int durationTicks) {
            if (tick == lastPress) return Press.REJECTED;
            lastPress = tick;
            if (active != null) { cancel(); return Press.STOPPED; }
            if (mode.kind == Kind.BLINK) {
                rechargeBlink(tick);
                if (blinkCharges == 0 || lastBlink != Long.MIN_VALUE && tick - lastBlink < 6) return Press.REJECTED;
                // Recharge works in midair and never reads or changes normal jump fuel/starts.
                blinkCharges--; lastBlink = tick;
                return Press.STARTED;
            }
            if (mode.continuous() && starts >= 3) return Press.REJECTED;
            int boundedDuration = Math.max(1, Math.min(100, durationTicks));
            double cost = mode.continuous() ? 1.0 / boundedDuration
                    : mode == Mode.HUNTER_TRIPLE ? .5 : 1;
            if (!spend(cost)) return Press.REJECTED;
            if (mode.continuous()) {
                starts++; active = mode; duration = boundedDuration;
                lastMotion = tick; // Initial impulse already owns this tick's movement.
            }
            return Press.STARTED;
        }
        private void rechargeBlink(long tick) {
            if (lastBlink != Long.MIN_VALUE && tick - lastBlink >= 44) blinkCharges = 2;
        }
        public boolean propel(long tick) {
            if (active == null || tick == lastMotion) return false;
            lastMotion = tick;
            if (!spend(1.0 / duration)) { cancel(); return false; }
            return true;
        }
        private boolean spend(double amount) {
            if (spent + amount > 1 + 1e-9) return false;
            spent = Math.min(1, spent + amount);
            return true;
        }
    }
}
