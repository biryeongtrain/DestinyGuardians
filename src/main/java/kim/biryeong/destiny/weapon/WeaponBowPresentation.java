package kim.biryeong.destiny.weapon;

import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.Map;

/** W50 ordinary-bow cosmetics. Only WeaponRuntime writes live state on the server thread.
 * Float2 is a transient discrete selector; stored/copied CMD never authorizes draw, reload or animation.
 * Read-only Polymer getters must not bind an item, transfer ammo, or advance its clock.
 */
public final class WeaponBowPresentation {
    public static final int SELECTOR_INDEX = 2;
    public static final int EMPTY = 0, LOADED = 1, DRAW_BASE = 2, NOCK_BASE = 32, STEPS = 20;
    private record Binding(ServerPlayer owner, ServerLevel level, float offset) {}
    private static final Map<ItemStack, Binding> ACTIVE = new IdentityHashMap<>();
    private WeaponBowPresentation() {}

    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry != null && (entry.id().equals("biting_winds") || entry.id().equals("whispering_slab"));
    }
    public static Identifier model(WeaponCatalog.Entry entry) {
        if (!supports(entry)) throw new IllegalArgumentException("No W50 bow presentation: " + entry);
        return Identifier.fromNamespaceAndPath("destiny", "weapon_bow_w50/" + entry.id());
    }
    public static boolean active(ItemStack stack) {
        var binding = ACTIVE.get(stack);
        return binding != null && binding.owner.getMainHandItem() == stack && binding.owner.level() == binding.level
                && binding.owner.isAlive() && !binding.owner.isRemoved() && !binding.owner.isSpectator()
                && !kim.biryeong.destiny.ability.AbilityService.inSuper(binding.owner) && WeaponLoadout.canUse(binding.owner)
                && WeaponItems.entry(stack).filter(WeaponBowPresentation::supports).isPresent();
    }
    /** Pure transport admission; a donor's live binding is not the recipient's. */
    public static boolean ownedBy(ServerPlayer owner, ItemStack stack) {
        var binding = ACTIVE.get(stack);
        return binding != null && binding.owner == owner && active(stack);
    }
    static void update(ServerPlayer player, ItemStack stack, boolean loaded, long drawTicks, int fullDrawTicks,
                       boolean nocking, float nockProgress) {
        if (WeaponItems.entry(stack).filter(WeaponBowPresentation::supports).isEmpty()) {
            clear(player, stack); return;
        }
        int selector = nocking ? NOCK_BASE + sample(nockProgress)
                : !loaded ? EMPTY : drawTicks >= 0 ? DRAW_BASE + sample(drawTicks / (float)Math.max(1, fullDrawTicks)) : LOADED;
        // A saved/copied selector can already equal the new idle/draw sample. Give
        // each activation a stable 0 or .5 fractional offset differing from the
        // current value, so inventory/equipment diffing sees ownership acquisition.
        // Integer range thresholds make both offsets select exactly the same pose.
        var binding = ACTIVE.get(stack);
        if (binding == null || binding.owner != player || binding.level != player.level()) {
            Float stored = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY).getFloat(SELECTOR_INDEX);
            float offset = stored != null && Float.compare(stored, selector) == 0 ? .5f : 0f;
            binding = new Binding(player, player.level(), offset);
            ACTIVE.put(stack, binding);
        }
        write(stack, selector + binding.offset);
    }
    public static void clear(ItemStack stack) {
        // Invalidate same-tick wire-cache lookups even if an immediately cancelled draw was at frame0.
        if (ACTIVE.remove(stack) != null) write(stack, -1);
    }
    /** Retire only this acquisition's owner, never a transferred original's new binding. */
    public static void clear(ServerPlayer owner, ItemStack stack) {
        var binding = ACTIVE.get(stack);
        if (binding != null && binding.owner == owner) clear(stack);
    }
    private static int sample(float progress) {
        return (int)Math.floor((Float.isFinite(progress) ? Math.clamp(progress, 0, 1) : 0) * STEPS + 1e-6f);
    }
    private static void write(ItemStack stack, float selector) {
        var data = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        var values = new ArrayList<>(data.floats());
        while (values.size() <= SELECTOR_INDEX) values.add(0f);
        if (Float.compare(values.get(SELECTOR_INDEX), selector) == 0 && values.size() == data.floats().size()) return;
        values.set(SELECTOR_INDEX, selector);
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(values, data.flags(), data.strings(), data.colors()));
    }
}
