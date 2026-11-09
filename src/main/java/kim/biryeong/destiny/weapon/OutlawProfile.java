package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Pinned exact sockets and effective reload curves; absolute durations are community approximations. */
public final class OutlawProfile {
    public static final String ID = "outlaw";
    public static final long HASH = 1168162263L;
    public record Perk(String id, long hash, int durationTicks, int reloadBonus, double durationMultiplier, String timingSource) {}
    public record Reload(String id, int firstTicks, int intervalTicks, int baseReloadStat, int effectiveReloadStat) {}
    private record Data(String stage, Perk perk, WeaponPerks.Roll[] weapons, Reload[] reloads) {}
    private static final Data DATA = load();
    private static final Map<String, Reload> RELOADS = index();
    private OutlawProfile() {}
    private static Data load() {
        var stream = OutlawProfile.class.getResourceAsStream("/destiny/weapons/w62-outlaw.json");
        if (stream == null) throw new IllegalStateException("Missing W62 Outlaw profile");
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            if (d == null || !"W62".equals(d.stage) || d.perk == null || !ID.equals(d.perk.id) || d.perk.hash != HASH
                    || d.perk.durationTicks < 1 || d.perk.durationTicks > 1200 || d.perk.reloadBonus < 1 || d.perk.reloadBonus > 100
                    || !Double.isFinite(d.perk.durationMultiplier) || d.perk.durationMultiplier <= 0 || d.perk.durationMultiplier > 1
                    || d.perk.timingSource == null || d.perk.timingSource.isBlank() || d.weapons == null || d.weapons.length == 0
                    || d.reloads == null || d.reloads.length == 0) throw new IllegalStateException("Invalid W62 profile");
            var slots = new HashSet<String>(); var ids = new HashSet<String>();
            for (var roll : d.weapons) {
                var entry = WeaponCatalog.find(roll.id()).orElseThrow(); var meta = WeaponCharacteristics.of(entry);
                if (roll.hash() != meta.bungieHash() || roll.perkHash() != HASH || roll.socket() < 0 || roll.socket() > 63
                        || roll.plugSetHash() <= 0 || meta.exotic() || entry.family().equals("sword")
                        || !slots.add(roll.id() + ":" + roll.socket())) throw new IllegalStateException("Invalid Outlaw socket " + roll);
                ids.add(roll.id());
            }
            var plans = new HashSet<String>();
            for (var reload : d.reloads) {
                if (reload == null || !ids.contains(reload.id) || !plans.add(reload.id)
                        || reload.firstTicks < 1 || reload.firstTicks > 1200 || reload.intervalTicks < 1 || reload.intervalTicks > 1200
                        || reload.baseReloadStat < 0 || reload.baseReloadStat > 100
                        || reload.effectiveReloadStat != Math.min(100, reload.baseReloadStat + d.perk.reloadBonus))
                    throw new IllegalStateException("Invalid Outlaw reload " + reload);
                var base = WeaponProfile.forEntry(WeaponCatalog.find(reload.id).orElseThrow());
                var stats = WeaponCharacteristics.of(WeaponCatalog.find(reload.id).orElseThrow()).stats();
                if (!Objects.equals(stats.get("4188031367"),reload.baseReloadStat))
                    throw new IllegalStateException("Outlaw base stat does not match selected official weapon " + reload.id);
                if (reload.firstTicks > base.firstReloadTicks() || reload.intervalTicks > base.reloadTicks())
                    throw new IllegalStateException("Outlaw may not slow a selected weapon " + reload.id);
            }
            if (!plans.equals(ids)) throw new IllegalStateException("Incomplete Outlaw effective reloads");
            return d;
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    private static Map<String, Reload> index() {
        var result = new HashMap<String, Reload>(); for (var row : DATA.reloads) result.put(row.id, row); return Map.copyOf(result);
    }
    public static Perk perk() { return DATA.perk; }
    public static List<WeaponPerks.Roll> rolls() { return LegendaryPerks.expandRolls(ID, List.of(DATA.weapons)); }
    public static Reload reload(WeaponCatalog.Entry entry) {
        if (entry != null && LegendaryWeapons.contains(entry.id())
                && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
                && LegendaryPerks.extraRolls(ID).stream().anyMatch(r -> r.id().equals(entry.id()))) {
            var base = WeaponProfile.forEntry(entry);
            int stat = WeaponCharacteristics.of(entry).stats().get("4188031367");
            return new Reload(entry.id(),
                WeaponStatCurves.reloadTicks(entry.id(), base.firstReloadTicks(), perk().reloadBonus(), perk().durationMultiplier()),
                WeaponStatCurves.reloadTicks(entry.id(), base.reloadTicks(), perk().reloadBonus(), perk().durationMultiplier()),
                stat, Math.min(100, stat + perk().reloadBonus()));
        }
        var row = RELOADS.get(entry.id()); if (row == null) throw new IllegalArgumentException("No Outlaw reload " + entry.id()); return row;
    }
}
