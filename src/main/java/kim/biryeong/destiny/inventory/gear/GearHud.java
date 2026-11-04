package kim.biryeong.destiny.inventory.gear;

import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.inventory.HudPainter;
import kim.biryeong.destiny.inventory.PlayerFigure;
import kim.biryeong.destiny.inventory.WeaponScreenLayout.Box;
import kim.biryeong.destiny.inventory.WeaponScreenText;
import kim.biryeong.destiny.inventory.WeaponScreenView;
import kim.biryeong.destiny.inventory.gear.GearLayout.Stage;
import net.minecraft.server.level.ServerPlayer;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Draws a {@link GearView}. Display only: no input, ownership or equipment decisions live here. */
public final class GearHud {
    public static final String PREFIX = "destiny:gear_";
    static final int WHITE = 0xF2F2EE, MUTED = 0x9AA3AA, DIM = 0x5D666E, LINE = 0x3A434B, PANEL = 0x161B20,
            BACK = 0x0E1318, LEGENDARY = 0x522F65, EXOTIC = 0xCEAE33, UNCOMMON = 0x366F42, RARE = 0x5076A3,
            UP = 0x6FD08A, DOWN = 0xE0645A, GOLD = 0xE3C46B;
    static final float TIP_W = 520;

    private GearHud() { }

    public static void remove(ServerPlayer player) { HudPainter.clear(player, PREFIX); }

    public static void render(ServerPlayer player, GearView v) {
        var p = new HudPainter(player, PREFIX);
        p.backdrop("backdrop", 100, BACK);
        // Soft vignette: nested low-contrast steps read as a radial light behind the Guardian.
        for (int i = 0; i < 6; i++) {
            float w = 1320 - i * 170, h = 900 - i * 110;
            p.rect("vignette_" + i, 960, 580, w, h, 101 + i * .1f, mix(BACK, 0x1E2730, (i + 1) / 6f));
        }
        header(p, v);
        switch (v.stage()) {
            case GEAR -> gear(p, v);
            case DETAIL -> detail(p, v);
            case SUBCLASS, OPTIONS -> subclass(p, v);
        }
        footer(p, v);
        cursor(p, v);
        p.finish();
    }

    private static void header(HudPainter p, GearView v) {
        var cls = v.guardianClass();
        String icon = classIcon(cls);
        if (icon != null) p.icon("class_icon", icon, 96, 92, 64, 110, classColor(cls));
        p.textLeft("name", v.playerName(), 146, 74, 30, WHITE, 600, 255);
        var c = v.character();
        p.textLeft("class_line", c.className() + "  ·  " + c.subclassName(), 146, 112, 20, MUTED, 600, 255);
        p.textRight("tab", v.stage() == Stage.SUBCLASS || v.stage() == Stage.OPTIONS ? "하위직업" : "캐릭터", 1860, 80, 26, WHITE, 255);
        p.rect("header_rule", 960, 150, 1760, 1, 104, LINE);
    }

    // ---------------------------------------------------------------- gear

    private static void gear(HudPainter p, GearView v) {
        guardian(p, v);
        for (var slot : GearSlot.values()) slot(p, v, slot);
        if (v.expanded() != null && v.expanded().weapon() != null) storage(p, v, v.expanded());
        if (v.focus() >= 0 && v.focus() < GearLayout.STORAGE + GearLayout.STORAGE_COUNT) {
            Box b = focusBox(v);
            if (b != null) p.frame("focus", b, 3, 125, WHITE);
        }
        if (v.tooltip() != null) tooltip(p, v, v.tooltip(), v.compare(), tooltipLeft(v));
        else if (v.focus() >= 0 && v.focus() < GearLayout.SLOT_COUNT) staticTooltip(p, v, GearSlot.values()[v.focus()]);
        if (v.armory()) button(p, "armory", GearLayout.armory(), "테스트 무기고", v.focus() == GearLayout.ARMORY);
    }

