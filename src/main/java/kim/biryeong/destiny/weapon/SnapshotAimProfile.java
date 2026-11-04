package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import net.minecraft.world.item.ItemStack;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base Snapshot sockets and pre-quantization ADS timing. See W68 source-tier policy.
 * W320: the two official Heavy rolls (Bad Omens, Edge Transit) come from w320-snapshot-heavy.json with
 * a LOCAL heavyScalar 0.8 (DDC row205 "Special and Power?"); the frozen W68 resource is unchanged. */
public final class SnapshotAimProfile {
    public static final String ID = "snapshot_sights";
    public static final long HASH = 957782887L;
    public record Timing(String id, int baseTicks, int snapshotTicks, int ammoType, double adsSeconds) {}
    private record Data(int schemaVersion, long perkHash, double primaryScalar, double specialScalar,
                        List<WeaponPerks.Roll> rolls, List<Timing> timings) {}
    private record Heavy(String stage, long perkHash, double heavyScalar, String policy,
                         List<WeaponPerks.Roll> rolls, List<Timing> timings) {}
    private static final Data DATA = load();
    private static final Heavy HEAVY = loadHeavy();
    private static final List<WeaponPerks.Roll> ROLLS = merged();
    private static final Map<String, Timing> TIMINGS = index();
    private SnapshotAimProfile() {}
    private static Data load() {
        var input = SnapshotAimProfile.class.getResourceAsStream("/destiny/weapons/w68-snapshot.json");
        if (input == null) throw new IllegalStateException("Missing W68 Snapshot data");
        try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            if (d == null || d.schemaVersion != 1 || d.perkHash != HASH
                    || d.primaryScalar != .5 || d.specialScalar != .8
                    || d.rolls == null || d.rolls.isEmpty() || d.timings == null)
                throw new IllegalStateException("Invalid W68 Snapshot profile");
            var seen = new HashSet<String>();
            for (var r : d.rolls) {
                var e = WeaponCatalog.find(r.id()).orElseThrow();
                var c = WeaponCharacteristics.of(e);
                if (c.exotic() || c.bungieHash() != r.hash() || r.perkHash() != HASH
                        || r.socket() < 0 || r.socket() > 63 || r.plugSetHash() <= 0
                        || c.ammo() == WeaponAmmoType.HEAVY || !WeaponAimProfile.supports(e)
                        || !seen.add(r.id() + ":" + r.socket()))
                    throw new IllegalStateException("Invalid W68 Snapshot socket " + r);
            }
            return new Data(d.schemaVersion, d.perkHash, d.primaryScalar, d.specialScalar,
                    List.copyOf(d.rolls), List.copyOf(d.timings));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    private static Heavy loadHeavy() {
        var input = SnapshotAimProfile.class.getResourceAsStream("/destiny/weapons/w320-snapshot-heavy.json");
        if (input == null) throw new IllegalStateException("Missing W320 heavy Snapshot data");
        try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
            var h = new Gson().fromJson(reader, Heavy.class);
            if (h == null || !"W320".equals(h.stage) || h.perkHash != HASH || h.heavyScalar != .8
                    || h.policy == null || !h.policy.startsWith("LOCAL_POLICY_W320")
                    || h.rolls == null || h.rolls.size() != 2 || h.timings == null || h.timings.size() != 2)
                throw new IllegalStateException("Invalid W320 heavy Snapshot profile");
            for (var r : h.rolls) {
                var e = WeaponCatalog.find(r.id()).orElseThrow();
                var c = WeaponCharacteristics.of(e);
                if (c.exotic() || c.bungieHash() != r.hash() || r.perkHash() != HASH || r.socket() < 0 || r.socket() > 63
                        || r.plugSetHash() <= 0 || c.ammo() != WeaponAmmoType.HEAVY || !WeaponAimProfile.supports(e)
                        || DATA.rolls.stream().anyMatch(o -> o.id().equals(r.id())))
                    throw new IllegalStateException("Invalid W320 heavy Snapshot socket " + r);
            }
            for (var t : h.timings) {
                var e = WeaponCatalog.find(t.id).orElseThrow();
                if (t.ammoType != 3 || WeaponCharacteristics.of(e).ammo() != WeaponAmmoType.HEAVY
                        || h.rolls.stream().noneMatch(r -> r.id().equals(t.id))
                        || t.baseTicks != WeaponAimProfile.of(e).transitionTicks()
                        || DATA.timings.stream().noneMatch(o -> o.id.equals(t.id) && o.adsSeconds == t.adsSeconds)
                        || t.snapshotTicks != Math.clamp((int)Math.ceil(t.adsSeconds * h.heavyScalar * 20), 1, 20))
                    throw new IllegalStateException("Invalid W320 heavy Snapshot timing " + t);
            }
            return new Heavy(h.stage, h.perkHash, h.heavyScalar, h.policy, List.copyOf(h.rolls), List.copyOf(h.timings));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    private static List<WeaponPerks.Roll> merged() {
        var all = new ArrayList<>(DATA.rolls);
        all.addAll(HEAVY.rolls);
        return List.copyOf(all);
    }
    private static Map<String, Timing> index() {
        Map<String, Timing> result = new HashMap<>();
        for (var t : DATA.timings) {
            var e = WeaponCatalog.find(t.id).orElseThrow();
            var ammo = WeaponCharacteristics.of(e).ammo();
            int type = ammo == WeaponAmmoType.PRIMARY ? 1 : ammo == WeaponAmmoType.SPECIAL ? 2 : 3;
            double scalar = type == 1 ? DATA.primaryScalar : type == 2 ? DATA.specialScalar : 1;
            int expected = Math.clamp((int)Math.ceil(t.adsSeconds * scalar * 20), 1, 20);
            if (!WeaponAimProfile.supports(e) || !Double.isFinite(t.adsSeconds) || t.adsSeconds <= 0
                    || t.ammoType != type || t.baseTicks != WeaponAimProfile.of(e).transitionTicks()
                    || t.snapshotTicks != expected || result.putIfAbsent(t.id, t) != null)
                throw new IllegalStateException("Invalid W68 ADS timing " + t);
        }
        // This frozen perk table covers legendary ADS timings. Exotics cannot select Snapshot;
        // their native base ADS still comes from WeaponAimProfile in enterTicks().
        var supported = WeaponCatalog.all().stream().filter(e -> !WeaponCharacteristics.of(e).exotic())
                .filter(WeaponAimProfile::supports)
                .map(WeaponCatalog.Entry::id).collect(java.util.stream.Collectors.toSet());
        if (!result.keySet().equals(supported)) throw new IllegalStateException("Incomplete W68 ADS timing");
        for (var t : HEAVY.timings) result.put(t.id, t); // W320 local Heavy scalar for the official Heavy rolls
        return Map.copyOf(result);
    }
    public static List<WeaponPerks.Roll> rolls() { return ROLLS; }
    public static Timing timing(WeaponCatalog.Entry e) { return Objects.requireNonNull(TIMINGS.get(e.id())); }
    /** Read-only selection: no progress/cooldown/ammunition/FOV side effects. */
    public static int enterTicks(ItemStack stack) {
        var e = WeaponItems.entry(stack).orElseThrow();
        int base = WeaponAimProfile.of(e).transitionTicks();
        return WeaponPerks.selected(stack, ID).isPresent() ? timing(e).snapshotTicks : base;
    }
}
