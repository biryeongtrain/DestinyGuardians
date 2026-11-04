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

import java.util.ArrayList;
import java.util.List;

/**
 * W301 opening class picker: three augment-style cards (emblem, name, role, blurb, class ability) drawn with
 * the display HUD in the 1920x1080 reference space, plus header, keycap footer and a dark vignette.
 * Pure presentation: {@link OpeningScan.ClassChoice} owns the input and the selected index.
 *
 * <pre>
 *  open      cards rise in one after another (3-tick stagger, 6-tick slide)
 *  select    highlighted card lifts and grows; halo in the class colour; others sit under a dark veil
 *  confirm   flash on the chosen card, the others drop away; {@link #OUTRO} ticks later everything is removed
 * </pre>
 * Textures come from scripts/art/build_rg_class_cards_w301.py.
 */
final class ClassCardHud {
    static final int OUTRO = 30;
    private static final String PREFIX = "destiny:rg_class_";
    private static final float CARD_W = 307, CARD_H = 422, CY = 580, PITCH = 370;
    private static final float GLOW_W = CARD_W * (296f / 256f), GLOW_H = CARD_H * (392f / 352f);
    private static final int WHITE = 0xF1F3F5, GREY = 0xA9B4C0, MUTED = 0x6E7884, CYAN = 0x6FD6F0;

    record Info(String key, String name, int color, String role, List<String> blurb, String abilityIcon, String ability) { }

    static final List<Info> CLASSES = List.of(
            new Info("titan", "타이탄", 0xE57575, "투사 · 도시의 방벽",
                    List.of("강철 같은 의지로 전선을", "지키는 수호자. 방벽을 세워", "아군을 지키고 돌격합니다."),
                    "titan_barricade", "방벽"),
            new Info("hunter", "헌터", 0x79B9DF, "개척자 · 변경의 사냥꾼",
                    List.of("위험을 두려워하지 않는", "변경의 사냥꾼. 민첩한 회피와", "정밀한 사격으로 싸웁니다."),
                    "dodge", "회피"),
            new Info("warlock", "워록", 0xEDCE79, "학자 · 빛의 탐구자",
                    List.of("빛의 비밀을 탐구하는", "전투 학자. 균열을 열어 아군을", "치유하고 빛을 휘두릅니다."),
                    "warlock_rift", "균열"));

    private final ServerPlayer player;
    private final int opened;
    private int confirmedAt = -1, shownIndex = -1;
    private final int[] spawnedAt = {-1, -1, -1};
    private final List<String> ids = new ArrayList<>();

    ClassCardHud(ServerPlayer player, int now) {
        this.player = player;
        this.opened = now;
        sprite("backdrop", "rg_class_backdrop", 960, 540, 1920, 1080, 1, 0xFFFFFF, 0);
        text("header_label", "고스트 · 신원 스캔 완료", 960, 268, 14, CYAN, 0);
        text("header_title", "당신은… 누구입니까?", 960, 304, 30, WHITE, 0);
        sprite("header_line", "rg_line", 960, 334, 560, 8, 5, CYAN, 0);
        float y = 852;
        sprite("key_a", "rg_key", 819, y, 40, 40, 5, 0xFFFFFF, 0);
        text("key_a_t", "A", 819, y, 16, WHITE, 0);
        sprite("key_d", "rg_key", 867, y, 40, 40, 5, 0xFFFFFF, 0);
        text("key_d_t", "D", 867, y, 16, WHITE, 0);
        text("key_sel", "선택", 921, y, 16, GREY, 0);
        sprite("key_space", "rg_key_wide", 1017, y, 120, 40, 5, 0xFFFFFF, 0);
        text("key_space_t", "SPACE", 1017, y, 15, WHITE, 0);
        text("key_ok", "결정", 1107, y, 16, GREY, 0);
    }

    /** Called every tick while the picker is up (and through the outro). */
    void tick(int now, int index, boolean confirmed) {
        int age = now - opened;
        if (confirmed && confirmedAt < 0) confirm(now, index);
        if (shownIndex < 0) shownIndex = index;
        for (int i = 0; i < 3 && confirmedAt < 0; i++) {
            if (spawnedAt[i] < 0 && age >= i * 3) {
                spawnedAt[i] = now;
                layout(i, i == shownIndex, 0, 60, 0); // spawn low...
            } else if (spawnedAt[i] >= 0 && now - spawnedAt[i] == 1) {
                layout(i, i == shownIndex, 0, 0, 6); // ...then slide up (separate tick so the client interpolates)
            }
        }
        if (confirmedAt < 0 && index != shownIndex) {
            shownIndex = index;
            for (int i = 0; i < 3; i++) if (spawnedAt[i] >= 0) layout(i, i == index, 0, 0, 3);
        }
        if (confirmedAt >= 0) {
            int t = now - confirmedAt;
            if (t == 3) remove("c" + index + "_flash");
            if (t == 8) for (int i = 0; i < 3; i++) if (i != index) removeCard(i);
            if (t == 16) layout(index, true, 0, -6, 6);
        }
    }

    boolean done(int now) { return confirmedAt >= 0 && now - confirmedAt >= OUTRO; }

