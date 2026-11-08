package kim.biryeong.destiny.fireteam;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.inventory.HudPainter;
import kim.biryeong.destiny.inventory.WeaponScreenControls;
import kim.biryeong.destiny.inventory.WeaponScreenLayout.Box;
import kim.biryeong.destiny.weapon.WeaponAiming;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.phys.Vec3;

import java.util.*;
import java.util.function.Consumer;

/**
 * Destiny-style Fireteam Finder: a full-screen HUD (same pointer and input path as the gear screen) with the
 * activity categories on the left, the category's activities or the chosen activity's listings in the centre, and the
 * player's fireteam on the right. Everything shown is generated from {@link ActivityCatalog} and {@link Fireteams};
 * nothing here is activity-specific. One session per player, server thread.
 */
public final class FinderScreen {
    public static final String PREFIX = "destiny:finder_";
    private static final Map<UUID, Session> OPEN = new HashMap<>();
    private static final net.minecraft.resources.Identifier FREEZE = DestinyGuardians.id("finder_screen");
    static final int WHITE = 0xF2F2EE, MUTED = 0x9AA3AA, DIM = 0x5D666E, LINE = 0x3A434B, PANEL = 0x161B20, BACK = 0x0E1318,
            ACCENT = 0x7FB2E5, GOLD = 0xE3C46B, GOOD = 0x6FD08A, BAD = 0xE0645A, CARD = 0x1A2128, HOVER = 0x2E3740;
    static final int LIST_ROWS = 5;

    enum Page { CATEGORY, ACTIVITY }
    /** A clickable region of the last frame. */
    record Target(String key, Box box, Consumer<Session> action) { }

    static final class Session {
        final ServerPlayer owner; final ServerLevel level; final Object connection;
        Vec3 anchor;
        final WeaponScreenControls controls = new WeaponScreenControls();
        Page page = Page.CATEGORY;
        String category, activity;
        int listPage, lastClick = Integer.MIN_VALUE / 2, lastActive;
        Input input = Input.EMPTY;
        List<Target> targets = List.of();
        String focus = "";
        String message = ""; boolean messageGood; int messageUntil;
        Session(ServerPlayer p) {
            owner = p; level = p.level(); connection = p.connection; anchor = p.position();
            controls.baseline(p.getYRot(), p.getXRot());
            controls.point(960, 540);
            lastActive = p.level().getServer().getTickCount();
            var cats = ActivityCatalog.categories();
            category = cats.isEmpty() ? null : cats.getFirst().id();
            // Open on the fireteam's activity, so a member sees what the leader picked.
            Fireteams.team(p).flatMap(t -> ActivityCatalog.find(t.activity())).ifPresent(a -> {
                category = a.category(); activity = a.id(); page = Page.ACTIVITY;
            });
        }
    }

    private FinderScreen() { }

