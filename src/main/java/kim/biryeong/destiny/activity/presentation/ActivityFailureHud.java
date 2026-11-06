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
    ActivityFailureHud(ServerPlayer player, UUID activity) {
        this.player = player; prefix = "destiny:activity_failure/" + activity + "/";
    }
    void render(boolean entry, boolean wiping, int age, int seconds, int wipeRemaining) {
        used.clear();
        if (wiping) {
            sprite("black", age >= 24 ? "backdrop" : "black_" + Math.min(8, age / 3), 960, 540, 1920, 1080, 110, 0xFFFFFF);
            if (age >= 6) {
                sprite("wipe", "wipe", 960, 570, 470, 470, 120, 0xFFFFFF);
                text("title", "당신의 빛이 사라집니다…", 590, 150, 43, 0xF3F3EF, true);
                text("checkpoint", "마지막 체크포인트에서 다시 시작합니다…", 590, 206, 25, 0xC0C4C8, false);
                text("restarting", seconds > 0 ? "재시작까지 " + seconds + "초" : "체크포인트 복구 중", 960, 930, 24, 0xC0C4C8, false);
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
    void clear() { for (String id : ids) DisplayHud.removeHud(player, id); ids.clear(); }
    private void sprite(String key, String image, float x, float y, float w, float h, float z, int color) {
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
        String state = value + ":" + x + ":" + y + ":" + px + ":" + color;
        if (existing != null && state.equals(hud.getExtraData("state"))) return;
        var font = new FontDescription.Resource(Identifier.fromNamespaceAndPath("destiny", "rg_objective_" + (bold ? "bold" : "medium")));
        Component component = Component.literal(value).withStyle(s -> s.withFont(font).withColor(color));
        hud.updateWhenDataChanged(false); hud.setLineWidth(2000);
        hud.setTextAlignment(Display.TextDisplay.Align.CENTER); hud.setText(component);
        hud.getTextDisplay().setText(Component.literal("\n").append(component));
        hud.setBackgroundColor(0); hud.setShadowToggle(true); hud.setOpacity(255);
        hud.setScale(px * 2, px * 2, 1); hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        hud.setLocation(x, y + px * 1.2f, 130); hud.setAboveHand(true); hud.setViewRange(1000);
        hud.setExtraData("state", state);
        if (existing == null) { hud.spawn(player, id); ids.add(id); }
        hud.updateWhenDataChanged(true); hud.update();
    }
}
