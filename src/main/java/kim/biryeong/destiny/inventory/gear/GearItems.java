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
 * Read-only projections of the player's real weapon stacks for the gear screen. Storage is a persistent player
 * attachment; equipped slots remain in inventory. Perks travel with each canonical stack. Nothing here mutates.
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

    /** {@code base} is the value before barrel/magazine plugs, or null when the plugs leave it unchanged. */
    public record Stat(String name, int value, boolean bar, Integer base) {
        public Stat(String name, int value, boolean bar) { this(name, value, bar, null); }
    }
    /** One stat change of a barrel/magazine plug, e.g. 사거리 +15. */
    public record Delta(String stat, int value) { }
    /** {@code slot} is 총열/탄창 for a barrel/magazine plug (with its {@code deltas}), empty for a trait. */
    public record Perk(String id, long hash, String name, String description, String slot, List<Delta> deltas) {
        public Perk(String id, long hash, String name, String description) { this(id, hash, name, description, "", List.of()); }
    }

    /** One owned weapon; {@code inventoryIndex}/{@code stack} are the click token for equipping. */
    public record Weapon(int inventoryIndex, ItemStack stack, WeaponCatalog.Entry entry, boolean equipped,
                         String name, String family, String frame, String damage, String ammo, boolean exotic,
                         String flavour, List<Stat> stats, List<Perk> perks, int rounds, int magazine,
                         WeaponRarity rarity) {
        public String id() { return entry.id(); }
        /** Icon/model key: the W325/W302 skin id when the stack wears one, else the catalog id. */
        public String iconId() { return WeaponSkins.of(stack).map(WeaponSkins.Skin::id).orElse(entry.id()); }
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
        var skin = WeaponSkins.of(stack);
        String name = skin.map(WeaponSkins.Skin::display).orElse(WeaponScreenText.weapon(entry.id(), entry.name()));
        String flavour = skin.filter(k -> k.bungieHash() > 0).map(k -> GearSamples.flavour(k.bungieHash()))
                .filter(f -> !f.isBlank()).orElse(skin.isPresent() ? "" : GearSamples.flavour(c.bungieHash()));
        return new Weapon(index, stack, entry, equipped, name,
                WeaponScreenText.family(entry.family()), WeaponScreenText.frame(entry.source_frame_label()),
                c.damage().name(), c.ammo().name(), c.exotic(), flavour,
                stats(withComponents(c.stats(), stack), baseStats(c.stats(), entry)), perks(stack), ammo.rounds(), ammo.loadedLimit(), WeaponRarity.of(stack));
    }

    /** Stats the weapon actually has, in tooltip order. Bars skip zero values; numbers keep them only if set. Pure. */
    public static List<Stat> stats(Map<String, Integer> raw) { return stats(raw, raw); }
    /** As {@link #stats(Map)}, recording the pre-plug value of every stat the plugs changed. */
    public static List<Stat> stats(Map<String, Integer> raw, Map<String, Integer> base) {
        var out = new ArrayList<Stat>();
        for (var def : STATS) {
            Integer v = raw.get(def.hash());
            if (v == null || (v <= 0 && !def.hash().equals("2715839340"))) continue;
            Integer b = base.get(def.hash());
            out.add(new Stat(def.name(), v, def.bar(), b == null || b.equals(v) ? null : b));
        }
        return out;
    }
    /** Characteristics without plugs; magazine as the frame's plain round count, like {@link #withComponents}. */
    private static Map<String, Integer> baseStats(Map<String, Integer> raw, WeaponCatalog.Entry entry) {
        if (!raw.containsKey("3871231066")) return raw;
        var out = new java.util.LinkedHashMap<>(raw);
        out.put("3871231066", WeaponProfile.forEntry(entry).magazine());
        return out;
    }

    /** Manifest stat hash ↔ W326 component stat key. */
    private static final Map<String, String> COMPONENT_STATS = Map.of("1240592695", "range", "155624089", "stability",
            "943549884", "handling", "4188031367", "reload", "2715839340", "recoilDirection",
            "1345609583", "aimAssist", "2714457168", "airborne", "4043523819", "impact", "925767036", "ammoCapacity");
    /** Base characteristics plus this stack's barrel/magazine plugs (Destiny shows the rolled total), clamped 0..100. */
    public static Map<String, Integer> withComponents(Map<String, Integer> raw, ItemStack stack) {
        var parts = kim.biryeong.destiny.weapon.WeaponComponents.of(stack);
        if (parts.isEmpty()) return raw;
        var out = new java.util.LinkedHashMap<>(raw);
        for (var e : COMPONENT_STATS.entrySet()) {
            int bonus = 0;
            for (var c : parts) bonus += c.stat(e.getValue());
            if (bonus == 0 || !out.containsKey(e.getKey())) continue;
            int v = out.get(e.getKey()) + bonus;
            out.put(e.getKey(), Math.clamp(v, 0, 100));
        }
        // Magazine is shown as rounds: the stack's component-sized capacity.
        var entry = WeaponItems.entry(stack);
        if (entry.isPresent() && out.containsKey("3871231066"))
            out.put("3871231066", WeaponComponents.profile(stack, WeaponProfile.forEntry(entry.get())).magazine());
        return out;
    }

    /** Barrel and magazine plugs first, then the traits rolled on this exact stack (bound to the weapon), in socket order. */
    public static List<Perk> perks(ItemStack stack) {
        record Found(int socket, String id, long hash) { }
        var found = new ArrayList<Found>();
        for (String id : WeaponPerks.ids())
            WeaponPerks.selected(stack, id).ifPresent(r -> found.add(new Found(r.socket(), id, r.perkHash())));
        found.sort(java.util.Comparator.comparingInt(Found::socket));
        var out = new ArrayList<Perk>();
        for (var c : kim.biryeong.destiny.weapon.WeaponComponents.of(stack))
            out.add(new Perk(c.id(), c.hash(), c.nameKo() == null || c.nameKo().isBlank() ? c.name() : c.nameKo(),
                    c.descriptionKo() == null ? "" : c.descriptionKo(), "barrel".equals(c.slot()) ? "총열" : "탄창", deltas(c)));
        found.stream().map(f -> new Perk(f.id(), f.hash(), label(f.id()), WeaponPerkLabels.description(f.id()))).forEach(out::add);
        return out;
    }

    private static final Map<String, String> STAT_KO = Map.of("range", "사거리", "stability", "안정성", "handling", "조작성",
            "reload", "재장전 속도", "magazine", "탄창", "recoilDirection", "반동 방향", "aimAssist", "조준 지원",
            "airborne", "공중 효율", "impact", "충격", "blastRadius", "폭발 반경");
    private static List<Delta> deltas(kim.biryeong.destiny.weapon.WeaponComponents.Component c) {
        var out = new ArrayList<Delta>();
        if (c.stats() != null) for (var e : c.stats().entrySet())
            if (e.getValue() != 0) out.add(new Delta(STAT_KO.getOrDefault(e.getKey(), e.getKey()), e.getValue()));
        return out;
    }

    private static String label(String id) {
        String ko = WeaponPerkLabels.name(id);
        return ko.equals(id) ? WeaponPerks.name(id) : ko;
    }
}
