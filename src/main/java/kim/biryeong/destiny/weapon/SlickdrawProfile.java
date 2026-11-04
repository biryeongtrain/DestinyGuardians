package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** BASIC DDC row200: Handling100, ready-only .95. Auto Aim Cone Size is source-only.
 * JSON-only initialization; no catalog, characteristics or perk-registry calls at class init. */
public final class SlickdrawProfile {
    public static final String ID = "slickdraw";
    public static final long HASH = 1821614984L;
    private record Perk(String id, long hash, int handlingBonus, double readyScalar,
                        double stowScalar, double adsScalar, String autoAimPolicy) {}
    private record Quadratic(double evpp, double vpp, double offset) {
        double seconds(int stat) { return evpp * stat * stat + vpp * stat + offset; }
    }
    private record Curve(String id, int baseHandlingStat, Quadratic ready, Quadratic stow, Quadratic ads) {}
    private record Data(String stage, Perk perk, List<WeaponPerks.Roll> weapons, Curve curve) {}
    private static final Data DATA = load();
    private SlickdrawProfile() {}
    private static Data load() {
        var in = SlickdrawProfile.class.getResourceAsStream("/destiny/weapons/w226-slickdraw.json");
        if (in == null) throw new IllegalStateException("Missing W226 Slickdraw");
        try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            var expected = new WeaponPerks.Roll("bite_of_the_fox", 1403800851L, 3, HASH, 563442205L);
            var curve = new Curve("bite_of_the_fox", 25,
                new Quadratic(0, -.002623944983, .5079465458),
                new Quadratic(0, -.002083932479, .4392525789),
                new Quadratic(0, -.00194998437, .5021325414));
            if (d == null || !"W226".equals(d.stage) || d.perk == null
                || !ID.equals(d.perk.id) || d.perk.hash != HASH || d.perk.handlingBonus != 100
                || d.perk.readyScalar != .95 || d.perk.stowScalar != 1 || d.perk.adsScalar != 1
                || !"source-only; unsimulated".equals(d.perk.autoAimPolicy)
                || !List.of(expected).equals(d.weapons) || !curve.equals(d.curve))
                throw new IllegalStateException("Invalid W226 BASIC Slickdraw");
            return new Data(d.stage, d.perk, List.copyOf(d.weapons), d.curve);
        } catch (IOException e) { throw new IllegalStateException(e); }
    }
    public static List<WeaponPerks.Roll> rolls() { return DATA.weapons; }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
            && DATA.weapons.stream().anyMatch(r -> r.id().equals(entry.id())
                && r.hash() == WeaponCharacteristics.of(entry).bungieHash())
            && !WeaponCharacteristics.of(entry).exotic();
    }
    private static int ticks(double seconds) { return Math.max(1, (int)Math.ceil(seconds * 20)); }
    private static int handling() { return Math.clamp(DATA.curve.baseHandlingStat + DATA.perk.handlingBonus, 0, 100); }
    /** Raw curve first, ready-only scalar next, one final ceil. Never scales prior rounded ticks. */
    public static int handlingTicks(WeaponCatalog.Entry entry, boolean ready) {
        if (!supports(entry)) throw new IllegalArgumentException("Exact canonical Slickdraw entry required");
        return ticks((ready ? DATA.curve.ready : DATA.curve.stow).seconds(handling())
            * (ready ? DATA.perk.readyScalar : DATA.perk.stowScalar));
    }
    /** Both enter and exit use raw Handling100; Slickdraw has no ADS duration scalar.
     * Snapshot and Firmly Planted occupy Slickdraw's own socket and cannot combine. */
    public static int adsTicks(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("Exact canonical Slickdraw entry required");
        return Math.clamp(ticks(DATA.curve.ads.seconds(handling()) * DATA.perk.adsScalar), 2, 20);
    }
}
