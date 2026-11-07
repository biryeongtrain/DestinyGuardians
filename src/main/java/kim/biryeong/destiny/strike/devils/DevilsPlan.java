package kim.biryeong.destiny.strike.devils;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Fixed three-Guardian porting values from docs/design/strikes/devils-lair-3p, not extracted D2 stats. */
public final class DevilsPlan {
    public static final int MIN_PLAYERS = 1, PLAYERS = 3, PACK_SIZE = 8, SPAWNS_PER_TICK = 2;
    public static final int TELEGRAPH_TICKS = 40, FLYING_TELEGRAPH_TICKS = 24;
    public static final int REINFORCEMENT_GAP = 120, INTERMISSION_TICKS = 160;
    public static final int SEPIKS_RESERVED_SERVITORS = 3;

    public enum Zone {
        RY(24, 3), RF(24, 3), BL(32, 4), SP(24, 3);
        private final int actorCap, packCap;
        Zone(int actorCap, int packCap) { this.actorCap = actorCap; this.packCap = packCap; }
        public int actorCap() { return actorCap; }
        public int packCap() { return packCap; }
    }

    public enum Kind {
        DREG(11, 0), VANDAL(34, 0), SHANK(10, 0), MARAUDER(28, 0), CAPTAIN(80, 24),
        THRALL(11, 0), ACOLYTE(11, 0), KNIGHT(90, 0), WIZARD(64, 24),
        SERVITOR(60, 0), BRIG(700, 0), WALKER(DevilsWalkerState.MAX_CORE, 0), SEPIKS(550, 0);
        private final double health, shield;
        Kind(double health, double shield) { this.health = health; this.shield = shield; }
        public double health() { return health; }
        public double shield() { return shield; }
        public boolean boss() { return this == BRIG || this == WALKER || this == SEPIKS; }
    }

    public record Slot(String id, Zone zone, String packId, Kind kind, String anchor, int index) {
        public Slot {
            Objects.requireNonNull(id); Objects.requireNonNull(zone); Objects.requireNonNull(kind);
            Objects.requireNonNull(anchor);
            if (id.isBlank() || anchor.isBlank() || index < 0) throw new IllegalArgumentException("Invalid slot");
        }
        public boolean ordinary() { return packId != null; }
    }

    public record Pack(String id, Zone zone, String phase, String template, String anchor, List<Kind> members) {
        public Pack {
            Objects.requireNonNull(id); Objects.requireNonNull(zone); Objects.requireNonNull(phase);
            Objects.requireNonNull(template); Objects.requireNonNull(anchor);
            members = List.copyOf(members);
            if (members.size() != PACK_SIZE) throw new IllegalArgumentException("A planned pack has eight actors");
        }
        public List<Slot> slots() {
            var result = new ArrayList<Slot>();
            for (int i = 0; i < members.size(); i++) result.add(new Slot(id + "/" + i, zone, id, members.get(i), anchor, i));
            return List.copyOf(result);
        }
    }

    private static List<Kind> roster(Object... values) {
        var result = new ArrayList<Kind>();
        for (int i = 0; i < values.length; i += 2)
            for (int n = 0; n < (int) values[i + 1]; n++) result.add((Kind) values[i]);
        return List.copyOf(result);
    }

    public static List<Kind> template(String name) {
        return switch (name) {
            case "F1" -> roster(Kind.DREG, 4, Kind.VANDAL, 2, Kind.SHANK, 2);
            case "F2" -> roster(Kind.DREG, 3, Kind.VANDAL, 2, Kind.MARAUDER, 2, Kind.CAPTAIN, 1);
            case "F3" -> roster(Kind.DREG, 4, Kind.VANDAL, 3, Kind.CAPTAIN, 1);
            case "F4" -> roster(Kind.DREG, 2, Kind.VANDAL, 2, Kind.SHANK, 4);
            case "H1" -> roster(Kind.THRALL, 4, Kind.ACOLYTE, 3, Kind.KNIGHT, 1);
            case "H2" -> roster(Kind.THRALL, 3, Kind.ACOLYTE, 3, Kind.WIZARD, 1, Kind.KNIGHT, 1);
            case "H3" -> roster(Kind.THRALL, 4, Kind.ACOLYTE, 2, Kind.KNIGHT, 1, Kind.WIZARD, 1);
            case "S1" -> roster(Kind.DREG, 3, Kind.VANDAL, 3, Kind.MARAUDER, 2);
            default -> throw new IllegalArgumentException("Unknown pack " + name);
        };
    }

