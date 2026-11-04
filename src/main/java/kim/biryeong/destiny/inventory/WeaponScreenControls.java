package kim.biryeong.destiny.inventory;

/** Screen-space cursor integrates vanilla view deltas, without a client mod or OS pointer capture. */
public final class WeaponScreenControls {
    private float x = 232, y = 352, yaw, pitch;
    private boolean primed;
    public float x() { return x; }
    public float y() { return y; }
    /** View rotation the current position belongs to. */
    public float yaw() { return yaw; }
    public float pitch() { return pitch; }
    public void point(float x, float y) {
        if (!Float.isFinite(x) || !Float.isFinite(y)) return;
        this.x = Math.clamp(x, 24, 1896); this.y = Math.clamp(y, 24, 1056);
    }
    public void baseline(float yaw, float pitch) {
        if (!Float.isFinite(yaw) || !Float.isFinite(pitch)) return;
        this.yaw = yaw; this.pitch = pitch; primed = true;
    }
    public boolean rotate(float yaw, float pitch) {
        if (!Float.isFinite(yaw) || !Float.isFinite(pitch)) return false;
        if (!primed) { baseline(yaw, pitch); return false; }
        float dx = wrap(yaw - this.yaw), dy = pitch - this.pitch;
        baseline(yaw, pitch);
        float oldX = x, oldY = y;
        point(x + Math.clamp(dx, -90, 90) * 15, y + Math.clamp(dy, -90, 90) * 15);
        return Math.abs(x - oldX) + Math.abs(y - oldY) > .05;
    }
    private static float wrap(float value) { return ((value + 180) % 360 + 360) % 360 - 180; }
}
