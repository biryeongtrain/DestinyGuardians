package kim.biryeong.destiny.campaign.presentation;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import kim.biryeong.minigamelib.displayhud.TextDisplayHud;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;

import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * Korean subtitles for Guardian Rises. Lines come from subtitles_ko.json, generated from the
 * extraction's dialogue-ko.csv korean column (exact text). Two opening lines are original
 * authored subtitle-only text and carry {@code authored=true, voice=false}.
 *
 * <p>Gameplay: a bottom-centre DisplayHud card (Crucible banner sprites, same look as the tutorial).
 * Cinematic (input locked, world under a post effect): the vanilla action bar. The action bar is GUI,
 * so the blackout/scan grades cannot hide it, and it stays visible while the HUD is hidden.
 */
public final class RisingSubtitles {
    public static final String RESOURCE = "/destiny/guardian_rises/subtitles_ko.json";
    private static final String P = "destiny:rising_sub/";
    static final int WHITE = 0xF4F6F8, DARK = 0x05080C, GHOST = 0x8FE3FF;
    private static final int CARD_X = 960, CARD_BOTTOM = 905, WRAP = 30, CARD_W = 760; // bottom centre (user W303)

    public record Line(String id, String speaker, String text, int ticks, boolean voice, boolean authored) {}

    private record Showing(ServerPlayer player, Line line, int until, boolean cinematic, Set<String> ids, int nextBar) {}

    private static final Map<String, Line> LINES = load();
    private static final Map<UUID, Showing> SHOWN = new HashMap<>();

    private RisingSubtitles() {}