    private void confirm(int now, int index) {
        confirmedAt = now;
        shownIndex = index;
        Info info = CLASSES.get(index);
        layout(index, true, 0, -24, 4, 1.09f);
        float cx = 960 + (index - 1) * PITCH;
        sprite("c" + index + "_flash", "rg_class_flash", cx, CY - 24, CARD_W * 1.09f, CARD_H * 1.09f, 150, info.color(), 4);
        for (int i = 0; i < 3; i++) if (i != index) layout(i, false, 0, 90, 8);
        text("header_title", info.name() + " — " + info.role().substring(0, info.role().indexOf(' ')), 960, 304, 30, info.color(), 0);
        for (String k : List.of("key_a", "key_a_t", "key_d", "key_d_t", "key_sel", "key_space", "key_space_t", "key_ok")) remove(k);
    }

    private void layout(int i, boolean selected, float dx, float dy, int time) {
        layout(i, selected, dx, dy, time, selected ? 1.05f : 0.97f);
    }

    /** Positions every element of card i around its centre: scale s about the centre, lifted when selected. */
    private void layout(int i, boolean selected, float dx, float dy, int time, float s) {
        Info info = CLASSES.get(i);
        float cx = 960 + (i - 1) * PITCH + dx;
        float cy = CY + dy + (selected ? -16 : 0);
        String c = "c" + i + "_";
        if (selected) sprite(c + "glow", "rg_class_glow", cx, cy, GLOW_W * s, GLOW_H * s, 2, info.color(), time);
        else remove(c + "glow");
        // Unselected cards are dimmed by tint (a translucent veil on top depth-occludes the card in the client).
        sprite(c + "card", "rg_class_card_" + info.key(), cx, cy, CARD_W * s, CARD_H * s, 3, selected ? 0xFFFFFF : 0x9A9A9A, time);
        sprite(c + "icon", "rg_class_icon_" + info.key(), cx, cy - 89 * s, 108 * s, 108 * s, 5,
                selected ? 0xFFFFFF : info.color(), time);
        text(c + "name", info.name(), cx, cy + 6 * s, 40 * s, selected ? WHITE : 0xC8CDD3, time, true);
        text(c + "role", info.role(), cx, cy + 46 * s, 17 * s, info.color(), time, false);
        for (int l = 0; l < info.blurb().size(); l++)
            text(c + "blurb" + l, info.blurb().get(l), cx, cy + (98 + l * 25) * s, 16 * s, GREY, time, false);
        String ability = "직업 능력  " + info.ability();
        float textW = width(ability) * 15 * s * .125f;
        float iconX = cx - (textW + 30 * s) / 2 + 12 * s;
        sprite(c + "ability_icon", info.abilityIcon(), iconX, cy + 186 * s, 24 * s, 24 * s, 5, info.color(), time);
        text(c + "ability", ability, iconX + 18 * s + textW / 2, cy + 186 * s, 15 * s, MUTED + 0x202020, time, false);
    }

    private void removeCard(int i) {
        String c = PREFIX + "c" + i + "_";
        for (String id : List.copyOf(ids)) if (id.startsWith(c)) { DisplayHud.removeHud(player, id); ids.remove(id); }
    }

    void close() {
        if (player.hasDisconnected()) { ids.clear(); return; }
        for (String id : ids) DisplayHud.removeHud(player, id);
        ids.clear();
    }

    private static int width(String s) {
        int w = 0;
        for (int p : s.codePoints().toArray()) w += p == ' ' ? 4 : p < 128 ? 6 : 9;
        return w;
    }

    private void remove(String key) {
        String id = PREFIX + key;
        if (ids.remove(id)) DisplayHud.removeHud(player, id);
    }

    private void sprite(String key, String image, float x, float y, float w, float h, float z, int color, int time) {
        String id = PREFIX + key;
        DisplayHud existing = DisplayHud.getHud(player, id);
        ItemDisplayHud hud = existing instanceof ItemDisplayHud item ? item : new ItemDisplayHud();
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
        if (fresh) { hud.spawn(player, id); if (!ids.contains(id)) ids.add(id); }
        hud.updateWhenDataChanged(true);
        hud.update();
    }

    private void text(String key, String value, float x, float y, float px, int color, int time) {
        text(key, value, x, y, px, color, time, false);
    }

    private void text(String key, String value, float x, float y, float px, int color, int time, boolean bold) {
        String id = PREFIX + key;
        DisplayHud existing = DisplayHud.getHud(player, id);
        TextDisplayHud hud = existing instanceof TextDisplayHud t ? t : new TextDisplayHud();
        hud.updateWhenDataChanged(false);
        hud.setLineWidth(512);
        hud.setTextAlignment(Display.TextDisplay.Align.CENTER);
        Component component = Component.literal(value).withStyle(st -> st.withColor(color).withBold(bold));
        hud.setText(component);
        hud.getTextDisplay().setText(Component.literal("\n").append(component));
        hud.setBackgroundColor(0);
        hud.setShadowToggle(true);
        hud.setOpacity(255);
        boolean fresh = existing == null;
        hud.setScale(px * 5, px * 5, 1, fresh ? 0 : time);
        hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        // Native spacer/baseline: the glyph centre sits px*1.25 above the logical y (see WeaponScreenHud).
        hud.setLocation(x, y + px * 1.25f, 130, fresh ? 0 : time);
        hud.setAboveHand(true);
        hud.setViewRange(1000);
        if (fresh) { hud.spawn(player, id); if (!ids.contains(id)) ids.add(id); }
        hud.updateWhenDataChanged(true);
        hud.update();
    }
}
