package kim.biryeong.destiny.inventory;

import com.mojang.math.Transformation;
import kim.biryeong.destiny.inventory.WeaponScreenLayout.Box;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponModels;
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
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/**
 * Shared retained-mode painter for full-screen DisplayHud menus (gear screen, vault, vendors). Coordinates are
 * centres on the 1920 x 1080 CENTER canvas. Each frame names every element it draws; {@link #finish()} removes
 * elements of this prefix that were not drawn. Unchanged elements send no packets.
 */
public final class HudPainter {
    public static final float MIN_TEXT_PIXELS = 18f;
    private static final String STATE = "hud_painter_state";
    private static final Identifier SOLID = Identifier.parse("destiny:gui/hud/solid");

    private record Tile(Box box, float depth, int color, String weapon, Identifier model, boolean stretch, float spin) { }
    private record Model(String stackKey, ItemDisplayContext context, Transformation transform) { }
    private record Label(String text, float x, float y, float pixels, int color, int opacity) { }

    private final ServerPlayer player;
    private final String prefix;
    private final Set<String> used = new HashSet<>();

    public HudPainter(ServerPlayer player, String prefix) { this.player = player; this.prefix = prefix; }

    public ServerPlayer player() { return player; }

    public static void clear(ServerPlayer player, String prefix) {
        for (String id : List.copyOf(DisplayHud.getHuds(player).keySet()))
            if (id.startsWith(prefix)) DisplayHud.removeHud(player, id);
    }

    public void rect(String key, float x, float y, float width, float height, float depth, int color) {
        paint(key, new Box(x, y, width, height), depth, color, null, null, false, 0);
    }

    public void backdrop(String key, float depth, int color) {
        paint(key, new Box(960, 540, 1920, 1080), depth, color, null, null, true, 0);
    }

    public void frame(String key, Box b, float thickness, float depth, int color) {
        rect(key + "_t", b.x(), b.y() - (b.height() - thickness) / 2, b.width(), thickness, depth, color);
        rect(key + "_b", b.x(), b.y() + (b.height() - thickness) / 2, b.width(), thickness, depth, color);
        rect(key + "_l", b.x() - (b.width() - thickness) / 2, b.y(), thickness, b.height(), depth, color);
        rect(key + "_r", b.x() + (b.width() - thickness) / 2, b.y(), thickness, b.height(), depth, color);
    }

    /** The weapon's own GUI model as its icon. */
    public void weapon(String key, String weaponId, float x, float y, float size, float depth) {
        weapon(key, weaponId, x, y, size, depth, 0);
    }

    /** {@code spin} degrees about the vertical axis. Only for models drawn well in front of every other layer:
     * GUI models are flattened to one unit of depth, so a rotated card would cut through nearby layers. */
    public void weapon(String key, String weaponId, float x, float y, float size, float depth, float spin) {
        if (WeaponCatalog.find(weaponId).isEmpty()) return;
        paint(key, new Box(x, y, size, size), depth, 0xFFFFFF, weaponId, null, false, spin);
    }

    public void icon(String key, String icon, float x, float y, float size, float depth, int color) {
        paint(key, new Box(x, y, size, size), depth, color, null, Identifier.parse("destiny:gui/hud/" + icon), false, 0);
    }

    /**
     * An icon that follows a moving point (a pointer): position changes of the same icon are interpolated by the
     * client over {@code glide} ticks, so 20 Hz server updates render as continuous motion.
     */
    public void glide(String key, String icon, float x, float y, float size, float depth, int color, int glide) {
        paint(key, new Box(x, y, size, size), depth, color, null, Identifier.parse("destiny:gui/hud/" + icon), false, 0, glide);
    }

    /**
     * A mouse pointer at ({@code x}, {@code y}), the position for view rotation ({@code yaw}, {@code pitch}). The
     * client shader keeps moving it with the live view rotation every frame (DisplayHud pointer), so it tracks the
     * mouse at frame rate with no server round trip; each server update only corrects clamping at the edges.
     * The icon is drawn white.
     */
    public void pointer(String key, String icon, float x, float y, float size, float depth, float yaw, float pitch) {
        paint(key, new Box(x, y, size, size), depth, DisplayHud.pointerTint(yaw, pitch), null,
                Identifier.parse("destiny:gui/hud/" + icon), false, 0, 0);
        if (DisplayHud.getHud(player, prefix + key) instanceof ItemDisplayHud hud) { hud.setPointer(true); hud.update(); }
    }

    /** A non-square HUD image (box size in canvas pixels). */
    public void image(String key, String icon, float x, float y, float width, float height, float depth, int color) {
        paint(key, new Box(x, y, width, height), depth, color, null, Identifier.parse("destiny:gui/hud/" + icon), false, 0);
    }

    private void paint(String key, Box box, float depth, int color, String weapon, Identifier model, boolean stretch, float spin) {
        paint(key, box, depth, color, weapon, model, stretch, spin, 0);
    }

