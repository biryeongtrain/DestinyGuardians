package kim.biryeong.destiny.inventory;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponCharacteristics;
import kim.biryeong.destiny.weapon.WeaponHandling;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponLoadout;
import kim.biryeong.destiny.weapon.WeaponPerks;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import kim.biryeong.destiny.weapon.WeaponSlot;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.protocol.game.ClientboundSetHeldSlotPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;

import java.util.ArrayList;
import java.util.List;

/** Explicit test-stage minting into the actual inventory. No cached or shadow equipment. */
public final class WeaponTestArmory {
    public static final String OWNER_KEY = "destiny_test_armory_owner";

    private WeaponTestArmory() {}

    public static boolean enabled() {
        return Boolean.parseBoolean(System.getProperty("destiny.testArmory", "true"));
    }

    public static List<WeaponCatalog.Entry> catalog(WeaponSlot slot) {
        return WeaponCatalog.all().stream().filter(e -> WeaponCharacteristics.of(e).slot() == slot)
                .sorted(java.util.Comparator.comparing(WeaponCatalog.Entry::id)).toList();
    }

    private static String validate(ServerPlayer p) {
        if (!enabled()) return "테스트 무기 기능이 비활성화되어 있습니다.";
        if (p == null || !p.level().getServer().isSameThread()) return "서버에서 테스트 무기를 다시 선택해 주세요.";
        if (!p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected() || AbilityService.inSuper(p))
            return "현재 동작 중에는 장비를 변경할 수 없습니다.";
        return null;
    }

    private static ItemStack mint(ServerPlayer p, WeaponCatalog.Entry entry) {
        var stack = WeaponItems.create(entry);
        var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.putString(OWNER_KEY, p.getUUID().toString());
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        return stack;
    }

    private static boolean disposable(ServerPlayer p, ItemStack stack, WeaponSlot slot) {
        if (stack.getCount() != 1 || WeaponItems.entry(stack)
                .filter(e -> WeaponCharacteristics.of(e).slot() == slot).isEmpty()) return false;
        var data = stack.get(DataComponents.CUSTOM_DATA);
        return data != null && p.getUUID().toString().equals(data.copyTag().getStringOr(OWNER_KEY, ""));
    }

    private static void sync(ServerPlayer p) {
        p.getInventory().setChanged();
        p.containerMenu.broadcastChanges();
    }

    /** Validate every bucket first, then fill only empty buckets. Existing items stay intact. */
    public static String prepare(ServerPlayer p) {
        String error = validate(p);
        if (error != null) return error;
        var missing = new ArrayList<WeaponCatalog.Entry>();
        int exotics = 0;
        for (var slot : WeaponSlot.values()) {
            var stack = p.getInventory().getItem(slot.hotbar());
            if (stack.isEmpty()) {
                String id = switch (slot) {
                    case KINETIC -> "austringer";
                    case ENERGY -> "ammit_ar2";
                    case POWER -> "bad_omens";
                };
                missing.add(WeaponCatalog.find(id).orElseThrow());
            } else {
                var entry = WeaponItems.entry(stack);
                if (stack.getCount() != 1 || entry.isEmpty() || WeaponCharacteristics.of(entry.get()).slot() != slot)
                    return "장비 칸 " + (slot.hotbar() + 1) + "의 아이템을 보관 칸으로 옮겨 주세요. 해당 분류의 전투 무기만 유지할 수 있습니다.";
                if (WeaponCharacteristics.of(entry.get()).exotic()) exotics++;
            }
        }
        if (exotics > 1) return "경이 무기는 한 개만 장착할 수 있습니다.";
        // Construct all new stacks before touching inventory or runtime.
        var minted = missing.stream().map(e -> mint(p, e)).toList();
        if (!minted.isEmpty()) {
            WeaponHandling.update(p);
            WeaponRuntime.cancelUseForSkill(p);
            for (int i = 0; i < missing.size(); i++)
                p.getInventory().setItem(WeaponCharacteristics.of(missing.get(i)).slot().hotbar(), minted.get(i));
            WeaponHandling.update(p);
        }
        p.setAttached(WeaponLoadout.ENABLED, true);
        sync(p);
        return null;
    }

    public static String equip(ServerPlayer p, String id) {
        return equip(p, id, null);
    }

