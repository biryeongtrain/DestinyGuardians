package kim.biryeong.destiny.inventory;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.weapon.WeaponCharacteristics;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponPerks;
import kim.biryeong.destiny.weapon.WeaponSlot;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/** Two UI groups backed only by real, exact weapon trait sockets. No preview mutation. */
public final class WeaponPerkSelection {
    public enum Group { DAMAGE, UTILITY }
    public record Option(String id, String name, String description, boolean selected, boolean enabled, String reason) {}

    private WeaponPerkSelection() {}

    private static boolean matches(String id, Group group) {
        return WeaponPerkLabels.damage(id) == (group == Group.DAMAGE);
    }

    public static String selected(ItemStack stack, Group group) {
        if (stack == null || group == null) return "";
        return WeaponPerks.ids().stream().filter(id -> matches(id, group))
                .filter(id -> WeaponPerks.selected(stack, id).isPresent()).findFirst().orElse("");
    }

    private static Optional<WeaponPerks.Roll> other(ItemStack stack, Group group) {
        String id = selected(stack, group == Group.DAMAGE ? Group.UTILITY : Group.DAMAGE);
        return id.isEmpty() ? Optional.empty() : WeaponPerks.selected(stack, id);
    }

    private static Optional<WeaponPerks.Roll> fitting(ItemStack stack, String id, Optional<WeaponPerks.Roll> kept) {
        return WeaponPerks.available(stack, id).stream()
                .filter(roll -> kept.isEmpty() || roll.socket() != kept.get().socket()).findFirst();
    }

    private static String conflict() {
        return "다른 분류에서 선택한 퍽과 같은 소켓을 사용합니다. 먼저 해당 퍽을 해제해 주세요.";
    }

    /** Pure projection; descriptions are original-game text, labeled by the HUD. */
    public static List<Option> options(ItemStack stack, Group group) {
        if (stack == null || group == null) return List.of();
        String current = selected(stack, group);
        String keptId = selected(stack, group == Group.DAMAGE ? Group.UTILITY : Group.DAMAGE);
        var kept = keptId.isEmpty() ? List.<WeaponPerks.Roll>of() : WeaponPerks.available(stack, keptId);
        var result = new ArrayList<Option>();
        result.add(new Option("", "없음", "이 분류의 선택한 퍽을 해제합니다.", current.isEmpty(), true, ""));
        for (String id : WeaponPerks.choices(stack)) {
            if (!matches(id, group)) continue;
            var candidates = WeaponPerks.available(stack, id);
            // Match configure(): the kept logical perk may move to another permitted socket.
            boolean enabled = !candidates.isEmpty() && (keptId.isEmpty() || candidates.stream()
                    .anyMatch(candidate -> kept.stream().anyMatch(other -> candidate.socket() != other.socket())));
            result.add(new Option(id, WeaponPerkLabels.name(id), WeaponPerkLabels.description(id),
                    id.equals(current), enabled, enabled ? "" : conflict()));
        }
        return List.copyOf(result);
    }

    /** Configure a caller-owned detached draft. Resolve the complete pair before touching it.
     * Availability comes from the real weapon pool; this method neither grants nor equips items.
     */
    public static String configure(ItemStack draft, String damageId, String utilityId) {
        if (draft == null || draft.getCount() != 1 || WeaponItems.entry(draft).isEmpty())
            return "선택한 무기의 테스트 초안을 다시 만들어 주세요.";
        if (damageId == null || utilityId == null) return "퍽 선택을 다시 확인해 주세요. 없음은 빈 선택으로 지정해 주세요.";
        var choices = WeaponPerks.choices(draft);
        if (!damageId.isEmpty() && (!choices.contains(damageId) || !matches(damageId, Group.DAMAGE)))
            return "이 무기의 공격력 분류에서 지원하지 않는 퍽입니다.";
        if (!utilityId.isEmpty() && (!choices.contains(utilityId) || !matches(utilityId, Group.UTILITY)))
            return "이 무기의 유틸리티 분류에서 지원하지 않는 퍽입니다.";
        List<WeaponPerks.Roll> replacement = List.of();
        if (damageId.isEmpty()) {
            if (!utilityId.isEmpty()) replacement = List.of(WeaponPerks.available(draft, utilityId).getFirst());
        } else if (utilityId.isEmpty()) {
            replacement = List.of(WeaponPerks.available(draft, damageId).getFirst());
        } else {
            // Search every exact supported alternative, rather than rejecting a pair because
            // its first damage roll occupies the first utility roll's socket.
            for (var damage : WeaponPerks.available(draft, damageId)) {
                var utility = fitting(draft, utilityId, Optional.of(damage));
                if (utility.isPresent()) { replacement = List.of(damage, utility.get()); break; }
            }
            if (replacement.isEmpty()) return conflict();
        }
        return WeaponPerks.replaceSelection(draft, replacement) ? null : "무기의 실제 퍽 소켓을 다시 확인해 주세요.";
    }

    /** Reject before any writes, including equal copies, stale tokens and misplaced live weapons. */
    public static String edit(ServerPlayer p, ItemStack expected, Group group, String id) {
        if (p == null || !p.level().getServer().isSameThread()) return "서버에서 퍽을 다시 선택해 주세요.";
        if (!p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected() || AbilityService.inSuper(p))
            return "현재 동작 중에는 퍽을 변경할 수 없습니다.";
        if (group == null || id == null) return "퍽 분류와 선택을 다시 확인해 주세요.";
        if (expected == null || expected.getCount() != 1) return "장착한 전투 무기 한 개를 선택해 주세요.";
        var entry = WeaponItems.entry(expected);
        if (entry.isEmpty()) return "테스트 미리 보기가 아닌 장착 무기를 선택해 주세요.";
        WeaponSlot slot = WeaponCharacteristics.of(entry.get()).slot();
        if (p.getInventory().getItem(slot.hotbar()) != expected)
            return "장착 무기가 변경되었습니다. 장착 무기의 퍽을 다시 선택해 주세요.";
        if (!id.isEmpty() && (!WeaponPerks.choices(expected).contains(id) || !matches(id, group)))
            return "이 무기의 해당 분류에서 지원하지 않는 퍽입니다.";
        if (selected(expected, group).equals(id)) return null;

        var kept = other(expected, group);
        var replacement = new ArrayList<WeaponPerks.Roll>();
        kept.ifPresent(replacement::add);
        if (!id.isEmpty()) {
            var choice = fitting(expected, id, kept);
            if (choice.isEmpty()) return conflict();
            replacement.add(choice.get());
        }
        if (!WeaponPerks.replaceSelection(expected, replacement)) return "무기의 실제 퍽 소켓을 다시 확인해 주세요.";
        p.getInventory().setChanged();
        p.containerMenu.broadcastChanges();
        return null;
    }
}
