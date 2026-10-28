package kim.biryeong.destiny.inventory;

import kim.biryeong.destiny.inventory.WeaponScreenLayout.Box;
import kim.biryeong.destiny.inventory.WeaponScreenView.Card;
import kim.biryeong.destiny.inventory.WeaponScreenView.FamilyOption;
import kim.biryeong.destiny.inventory.WeaponScreenView.PerkOption;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponModels;
import kim.biryeong.destiny.weapon.WeaponSlot;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import kim.biryeong.minigamelib.displayhud.TextDisplayHud;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Display;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/** Display-only equipment screen. Controller/input, ownership and equipping remain with the caller. */
public final class WeaponScreenHud {
    public static final String PREFIX = "destiny:equipment_w227_";
    private static final String STATE = "w227_state";
    private static final float MIN_TEXT_PIXELS = 18f;
    private static final int WHITE = 0xE8E9E5;
    private static final int MUTED = 0xA8B0B4;
    private static final int LINE = 0x4A545D;
    private static final int GOLD = 0xD6BE7A;
    private static final int PURPLE = 0xAA8BC4;
    private static final int DISABLED = 0xD5A99B;
    private static final Identifier SOLID = Identifier.parse("destiny:gui/hud/solid");
    private static final WeaponSlot[] SLOTS = {WeaponSlot.KINETIC, WeaponSlot.ENERGY, WeaponSlot.POWER};
    // Official stat hashes in WeaponCharacteristics; also accept named keys in a caller projection.
    private static final String[][] STATS = {
            {"충격", "impact", "4043523819"}, {"사거리", "range", "1240592695"},
            {"안정성", "stability", "155624089"}, {"조작성", "handling", "943549884"},
            {"재장전 속도", "reload_speed", "4188031367"}
    };

    private WeaponScreenHud() { }

