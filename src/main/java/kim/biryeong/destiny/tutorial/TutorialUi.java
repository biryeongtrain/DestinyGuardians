package kim.biryeong.destiny.tutorial;

import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import kim.biryeong.minigamelib.displayhud.TextDisplayHud;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;

import java.util.*;

/**
 * Destiny-style tutorial HUD in 1920x1080 reference pixels: a left objective tracker, a centred button
 * prompt, the Ghost's subtitle line, a stage toast and a choice inspector. Each frame declares the ids it
 * needs; stale ids are removed. Shares the Crucible banner/line sprites.
 */
final class TutorialUi {
    private static final String P = "destiny:tutorial_ui/";
    static final int WHITE = 0xF4F6F8, GREY = 0xA9B2BC, DARK = 0x05080C, GOLD = 0xF2C14E, GHOST = 0x8FE3FF, DONE = 0x7BD88F;
    private static final Map<UUID, Set<String>> SHOWN = new HashMap<>();

    record Objective(String text, int count, int goal) {
        boolean done() { return count >= goal; }
    }
    record Choice(String name, String icon, int color, String blurb, float progress) { }
    record Toast(String title, String sub, int color) { }
    record View(String chapter, int index, int total, String title, List<Objective> objectives,
                String keyLabel, String keyAction, String ghost, Toast toast, Choice choice, boolean compact) { }

    private TutorialUi() { }

    static void render(ServerPlayer p, View v) {
        var used = new HashSet<String>();
        var f = new Frame(p, used);
        if (v.compact()) { finish(p, used); return; }
        // Objective tracker (left).
        int rows = v.objectives().size();
        float panelH = 96 + rows * 38;
        float top = 250;
        f.sprite("obj_bg", "crucible_banner", 300, top + panelH / 2, 500, panelH, 20, DARK);
        f.sprite("obj_line", "crucible_line", 300, top + 66, 440, 3, 21, GOLD);
        f.text("obj_chapter", c("◆ " + v.chapter() + "  ·  " + v.index() + "/" + v.total(), GREY), 300, top + 14, 18, 460, 30);
        f.text("obj_title", bold(v.title(), WHITE), 300, top + 38, 26, 460, 30);
        for (int i = 0; i < rows; i++) {
            var o = v.objectives().get(i);
            String box = o.goal() == 0 ? "" : o.done() ? "■ " : "□ ";
            String progress = o.goal() > 1 ? "  " + Math.min(o.count(), o.goal()) + "/" + o.goal() : "";
            f.text("obj_" + i, c(box + o.text() + progress, o.goal() == 0 ? GREY : o.done() ? DONE : WHITE), 300, top + 84 + i * 38, 21, 460, 30);
        }
        if (!v.compact()) {
            // Prompts live under the tracker: the first-person weapon owns the lower-right and centre.
            float y = top + panelH + 18;
            if (v.keyLabel() != null) {
                f.sprite("key_bg", "crucible_banner", 300, y + 26, 500, 52, 20, DARK);
                f.text("key", Component.empty().append(bold("[ " + v.keyLabel() + " ]", GOLD)).append(c("  " + v.keyAction(), WHITE)), 300, y + 14, 22, 480, 30);
                y += 64;
            }
            if (v.ghost() != null) {
                var wrapped = wrap(v.ghost(), 22);
                int lines = wrapped.size();
                float h = 44 + lines * 28;
                f.sprite("ghost_bg", "crucible_banner", 300, y + h / 2, 500, h, 20, DARK);
                f.sprite("ghost_line", "crucible_line", 62, y + h / 2, 3, h - 12, 21, GHOST);
                f.text("ghost_name", bold("◇ 고스트", GHOST), 300, y + 8, 18, 460, 30);
                // Text displays grow upward from their anchor: anchor the last line, not the first.
                f.text("ghost", c(String.join("\n", wrapped), WHITE), 300, y + 34 + (lines - 1) * 27, 21, 2000, 30);
            }
            if (v.toast() != null) {
                f.sprite("toast_bg", "crucible_banner", 960, 230, 820, 110, 20, DARK);
                f.sprite("toast_line", "crucible_line", 960, 276, 520, 3, 22, v.toast().color());
                f.text("toast_title", bold(v.toast().title(), v.toast().color()), 960, 200, 36, 780, 30);
                f.text("toast_sub", c(v.toast().sub(), GREY), 960, 244, 21, 780, 30);
            }
            if (v.choice() != null) {
                var ch = v.choice();
                f.sprite("choice_bg", "crucible_banner", 1560, 520, 520, 260, 20, DARK);
                f.sprite("choice_icon", ch.icon(), 1560, 440, 92, 92, 22, ch.color());
                f.text("choice_name", bold(ch.name(), ch.color()), 1560, 500, 34, 480, 30);
                f.text("choice_blurb", c(ch.blurb(), WHITE), 1560, 548, 20, 470, 30);
                int filled = Math.round(ch.progress() * 10);
                f.text("choice_bar", c("■".repeat(filled), ch.color()).copy().append(c("□".repeat(10 - filled), GREY)), 1560, 600, 22, 470, 30);
                f.text("choice_hint", c("원 안에 머물러 선택", GREY), 1560, 630, 18, 470, 30);
            }
        }
        finish(p, used);
    }

