package kim.biryeong.destiny.down;

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
import java.util.List;

/**
 * W303 Guardian Down HUD (1920x1080 reference space), Destiny 2 style:
 * <pre>
 *            수호자 쓰러짐                         title + crimson rule + Ghost status line
 *        ── 고스트가 빛을 모으는 중 ──
 *               ( ◎ )                             revive ring (24 segments): white = Ghost charging,
 *                                                  cyan = hold-to-revive progress; Ghost emblem pulses
 *        [SPACE] 길게 눌러 부활                    prompt appears when the Ghost is ready
 *        [SHIFT] 길게 눌러 귀환 지점에서 부활
 *   ▌☾ 처치자 · 드렉                               killer card (sigil + name)
 * </pre>
 * Textures: scripts/art/build_guardian_down_hud_w303.py. Pure presentation; {@link GuardianDown} owns state.
 */
final class GuardianDownHud {
    private static final String PREFIX = "destiny:gd_";
    static final int SEGMENTS = 24;
    private static final float RY = 742;
    private static final int WHITE = 0xF1F3F5, GREY = 0xA9B4C0, MUTED = 0x707A86, CYAN = 0x6FD6F0, CRIMSON = 0xD0414C,
            RING_DIM = 0x39424D;

    record Killer(Component name, String icon) { }
    record Frame(int age, float charge, float hold, boolean ready, boolean manual, boolean checkpoint,
                 int secondsLeft, float checkpointHold, String status) { }

    private final ServerPlayer player;
    private final Killer killer;
    private final List<String> ids = new ArrayList<>();
    private int lastRing = -1;
    private String lastRingColor = "";

    GuardianDownHud(ServerPlayer player, Killer killer) {
        this.player = player;
        this.killer = killer;
    }

    void render(Frame f) {
        int a = f.age();
        sprite("vignette", "gd_vignette", 960, 540, 1920, 1080, 1, 0xFFFFFF, 0);
        if (a >= 4) {
            text("title", "수호자 쓰러짐", 960, 150, 42, WHITE, 0, true);
            sprite("rule", "rg_line", 960, 190, a < 10 ? 120 : 620, 8, 5, CRIMSON, 8);
        }
        if (a >= 8) text("status", f.status(), 960, 214, 22, GREY, 0, false);
        if (a >= 6) {
            float pulse = 1 + .06f * (float) Math.sin(a / 5.0);
            boolean holding = f.ready() && f.hold() > 0;
            sprite("glow", "gd_glow", 960, RY, (f.ready() ? 230 : 180) * pulse, (f.ready() ? 230 : 180) * pulse, 3,
                    f.ready() ? CYAN : 0x9FB4C8, 6);
            sprite("ring_bg", "gd_ring_bg", 960, RY, 112, 112, 4, RING_DIM, 0);
            int seg = f.ready() ? Math.round(f.hold() * SEGMENTS) : Math.round(f.charge() * SEGMENTS);
            String color = f.ready() ? (holding ? "cyan" : "white") : "white";
            if (f.ready() && !holding) seg = SEGMENTS;
            if (seg != lastRing || !color.equals(lastRingColor)) {
                sprite("ring", "gd_ring_" + String.format("%02d", Math.clamp(seg, 0, SEGMENTS)), 960, RY, 112, 112, 6,
                        holding ? CYAN : f.ready() ? 0xDCE7F0 : WHITE, 0);
                lastRing = seg; lastRingColor = color;
            }
            sprite("ghost", "gd_ghost", 960, RY, 44 * pulse, 44 * pulse, 7, f.ready() ? CYAN : WHITE, 4);
        }
        if (a >= 10) prompts(f);
        if (a >= 12) killerCard(a);
    }

    private void prompts(Frame f) {
        if (!f.manual()) {
            removeAll("key_");
            remove("prompt_wait"); remove("prompt_hold"); remove("prompt_cp");
            text("prompt_auto", f.secondsLeft() > 0 ? "부활까지 " + f.secondsLeft() + "초" : "부활 중", 960, 826, 24, WHITE, 0, true);
            return;
        }
        remove("prompt_auto");
        if (!f.ready()) {
            removeAll("key_");
            remove("prompt_hold");
            remove("prompt_cp");
            text("prompt_wait", "부활 준비 중  ·  " + Math.max(1, f.secondsLeft()), 960, 826, 24, WHITE, 0, true);
            return;
        }
        remove("prompt_wait");
        sprite("key_space", "rg_key_wide", 862, 826, 120, 40, 8, f.hold() > 0 ? CYAN : 0xFFFFFF, 0);
        text("key_space_t", "SPACE", 862, 826, 15, WHITE, 0, false);
        text("prompt_hold", "길게 눌러 부활", 1036, 826, 22, WHITE, 0, true);
        if (f.checkpoint()) {
            sprite("key_shift", "rg_key_wide", 818, 874, 120, 40, 8, f.checkpointHold() > 0 ? CRIMSON : 0xFFFFFF, 0);
            text("key_shift_t", "SHIFT", 818, 874, 15, WHITE, 0, false);
            text("prompt_cp", f.checkpointHold() > 0 ? "귀환 중…" : "길게 눌러 귀환 지점에서 부활",
                    1046, 874, 19, GREY, 0, false);
        }
    }