    private static Box focusBox(GearView v) {
        int f = v.focus();
        if (f < GearLayout.SLOT_COUNT) return GearLayout.slot(GearSlot.values()[f]);
        return v.expanded() == null ? null : GearLayout.storage(v.expanded(), f - GearLayout.STORAGE);
    }

    /**
     * The Guardian in the centre: the player's own skinned body in a relaxed stance, turned slightly like the
     * character screen, over the faint class emblem.
     */
    private static void guardian(HudPainter p, GearView v) {
        String icon = classIcon(v.guardianClass());
        if (icon != null) p.icon("guardian_emblem", icon, 960, 500, 420, 102, dim(classColor(v.guardianClass()), .16f));
        p.rect("guardian_floor", 960, 905, 460, 2, 103, LINE);
        // Holds the weapon under the cursor (preview, as in Destiny), otherwise the equipped kinetic weapon.
        var kinetic = v.bucket(kim.biryeong.destiny.weapon.WeaponSlot.KINETIC);
        var held = v.tooltip() != null ? v.tooltip() : kinetic == null ? null : kinetic.equipped();
        PlayerFigure.draw(p, p.player(), "guardian", 960, 900, 640, 104, -34, PlayerFigure.Pose.STANDING,
                held == null ? null : kim.biryeong.destiny.weapon.WeaponModels.create(held.entry()), held == null ? "" : held.entry().id());
    }

    private static void slot(HudPainter p, GearView v, GearSlot slot) {
        Box b = GearLayout.slot(slot);
        String k = "slot_" + slot.name().toLowerCase(Locale.ROOT);
        switch (slot) {
            case SUBCLASS -> {
                var c = v.character();
                int color = elementColor(c.subclass());
                p.rect(k + "_bg", b.x(), b.y(), b.width(), b.height(), 108, c.subclass().isEmpty() ? 0x1E262E : dim(color, .3f));
                String icon = subclassIcon(c.subclass());
                if (icon != null) p.icon(k + "_icon", icon, b.x(), b.y(), 92, 112, color);
                else p.text(k + "_empty", "미선택", b.x(), b.y(), 18, MUTED);
            }
            case KINETIC, ENERGY, POWER -> {
                var bucket = v.bucket(slot.weapon());
                var w = bucket == null ? null : bucket.equipped();
                weaponTile(p, k, b, w, 108);
            }
            case GHOST -> {
                var g = GearSamples.ghost();
                p.rect(k + "_bg", b.x(), b.y(), b.width(), b.height(), 108, rarity(g.rarity()));
                p.icon(k + "_icon", g.icon(), b.x(), b.y(), b.width() - 4, 112, 0xFFFFFF);
            }
            default -> {
                var item = GearSamples.armor(v.guardianClass(), slot);
                if (item.isPresent()) {
                    p.rect(k + "_bg", b.x(), b.y(), b.width(), b.height(), 108, rarity(item.get().rarity()));
                    p.icon(k + "_icon", item.get().icon(), b.x(), b.y(), b.width() - 4, 112, 0xFFFFFF);
                } else {
                    p.rect(k + "_bg", b.x(), b.y(), b.width(), b.height(), 108, 0x1E262E);
                    p.text(k + "_empty", slot.label(), b.x(), b.y(), 18, DIM);
                }
            }
        }
        p.frame(k + "_edge", b, 1, 114, 0x6B747C);
    }

    private static void weaponTile(HudPainter p, String k, Box b, GearItems.Weapon w, float depth) {
        if (w == null) {
            p.rect(k + "_bg", b.x(), b.y(), b.width(), b.height(), depth, 0x161C22);
            p.rect(k + "_plus_h", b.x(), b.y(), 24, 1, depth + 1, LINE);
            p.rect(k + "_plus_v", b.x(), b.y(), 1, 24, depth + 1, LINE);
            return;
        }
        p.rect(k + "_bg", b.x(), b.y(), b.width(), b.height(), depth, w.exotic() ? dim(EXOTIC, .55f) : LEGENDARY);
        p.rect(k + "_shade", b.x(), b.y() + b.height() * .32f, b.width(), b.height() * .36f, depth + .5f, w.exotic() ? dim(EXOTIC, .42f) : 0x452856);
        p.weapon(k + "_model", w.id(), b.x(), b.y() - 4, b.width() * .92f, depth + 2);
        p.icon(k + "_damage", "ammo_damage_" + w.damage().toLowerCase(Locale.ROOT), b.x() - b.width() / 2 + 14, b.y() + b.height() / 2 - 14, 18, depth + 4, damageColor(w.damage()));
    }

