package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Exact base sockets and community radius; damage and falloff are authored Minecraft PvE tuning. */
public final class DragonflyProfile {
    public static final String ID = "dragonfly";
    public static final long HASH = 2848615171L;
    public record Source(String authority, String url, String sourceSha256) {}
    public record Policy(String authority, String units, String scaling, String description) {}
    public record Perk(String id, long hash, double radiusMeters, float damageHp, float falloffFloor,
                       Source radiusSource, Source officialChange, Policy damagePolicy, Policy falloffPolicy) {}
    private record Data(String stage, Perk perk, WeaponPerks.Roll[] weapons) {}
    private static final String COMMUNITY_URL = "https://www.light.gg/db/items/2848615171/dragonfly/";
    private static final String OFFICIAL_URL = "https://www.bungie.net/7/en/News/Article/twid_07_03_2025";
    private static final Set<WeaponPerks.Roll> EXPECTED_ROLLS = Set.of(
            new WeaponPerks.Roll("brass_attacks", 2121785039L, 4, HASH, 3403850295L),
            new WeaponPerks.Roll("distant_relation", 2034817450L, 4, HASH, 3824767299L),
            new WeaponPerks.Roll("line_in_the_sand", 946443267L, 4, HASH, 3257645194L),
            new WeaponPerks.Roll("long_arm", 8293111L, 4, HASH, 619833418L));
    private static final Data DATA = load();
    private DragonflyProfile() {}

    private static Data load() {
        var input = DragonflyProfile.class.getResourceAsStream("/destiny/weapons/w77-dragonfly.json");
        if (input == null) throw new IllegalStateException("Missing W77 Dragonfly profile");
        try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            if (data == null || !"W77".equals(data.stage) || data.perk == null || data.weapons == null)
                throw new IllegalStateException("Invalid W77 Dragonfly profile");
            var p = data.perk;
            if (!ID.equals(p.id) || p.hash != HASH || !Double.isFinite(p.radiusMeters) || p.radiusMeters != 4.5
                    || !Float.isFinite(p.damageHp) || p.damageHp != 10f
                    || !Float.isFinite(p.falloffFloor) || p.falloffFloor != .3f
                    || !source(p.radiusSource, "community", COMMUNITY_URL)
                    || !source(p.officialChange, "official", OFFICIAL_URL)
                    || !policy(p.damagePolicy, "Minecraft HP", "fixed_perk_damage")
                    || !policy(p.falloffPolicy, "damage fraction", "linear_floor")
                    || data.weapons.length != EXPECTED_ROLLS.size())
                throw new IllegalStateException("Invalid W77 Dragonfly mechanics/provenance");
            var seen = new HashSet<WeaponPerks.Roll>();
            var sockets = new HashSet<String>();
            for (var roll : data.weapons) {
                if (roll == null || roll.id() == null)
                    throw new IllegalStateException("Missing W77 Dragonfly socket identity");
                var entry = WeaponCatalog.find(roll.id()).orElseThrow(
                        () -> new IllegalStateException("Unknown W77 weapon " + roll.id()));
                var c = WeaponCharacteristics.of(entry);
                if (roll.hash() != c.bungieHash() || roll.perkHash() != HASH || c.exotic()
                        || roll.socket() < 0 || roll.socket() > 63
                        || roll.plugSetHash() <= 0 || roll.plugSetHash() > 0xffffffffL
                        || !Set.of(WeaponCharacteristics.Damage.ARC, WeaponCharacteristics.Damage.SOLAR,
                                   WeaponCharacteristics.Damage.VOID).contains(c.damage())
                        || !Set.of("scout_rifle", "sidearm", "linear_fusion_rifle").contains(entry.family())
                        || !EXPECTED_ROLLS.contains(roll) || !seen.add(roll)
                        || !sockets.add(roll.id() + ":" + roll.socket()))
                    throw new IllegalStateException("Invalid W77 Dragonfly trait socket " + roll);
            }
            if (!seen.equals(EXPECTED_ROLLS)) throw new IllegalStateException("Incomplete W77 Dragonfly rolls");
            return data;
        } catch (java.io.IOException e) { throw new IllegalStateException("Unreadable W77 Dragonfly profile", e); }
    }

    private static boolean source(Source source, String authority, String url) {
        return source != null && authority.equals(source.authority) && url.equals(source.url)
                && source.sourceSha256 != null && source.sourceSha256.matches("[0-9a-f]{64}");
    }
    private static boolean policy(Policy policy, String units, String scaling) {
        return policy != null && "local_authored_pve".equals(policy.authority)
                && units.equals(policy.units) && scaling.equals(policy.scaling)
                && policy.description != null && !policy.description.isBlank();
    }
    public static Perk perk() { return DATA.perk; }
    public static List<WeaponPerks.Roll> rolls() { return List.of(DATA.weapons); }
    /** Community 4.5 m radius, mapped to 4.5 Minecraft blocks by local policy. */
    public static double radius() { return DATA.perk.radiusMeters; }
    /** Fixed center damage: authored PvE tuning, not original Destiny damage or weapon-shot scaling. */
    public static float damage() { return DATA.perk.damageHp; }
    /** Local linear attenuation floor inside the radius; outside-radius damage is zero. */
    public static float falloffFloor() { return DATA.perk.falloffFloor; }
}
