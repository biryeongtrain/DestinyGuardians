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
import java.util.Set;

/** Cosmetic server-tick samples on the selected incoming carrier, never a gameplay clock.
 * STOW renders the outgoing weapon; READY renders the incoming weapon. Float5 encodes
 * 0..1 / 2..3 respectively, plus a positive sub-.001 binding cache offset.
 * No frame interpolation, hand IK or persisted-CMD authority.
 * Main server thread only. Queries neither create bindings nor change components.
 */
public final class WeaponSwapPresentation {
    public static final int SELECTOR_INDEX = 5, STEPS = 20;

    private static final Set<String> AUTHORED_WEAPONS =
            Set.of("austringer", "beloved", "ammit_ar2", "the_recluse");

    // Snapshot ONLY our slot, not another renderer's component/list. null means absent.
    private record Binding(ServerPlayer owner, ServerLevel level, WeaponCatalog.Entry outgoing,
                           WeaponCatalog.Entry incoming, WeaponSwapCycle.Phase phase, Float previous, float offset) {}
    private static final Map<ItemStack, Binding> ACTIVE = new IdentityHashMap<>();

    private WeaponSwapPresentation() {}

    public static boolean supports(WeaponCatalog.Entry fromEntry, WeaponCatalog.Entry toEntry) {
        if (fromEntry == null || toEntry == null) return false;
        // Pair graphs contain both identities. A single incoming skin cannot also
        // replace the outgoing donor, so new identities use the normal item switch.
        if (LegendaryWeapons.contains(fromEntry.id()) || LegendaryWeapons.contains(toEntry.id())) return false;
        return AUTHORED_WEAPONS.contains(fromEntry.id()) && AUTHORED_WEAPONS.contains(toEntry.id())
                && !fromEntry.id().equals(toEntry.id());
    }

    public static boolean active(ItemStack stack) {
        var b = ACTIVE.get(stack);
        if (b == null || b.owner.getMainHandItem() != stack || b.owner.level() != b.level
                || !WeaponLoadout.canUse(b.owner)
                || !WeaponItems.entry(stack).filter(b.incoming::equals).isPresent()) return false;
        // Handling verifies actual current stack, owner, level and eligibility. A saved selector,
        // component-equal copy or a donor's old session cannot authorize this model route.
        return WeaponHandling.presentation(b.owner).filter(view -> view.outgoing().equals(b.outgoing)
                && view.phase() == b.phase && view.phase() != WeaponSwapCycle.Phase.NONE).isPresent();
    }

    /** Recipient-scoped transport admission; equality/copies confer no ownership. */
    public static boolean ownedBy(ServerPlayer owner, ItemStack stack) {
        var b = ACTIVE.get(stack);
        return b != null && b.owner == owner && active(stack);
    }

    public static Identifier model(ItemStack stack) {
        if (!active(stack)) throw new IllegalStateException("No live swap presentation");
        var b = ACTIVE.get(stack);
        return packModel(b.outgoing, b.incoming);
    }

    static Identifier packModel(WeaponCatalog.Entry outgoing, WeaponCatalog.Entry incoming) {
        if (!supports(outgoing, incoming)) throw new IllegalArgumentException("Unsupported swap");
        boolean w91 = (outgoing.id().equals("austringer") && incoming.id().equals("beloved"))
                || (outgoing.id().equals("beloved") && incoming.id().equals("austringer"));
        return Identifier.fromNamespaceAndPath("destiny", (w91 ? "weapon_swap_w91/" : "weapon_swap_w113/")
                + outgoing.id() + "_to_" + incoming.id());
    }

