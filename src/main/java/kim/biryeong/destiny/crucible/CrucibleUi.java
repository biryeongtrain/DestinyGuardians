package kim.biryeong.destiny.crucible;

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

import static kim.biryeong.destiny.crucible.CrucibleUiTimeline.*;

/**
 * Destiny 2 Control presentation: letterboxed map reveal, team face-off rosters, countdown, top-centre
 * score/timer/zone diamonds, event toasts and result card. Everything is a DisplayHud owned by this class;
 * each frame declares the ids it wants and stale ids are removed. Moves use client-side interpolation.
 */
public final class CrucibleUi {
    private static final String P = "destiny:crucible_ui/";
    private static final int FRIEND = CrucibleTeamVisuals.FRIEND, ENEMY = CrucibleTeamVisuals.ENEMY;
    private static final int WHITE = 0xF4F6F8, GREY = 0xA9B2BC, NEUTRAL = 0xDAD8CC, DARK = 0x05080C, GOLD = 0xF2C14E;
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private CrucibleUi() { }

    public record Roster(List<String> friends, List<String> enemies) {
        public static final Roster EMPTY = new Roster(List.of(), List.of());
    }

    private static final class Toast {
        final String title, sub; final int color, until;
        Toast(String title, String sub, int color, int until) { this.title = title; this.sub = sub; this.color = color; this.until = until; }
    }
    private static final class Session {
        final Set<String> ids = new HashSet<>();
        ControlMatch.Phase phase;
        Toast toast;
        int introStart = Integer.MIN_VALUE;
        boolean grade;
        net.minecraft.resources.Identifier pulse;
        int pulseUntil;
        int lastDigit = -1;
    }
    private static final net.minecraft.resources.Identifier GRADE = kim.biryeong.destiny.DestinyGuardians.id("crucible/intro");
    private static final net.minecraft.resources.Identifier START_FLASH = kim.biryeong.destiny.DestinyGuardians.id("crucible/start_flash");
    private static final net.minecraft.resources.Identifier TICK_PULSE = kim.biryeong.destiny.DestinyGuardians.id("crucible/tick_pulse");

    private static void pulse(ServerPlayer p, Session s, net.minecraft.resources.Identifier id, int nowTick, int ticks) {
        if (s.pulse != null) p.removePostEffect(s.pulse);
        s.pulse = p.addPostEffect(id) ? id : null;
        s.pulseUntil = nowTick + ticks;
    }

    /** Post-effect polish: cool cinematic grade during the intro, a pulse on each countdown digit and a flash on start. */
    private static void postFx(ServerPlayer p, Session s, ControlMatch.Snapshot snap, int nowTick, int introTicks, boolean phaseChanged) {
        boolean wantGrade = snap.phase() == ControlMatch.Phase.INTRO;
        if (wantGrade && !s.grade) s.grade = p.addPostEffect(GRADE);
        else if (!wantGrade && s.grade) { p.removePostEffect(GRADE); s.grade = false; }
        if (s.pulse != null && nowTick >= s.pulseUntil) { p.removePostEffect(s.pulse); s.pulse = null; }
        if (snap.phase() == ControlMatch.Phase.INTRO
                && CrucibleUiTimeline.segment(snap.phaseTicks(), introTicks) == Segment.COUNTDOWN) {
            int digit = countdownDigit(Math.max(0, introTicks - snap.phaseTicks()));
            if (digit != s.lastDigit) { s.lastDigit = digit; pulse(p, s, digit == 0 ? START_FLASH : TICK_PULSE, nowTick, digit == 0 ? 10 : 4); }
        } else if (snap.phase() == ControlMatch.Phase.PLAYING && phaseChanged) {
            s.lastDigit = -1; pulse(p, s, START_FLASH, nowTick, 10);
        } else if (snap.phase() != ControlMatch.Phase.INTRO) s.lastDigit = -1;
    }


    /** Event banner under the zone row; replaces any current toast. */
    public static void toast(ServerPlayer p, String title, String sub, int color, int nowTick, int ticks) {
        SESSIONS.computeIfAbsent(p.getUUID(), k -> new Session()).toast = new Toast(title, sub, color, nowTick + ticks);
    }

