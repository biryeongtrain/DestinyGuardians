package kim.biryeong.destiny.inventory;

import kim.biryeong.destiny.inventory.WeaponScreenLayout.Box;
import kim.biryeong.destiny.inventory.WeaponScreenView.Card;
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
        p.text("collection_title", slotName(view.selectedSlot()) + "  /  소지 무기", 720, 227, 20, WHITE);
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
        for (int node = 3; node < 12; node++) {
            int index = node - 3; // choices is the caller's current page, not the entire inventory.
            card(p, node, index < view.choices().size() ? view.choices().get(index) : null, false);
        }
        if (view.choices().isEmpty())
            p.text("empty_collection", "이 분류에 여분의 소지 무기가 없습니다", 720, 925, 20, MUTED);
        else
            p.text("collection_hint", "장착할 무기를 선택하세요", 720, 925, 20, MUTED);

        int pages = Math.max(1, view.pages());
        int page = Math.max(0, Math.min(pages - 1, view.page()));
        button(p, WeaponScreenLayout.PREVIOUS, "<  이전", page > 0);
        button(p, WeaponScreenLayout.NEXT, "다음  >", page + 1 < pages);
        button(p, WeaponScreenLayout.CLOSE, "닫기  [Q]", true);
        p.text("pages", (page + 1) + " / " + pages, 720, 860, 20, WHITE);

        details(p, view.inspected());
        if (view.focus() >= 0 && view.focus() < WeaponScreenLayout.NODE_COUNT)
            p.frame("focus", WeaponScreenLayout.bounds(view.focus()), 3, 125, WHITE);

        p.rect("footer_rule", 960, 958, 1760, 1, 104, LINE);
        p.text("footer_pointer", "마우스 포인터 · WASD 선택", 465, 992, 18, MUTED);
        p.text("footer_equip", "좌클릭·Space 장착 · 우클릭·Q 닫기", 1370, 992, 18, WHITE);
        p.text("footer_open", "열기: /destiny inventory 또는 웅크리기+Q", 960, 1041, 18, MUTED);
        if (view.message() != null && !view.message().isBlank())
            p.textFit("message", statusMessage(view.message()), 1440, 918, 20, GOLD, 600);

        Box fallback = WeaponScreenLayout.bounds(view.focus() >= 0 && view.focus() < WeaponScreenLayout.NODE_COUNT
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
        p.text(key + "_label", label, box.x(), box.y(), 20, enabled ? WHITE : 0x7E8991);
    }

    private static void details(Painter p, Card card) {
        p.rect("detail_panel", 1440, 558, 672, 676, 103, 0x273139);
        if (card == null) {
            p.text("detail_empty_title", "선택한 무기 없음", 1440, 448, 25, WHITE);
            p.text("detail_empty_hint", "분류를 고른 뒤 소지 무기를 선택하세요", 1440, 510, 20, MUTED);
            return;
        }
        int rarity = card.exotic() ? GOLD : PURPLE;
        p.rect("detail_rarity_rule", 1440, 221, 672, 3, 106, rarity);
        p.text("detail_rarity", card.exotic() ? "경이" : "전설", 1440, 247, 20, rarity);
        p.textFit("detail_name", WeaponScreenText.weapon(card.id(), card.name()),
                1440, 290, 26, WHITE, 600);
        p.textFit("detail_family", WeaponScreenText.family(card.family()), 1440, 332, 20, MUTED, 550);
        p.textFit("detail_damage", WeaponScreenText.damage(card.damage()), 1220, 382, 20, damageColor(card.damage()), 176);
        p.textFit("detail_ammo", WeaponScreenText.ammo(card.ammo()), 1650, 382, 20, ammoColor(card.ammo()), 192);
        p.preview("detail_preview", card, 1440, 437, 208);
        p.text("detail_equipped", card.equipped() ? "장착 중" : "소지 무기  /  목록에서 장착", 1440, 512, 20,
                card.equipped() ? GOLD : MUTED);
        p.textFit("detail_frame", WeaponScreenText.frame(card.frame()),
                1440, 548, 20, WHITE, 560);
        p.rect("detail_rule", 1440, 576, 596, 1, 106, LINE);
        p.text("base_stats_label", "기본 능력치", 1440, 590, 18, MUTED);
        for (int index = 0; index < STATS.length; index++) {
            String[] stat = STATS[index];
            Integer value = stat(card.stats(), stat[1], stat[2]);
            float y = 609 + index * 39;
            p.text("stat_" + index + "_name", stat[0], 1218, y, 20, MUTED);
            p.rect("stat_" + index + "_track", 1485, y, 258, 7, 108, LINE);
            if (value != null && value > 0) {
                float width = Math.min(100, value) / 100f * 258;
                p.rect("stat_" + index + "_fill", 1356 + width / 2, y, width, 7, 111, WHITE);
            }
            p.text("stat_" + index + "_value", value == null ? "—" : value.toString(), 1681, y, 20, WHITE);
        }
        p.rect("ammo_rule", 1440, 796, 596, 1, 106, LINE);
        p.text("magazine_label", "탄창", 1238, 830, 20, MUTED);
        // Real projected state, including overflow magazines and zero-round states; never catalog defaults.
        p.text("magazine_count", card.rounds() + " / " + card.capacity(), 1512, 831, 26, WHITE);
        Integer cadence = stat(card.stats(), "rpm", "4284893193");
        if (cadence != null && cadence > 0)
            p.text("cadence", "분당 발사 수 " + cadence, 1440, 875, 20, MUTED);
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
