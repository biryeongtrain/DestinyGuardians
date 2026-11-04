package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
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

/** Live cosmetic binding only; W84 owns all ammunition, deadlines and saved charge.
 * Float6: reload 0..1, Honed 2..3 (21 samples), completed charge 4. A 0..0.0005
 * generation offset stays within each model bucket and invalidates wire caches.
 * No persisted selector can create a binding. Main server thread only; getters are pure.
 */
public final class WeaponIzanagiPresentation {
    public static final int SELECTOR_INDEX = 6;
    public enum Mode { IDLE, RELOAD, HONED }
    private static final Identifier MODEL = Identifier.parse("destiny:weapon_izanagi_w91/izanagis_burden");
    private static final Map<ItemStack, Binding> ACTIVE = new IdentityHashMap<>();
    private static final Map<ServerPlayer, Binding> OWNERS = new IdentityHashMap<>();

    private static final class Binding {
        final ServerPlayer owner;
        final ServerLevel level;
        final ItemStack stack;
        final Float previousSelector;
        final float offset;
        Mode mode;
        float written;

        Binding(ServerPlayer owner, ItemStack stack, List<Float> current, float offset) {
            this.owner = owner; this.level = owner.level(); this.stack = stack;
            previousSelector = current.size() > SELECTOR_INDEX ? current.get(SELECTOR_INDEX) : null;
            this.offset = offset;
        }
    }

    private WeaponIzanagiPresentation() {}

    public static boolean supports(WeaponCatalog.Entry entry) { return WeaponExotics.izanagi(entry); }

    private static boolean live(ServerPlayer owner, ItemStack stack) {
        return owner != null && stack != null && owner.getMainHandItem() == stack
                && owner.isAlive() && !owner.isRemoved() && !owner.isSpectator() && !owner.hasDisconnected()
                && !AbilityService.inSuper(owner) && WeaponLoadout.canUse(owner)
                && WeaponItems.entry(stack).filter(WeaponIzanagiPresentation::supports).isPresent();
    }

    private static boolean admitted(ServerPlayer owner, ItemStack stack, Mode mode) {
        if (!live(owner, stack) || mode == null) return false;
        if (mode == Mode.IDLE) return WeaponIzanagi.charge(stack) >= 2;
        return WeaponRuntime.reloading(owner)
                && (mode == Mode.HONED) == WeaponIzanagi.honing(owner);
    }

    public static boolean active(ItemStack stack) {
        var b = ACTIVE.get(stack);
        var data = stack == null ? null : stack.get(DataComponents.CUSTOM_MODEL_DATA);
        return b != null && OWNERS.get(b.owner) == b && b.owner.level() == b.level
                && data != null && data.floats().size() > SELECTOR_INDEX
                && Float.compare(data.floats().get(SELECTOR_INDEX), b.written) == 0
                && admitted(b.owner, stack, b.mode);
    }

    /** Recipient-scoped transport admission; snapshots still never own a binding. */
    public static boolean ownedBy(ServerPlayer owner, ItemStack stack) {
        var b = ACTIVE.get(stack);
        return b != null && b.owner == owner && active(stack);
    }

    /** Only an admitted charged idle binding may use the scope wrapper. Reload/honing
     * retain their authored part motion even if a stale cosmetic pose says scope. */
    public static boolean scopedIdle(ItemStack stack) {
        var binding = ACTIVE.get(stack);
        return binding != null && binding.mode == Mode.IDLE && active(stack) && WeaponScopes.scoped(stack);
    }

    /** Wrapper preserves the full original pose/grip/scope route and charged ADS float3. */
    public static Identifier model(ItemStack stack) {
        if (!active(stack)) throw new IllegalArgumentException("No live Izanagi presentation");
        return MODEL;
    }

    public static void update(ServerPlayer owner, ItemStack stack, Mode mode, float progress) {
        var owned = OWNERS.get(owner);
        if (owned != null && (owned.stack != stack || owned.level != owner.level()))
            clear(owner, owned.stack);
        if (!admitted(owner, stack, mode)) { clear(owner, stack); return; }
        var b = ACTIVE.get(stack);
        Float replaced = b == null ? null : b.written;
        if (b != null && b.owner != owner) {
            // A mistaken donor update must not steal a still-live recipient binding.
            if (active(stack)) return;
            clear(b.owner, stack);
            b = null;
        }
        if (b == null) {
            var current = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY).floats();
            Float prior = current.size() > SELECTOR_INDEX ? current.get(SELECTOR_INDEX) : null;
            float offset = 0;
            // At most two offsets are forbidden, including the donor's last wire sample.
            while (collides(prior, offset) || collides(replaced, offset)) offset += .00025f;
            b = new Binding(owner, stack, current, offset);
            ACTIVE.put(stack, b); OWNERS.put(owner, b);
        }
        b.mode = mode;
        float p = Float.isFinite(progress) ? Math.clamp(progress, 0, 1) : 0;
        float sample = (float) Math.floor(p * 20 + 1e-6f) / 20;
        b.written = (mode == Mode.IDLE ? 4 : (mode == Mode.HONED ? 2 : 0) + sample) + b.offset;
        write(stack, b.written);
    }

    private static boolean collides(Float prior, float offset) {
        if (prior == null || !Float.isFinite(prior)) return false;
        if (Float.compare(prior, 4 + offset) == 0) return true;
        for (int base : new int[]{0, 2}) for (int i = 0; i <= 20; i++)
            if (Float.compare(prior, base + (float) i / 20 + offset) == 0) return true;
        return false;
    }

    public static void clear(ServerPlayer owner, ItemStack stack) {
        var b = ACTIVE.get(stack);
        if (b == null || b.owner != owner || !ACTIVE.remove(stack, b)) return;
        OWNERS.remove(owner, b);
        var data = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        var values = new ArrayList<>(data.floats());
        // Another writer's slot6 wins. Never restore an entire old selector vector.
        if (values.size() <= SELECTOR_INDEX || Float.compare(values.get(SELECTOR_INDEX), b.written) != 0) return;
        if (b.previousSelector != null) values.set(SELECTOR_INDEX, b.previousSelector);
        else if (values.size() > SELECTOR_INDEX + 1) values.set(SELECTOR_INDEX, -1f);
        else values.remove(SELECTOR_INDEX);
        // Lower zero padding may now belong to another renderer, even when unchanged.
        // Leave it in place; only slot6 is ours to restore or remove.
        if (!values.equals(data.floats())) stack.set(DataComponents.CUSTOM_MODEL_DATA,
                new CustomModelData(values, data.flags(), data.strings(), data.colors()));
    }

    public static void clearAll() {
        for (var b : List.copyOf(ACTIVE.values())) clear(b.owner, b.stack);
    }

    /** Also releases idle charged bindings created without a WeaponRuntime combat State. */
    public static void cleanup(ServerPlayer owner) {
        var b = OWNERS.get(owner);
        if (b != null) clear(owner, b.stack);
    }

    private static void write(ItemStack stack, float value) {
        var data = stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        var values = new ArrayList<>(data.floats());
        while (values.size() <= SELECTOR_INDEX) values.add(0f);
        if (Float.compare(values.get(SELECTOR_INDEX), value) == 0 && values.size() == data.floats().size()) return;
        values.set(SELECTOR_INDEX, value);
        stack.set(DataComponents.CUSTOM_MODEL_DATA,
                new CustomModelData(values, data.flags(), data.strings(), data.colors()));
    }
}
