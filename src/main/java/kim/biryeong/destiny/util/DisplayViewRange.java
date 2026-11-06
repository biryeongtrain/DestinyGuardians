package kim.biryeong.destiny.util;

/** Vanilla display visibility, compensating for its chunk-distance multiplier.
 * The client's separate entity-distance slider is not sent to the server. */
public final class DisplayViewRange {
    private DisplayViewRange() {}

    public static float nearCamera(float radius, int clientChunks, int serverChunks) {
        if (!Float.isFinite(radius) || radius <= 0) throw new IllegalArgumentException("Positive finite radius required");
        int effective = serverChunks > 0 ? Math.min(clientChunks, serverChunks) : clientChunks;
        double chunkScale = Math.clamp(effective / 8.0, 1.0, 2.5);
        return (float) (radius / (64 * chunkScale));
    }
}
