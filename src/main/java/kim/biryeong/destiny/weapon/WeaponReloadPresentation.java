package kim.biryeong.destiny.weapon;

import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;
import java.util.Map;

/** Live-only first-person reload (including Ace W157). Cosmetic data never authorizes a reload or transfers ammo.
 * Float slot 1 is transient normalized progress (-1 inactive); slot 0/strings/grip/colours belong to other renderers.
 * Identity set prevents persisted selectors/OP previews from masquerading as active reloads.
 * Main server thread only; packet getters read this set, never bind state or mutate a stack.
 */
public final class WeaponReloadPresentation {
    private static final Set<ItemStack> ACTIVE = Collections.newSetFromMap(new IdentityHashMap<>());
    private record Binding(ServerPlayer owner, float offset) {}
    private static final Map<ItemStack, Binding> OWNERS = new IdentityHashMap<>();
    public static final int PROGRESS_INDEX = 1;
    /** Dense reload banks; older unaffected weapon banks still have 21 poses. */
    static int intervals(ItemStack stack) {
        return WeaponItems.entry(stack).filter(e -> e.id().equals("ace_of_spades")
                || e.id().equals("duke_mk_44") || e.id().equals("ammit_ar2")
                || e.id().equals("blast_furnace") || e.id().equals("hammerhead")
                || e.id().equals("the_recluse") || e.id().equals("beloved")
                || e.id().equals("gnawing_hunger") || e.id().equals("austringer")
                || e.id().equals("antiope_d") || e.id().equals("bug_out_bag")
                || e.id().equals("cold_denial") || e.id().equals("bygones")
                || e.id().equals("lonesome") || e.id().equals("steelfeather_repeater")
                || e.id().equals("aishas_embrace") || e.id().equals("chattering_bone")
                || e.id().equals("halfdan_d") || e.id().equals("claws_of_the_wolf")
                || e.id().equals("bite_of_the_fox") || e.id().equals("retrofit_escapade")
                || e.id().equals("farewell") || e.id().equals("apostate") || e.id().equals("fixed_odds")
                || e.id().equals("distant_relation") || e.id().equals("patron_of_lost_causes")
                || e.id().equals("brass_attacks") || e.id().equals("ikelos_smg_v1_0_1")
                || e.id().equals("erentil_fr4") || e.id().equals("hollow_words") || e.id().equals("dream_breaker") || e.id().equals("null_composure") || e.id().equals("coriolis_force")
                || e.id().equals("line_in_the_sand") || e.id().equals("stormchaser") || e.id().equals("code_duello") || e.id().equals("bellowing_giant") || e.id().equals("bad_omens") || e.id().equals("allied_demand") || e.id().equals("dead_man_walking_xx7463") || e.id().equals("high_albedo") || e.id().equals("frontier_justice") || e.id().equals("retraced_path") || e.id().equals("edge_transit") || e.id().equals("canis_major") || e.id().equals("dimensional_hypotrochoid") || e.id().equals("deafening_whisper") || e.id().equals("salvager_s_salvo") || e.id().equals("pyroclastic_flow") || e.id().equals("seventh_seraph_officer_revolver") || e.id().equals("biting_winds") || e.id().equals("whispering_slab") || e.id().equals("nezarec_s_whisper")).isPresent() ? 60 : 20;
    }
    private WeaponReloadPresentation() {}
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && (entry.id().equals("beloved") || entry.id().equals("duke_mk_44")
                || entry.id().equals("ammit_ar2") || entry.id().equals("the_recluse")
                || entry.id().equals("blast_furnace") || entry.id().equals("hammerhead")
                || entry.id().equals("ace_of_spades") || entry.id().equals("gnawing_hunger")
                || entry.id().equals("lonesome") || entry.id().equals("steelfeather_repeater")
                || entry.id().equals("bug_out_bag") || entry.id().equals("cold_denial")
                || entry.id().equals("austringer") || entry.id().equals("bygones")
                || entry.id().equals("retraced_path") || entry.id().equals("aishas_embrace") || entry.id().equals("chattering_bone") || entry.id().equals("salvager_s_salvo") || entry.id().equals("claws_of_the_wolf") || entry.id().equals("brass_attacks") || entry.id().equals("bite_of_the_fox") || entry.id().equals("bad_omens") || entry.id().equals("dream_breaker") || entry.id().equals("seventh_seraph_officer_revolver") || entry.id().equals("retrofit_escapade") || entry.id().equals("erentil_fr4") || entry.id().equals("coriolis_force") || entry.id().equals("line_in_the_sand") || entry.id().equals("stormchaser") || entry.id().equals("code_duello") || entry.id().equals("bellowing_giant") || entry.id().equals("apostate") || entry.id().equals("hollow_words") || entry.id().equals("distant_relation") || entry.id().equals("farewell") || entry.id().equals("patron_of_lost_causes") || entry.id().equals("high_albedo") || entry.id().equals("antiope_d") || entry.id().equals("ikelos_smg_v1_0_1") || entry.id().equals("halfdan_d") || entry.id().equals("edge_transit") || entry.id().equals("fixed_odds") || entry.id().equals("null_composure") || entry.id().equals("allied_demand") || entry.id().equals("dead_man_walking_xx7463") || entry.id().equals("frontier_justice") || entry.id().equals("canis_major") || entry.id().equals("dimensional_hypotrochoid") || entry.id().equals("deafening_whisper") || entry.id().equals("pyroclastic_flow") || entry.id().equals("biting_winds") || entry.id().equals("whispering_slab") || entry.id().equals("nezarec_s_whisper"));
    }
    public static Identifier model(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("No reload presentation: " + entry);
        String namespace = switch (entry.id()) {
            case "biting_winds", "whispering_slab", "nezarec_s_whisper" -> "weapon_reload_w222_" + entry.id() + "/";
            case "pyroclastic_flow", "seventh_seraph_officer_revolver" -> "weapon_reload_w221_" + entry.id() + "/";
            case "edge_transit", "canis_major", "dimensional_hypotrochoid", "deafening_whisper", "salvager_s_salvo" -> "weapon_reload_w220_" + entry.id() + "/";
            case "allied_demand", "dead_man_walking_xx7463", "high_albedo", "frontier_justice", "retraced_path" -> "weapon_reload_w219_" + entry.id() + "/";
            case "line_in_the_sand", "stormchaser", "code_duello", "bellowing_giant", "bad_omens" -> "weapon_reload_w218_" + entry.id() + "/";
            case "erentil_fr4", "hollow_words", "dream_breaker", "null_composure", "coriolis_force" -> "weapon_reload_w217_" + entry.id() + "/";
            case "distant_relation", "patron_of_lost_causes", "brass_attacks", "ikelos_smg_v1_0_1" -> "weapon_reload_w216_" + entry.id() + "/";
            case "duke_mk_44", "farewell", "apostate", "fixed_odds" -> "weapon_reload_w215_" + entry.id() + "/";
            case "halfdan_d", "claws_of_the_wolf", "bite_of_the_fox", "retrofit_escapade" -> "weapon_reload_w214_" + entry.id() + "/";
            case "lonesome", "steelfeather_repeater", "aishas_embrace", "chattering_bone" -> "weapon_reload_w213_" + entry.id() + "/";
            case "antiope_d", "bug_out_bag", "cold_denial", "bygones" -> "weapon_reload_w212_" + entry.id() + "/";
            case "beloved", "the_recluse", "gnawing_hunger", "austringer" -> "weapon_reload_w208_" + entry.id() + "/";
            case "ammit_ar2" -> "weapon_reload_w207_ammit_ar2/";
            case "blast_furnace" -> "weapon_reload_w207_blast_furnace/";
            case "hammerhead" -> "weapon_reload_w207_hammerhead/";
            case "ace_of_spades" -> "weapon_reload_w157/";
            default -> throw new IllegalArgumentException("No reload presentation: " + entry);
        };
        return Identifier.fromNamespaceAndPath("destiny", namespace + entry.id());
    }
    public static boolean active(ItemStack stack) {
        return ACTIVE.contains(stack) && WeaponItems.entry(stack).filter(WeaponReloadPresentation::supports).isPresent();
    }
    /** The legacy identity set alone has no recipient: require the real reload owner too. */
    public static boolean ownedBy(ServerPlayer owner, ItemStack stack) {
        var binding = OWNERS.get(stack);
        return binding != null && binding.owner == owner && active(stack) && WeaponRuntime.reloadOwnedBy(owner, stack);
    }
    /** Production acquisition tracks retirement ownership independently of the legacy test API. */
    public static void update(ServerPlayer owner, ItemStack stack, boolean reloading, float progress) {
        if (!reloading || !WeaponItems.entry(stack).filter(WeaponReloadPresentation::supports).isPresent()) {
            clear(owner, stack); return;
        }
        var binding = OWNERS.get(stack);
        if (binding == null || binding.owner != owner) {
            Float previous = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY).getFloat(PROGRESS_INDEX);
            float offset = 0;
            // Distinguish even a saved frame0 activation from RemoteSlot's idle snapshot.
            // Tiny offsets stay below the smallest 1/60 model-sample spacing.
            int intervals = intervals(stack);
            if (previous != null) for (int i = 0; i <= intervals; i++)
                if (Float.compare(previous, i / (float) intervals) == 0) { offset = .001f; break; }
            binding = new Binding(owner, offset);
            OWNERS.put(stack, binding);
        }
        ACTIVE.add(stack);
        float normalized = Float.isFinite(progress) ? Math.clamp(progress, 0, 1) : 0;
        int intervals = intervals(stack);
        writeProgress(stack, (float)Math.floor(normalized * intervals + 1e-6f) / intervals + binding.offset);
    }
    /** A stale donor must not retire the recipient's newly acquired binding. */
    public static void clear(ServerPlayer owner, ItemStack stack) {
        var binding = OWNERS.get(stack);
        if (binding != null && binding.owner == owner) clear(stack);
    }
    public static void update(ItemStack stack, boolean reloading, float progress) {
        if (!reloading || !WeaponItems.entry(stack).filter(WeaponReloadPresentation::supports).isPresent()) {
            clear(stack); return;
        }
        ACTIVE.add(stack);
        // No component churn while the rendered sample is unchanged.
        float normalized = Float.isFinite(progress) ? Math.clamp(progress, 0, 1) : 0;
        int intervals = intervals(stack);
        writeProgress(stack, (float)Math.floor(normalized * intervals + 1e-6f) / intervals);
    }
    public static void clear(ItemStack stack) {
        OWNERS.remove(stack);
        // Distinct from progress=0 even for same-tick cancellation: invalidate item/wire caches.
        if (ACTIVE.remove(stack)) writeProgress(stack, -1);
    }
    private static void writeProgress(ItemStack stack, float value) {
        var data = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        var values = new ArrayList<>(data.floats());
        while (values.size() <= PROGRESS_INDEX) values.add(0f);
        if (Float.compare(values.get(PROGRESS_INDEX), value) == 0 && values.size() == data.floats().size()) return;
        values.set(PROGRESS_INDEX, value);
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(values, data.flags(), data.strings(), data.colors()));
    }
}
