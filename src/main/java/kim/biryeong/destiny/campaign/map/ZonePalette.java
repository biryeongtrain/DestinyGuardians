package kim.biryeong.destiny.campaign.map;

import java.util.Set;
import java.util.regex.Pattern;

/**
 * Curated vanilla block vocabulary for the Guardian Rises zones (mirrors PALETTE_DEF in
 * scripts/campaign/rising_maps.py). Every palette entry of a bundled {@code .zone} file must be a plain
 * {@code minecraft:} block state from this set; anything else (block entities, command blocks, fluids,
 * gravity or random-tick blocks) is rejected at load time.
 *
 * <p>Families (Lab nearest-colour classification of the source base-colour textures):
 * snow/ground/rock for terrain, concrete/metal/dark for the Cosmodrome structures, rust/paint for
 * oxidised steel and hazard paint, teal for the weathered-copper accents. Slabs, walls, bars and chains
 * are geometry shapes produced from sub-voxel occupancy; copper bulbs are the switchable light
 * fixtures referenced by {@code light.*} markers; barriers fence the playable core.
 */
public final class ZonePalette {
    private ZonePalette() {}

    public static final Set<String> FULL_BLOCKS = Set.of(
            "snow_block", "calcite", "polished_diorite", "smooth_stone", "andesite", "polished_andesite", "stone",
            "stone_bricks", "tuff", "polished_tuff", "cobbled_deepslate", "polished_deepslate", "deepslate_tiles",
            "polished_blackstone", "netherite_block", "smooth_basalt", "iron_block",
            "waxed_exposed_cut_copper", "waxed_weathered_cut_copper", "waxed_oxidized_cut_copper", "waxed_cut_copper",
            "terracotta", "granite", "brown_terracotta", "orange_terracotta", "red_terracotta", "yellow_terracotta",
            "light_gray_terracotta", "cyan_terracotta", "gray_terracotta", "packed_mud", "mud_bricks", "coarse_dirt",
            "rooted_dirt", "dirt", "moss_block", "soul_soil", "podzol", "prismarine", "dark_prismarine", "orange_concrete", "yellow_concrete",
            "white_concrete");

    public static final Set<String> SHAPES = Set.of(
            // slabs (half-height floors/ramps)
            "polished_diorite_slab", "smooth_stone_slab", "andesite_slab", "polished_andesite_slab", "stone_slab",
            "stone_brick_slab", "tuff_slab", "polished_tuff_slab", "cobbled_deepslate_slab", "polished_deepslate_slab",
            "deepslate_tile_slab", "polished_blackstone_slab", "waxed_exposed_cut_copper_slab",
            "waxed_weathered_cut_copper_slab", "waxed_oxidized_cut_copper_slab", "waxed_cut_copper_slab",
            "granite_slab", "cut_red_sandstone_slab", "mud_brick_slab", "prismarine_slab", "dark_prismarine_slab",
            "snow",
            // thin geometry
            "iron_bars", "iron_chain", "polished_deepslate_wall", "andesite_wall", "mud_brick_wall", "prismarine_wall",
            "diorite_wall",
            // lights and fences
            "waxed_copper_bulb", "waxed_exposed_copper_bulb", "waxed_weathered_copper_bulb", "lantern", "barrier", "light");

    private static final Pattern STATE = Pattern.compile("minecraft:([a-z0-9_]+)(\\[[a-z0-9_=,]+])?");

    /** True when {@code state} is a syntactically plain state of an allowed block. Air is index 0 only. */
    public static boolean allowed(String state) {
        var m = STATE.matcher(state);
        if (!m.matches()) return false;
        String id = m.group(1);
        return FULL_BLOCKS.contains(id) || SHAPES.contains(id);
    }

    public static String blockId(String state) {
        int b = state.indexOf('[');
        return b < 0 ? state : state.substring(0, b);
    }
}
