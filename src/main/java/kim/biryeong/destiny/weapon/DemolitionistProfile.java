package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Exact base-trait sockets. Energy is a baseline chunk, not the live D2 ability/stat formula. */
public final class DemolitionistProfile {
    public static final String ID = "demolitionist";
    public static final long HASH = 3523296417L;
    public record Perk(String id, long hash, int energyPercent, int specialEnergyPercent,
                       List<String> specialEnergyFamilies, int reloadCooldownTicks,
                       boolean reloadFromReserves, boolean energyIsBaseChunk, String mechanicsSource) {
        public Perk { specialEnergyFamilies = List.copyOf(specialEnergyFamilies); }
    }
    private record Row(String id, long hash, int socket, long perkHash, long plugSetHash,
                       String proofMode, int baseEnergyPercent) {
        WeaponPerks.Roll roll() { return new WeaponPerks.Roll(id,hash,socket,perkHash,plugSetHash); }
    }
    private record Data(String stage, Perk perk, Row[] weapons) {}
    private static final Data DATA = load();
    private DemolitionistProfile() {}
    private static Data load() {
        var input = DemolitionistProfile.class.getResourceAsStream("/destiny/weapons/w103-demolitionist.json");
        if (input == null) throw new IllegalStateException("Missing W103 Demolitionist profile");
        try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
            var d = new Gson().fromJson(reader, Data.class);
            if (d == null || !"W103".equals(d.stage) || d.perk == null || !ID.equals(d.perk.id)
                    || d.perk.hash != HASH || d.perk.energyPercent != 10 || d.perk.specialEnergyPercent != 20
                    || !d.perk.specialEnergyFamilies.equals(List.of("sniper_rifle","shotgun","glaive","fusion_rifle"))
                    || d.perk.reloadCooldownTicks != 60 || !d.perk.reloadFromReserves || !d.perk.energyIsBaseChunk
                    || !"art/weapons/w103/references/mechanics.json".equals(d.perk.mechanicsSource)
                    || d.weapons == null || d.weapons.length != 11) throw new IllegalStateException("Invalid W103 profile");
            var slots = new HashSet<String>(); int fixed = 0;
            for (var row : d.weapons) {
                var entry = WeaponCatalog.find(row.id).orElseThrow();
                var meta = WeaponCharacteristics.of(entry);
                int percent = d.perk.specialEnergyFamilies.contains(entry.family())
                        ? d.perk.specialEnergyPercent : d.perk.energyPercent;
                if (row.hash != meta.bungieHash() || row.perkHash != HASH || meta.exotic()
                        || row.socket < 0 || row.socket > 63 || row.plugSetHash <= 0
                        || row.baseEnergyPercent != percent || !slots.add(row.id + ":" + row.socket))
                    throw new IllegalStateException("Invalid Demolitionist socket " + row);
                if ("fixedCuratedOption".equals(row.proofMode)) {
                    // Official fake reusable set 253, not an invented randomized pool or initial equipped perk.
                    if (!row.id.equals("salvager_s_salvo") || row.hash != 2060863616L
                            || row.socket != 3 || row.plugSetHash != 253) throw new IllegalStateException("Invalid curated option");
                    fixed++;
                } else if (!"randomized".equals(row.proofMode) || row.id.equals("salvager_s_salvo"))
                    throw new IllegalStateException("Unknown Demolitionist socket proof");
            }
            if (fixed != 1) throw new IllegalStateException("Missing curated Salvo proof");
            return d;
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static Perk perk() { return DATA.perk; }
    public static List<WeaponPerks.Roll> rolls() { return Arrays.stream(DATA.weapons).map(Row::roll).toList(); }
    /** BASE percentage; zero for exact weapons without a verified base-trait socket. */
    public static int energyPercent(WeaponCatalog.Entry entry) {
        return Arrays.stream(DATA.weapons).filter(r -> r.id.equals(entry.id())).findFirst().map(Row::baseEnergyPercent).orElse(0);
    }
}