    /** Call on the server thread with a read-only snapshot; never moves or mutates an owned stack. */
    public static void render(ServerPlayer player, WeaponScreenView view) {
        Painter p = new Painter(player);
        boolean perkMode = view.perkMode();
        String stage = view.stage();
        boolean familyMode = "FAMILY".equals(stage);
        boolean weaponMode = "WEAPON".equals(stage);
        boolean loadoutMode = !familyMode && !weaponMode && !perkMode;
        // UNALIGNED stretches only the underlay to cover non-16:9 viewports. All content and hits use CENTER.
        p.tile("backdrop", new Box(960, 540, 1920, 1080), 100, 0x1B2229, null, true);
        p.rect("canvas", 960, 540, 1920, 1080, 101, 0x222B33);
        p.rect("header", 960, 112, 1760, 128, 103, 0x2B343C);
        p.rect("header_rule", 960, 181, 1760, 1, 104, LINE);
        p.rect("identity_mark", 116, 112, 4, 65, 105, GOLD);
        p.text("identity", clipped(view.playerName(), 21), 365, 89, 30, WHITE);
        p.text("identity_sub", "수호자  /  캐릭터", 365, 138, 20, MUTED);
        p.text("tab_character", "캐릭터", 890, 110, 20, MUTED);
        p.text("tab_equipment", "장비", 1130, 110, 21, WHITE);
        p.rect("active_tab", 1130, 178, 186, 3, 105, GOLD);
        p.text("weapons_title", "무기", 240, 227, 20, WHITE);
        p.textFit("collection_title", collectionTitle(view),
                720, 227, 20, WHITE, 550);
        p.rect("collection", 720, 540, 576, 584, 103, 0x27313A);
        p.rect("slot_divider", 392, 540, 1, 564, 104, LINE);

        for (int node = 0; node < 3; node++) {
            WeaponSlot slot = SLOTS[node];
            Card equipped = view.equipped().stream().filter(c -> c.slot() == slot).findFirst().orElse(null);
            Box box = WeaponScreenLayout.bounds(node);
            p.text("slot_label_" + node, slotName(slot), 99, box.y(), 20,
                    slot == view.selectedSlot() ? GOLD : MUTED);
            card(p, node, equipped, true);
            if (slot == view.selectedSlot()) {
                p.frame("selected_category", box, 2, 122, GOLD);
                p.rect("expanded_link", 390, box.y(), 88, 1, 106, GOLD);
                p.rect("selected_tick", 151, box.y(), 3, 36, 107, GOLD);
            }
        }
        for (int node = 3; !loadoutMode && node < 12; node++) {
            int index = node - 3; // choices is the caller's current page, not the entire inventory.
            if (perkMode)
                perkCard(p, node, index < view.perks().size() ? view.perks().get(index) : null);
            else if (familyMode)
                familyCard(p, node, index < view.families().size() ? view.families().get(index) : null);
            else
                card(p, node, index < view.choices().size() ? view.choices().get(index) : null, false);
        }
        if (loadoutMode) {
            loadoutGuide(p, view);
        } else {
            button(p, WeaponScreenLayout.BACK_WEAPONS,
                    familyMode ? "로드아웃으로" : weaponMode ? "무기군으로" : "무기 선택으로", true);
            String hint = familyMode ? "무기군을 선택하세요"
                    : weaponMode ? "무기 선택 · 다음: 퍽 선택" : "퍽 선택 · 확정 전 미적용";
            p.textFit("collection_hint", hint, 720, 264, 18, MUTED, 550);
        }

        int pages = Math.max(1, view.pages());
        int page = Math.max(0, Math.min(pages - 1, view.page()));
        if (!loadoutMode) {
            button(p, WeaponScreenLayout.PREVIOUS, "<  이전", page > 0);
            button(p, WeaponScreenLayout.NEXT, "다음  >", page + 1 < pages);
            p.text("pages", (page + 1) + " / " + pages, 720, 860, 20, WHITE);
        }
        button(p, WeaponScreenLayout.CLOSE, "닫기  [Q]", true);
        if (loadoutMode) button(p, WeaponScreenLayout.TEST_ARMORY, "새 무기", true);

        if (perkMode) {
            perkDetails(p, view);
            perkControls(p, view);
        } else if (familyMode) {
            familyDetails(p, view);
        } else {
            details(p, loadoutMode ? view.perkTarget() : view.inspected(), weaponMode);
        }
        if (WeaponScreenLayout.visible(view.focus(), stage))
            p.frame("focus", WeaponScreenLayout.bounds(view.focus()), 3, 125, WHITE);

        p.rect("footer_rule", 960, 958, 1760, 1, 104, LINE);
        p.text("footer_pointer", "마우스 포인터 · WASD 선택", 465, 992, 18, MUTED);
        String action = perkMode ? "퍽 선택" : familyMode ? "무기군 선택" : weaponMode ? "다음: 퍽 선택" : "슬롯·새 무기 선택";
        p.textFit("footer_equip", "좌클릭·Space " + action + " · 우클릭·Q 닫기", 1370, 992, 18, WHITE, 800);
        if (view.message() != null && !view.message().isBlank())
            p.textFit("message", statusMessage(view.message()), 960, 1041, 20, GOLD, 1640);
        else
            p.text("footer_open", "슬롯 → 새 무기 → 무기군 → 무기 → 퍽 선택 → 로드아웃에 추가", 960, 1041, 18, MUTED);

        Box fallback = WeaponScreenLayout.bounds(WeaponScreenLayout.visible(view.focus(), stage)
                ? view.focus() : 0);
        float cursorX = Float.isFinite(view.cursorX()) ? Math.max(0, Math.min(1920, view.cursorX())) : fallback.x();
        float cursorY = Float.isFinite(view.cursorY()) ? Math.max(0, Math.min(1080, view.cursorY())) : fallback.y();
        cursor(p, cursorX, cursorY);
        p.finish();
    }

    public static void remove(ServerPlayer player) {
        for (String id : List.copyOf(DisplayHud.getHuds(player).keySet()))
            if (id.startsWith(PREFIX)) DisplayHud.removeHud(player, id);
    }