    private void killerCard(int a) {
        float x = 960, y = 984;
        sprite("card", "gd_card", x, y, 480, 120, 9, 0xFFFFFF, 0);
        sprite("card_icon", killer.icon(), x - 180, y, 62, 62, 10, CRIMSON, 0);
        text("card_label", Component.literal("처치자"), x + 24, y - 30, 19, MUTED, 0, false);
        text("card_name", killer.name(), x + 24, y + 2, 30, WHITE, 0, true);
    }

    void revived() { removeAll(""); }

    void clear() { removeAll(""); }

    private void removeAll(String prefix) {
        for (String id : List.copyOf(ids))
            if (id.startsWith(PREFIX + prefix)) { ids.remove(id); DisplayHud.removeHud(player, id); }
    }

    private void remove(String key) {
        String id = PREFIX + key;
        if (ids.remove(id)) DisplayHud.removeHud(player, id);
    }

    private void sprite(String key, String image, float x, float y, float w, float h, float z, int color, int time) {
        String id = PREFIX + key;
        DisplayHud existing = DisplayHud.getHud(player, id);
        ItemDisplayHud hud = existing instanceof ItemDisplayHud item ? item : new ItemDisplayHud();
        String state = image + ":" + color + ":" + x + ":" + y + ":" + w + ":" + h;
        if (existing != null && state.equals(hud.getExtraData("state"))) return;
        hud.updateWhenDataChanged(false);
        String look = image + ":" + color;
        if (!look.equals(hud.getExtraData("look"))) {
            ItemStack stack = new ItemStack(Items.PAPER);
            stack.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "gui/hud/" + image));
            stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(), List.of(), List.of(color)));
            hud.setItem(stack);
            hud.setExtraData("look", look);
        }
        hud.setItemTransform(ItemDisplayContext.NONE);
        boolean fresh = existing == null;
        hud.setScale(w, h, 1, fresh ? 0 : time);
        hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        hud.setLocation(x, y, z, fresh ? 0 : time);
        hud.setViewRange(1000);
        hud.setAboveHand(true);
        hud.setExtraData("state", state);
        if (fresh) { hud.spawn(player, id); if (!ids.contains(id)) ids.add(id); }
        hud.updateWhenDataChanged(true);
        hud.update();
    }

    private void text(String key, String value, float x, float y, float px, int color, int time, boolean bold) {
        text(key, Component.literal(value), x, y, px, color, time, bold);
    }

    private void text(String key, Component value, float x, float y, float px, int color, int time, boolean bold) {
        String id = PREFIX + key;
        DisplayHud existing = DisplayHud.getHud(player, id);
        TextDisplayHud hud = existing instanceof TextDisplayHud t ? t : new TextDisplayHud();
        String state = value.getString() + ":" + value.hashCode() + ":" + color + ":" + x + ":" + y + ":" + px + ":" + bold;
        if (existing != null && state.equals(hud.getExtraData("state"))) return;
        hud.updateWhenDataChanged(false);
        hud.setLineWidth(512);
        hud.setTextAlignment(Display.TextDisplay.Align.CENTER);
        Component component = value.copy().withStyle(st -> st.withColor(color).withBold(bold));
        hud.setText(component);
        hud.getTextDisplay().setText(Component.literal("\n").append(component));
        hud.setBackgroundColor(0);
        hud.setShadowToggle(true);
        hud.setOpacity(255);
        boolean fresh = existing == null;
        hud.setScale(px * 5, px * 5, 1, fresh ? 0 : time);
        hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        hud.setLocation(x, y + px * 1.25f, 130, fresh ? 0 : time);
        hud.setAboveHand(true);
        hud.setViewRange(1000);
        hud.setExtraData("state", state);
        if (fresh) { hud.spawn(player, id); if (!ids.contains(id)) ids.add(id); }
        hud.updateWhenDataChanged(true);
        hud.update();
    }
}
