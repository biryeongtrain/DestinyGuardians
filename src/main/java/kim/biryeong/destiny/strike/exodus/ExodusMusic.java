package kim.biryeong.destiny.strike.exodus;

import kim.biryeong.destiny.activity.strike.StrikeScore;
import net.minecraft.server.level.ServerPlayer;

import java.util.List;

/**
 * Score selection for Exodus Crash. The extracted Exodus score (90 MB) is not packaged yet, so this reuses the Devils
 * Lair score sections: travel -> low intensity, combat -> strike combat, charge/defend -> hold sections, boss -> finale.
 */
final class ExodusMusic implements AutoCloseable {
    private static final StrikeScore.Spec SPEC = new StrikeScore.Spec(
            "/destiny/devils_lair/music.json", "destiny_music", "Exodus music");
    private final StrikeScore score = new StrikeScore(SPEC);

    static int section(ExodusPlan.BeatKind kind, boolean active, boolean complete) {
        if (complete) return 9;
        if (!active) return 0;
        return switch (kind) {
            case ADVANCE -> 0; case COMBAT -> 5; case CHARGE -> 2; case DEFEND -> 3; case BOSS -> 7;
        };
    }
    void tick(int section, List<ServerPlayer> audience, long now) { score.tick(section, audience, now); }
    void remove(ServerPlayer p) { score.remove(p); }
    @Override public void close() { score.close(); }
}