    private static void card(Painter p, int node, Card card, boolean equippedSlot) {
        Box box = WeaponScreenLayout.bounds(node); // Exact same square as the hit target and focus ring.
        String key = "node_" + node;
        int rarity = card == null ? LINE : card.exotic() ? GOLD : PURPLE;
        p.tile(key + "_base", box, 108, card == null ? 0x202930 : card.exotic() ? 0x71613A : 0x51405E, null, false);
        p.frame(key + "_edge", box, 1, 110, rarity);
        if (card == null) {
            p.rect(key + "_empty_h", box.x(), box.y() - 7, 22, 1, 111, LINE);
            p.rect(key + "_empty_v", box.x(), box.y() - 7, 1, 22, 111, LINE);
            p.text(key + "_empty", equippedSlot ? "미장착" : "빈 칸", box.x(), box.y() + 49, 20, MUTED);
            return;
        }
        p.preview(key + "_preview", card, box.x(), box.y() - 3, 112);
        p.rect(key + "_nameplate", box.x(), box.y() + 61, box.width() - 2, 32, 114, 0x262D34);
        p.textFit(key + "_name", WeaponScreenText.weapon(card.id(), card.name()),
                box.x(), box.y() + 61, 18, WHITE, 138);
        p.textFit(key + "_ammo", WeaponScreenText.ammo(card.ammo()), box.x(), box.y() - 61, 18, WHITE, 124);
        if (card.equipped()) {
            p.rect(key + "_equipped", box.x() - 66, box.y() - 61, 6, 6, 119, GOLD);
        }
    }

    private static void button(Painter p, int node, String label, boolean enabled) {
        Box box = WeaponScreenLayout.bounds(node);
        String key = "button_" + node;
        p.tile(key, box, 108, enabled ? 0x35414B : 0x283139, null, false);
        p.frame(key + "_edge", box, 1, 110, enabled ? LINE : 0x35404A);
        p.textFit(key + "_label", label, box.x(), box.y(), 20, enabled ? WHITE : MUTED, box.width() - 24);
    }

    private static String collectionTitle(WeaponScreenView view) {
        String title = switch (view.stage()) {
            case "FAMILY" -> "무기군 선택";
            case "WEAPON" -> "무기 선택 · " + selectedFamilyName(view);
            case "PERKS" -> groupName(view) + " 선택";
            default -> "로드아웃";
        };
        return slotName(view.selectedSlot()) + "  /  " + title;
    }

    private static String selectedFamilyName(WeaponScreenView view) {
        return view.families().stream().filter(family -> family.id().equals(view.selectedFamily()))
                .map(FamilyOption::name).findFirst().orElseGet(() -> WeaponScreenText.family(view.selectedFamily()));
    }

    private static void loadoutGuide(Painter p, WeaponScreenView view) {
        p.text("loadout_title", "새 무기 추가", 720, 360, 26, WHITE);
        p.text("loadout_slot", slotName(view.selectedSlot()) + " 슬롯", 720, 409, 20, GOLD);
        p.text("loadout_choose_slot", "왼쪽에서 슬롯을 선택한 뒤", 720, 465, 20, WHITE);
        p.text("loadout_new_weapon", "상단의 새 무기를 누르세요", 720, 498, 20, WHITE);
        p.text("loadout_steps", "무기군 → 무기 → 퍽 선택", 720, 588, 20, GOLD);
        p.textFit("loadout_confirm_hint", "마지막에 확정하면 슬롯에 추가됩니다", 720, 626, 18, MUTED, 530);
        p.textFit("loadout_preserve_hint", "확정 전까지 현재 장비는 유지됩니다", 720, 686, 18, MUTED, 530);
    }

    private static void familyCard(Painter p, int node, FamilyOption family) {
        Box box = WeaponScreenLayout.bounds(node);
        String key = "node_" + node;
        p.tile(key + "_base", box, 108, 0x2B353E, null, false);
        p.frame(key + "_edge", box, 1, 110, family == null ? LINE : WHITE);
        if (family == null) {
            p.text(key + "_empty", "빈 칸", box.x(), box.y(), 20, MUTED);
            return;
        }
        p.wrapped(key + "_family", family.name(), box.x(), box.y() - 36, 20, WHITE, 132, 2, 27);
        p.textFit(key + "_count", "무기 " + family.count() + "종", box.x(), box.y() + 26, 18, GOLD, 132);
        p.text(key + "_next", "무기 선택", box.x(), box.y() + 57, 18, MUTED);
    }