    /** Maps a CrucibleSounds zone cue to a toast; null cues are ignored. */
    public static void zoneCue(ServerPlayer p, String cue, int nowTick) {
        if (cue == null) return;
        switch (cue) {
            case "power_play" -> toast(p, "파워 플레이", "세 거점을 모두 장악했습니다", FRIEND, nowTick, 80);
            case "enemy_power_play" -> toast(p, "적 파워 플레이", "적이 세 거점을 모두 장악했습니다", ENEMY, nowTick, 80);
            case "advantage" -> toast(p, "거점 우세", "두 거점을 확보했습니다", FRIEND, nowTick, 60);
            case "enemy_advantage" -> toast(p, "적 거점 우세", "적이 두 거점을 확보했습니다", ENEMY, nowTick, 60);
            default -> {
                String zone = cue.substring(cue.length() - 1).toUpperCase(Locale.ROOT);
                if (cue.startsWith("capture_")) toast(p, zone + " 거점 점령", "거점을 확보했습니다", FRIEND, nowTick, 50);
                else if (cue.startsWith("lost_")) toast(p, zone + " 거점 상실", "거점을 빼앗겼습니다", ENEMY, nowTick, 50);
            }
        }
    }

    public static void remove(ServerPlayer p) {
        Session s = SESSIONS.remove(p.getUUID());
        if (s != null) {
            for (String id : s.ids) DisplayHud.removeHud(p, id);
            if (s.grade) p.removePostEffect(GRADE);
            if (s.pulse != null) p.removePostEffect(s.pulse);
        }
        for (String id : List.copyOf(DisplayHud.getHuds(p).keySet()))
            if (id.startsWith(P)) DisplayHud.removeHud(p, id);
    }

    public static void render(ServerPlayer p, ControlMatch.Snapshot snap, String map, int respawnTicks,
                              Roster roster, int nowTick, int introTicks) {
        var own = snap.members().get(p.getUUID());
        if (own == null) { remove(p); return; }
        Session s = SESSIONS.computeIfAbsent(p.getUUID(), k -> new Session());
        var foe = own == ControlMatch.Team.ALPHA ? ControlMatch.Team.BRAVO : ControlMatch.Team.ALPHA;
        Frame f = new Frame(p, s);
        boolean phaseChanged = s.phase != snap.phase();
        if (phaseChanged) { s.phase = snap.phase(); s.introStart = nowTick; s.toast = null; }
        postFx(p, s, snap, nowTick, introTicks, phaseChanged);
        switch (snap.phase()) {
            case WAITING -> waiting(f, snap, map, own);
            case INTRO -> intro(f, snap, map, own, roster, introTicks);
            case PLAYING -> {
                playing(f, snap, own, foe, respawnTicks);
                int sincePlay = nowTick - s.introStart;
                if (sincePlay < 120 && s.toast == null) objective(f, sincePlay);
                if (s.toast != null) {
                    if (nowTick >= s.toast.until) s.toast = null; else toastPanel(f, s.toast);
                }
            }
            case RESULTS -> results(f, snap, own, foe);
        }
        f.finish();
    }

    // ---- frame ------------------------------------------------------------------------------------------------
    private static final class Frame {
        final ServerPlayer p; final Session s; final Set<String> used = new HashSet<>();
        Frame(ServerPlayer p, Session s) { this.p = p; this.s = s; }