    public static void update(ServerPlayer owner, ItemStack current, WeaponCatalog.Entry outgoing,
                              WeaponSwapCycle.Phase phase, float progress) {
        var incoming = WeaponItems.entry(current).orElse(null);
        var view = WeaponHandling.presentation(owner);
        if (owner.getMainHandItem() != current || !WeaponLoadout.canUse(owner) || !supports(outgoing, incoming)
                || phase == null || phase == WeaponSwapCycle.Phase.NONE || !Float.isFinite(progress)
                || view.isEmpty() || !view.get().outgoing().equals(outgoing)
                || view.get().phase() != phase || Float.compare(view.get().progress(), progress) != 0) {
            clear(owner, current);
            return;
        }
        var old = ACTIVE.get(current);
        var data = current.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        // An exact-stack handoff carries its ORIGINAL slot through to the recipient.
        // The donor's live sample must never become the recipient's restoration snapshot.
        Float previous = old != null ? old.previous
                : data.floats().size() > SELECTOR_INDEX ? data.floats().get(SELECTOR_INDEX) : null;
        float offset;
        if (old != null && old.owner == owner && old.level == owner.level()
                && old.outgoing.equals(outgoing) && old.incoming.equals(incoming)) offset = old.offset;
        else {
            Float replaced = data.floats().size() > SELECTOR_INDEX ? data.floats().get(SELECTOR_INDEX) : null;
            offset = .0001f;
            // Two forbidden values can exclude at most two candidates. Positive sub-.001
            // offsets preserve every asset threshold yet invalidate component-keyed wire
            // caches even if saved CMD already equals the first sample or a donor's sample.
            while (collides(previous, offset) || collides(replaced, offset)) offset += .0001f;
        }
        ACTIVE.put(current, new Binding(owner, owner.level(), outgoing, incoming, phase, previous, offset));
        float p = Math.clamp(progress, 0, 1);
        float value = (phase == WeaponSwapCycle.Phase.READY ? 2 : 0)
                + (float) Math.floor(p * STEPS + 1e-6f) / STEPS + offset;
        var values = new ArrayList<>(data.floats());
        while (values.size() <= SELECTOR_INDEX) values.add(0f);
        if (Float.compare(values.get(SELECTOR_INDEX), value) == 0
                && values.size() == data.floats().size()) return;
        values.set(SELECTOR_INDEX, value);
        current.set(DataComponents.CUSTOM_MODEL_DATA,
                new CustomModelData(values, data.flags(), data.strings(), data.colors()));
    }

    private static boolean collides(Float value, float offset) {
        if (value == null || !Float.isFinite(value)) return false;
        for (int phase = 0; phase < 2; phase++) for (int sample = 0; sample <= STEPS; sample++)
            if (Float.compare(value, phase * 2 + (float) sample / STEPS + offset) == 0) return true;
        return false;
    }

    public static void clear(ServerPlayer owner, ItemStack stack) {
        var b = ACTIVE.get(stack);
        if (b == null || b.owner != owner || !ACTIVE.remove(stack, b)) return;
        var data = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        if (data.floats().size() <= SELECTOR_INDEX) return;
        var values = new ArrayList<>(data.floats());
        if (b.previous != null) values.set(SELECTOR_INDEX, b.previous);
        else if (values.size() == SELECTOR_INDEX + 1) values.remove(SELECTOR_INDEX);
        else values.set(SELECTOR_INDEX, 0f); // Keep higher selectors at their original indices.
        // Lower padding is deliberately left alone: lower floats belong to other renderers,
        // even when zero. Never restore a whole old CMD or trim another renderer's slots.
        if (!values.equals(data.floats())) stack.set(DataComponents.CUSTOM_MODEL_DATA,
                new CustomModelData(values, data.flags(), data.strings(), data.colors()));
    }

    public static void cleanup(ServerPlayer owner) {
        for (var stack : List.copyOf(ACTIVE.keySet())) {
            var b = ACTIVE.get(stack);
            if (b != null && b.owner == owner) clear(owner, stack);
        }
    }

    public static void clearAll() {
        for (var stack : List.copyOf(ACTIVE.keySet())) {
            var b = ACTIVE.get(stack);
            if (b != null) clear(b.owner, stack);
        }
    }
}
