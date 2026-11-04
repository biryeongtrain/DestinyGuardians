package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base Moving Target sources and DDC row149 values. Static initialization reads only
 * pinned JSON; nested record construction never calls the enclosing weapon registries. */
public final class MovingTargetProfile {
    public static final String ID = "moving_target";
    public static final long HASH = 588594999L;
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        new WeaponPerks.Roll("duke_mk_44", 2112909414L, 4, HASH, 3815727680L),
        new WeaponPerks.Roll("distant_relation", 2034817450L, 4, HASH, 3824767299L),
        new WeaponPerks.Roll("bug_out_bag", 2744715540L, 4, HASH, 575371383L),
        new WeaponPerks.Roll("farewell", 541188001L, 3, HASH, 284168234L),
        new WeaponPerks.Roll("dead_man_walking_xx7463", 3751622019L, 3, HASH, 3268663985L),
        new WeaponPerks.Roll("biting_winds", 1621657423L, 3, HASH, 3968704963L),
        new WeaponPerks.Roll("bite_of_the_fox", 1403800851L, 4, HASH, 2442672691L),
        new WeaponPerks.Roll("beloved", 3107853529L, 4, HASH, 887157889L),
        new WeaponPerks.Roll("apostate", 2164448701L, 3, HASH, 1306932196L),
        new WeaponPerks.Roll("dust_rock_blues", 636912560L, 3, HASH, 3511609070L),
        new WeaponPerks.Roll("parcel_of_stardust_fell_to_earth", 2217366863L, 4, HASH, 3424940310L),
        new WeaponPerks.Roll("ikelos_sg_v1_0_1", 1887808042L, 4, HASH, 1324L), // curated fixed-roll legendary
        new WeaponPerks.Roll("dream_breaker", 2931957300L, 3, HASH, 3785896921L),
        new WeaponPerks.Roll("coriolis_force", 3512349612L, 3, HASH, 2568674372L),
        new WeaponPerks.Roll("line_in_the_sand", 946443267L, 3, HASH, 1503774254L),
        new WeaponPerks.Roll("deafening_whisper", 981718087L, 3, HASH, 3110206796L),
        new WeaponPerks.Roll("bellowing_giant", 2186258845L, 4, HASH, 1722393382L),
        new WeaponPerks.Roll("pyroclastic_flow", 1289324202L, 4, HASH, 3838086002L));
    private static final JsonObject PERK = JsonParser.parseString("""
        {"id":"moving_target","hash":588594999,"adsMovementPenaltyScalar":0.9,
         "sourceAimAssistBonus":10,"aimAssistImplemented":false}
        """).getAsJsonObject();
    private record Data(List<WeaponPerks.Roll> rolls, Map<String, WeaponCatalog.Entry> entries) {}
    private static final Data DATA = load();
    private MovingTargetProfile() {}

    private static void check(boolean value, String message) {
        if (!value) throw new IllegalStateException("Invalid W203 Moving Target: " + message);
    }
    private static JsonElement json(String path) {
        var stream = MovingTargetProfile.class.getResourceAsStream(path);
        check(stream != null, "missing " + path);
        try (stream) {
            return JsonParser.parseString(new String(stream.readAllBytes(), StandardCharsets.UTF_8));
        } catch (IOException e) { throw new IllegalStateException(e); }
    }
    private static Data load() {
        validate(json("/destiny/weapons/w203-moving-target.json").getAsJsonObject());
        var entries = new HashMap<String, WeaponCatalog.Entry>();
        for (var row : json("/destiny/weapons/w30.json").getAsJsonArray()) {
            var entry = GSON.fromJson(row, WeaponCatalog.Entry.class);
            if (EXPECTED.stream().anyMatch(r -> r.id().equals(entry.id())))
                check(entries.putIfAbsent(entry.id(), entry) == null, "duplicate canonical entry");
        }
        check(entries.size() == EXPECTED.size(), "18 canonical entries");
        var seen = new HashSet<String>();
        for (var row : json("/destiny/weapons/w40-characteristics.json").getAsJsonArray()) {
            var stat = row.getAsJsonObject();
            String id = stat.get("id").getAsString();
            if (!entries.containsKey(id)) continue;
            var roll = EXPECTED.stream().filter(r -> r.id().equals(id)).findFirst().orElseThrow();
            check(seen.add(id) && !stat.get("exotic").getAsBoolean()
                    && stat.get("bungieHash").getAsLong() == roll.hash(), "exact legendary item identity");
        }
        check(seen.size() == EXPECTED.size(), "complete characteristics");
        return new Data(EXPECTED, Map.copyOf(entries));
    }
    private static void validate(JsonObject root) {
        check(root.keySet().equals(Set.of("stage", "perk", "weapons"))
                && root.get("stage").getAsString().equals("W203")
                && PERK.equals(root.get("perk")), "schema/mechanics");
        var seen = new HashSet<WeaponPerks.Roll>();
        for (var row : root.getAsJsonArray("weapons")) {
            var roll = GSON.fromJson(row, WeaponPerks.Roll.class);
            check(roll != null && EXPECTED.contains(roll) && seen.add(roll)
                    && row.equals(GSON.toJsonTree(roll)), "exact unique base socket");
        }
        check(seen.size() == EXPECTED.size(), "complete 18 sockets");
    }
    static void validateResource(String value) {
        try { validate(JsonParser.parseString(value).getAsJsonObject()); }
        catch (RuntimeException e) { throw new IllegalStateException("Invalid W203 Moving Target resource", e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    public static boolean supports(String id) { return id != null && DATA.entries.containsKey(id); }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.equals(DATA.entries.get(entry.id()));
    }
    public static double adsMovementPenaltyScalar() { return 0.9; }
    /** Provenance only. The server does not simulate this aim-assist stat. */
    public static int sourceAimAssistBonus() { return 10; }
}