    private static void familyDetails(Painter p, WeaponScreenView view) {
        p.rect("detail_panel", 1440, 558, 672, 676, 103, 0x273139);
        p.rect("detail_rarity_rule", 1440, 221, 672, 3, 106, GOLD);
        p.text("detail_rarity", slotName(view.selectedSlot()) + " 슬롯", 1440, 247, 20, GOLD);
        p.text("detail_name", "무기군 선택", 1440, 285, 26, WHITE);
        int index = view.focus() - 3;
        FamilyOption hovered = index >= 0 && index < Math.min(9, view.families().size())
                ? view.families().get(index) : null;
        p.textFit("family_name", hovered == null ? "원하는 무기군을 선택하세요" : hovered.name(),
                1440, 416, 26, WHITE, 596);
        if (hovered != null)
            p.text("family_count", "선택 가능한 무기 " + hovered.count() + "종", 1440, 465, 20, GOLD);
        p.text("family_next", "다음: 무기 선택 → 퍽 선택", 1440, 561, 20, WHITE);
        p.wrapped("family_apply_hint", "마지막에 로드아웃에 추가를 눌러야 실제 장비가 변경됩니다.",
                1440, 626, 20, MUTED, 560, 2, 30);
    }

    private static void perkCard(Painter p, int node, PerkOption option) {
        Box box = WeaponScreenLayout.bounds(node);
        String key = "node_" + node;
        int accent = option == null ? LINE : option.selected() ? GOLD : option.enabled() ? WHITE : DISABLED;
        p.tile(key + "_base", box, 108, option != null && option.selected() ? 0x494432 : 0x2B353E, null, false);
        p.frame(key + "_edge", box, option != null && option.selected() ? 2 : 1, 110, accent);
        if (option == null) {
            p.text(key + "_empty", "빈 칸", box.x(), box.y(), 20, MUTED);
            return;
        }
        p.wrapped(key + "_name", optionName(option), box.x(), box.y() - 47, 20, WHITE, 132, 2, 25);
        p.text(key + "_status", perkStatus(option), box.x(), box.y() + 7, 18, accent);
        String reason = option.reason();
        if (reason == null || reason.isBlank())
            reason = option.selected() ? "초안에 저장됨" : option.enabled() ? "초안에 저장" : "이 무기와 호환되지 않음";
        p.wrapped(key + "_reason", reason, box.x(), box.y() + 36, 18,
                option.enabled() ? MUTED : DISABLED, 132, 2, 21);
    }

    private static void details(Painter p, Card card, boolean selectingWeapon) {
        p.rect("detail_panel", 1440, 558, 672, 676, 103, 0x273139);
        if (card == null) {
            p.text("detail_empty_title", selectingWeapon ? "무기 선택" : "선택한 무기 없음", 1440, 448, 26, WHITE);
            p.textFit("detail_empty_hint", selectingWeapon ? "목록에서 무기를 고르면 퍽 선택으로 이동합니다"
                    : "새 무기를 눌러 무기군부터 선택하세요", 1440, 510, 20, MUTED, 596);
            return;
        }
        int rarity = card.exotic() ? GOLD : PURPLE;
        p.rect("detail_rarity_rule", 1440, 221, 672, 3, 106, rarity);
        p.text("detail_rarity", card.exotic() ? "경이" : "전설", 1440, 247, 20, rarity);
        p.textFit("detail_name", WeaponScreenText.weapon(card.id(), card.name()),
                1440, 285, 26, WHITE, 600);
        p.textFit("detail_family", WeaponScreenText.family(card.family()), 1440, 325, 20, MUTED, 550);
        p.textFit("detail_damage", WeaponScreenText.damage(card.damage()), 1220, 371, 20, damageColor(card.damage()), 176);
        p.textFit("detail_ammo", WeaponScreenText.ammo(card.ammo()), 1650, 371, 20, ammoColor(card.ammo()), 192);
        p.preview("detail_preview", card, 1440, 411, 128);
        p.text("detail_equipped", card.inventoryIndex() < 0 ? "장착 예정 무기 · 확정 전 미적용"
                : card.equipped() ? "장착 중" : "소지 무기  /  목록에서 장착", 1440, 493, 20,
                card.equipped() ? GOLD : MUTED);
        p.textFit("detail_frame", WeaponScreenText.frame(card.frame()),
                1440, 526, 20, WHITE, 560);
        p.rect("detail_rule", 1440, 550, 596, 1, 106, LINE);
        p.text("base_stats_label", "기본 능력치", 1440, 569, 18, MUTED);
        for (int index = 0; index < STATS.length; index++) {
            String[] stat = STATS[index];
            Integer value = stat(card.stats(), stat[1], stat[2]);
            float y = 596 + index * 34;
            p.text("stat_" + index + "_name", stat[0], 1218, y, 20, MUTED);
            p.rect("stat_" + index + "_track", 1485, y, 258, 7, 108, LINE);
            if (value != null && value > 0) {
                float width = Math.min(100, value) / 100f * 258;
                p.rect("stat_" + index + "_fill", 1356 + width / 2, y, width, 7, 111, WHITE);
            }
            p.text("stat_" + index + "_value", value == null ? "—" : value.toString(), 1681, y, 20, WHITE);
        }
        p.rect("ammo_rule", 1440, 752, 596, 1, 106, LINE);
        boolean preview = card.inventoryIndex() < 0;
        p.text("magazine_label", preview ? "기본 탄창" : "탄창", 1238, 778, 20, MUTED);
        // Catalog cards have no live ammunition. Owned stacks preserve zero/overflow state exactly.
        p.text("magazine_count", preview ? Integer.toString(card.capacity())
                : card.rounds() + " / " + card.capacity(), 1512, 778, 26, WHITE);
        if (selectingWeapon)
            p.textFit("weapon_next", "다음: 퍽 선택 · 실제 장착은 마지막에 확정", 1440, 850, 20, GOLD, 596);
    }

