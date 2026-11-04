package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact selected-item metadata from pinned official definitions, independent of approximate combat tuning. */
public final class WeaponCharacteristics {
    public enum Damage {
        KINETIC(0xDFE4EA), ARC(0x7AD8F5), SOLAR(0xF79254), VOID(0xB192E8),
        STASIS(0x688DCB), STRAND(0x6DCB87);
        private final int color;
        Damage(int color) { this.color=color; }
        public int color() { return color; }
    }
    public record Entry(String id, long bungieHash, WeaponSlot slot, WeaponAmmoType ammo, Damage damage,
                        boolean exotic, Map<String,Integer> stats) {
        public Entry { stats=Map.copyOf(stats); }
    }
    private static final Map<String,Entry> ALL=load();
    private WeaponCharacteristics() {}
    private static Map<String,Entry> load() {
        var stream=WeaponCharacteristics.class.getResourceAsStream("/destiny/weapons/w40-characteristics.json");
        if(stream==null)throw new IllegalStateException("Missing W40 characteristics");
        try(var reader=new InputStreamReader(stream,StandardCharsets.UTF_8)) {
            Map<String,Entry> result=new LinkedHashMap<>();
            for(var e:WeaponExotics.append(new Gson().fromJson(reader,Entry[].class), "characteristics", Entry.class)) {
                if(e.slot()==null||e.ammo()==null||e.damage()==null||e.bungieHash()<=0
                        || (e.slot()==WeaponSlot.POWER)!=(e.ammo()==WeaponAmmoType.HEAVY)
                        || result.putIfAbsent(e.id(),e)!=null)throw new IllegalStateException("Invalid characteristics "+e);
            }
            if(!result.keySet().equals(WeaponCatalog.all().stream().map(WeaponCatalog.Entry::id)
                    .collect(java.util.stream.Collectors.toSet())))throw new IllegalStateException("Incomplete W40 catalog");
            return Map.copyOf(result);
        } catch(java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static Entry of(WeaponCatalog.Entry entry) { return Objects.requireNonNull(ALL.get(entry.id())); }
}