    private static void storage(HudPainter p, GearView v, GearSlot slot) {
        var bucket = v.bucket(slot.weapon());
        var stored = bucket == null ? List.<GearItems.Weapon>of() : bucket.stored();
        Box first = GearLayout.storage(slot, 0), last = GearLayout.storage(slot, 8);
        float cx = (first.x() + last.x()) / 2, cy = (first.y() + last.y()) / 2;
        p.rect("grid_panel", cx, cy, Math.abs(last.x() - first.x()) + GearLayout.CELL + 24, Math.abs(last.y() - first.y()) + GearLayout.CELL + 24, 106, 0x12171C);
        for (int i = 0; i < GearLayout.STORAGE_COUNT; i++) {
            Box b = GearLayout.storage(slot, i);
            weaponTile(p, "cell_" + i, b, i < stored.size() ? stored.get(i) : null, 108);
            p.frame("cell_" + i + "_edge", b, 1, 114, i < stored.size() ? 0x6B747C : 0x262E36);
        }
        p.textLeft("grid_label", slot.label() + "  " + stored.size() + " / " + GearLayout.STORAGE_COUNT,
                Math.min(first.x(), last.x()) - GearLayout.CELL / 2, Math.min(first.y(), last.y()) - GearLayout.CELL / 2 - 26, 18, MUTED, 340, 255);
    }

    private static float tooltipLeft(GearView v) {
        boolean left = v.expanded() == null || v.expanded().left() || (v.focus() >= 0 && v.focus() < 5);
        return left ? 1036 : 364;
    }

    // ---------------------------------------------------------------- tooltip

    private record Row(float height, java.util.function.Consumer<Float> draw) { }

