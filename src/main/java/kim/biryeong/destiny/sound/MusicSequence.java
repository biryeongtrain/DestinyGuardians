package kim.biryeong.destiny.sound;

import java.util.List;
import java.util.Objects;

/** Per-listener activity policy. MusicService owns audio duration; only inter-track gaps live here. */
public final class MusicSequence {
    public enum Scene { NONE, TOWER, INTRO, RESULTS }
    public record Track(String event, double seconds, float volume) {
        public Track {
            if (event == null || !event.matches("[a-z0-9_]+") || !Double.isFinite(seconds)
                    || seconds <= 0 || !Float.isFinite(volume) || volume <= 0 || volume > 1)
                throw new IllegalArgumentException("Invalid music track");
        }
    }
    public record Change(boolean stop, Track play) {
        static final Change NONE = new Change(false, null);
    }
    private Scene scene = Scene.NONE;
    private List<Track> tracks = List.of();
    private int index;
    private long nextAt;
    private boolean playing, completed;

    public Change update(Scene desired, List<Track> playlist, boolean ready, boolean playbackDone, long now) {
        Objects.requireNonNull(desired);
        boolean stop = false;
        if (desired != scene) {
            stop = playing; scene = desired; tracks = List.copyOf(playlist);
            index = 0; playing = false; completed = false; nextAt = now;
        }
        if (!ready) {
            stop |= playing;
            // A one-shot already heard (even partly) must not restart on a pack reload.
            completed = scene != Scene.TOWER && (completed || playing);
            playing = false; nextAt = now;
            return stop ? new Change(true, null) : Change.NONE;
        }
        if (scene == Scene.NONE || tracks.isEmpty() || completed) return stop ? new Change(true, null) : Change.NONE;
        if (playing && !playbackDone) return stop ? new Change(true, null) : Change.NONE;
        if (playing) {
            playing = false; stop = true;
            if (scene != Scene.TOWER) { completed = true; return new Change(true, null); }
            index = (index + 1) % tracks.size();
            nextAt = now + 3_000_000_000L;
            return new Change(true, null);
        }
        if (now < nextAt) return stop ? new Change(true, null) : Change.NONE;
        Track track = tracks.get(index); playing = true;
        return new Change(stop, track);
    }
    public Scene scene() { return scene; }
}