    private static void finish(ServerPlayer p, Set<String> used) {
        var old = SHOWN.put(p.getUUID(), used);
        if (old != null) for (String id : old) if (!used.contains(id)) DisplayHud.removeHud(p, id);
    }

    static void remove(ServerPlayer p) {
        var old = SHOWN.remove(p.getUUID());
        if (old != null) for (String id : old) DisplayHud.removeHud(p, id);
        for (String id : List.copyOf(DisplayHud.getHuds(p).keySet())) if (id.startsWith(P)) DisplayHud.removeHud(p, id);
    }

    /** Greedy word wrap by display width (Hangul counts 1, ASCII about half). */
    static List<String> wrap(String text, int width) {
        var out = new ArrayList<String>();
        var line = new StringBuilder();
        float used = 0;
        for (String word : text.split(" ")) {
            float w = 0;
            for (char ch : word.toCharArray()) w += ch < 128 ? .55f : 1f;
            if (line.length() > 0 && used + .5f + w > width) { out.add(line.toString()); line.setLength(0); used = 0; }
            if (line.length() > 0) { line.append(' '); used += .5f; }
            line.append(word);
            used += w;
        }
        if (line.length() > 0) out.add(line.toString());
        return out;
    }

    private static Component c(String s, int color) { return Component.literal(s).withColor(color); }
    private static Component bold(String s, int color) { return Component.literal(s).withStyle(st -> st.withColor(color).withBold(true)); }

    private record Frame(ServerPlayer p, Set<String> used) {
        void sprite(String id, String image, float x, float y, float w, float h, float z, int color) {
            String full = P + id; used.add(full);
            String shape = image + ":" + color + ":" + w + ":" + h + ":" + z;
            DisplayHud existing = DisplayHud.getHud(p, full);
            if (existing instanceof ItemDisplayHud item && shape.equals(existing.getExtraData("shape"))) {
                String pos = x + "," + y;
                if (!pos.equals(existing.getExtraData("pos"))) { item.setLocation(x, y, z); item.setExtraData("pos", pos); item.update(); }
                return;
            }
            if (existing != null) DisplayHud.removeHud(p, full);
            ItemDisplayHud hud = new ItemDisplayHud();
            hud.updateWhenDataChanged(false);
            ItemStack stack = new ItemStack(Items.PAPER);
            stack.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "gui/hud/" + image));
            stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(), List.of(), List.of(color)));
            hud.setItem(stack);
            hud.setItemTransform(ItemDisplayContext.NONE);
            hud.setScale(w, h, 1);
            hud.setAlignment(DisplayHud.HudAlignment.CENTER);
            hud.setLocation(x, y, z);
            hud.setViewRange(1000);
            hud.setExtraData("shape", shape); hud.setExtraData("pos", x + "," + y);
            hud.spawn(p, full);
            hud.updateWhenDataChanged(true);
            hud.update();
        }

        void text(String id, Component value, float x, float y, float size, float lineWidth, float z) {
            String full = P + id; used.add(full);
            String state = value.getString() + ":" + value.toString().hashCode() + ":" + size + ":" + lineWidth + ":" + z;
            DisplayHud existing = DisplayHud.getHud(p, full);
            if (existing instanceof TextDisplayHud text && state.equals(existing.getExtraData("shape"))) {
                String pos = x + "," + y;
                if (!pos.equals(existing.getExtraData("pos"))) { text.setLocation(x, y + size * 1.25f, z); text.setExtraData("pos", pos); text.update(); }
                return;
            }
            if (existing != null) DisplayHud.removeHud(p, full);
            TextDisplayHud hud = new TextDisplayHud();
            hud.updateWhenDataChanged(false);
            hud.setLineWidth(Math.round(lineWidth));
            hud.setTextAlignment(net.minecraft.world.entity.Display.TextDisplay.Align.CENTER);
            hud.setText(value);
            hud.getTextDisplay().setText(Component.literal("\n").append(value));
            hud.setBackgroundColor(0); hud.setShadowToggle(true); hud.setOpacity(255);
            hud.setScale(size * 5, size * 5, 1);
            hud.setAlignment(DisplayHud.HudAlignment.CENTER);
            hud.setLocation(x, y + size * 1.25f, z);
            hud.setViewRange(1000);
            hud.setExtraData("shape", state); hud.setExtraData("pos", x + "," + y);
            hud.spawn(p, full);
            hud.updateWhenDataChanged(true);
            hud.update();
        }
    }
}
