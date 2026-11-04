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
    private WeaponReloadPresentation() {}
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && (entry.id().equals("beloved") || entry.id().equals("duke_mk_44")
                || entry.id().equals("ammit_ar2") || entry.id().equals("the_recluse")
                || entry.id().equals("blast_furnace") || entry.id().equals("hammerhead")
                || entry.id().equals("ace_of_spades") || entry.id().equals("gnawing_hunger")
                || entry.id().equals("lonesome") || entry.id().equals("steelfeather_repeater")
                || entry.id().equals("bug_out_bag") || entry.id().equals("cold_denial")
                || entry.id().equals("austringer") || entry.id().equals("bygones")
                || entry.id().equals("retraced_path") || entry.id().equals("aishas_embrace") || entry.id().equals("chattering_bone") || entry.id().equals("salvager_s_salvo") || entry.id().equals("claws_of_the_wolf") || entry.id().equals("brass_attacks") || entry.id().equals("bite_of_the_fox") || entry.id().equals("bad_omens") || entry.id().equals("dream_breaker") || entry.id().equals("seventh_seraph_officer_revolver") || entry.id().equals("retrofit_escapade") || entry.id().equals("erentil_fr4") || entry.id().equals("coriolis_force") || entry.id().equals("line_in_the_sand") || entry.id().equals("stormchaser") || entry.id().equals("code_duello") || entry.id().equals("bellowing_giant") || entry.id().equals("apostate") || entry.id().equals("hollow_words") || entry.id().equals("distant_relation") || entry.id().equals("farewell") || entry.id().equals("patron_of_lost_causes") || entry.id().equals("high_albedo") || entry.id().equals("antiope_d") || entry.id().equals("ikelos_smg_v1_0_1") || entry.id().equals("halfdan_d") || entry.id().equals("edge_transit") || entry.id().equals("fixed_odds") || entry.id().equals("null_composure"));
    }
    public static Identifier model(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("No reload presentation: " + entry);
        String namespace = switch (entry.id()) {
            case "beloved" -> "weapon_reload_w47/";
            case "duke_mk_44" -> "weapon_reload_w169_duke_mk_44/";
            case "erentil_fr4", "coriolis_force" -> "weapon_reload_w189_" + entry.id() + "/";
            case "line_in_the_sand", "stormchaser" -> "weapon_reload_w188_" + entry.id() + "/";
            case "code_duello", "bellowing_giant" -> "weapon_reload_w187_" + entry.id() + "/";
            case "apostate", "hollow_words" -> "weapon_reload_w185_" + entry.id() + "/";
            case "distant_relation", "farewell" -> "weapon_reload_w184_" + entry.id() + "/";
            case "patron_of_lost_causes", "high_albedo" -> "weapon_reload_w183_" + entry.id() + "/";
            case "antiope_d", "ikelos_smg_v1_0_1" -> "weapon_reload_w182_" + entry.id() + "/";
            case "seventh_seraph_officer_revolver", "retrofit_escapade" -> "weapon_reload_w181_" + entry.id() + "/";
            case "halfdan_d", "edge_transit" -> "weapon_reload_w180_" + entry.id() + "/";
            case "fixed_odds", "null_composure" -> "weapon_reload_w179_" + entry.id() + "/";
            case "dream_breaker" -> "weapon_reload_w178_dream_breaker/";
            case "bite_of_the_fox", "bad_omens" -> "weapon_reload_w177_" + entry.id() + "/";
            case "brass_attacks" -> "weapon_reload_w176_brass_attacks/";
            case "claws_of_the_wolf" -> "weapon_reload_w174_claws_of_the_wolf/";
            case "salvager_s_salvo" -> "weapon_reload_w173_salvager_s_salvo/";
            case "chattering_bone" -> "weapon_reload_w172_chattering_bone/";
            case "aishas_embrace" -> "weapon_reload_w171_aishas_embrace/";
            case "retraced_path" -> "weapon_reload_w170_retraced_path/";
            case "ammit_ar2" -> "weapon_reload_w69/";
            case "the_recluse" -> "weapon_reload_w101/";
            case "blast_furnace" -> "weapon_reload_w114_blast_furnace/";
            case "hammerhead" -> "weapon_reload_w114_hammerhead/";
            case "ace_of_spades" -> "weapon_reload_w157/";
            case "gnawing_hunger", "lonesome" -> "weapon_reload_w164_" + entry.id() + "/";
            case "steelfeather_repeater", "bug_out_bag" -> "weapon_reload_w166_" + entry.id() + "/";
            case "cold_denial" -> "weapon_reload_w167_cold_denial/";
            case "austringer", "bygones" -> "weapon_reload_w168_" + entry.id() + "/";
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
            // Tiny offsets stay below the existing .05 model-sample spacing.
            if (previous != null) for (int i = 0; i <= 20; i++)
                if (Float.compare(previous, i / 20f) == 0) { offset = .001f; break; }
            binding = new Binding(owner, offset);
            OWNERS.put(stack, binding);
        }
        ACTIVE.add(stack);
        float normalized = Float.isFinite(progress) ? Math.clamp(progress, 0, 1) : 0;
        writeProgress(stack, (float)Math.floor(normalized * 20 + 1e-6f) / 20 + binding.offset);
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
        // Match the 21 model samples; no component churn while the rendered sample is unchanged.
        float normalized = Float.isFinite(progress) ? Math.clamp(progress, 0, 1) : 0;
        writeProgress(stack, (float)Math.floor(normalized * 20 + 1e-6f) / 20);
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