    static void init() {
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(FinderScreen::tick);
        net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents.DISCONNECT.register((h, s) -> close(h.getPlayer()));
        net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((p, a, b) -> close(p));
        net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.AFTER_DEATH.register((e, s) -> { if (e instanceof ServerPlayer p) close(p); });
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            for (var s : List.copyOf(OPEN.values())) if (s.level.getServer() == server) retire(s);
        });
    }

    public static boolean active(ServerPlayer p) { return current(p) != null; }
    /** The player has opened one activity's detail page (tutorial guide). */
    public static boolean onActivityPage(ServerPlayer p) { var s = current(p); return s != null && s.page == Page.ACTIVITY; }
    private static Session current(ServerPlayer p) {
        var s = OPEN.get(p.getUUID());
        return s != null && s.owner == p && s.connection == p.connection ? s : null;
    }

    static String blocked(ServerPlayer p) {
        if (!p.level().getServer().isSameThread() || !p.isAlive() || p.isRemoved() || p.hasDisconnected() || p.isSpectator())
            return "지금은 화력팀 탐색기를 열 수 없습니다.";
        if (ActivityCatalog.busy(p) || kim.biryeong.destiny.tutorial.Tutorial.active(p)
                || kim.biryeong.destiny.crucible.CrucibleRuntime.participating(p))
            return "활동 중에는 화력팀 탐색기를 열 수 없습니다.";
        if (Fireteams.dark(p)) return "출발 중입니다.";
        if (p.isSleeping() || p.isPassenger() || p.getCamera() != p || AbilityService.inSuper(p)
                || kim.biryeong.destiny.down.GuardianDown.active(p) || p.containerMenu != p.inventoryMenu)
            return "현재 동작을 마친 뒤 화력팀 탐색기를 여세요.";
        return null;
    }

    public static boolean open(ServerPlayer p) {
        if (active(p)) return true;
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(p)) kim.biryeong.destiny.inventory.WeaponScreen.close(p);
        String reason = blocked(p);
        if (reason != null) { p.sendOverlayMessage(Component.literal(reason)); return false; }
        var old = OPEN.get(p.getUUID()); if (old != null) retire(old);
        WeaponRuntime.cancelUseForSkill(p); WeaponAiming.suspend(p); p.stopUsingItem();
        p.setSprinting(false); p.setShiftKeyDown(false); p.setLastClientInput(Input.EMPTY);
        p.setDeltaMovement(new Vec3(0, Math.min(0, p.getDeltaMovement().y), 0));
        freeze(p, Attributes.MOVEMENT_SPEED); freeze(p, Attributes.JUMP_STRENGTH);
        var s = new Session(p); OPEN.put(p.getUUID(), s);
        CombatHud.remove(p); p.inventoryMenu.broadcastFullState();
        FinderSounds.play(p, SoundEvents.UI_BUTTON_CLICK, .35f, 1.5f);
        render(s); return true;
    }

    private static void freeze(ServerPlayer p, Holder<Attribute> type) {
        var attr = p.getAttribute(type);
        if (attr != null) { attr.removeModifier(FREEZE); attr.addTransientModifier(new AttributeModifier(FREEZE, -1, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL)); }
    }

    public static void close(ServerPlayer p) { var s = current(p); if (s != null) retire(s); }

    private static void retire(Session s) {
        if (!OPEN.remove(s.owner.getUUID(), s)) return;
        HudPainter.clear(s.owner, PREFIX);
        for (var type : List.of(Attributes.MOVEMENT_SPEED, Attributes.JUMP_STRENGTH)) {
            var attr = s.owner.getAttribute(type); if (attr != null) attr.removeModifier(FREEZE);
        }
        s.owner.setLastClientInput(Input.EMPTY);
        if (!s.owner.hasDisconnected()) s.owner.inventoryMenu.broadcastFullState();
    }

    static void refreshAll() { for (var s : List.copyOf(OPEN.values())) render(s); }

    // ------------------------------------------------------------------ input (routed through WeaponScreen)

    public static boolean move(ServerPlayer p, ServerboundMovePlayerPacket packet) {
        var s = current(p); if (s == null) return false;
        if (packet.hasRotation()) {
            float yaw = packet.getYRot(p.getYRot()), pitch = packet.getXRot(p.getXRot());
            if (Float.isFinite(yaw) && Float.isFinite(pitch)) {
                p.setYRot(yaw); p.setYHeadRot(yaw); p.setXRot(Math.clamp(pitch, -90, 90));
                float lastYaw = s.controls.yaw(), lastPitch = s.controls.pitch();
                if (s.controls.rotate(yaw, pitch)) { s.lastActive = now(s); if (hover(s)) render(s); else cursor(s); }
                else if (lastYaw != s.controls.yaw() || lastPitch != s.controls.pitch()) cursor(s);
            }
        }
        if (packet.hasPosition()) {
            double x = packet.getX(s.anchor.x), y = packet.getY(p.getY()), z = packet.getZ(s.anchor.z);
            double dx = x - s.anchor.x, dz = z - s.anchor.z;
            if (!Double.isFinite(x + y + z) || dx * dx + dz * dz > .0001) pin(p, s.anchor.x, Double.isFinite(y) ? y : p.getY(), s.anchor.z);
            else { p.absSnapTo(s.anchor.x, y, s.anchor.z); p.setOnGround(packet.isOnGround()); }
            if (Double.isFinite(y)) s.anchor = new Vec3(s.anchor.x, y, s.anchor.z);
        }
        return true;
    }

    private static void pin(ServerPlayer p, double x, double y, double z) {
        p.connection.teleport(new net.minecraft.world.entity.PositionMoveRotation(new Vec3(x, y, z), Vec3.ZERO, 0, 0),
                Set.of(net.minecraft.world.entity.Relative.Y_ROT, net.minecraft.world.entity.Relative.X_ROT));
    }

    public static boolean input(ServerPlayer p, Input next) {
        var s = current(p); if (s == null) return false;
        Input old = s.input; s.input = next; s.lastActive = now(s);
        if (next.jump() && !old.jump()) click(p, false);
        return true;
    }

    /** Left click / Space activates the hovered target; right click goes back a page, then closes. */
    public static boolean click(ServerPlayer p, boolean back) {
        var s = current(p); if (s == null) return false;
        int now = now(s); if (now - s.lastClick < 3) return true;
        s.lastClick = now; s.lastActive = now;
        if (back) {
            if (s.page == Page.ACTIVITY) { s.page = Page.CATEGORY; s.listPage = 0; sound(s, .9f); render(s); }
            else close(p);
            return true;
        }
        hover(s);
        for (var t : s.targets) if (t.key().equals(s.focus)) {
            // Accepted play carries its own exact click+countdown recording from tick0.
            if (!Set.of("play", "play_solo", "ft_play", "retarget").contains(t.key()) && !t.key().startsWith("card_")) sound(s, 1.4f);
            t.action().accept(s);
            if (current(p) == s) render(s);
            return true;
        }
        return true;
    }

    /** QA: park the pointer at canvas coordinates and hover what is under it. */
    public static boolean qaPoint(ServerPlayer p, float x, float y) {
        var s = current(p); if (s == null) return false;
        s.controls.point(x, y); hover(s); render(s); return true;
    }

    /** Focus the target under the pointer. True when the focus changed (the frame must be redrawn). */
    private static boolean hover(Session s) {
        String before = s.focus;
        s.focus = "";
        for (int i = s.targets.size() - 1; i >= 0; i--) {
            var t = s.targets.get(i);
            if (t.box().contains(s.controls.x(), s.controls.y())) { s.focus = t.key(); break; }
        }
        return !s.focus.equals(before);
    }

    private static void sound(Session s, float pitch) {
        FinderSounds.play(s.owner, SoundEvents.UI_BUTTON_CLICK, .3f, pitch);
    }
    static void notice(Session s, String text, boolean good) { s.message = text; s.messageGood = good; s.messageUntil = now(s) + 80; }
    /** Shows {@code error} or {@code ok} as the frame notice. */
    private static void result(Session s, String error, String ok) {
        if (error != null) { notice(s, error, false); FinderSounds.play(s.owner, SoundEvents.VILLAGER_NO, .4f, 1f); }
        else if (ok != null) notice(s, ok, true);
    }
    private static int now(Session s) { return s.level.getServer().getTickCount(); }

    private static void tick(MinecraftServer server) {
        for (var s : List.copyOf(OPEN.values())) {
            if (s.level.getServer() != server) continue;
            var p = s.owner;
            double dx = p.getX() - s.anchor.x, dz = p.getZ() - s.anchor.z;
            if (p.hasDisconnected() || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.level() != s.level
                    || p.isPassenger() || p.isSleeping() || p.getCamera() != p || AbilityService.inSuper(p)
                    || kim.biryeong.destiny.down.GuardianDown.active(p)
                    || dx * dx + dz * dz > .25 || now(s) - s.lastActive > 20 * 300) { retire(s); continue; }
            var v = p.getDeltaMovement(); p.setDeltaMovement(0, v.y, 0);
            if (now(s) % 10 == 0 || (s.messageUntil > 0 && now(s) >= s.messageUntil)) render(s);
        }
    }

    // ------------------------------------------------------------------ drawing

    /** Draw state for one frame; targets are registered as they are drawn so hit-testing matches the picture. */
    private static final class Frame {
        final Session s; final HudPainter p; final List<Target> targets = new ArrayList<>();
        Frame(Session s) { this.s = s; this.p = new HudPainter(s.owner, PREFIX); }
        boolean focused(String key) { return key.equals(s.focus); }
        void target(String key, Box b, Consumer<Session> action) { targets.add(new Target(key, b, action)); }
    }

    /** Only the pointer moved: refresh it without rebuilding the frame. */
    private static void cursor(Session s) {
        var p = new HudPainter(s.owner, PREFIX);
        p.pointer("cursor", "gear_cursor", s.controls.x(), s.controls.y(), 30, 152, s.controls.yaw(), s.controls.pitch());
    }

    static void render(Session s) { render(s, false); }

    private static void render(Session s, boolean again) {
        if (s.messageUntil > 0 && now(s) >= s.messageUntil) { s.message = ""; s.messageUntil = 0; }
        var cats = ActivityCatalog.categories();
        if (s.category == null || ActivityCatalog.category(s.category).isEmpty()) s.category = cats.isEmpty() ? null : cats.getFirst().id();
        if (s.page == Page.ACTIVITY && ActivityCatalog.find(s.activity).isEmpty()) s.page = Page.CATEGORY;
        var f = new Frame(s);
        var p = f.p;
        var category = ActivityCatalog.category(s.category).orElse(null);
        p.backdrop("backdrop", 100, BACK);
        // The selected category's (or activity's) art, dimmed, behind the whole screen.
        String art = s.page == Page.ACTIVITY ? ActivityCatalog.find(s.activity).map(ActivityCatalog.Activity::banner).orElse(null)
                : category == null ? null : category.banner();
        if (art != null) p.image("art", art, 960, 540, 1920, 1080, 100.5f, 0x2A2F35);
        for (int i = 0; i < 4; i++) p.rect("veil_" + i, 960, 540, 1920 - i * 360, 1080, 100.6f + i * .1f, mix(BACK, 0x101820, i / 4f));
        header(f, category);
        nav(f, cats);
        if (s.page == Page.CATEGORY) categoryPage(f, category); else activityPage(f, ActivityCatalog.find(s.activity).orElseThrow());
        fireteamPanel(f);
        footer(f);
        p.pointer("cursor", "gear_cursor", s.controls.x(), s.controls.y(), 30, 152, s.controls.yaw(), s.controls.pitch());
        p.finish();
        s.targets = List.copyOf(f.targets);
        // The new frame may have moved a target under the pointer: redraw once with the corrected focus.
        if (hover(s) && !again) render(s, true);
    }

    private static void header(Frame f, ActivityCatalog.Category category) {
        var p = f.p; var s = f.s;
        p.icon("title_icon", "fireteam/mode_strikes", 96, 96, 56, 110, WHITE);
        p.textLeft("title", "화력팀 탐색기", 140, 70, 32, WHITE, 600, 255);
        String crumb = "활동" + (category == null ? "" : "  /  " + category.name())
                + (s.page == Page.ACTIVITY ? ActivityCatalog.find(s.activity).map(a -> "  /  " + a.name()).orElse("") : "");
        p.textLeft("crumb", crumb, 142, 112, 20, MUTED, 900, 255);
        int open = (int) Fireteams.roster().all().stream().filter(FireteamRoster.Team::recruiting).count();
        p.textRight("open_count", "모집 중인 화력팀  " + open, 1840, 92, 20, MUTED, 255);
        p.rect("header_rule", 960, 150, 1760, 1, 104, LINE);
    }

    private static void nav(Frame f, List<ActivityCatalog.Category> cats) {
        var p = f.p; var s = f.s;
        p.textLeft("nav_label", "활동", 120, 186, 18, DIM, 300, 255);
        for (int i = 0; i < cats.size(); i++) {
            var c = cats.get(i);
            var b = new Box(290, 260 + i * 100, 340, 84);
            String key = "nav_" + c.id();
            boolean selected = c.id().equals(s.category), hot = f.focused(key);
            p.rect(key + "_bg", b.x(), b.y(), b.width(), b.height(), 106, selected ? 0x26303A : hot ? HOVER : 0x141A20);
            if (selected) p.rect(key + "_bar", b.x() - b.width() / 2 + 3, b.y(), 6, b.height(), 107, WHITE);
            if (hot) p.frame(key + "_edge", b, 2, 108, WHITE);
            p.icon(key + "_icon", c.icon(), b.x() - b.width() / 2 + 46, b.y(), 48, 108, selected ? WHITE : MUTED);
            p.textLeft(key + "_name", c.name(), b.x() - b.width() / 2 + 86, b.y() - 24, 24, selected ? WHITE : 0xC9D1D8, 240, 255);
            long listings = ActivityCatalog.activities(c.id()).stream().mapToLong(a -> Fireteams.roster().listings(a.id()).size()).sum();
            p.textLeft(key + "_sub", ActivityCatalog.activities(c.id()).size() + "개 활동  ·  모집 " + listings, b.x() - b.width() / 2 + 86, b.y() + 6, 16, MUTED, 240, 255);
            f.target(key, b, ss -> { ss.category = c.id(); ss.page = Page.CATEGORY; ss.listPage = 0; });
        }
    }

    private static void categoryPage(Frame f, ActivityCatalog.Category category) {
        var p = f.p;
        if (category == null) { p.text("empty", "등록된 활동이 없습니다.", 950, 540, 22, MUTED); return; }
        p.textLeft("cat_name", category.name(), 500, 184, 34, WHITE, 900, 255);
        p.textLeft("cat_desc", category.description(), 502, 232, 18, MUTED, 900, 255);
        var list = ActivityCatalog.activities(category.id());
        for (int i = 0; i < list.size() && i < 6; i++) {
            var a = list.get(i);
            float cx = 725 + (i % 2) * 455, cy = 430 + (i / 2) * 330;
            var b = new Box(cx, cy, 430, 290);
            String key = "card_" + a.id();
            boolean hot = f.focused(key);
            p.rect(key + "_bg", cx, cy, 430, 290, 106, hot ? HOVER : CARD);
            p.image(key + "_art", a.banner(), cx, cy - 32, 426, 226, 107, hot ? 0xFFFFFF : 0xC8C8C8);
            p.rect(key + "_strip", cx, cy + 104, 430, 82, 108, 0x10151A);
            p.textLeft(key + "_type", a.type(), cx - 200, cy + 70, 15, MUTED, 400, 255);
            p.textLeft(key + "_name", a.name(), cx - 200, cy + 92, 24, WHITE, 300, 255);
            int open = Fireteams.roster().listings(a.id()).size();
            p.textRight(key + "_size", a.sizeLabel() + (a.maxPlayers() > 1 ? "  ·  모집 " + open : "  ·  1인"), cx + 200, cy + 96, 17, open > 0 ? GOOD : MUTED, 255);
            if (hot) p.frame(key + "_edge", b, 2, 110, WHITE);
            f.target(key, b, ss -> selectActivity(ss, a));
        }
    }

    private static void selectActivity(Session s, ActivityCatalog.Activity activity) {
        if (current(s.owner) != s || s.owner.level() != s.level || s.owner.hasDisconnected()
                || ActivityCatalog.find(activity.id()).orElse(null) != activity) return;
        String previous = s.activity;
        s.activity = activity.id(); s.page = Page.ACTIVITY; s.listPage = 0;
        FinderSounds.activityChanged(s.owner, previous, s.activity);
    }

    private static void activityPage(Frame f, ActivityCatalog.Activity a) {
        var p = f.p; var s = f.s;
        var me = Fireteams.team(s.owner).orElse(null);
        button(f, "back", new Box(560, 186, 140, 44), "<  활동 목록", true, ss -> { ss.page = Page.CATEGORY; ss.listPage = 0; });
        p.image("act_art", a.banner(), 720, 380, 440, 248, 106, 0xFFFFFF);
        p.frame("act_art_edge", new Box(720, 380, 440, 248), 1, 107, LINE);
        p.textLeft("act_type", a.type(), 966, 266, 17, MUTED, 430, 255);
        p.textLeft("act_name", a.name(), 964, 292, 34, WHITE, 430, 255);
        p.wrappedLeft("act_desc", a.description(), 966, 348, 18, 0xC9D1D8, 430, 3, 26, 255);
        p.textLeft("act_size", "화력팀 " + a.sizeLabel(), 966, 440, 18, GOLD, 430, 255);

        // Actions for this activity.
        boolean leader = me != null && me.leader().equals(s.owner.getUUID());
        boolean here = me != null && me.activity().equals(a.id());
        var launching = me == null ? null : Fireteams.launch(me).orElse(null);
        if (launching != null && launching.cancelable()) {
            int seconds = launching.secondsLeft();
            p.textLeft("act_launch", seconds > 0 ? "출발까지 " + seconds + "초" : "출발 준비 중", 966, 478, 22, GOLD, 430, 255);
        } else if (me == null) {
            if (a.maxPlayers() > 1) button(f, "recruit", new Box(1060, 496, 196, 52), "화력팀 모집", true,
                    ss -> result(ss, Fireteams.create(ss.owner, a, true), a.name() + " 화력팀 모집을 시작했습니다."));
            button(f, "play_solo", new Box(a.maxPlayers() > 1 ? 1276 : 1060, 496, 196, 52), "플레이", true,
                    ss -> result(ss, Fireteams.play(ss.owner, a), null));
        } else if (!here) {
            if (leader) button(f, "retarget", new Box(1100, 496, 276, 52), "이 활동으로 변경", true,
                    ss -> result(ss, Fireteams.retarget(ss.owner, a), "목표 활동을 바꿨습니다."));
            else p.textLeft("act_other", "화력팀은 다른 활동을 목표로 하고 있습니다.", 966, 488, 18, MUTED, 430, 255);
        } else if (leader) {
            button(f, "play", new Box(1060, 496, 196, 52), "플레이", true, ss -> result(ss, Fireteams.play(ss.owner, null), null));
        } else p.textLeft("act_wait", "화력팀장이 플레이를 누르면 출발합니다.", 966, 488, 18, MUTED, 430, 255);

        // Listings.
        p.rect("list_rule", 950, 560, 900, 1, 104, LINE);
        if (a.maxPlayers() < 2) {
            p.textLeft("list_title", "1인 전용 활동", 500, 584, 22, WHITE, 600, 255);
            p.textLeft("list_note", "이 활동은 화력팀 모집 없이 혼자 진행합니다.", 502, 622, 18, MUTED, 800, 255);
            return;
        }
        var listings = Fireteams.roster().listings(a.id());
        p.textLeft("list_title", "모집 중인 화력팀  " + listings.size(), 500, 584, 22, WHITE, 600, 255);
        int pages = Math.max(1, (listings.size() + LIST_ROWS - 1) / LIST_ROWS);
        s.listPage = Math.clamp(s.listPage, 0, pages - 1);
        if (listings.isEmpty()) p.textLeft("list_empty", "아직 모집 중인 화력팀이 없습니다. 화력팀 모집으로 첫 모집 글을 올려 보세요.", 502, 640, 18, MUTED, 880, 255);
        for (int i = 0; i < LIST_ROWS; i++) {
            int index = s.listPage * LIST_ROWS + i;
            if (index >= listings.size()) break;
            var t = listings.get(index);
            float y = 660 + i * 70;
            var row = new Box(950, y, 900, 62);
            String key = "row_" + i;
            boolean mine = me == t, hot = f.focused(key);
            f.target(key, row, ss -> { });
            p.rect(key + "_bg", row.x(), row.y(), row.width(), row.height(), 106, mine ? 0x1F2E3A : hot ? HOVER : CARD);
            if (mine) p.rect(key + "_bar", 503, y, 6, 62, 107, ACCENT);
            p.textLeft(key + "_leader", t.name(t.leader()), 520, y - 22, 22, WHITE, 260, 255);
            p.textLeft(key + "_tags", t.tags().isEmpty() ? "태그 없음" : String.join("  ·  ", t.tags()), 522, y + 6, 16, MUTED, 420, 255);
            for (int m = 0; m < a.maxPlayers(); m++)
                p.rect(key + "_pip" + m, 1010 + m * 26, y, 18, 18, 108, m < t.size() ? GOOD : 0x2A333B);
            p.textLeft(key + "_count", t.size() + " / " + a.maxPlayers(), 1010 + a.maxPlayers() * 26 + 6, y - 12, 18, MUTED, 120, 255);
            long minutes = Math.max(0, (Fireteams.now() - t.created()) / 1200);
            p.textRight(key + "_age", minutes < 1 ? "방금" : minutes + "분 전", 1226, y - 12, 16, DIM, 255);
            if (!mine && me == null && t.size() < a.maxPlayers())
                button(f, key + "_join", new Box(1318, y, 140, 44), "참가", true,
                        ss -> result(ss, Fireteams.join(ss.owner, t.id), t.name(t.leader()) + " 님의 화력팀에 합류했습니다."));
            else p.textRight(key + "_state", mine ? "내 화력팀" : t.size() >= a.maxPlayers() ? "정원 마감" : "", 1384, y - 12, 18, mine ? ACCENT : DIM, 255);
            if (hot) p.frame(key + "_edge", row, 1, 108, 0x6B747C);
        }
        if (pages > 1) {
            p.text("list_page", (s.listPage + 1) + " / " + pages, 950, 1022, 18, MUTED);
            if (s.listPage > 0) button(f, "list_prev", new Box(820, 1030, 90, 40), "<", true, ss -> ss.listPage--);
            if (s.listPage + 1 < pages) button(f, "list_next", new Box(1080, 1030, 90, 40), ">", true, ss -> ss.listPage++);
        }
    }

    private static void fireteamPanel(Frame f) {
        var p = f.p; var s = f.s;
        float cx = 1650, left = 1460;
        p.rect("ft_panel", cx, 590, 400, 860, 104, 0x12171C);
        p.textLeft("ft_title", "내 화력팀", left + 4, 176, 24, WHITE, 360, 255);
        var me = Fireteams.team(s.owner).orElse(null);
        if (me == null) {
            p.wrappedLeft("ft_none", "화력팀이 없습니다. 활동을 골라 화력팀을 모집하거나, 모집 중인 화력팀에 참가하세요.",
                    left + 4, 226, 18, MUTED, 370, 4, 26, 255);
            member(f, 0, s.owner.getUUID(), Fireteams.name(s.owner), false, false);
            return;
        }
        var a = ActivityCatalog.find(me.activity()).orElse(null);
        boolean leader = me.leader().equals(s.owner.getUUID());
        if (a != null) {
            p.image("ft_art", a.banner(), cx, 316, 380, 200, 106, 0xFFFFFF);
            p.rect("ft_art_strip", cx, 392, 380, 48, 107, 0x10151A);
            p.textLeft("ft_act", a.name(), left + 16, 378, 20, WHITE, 340, 255);
            var target = new Box(cx, 316, 380, 200);
            f.target("ft_art", target, ss -> { ss.category = a.category(); ss.activity = a.id(); ss.page = Page.ACTIVITY; });
            if (f.focused("ft_art")) p.frame("ft_art_edge", target, 2, 108, WHITE);
        }
        p.textLeft("ft_members", "화력팀원  " + me.size() + (a == null ? "" : " / " + a.maxPlayers()), left + 4, 438, 18, MUTED, 360, 255);
        var ids = me.members();
        for (int i = 0; i < ids.size(); i++) member(f, i, ids.get(i), me.name(ids.get(i)), i == 0, leader);
        float y = 490 + Math.max(ids.size(), 1) * 66 + 10;
        var launching = Fireteams.launch(me).orElse(null);
        if (leader && a != null && a.maxPlayers() > 1) {
            boolean listed = me.listed();
            button(f, "ft_listed", new Box(cx, y, 380, 46), listed ? "모집 공개 중  ·  끄기" : "모집 비공개  ·  공개하기", true,
                    ss -> result(ss, Fireteams.listed(ss.owner, !listed), listed ? "모집 글을 내렸습니다." : "모집 글을 올렸습니다."));
            y += 40;
            p.textLeft("ft_tags_label", "태그 (최대 " + FireteamRoster.MAX_TAGS + "개)", left + 4, y, 16, MUTED, 360, 255);
            y += 52;
            for (int i = 0; i < FireteamRoster.TAGS.size(); i++) {
                String tag = FireteamRoster.TAGS.get(i);
                boolean on = me.tags().contains(tag);
                var b = new Box(left + 64 + (i % 3) * 126, y + (i / 3) * 46, 118, 38);
                String key = "tag_" + i; boolean hot = f.focused(key);
                p.rect(key + "_bg", b.x(), b.y(), b.width(), b.height(), 106, on ? 0x2C4A5E : hot ? HOVER : 0x1A2128);
                p.frame(key + "_edge", b, 1, 107, on ? ACCENT : hot ? WHITE : LINE);
                p.textFit(key + "_label", tag, b.x(), b.y() - 11, 16, on ? WHITE : MUTED, b.width() - 8);
                f.target(key, b, ss -> result(ss, Fireteams.toggleTag(ss.owner, tag), null));
            }
            y += 2 * 46 + 10;
        } else if (!me.tags().isEmpty()) {
            p.textLeft("ft_tags_ro", String.join("  ·  ", me.tags()), left + 4, y - 14, 16, MUTED, 370, 255);
            y += 30;
        }
        if (launching != null && launching.cancelable()) {
            int seconds = launching.secondsLeft();
            p.text("ft_count", seconds > 0 ? "출발까지 " + seconds : "출발 준비 중", cx, 900, 30, GOLD);
            if (leader) button(f, "ft_cancel", new Box(cx, 966, 380, 54), "출발 취소", true, ss -> result(ss, Fireteams.cancel(ss.owner), null));
        } else if (me.inActivity()) {
            p.text("ft_busy", "화력팀이 활동 중입니다.", cx, 920, 20, MUTED);
        } else if (leader) {
            button(f, "ft_play", new Box(cx, 940, 380, 64), a == null ? "플레이" : "플레이  ·  " + a.name(), a != null,
                    ss -> result(ss, Fireteams.play(ss.owner, null), null));
        } else p.text("ft_wait", "화력팀장이 플레이를 누르길 기다리는 중", cx, 930, 18, MUTED);
        button(f, "ft_leave", new Box(cx, 1010, 380, 40), "화력팀 나가기", launching == null,
                ss -> { Fireteams.leave(ss.owner, null); notice(ss, "화력팀을 나갔습니다.", true); });
    }

    private static void member(Frame f, int i, UUID id, String name, boolean leaderRow, boolean viewerLeads) {
        var p = f.p; var s = f.s;
        float y = 490 + i * 66, left = 1460;
        String key = "member_" + i;
        p.rect(key + "_bg", 1650, y, 380, 58, 106, 0x1A2128);
        var online = s.owner.level().getServer().getPlayerList().getPlayer(id);
        var cls = online == null ? GuardianClass.NONE : kim.biryeong.destiny.guardian.Guardians.data(online).guardianClass();
        String icon = switch (cls) { case HUNTER -> "class_hunter_w248"; case TITAN -> "class_titan_w248"; case WARLOCK -> "class_warlock_w248"; default -> null; };
        int color = switch (cls) { case HUNTER -> 0x79B9DF; case TITAN -> 0xE57575; case WARLOCK -> 0xEDCE79; default -> MUTED; };
        if (icon != null) p.icon(key + "_class", icon, left + 30, y, 40, 108, color);
        p.textLeft(key + "_name", name, left + 60, y - 22, 20, online == null ? DIM : WHITE, 220, 255);
        p.textLeft(key + "_role", leaderRow ? "화력팀장" : online == null ? "접속 끊김" : viewerLeads || Fireteams.team(s.owner).isPresent() ? "화력팀원" : "화력팀 없음", left + 60, y + 2, 15, leaderRow ? GOLD : MUTED, 200, 255);
        if (viewerLeads && !id.equals(s.owner.getUUID())) {
            button(f, key + "_lead", new Box(left + 272, y, 70, 40), "팀장", true, ss -> result(ss, Fireteams.promote(ss.owner, id), null));
            button(f, key + "_kick", new Box(left + 348, y, 56, 40), "제외", true, ss -> result(ss, Fireteams.kick(ss.owner, id), null));
        }
    }

    private static void footer(Frame f) {
        var p = f.p; var s = f.s;
        p.rect("footer_rule", 960, 990, 1760, 1, 104, LINE);
        p.textLeft("footer_hint", "좌클릭 · Space 선택    우클릭 뒤로    E 닫기", 120, 1008, 18, MUTED, 900, 255);
        if (!s.message.isBlank()) p.text("message", s.message, 950, 950, 22, s.messageGood ? GOLD : BAD);
    }

    private static void button(Frame f, String key, Box b, String label, boolean enabled, Consumer<Session> action) {
        var p = f.p;
        boolean hot = enabled && f.focused(key);
        p.rect("btn_" + key, b.x(), b.y(), b.width(), b.height(), 108, !enabled ? 0x171C21 : hot ? 0x3A4650 : 0x232B32);
        p.frame("btn_" + key + "_edge", b, hot ? 2 : 1, 110, hot ? WHITE : LINE);
        p.textFit("btn_" + key + "_label", label, b.x(), b.y() - 12, 20, enabled ? WHITE : DIM, b.width() - 16);
        if (enabled) f.target(key, b, action);
    }

    static int mix(int a, int b, float t) {
        int r = Math.round(((a >> 16) & 255) + (((b >> 16) & 255) - ((a >> 16) & 255)) * t);
        int g = Math.round(((a >> 8) & 255) + (((b >> 8) & 255) - ((a >> 8) & 255)) * t);
        int bl = Math.round((a & 255) + ((b & 255) - (a & 255)) * t);
        return r << 16 | g << 8 | bl;
    }
}