    private static Pack pack(String id, Zone zone, String phase, String template, String anchor) {
        return new Pack(id, zone, phase, template, anchor, template(template));
    }

    private static final List<Pack> PACKS = List.of(
            pack("RY-approach-1", Zone.RY, "approach", "F1", "RY.C1"),
            pack("RY-approach-2", Zone.RY, "approach", "F3", "RY.R"),
            pack("RY-approach-3", Zone.RY, "approach", "F1", "RY.L"),
            pack("RF-entry-1", Zone.RF, "entry", "F1", "RF.A"),
            pack("RF-entry-2", Zone.RF, "entry", "H1", "RF.B"),
            pack("RF-entry-3", Zone.RF, "entry", "F2", "RF.D"),
            pack("RF-defense1-1", Zone.RF, "defense1", "F1", "RF.A"),
            pack("RF-defense1-2", Zone.RF, "defense1", "F3", "RF.C"),
            pack("RF-defense1-3", Zone.RF, "defense1", "H1", "RF.B"),
            pack("RF-defense2-1", Zone.RF, "defense2", "H1", "RF.B"),
            pack("RF-defense2-2", Zone.RF, "defense2", "F2", "RF.D"),
            pack("RF-defense2-3", Zone.RF, "defense2", "H2", "RF.B"),
            pack("RF-defense2-4", Zone.RF, "defense2", "F4", "RF.A"),
            pack("RF-defense3-1", Zone.RF, "defense3", "F3", "RF.C"),
            pack("RF-defense3-2", Zone.RF, "defense3", "H3", "RF.B"),
            pack("RF-defense3-3", Zone.RF, "defense3", "F2", "RF.A"),
            pack("RF-defense3-4", Zone.RF, "defense3", "H2", "RF.D"),
            pack("BL-entry-1", Zone.BL, "entry", "F3", "BL.R"),
            pack("BL-entry-2", Zone.BL, "entry", "F2", "BL.L"),
            pack("BL-entry-3", Zone.BL, "entry", "F1", "BL.H"),
            pack("BL-reinforce-1", Zone.BL, "reinforce", "F4", "BL.EXIT"),
            pack("BL-reinforce-2", Zone.BL, "reinforce", "F2", "BL.L"),
            pack("BL-reinforce-3", Zone.BL, "reinforce", "F1", "BL.R"),
            pack("BL-reinforce-4", Zone.BL, "reinforce", "F4", "BL.H"),
            pack("SP-guard-1", Zone.SP, "guard", "F3", "SP.D1"),
            pack("SP-guard-2", Zone.SP, "guard", "S1", "SP.D2"),
            pack("SP-damage-1", Zone.SP, "damage", "F1", "SP.D1"),
            pack("SP-damage-2", Zone.SP, "damage", "F2", "SP.D2"),
            pack("SP-damage-3", Zone.SP, "damage", "F4", "SP.D1"),
            pack("SP-shield-1", Zone.SP, "shield", "S1", "SP.D2"),
            pack("SP-shield-2", Zone.SP, "shield", "F2", "SP.D1"));

    public static List<Pack> packs() { return PACKS; }
    public static List<Pack> packs(Zone zone, String phase) {
        return PACKS.stream().filter(p -> p.zone() == zone && p.phase().equals(phase)).toList();
    }
    public static Pack pack(String id) {
        return PACKS.stream().filter(p -> p.id().equals(id)).findFirst().orElseThrow(() -> new IllegalArgumentException(id));
    }
    public static Slot walker() { return new Slot("BL-walker", Zone.BL, null, Kind.WALKER, "BL.W", 0); }
    public static Slot brig(int index) {
        if (index < 1 || index > 2) throw new IllegalArgumentException("Brig index");
        return new Slot("BL-brig-" + index, Zone.BL, null, Kind.BRIG, "BL.B" + index, index - 1);
    }
    public static Slot sepiks() { return new Slot("SP-sepiks", Zone.SP, null, Kind.SEPIKS, "SP.C", 0); }
    public static Slot servitor(int shield, int index) {
        if (shield < 1 || shield > 2 || index < 1 || index > 3) throw new IllegalArgumentException("Servitor index");
        return new Slot("SP-servitor-" + shield + "-" + index, Zone.SP, null, Kind.SERVITOR, "SP.S" + index, index - 1);
    }
    public static List<Slot> specials() {
        var slots = new ArrayList<Slot>(List.of(walker(), brig(1), brig(2), sepiks()));
        for (int s = 1; s <= 2; s++) for (int i = 1; i <= 3; i++) slots.add(servitor(s, i));
        return List.copyOf(slots);
    }
    private DevilsPlan() { }
}