    private static void perkControls(Painter p, WeaponScreenView view) {
        Card target = view.perkTarget();
        String identity = target == null ? "선택한 무기 없음" : WeaponScreenText.weapon(target.id(), target.name());
        p.textFit("perk_target", "장착 예정 무기 · " + identity, 1440, 756, 18, GOLD, 596);
        p.textFit("selected_damage", "데미지: " + selectedName(view.selectedDamage()), 1440, 790, 20, WHITE, 596);
        p.textFit("selected_utility", "유틸리티: " + selectedName(view.selectedUtility()), 1440, 820, 20, WHITE, 596);
        button(p, WeaponScreenLayout.CONFIRM_LOADOUT, "로드아웃에 추가", target != null);
        button(p, WeaponScreenLayout.DAMAGE_PERKS, "데미지 퍽", target != null);
        button(p, WeaponScreenLayout.UTILITY_PERKS, "유틸리티 퍽", target != null);
        if (view.perkMode()) {
            int active = "DAMAGE".equals(view.perkGroup()) ? WeaponScreenLayout.DAMAGE_PERKS : WeaponScreenLayout.UTILITY_PERKS;
            p.frame("active_perk_group", WeaponScreenLayout.bounds(active), 2, 122, GOLD);
        }
    }

    private static void perkDetails(Painter p, WeaponScreenView view) {
        p.rect("detail_panel", 1440, 558, 672, 676, 103, 0x273139);
        Card target = view.perkTarget();
        p.rect("detail_rarity_rule", 1440, 221, 672, 3, 106, GOLD);
        p.text("detail_rarity", slotName(view.selectedSlot()) + " · 장착 예정 무기", 1440, 247, 20, GOLD);
        p.textFit("detail_name", target == null ? "선택한 무기 없음"
                : WeaponScreenText.weapon(target.id(), target.name()), 1440, 285, 26, WHITE, 600);
        p.textFit("detail_family", target == null ? "뒤로 이동하여 무기를 먼저 선택하세요"
                : WeaponScreenText.family(target.family()) + " · 확정 전 미적용", 1440, 325, 20, MUTED, 596);
        p.rect("perk_detail_rule", 1440, 351, 596, 1, 106, LINE);
        p.text("perk_group", groupName(view), 1440, 378, 20, GOLD);
        int index = view.focus() - 3;
        PerkOption hovered = index >= 0 && index < Math.min(9, view.perks().size()) ? view.perks().get(index) : null;
        if (hovered == null) {
            p.wrapped("perk_hover_hint", view.perks().isEmpty() ? "이 무기에 선택 가능한 퍽이 없습니다"
                    : "퍽을 가리키면 원작 설명이 표시됩니다", 1440, 455, 20, MUTED, 560, 2, 30);
            return;
        }
        p.textFit("perk_name", optionName(hovered), 1440, 416, 26, WHITE, 596);
        p.text("perk_status", perkStatus(hovered), 1440, 456, 20,
                hovered.selected() ? GOLD : hovered.enabled() ? WHITE : DISABLED);
        String reason = hovered.reason();
        if (reason == null || reason.isBlank())
            reason = hovered.enabled() ? "장착 예정 무기의 퍽 선택 · 확정 전 미적용" : "이 무기와 호환되지 않습니다";
        p.wrapped("perk_reason", reason, 1440, 493, 20, hovered.enabled() ? MUTED : DISABLED, 596, 2, 28);
        p.text("perk_description_label", "원작 설명", 1440, 561, 20, GOLD);
        String description = hovered.description();
        if (description == null || description.isBlank())
            description = hovered.id() == null || hovered.id().isBlank()
                    ? "이 분류의 퍽 선택을 해제합니다. 다른 분류의 퍽은 유지됩니다." : "제공된 원작 설명이 없습니다.";
        p.wrapped("perk_description", description, 1440, 601, 20, WHITE, 596, 5, 28);
    }

