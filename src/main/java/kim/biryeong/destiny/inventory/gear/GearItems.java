package kim.biryeong.destiny.inventory.gear;

import kim.biryeong.destiny.inventory.WeaponEquipmentService;
import kim.biryeong.destiny.inventory.WeaponPerkLabels;
import kim.biryeong.destiny.inventory.WeaponScreenText;
import kim.biryeong.destiny.weapon.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Read-only projections of the player's real weapon stacks for the gear screen. Storage is the player's own
 * inventory (slots 3..35); perks live on each stack, so they travel with the weapon. Nothing here mutates.
 */
public final class GearItems {
    /** Stat display order of the Destiny tooltip; {@code bar=false} values are numbers only. */
    public record StatDef(String hash, String name, boolean bar) { }
    public static final List<StatDef> STATS = List.of(
            new StatDef("4284893193", "분당 발사 수", false), new StatDef("2961396640", "충전 시간", false),
            new StatDef("447667954", "당기기 시간", false), new StatDef("2837207746", "휘두르기 속도", true),
            new StatDef("4043523819", "충격", true), new StatDef("3614673599", "폭발 반경", true),
            new StatDef("2523465841", "속도", true), new StatDef("1240592695", "사거리", true),
            new StatDef("1591432999", "정확도", true), new StatDef("155624089", "안정성", true),
            new StatDef("943549884", "조작성", true), new StatDef("4188031367", "재장전 속도", true),
            new StatDef("3022301683", "충전 속도", true), new StatDef("2762071195", "방어 효율", true),
            new StatDef("209426660", "방어 저항", true), new StatDef("1842278586", "보호막 지속 시간", true),
            new StatDef("925767036", "탄약 용량", true), new StatDef("3871231066", "탄창", false),
            new StatDef("1345609583", "조준 지원", true), new StatDef("3555269338", "확대/축소", true),
            new StatDef("2715839340", "반동 방향", false), new StatDef("2714457168", "공중 효율", true),
            new StatDef("1931675084", "탄약 생성", true));

    public record Stat(String name, int value, boolean bar) { }
    public record Perk(String id, String name, String description) { }

    /** One owned weapon; {@code inventoryIndex}/{@code stack} are the click token for equipping. */
    public record Weapon(int inventoryIndex, ItemStack stack, WeaponCatalog.Entry entry, boolean equipped,
                         String name, String family, String frame, String damage, String ammo, boolean exotic,
                         String flavour, List<Stat> stats, List<Perk> perks, int rounds, int magazine) {
        public String id() { return entry.id(); }
        public Map<String, Integer> statMap() {
            var out = new java.util.LinkedHashMap<String, Integer>();
            for (var s : stats) out.put(s.name(), s.value());
            return out;
        }
    }

    public record Bucket(Weapon equipped, List<Weapon> stored) {
        public Bucket { stored = List.copyOf(stored); }
    }

    private GearItems() { }

    public static Bucket bucket(ServerPlayer p, WeaponSlot slot) {
        Weapon equipped = null;
        var stored = new ArrayList<Weapon>();
        for (var owned : WeaponEquipmentService.owned(p, slot)) {
            var w = weapon(owned.inventoryIndex(), owned.stack(), owned.weapon(), owned.equipped());
            if (owned.equipped()) equipped = w; else if (owned.inventoryIndex() >= 3) stored.add(w);
        }
        return new Bucket(equipped, stored);
    }

    public static Weapon weapon(int index, ItemStack stack, WeaponCatalog.Entry entry, boolean equipped) {
        var c = WeaponCharacteristics.of(entry);
        var profile = WeaponProfile.forEntry(entry);
        var ammo = WeaponItems.magazine(stack, profile);
        return new Weapon(index, stack, entry, equipped, WeaponScreenText.weapon(entry.id(), entry.name()),
                WeaponScreenText.family(entry.family()), WeaponScreenText.frame(entry.source_frame_label()),
                c.damage().name(), c.ammo().name(), c.exotic(), GearSamples.flavour(c.bungieHash()),
                stats(c.stats()), perks(stack), ammo.rounds(), ammo.loadedLimit());
    }

    /** Stats the weapon actually has, in tooltip order. Bars skip zero values; numbers keep them only if set. Pure. */
    public static List<Stat> stats(Map<String, Integer> raw) {
        var out = new ArrayList<Stat>();
        for (var def : STATS) {
            Integer v = raw.get(def.hash());
            if (v == null || (v <= 0 && !def.hash().equals("2715839340"))) continue;
            out.add(new Stat(def.name(), v, def.bar()));
        }
        return out;
    }

    /** The traits rolled on this exact stack (bound to the weapon), in socket order. */
    public static List<Perk> perks(ItemStack stack) {
        record Found(int socket, String id) { }
        var found = new ArrayList<Found>();
        for (String id : WeaponPerks.ids())
            WeaponPerks.selected(stack, id).ifPresent(r -> found.add(new Found(r.socket(), id)));
        found.sort(java.util.Comparator.comparingInt(Found::socket));
        return found.stream().map(f -> new Perk(f.id(), label(f.id()), WeaponPerkLabels.description(f.id()))).toList();
    }

    private static String label(String id) {
        String ko = WeaponPerkLabels.name(id);
        return ko.equals(id) ? WeaponPerks.name(id) : ko;
    }
}
