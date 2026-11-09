package kim.biryeong.destiny.weapon;

import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

/** Server-tick sampled first-person ADS transforms, not client-frame interpolation or hand IK.
 * Float3 never authorizes aiming; only an actual matching WeaponAiming session does.
 * Reload1/bow2/grip flag0/pose string0 and arbitrary unrelated data remain independent.
 */
public final class WeaponAimPresentation {
    public static final int PROGRESS_INDEX = 3, STEPS = 20;
    private static final java.util.Set<String> SIGHT_ALIGNED = java.util.Set.of(
            "dust_rock_blues", "first_in_last_out", "ikelos_sg_v1_0_1",
            "parcel_of_stardust_fell_to_earth", "mindbender_s_ambition_adept",
            "biting_winds", "whispering_slab");
    private static final java.util.Set<String> LAUNCHER_SIGHTS = java.util.Set.of(
            "canis_major", "dimensional_hypotrochoid", "deafening_whisper", "salvager_s_salvo");
    private static final java.util.Set<String> TRACE_ROCKET_SIGHTS = java.util.Set.of(
            "retraced_path", "bellowing_giant", "pyroclastic_flow");
    private static final java.util.Set<String> LFR_SIGHTS = java.util.Set.of("line_in_the_sand", "stormchaser");
    private static final java.util.Set<String> RIFLE_HANDGUN_SIGHTS = java.util.Set.of(
            "duke_mk_44", "austringer", "seventh_seraph_officer_revolver",
            "allied_demand", "farewell", "lonesome",
            "halfdan_d", "ammit_ar2", "gnawing_hunger", "steelfeather_repeater",
            "frontier_justice", "distant_relation", "cold_denial", "bygones",
            "chattering_bone", "blast_furnace", "claws_of_the_wolf", "hammerhead",
            "bad_omens", "code_duello");
    private static final java.util.Set<String> REMAINING_RANGED_SIGHTS = java.util.Set.of(
            "patron_of_lost_causes", "aishas_embrace", "long_arm", "antiope_d", "bug_out_bag", "ikelos_smg_v1_0_1", "the_recluse", "dead_man_walking_xx7463", "high_albedo", "brass_attacks", "erentil_fr4", "hollow_words", "dream_breaker", "null_composure", "coriolis_force", "edge_transit", "fixed_odds", "retrofit_escapade");
    static String modelPrefix(WeaponCatalog.Entry entry) {
        entry = LegendaryWeapons.base(entry);
        if (entry.id().equals("ace_of_spades")) return "weapon_sight_w159/";
        if (REMAINING_RANGED_SIGHTS.contains(entry.id())) return "weapon_sight_w153/";
        if (RIFLE_HANDGUN_SIGHTS.contains(entry.id())) return "weapon_sight_w151/";
        return (TRACE_ROCKET_SIGHTS.contains(entry.id()) || LFR_SIGHTS.contains(entry.id())) ? "weapon_sight_w150/" : LAUNCHER_SIGHTS.contains(entry.id()) ? "weapon_sight_w149/" : SIGHT_ALIGNED.contains(entry.id()) ? "weapon_sight_w148/" : "weapon_aim_w70/";
    }
    /** Only a fully raised physical or holographic sight replaces the screen-space hip reticle. */
    public static boolean physicalSight(WeaponCatalog.Entry entry, float progress) {
        entry = LegendaryWeapons.base(entry);
        return Float.isFinite(progress) && progress >= .95f && (entry.id().equals("ace_of_spades") || SIGHT_ALIGNED.contains(entry.id()) || LAUNCHER_SIGHTS.contains(entry.id()) || TRACE_ROCKET_SIGHTS.contains(entry.id()) || RIFLE_HANDGUN_SIGHTS.contains(entry.id()) || REMAINING_RANGED_SIGHTS.contains(entry.id()));
    }
    private record Binding(ServerPlayer owner, ServerLevel level, float offset, List<Float> previous) {}
    private static final Map<ItemStack, Binding> ACTIVE = new IdentityHashMap<>();
    private WeaponAimPresentation() {}
    public static boolean supports(WeaponCatalog.Entry entry) { return WeaponAimProfile.supports(LegendaryWeapons.base(entry)); }
    public static boolean active(ItemStack stack) {
        var b = ACTIVE.get(stack);
        return b != null && b.owner.getMainHandItem() == stack && b.owner.level() == b.level
                && WeaponAiming.progress(b.owner) > 0
                && WeaponItems.entry(stack).filter(WeaponAimPresentation::supports).isPresent();
    }
    /** Pure transport admission against the original held object, never a snapshot. */
    public static boolean ownedBy(ServerPlayer owner, ItemStack stack) {
        var binding = ACTIVE.get(stack);
        return binding != null && binding.owner == owner && active(stack);
    }
    public static Identifier model(ItemStack stack) {
        var e = WeaponItems.entry(stack).filter(WeaponAimPresentation::supports).map(LegendaryWeapons::base).orElseThrow();
        return Identifier.fromNamespaceAndPath("destiny", modelPrefix(e) + e.id()
                + (WeaponBowPresentation.active(stack) ? "_bow" : ""));
    }
    static void update(ServerPlayer owner, ItemStack stack, float progress) {
        float p = Float.isFinite(progress) ? Math.clamp(progress, 0, 1) : 0;
        if (p <= 0 || !WeaponItems.entry(stack).filter(WeaponAimPresentation::supports).isPresent()) {
            clear(owner,stack); return;
        }
        WeaponInsertPresentation.beforeAim(owner,stack);
        float sample = (float)Math.floor(p * STEPS + 1e-6f) / STEPS;
        var b = ACTIVE.get(stack);
        if (b == null || b.owner != owner || b.level != owner.level()) {
            var current = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY).floats();
            // Carry the original value through exact-stack handoffs, not the donor's live sample.
            var previous = b == null ? List.copyOf(current) : b.previous;
            Float saved = previous.size() > PROGRESS_INDEX ? previous.get(PROGRESS_INDEX) : null;
            Float replaced = current.size() > PROGRESS_INDEX ? current.get(PROGRESS_INDEX) : null;
            // At most two candidates are forbidden. Keep all samples distinct from both the
            // original value and the previous owner's last sample, even on repeated handoffs.
            float offset = 0;
            while (collides(saved, offset) || collides(replaced, offset)) offset += .001f;
            b = new Binding(owner, owner.level(), offset, previous);
            ACTIVE.put(stack, b);
        }
        write(stack, sample + b.offset);
    }
    private static boolean collides(Float value, float offset) {
        if (value == null || !Float.isFinite(value)) return false;
        for (int i = 0; i <= STEPS; i++)
            if (Float.compare(value, (float)i / STEPS + offset) == 0) return true;
        return false;
    }
    static boolean boundToOther(ServerPlayer owner, ItemStack stack) {
        var b = ACTIVE.get(stack);
        return b != null && b.owner != owner && active(stack);
    }
    static void clear(ServerPlayer owner, ItemStack stack) {
        var b = ACTIVE.get(stack);
        if (b == null || b.owner != owner || !ACTIVE.remove(stack,b)) return;
        var d = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        var values = new ArrayList<>(d.floats());
        if (values.size() > PROGRESS_INDEX) {
            if (b.previous.size() > PROGRESS_INDEX) values.set(PROGRESS_INDEX,b.previous.get(PROGRESS_INDEX));
            else if (values.size() > PROGRESS_INDEX + 1) values.set(PROGRESS_INDEX,0f); // Keep higher slots at their indices.
            else {
                values.remove(PROGRESS_INDEX);
                // Remove only our untouched padding, never another renderer's live selector.
                while (values.size() > b.previous.size() && !values.isEmpty()) {
                    int i = values.size()-1;
                    if (values.get(i) != 0f || i == WeaponBowPresentation.SELECTOR_INDEX && WeaponBowPresentation.active(stack)
                            || i == WeaponReloadPresentation.PROGRESS_INDEX && WeaponReloadPresentation.active(stack)) break;
                    values.remove(i);
                }
            }
        }
        if (!values.equals(d.floats()))
            stack.set(DataComponents.CUSTOM_MODEL_DATA,new CustomModelData(values,d.flags(),d.strings(),d.colors()));
    }
    private static void write(ItemStack stack, float value) {
        var d = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        var values = new ArrayList<>(d.floats());
        while (values.size() <= PROGRESS_INDEX) values.add(0f);
        if (Float.compare(values.get(PROGRESS_INDEX), value) == 0 && values.size() == d.floats().size()) return;
        values.set(PROGRESS_INDEX, value);
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(values, d.flags(), d.strings(), d.colors()));
    }
}