    private static void tooltip(HudPainter p, GearView v, GearItems.Weapon w, GearItems.Weapon compare, float left) {
        float top = 176, x0 = left + 24, x1 = left + TIP_W - 24;
        int head = w.exotic() ? EXOTIC : LEGENDARY;
        var rows = new ArrayList<Row>();
        if (!w.flavour().isBlank()) {
            var lines = HudPainter.wrap(w.flavour(), 18, TIP_W - 48, 3);
            rows.add(new Row(lines.size() * 26 + 14, y -> {
                for (int i = 0; i < lines.size(); i++) p.textLeft("tip_flavour_" + i, lines.get(i), x0, y + i * 26, 18, MUTED, TIP_W - 48, 255);
            }));
            rows.add(rule(p, "tip_rule0", left));
        }
        rows.add(new Row(40, y -> {
            p.icon("tip_damage", "ammo_damage_" + w.damage().toLowerCase(Locale.ROOT), x0 + 12, y + 8, 26, 132, damageColor(w.damage()));
            p.textLeft("tip_damage_name", WeaponScreenText.damage(w.damage()), x0 + 34, y, 22, damageColor(w.damage()), 200, 255);
            p.textRight("tip_ammo", WeaponScreenText.ammo(w.ammo()) + "  ·  탄창 " + w.magazine(), x1, y, 20, WHITE, 255);
        }));
        rows.add(rule(p, "tip_rule1", left));
        var base = compare == null ? null : compare.statMap();
        int i = 0;
        for (var stat : w.stats()) {
            int index = i++;
            Integer other = base == null ? null : base.get(stat.name());
            rows.add(new Row(27, y -> statRow(p, "tip_stat_" + index, stat, other, x0, x1, y)));
        }
        if (!w.perks().isEmpty()) {
            rows.add(rule(p, "tip_rule2", left));
            rows.add(new Row(30, y -> p.textLeft("tip_perks_title", "특성  ·  " + w.frame(), x0, y, 18, MUTED, TIP_W - 48, 255)));
            int j = 0;
            for (var perk : w.perks()) {
                int index = j++;
                rows.add(new Row(30, y -> {
                    p.rect("tip_perk_" + index + "_dot", x0 + 8, y + 10, 10, 10, 132, WHITE);
                    p.textLeft("tip_perk_" + index, perk.name(), x0 + 24, y, 20, WHITE, TIP_W - 72, 255);
                }));
            }
        }
        rows.add(rule(p, "tip_rule3", left));
        rows.add(new Row(30, y -> p.textLeft("tip_hint", w.equipped() ? "장착 중  ·  F 상세 보기" : "좌클릭 장착  ·  F 상세 보기", x0, y, 18, GOLD, TIP_W - 48, 255)));
        float bodyTop = top + 104, h = 16;
        for (var r : rows) h += r.height();
        p.rect("tip_head", left + TIP_W / 2, top + 52, TIP_W, 104, 120, head);
        p.weapon("tip_icon", w.id(), left + 58, top + 52, 84, 124);
        p.textLeft("tip_name", w.name(), left + 110, top + 22, 28, WHITE, TIP_W - 130, 255);
        p.textLeft("tip_type", w.family() + "  ·  " + (w.exotic() ? "경이" : "전설") + (w.equipped() ? "  ·  장착 중" : ""),
                left + 110, top + 62, 20, w.exotic() ? 0xFFF3CF : 0xD9C9E3, TIP_W - 130, 255);
        p.rect("tip_body", left + TIP_W / 2, bodyTop + h / 2, TIP_W, h, 120, PANEL);
        float y = bodyTop + 12;
        for (var r : rows) { r.draw().accept(y); y += r.height(); }
    }

    private static Row rule(HudPainter p, String key, float left) {
        return new Row(14, y -> p.rect(key, left + TIP_W / 2, y + 6, TIP_W - 48, 1, 124, LINE));
    }

    static void statRow(HudPainter p, String k, GearItems.Stat stat, Integer other, float x0, float x1, float y) {
        p.textLeft(k + "_name", stat.name(), x0, y, 18, MUTED, 170, 255);
        int color = other == null || other == stat.value() ? WHITE : stat.value() > other ? UP : DOWN;
        p.textRight(k + "_value", Integer.toString(stat.value()), x1, y, 18, color, 255);
        if (!stat.bar()) return;
        float tx = x0 + 190, tw = x1 - 50 - tx, ty = y + 9;
        p.rect(k + "_track", tx + tw / 2, ty, tw, 6, 124, 0x2C343B);
        int v = Math.clamp(stat.value(), 0, 100);
        if (other == null || other == stat.value()) {
            p.rect(k + "_fill", tx + tw * v / 200f, ty, Math.max(1, tw * v / 100f), 6, 126, WHITE);
            return;
        }
        int o = Math.clamp(other, 0, 100), low = Math.min(v, o), high = Math.max(v, o);
        p.rect(k + "_fill", tx + tw * low / 200f, ty, Math.max(1, tw * low / 100f), 6, 126, WHITE);
        p.rect(k + "_delta", tx + tw * (low + high) / 200f, ty, Math.max(1, tw * (high - low) / 100f), 6, 126, v > o ? UP : DOWN);
    }

