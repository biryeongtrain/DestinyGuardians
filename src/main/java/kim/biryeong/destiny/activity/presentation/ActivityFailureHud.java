package kim.biryeong.destiny.activity.presentation;

import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import kim.biryeong.minigamelib.displayhud.TextDisplayHud;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.FontDescription;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Display;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import java.util.*;

/** Authored D2-style approximation; coordinates use the established 1920x1080 DisplayHud space. */
final class ActivityFailureHud {
    private final ServerPlayer player;
    private final String prefix;
    private final Set<String> ids = new HashSet<>(), used = new HashSet<>();
    private int fadeStep = 8, contentOpacity = 255;
    ActivityFailureHud(ServerPlayer player, UUID activity) {
        this.player = player; prefix = "destiny:activity_failure/" + activity + "/";
    }
    void render(boolean entry, boolean wiping, int age, int seconds, int wipeRemaining,
                kim.biryeong.destiny.activity.ActivityAttemptStats.Snapshot results) {
        used.clear();
        fadeStep = wiping ? Math.clamp(age * 8 / 20, 0, 8) : 8;
        contentOpacity = Math.round(255 * fadeStep / 8f);
        if (wiping) {
            sprite("black", age >= 20 ? "backdrop" : "black_" + fadeStep, 960, 540, 1920, 1080, 110, 0xFFFFFF);
            if (contentOpacity > 0) {
                sprite("wipe", "failure_banner", 205, 313, 410, 626, 120, 0xFFFFFF);
                left("title", "빛이 스러집니다…", 410, 110, 52, 0xF3F3EF, true);
                left("checkpoint", "마지막 체크포인트에서 다시 시작…", 410, 186, 24, 0xA4A6AA, false);
                table(results);
                text("restarting", seconds > 0 ? "재시작까지 " + seconds + "초" : "체크포인트 복구 중", 1460, 900, 24, 0xC0C4C8, false);
            }
        } else {
            // Compact marker remains after the entry notice, including the downed state.
            sprite("restricted", "restricted", 840, 124, 38, 38, 120, 0xFFFFFF);
            text("restricted_text", "부활 제한", 960, 118, 21, 0xE5E7E9, false);
            if (entry) {
                sprite("entry", "restricted", 960, 425, 110, 110, 120, 0xFFFFFF);
                text("entry_text", "부활 제한", 960, 510, 29, 0xF3F3EF, false);
            }
            if (wipeRemaining >= 0)
                text("light_fading", "빛이 사라지기까지 " + ((wipeRemaining + 19) / 20) + "초", 960, 300, 24, 0xD65A58, false);
        }
        for (String id : Set.copyOf(ids)) if (!used.contains(id)) { ids.remove(id); DisplayHud.removeHud(player, id); }
    }
    private void table(kim.biryeong.destiny.activity.ActivityAttemptStats.Snapshot results) {
        if (results == null) { left("stats_wait", "이번 시도 통계 집계 중", 410, 315, 24, 0xAAAAAA, false); return; }
        left("attempt", "이번 체크포인트 · " + results.checkpoint() + " · 시도 " + results.attempt(), 410, 266, 22, 0xC4C6C8, false);
        left("header_name", "수호자", 460, 340, 22, 0xB8BABD, false);
        text("header_kills", "처치", 1000, 340, 22, 0xB8BABD, false);
        text("header_damage", "가한 피해", 1190, 340, 22, 0xB8BABD, false);
        text("header_boss", "보스 피해", 1410, 340, 22, 0xB8BABD, false);
        text("header_deaths", "사망", 1610, 340, 22, 0xB8BABD, false);
        sprite("table_rule", "rule", 1055, 377, 1290, 1, 121, 0x737579);
        for (int n = 0; n < Math.min(6, results.rows().size()); n++) {
            var row = results.rows().get(n); boolean self = row.player().equals(player.getUUID());
            float y = 405 + n * 68;
            sprite("row_" + n, "table_row", 1055, y + 28, 1290, 56, 120,
                    self ? 0xDCCB7B : n % 2 == 0 ? 0xB8BABD : 0x71757C);
            if (self) sprite("self_" + n, "rule", 414, y + 28, 4, 56, 122, 0xD7BE69);
            String state = switch (row.presence()) { case PRESENT -> self ? " · 나" : ""; case DISCONNECTED -> " · 연결 끊김"; case LEFT -> " · 이탈"; };
            left("name_" + n, ActivityResultText.fit(row.name() + state, 25, 400), 460, y + 13, 25, 0xF2F2ED, false);
            right("kills_" + n, Long.toString(row.kills()), 1040, y + 13, 27);
            right("damage_" + n, ActivityResultText.damage(row.damage()), 1260, y + 13, 27);
            right("boss_" + n, ActivityResultText.damage(row.bossDamage()), 1480, y + 13, 27);
            right("deaths_" + n, Long.toString(row.deaths()), 1650, y + 13, 27);
        }
    }
    private void left(String key, String value, float x, float y, float size, int color, boolean bold) {
        text(key, value, x + ActivityResultText.width(value, size) / 2, y, size, color, bold);
    }
    private void right(String key, String value, float x, float y, float size) {
        text(key, value, x - ActivityResultText.width(value, size) / 2, y, size, 0xF2F2ED, false);
    }
    void clear() { for (String id : ids) DisplayHud.removeHud(player, id); ids.clear(); }
    private void sprite(String key, String image, float x, float y, float w, float h, float z, int color) {
        if (!key.equals("black") && fadeStep < 8
                && (image.equals("failure_banner") || image.equals("table_row") || image.equals("rule")))
            image += "_f0" + fadeStep;
        String id = prefix + key; used.add(id);
        DisplayHud existing = DisplayHud.getHud(player, id);
        ItemDisplayHud hud = existing instanceof ItemDisplayHud item ? item : new ItemDisplayHud();
        String state = image + ":" + x + ":" + y + ":" + w + ":" + h + ":" + color;
        if (existing != null && state.equals(hud.getExtraData("state"))) return;
        hud.updateWhenDataChanged(false);
        ItemStack stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny_activity_failure", "gui/" + image));
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(), List.of(), List.of(color)));
        hud.setItem(stack); hud.setItemTransform(ItemDisplayContext.NONE);
        hud.setScale(w, h, 1); hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        hud.setLocation(x, y, z); hud.setViewRange(1000); hud.setAboveHand(true);
        hud.setExtraData("state", state);
        if (existing == null) { hud.spawn(player, id); ids.add(id); }
        hud.updateWhenDataChanged(true); hud.update();
    }
    private void text(String key, String value, float x, float y, float px, int color, boolean bold) {
        String id = prefix + key; used.add(id);
        DisplayHud existing = DisplayHud.getHud(player, id);
        TextDisplayHud hud = existing instanceof TextDisplayHud text ? text : new TextDisplayHud();
        String state = value + ":" + x + ":" + y + ":" + px + ":" + color + ":" + contentOpacity;
        if (existing != null && state.equals(hud.getExtraData("state"))) return;
        var font = new FontDescription.Resource(Identifier.fromNamespaceAndPath("destiny", "rg_objective_" + (bold ? "bold" : "medium")));
        Component component = Component.literal(value).withStyle(s -> s.withFont(font).withColor(color));
        hud.updateWhenDataChanged(false); hud.setLineWidth(2000);
        hud.setTextAlignment(Display.TextDisplay.Align.CENTER); hud.setText(component);
        hud.getTextDisplay().setText(Component.literal("\n").append(component));
        hud.setBackgroundColor(0); hud.setShadowToggle(true); hud.setOpacity(Math.max(4, contentOpacity), 0);
        hud.setScale(px * 2, px * 2, 1); hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        hud.setLocation(x, y + px * 1.2f, 130); hud.setAboveHand(true); hud.setViewRange(1000);
        hud.setExtraData("state", state);
        if (existing == null) { hud.spawn(player, id); ids.add(id); }
        hud.updateWhenDataChanged(true); hud.update();
    }
}
