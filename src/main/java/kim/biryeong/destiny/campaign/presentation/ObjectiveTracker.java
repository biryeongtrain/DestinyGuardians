package kim.biryeong.destiny.campaign.presentation;

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

import java.util.*;

/** Mission tracker using the supplied Korean objective HUD layers and original Noto Sans KR glyphs.
 * Coordinates follow hud/layout.json in 1920x1080 reference pixels. Progress and controls extend below
 * that source card; the source itself does not establish Minecraft animation or projection fidelity.
 */
public final class ObjectiveTracker {
    private static final String P = "destiny:objective_tracker/";
    private static final int WHITE = 0xF2F4F7, GREY = 0xA9B2BC, DIM = 0x8A939C, GOLD = 0xF2C14E, DONE = 0xB8C2CC,
            DARK = 0x05080C;
    private static final float TOP = 220;
    private static final Map<UUID, Set<String>> SHOWN = new HashMap<>();
    private static final Map<UUID, String> LAST_OBJECTIVE = new HashMap<>();

    public record View(String mission, String step, String objective, int count, int goal,
                       String key, String action, String toastTitle, String toastSub, boolean hidden) { }

    private ObjectiveTracker() { }

    public static void render(ServerPlayer p, View v) {
        var used = new HashSet<String>();
        if (v.hidden()) { finish(p, used); return; }
        var f = new Frame(p, used);
        String sig = v.step() + "|" + v.objective();
        boolean changed = !sig.equals(LAST_OBJECTIVE.put(p.getUUID(), sig));
        int slide = changed ? 7 : 0;
        boolean counted = v.goal() > 1;
        boolean done = v.goal() > 0 && v.count() >= v.goal();
        // Exact supplied layer positions: header (0,8), badge (48,0), guide (59,43), box (73,66).
        f.sprite("header", "rg_objective_header", 256, TOP + 24.5f, 512, 33, 20, 0xFFFFFF, 256, 0);
        f.sprite("shield", "rg_objective_shield", 78, TOP + 30, 60, 60, 22, 0xFFFFFF, 78, 0);
        f.label("mission", v.mission(), WHITE, true, 116, TOP + 15, 20, 0);
        var lines = ObjectiveTypography.wrap(v.objective(), 380, 20);
        float extra = (lines.size() - 1) * 28;
        f.sprite("guide", "rg_objective_guide", 79, TOP + 75.5f + extra / 2, 40, 65 + extra, 20,
                0xFFFFFF, 79, 0);
        f.sprite("box", done ? "rg_objective_box_done" : "rg_objective_box", 79, TOP + 72, 12, 12, 21,
                done ? GOLD : 0xFFFFFF, 43, slide);
        for (int i = 0; i < lines.size(); i++)
            f.label("objective_" + i, lines.get(i), done ? DONE : WHITE, false, 116, TOP + 65 + i * 28, 20, slide);
        float y = TOP + 108 + extra;
        if (counted) {
            int pct = Math.round(100f * Math.clamp(v.count(), 0, v.goal()) / v.goal());
            f.label("progress", pct + "%", done ? DONE : WHITE, false, 116, y, 20, slide);
            y += 32;
        }
        if (v.key() != null) {
            float kw = ObjectiveTypography.width(v.key(), 17, true) + 20;
            f.sprite("key_cap", "rg_objective_key", 116 + kw / 2, y + 16, kw, 32, 21, 0xFFFFFF, 116 + kw / 2, 0);
            f.label("key_label", v.key(), WHITE, true, 126, y + 7, 17, 0);
            float actionX = 116 + kw + 12;
            // Long bindings keep the instruction on a separate row instead of squeezing/overlapping it.
            if (ObjectiveTypography.width(v.action() == null ? "" : v.action(), 18, false) > 512 - actionX) {
                actionX = 116;
                y += 38;
            }
            var actions = ObjectiveTypography.wrap(v.action() == null ? "" : v.action(), 512 - actionX, 18);
            for (int i = 0; i < actions.size(); i++)
                f.label("key_action_" + i, actions.get(i), GREY, false, actionX, y + 6 + i * 25, 18, 0);
        }

        if (v.toastTitle() != null) {
            f.sprite("toast_bg", "crucible_banner", 960, 230, 820, 110, 20, DARK, 960, 0);
            f.sprite("toast_line", "crucible_line", 960, 276, 520, 3, 22, GOLD, 960, 0);
            f.text("toast_title", bold(v.toastTitle(), GOLD), 960, 200, 36, Display.TextDisplay.Align.CENTER, 960, 0);
            f.text("toast_sub", c(v.toastSub() == null ? "" : v.toastSub(), GREY), 960, 244, 21, Display.TextDisplay.Align.CENTER, 960, 0);
        }
        finish(p, used);
    }