    /** Non-weapon slots: name card only (armour and ghost are not connected to gameplay yet). */
    private static void staticTooltip(HudPainter p, GearView v, GearSlot slot) {
        String name, type, flavour; int head;
        if (slot == GearSlot.SUBCLASS) {
            var c = v.character();
            name = c.subclassName(); type = c.className() + " 하위직업"; flavour = "선택하면 직업·하위직업·능력을 바꿉니다."; head = dim(elementColor(c.subclass()), .55f);
        } else if (slot == GearSlot.GHOST) {
            var g = GearSamples.ghost(); name = g.name(); type = g.type() + "  ·  고급"; flavour = g.flavour(); head = UNCOMMON;
        } else if (slot.armor()) {
            var item = GearSamples.armor(v.guardianClass(), slot);
            if (item.isEmpty()) return;
            name = item.get().name(); type = item.get().type() + "  ·  전설"; flavour = item.get().flavour(); head = LEGENDARY;
        } else return;
        float left = slot.left() ? 1036 : 364, top = 176;
        p.rect("tip_head", left + TIP_W / 2, top + 52, TIP_W, 104, 120, head);
        p.textLeft("tip_name", name, left + 24, top + 22, 28, WHITE, TIP_W - 48, 255);
        p.textLeft("tip_type", type, left + 24, top + 62, 20, 0xD9C9E3, TIP_W - 48, 255);
        var lines = HudPainter.wrap(flavour, 18, TIP_W - 48, 4);
        String note = slot.armor() || slot == GearSlot.GHOST ? "외형 표시 전용 · 능력치 미적용" : "좌클릭 하위직업 화면";
        float h = 24 + lines.size() * 26 + 44;
        p.rect("tip_body", left + TIP_W / 2, top + 104 + h / 2, TIP_W, h, 120, PANEL);
        for (int i = 0; i < lines.size(); i++) p.textLeft("tip_flavour_" + i, lines.get(i), left + 24, top + 116 + i * 26, 18, MUTED, TIP_W - 48, 255);
        p.textLeft("tip_hint", note, left + 24, top + 116 + lines.size() * 26 + 10, 18, GOLD, TIP_W - 48, 255);
    }

    // ---------------------------------------------------------------- detail

    private static void detail(HudPainter p, GearView v) {
        var w = v.detail();
        if (w == null) return;
        p.rect("detail_stage", 700, 560, 1100, 820, 102, 0x141A20);
        p.weapon("detail_model", w.id(), 680, 540, 700, 110);
        p.textLeft("detail_name", w.name(), 180, 200, 40, w.exotic() ? EXOTIC : WHITE, 900, 255);
        p.textLeft("detail_type", w.family() + "  ·  " + (w.exotic() ? "경이" : "전설") + "  ·  " + WeaponScreenText.damage(w.damage()),
                180, 252, 22, MUTED, 900, 255);
        if (!w.flavour().isBlank()) p.wrappedLeft("detail_flavour", w.flavour(), 180, 860, 20, MUTED, 1000, 2, 30, 255);
        float left = 1300, x0 = left + 24, x1 = left + 540;
        p.rect("detail_panel", left + 282, 560, 564, 800, 104, PANEL);
        p.textLeft("detail_stats", "능력치", x0, 182, 22, WHITE, 400, 255);
        float y = 222;
        int i = 0;
        for (var stat : w.stats()) { statRow(p, "detail_stat_" + i++, stat, null, x0, x1, y); y += 27; }
        p.rect("detail_rule", left + 282, y + 8, 516, 1, 106, LINE);
        y += 24;
        p.textLeft("detail_perks", "특성  ·  " + w.frame(), x0, y, 22, WHITE, 500, 255);
        y += 38;
        int j = 0;
        for (var perk : w.perks()) {
            p.rect("detail_perk_" + j + "_dot", x0 + 8, y + 10, 10, 10, 112, WHITE);
            p.textLeft("detail_perk_" + j, perk.name(), x0 + 24, y, 20, WHITE, 480, 255);
            int lines = p.wrappedLeft("detail_perk_" + j + "_desc", perk.description(), x0 + 24, y + 28, 18, MUTED, 480, 3, 24, 255);
            y += 36 + lines * 24; j++;
            if (y > 900) break;
        }
        if (w.perks().isEmpty()) p.textLeft("detail_perks_none", "이 무기에는 선택된 특성이 없습니다.", x0, y, 18, MUTED, 500, 255);
        p.textLeft("detail_bound", "특성은 이 무기에 귀속되어 바꿀 수 없습니다.", x0, 930, 18, DIM, 500, 255);
        button(p, "back", GearLayout.back(), "뒤로", v.focus() == GearLayout.BACK);
    }