    private static String groupName(WeaponScreenView view) {
        return "DAMAGE".equals(view.perkGroup()) ? "데미지 퍽" : "유틸리티 퍽";
    }

    private static String optionName(PerkOption option) {
        return option.name() == null || option.name().isBlank() ? "없음" : option.name();
    }

    private static String selectedName(String name) { return name.isBlank() ? "없음" : name; }

    private static String perkStatus(PerkOption option) {
        return option.selected() ? "선택됨" : option.enabled() ? "선택 가능" : "호환 불가";
    }

    private static Integer stat(Map<String, Integer> stats, String name, String hash) {
        Integer value = stats.get(name);
        return value != null ? value : stats.get(hash);
    }

    private static int damageColor(String damage) {
        return switch (title(damage)) {
            case "ARC" -> 0x7AD8F5; case "SOLAR" -> 0xF2A274; case "VOID" -> 0xB79AD9;
            case "STASIS" -> 0x82A5DF; case "STRAND" -> 0x87CFA2; default -> WHITE;
        };
    }

    private static int ammoColor(String ammo) {
        return switch (title(ammo)) {
            case "SPECIAL" -> 0x91BF9D; case "HEAVY" -> 0xB39BCB; default -> WHITE;
        };
    }

    private static String slotName(WeaponSlot slot) {
        if (slot == null) return "무기";
        return switch (slot) { case KINETIC -> "물리"; case ENERGY -> "에너지"; case POWER -> "파워"; };
    }
    /** The caller owns other status messages and supplies them already localized. */
    private static String statusMessage(String message) {
        return switch (message) {
            case "Choose an equipped slot, then a weapon you own." -> "장착 칸을 고른 뒤 소지 무기를 선택하세요";
            case "Select an owned weapon to equip." -> "장착할 소지 무기를 선택하세요";
            default -> message;
        };
    }

    private static String title(String value) {
        return value == null || value.isBlank() ? "—" : value.replace('_', ' ').toUpperCase(Locale.ROOT);
    }
    private static String clipped(String value, int max) {
        if (value == null || value.isBlank()) return "—";
        String clean = value.replaceAll("[\\p{Cntrl}§]", " ").strip();
        int count = clean.codePointCount(0, clean.length());
        return count <= max ? clean : clean.substring(0, clean.offsetByCodePoints(0, max - 1)) + "…";
    }

    private static void cursor(Painter p, float x, float y) {
        for (int i = 0; i < 16; i++) {
            double angle = i * Math.PI / 8;
            p.rect("cursor_ring_" + i, x + (float) Math.cos(angle) * 12,
                    y + (float) Math.sin(angle) * 12, 2.5f, 2.5f, 151, WHITE);
        }
        p.rect("cursor_left", x - 5, y, 4, 1, 152, WHITE);
        p.rect("cursor_right", x + 5, y, 4, 1, 152, WHITE);
        p.rect("cursor_top", x, y - 5, 1, 4, 152, WHITE);
        p.rect("cursor_bottom", x, y + 5, 1, 4, 152, WHITE);
    }

    private record Tile(Box box, float depth, int color, String weapon, boolean stretch) { }
    private record Label(String text, float x, float y, float pixels, int color) { }

    /** Cache belongs to the registered node, avoiding a separate player/session map or offline leaks. */
    private static final class Painter {
        private final ServerPlayer player;
        private final Set<String> used = new HashSet<>();

        private Painter(ServerPlayer player) { this.player = player; }

