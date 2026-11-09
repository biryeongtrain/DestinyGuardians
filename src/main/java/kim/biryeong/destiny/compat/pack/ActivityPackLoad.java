package kim.biryeong.destiny.compat.pack;

import java.util.UUID;

/** One wire request. Old acknowledgements and duplicate progress cannot approve a newer request. */
public final class ActivityPackLoad {
    public enum Stage { REQUESTED, ACCEPTED, DOWNLOADED, READY, FAILED }
    private final UUID request;
    private Stage stage = Stage.REQUESTED;
    private String failure;
    public ActivityPackLoad(UUID request) { this.request = request; }
    public UUID request() { return request; }
    public Stage stage() { return stage; }
    public boolean ready() { return stage == Stage.READY; }
    public String failure() { return failure; }
    public void response(UUID request, String action) {
        if (!this.request.equals(request) || stage == Stage.FAILED) return;
        switch (action) {
            case "SUCCESSFULLY_LOADED" -> stage = Stage.READY;
            case "ACCEPTED" -> { if (stage == Stage.REQUESTED) stage = Stage.ACCEPTED; }
            case "DOWNLOADED" -> { if (stage != Stage.READY) stage = Stage.DOWNLOADED; }
            case "DECLINED", "FAILED_DOWNLOAD", "INVALID_URL", "FAILED_RELOAD", "DISCARDED" -> fail(action);
            default -> { }
        }
    }
    public void fail(String reason) { stage = Stage.FAILED; failure = reason; }
}