    // ---------------------------------------------------------------- subclass

    private static void subclass(HudPainter p, GearView v) {
        var c = v.character();
        int color = elementColor(c.subclass());
        for (int i = 0; i < v.fields().size() && i < GearLayout.FIELD_COUNT; i++) {
            var f = v.fields().get(i);
            Box b = GearLayout.field(i);
            boolean selected = v.stage() == Stage.OPTIONS && f.id().equals(v.field());
            p.rect("field_" + i, b.x(), b.y(), b.width(), b.height(), 108, selected ? dim(color, .4f) : 0x1B2228);
            p.rect("field_" + i + "_mark", b.x() - b.width() / 2 + 3, b.y(), 4, b.height() - 16, 110, selected ? color : LINE);
            p.textLeft("field_" + i + "_name", f.name(), b.x() - b.width() / 2 + 22, b.y() - 30, 18, MUTED, b.width() - 40, 255);
            p.textLeft("field_" + i + "_value", f.value(), b.x() - b.width() / 2 + 22, b.y() - 4, 22, f.enabled() ? WHITE : DIM, b.width() - 40, 255);
            if (v.focus() == GearLayout.FIELD + i) p.frame("field_focus", b, 3, 125, WHITE);
        }
        String icon = subclassIcon(c.subclass());
        if (v.stage() == Stage.SUBCLASS) {
            if (icon != null) p.icon("subclass_emblem", icon, 960, 520, 360, 104, dim(color, .7f));
            p.text("subclass_name", c.subclassName(), 960, 760, 40, color);
            p.text("subclass_hint", "왼쪽 항목을 골라 바꿉니다. 선택은 즉시 적용됩니다.", 960, 820, 20, MUTED);
        } else {
            p.textLeft("options_title", fieldTitle(v), 668, 190, 24, WHITE, 600, 255);
            for (int i = 0; i < v.options().size() && i < GearLayout.STORAGE_COUNT; i++) {
                var o = v.options().get(i);
                Box b = GearLayout.option(i);
                p.rect("option_" + i, b.x(), b.y(), b.width(), b.height(), 108, o.selected() ? dim(color, .45f) : 0x1B2228);
                p.frame("option_" + i + "_edge", b, 1, 110, o.selected() ? color : LINE);
                var lines = HudPainter.wrap(o.name(), 20, b.width() - 24, 3);
                for (int l = 0; l < lines.size(); l++) p.text("option_" + i + "_name_" + l, lines.get(l), b.x(), b.y() - 14 * lines.size() + l * 28, 20, o.enabled() ? WHITE : DIM);
                if (o.selected()) p.text("option_" + i + "_on", "장착 중", b.x(), b.y() + 60, 18, GOLD);
                if (v.focus() == GearLayout.STORAGE + i) p.frame("option_focus", b, 3, 125, WHITE);
            }
            int f = v.focus() - GearLayout.STORAGE;
            var focused = f >= 0 && f < v.options().size() ? v.options().get(f) : null;
            p.rect("option_panel", 1600, 560, 520, 720, 104, PANEL);
            if (focused != null) {
                p.textLeft("option_name", focused.name(), 1364, 230, 28, WHITE, 470, 255);
                p.wrappedLeft("option_desc", focused.description(), 1364, 290, 20, MUTED, 470, 12, 30, 255);
                p.wrappedLeft("option_reason", focused.reason(), 1364, 720, 18, focused.enabled() ? DIM : DOWN, 470, 4, 26, 255);
            }
        }
        button(p, "back", GearLayout.back(), "뒤로", v.focus() == GearLayout.BACK);
    }

    private static String fieldTitle(GearView v) {
        return v.fields().stream().filter(f -> f.id().equals(v.field())).map(WeaponScreenView.CharacterField::name).findFirst().orElse("") + " 선택";
    }

