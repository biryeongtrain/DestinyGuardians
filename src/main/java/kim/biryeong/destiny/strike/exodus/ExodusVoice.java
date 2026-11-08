package kim.biryeong.destiny.strike.exodus;

import kim.biryeong.destiny.activity.strike.StrikeVoiceCatalog;
import kim.biryeong.destiny.activity.strike.StrikeVoicePlayback;
import net.minecraft.server.level.ServerPlayer;

import java.util.List;
import java.util.function.LongConsumer;
import java.util.function.Supplier;

/** Exodus Crash's 62 Korean lines over the shared voice catalog, plus which line plays at which moment. */
public final class ExodusVoice {
    private static final StrikeVoiceCatalog CATALOG = new StrikeVoiceCatalog(new StrikeVoiceCatalog.Spec(
            "/destiny/exodus_crash/subtitles_ko.json", "80b5c2[0-9a-f]{2}", "destiny_exodus:voice.",
            "/assets/destiny_exodus/sounds/voice/", 62));
    private ExodusVoice() { }

    public static StrikeVoiceCatalog catalog() { return CATALOG; }
    public static StrikeVoicePlayback playback(Supplier<List<ServerPlayer>> audience, LongConsumer completed) {
        return new StrikeVoicePlayback(CATALOG, id -> "임무 안내: 목표를 확인하세요.", audience, completed);
    }

    /** Lines played when a beat begins (id of the beat to the extracted clips, in order). */
    static List<String> opening(String beat) {
        return switch (beat) {
            case "B00" -> List.of("80b5c238", "80b5c24f");
            case "B01" -> List.of("80b5c244");
            case "B02" -> List.of("80b5c229", "80b5c22c", "80b5c22a");
            case "B03" -> List.of("80b5c233", "80b5c22d", "80b5c22e");
            case "B04" -> List.of("80b5c222");
            case "B05" -> List.of("80b5c243", "80b5c242");
            case "B06" -> List.of("80b5c248");
            case "B07" -> List.of("80b5c249");
            case "B08" -> List.of("80b5c23d", "80b5c241");
            case "B09" -> List.of("80b5c232");
            case "B10" -> List.of("80b5c257", "80b5c256");
            case "B11" -> List.of("80b5c211", "80b5c216", "80b5c213");
            default -> List.of();
        };
    }
    /** First Arc charge of a charge phase drops. */
    static final String FIRST_CHARGE = "80b5c235";
    /** The charge goal is reached. */
    static final String CHARGE_DONE = "80b5c236";
    /** The boss's stealth field comes back. */
    static final String FIELD_BACK = "80b5c217";
    /** Strike complete. */
    static final List<String> COMPLETE = List.of("80b5c25e", "80b5c251");
}