        private void rect(String key, float x, float y, float width, float height, float depth, int color) {
            tile(key, new Box(x, y, width, height), depth, color, null, false);
        }

        private void frame(String key, Box b, float thickness, float depth, int color) {
            // Inset the four painted edges into the SAME hit box, rather than enlarging the visual target.
            rect(key + "_top", b.x(), b.y() - (b.height() - thickness) / 2, b.width(), thickness, depth, color);
            rect(key + "_bottom", b.x(), b.y() + (b.height() - thickness) / 2, b.width(), thickness, depth, color);
            rect(key + "_left", b.x() - (b.width() - thickness) / 2, b.y(), thickness, b.height(), depth, color);
            rect(key + "_right", b.x() + (b.width() - thickness) / 2, b.y(), thickness, b.height(), depth, color);
        }

        private void preview(String key, Card card, float x, float y, float size) {
            if (WeaponCatalog.find(card.id()).isPresent())
                tile(key, new Box(x, y, size, size), 112, WHITE, card.id(), false);
            else
                textFit(key + "_missing", "미리 보기 없음", x, y, 18, MUTED, size - 12);
        }

        private void tile(String key, Box box, float depth, int color, String weapon, boolean stretch) {
            String id = PREFIX + key;
            used.add(id);
            Tile state = new Tile(box, depth, color, weapon, stretch);
            DisplayHud old = DisplayHud.getHud(player, id);
            if (old instanceof ItemDisplayHud && state.equals(old.getExtraData(STATE))) return;
            if (old != null && !(old instanceof ItemDisplayHud)) { old.remove(); old = null; }
            ItemDisplayHud hud = old instanceof ItemDisplayHud item ? item : new ItemDisplayHud();
            hud.updateWhenDataChanged(false);
            if (!(old != null && old.getExtraData(STATE) instanceof Tile last
                    && last.color() == color && java.util.Objects.equals(last.weapon(), weapon))) {
                ItemStack stack;
                if (weapon != null) {
                    stack = WeaponModels.create(WeaponCatalog.find(weapon).orElseThrow());
                } else {
                    stack = new ItemStack(Items.PAPER);
                    stack.set(DataComponents.ITEM_MODEL, SOLID);
                    stack.set(DataComponents.CUSTOM_MODEL_DATA,
                            new CustomModelData(List.of(), List.of(), List.of(), List.of(color)));
                }
                hud.setItem(stack);
            }
            hud.setItemTransform(weapon == null ? ItemDisplayContext.NONE : ItemDisplayContext.GUI);
            // Flatten only depth, retaining authored GUI orientation and proportions without crossing UI layers.
            hud.setScale(box.width(), box.height(), 1);
            hud.setAlignment(stretch ? DisplayHud.HudAlignment.UNALIGNED : DisplayHud.HudAlignment.CENTER);
            hud.setLocation(box.x(), box.y(), depth);
            hud.setAboveHand(true);
            hud.setViewRange(1000);
            hud.removeWhenPlayerDied(true);
            hud.setExtraData(STATE, state);
            if (old == null) hud.spawn(player, id);
            hud.update();
        }

        /** Preserve readable glyph size; shorten content instead of undersampling Hangul to fit. */
        private void textFit(String key, String text, float x, float y, float pixels, int color, float maxWidth) {
            pixels = Math.max(MIN_TEXT_PIXELS, pixels);
            text(key, ellipsized(text, pixels, maxWidth), x, y, pixels, color);
        }

        /** Fixed-size lines keep long Korean names, compatibility reasons and original text readable. */
        private void wrapped(String key, String value, float x, float y, float pixels, int color,
                float maxWidth, int maxLines, float lineHeight) {
            pixels = Math.max(MIN_TEXT_PIXELS, pixels);
            List<String> lines = wrappedLines(value, pixels, maxWidth, maxLines);
            for (int line = 0; line < lines.size(); line++)
                text(key + "_" + line, lines.get(line), x, y + line * lineHeight, pixels, color);
        }