    public static void remove(ServerPlayer p) {
        var old = SHOWN.remove(p.getUUID());
        LAST_OBJECTIVE.remove(p.getUUID());
        if (old != null) for (String id : old) DisplayHud.removeHud(p, id);
        for (String id : List.copyOf(DisplayHud.getHuds(p).keySet())) if (id.startsWith(P)) DisplayHud.removeHud(p, id);
    }

    private static void finish(ServerPlayer p, Set<String> used) {
        var old = SHOWN.put(p.getUUID(), used);
        if (old != null) for (String id : old) if (!used.contains(id)) DisplayHud.removeHud(p, id);
    }

    private static Component c(String s, int color) { return Component.literal(s).withColor(color); }
    private static Component bold(String s, int color) { return Component.literal(s).withStyle(st -> st.withColor(color).withBold(true)); }

    private record Frame(ServerPlayer p, Set<String> used) {
        void sprite(String id, String image, float x, float y, float w, float h, float z, int color, float fromX, int slide) {
            String full = P + id; used.add(full);
            String shape = image + ":" + color + ":" + w + ":" + h + ":" + z;
            DisplayHud existing = DisplayHud.getHud(p, full);
            if (existing instanceof ItemDisplayHud item && shape.equals(existing.getExtraData("shape"))) {
                String pos = x + "," + y;
                if (slide > 0) { item.setLocation(fromX, y, z); item.update(); item.setLocation(x, y, z, slide); item.setExtraData("pos", pos); item.update(); }
                else if (!pos.equals(existing.getExtraData("pos"))) { item.setLocation(x, y, z); item.setExtraData("pos", pos); item.update(); }
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
            hud.setAboveHand(true);
            boolean slideIn = slide > 0 && fromX != x;
            hud.setLocation(slideIn ? fromX : x, y, z);
            hud.setViewRange(1000);
            hud.setExtraData("shape", shape); hud.setExtraData("pos", x + "," + y);
            hud.spawn(p, full);
            hud.updateWhenDataChanged(true);
            hud.update();
            if (slideIn) { hud.setLocation(x, y, z, slide); hud.update(); }
        }

        /** Pixel metrics are shared with the generated bitmap providers; no language-width guess. */
        void label(String id, String value, int color, boolean bold, float x, float y, float size, int slide) {
            float half = ObjectiveTypography.width(value, size, bold) / 2;
            text(id, ObjectiveTypography.text(value, color, bold), x + half, y, size,
                    Display.TextDisplay.Align.CENTER, x + half - 36, slide, true);
        }

        /** Legacy toast text retains the existing centred Minecraft typography. */
        void text(String id, Component value, float x, float y, float size, Display.TextDisplay.Align align, float fromX, int slide) {
            text(id, value, x, y, size, align, fromX, slide, false);
        }

        void text(String id, Component value, float x, float y, float size, Display.TextDisplay.Align align,
                  float fromX, int slide, boolean bitmap) {
            float anchorY = y + (bitmap ? size * 1.2f : size * 1.25f);
            String full = P + id; used.add(full);
            String state = value.getString() + ":" + value.toString().hashCode() + ":" + size;
            DisplayHud existing = DisplayHud.getHud(p, full);
            if (existing instanceof TextDisplayHud text && state.equals(existing.getExtraData("shape"))) {
                String pos = x + "," + y;
                if (!pos.equals(existing.getExtraData("pos"))) { text.setLocation(x, anchorY, 30); text.setExtraData("pos", pos); text.update(); }
                return;
            }
            if (existing != null) DisplayHud.removeHud(p, full);
            TextDisplayHud hud = new TextDisplayHud();
            hud.updateWhenDataChanged(false);
            hud.setLineWidth(2000);
            hud.setTextAlignment(Display.TextDisplay.Align.CENTER);
            hud.setText(value);
            hud.getTextDisplay().setText(Component.literal("\n").append(value));
            hud.setBackgroundColor(0); hud.setShadowToggle(true); hud.setOpacity(255);
            hud.setScale(size * (bitmap ? 2 : 5), size * (bitmap ? 2 : 5), 1);
            hud.setAlignment(DisplayHud.HudAlignment.CENTER);
            hud.setAboveHand(true);
            boolean slideIn = slide > 0 && fromX != x;
            hud.setLocation(slideIn ? fromX : x, anchorY, 30);
            hud.setViewRange(1000);
            hud.setExtraData("shape", state); hud.setExtraData("pos", x + "," + y);
            hud.spawn(p, full);
            hud.updateWhenDataChanged(true);
            hud.update();
            if (slideIn) { hud.setLocation(x, anchorY, 30, slide); hud.update(); }
        }
    }
}
