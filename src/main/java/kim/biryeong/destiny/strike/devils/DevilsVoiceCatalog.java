package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.activity.strike.StrikeVoiceCatalog;
import kim.biryeong.destiny.activity.strike.StrikeVoicePlayback;
import net.minecraft.server.level.ServerPlayer;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.LongConsumer;
import java.util.function.Predicate;
import java.util.function.Supplier;

/** The Devils' Lair table over the shared voice catalog; the twelve base lines of the strike only. */
public final class DevilsVoiceCatalog {
    private static final StrikeVoiceCatalog CATALOG = new StrikeVoiceCatalog(new StrikeVoiceCatalog.Spec(
            "/destiny/devils_lair/subtitles_ko.json", "80b59f[0-9a-f]{2}", "destiny_devils:voice.",
            "/assets/destiny_devils/sounds/voice/", 12));
    private DevilsVoiceCatalog() { }
    public static Optional<StrikeVoiceCatalog.Line> line(String id) { return CATALOG.line(id); }
    public static Map<String, StrikeVoiceCatalog.Line> lines() { return CATALOG.lines(); }
    public static StrikeVoicePlayback playback(Supplier<List<ServerPlayer>> audience, LongConsumer completed) {
        return new StrikeVoicePlayback(CATALOG, DevilsVoiceCatalog::fallbackText, audience, completed);
    }
    /** Test seam: decide clip availability without touching the packaged resources. */
    static StrikeVoicePlayback playback(Supplier<List<ServerPlayer>> audience, LongConsumer completed,
                                        Predicate<StrikeVoiceCatalog.Line> available) {
        return new StrikeVoicePlayback(CATALOG, DevilsVoiceCatalog::fallbackText, audience, completed, available);
    }
    /** Authored gameplay notices; never attributed to the original Ghost or Zavala dialogue. */
    static String fallbackText(String id) {
        return switch (id) {
            case "80b59f27" -> "정제소로 향하는 길을 확보하세요.";
            case "80b59f22" -> "정제소의 몰락자와 군체를 처치하세요.";
            case "80b59f1d" -> "보안 장치에 고스트를 배치하세요.";
            case "80b59f26" -> "해킹을 시작합니다. 적의 공격에 대비하세요.";
            case "80b59f25", "80b59f20", "80b59f21" -> "증원 병력이 접근합니다. 고스트를 보호하세요.";
            case "80b59f24" -> "장벽이 해제되었습니다. 화력팀과 함께 이동하세요.";
            case "80b59f23" -> "워커와 브리그를 파괴하고 진입로를 확보하세요.";
            case "80b59f1e" -> "워커가 파괴되었습니다. 남은 목표를 확인하세요.";
            case "80b59f1f" -> "세픽스 프라임의 소굴에 진입합니다.";
            case "80b59f28" -> "공격전을 완료했습니다. 귀환을 준비하세요.";
            default -> "음성 안내를 재생할 수 없습니다. 임무 목표를 확인하세요.";
        };
    }
}
