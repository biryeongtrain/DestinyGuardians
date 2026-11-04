package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact official sockets; damage/refresh official, absolute timing separately community-measured. */
public final class KillClipProfile {
    public static final String ID = "kill_clip";
    public static final long HASH = 1015611457L;
    public record Perk(String id, long hash, int killWindowTicks, int durationTicks, float multiplier, String timingSource) {}
    private record Data(String stage, Perk perk, WeaponPerks.Roll[] weapons) {}
    private static final Data DATA = load();
    private KillClipProfile() {}
    private static Data load() {
        var input = KillClipProfile.class.getResourceAsStream("/destiny/weapons/w61-kill-clip.json");
        if (input == null) throw new IllegalStateException("Missing W61 Kill Clip data");
        try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            if (d == null || !"W61".equals(d.stage) || d.perk == null || !ID.equals(d.perk.id) || d.perk.hash != HASH
                    || d.perk.killWindowTicks < 1 || d.perk.killWindowTicks > 1200 || d.perk.durationTicks < 1 || d.perk.durationTicks > 1200
                    || !Float.isFinite(d.perk.multiplier) || d.perk.multiplier <= 1 || d.perk.multiplier > 2
                    || d.perk.timingSource == null || d.perk.timingSource.isBlank() || d.weapons == null || d.weapons.length == 0)
                throw new IllegalStateException("Invalid W61 perk profile");
            var seen = new HashSet<String>();
            for (var r : d.weapons) {
                var e = WeaponCatalog.find(r.id()).orElseThrow(); var meta = WeaponCharacteristics.of(e);
                if (r.hash() != meta.bungieHash() || r.perkHash() != HASH || r.socket() < 0 || r.socket() > 63
                        || r.plugSetHash() <= 0 || meta.exotic() || e.family().equals("sword")
                        || !seen.add(r.id() + ":" + r.socket())) throw new IllegalStateException("Invalid W61 trait socket " + r);
            }
            return d;
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static Perk perk() { return DATA.perk; }
    public static List<WeaponPerks.Roll> rolls() { return List.of(DATA.weapons); }
}