        void sprite(String id, String image, float x, float y, float w, float h, float z, int color, float fromX, int slide) {
            String full = P + id; used.add(full);
            String shape = image + ":" + color + ":" + w + ":" + h + ":" + z;
            DisplayHud existing = DisplayHud.getHud(p, full);
            if (existing instanceof ItemDisplayHud item && shape.equals(existing.getExtraData("shape"))) {
                String pos = x + "," + y;
                if (!pos.equals(existing.getExtraData("pos"))) { item.setLocation(x, y, z, slide); item.setExtraData("pos", pos); item.update(); }
                return;
            }
            if (existing != null) { DisplayHud.removeHud(p, full); existing = null; }
            ItemDisplayHud hud = new ItemDisplayHud();
            hud.updateWhenDataChanged(false);
            ItemStack stack = new ItemStack(Items.PAPER);
            stack.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "gui/hud/" + image));
            stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(), List.of(), List.of(color)));
            hud.setItem(stack);
            hud.setItemTransform(ItemDisplayContext.NONE);
            hud.setScale(w, h, 1);
            hud.setAlignment(DisplayHud.HudAlignment.CENTER);
            boolean slideIn = slide > 0 && fromX != x;
            hud.setLocation(slideIn ? fromX : x, y, z);
            hud.setViewRange(1000);
            hud.setExtraData("shape", shape); hud.setExtraData("pos", x + "," + y);
            hud.spawn(p, full);
            hud.updateWhenDataChanged(true);
            hud.update();
            if (slideIn) { hud.setLocation(x, y, z, slide); hud.update(); }
        }
        void sprite(String id, String image, float x, float y, float w, float h, float z, int color) {
            sprite(id, image, x, y, w, h, z, color, x, 0);
        }

        /** Text block centred on x (reference px). size = glyph height px. */
        void text(String id, Component value, float x, float y, float size, float lineWidth, float z,
                  Display.TextDisplay.Align align, float fromX, int slide) {
            // The library's LEFT/RIGHT text offsets assume its width spacer row; we render a bare row instead,
            // so anchor edges ourselves and always centre the display on an estimated box.
            if (align != Display.TextDisplay.Align.CENTER) {
                float half = estimateWidth(value.getString(), size) / 2f * (align == Display.TextDisplay.Align.LEFT ? 1 : -1);
                x += half; fromX += half; align = Display.TextDisplay.Align.CENTER;
            }
            String full = P + id; used.add(full);
            String state = value.getString() + ":" + value.toString().hashCode() + ":" + size + ":" + lineWidth + ":" + z + ":" + align;
            DisplayHud existing = DisplayHud.getHud(p, full);
            if (existing instanceof TextDisplayHud text && state.equals(existing.getExtraData("shape"))) {
                String pos = x + "," + y;
                if (!pos.equals(existing.getExtraData("pos"))) { text.setLocation(x, y + size * 1.25f, z, slide); text.setExtraData("pos", pos); text.update(); }
                return;
            }
            if (existing != null) { DisplayHud.removeHud(p, full); existing = null; }
            TextDisplayHud hud = new TextDisplayHud();
            hud.updateWhenDataChanged(false);
            hud.setLineWidth(Math.round(lineWidth));
            hud.setTextAlignment(align);
            hud.setText(value);
            hud.getTextDisplay().setText(Component.literal("\n").append(value));
            hud.setBackgroundColor(0); hud.setShadowToggle(true); hud.setOpacity(255);
            hud.setScale(size * 5, size * 5, 1);
            hud.setAlignment(DisplayHud.HudAlignment.CENTER);
            boolean slideIn = slide > 0 && fromX != x;
            hud.setLocation(slideIn ? fromX : x, y + size * 1.25f, z);
            hud.setViewRange(1000);
            hud.setExtraData("shape", state); hud.setExtraData("pos", x + "," + y);
            hud.spawn(p, full);
            hud.updateWhenDataChanged(true);
            hud.update();
            if (slideIn) { hud.setLocation(x, y + size * 1.25f, z, slide); hud.update(); }
        }
        void text(String id, Component value, float x, float y, float size, float lineWidth, float z) {
            text(id, value, x, y, size, lineWidth, z, Display.TextDisplay.Align.CENTER, x, 0);
        }

        void finish() {
            for (String id : s.ids) if (!used.contains(id)) DisplayHud.removeHud(p, id);
            s.ids.clear(); s.ids.addAll(used);
        }
    }

    /** Rendered width estimate in reference px for bold text of the given glyph size. */
    static float estimateWidth(String text, float size) {
        float w = 0;
        for (char ch : text.toCharArray()) w += (ch < 128 ? (ch == ' ' ? 0.45f : 0.85f) : 1.3f) * size;
        return w;
    }

    private static Component c(String s, int color) { return Component.literal(s).withColor(color); }
    private static Component bold(String s, int color) { return Component.literal(s).withStyle(st -> st.withColor(color).withBold(true)); }
    private static int dim(int rgb, double k) {
        return ((int) ((rgb >> 16 & 255) * k) << 16) | ((int) ((rgb >> 8 & 255) * k) << 8) | (int) ((rgb & 255) * k);
    }

    // ---- WAITING ------------------------------------------------------------------------------------------------
    private static void waiting(Frame f, ControlMatch.Snapshot snap, String map, ControlMatch.Team own) {
        f.sprite("wait_banner", "crucible_banner", 960, 110, 760, 120, 20, DARK);
        f.sprite("wait_line", "crucible_line", 960, 160, 520, 3, 21, WHITE);
        f.text("wait_title", bold("시련의 장 · 점령", WHITE), 960, 70, 30, 700, 30);
        f.text("wait_sub", c(map + "  ·  상대 수호자를 기다리는 중  " + snap.members().size() + "명", GREY), 960, 118, 22, 800, 30);
        f.sprite("wait_emblem", own == ControlMatch.Team.ALPHA ? "crucible_emblem_alpha" : "crucible_emblem_bravo", 700, 100, 56, 56, 31, FRIEND);
    }

    // ---- INTRO --------------------------------------------------------------------------------------------------
    private static void intro(Frame f, ControlMatch.Snapshot snap, String map, ControlMatch.Team own,
                              Roster roster, int introTicks) {
        int elapsed = snap.phaseTicks();
        int remaining = Math.max(0, introTicks - elapsed);
        // cinematic bars slide in during the first ten ticks and stay for the whole intro
        f.sprite("lb_top", "solid", 960, 54, 2100, 108, 10, 0x000000, 960, 0);
        f.sprite("lb_bottom", "solid", 960, 1026, 2100, 108, 10, 0x000000, 960, 0);
        var seg = CrucibleUiTimeline.segment(elapsed, introTicks);
        if (seg == Segment.TITLE || elapsed < ROSTER_START - 6) titleCard(f, map);
        if (seg == Segment.ROSTER || seg == Segment.COUNTDOWN) rosters(f, roster, own);
        if (seg == Segment.COUNTDOWN) countdown(f, remaining);
        else if (seg == Segment.ROSTER) {
            f.text("vs", bold("VS", WHITE), 960, 880, 54, 300, 40);
        }
    }

    private static void titleCard(Frame f, String map) {
        float left = 140;
        f.sprite("t_fade", "crucible_fade_l", 640, 780, 1280, 380, 20, 0x04070B, -700, 12);
        f.sprite("t_line", "crucible_line", 440, 660, 640, 4, 22, GOLD, -400, 10);
        f.text("t_label", c("시련의 장", GOLD), left, 690, 40, 800, 30, Display.TextDisplay.Align.LEFT, -300, 12);
        f.text("t_mode", bold("점령", WHITE), left, 760, 120, 1000, 30, Display.TextDisplay.Align.LEFT, -300, 14);
        f.text("t_map", bold(map, WHITE), left, 880, 56, 1000, 30, Display.TextDisplay.Align.LEFT, -300, 16);
        f.text("t_loc", c("코스모드롬 · 지구", GREY), left, 950, 32, 1000, 30, Display.TextDisplay.Align.LEFT, -300, 18);
    }

    private static void rosters(Frame f, Roster roster, ControlMatch.Team own) {
        String mine = own == ControlMatch.Team.ALPHA ? "crucible_emblem_alpha" : "crucible_emblem_bravo";
        String theirs = own == ControlMatch.Team.ALPHA ? "crucible_emblem_bravo" : "crucible_emblem_alpha";
        f.sprite("r_head_l", "crucible_fade_l", 430, 690, 860, 56, 20, dim(FRIEND, .35), -430, 10);
        f.sprite("r_head_r", "crucible_fade_r", 1490, 690, 860, 56, 20, dim(ENEMY, .35), 2350, 10);
        f.sprite("r_emb_l", mine, 90, 690, 44, 44, 31, FRIEND, -200, 10);
        f.sprite("r_emb_r", theirs, 1830, 690, 44, 44, 31, ENEMY, 2120, 10);
        f.text("r_cap_l", bold("아군 · 나의 팀", FRIEND), 150, 676, 28, 600, 30, Display.TextDisplay.Align.LEFT, -300, 10);
        f.text("r_cap_r", bold("적 팀", ENEMY), 1770, 676, 28, 600, 30, Display.TextDisplay.Align.RIGHT, 2200, 10);
        for (int i = 0; i < Math.min(6, roster.friends().size()); i++) {
            float y = 748 + i * 44;
            f.sprite("rf_bg" + i, "crucible_fade_l", 330, y, 660, 38, 20, 0x070C12, -340, 8 + i * 2);
            f.sprite("rf_bar" + i, "solid", 22, y, 6, 30, 31, FRIEND, -300, 8 + i * 2);
            f.text("rf_n" + i, bold(roster.friends().get(i), WHITE), 48, y - 14, 24, 520, 32, Display.TextDisplay.Align.LEFT, -300, 8 + i * 2);
        }
        for (int i = 0; i < Math.min(6, roster.enemies().size()); i++) {
            float y = 748 + i * 44;
            f.sprite("re_bg" + i, "crucible_fade_r", 1590, y, 660, 38, 20, 0x0C0709, 2260, 8 + i * 2);
            f.sprite("re_bar" + i, "solid", 1898, y, 6, 30, 31, ENEMY, 2200, 8 + i * 2);
            f.text("re_n" + i, bold(roster.enemies().get(i), WHITE), 1872, y - 14, 24, 520, 32, Display.TextDisplay.Align.RIGHT, 2200, 8 + i * 2);
        }
    }

    private static void countdown(Frame f, int remaining) {
        int digit = countdownDigit(remaining);
        f.sprite("cd_banner", "crucible_banner", 960, 505, 980, 260, 20, DARK);
        f.sprite("cd_line", "crucible_line", 960, 584, 640, 3, 22, GOLD);
        f.text("cd_num", bold(digit == 0 ? "시작" : String.valueOf(digit), digit == 0 ? GOLD : WHITE), 960, 438, 116, 400, 40);
        f.text("cd_sub", c("거점을 점령하고 150점을 먼저 달성하세요", NEUTRAL), 960, 600, 28, 900, 40);
    }

    // ---- PLAYING --------------------------------------------------------------------------------------------------
    private static void objective(Frame f, int since) {
        float slide = since < 8 ? -240 : 0;
        f.sprite("o_banner", "crucible_banner", 960, 270, 860, 96, 20, DARK, 960, 0);
        f.sprite("o_line", "crucible_line", 960, 310, 520, 3, 22, GOLD);
        f.text("o_title", bold("거점을 점령하세요", WHITE), 960, 240, 34, 700, 30);
        f.text("o_sub", c("A · B · C 거점을 확보해 점수를 얻으세요", GREY), 960, 280, 22, 800, 30);
    }

    private static void playing(Frame f, ControlMatch.Snapshot snap, ControlMatch.Team own, ControlMatch.Team foe, int respawnTicks) {
        int seconds = (snap.remainingTicks() + 19) / 20;
        int mine = snap.scores().get(own), theirs = snap.scores().get(foe), limit = 150;
        float lx = barX(-1), rx = barX(1);
        f.sprite("bar_l_bg", "crucible_bar_frame_l", lx, 46, 580, 26, 20, 0x0A0F15);
        f.sprite("bar_r_bg", "crucible_bar_frame_r", rx, 46, 580, 26, 20, 0x0A0F15);
        float fw = fillWidth(mine, limit), ew = fillWidth(theirs, limit);
        // friend bar fills from the centre outward (right-anchored), enemy mirrored
        if (fw > 0) f.sprite("bar_l_fill", "crucible_bar_fill_l", lx + 283 - fw / 2, 46, fw, 20, 21, FRIEND);
        if (ew > 0) f.sprite("bar_r_fill", "crucible_bar_fill_r", rx - 283 + ew / 2, 46, ew, 20, 21, ENEMY);
        f.sprite("timer_plate", "crucible_timer_plate", 960, 46, PLATE_W, 64, 22, 0x0A0F15);
        f.text("timer", bold(String.format(Locale.ROOT, "%d:%02d", seconds / 60, seconds % 60), WHITE), 960, 33, 30, 220, 30);
        f.text("score_l", bold(String.valueOf(mine), FRIEND), lx - 250, 31, 28, 160, 30);
        f.text("score_r", bold(String.valueOf(theirs), ENEMY), rx + 250, 31, 28, 160, 30);
        for (int i = 0; i < ControlMatch.ZONE_IDS.size(); i++) {
            String id = ControlMatch.ZONE_IDS.get(i);
            var zone = snap.zones().get(id);
            float zx = zoneX(i), zy = 124;
            int owner = zone.owner() == null ? NEUTRAL : zone.owner() == own ? FRIEND : ENEMY;
            f.sprite("z_bg" + i, "crucible_diamond_bg", zx, zy, 66, 66, 20, 0x070B10);
            if (zone.capturingTeam() != null && zone.progress() > 0.01) {
                int capColor = zone.capturingTeam() == own ? FRIEND : ENEMY;
                int frame = diamondFrame(zone.progress());
                if (frame > 0) f.sprite("z_fill" + i, String.format(Locale.ROOT, "crucible_diamond_fill_%02d", frame), zx, zy, 66, 66, 21, zone.contested() ? WHITE : capColor);
            } else if (zone.owner() != null) {
                f.sprite("z_fill" + i, "crucible_diamond_fill_10", zx, zy, 66, 66, 21, dim(owner, .55));
            }
            f.sprite("z_ring" + i, "crucible_diamond_ring", zx, zy, 66, 66, 22, owner);
            f.sprite("z_letter" + i, "crucible_letter_" + id.toLowerCase(Locale.ROOT), zx, zy, 40, 40, 23, WHITE);
        }
        if (snap.paused()) {
            f.sprite("pause_banner", "crucible_banner", 960, 214, 760, 70, 20, DARK);
            f.text("pause", c("상대 팀 복귀 대기 · " + (snap.forfeitRemainingTicks() + 19) / 20 + "초", NEUTRAL), 960, 202, 24, 700, 30);
        }
        if (respawnTicks > 0) {
            f.sprite("respawn_banner", "crucible_banner", 960, 640, 640, 110, 20, DARK);
            f.text("respawn_label", c("부활 준비", GREY), 960, 606, 24, 400, 30);
            f.text("respawn_num", bold(String.valueOf((respawnTicks + 19) / 20), WHITE), 960, 640, 60, 300, 30);
        }
    }

    private static void toastPanel(Frame f, Toast t) {
        f.sprite("toast_banner", "crucible_banner", 960, 214, 760, 96, 20, DARK);
        f.sprite("toast_line", "crucible_line", 960, 252, 460, 3, 22, t.color);
        f.text("toast_title", bold(t.title, t.color), 960, 196, 32, 700, 30);
        f.text("toast_sub", c(t.sub, GREY), 960, 232, 20, 700, 30);
    }

    // ---- RESULTS --------------------------------------------------------------------------------------------------
    private static void results(Frame f, ControlMatch.Snapshot snap, ControlMatch.Team own, ControlMatch.Team foe) {
        boolean draw = snap.winner() == null, win = snap.winner() == own;
        int color = draw ? NEUTRAL : win ? FRIEND : ENEMY;
        f.sprite("res_banner", "crucible_banner", 960, 330, 1500, 220, 20, DARK);
        f.sprite("res_line", "crucible_line", 960, 418, 900, 4, 22, color);
        f.text("res_title", bold(draw ? "무승부" : win ? "승리" : "패배", color), 960, 270, 96, 700, 30);
        f.text("res_score", bold(snap.scores().get(own) + "  :  " + snap.scores().get(foe), WHITE), 960, 372, 40, 700, 30);
        f.text("res_sub", c(((snap.remainingTicks() + 19) / 20) + "초 후 탑으로 복귀합니다", GREY), 960, 432, 22, 700, 30);
    }
}