    // ---------------------------------------------------------------- shared bits

    private static void footer(HudPainter p, GearView v) {
        p.rect("footer_rule", 960, 990, 1760, 1, 104, LINE);
        String hint = switch (v.stage()) {
            case GEAR -> "마우스 · WASD 이동    좌클릭 · Space 선택    F 상세    우클릭 · E 닫기";
            case DETAIL -> "F · 우클릭 뒤로    E 닫기";
            default -> "좌클릭 · Space 선택    우클릭 뒤로    E 닫기";
        };
        p.textLeft("footer_hint", hint, 290, 1008, 18, MUTED, 1100, 255);
        if (!v.message().isBlank()) p.text("message", v.message(), 960, 950, 22, GOLD);
        button(p, "close", GearLayout.close(), "닫기  [E]", v.focus() == GearLayout.CLOSE);
    }

    private static void button(HudPainter p, String k, Box b, String label, boolean focused) {
        p.rect("btn_" + k, b.x(), b.y(), b.width(), b.height(), 108, focused ? 0x3A4650 : 0x232B32);
        p.frame("btn_" + k + "_edge", b, focused ? 2 : 1, 110, focused ? WHITE : LINE);
        p.textFit("btn_" + k + "_label", label, b.x(), b.y() - 2, 20, WHITE, b.width() - 20);
    }

    /** The mouse pointer: moved by the client every frame from the live view rotation (see HudPainter#pointer). */
    private static void cursor(HudPainter p, GearView v) {
        p.pointer("cursor", "gear_cursor", v.cursorX(), v.cursorY(), 30, 152, v.cursorYaw(), v.cursorPitch());
    }

    static int mix(int a, int b, float t) {
        int r = Math.round(((a >> 16) & 255) + (((b >> 16) & 255) - ((a >> 16) & 255)) * t);
        int g = Math.round(((a >> 8) & 255) + (((b >> 8) & 255) - ((a >> 8) & 255)) * t);
        int bl = Math.round((a & 255) + ((b & 255) - (a & 255)) * t);
        return r << 16 | g << 8 | bl;
    }

    static int rarity(String r) {
        return switch (r == null ? "" : r) {
            case "EXOTIC" -> EXOTIC; case "RARE" -> RARE; case "UNCOMMON" -> UNCOMMON; case "COMMON" -> 0x6E6A66;
            default -> LEGENDARY;
        };
    }

    static int dim(int color, float k) {
        int r = Math.round(((color >> 16) & 255) * k), g = Math.round(((color >> 8) & 255) * k), b = Math.round((color & 255) * k);
        return r << 16 | g << 8 | b;
    }

    static int damageColor(String damage) {
        return switch (damage == null ? "" : damage) {
            case "ARC" -> 0x7AECF3; case "SOLAR" -> 0xF2721B; case "VOID" -> 0xB185DF; case "STASIS" -> 0x4D88FF;
            case "STRAND" -> 0x35E366; default -> 0xF2F2EE;
        };
    }

    static int elementColor(String element) {
        return switch (element == null ? "" : element) {
            case "ARC" -> 0x80D9F3; case "SOLAR" -> 0xFFAA63; case "VOID" -> 0xB695FF; default -> 0x9AA3AA;
        };
    }

    static String subclassIcon(String element) {
        return switch (element == null ? "" : element) {
            case "ARC" -> "subclass_arc_w248"; case "SOLAR" -> "subclass_solar_w248"; case "VOID" -> "subclass_void_w248"; default -> null;
        };
    }

    static String classIcon(GuardianClass cls) {
        return switch (cls) { case HUNTER -> "class_hunter_w248"; case TITAN -> "class_titan_w248"; case WARLOCK -> "class_warlock_w248"; default -> null; };
    }

    static int classColor(GuardianClass cls) {
        return switch (cls) { case HUNTER -> 0x79B9DF; case TITAN -> 0xE57575; case WARLOCK -> 0xEDCE79; default -> MUTED; };
    }
}
