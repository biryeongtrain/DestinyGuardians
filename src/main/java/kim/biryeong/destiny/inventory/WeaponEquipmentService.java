package kim.biryeong.destiny.inventory;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponCharacteristics;
import kim.biryeong.destiny.weapon.WeaponHandling;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponLoadout;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import kim.biryeong.destiny.weapon.WeaponSlot;
import net.minecraft.network.protocol.game.ClientboundSetHeldSlotPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/** Equipped inventory plus persistent spare-weapon ownership. UI sessions never own item copies. */
public final class WeaponEquipmentService {
    private static final int MAIN_SIZE = 36;

    public record Owned(int inventoryIndex, ItemStack stack, WeaponCatalog.Entry weapon, boolean equipped) {}

    private WeaponEquipmentService() {}

    private static Optional<WeaponCatalog.Entry> live(ItemStack stack) {
        return stack.getCount() == 1 ? WeaponItems.entry(stack) : Optional.empty();
    }

    /** Read-only equipped/spare projection. Tokens >=1000 resolve only through WeaponStorage.
     * Legacy physical spares remain readable until the next migration boundary.
     */
    public static List<Owned> owned(ServerPlayer p, WeaponSlot slot) {
        List<Owned> result = new ArrayList<>();
        for (int index = 0; index < MAIN_SIZE; index++) {
            ItemStack stack = p.getInventory().getItem(index);
            var entry = live(stack);
            if (entry.isPresent() && WeaponLoadout.slot(p, stack, entry.get()) == slot)
                result.add(new Owned(index, stack, entry.get(), index == slot.hotbar()));
        }
        for (var stored : WeaponStorage.entries(p)) {
            var entry = live(stored.stack());
            if (entry.isPresent() && WeaponLoadout.slot(p, stored.stack(), entry.get()) == slot)
                result.add(new Owned(stored.token(), stored.stack(), entry.get(), false));
        }
        return List.copyOf(result);
    }

    /** Revalidate a click against the exact owned object. All rejection paths precede lifecycle
     * callbacks and inventory/attachment writes. Server-thread confinement makes the storage/equipment
     * transaction indivisible to other inventory actions; asynchronous/stale callers must retry.
     * @return null on success, otherwise a player-facing reason
     */
    public static String equip(ServerPlayer p, int from, ItemStack expected) {
        if (!p.level().getServer().isSameThread()) return "서버에서 장비를 다시 선택해 주세요.";
        if (!p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected() || AbilityService.inSuper(p))
            return "현재 동작 중에는 장비를 변경할 수 없습니다.";
        if (from < 0 || (!WeaponStorage.token(from) && from >= MAIN_SIZE) || expected == null || WeaponStorage.resolve(p, from) != expected)
            return "인벤토리가 변경되었습니다. 소유 무기를 다시 선택해 주세요.";
        var entry = live(expected);
        if (entry.isEmpty()) return "소유한 전투 무기 한 개를 선택해 주세요. 프리뷰는 사용할 수 없습니다.";
        var category = WeaponCharacteristics.of(entry.get());
        var equipmentSlot = WeaponLoadout.slot(p, expected, entry.get());
        int to = equipmentSlot.hotbar();
        ItemStack displaced = p.getInventory().getItem(to);
        if (from != to) {
            // A misplaced weapon in another equipment bucket cannot steal that bucket, even
            // when its own destination is empty. Storage/hotbar indices 3..35 can be swapped.
            if (from < 3) return "무기를 인벤토리 보관 칸으로 옮긴 뒤 장착해 주세요.";
            if (!displaced.isEmpty() && live(displaced)
                    .filter(e -> WeaponLoadout.slot(p, displaced, e) == equipmentSlot).isEmpty())
                return "대상 장비 슬롯을 먼저 비워 주세요. 기존 아이템은 덮어쓰지 않습니다.";
        }
        int exotics = category.exotic() ? 1 : 0;
        for (var slot : WeaponSlot.values()) {
            if (slot.hotbar() == to) continue;
            var other = live(p.getInventory().getItem(slot.hotbar()));
            if (other.filter(e -> WeaponLoadout.slot(p, p.getInventory().getItem(slot.hotbar()), e) == slot
                    && WeaponCharacteristics.of(e).exotic()).isPresent()) exotics++;
        }
        if (exotics > 1) return "경이 무기는 한 개만 장착할 수 있습니다.";

        if (from != to && !displaced.isEmpty() && WeaponStorage.data(p).nextId() == Integer.MAX_VALUE)
            return "무기 보관함에 더 저장할 수 없습니다.";
        int selected = p.getInventory().getSelectedSlot();
        if (from == to && selected == to) {
            // Reaffirming current equipment must not cancel a reload/charge or restart its
            // Handling/RPM clock. Opt-in is the only possible change on this path.
            if (!WeaponLoadout.enabled(p)) p.setAttached(WeaponLoadout.ENABLED, true);
            return null;
        }
        WeaponHandling.update(p);
        WeaponRuntime.cancelUseForSkill(p);
        if (from != to) {
            if (WeaponStorage.token(from)) {
                if (!WeaponStorage.exchange(p, from, expected, displaced)) throw new IllegalStateException("Validated storage ownership changed");
            } else {
                p.getInventory().setItem(from, ItemStack.EMPTY);
                WeaponStorage.retain(p, displaced);
            }
            p.getInventory().setItem(to, expected);
        }
        p.setAttached(WeaponLoadout.ENABLED, true);
        // When the source was held, the same object is still being held after its move.
        // Observing the displaced item temporarily placed at 'from' would invent a swap.
        // Other selections can use the ordinary lifecycle with the final target in place.
        if (selected != from) WeaponRuntime.selectedSlotChanging(p, to);
        p.getInventory().setSelectedSlot(to);
        p.connection.send(new ClientboundSetHeldSlotPacket(to));
        WeaponHandling.update(p);
        kim.biryeong.destiny.crucible.CrucibleAmmo.equipmentChanged(p);
        p.getInventory().setChanged();
        p.containerMenu.broadcastChanges();
        return null;
    }
}