    /** Final wizard confirmation only. The detached validation draft never enters inventory. */
    public static String add(ServerPlayer p, String id, String damageId, String utilityId) {
        String error = validate(p);
        if (error != null) return error;
        var entry = id == null ? java.util.Optional.<WeaponCatalog.Entry>empty() : WeaponCatalog.find(id);
        if (entry.isEmpty()) return "테스트 무기 목록에서 정확한 무기를 선택해 주세요.";
        var draft = WeaponItems.create(entry.get());
        error = WeaponPerkSelection.configure(draft, damageId, utilityId);
        if (error != null) return error;
        var selection = new ArrayList<WeaponPerks.Roll>();
        for (var group : WeaponPerkSelection.Group.values()) {
            String perk = WeaponPerkSelection.selected(draft, group);
            if (!perk.isEmpty()) selection.add(WeaponPerks.selected(draft, perk).orElseThrow());
        }
        return equip(p, id, List.copyOf(selection));
    }

    /** Null selection retains the original equip API; an empty list explicitly clears both groups. */
    private static String equip(ServerPlayer p, String id, List<WeaponPerks.Roll> selection) {
        String error = validate(p);
        if (error != null) return error;
        var entry = id == null ? java.util.Optional.<WeaponCatalog.Entry>empty() : WeaponCatalog.find(id);
        if (entry.isEmpty()) return "테스트 무기 목록에서 정확한 무기를 선택해 주세요.";
        var category = WeaponCharacteristics.of(entry.get());
        int to = category.slot().hotbar();
        // Prefer the already equipped identity, then real storage. Never mint an owned duplicate.
        var owned = WeaponEquipmentService.owned(p, category.slot());
        var candidate = owned.stream().filter(o -> o.equipped() && o.weapon().id().equals(id)).findFirst();
        if (candidate.isEmpty()) candidate = owned.stream()
                .filter(o -> o.inventoryIndex() >= 3 && o.weapon().id().equals(id)).findFirst();
        if (candidate.isPresent()) {
            var source = candidate.get();
            // Validate on a detached copy of the exact reused entry before equip can move it.
            // The server thread owns the whole transaction; no asynchronous token can intervene.
            if (selection != null && !WeaponPerks.replaceSelection(source.stack().copy(), selection))
                return "소유 무기의 실제 퍽 소켓을 다시 확인해 주세요.";
            error = WeaponEquipmentService.equip(p, source.inventoryIndex(), source.stack());
            if (error != null) return error;
            if (selection != null) {
                var actual = p.getInventory().getItem(to);
                // Existing equip moves this exact object without changing its entry/count.
                // An invariant violation is a programming error, never a partial-success rejection.
                if (actual != source.stack() || actual.getCount() != 1
                        || WeaponItems.entry(actual).filter(entry.get()::equals).isEmpty())
                    throw new IllegalStateException("W228 equipped weapon changed during synchronous confirmation");
                var before = actual.get(DataComponents.CUSTOM_DATA);
                if (!WeaponPerks.replaceSelection(actual, selection))
                    throw new IllegalStateException("W228 prevalidated exact selection became invalid");
                if (!java.util.Objects.equals(before, actual.get(DataComponents.CUSTOM_DATA))) sync(p);
            }
            return null;
        }
        if (owned.stream().anyMatch(o -> o.weapon().id().equals(id)))
            return "소유 무기를 올바른 보관 칸으로 옮긴 뒤 다시 선택해 주세요.";
        int exotics = category.exotic() ? 1 : 0;
        for (var slot : WeaponSlot.values()) {
            if (slot == category.slot()) continue;
            var stack = p.getInventory().getItem(slot.hotbar());
            if (stack.getCount() == 1 && WeaponItems.entry(stack)
                    .filter(e -> WeaponCharacteristics.of(e).slot() == slot && WeaponCharacteristics.of(e).exotic()).isPresent())
                exotics++;
        }
        if (exotics > 1) return "경이 무기는 한 개만 장착할 수 있습니다.";
        var displaced = p.getInventory().getItem(to);
        int storage = -1;
        if (!displaced.isEmpty() && !disposable(p, displaced, category.slot())) {
            for (int i = 3; i < 36; i++) if (p.getInventory().getItem(i).isEmpty()) { storage = i; break; }
            if (storage < 0) return "보관 칸이 가득 찼습니다. 기존 아이템을 보존할 빈 칸이 필요합니다.";
        }
        var incoming = mint(p, entry.get());
        if (selection != null && !WeaponPerks.replaceSelection(incoming, selection))
            return "무기의 실제 퍽 소켓을 다시 확인해 주세요.";
        WeaponHandling.update(p);
        WeaponRuntime.cancelUseForSkill(p);
        if (storage >= 0) p.getInventory().setItem(storage, displaced);
        p.getInventory().setItem(to, incoming);
        p.setAttached(WeaponLoadout.ENABLED, true);
        WeaponRuntime.selectedSlotChanging(p, to);
        p.getInventory().setSelectedSlot(to);
        p.connection.send(new ClientboundSetHeldSlotPacket(to));
        WeaponHandling.update(p);
        sync(p);
        return null;
    }
}
