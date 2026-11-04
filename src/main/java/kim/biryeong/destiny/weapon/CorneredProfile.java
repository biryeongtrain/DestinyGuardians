package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;

/** BASIC DDC Weapon Perks row57. Static loading is JSON-only: no registry calls/cycles.
 * Enhanced active/passive stability is excluded. Exact current canonical support is checked lazily.
 */
public final class CorneredProfile {
    public static final String ID = "cornered";
    public static final long HASH = 1799762209L;
    private static final String SHA256 = "4dbd6fdcbe0830cfb0310b64024a11b7003448ba676d86465e1198abb10a3e29";
    private record Perk(String id, long hash, int enemiesRequired, double radiusMetres,
                        double chargeTimeMultiplier, int lingerTicks) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons) {}
    private static final Data DATA = load();
    private CorneredProfile() {}

    private static Data load() {
        var stream = CorneredProfile.class.getResourceAsStream("/destiny/weapons/w226-cornered.json");
        if (stream == null) throw new IllegalStateException("Missing W226 Cornered");
        try (stream) {
            var bytes = stream.readAllBytes();
            var digest = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
            if (!SHA256.equals(digest)) throw new IllegalStateException("Changed W226 Cornered resource");
            var d = new Gson().fromJson(new String(bytes, StandardCharsets.UTF_8), Data.class);
            var expected = new WeaponPerks.Roll("dream_breaker", 2931957300L, 4, HASH, 1206254527L);
            if (d == null || !"W226".equals(d.stage) || d.perk == null
                || !ID.equals(d.perk.id) || d.perk.hash != HASH
                || d.perk.enemiesRequired != CorneredCycle.ENEMIES_REQUIRED || d.perk.radiusMetres != 15
                || d.perk.chargeTimeMultiplier != .85 || d.perk.lingerTicks != CorneredCycle.LINGER_TICKS
                || !List.of(expected).equals(d.weapons))
                throw new IllegalStateException("Invalid W226 BASIC Cornered definition/socket");
            return new Data(d.stage, d.perk, List.copyOf(d.weapons));
        } catch (IOException | NoSuchAlgorithmException e) { throw new IllegalStateException(e); }
    }

    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && "fusion_rifle".equals(entry.family())
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id()))
            && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && !WeaponCharacteristics.of(entry).exotic()
            && DATA.weapons.getFirst().hash() == WeaponCharacteristics.of(entry).bungieHash();
    }
    public static int enemiesRequired() { return DATA.perk.enemiesRequired; }
    public static double radiusMetres() { return DATA.perk.radiusMetres; }
    public static double chargeTimeMultiplier() { return DATA.perk.chargeTimeMultiplier; }
    public static int lingerTicks() { return DATA.perk.lingerTicks; }

    /** Local 1 metre = 1 block, inclusive 3D footpoint distance, same as Threat Detector. */
    public static boolean withinRadius(double dx, double dy, double dz) {
        double squared = dx * dx + dy * dy + dz * dz;
        return Double.isFinite(squared) && squared <= radiusMetres() * radiusMetres();
    }

    /** Immutable accepted snapshot; only chargeTicks changes. Backup Plan cannot co-select. */
    public static WeaponProfile charge(WeaponCatalog.Entry entry, WeaponProfile base) {
        Objects.requireNonNull(base, "accepted charge profile");
        if (!supports(entry)) throw new IllegalArgumentException("Noncanonical Cornered weapon");
        if (base.chargeTicks() <= 0) return base;
        int ticks = (int)Math.ceil(base.chargeTicks() * chargeTimeMultiplier());
        return new WeaponProfile(base.mode(), base.damage(), base.intervalTicks(), base.magazine(),
            base.reserve(), base.reloadTicks(), base.range(), ticks, base.burst(), base.pellets(),
            base.spread(), base.speed(), base.gravity(), base.blastRadius(), base.automatic(),
            base.infiniteReserve(), base.cadenceTicks(), base.burstSpacingTicks(), base.sharedBurstAmmo(),
            base.shellReload(), base.firstReloadTicks(), base.roundsPerInsert());
    }
}
