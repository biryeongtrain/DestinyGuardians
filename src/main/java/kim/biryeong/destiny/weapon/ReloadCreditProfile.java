package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Explicit historical ammo-credit fractions, not guessed defaults or modern exact timings.
 * The effective full phase is captured first (including Outlaw); this pure query
 * only separates its paid transfer from its unchanged ready/recovery deadline.
 */
public final class ReloadCreditProfile {
    public record Credit(String id, long hash, String family, double fraction) {}
    private record Data(String stage, Credit[] weapons) {}
    private static final Map<String,Credit> CREDITS = load();
    private ReloadCreditProfile() {}
    private static Map<String,Credit> load() {
        var stream=ReloadCreditProfile.class.getResourceAsStream("/destiny/weapons/w65-reload-credit.json");
        if(stream==null)throw new IllegalStateException("Missing W65 reload credit profile");
        try(var reader=new InputStreamReader(stream,StandardCharsets.UTF_8)) {
            var d=new Gson().fromJson(reader,Data.class);
            if(d==null || !"W65".equals(d.stage) || d.weapons==null || d.weapons.length==0)
                throw new IllegalStateException("Invalid W65 reload credit profile");
            var result=new HashMap<String,Credit>();
            for(var credit:WeaponExotics.append(d.weapons, "reloadCredit", Credit.class)) {
                var e=WeaponCatalog.find(credit.id).orElseThrow();
                if(!e.family().equals(credit.family) || WeaponCharacteristics.of(e).bungieHash()!=credit.hash
                        || !Double.isFinite(credit.fraction) || credit.fraction<=0 || credit.fraction>=1
                        || result.put(credit.id,credit)!=null)
                    throw new IllegalStateException("Invalid reload credit "+credit);
            }
            return Map.copyOf(result);
        } catch(java.io.IOException e) {throw new IllegalStateException(e);}
    }
    public static Optional<Credit> find(WeaponCatalog.Entry entry) {
        if(entry==null || WeaponCatalog.find(entry.id()).filter(entry::equals).isEmpty())return Optional.empty();
        return Optional.ofNullable(CREDITS.get(entry.id()));
    }
    public static int ammoTicks(WeaponCatalog.Entry entry,WeaponReloadPolicy.Plan plan) {
        Objects.requireNonNull(plan,"reload plan");
        if(plan.incremental())return plan.firstTicks();
        return find(entry).map(c->Math.max(1,Math.min(plan.firstTicks(),
                (int)Math.ceil(plan.firstTicks()*c.fraction)))).orElse(plan.firstTicks());
    }
}
