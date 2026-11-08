package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.activity.strike.StrikeScore;
import net.minecraft.server.level.ServerPlayer;
import java.util.List;

/** Devils' Lair adapter over the shared strike score: which score section each phase plays. */
final class DevilsMusic implements AutoCloseable {
    private static final StrikeScore.Spec SPEC = new StrikeScore.Spec(
            "/destiny/devils_lair/music.json", "destiny_music", "Devils music");
    private final StrikeScore score = new StrikeScore(SPEC);

    static int section(DevilsDirector.Phase phase) {
        return switch(phase) {
            case READY,BRIEFING,CLOSED -> -1;
            case RY_APPROACH,RY_CLEAR,RF_ENTRY -> 0;
            case RF_DEVICE -> 1;
            case RF_HACK,RF_DEFENSE1 -> 2;
            case RF_INTERMISSION1,RF_DEFENSE2 -> 3;
            case RF_INTERMISSION2,RF_DEFENSE3 -> 4;
            case RF_CLEAR,BL_BATTLE -> 5;
            case BL_CLEAR,SP_GUARD,SP_INTRO -> 6;
            case SP_DAMAGE1,SP_SHIELD1,SP_RECOVER1,SP_DAMAGE2,SP_SHIELD2,SP_RECOVER2,SP_DAMAGE3 -> 7;
            case COMPLETE -> 9;
        };
    }
    void tick(DevilsDirector.Phase phase, List<ServerPlayer> audience, long now) { score.tick(section(phase), audience, now); }
    void remove(ServerPlayer p) { score.remove(p); }
    @Override public void close() { score.close(); }
}
