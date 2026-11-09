package kim.biryeong.destiny.fireteam;

import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.FontDescription;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.network.protocol.game.ClientboundClearTitlesPacket;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;

/**
 * What a Guardian sees while the launch curtain holds the screen black and the activity is built: the activity name,
 * an orbiting-dot spinner with "게임을 불러오는 중", and a thin progress line that never runs backwards. Everything is
 * drawn on the GUI layer (title, subtitle, action bar), which the black post effect does not touch.
 * <p>
 * The progress shown is eased toward the activity's real preparation progress ({@link ActivityCatalog.Launcher#progress})
 * and held below 100% until the client has actually loaded the destination; activities without a measurement get a
 * time-based curve that approaches but never reaches the end. Glyphs live in {@code destiny:loading_ui}
 * (scripts/ui/build_loading_ui.py).
 */
final class LaunchLoadingScreen {
    static final Identifier UI_FONT = DestinyGuardians.id("loading_ui");
    private static final FontDescription.Resource NOTO = new FontDescription.Resource(DestinyGuardians.id("econ_text"));
    private static final FontDescription.Resource GLYPHS = new FontDescription.Resource(UI_FONT);
    static final char SPINNER_FIRST = '\ue500', BAR_EMPTY = '\ue510', BAR_FULL = '\ue515', BAR_HEAD = '\ue516';
    static final int SPINNER_FRAMES = 12, SPINNER_TICKS_PER_FRAME = 2, SEGMENTS = 28, STEPS = 5;
    /** The bar's last stretch is held back until the destination is really there. */
    static final float WAITING_CAP = .96f;
    static final int NAME = 0xF2F2EE, STATUS = 0xB9C0C8, DIM = 0x4B525B, GOLD = 0xE3C46B, TEXT_MUTED = 0x8C949E;

    private final ServerPlayer player;
    private final String name;
    private final String type;
    private float shown;
    private boolean started, fading;
    private String detail;

    LaunchLoadingScreen(ServerPlayer player, String name, String type) {
        this.player = player; this.name = name; this.type = type;
    }

    float shown() { return shown; }

    // ---------------------------------------------------------------------------------------------------- pure

    /** Spinner glyph for an age in ticks. */
    static char spinner(int age) { return (char) (SPINNER_FIRST + Math.floorMod(age / SPINNER_TICKS_PER_FRAME, SPINNER_FRAMES)); }

    /** Bar glyph run for {@code progress} in 0..1: full segments, one partial segment, empty remainder; gold head while moving. */
    static String bar(float progress, boolean done) {
        float p = Math.clamp(progress, 0f, 1f);
        int units = Math.round(p * SEGMENTS * STEPS);
        int whole = Math.min(SEGMENTS, units / STEPS), part = units % STEPS;
        var out = new StringBuilder(SEGMENTS);
        for (int i = 0; i < SEGMENTS; i++) {
            if (i < whole) out.append(done || i < whole - 1 || part > 0 ? BAR_FULL : BAR_HEAD);
            else if (i == whole && part > 0) out.append((char) (BAR_EMPTY + part));
            else out.append(BAR_EMPTY);
        }
        return out.toString();
    }

    /** Target shown at {@code age} ticks into the wait: measured progress when known, otherwise a saturating curve. */
    static float goal(float measured, int age, boolean ready) {
        if (ready) return 1f;
        float base = measured >= 0 ? Math.clamp(measured, 0f, 1f) : (float) (1 - Math.exp(-age / 260.0));
        return Math.min(WAITING_CAP, base * WAITING_CAP);
    }

    /** One easing step; never decreases. */
    static float ease(float shown, float goal, boolean ready) {
        float rate = ready ? .35f : .07f;
        return Math.max(shown, shown + (goal - shown) * rate);
    }

    static int percent(float shown, boolean ready) { return ready ? 100 : Math.min(99, (int) (shown * 100)); }

    // -------------------------------------------------------------------------------------------------- render

    /** Draw one frame. {@code age}: ticks since the activity began preparing. */
    void render(int age, float measured, boolean ready) { render(age, measured, ready, null); }
    void render(int age, float measured, boolean ready, String detail) {
        this.detail = detail;
        if (player.hasDisconnected() || fading) return;
        shown = ease(shown, goal(measured, age, ready), ready);
        var c = player.connection;
        if (!started || age % 10 == 0) {
            c.send(new ClientboundSetTitlesAnimationPacket(started ? 0 : 12, 40, 0));
            c.send(new ClientboundSetTitleTextPacket(Component.literal(name).withStyle(plain(NAME))));
            started = true;
        }
        if (age % SPINNER_TICKS_PER_FRAME == 0 || ready) c.send(new ClientboundSetSubtitleTextPacket(status(age, ready)));
        if (age % 2 == 0 || ready) c.send(new ClientboundSetActionBarTextPacket(progress(ready)));
    }

    private Component status(int age, boolean ready) {
        MutableComponent out = Component.empty();
        if (ready) {
            out.append(Component.literal("준비 완료").withStyle(plain(GOLD)));
            return out;
        }
        out.append(Component.literal(String.valueOf(spinner(age))).withStyle(glyph(NAME)));
        out.append(Component.literal("  " + (detail == null ? "게임을 불러오는 중" : detail)).withStyle(plain(STATUS)));
        int lit = age / 8 % 4;   // 0..3 dots lit: a fixed-width ellipsis, so the line never shifts sideways
        for (int i = 0; i < 3; i++) {
            int color = i < lit ? STATUS : DIM;
            out.append(Component.literal(".").withStyle(plain(color)));
        }
        return out;
    }

    private Component progress(boolean ready) {
        MutableComponent out = Component.empty();
        out.append(Component.literal(bar(shown, ready)).withStyle(glyph(0xFFFFFF)));
        out.append(Component.literal("  " + percent(shown, ready) + "%").withStyle(plain(ready ? GOLD : TEXT_MUTED)));
        return out;
    }

    /** Flat text for the black screen: a drop shadow only reads as a smudge there. */
    private static Style plain(int color) { return Style.EMPTY.withFont(NOTO).withColor(color).withShadowColor(0); }

    private static Style glyph(int color) { return Style.EMPTY.withFont(GLYPHS).withColor(color).withShadowColor(0); }

    /** The curtain starts lifting: the title card (name over type) holds a moment over the revealed world, then fades. */
    void fadeOut(int ticks) {
        if (fading || player.hasDisconnected()) return;
        fading = true;
        var c = player.connection;
        c.send(new ClientboundSetActionBarTextPacket(Component.empty()));
        c.send(new ClientboundSetTitlesAnimationPacket(0, 36, ticks));
        c.send(new ClientboundSetTitleTextPacket(Component.literal(name).withStyle(s -> s.withColor(NAME).withFont(NOTO))));
        c.send(new ClientboundSetSubtitleTextPacket(Component.literal(type).withStyle(s -> s.withColor(STATUS).withFont(NOTO))));
    }

    /** Remove everything at once. Idempotent. */
    void clear() {
        if (player.hasDisconnected()) return;
        player.connection.send(new ClientboundClearTitlesPacket(true));
        player.connection.send(new ClientboundSetActionBarTextPacket(Component.empty()));
    }
}