    static Map<String, Line> load() {
        var input = RisingSubtitles.class.getResourceAsStream(RESOURCE);
        if (input == null) throw new IllegalStateException("Missing " + RESOURCE);
        try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            var out = new LinkedHashMap<String, Line>();
            for (var e : root.getAsJsonObject("lines").entrySet()) {
                var v = e.getValue().getAsJsonObject();
                out.put(e.getKey(), new Line(e.getKey(), v.get("speaker").getAsString(), v.get("text").getAsString(),
                        v.get("ticks").getAsInt(), v.get("voice").getAsBoolean(), v.get("authored").getAsBoolean()));
            }
            return Collections.unmodifiableMap(out);
        } catch (java.io.IOException e) {
            throw new IllegalStateException(e);
        }
    }

    public static Optional<Line> line(String id) {
        return id == null ? Optional.empty() : Optional.ofNullable(LINES.get(id.toLowerCase(Locale.ROOT)));
    }

    public static Collection<Line> lines() { return LINES.values(); }

    /** Shows {@code line} until server tick {@code until}; replaces any current subtitle. */
    static void show(ServerPlayer p, Line line, int until, boolean cinematic) {
        hide(p);
        var ids = new HashSet<String>();
        // W301: cinematics get film subtitles (centred, wrapped, in the letterbox) instead of a one-line action bar.
        if (cinematic) renderFilm(p, line, ids);
        else renderCard(p, line, ids);
        SHOWN.put(p.getUUID(), new Showing(p, line, until, cinematic, ids, tick(p) + 30));
    }

    static void hide(ServerPlayer p) {
        var old = SHOWN.remove(p.getUUID());
        if (old == null) return;
        if (!p.hasDisconnected()) {
            for (String id : old.ids()) DisplayHud.removeHud(p, id);
        }
    }

    /** Expires subtitles, keeps the action bar alive and moves a line between modes when the lock changes. */
    static void tick(int now) {
        for (var s : List.copyOf(SHOWN.values())) {
            var p = s.player();
            if (p.hasDisconnected() || p.isRemoved()) { SHOWN.remove(p.getUUID(), s); continue; }
            if (now >= s.until()) { hide(p); continue; }
            boolean cinematic = RisingPresentation.cinematic(p);
            if (cinematic != s.cinematic()) { show(p, s.line(), s.until(), cinematic); continue; }
        }
    }

    static void clearAll() {
        for (var s : List.copyOf(SHOWN.values())) hide(s.player());
        SHOWN.clear();
    }

    private static int tick(ServerPlayer p) { return p.level().getServer().getTickCount(); }

    /** Film subtitle: speaker + text centred at the bottom (inside the opening letterbox), at most 46 wide per row. */
    private static void renderFilm(ServerPlayer p, Line line, Set<String> ids) {
        var wrapped = wrap(line.text(), 46);
        var body = Component.empty().append(Component.literal(line.speaker() + "   ").withStyle(s -> s.withColor(GHOST).withBold(true)));
        for (int i = 0; i < wrapped.size(); i++) {
            if (i > 0) body.append(Component.literal("\n"));
            body.append(Component.literal(wrapped.get(i)).withColor(WHITE));
        }
        int rows = wrapped.size();
        // Just above the bottom letterbox bar (display text does not sort over the opaque bar).
        text(p, ids, "film", body, 960, 924, 22, 46 * 22 * 1.1f * 2.5f, 210);
    }

    private static void renderCard(ServerPlayer p, Line line, Set<String> ids) {
        var wrapped = wrap(line.text(), WRAP);
        int rows = wrapped.size();
        float h = 50 + rows * 30;
        float top = CARD_BOTTOM - h;
        sprite(p, ids, "bg", "crucible_banner", CARD_X, top + h / 2, CARD_W, h, 20, DARK);
        sprite(p, ids, "line", "crucible_line", CARD_X - CARD_W / 2f + 8, top + h / 2, 3, h - 14, 21, GHOST);
        text(p, ids, "speaker", Component.literal("◇ " + line.speaker()).withStyle(s -> s.withColor(GHOST).withBold(true)),
                CARD_X, top + 8, 18, CARD_W - 40, 30);
        // Text displays grow upward from their anchor: anchor the last line.
        text(p, ids, "text", Component.literal(String.join("\n", wrapped)).withColor(WHITE),
                CARD_X, top + 36 + (rows - 1) * 29, 22, (CARD_W - 40) * 2.5f, 30);
    }

    /** Greedy word wrap by display width: Hangul and other wide glyphs count 1, ASCII about half. */
    public static List<String> wrap(String text, int width) {
        var out = new ArrayList<String>();
        var line = new StringBuilder();
        float used = 0;
        for (String word : text.trim().split("\\s+")) {
            if (word.isEmpty()) continue;
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

    private static void sprite(ServerPlayer p, Set<String> ids, String id, String image, float x, float y, float w, float h,
                               float z, int color) {
        String full = P + id;
        ids.add(full);
        DisplayHud.removeHud(p, full);
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
        hud.setAboveHand(true); // draw over the first-person weapon
        hud.spawn(p, full);
        hud.updateWhenDataChanged(true);
        hud.update();
    }

    private static void text(ServerPlayer p, Set<String> ids, String id, Component value, float x, float y, float size,
                             float lineWidth, float z) {
        String full = P + id;
        ids.add(full);
        DisplayHud.removeHud(p, full);
        TextDisplayHud hud = new TextDisplayHud();
        hud.updateWhenDataChanged(false);
        hud.setLineWidth(Math.round(lineWidth));
        hud.setTextAlignment(net.minecraft.world.entity.Display.TextDisplay.Align.CENTER);
        hud.setText(value);
        hud.getTextDisplay().setText(Component.literal("\n").append(value));
        hud.setBackgroundColor(0);
        hud.setShadowToggle(true);
        hud.setOpacity(255);
        hud.setScale(size * 5, size * 5, 1);
        hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        hud.setLocation(x, y + size * 1.25f, z);
        hud.setViewRange(1000);
        hud.setAboveHand(true); // draw over the first-person weapon
        hud.spawn(p, full);
        hud.updateWhenDataChanged(true);
        hud.update();
    }
}
