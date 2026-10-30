package kim.biryeong.destiny.hud;

import kim.biryeong.destiny.input.ClientControls;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.TextDisplayHud;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Display;

/** Key guides in the existing combat cluster's 1920x1080 reference coordinates. */
final class AbilityKeyHud {
    private static final float TEXT_PIXELS = 14;
    private static final int COLOR = 0xD1D6DC;
    private static final String STATE = "ability_key_state";

    private record Label(String text, float x, float y, boolean aboveHand) { }

    private AbilityKeyHud() { }

    static void update(ServerPlayer player) {
        boolean gcb = ClientControls.gcb(player);
        // All IDs inherit CombatHud's ability/super prefixes, so both remove() and
        // removeAbilities() clean up every line on menus, death, spectator or class loss.
        key(player, CombatHud.ABILITIES_ID, 104, gcb ? "Z" : "F", "");
        key(player, CombatHud.ABILITIES_ID + "_1", 174, gcb ? "C" : "Shift+", gcb ? "" : "좌클릭");
        key(player, CombatHud.ABILITIES_ID + "_2", 244, gcb ? "V" : "Shift+", gcb ? "" : "Shift");
        // Diamond ends at y=896; the next row's tiles begin at y=921.5.
        text(player, CombatHud.SUPER_ID + "_key", gcb ? "F" : "Shift+F", 120, 910);
    }

    private static void key(ServerPlayer player, String id, float x, String first, String second) {
        // Charge bars end at y=982. Split long fallback chords instead of shrinking
        // Korean text: each line fits within 63px on a 70px pitch at this text size.
        // Rightmost label ends by x=275.5 (ammo starts at x=284); bottom ends at y=1023.
        // The 18px row pitch leaves 4px between nominal 14px glyph boxes.
        text(player, id + "_key", first, x, 998);
        if (second.isEmpty()) DisplayHud.removeHud(player, id + "_key_2");
        else text(player, id + "_key_2", second, x, 1016);
    }

    private static void text(ServerPlayer player, String id, String value, float x, float y) {
        boolean aboveHand = !player.getOffhandItem().isEmpty();
        Label state = new Label(value, x, y, aboveHand);
        DisplayHud existing = DisplayHud.getHud(player, id);
        if (existing instanceof TextDisplayHud && state.equals(existing.getExtraData(STATE))) return;
        if (existing != null && !(existing instanceof TextDisplayHud)) {
            DisplayHud.removeHud(player, id);
            existing = null;
        }
        TextDisplayHud hud = existing instanceof TextDisplayHud label ? label : new TextDisplayHud();
        hud.updateWhenDataChanged(false);
        hud.setLineWidth(128);
        hud.setTextAlignment(Display.TextDisplay.Align.CENTER);
        Component component = Component.literal(value).withStyle(style -> style.withColor(COLOR));
        hud.setText(component);
        // Match WeaponScreenHud's single spacer row without the library's wrapping
        // space padding. Keep each visible row separate so its baseline is predictable.
        hud.getTextDisplay().setText(Component.literal("\n").append(component));
        hud.setBackgroundColor(0);
        hud.setShadowToggle(false);
        hud.setOpacity(255);
        hud.setScale(TEXT_PIXELS * 5, TEXT_PIXELS * 5, 1);
        hud.setAlignment(DisplayHud.HudAlignment.LEFT);
        hud.setLocation(x, y + TEXT_PIXELS * 1.25f, 3);
        hud.setAboveHand(aboveHand);
        hud.setViewRange(1000);
        hud.removeWhenPlayerDied(true);
        hud.setExtraData(STATE, state);
        if (existing == null) hud.spawn(player, id);
        hud.updateWhenDataChanged(true);
        hud.update();
    }
}
