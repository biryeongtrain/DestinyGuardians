package kim.biryeong.destiny.weapon;

import net.minecraft.world.item.ItemStack;

import java.util.Locale;
import java.util.Optional;

/**
 * W325 Destiny item tiers. Catalog weapons are legendary or exotic; Red War white/green/blue weapons are
 * {@link WeaponSkins} over a catalog weapon with the same frame, so a stack's tier is its skin's tier when it has one.
 * A lower tier keeps the base frame's handling but rolls fewer trait columns ({@link #traitColumns()}).
 */
public enum WeaponRarity {
    // W326: green = barrel + magazine, blue = barrel + magazine + one trait (random, a local loot-shooter choice).
    COMMON("일반", 0xC7CBCF, 0x6E6A66, 0, 0),
    UNCOMMON("고급", 0x5FB872, 0x366F42, 0, 2),
    RARE("희귀", 0x6F9FDB, 0x5076A3, 1, 2),
    LEGENDARY("전설", 0xB57BE0, 0x522F65, Integer.MAX_VALUE, 2),
    EXOTIC("경이", 0xCEAE33, 0xCEAE33, Integer.MAX_VALUE, 0);

    private final String label;
    private final int color, band, traitColumns, componentColumns;

    WeaponRarity(String label, int color, int band, int traitColumns, int componentColumns) {
        this.label = label; this.color = color; this.band = band; this.traitColumns = traitColumns;
        this.componentColumns = componentColumns;
    }

    /** Korean tier name (일반 / 고급 / 희귀 / 전설 / 경이). */
    public String label() { return label; }
    /** Bright tier colour: text, glow, beams. */
    public int color() { return color; }
    /** Destiny tooltip/tile band colour. */
    public int band() { return band; }
    /** Trait columns a fresh roll fills (socket order). */
    public int traitColumns() { return traitColumns; }
    /** Barrel/magazine component columns a fresh roll fills ({@link WeaponComponents}). */
    public int componentColumns() { return componentColumns; }
    public String id() { return name().toLowerCase(Locale.ROOT); }

    public static Optional<WeaponRarity> parse(String value) {
        if (value == null) return Optional.empty();
        try { return Optional.of(valueOf(value.toUpperCase(Locale.ROOT))); }
        catch (IllegalArgumentException e) { return Optional.empty(); }
    }

    public static WeaponRarity of(WeaponCatalog.Entry entry) {
        return WeaponCharacteristics.of(entry).exotic() ? EXOTIC : LEGENDARY;
    }

    /** A combat/preview weapon stack's tier; non-weapons are legendary. */
    public static WeaponRarity of(ItemStack stack) {
        var skin = WeaponSkins.of(stack);
        if (skin.isPresent() && skin.get().rarity() != null) return skin.get().rarity();
        return WeaponModels.entry(stack).map(WeaponRarity::of).orElse(LEGENDARY);
    }
}