    private void paint(String key, Box box, float depth, int color, String weapon, Identifier model, boolean stretch, float spin, int glide) {
        String id = prefix + key;
        used.add(id);
        Tile state = new Tile(box, depth, color, weapon, model, stretch, spin);
        DisplayHud old = DisplayHud.getHud(player, id);
        if (old instanceof ItemDisplayHud && state.equals(old.getExtraData(STATE))) return;
        if (old != null && !(old instanceof ItemDisplayHud)) { old.remove(); old = null; }
        ItemDisplayHud hud = old instanceof ItemDisplayHud item ? item : new ItemDisplayHud();
        hud.updateWhenDataChanged(false);
        if (!(old != null && old.getExtraData(STATE) instanceof Tile last && last.color() == color
                && Objects.equals(last.weapon(), weapon) && Objects.equals(last.model(), model))) {
            ItemStack stack;
            if (weapon != null) stack = WeaponModels.create(WeaponCatalog.find(weapon).orElseThrow());
            else {
                stack = new ItemStack(Items.PAPER);
                stack.set(DataComponents.ITEM_MODEL, model == null ? SOLID : model);
                stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(), List.of(), List.of(color)));
            }
            hud.setItem(stack);
        }
        hud.setItemTransform(weapon == null ? ItemDisplayContext.NONE : ItemDisplayContext.GUI);
        hud.setScale(box.width(), box.height(), 1);
        if (weapon != null) hud.setLeftRotation(new Vector3f(0, (float) Math.toRadians(spin), 0),
                old != null && old.getExtraData(STATE) instanceof Tile last && last.spin() != spin ? 20 : 0);
        hud.setAlignment(stretch ? DisplayHud.HudAlignment.UNALIGNED : DisplayHud.HudAlignment.CENTER);
        // Only a pure move of the same tile glides; any other change snaps (the last transformation call sets the
        // interpolation duration of the whole packet).
        boolean moved = glide > 0 && old != null && old.getExtraData(STATE) instanceof Tile last
                && last.box().width() == box.width() && last.box().height() == box.height() && last.depth() == depth;
        hud.setLocation(box.x(), box.y(), depth, moved ? glide : 0);
        hud.setAboveHand(true);
        hud.setViewRange(1000);
        hud.removeWhenPlayerDied(true);
        hud.setExtraData(STATE, state);
        if (old == null) hud.spawn(player, id);
        hud.update();
    }

    /**
     * A raw item model with a display-space transformation (already including the HUD anchor; see
     * {@link PlayerFigure#anchor}). {@code stackKey} identifies the stack so unchanged models send nothing.
     */
    public void model(String key, ItemStack stack, String stackKey, ItemDisplayContext context, Transformation transform) {
        model(key, stack, stackKey, context, transform, 0);
    }

    /** As above; a changed transformation of an existing model blends over {@code blend} client ticks. */
    public void model(String key, ItemStack stack, String stackKey, ItemDisplayContext context, Transformation transform, int blend) {
        String id = prefix + key;
        used.add(id);
        Model state = new Model(stackKey, context, transform);
        DisplayHud old = DisplayHud.getHud(player, id);
        if (old instanceof ItemDisplayHud && state.equals(old.getExtraData(STATE))) return;
        if (old != null && !(old instanceof ItemDisplayHud)) { old.remove(); old = null; }
        // A new stack (different weapon or skin) snaps into place; only pose changes of the same model blend.
        boolean sameStack = old != null && old.getExtraData(STATE) instanceof Model last && last.stackKey().equals(stackKey);
        ItemDisplayHud hud = old instanceof ItemDisplayHud item ? item : new ItemDisplayHud();
        hud.updateWhenDataChanged(false);
        if (!sameStack) hud.setItem(stack);
        hud.setItemTransform(context);
        hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        hud.setAboveHand(true);
        hud.setViewRange(1000);
        hud.removeWhenPlayerDied(true);
        hud.setExtraData(STATE, state);
        // Spawning and setItem re-apply the location/scale helpers: the raw transformation goes last.
        if (old == null) hud.spawn(player, id);
        hud.setTransformation(transform, sameStack ? blend : 0);
        hud.update();
    }

    public void text(String key, String text, float x, float y, float pixels, int color) {
        text(key, text, x, y, pixels, color, 255);
    }

    /** Centre-aligned single line; {@code opacity} 0..255 fades over two ticks when it changes. */
    public void text(String key, String text, float x, float y, float pixels, int color, int opacity) {
        pixels = Math.max(MIN_TEXT_PIXELS, pixels);
        String id = prefix + key;
        used.add(id);
        Label state = new Label(text, x, y, pixels, color, opacity);
        DisplayHud old = DisplayHud.getHud(player, id);
        if (old instanceof TextDisplayHud && state.equals(old.getExtraData(STATE))) return;
        if (old != null && !(old instanceof TextDisplayHud)) { old.remove(); old = null; }
        TextDisplayHud hud = old instanceof TextDisplayHud label ? label : new TextDisplayHud();
        hud.updateWhenDataChanged(false);
        hud.setLineWidth(512);
        hud.setTextAlignment(Display.TextDisplay.Align.CENTER);
        Component component = Component.literal(text).withStyle(style -> style.withColor(color));
        hud.setText(component);
        hud.getTextDisplay().setText(Component.literal("\n").append(component));
        hud.setBackgroundColor(0);
        hud.setShadowToggle(false);
        boolean fade = old != null && old.getExtraData(STATE) instanceof Label last && last.opacity() != opacity;
        hud.setOpacity(Math.max(4, opacity), fade ? 3 : 0);
        hud.setScale(pixels * 5, pixels * 5, 1);
        hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        hud.setLocation(x, y + pixels * 1.25f, 130);
        hud.setAboveHand(true);
        hud.setViewRange(1000);
        hud.removeWhenPlayerDied(true);
        hud.setExtraData(STATE, state);
        if (old == null) hud.spawn(player, id);
        hud.update();
    }

    /** Left-aligned text: centres the run on {@code left + width/2}. */
    public void textLeft(String key, String text, float left, float y, float pixels, int color, float maxWidth, int opacity) {
        String clipped = ellipsized(text, Math.max(MIN_TEXT_PIXELS, pixels), maxWidth);
        text(key, clipped, left + width(clipped, Math.max(MIN_TEXT_PIXELS, pixels)) / 2, y, pixels, color, opacity);
    }

    public void textRight(String key, String text, float right, float y, float pixels, int color, int opacity) {
        float p = Math.max(MIN_TEXT_PIXELS, pixels);
        text(key, text, right - width(text, p) / 2, y, pixels, color, opacity);
    }

    public void textFit(String key, String text, float x, float y, float pixels, int color, float maxWidth) {
        float p = Math.max(MIN_TEXT_PIXELS, pixels);
        text(key, ellipsized(text, p, maxWidth), x, y, p, color);
    }

    /** Left-aligned wrapped paragraph; returns lines used. */
    public int wrappedLeft(String key, String value, float left, float y, float pixels, int color,
                           float maxWidth, int maxLines, float lineHeight, int opacity) {
        float p = Math.max(MIN_TEXT_PIXELS, pixels);
        var lines = wrap(value, p, maxWidth, maxLines);
        for (int i = 0; i < lines.size(); i++) textLeft(key + "_" + i, lines.get(i), left, y + i * lineHeight, p, color, maxWidth, opacity);
        return lines.size();
    }

    public void finish() {
        for (String id : List.copyOf(DisplayHud.getHuds(player).keySet()))
            if (id.startsWith(prefix) && !used.contains(id)) DisplayHud.removeHud(player, id);
    }

    /** Approximate rendered width in reference pixels (vanilla font advance at this size). Pure. */
    public static float width(String text, float pixels) {
        float units = 0;
        for (int point : text.codePoints().toArray()) units += advance(point);
        return units * pixels * 0.125f;
    }

    static int advance(int point) { return point == ' ' ? 4 : point < 128 || point == '…' ? 6 : 9; }

    public static String ellipsized(String value, float pixels, float maxWidth) {
        String clean = value == null ? "" : value.replaceAll("[\\p{Cntrl}]|§", " ").strip();
        if (width(clean, pixels) <= maxWidth) return clean;
        float budget = maxWidth / (pixels * 0.125f) - advance('…');
        StringBuilder out = new StringBuilder();
        for (int point : clean.codePoints().toArray()) {
            if (advance(point) > budget) break;
            out.appendCodePoint(point); budget -= advance(point);
        }
        return out.toString().stripTrailing() + "…";
    }

    /** Word-aware wrap that keeps Hangul words whole where possible. Pure. */
    public static List<String> wrap(String value, float pixels, float maxWidth, int maxLines) {
        String clean = value == null || value.isBlank() ? "" : value.replace("\r", "").replaceAll("§", " ").strip();
        List<String> lines = new ArrayList<>();
        for (String paragraph : clean.split("\n")) {
            StringBuilder line = new StringBuilder();
            for (String word : paragraph.split(" ")) {
                String candidate = line.isEmpty() ? word : line + " " + word;
                if (width(candidate, pixels) <= maxWidth) { line.setLength(0); line.append(candidate); continue; }
                if (!line.isEmpty()) { lines.add(line.toString()); line.setLength(0); }
                String rest = word;
                while (width(rest, pixels) > maxWidth) {
                    String head = ellipsized(rest, pixels, maxWidth + advance('…') * pixels * 0.125f);
                    head = head.endsWith("…") ? head.substring(0, head.length() - 1) : head;
                    if (head.isEmpty()) break;
                    lines.add(head); rest = rest.substring(head.length());
                }
                line.append(rest);
            }
            if (!line.isEmpty()) lines.add(line.toString());
        }
        if (lines.size() > maxLines) {
            var kept = new ArrayList<>(lines.subList(0, maxLines));
            kept.set(maxLines - 1, ellipsized(kept.get(maxLines - 1) + "…", pixels, maxWidth));
            return kept;
        }
        return lines;
    }
}
