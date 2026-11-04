package kim.biryeong.destiny.campaign.presentation;

import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import kim.biryeong.minigamelib.displayhud.TextDisplayHud;
import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Display;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import java.util.List;

/** Strike-owned subtitle rows, using the Korean bitmap font and its measured advances. */
public final class DevilsSubtitles {
    private static final String PREFIX = "destiny:devils_subtitle/";
    private DevilsSubtitles() { }

    /** Called for the current clip, including after a world-ready acknowledgement/reconnect. */
    public static void render(ServerPlayer player, String speaker, String text) {
        // Noto Sans KR bitmap metrics, in the shared 1920x1080 HUD coordinate space.
        // 32px retains readable glyphs even in the 854x480 verification window.
        var rows = ObjectiveTypography.wrap(text, 1280, 32);
        float top = 940 - rows.size() * 42;
        label(player, "speaker", speaker, true, 0xFFFFFF, top - 38, 26);
        for (int i = 0; i < rows.size(); i++) label(player, "row" + i, rows.get(i), false, 0xFFFFFF, top + i * 42, 32);
        for (String id : java.util.List.copyOf(DisplayHud.getHuds(player).keySet())) {
            String rowPrefix = id.startsWith(PREFIX + "background/row") ? PREFIX + "background/row" : PREFIX + "row";
            if (!id.startsWith(rowPrefix)) continue;
            String index = id.substring(rowPrefix.length());
            if (!index.matches("[0-9]+") || Integer.parseInt(index) >= rows.size()) DisplayHud.removeHud(player, id);
        }
    }
    public static void remove(ServerPlayer player) {
        for (String id : java.util.List.copyOf(DisplayHud.getHuds(player).keySet()))
            if (id.startsWith(PREFIX)) DisplayHud.removeHud(player, id);
    }
    private static void label(ServerPlayer player, String key, String text, boolean bold, int color, float y, float size) {
        background(player, key, ObjectiveTypography.width(text, size, bold) + 24, y + size * .5f, size + 10);
        String id = PREFIX + key;
        String shape = text + ":" + bold + ":" + y + ":" + size;
        var old = DisplayHud.getHud(player, id);
        if (old != null && shape.equals(old.getExtraData("shape"))) return;
        if (old != null) DisplayHud.removeHud(player, id);
        var value = ObjectiveTypography.text(text, color, bold);
        var hud = new TextDisplayHud();
        hud.updateWhenDataChanged(false);
        hud.setLineWidth(4000);
        hud.setTextAlignment(Display.TextDisplay.Align.CENTER);
        hud.setText(value);
        hud.getTextDisplay().setText(Component.literal("\n").append(value));
        // TextDisplay background shares the flattened HUD depth and can cover its own glyphs.
        // The separate plate below has an explicit depth behind the white text.
        hud.setBackgroundColor(0);
        hud.setShadowToggle(false);
        hud.setOpacity(255);
        hud.setScale(size * 2, size * 2, 1);
        hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        hud.setAboveHand(true);
        hud.setLocation(960, y + size * 1.2f, 30);
        hud.setViewRange(1000);
        hud.setExtraData("shape", shape);
        hud.spawn(player, id);
        hud.updateWhenDataChanged(true);
        hud.update();
    }
    private static void background(ServerPlayer player, String key, float width, float y, float height) {
        String id = PREFIX + "background/" + key;
        String shape = width + ":" + y + ":" + height;
        var old = DisplayHud.getHud(player, id);
        if (old != null && shape.equals(old.getExtraData("shape"))) return;
        if (old != null) DisplayHud.removeHud(player, id);
        var hud = new ItemDisplayHud();
        hud.updateWhenDataChanged(false);
        var stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_MODEL, DestinyGuardians.id("gui/hud/solid"));
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(), List.of(), List.of(0)));
        hud.setItem(stack);
        hud.setItemTransform(ItemDisplayContext.NONE);
        hud.setScale(width, height, 1);
        hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        hud.setAboveHand(true);
        hud.setLocation(960, y, 25);
        hud.setViewRange(1000);
        hud.setExtraData("shape", shape);
        hud.spawn(player, id);
        hud.updateWhenDataChanged(true);
        hud.update();
    }
}
