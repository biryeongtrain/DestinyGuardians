package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

/** Base Under Pressure, DDC Weapon Perks row239. Accuracy: 12.5% to 25% smaller cone
 * strictly below half, linear to empty. +30? stability remains UNVERIFIED: the 0..30
 * linear integer ramp is temporary server tuning. No original cartridge-timing claim.
 * Invalid sources/resources/rounds have neutral 0/1 effects; no gameplay state or writes.
 */
public final class UnderPressureProfile {
    public static final String ID = "under_pressure";
    public static final long HASH = 1645158859L;
    public static final boolean ORIGINAL_STABILITY_VERIFIED = false;
    public static final int TEMPORARY_SERVER_STABILITY_CAP = 30;
    private static final String RESOURCE = "/destiny/weapons/w190-under-pressure.json";
    private static final String RESOURCE_SHA256 = "895a9e398913bc4236f3949a1a3dc1efa99e52540f666c7de760d7d043ce5e30";
    private static final String CATALOG_SHA256 = "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a";
    private static final Gson GSON = new Gson();
    private static final List<WeaponPerks.Roll> EXPECTED = List.of(
        roll("bygones", 2712244741L, 4, 3060320121L),
        roll("chattering_bone", 568515759L, 4, 423791138L),
        roll("patron_of_lost_causes", 2723241847L, 4, 120674550L),
        roll("long_arm", 8293111L, 3, 3056706286L),
        roll("dead_man_walking_xx7463", 3751622019L, 3, 3268663985L),
        roll("erentil_fr4", 2398848320L, 3, 664L), // curated fixed-roll legendary
        roll("hollow_words", 607191995L, 3, 637298592L),
        roll("dream_breaker", 2931957300L, 3, 3785896921L),
        roll("coriolis_force", 3512349612L, 3, 2568674372L),
        roll("line_in_the_sand", 946443267L, 3, 1503774254L),
        roll("fixed_odds", 2194955522L, 3, 4227334000L));
    private record Data(List<WeaponPerks.Roll> rolls, Map<String, WeaponCatalog.Entry> canonical) {}
    private static final Data DATA = load();
    private UnderPressureProfile() {}

    private static WeaponPerks.Roll roll(String id, long hash, int socket, long pool) {
        return new WeaponPerks.Roll(id, hash, socket, HASH, pool);
    }
    private static void require(boolean ok, String detail) {
        if (!ok) throw new IllegalStateException("Invalid W190 Under Pressure: " + detail);
    }
    private static String pinned(String path, String expected)
            throws IOException, NoSuchAlgorithmException {
        try (var stream = UnderPressureProfile.class.getResourceAsStream(path)) {
            require(stream != null, "missing " + path);
            byte[] bytes = stream.readAllBytes();
            require(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))
                    .equals(expected), "checksum " + path);
            return new String(bytes, StandardCharsets.UTF_8);
        }
    }
    private static Data load() {
        try {
            // Independent pinned catalog read avoids registry/class-initialization cycles.
            var root = JsonParser.parseString(pinned(RESOURCE, RESOURCE_SHA256)).getAsJsonObject();
            require(root.get("stage").getAsString().equals("W190"), "stage");
            var perk = root.getAsJsonObject("perk");
            require(perk.get("id").getAsString().equals(ID) && perk.get("hash").getAsLong() == HASH
                    && !perk.get("originalStabilityVerified").getAsBoolean()
                    && perk.get("temporaryServerStabilityCap").getAsInt() == TEMPORARY_SERVER_STABILITY_CAP,
                    "base identity and temporary tuning policy");
            List<WeaponPerks.Roll> rolls = List.of(GSON.fromJson(root.get("weapons"), WeaponPerks.Roll[].class));
            require(rolls.equals(EXPECTED), "exact eleven official sockets");
            var canonical = new HashMap<String, WeaponCatalog.Entry>();
            var entries = GSON.fromJson(pinned("/destiny/weapons/w30.json", CATALOG_SHA256), WeaponCatalog.Entry[].class);
            for (var entry : entries) {
                if (rolls.stream().anyMatch(r -> r.id().equals(entry.id())))
                    require(canonical.putIfAbsent(entry.id(), entry) == null, "duplicate catalog ID");
            }
            require(canonical.size() == EXPECTED.size(), "canonical coverage");
            return new Data(rolls, Map.copyOf(canonical));
        } catch (IOException | NoSuchAlgorithmException | RuntimeException invalid) {
            System.getLogger(UnderPressureProfile.class.getName()).log(System.Logger.Level.WARNING,
                    "W190 Under Pressure disabled: missing or invalid pinned data", invalid);
            return new Data(List.of(), Map.of());
        }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.rolls; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && entry.id() != null && entry.equals(DATA.canonical.get(entry.id()));
    }
    private static boolean belowHalf(WeaponCatalog.Entry entry, int rounds, int baseCapacity) {
        return supports(entry) && baseCapacity > 0 && rounds >= 0 && rounds <= baseCapacity
                && baseCapacity == WeaponProfile.forEntry(entry).magazine()
                && 2L * rounds < baseCapacity;
    }
    /** Pure explicit-round query; caller decides evaluation time. Empty is a valid passive state.
     * Integer floor is local tuning; use long intermediates for overflow-safe rational arithmetic.
     */
    public static int stabilityBonus(WeaponCatalog.Entry entry, int rounds, int baseCapacity) {
        if (!belowHalf(entry, rounds, baseCapacity)) return 0;
        return (int)(TEMPORARY_SERVER_STABILITY_CAP * (baseCapacity - 2L * rounds) / baseCapacity);
    }
    /** Cone SIZE scalar only. Exactly half/full/invalid is 1; empty is .75.
     * Just below half approaches .875; no growth, aim-assist or extra recoil multiplier.
     */
    public static double accuracyScalar(WeaponCatalog.Entry entry, int rounds, int baseCapacity) {
        if (!belowHalf(entry, rounds, baseCapacity)) return 1;
        double progress = (baseCapacity - 2L * rounds) / (double)baseCapacity;
        return 1 - (.125 + .125 * progress);
    }
}
