package kim.biryeong.destiny.inventory;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.Map;

/** Screen-only Korean labels; canonical item identifiers and combat data stay unchanged. */
public final class WeaponScreenText {
    private record Names(Map<String, String> names) {}
    private static final Map<String, String> WEAPONS = load();
    private WeaponScreenText() {}

    private static Map<String, String> load() {
        var stream = WeaponScreenText.class.getResourceAsStream("/destiny/weapons/w227-ko.json");
        if (stream == null) throw new IllegalStateException("Missing Korean weapon names");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return Map.copyOf(new Gson().fromJson(reader, Names.class).names());
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static String weapon(String id, String fallback) { var extra = kim.biryeong.destiny.weapon.LegendaryWeapons.name(id); return extra == null ? WEAPONS.getOrDefault(id, fallback) : extra; }
    public static String family(String value) {
        return switch (key(value)) {
            case "hand_cannon" -> "핸드 캐논"; case "auto_rifle" -> "자동 소총";
            case "pulse_rifle" -> "파동 소총"; case "scout_rifle" -> "정찰 소총";
            case "submachine_gun" -> "기관단총"; case "sidearm" -> "보조 무기";
            case "bow" -> "활"; case "sniper_rifle" -> "저격총"; case "shotgun" -> "산탄총";
            case "fusion_rifle" -> "융합 소총"; case "linear_fusion_rifle" -> "선형 융합 소총";
            case "trace_rifle" -> "추적 소총";
            case "grenade_launcher", "heavy_grenade_launcher" -> "유탄 발사기";
            case "rocket_launcher" -> "로켓 발사기"; case "machine_gun" -> "기관총";
            case "sword" -> "검"; case "glaive" -> "월도"; default -> value == null ? "—" : value;
        };
    }
    public static String frame(String value) {
        return switch (key(value)) {
            case "adaptive_frame" -> "적응형 프레임"; case "aggressive_frame" -> "공격적 프레임";
            case "precision_frame" -> "정밀 프레임"; case "lightweight_frame" -> "경량 프레임";
            case "high-impact_frame" -> "고위력 프레임"; case "rapid-fire_frame" -> "속사 프레임";
            case "adaptive_burst" -> "적응형 점발사격"; case "aggressive_burst" -> "공격적 점발사격";
            case "heavy_burst" -> "중량 점발사격"; case "adaptive_glaive" -> "적응형 월도";
            case "pinpoint_slug_frame" -> "정밀 납탄 프레임"; case "wave_frame" -> "파동 프레임";
            case "compressed_wave_frame" -> "압축 파동 프레임";
            case "vortex_frame" -> "소용돌이 프레임"; case "caster_frame" -> "시전자 프레임";
            case "memento_mori" -> "메멘토 모리"; case "honed_edge" -> "날카로운 칼날";
            default -> value == null ? "—" : value;
        };
    }
    public static String damage(String value) {
        return switch (key(value)) {
            case "kinetic" -> "물리"; case "arc" -> "전기"; case "solar" -> "태양";
            case "void" -> "공허"; case "stasis" -> "시공"; case "strand" -> "초월";
            default -> value == null ? "—" : value;
        };
    }
    public static String ammo(String value) {
        return switch (key(value)) {
            case "primary" -> "주 무기"; case "special" -> "특수 화기"; case "heavy" -> "중화기";
            default -> value == null ? "—" : value;
        };
    }
    private static String key(String value) { return value == null ? "" : value.strip().replace(' ', '_').toLowerCase(Locale.ROOT); }
}
