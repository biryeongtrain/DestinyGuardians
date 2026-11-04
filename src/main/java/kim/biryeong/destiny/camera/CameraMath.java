package kim.biryeong.destiny.camera;

/** Pure eye-relative camera and vanilla movement-input math; no entity or world access. */
public final class CameraMath {
    private static final double REAR_DISTANCE = 3.0;
    private static final double SHOULDER_RIGHT = 0.45;
    private static final double UP = 0.25;

    private CameraMath() { }

    public record Point(double x, double y, double z) { }

    /** Vanilla signs: positive strafe is left; positive forward is forward. */
    public record InputVector(float strafe, float forward) { }

    /**
     * Unobstructed target from the eye, not a player/body teleport destination.
     * Yaw zero looks +Z, positive pitch looks down. Up is world +Y.
     * The caller owns collision resolution and any camera transport.
     *
     * @throws IllegalArgumentException if any coordinate or angle is nonfinite
     */
    public static Point desired(double eyeX, double eyeY, double eyeZ, float yaw, float pitch) {
        return desired(eyeX, eyeY, eyeZ, yaw, pitch, SHOULDER_RIGHT);
    }

    /** Keep the bow nearer the owner's centre aim while retaining clearance around the draw hand. */
    public static Point desiredBow(double eyeX, double eyeY, double eyeZ, float yaw, float pitch) {
        return desired(eyeX, eyeY, eyeZ, yaw, pitch, 0.75);
    }

    private static Point desired(double eyeX, double eyeY, double eyeZ, float yaw, float pitch, double shoulderRight) {
        if (!Double.isFinite(eyeX) || !Double.isFinite(eyeY) || !Double.isFinite(eyeZ)
                || !Float.isFinite(yaw) || !Float.isFinite(pitch)) {
            throw new IllegalArgumentException("Eye coordinates and camera angles must be finite");
        }
        double yawRadians = Math.toRadians(yaw % 360.0);
        double pitchRadians = Math.toRadians(Math.clamp((double) pitch, -90.0, 90.0));
        double sinYaw = Math.sin(yawRadians), cosYaw = Math.cos(yawRadians);
        double sinPitch = Math.sin(pitchRadians), cosPitch = Math.cos(pitchRadians);
        // look = (-sinYaw*cosPitch, -sinPitch, cosYaw*cosPitch)
        // right = (-cosYaw, 0, -sinYaw), defined even at vertical pitch.
        return new Point(
                eyeX + REAR_DISTANCE * sinYaw * cosPitch - shoulderRight * cosYaw,
                eyeY + REAR_DISTANCE * sinPitch + UP,
                eyeZ - REAR_DISTANCE * cosYaw * cosPitch - shoulderRight * sinYaw);
    }

    /** Opposite keys cancel before diagonal normalization; crouch scales the final vector. */
    public static InputVector input(boolean forward, boolean backward, boolean left, boolean right, boolean shift) {
        float strafe = (left ? 1f : 0f) - (right ? 1f : 0f);
        float ahead = (forward ? 1f : 0f) - (backward ? 1f : 0f);
        if (strafe != 0f && ahead != 0f) {
            float diagonal = (float) (1.0 / Math.sqrt(2.0));
            strafe *= diagonal;
            ahead *= diagonal;
        }
        if (shift) {
            strafe *= 0.3f;
            ahead *= 0.3f;
        }
        return new InputVector(strafe, ahead);
    }
}