        private static List<String> wrappedLines(String value, float pixels, float maxWidth, int maxLines) {
            String clean = value == null || value.isBlank() ? "—" : value.replace("\r\n", "\n")
                    .replace('\r', '\n').replaceAll("[\\p{Cntrl}&&[^\\n]]|§", " ").strip();
            int[] points = clean.codePoints().toArray();
            List<String> lines = new ArrayList<>();
            float budget = maxWidth / (pixels * 0.125f);
            int start = 0;
            while (start < points.length && lines.size() < maxLines) {
                while (start < points.length && Character.isWhitespace(points[start])) start++;
                if (start == points.length) break;
                if (lines.size() == maxLines - 1) {
                    lines.add(ellipsized(new String(points, start, points.length - start).replace('\n', ' '),
                            pixels, maxWidth));
                    break;
                }
                float advance = 0;
                int end = start;
                int space = -1;
                while (end < points.length && points[end] != '\n'
                        && advance + glyphAdvance(points[end]) <= budget) {
                    if (Character.isWhitespace(points[end])) space = end;
                    advance += glyphAdvance(points[end++]);
                }
                if (end < points.length && points[end] != '\n' && space > start) end = space;
                // The caller supplies widths larger than a glyph; still guarantee forward progress.
                if (end == start) end++;
                lines.add(ellipsized(new String(points, start, end - start).strip(), pixels, maxWidth));
                start = end;
            }
            return List.copyOf(lines);
        }

        private static String ellipsized(String value, float pixels, float maxWidth) {
            String clean = clipped(value, Integer.MAX_VALUE);
            int[] points = clean.codePoints().toArray();
            float budget = maxWidth / (pixels * 0.125f);
            float advance = 0;
            for (int point : points) advance += glyphAdvance(point);
            if (advance <= budget) return clean;
            // Reserve the ellipsis before copying code points, preserving Hangul and surrogate pairs.
            float remaining = Math.max(0, budget - glyphAdvance('…'));
            StringBuilder result = new StringBuilder();
            for (int point : points) {
                float width = glyphAdvance(point);
                if (width > remaining) break;
                result.appendCodePoint(point);
                remaining -= width;
            }
            return result.toString().stripTrailing() + "…";
        }

        private static int glyphAdvance(int point) {
            return point == ' ' ? 4 : point < 128 || point == '…' ? 6 : 9;
        }

        private void text(String key, String text, float x, float y, float pixels, int color) {
            // Enforce the readability floor even for labels that do not need width clipping.
            pixels = Math.max(MIN_TEXT_PIXELS, pixels);
            String id = PREFIX + key;
            used.add(id);
            Label state = new Label(text, x, y, pixels, color);
            DisplayHud old = DisplayHud.getHud(player, id);
            if (old instanceof TextDisplayHud && state.equals(old.getExtraData(STATE))) return;
            if (old != null && !(old instanceof TextDisplayHud)) { old.remove(); old = null; }
            TextDisplayHud hud = old instanceof TextDisplayHud label ? label : new TextDisplayHud();
            hud.updateWhenDataChanged(false);
            hud.setLineWidth(512);
            hud.setTextAlignment(Display.TextDisplay.Align.CENTER);
            Component component = Component.literal(text).withStyle(style -> style.withColor(color));
            hud.setText(component);
            // Keep the API's one spacer row, but not 512 spaces (which the client wraps into extra rows).
            // Public native backing-display API avoids changing the shared library or any shader/assets.
            hud.getTextDisplay().setText(Component.literal("\n").append(component));
            hud.setBackgroundColor(0);
            hud.setShadowToggle(false);
            hud.setOpacity(255);
            // Vanilla text glyphs are 8px * 0.025 display units: scale 100 means about 20 reference pixels.
            hud.setScale(pixels * 5, pixels * 5, 1);
            hud.setAlignment(DisplayHud.HudAlignment.CENTER);
            // Native spacer/baseline shifts the glyph centre up by scale/4; scale is pixels*5.
            // First-Vision PNGs confirm this 1.25*pixels displacement; preserve every logical Y.
            hud.setLocation(x, y + pixels * 1.25f, 130);
            hud.setAboveHand(true);
            hud.setViewRange(1000);
            hud.removeWhenPlayerDied(true);
            hud.setExtraData(STATE, state);
            if (old == null) hud.spawn(player, id);
            hud.update();
        }

        private void finish() {
            for (String id : List.copyOf(DisplayHud.getHuds(player).keySet()))
                if (id.startsWith(PREFIX) && !used.contains(id)) DisplayHud.removeHud(player, id);
        }
    }
}
