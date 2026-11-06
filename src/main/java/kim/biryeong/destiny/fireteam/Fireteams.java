package kim.biryeong.destiny.fireteam;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;

import java.util.*;

/**
 * Server side of the Fireteam Finder: the shared {@link FireteamRoster}, launches, notifications and the
 * {@code /화력팀} command. Every mutation goes through here so members are told and open finders refresh.
 * Server thread only.
 */
public final class Fireteams {
    private static final FireteamRoster ROSTER = new FireteamRoster();
    private static final Map<Long, ActivityLaunch> LAUNCHES = new HashMap<>();
    private static MinecraftServer server;
    private static boolean initialized;

    private Fireteams() { }

    public static void init() {
        if (initialized) return;
        initialized = true;
        FinderActivities.register();
        FinderScreen.init();
        ServerLifecycleEvents.SERVER_STARTED.register(s -> server = s);
        ServerLifecycleEvents.SERVER_STOPPING.register(s -> { for (var l : LAUNCHES.values()) l.abort(); LAUNCHES.clear(); FinderSounds.reset(s); });
        ServerLifecycleEvents.SERVER_STOPPED.register(s -> server = null);
        ServerTickEvents.END_SERVER_TICK.register(Fireteams::tick);
        ServerPlayConnectionEvents.DISCONNECT.register((h, s) -> leave(h.getPlayer(), "접속을 종료했습니다."));
        var hidden = kim.biryeong.destiny.hud.CombatHud.cinematic;
        kim.biryeong.destiny.hud.CombatHud.cinematic = hidden.or(Fireteams::dark);
        CommandRegistrationCallback.EVENT.register((d, access, env) -> {
            for (String name : new String[]{"화력팀", "fireteam"}) d.register(Commands.literal(name)
                    .executes(c -> FinderScreen.open(c.getSource().getPlayerOrException()) ? 1 : 0)
                    .then(Commands.literal("나가기").executes(c -> { leave(c.getSource().getPlayerOrException(), null); return 1; }))
                    .then(Commands.literal("취소").executes(c -> {
                        String e = cancel(c.getSource().getPlayerOrException());
                        if (e != null) { c.getSource().sendFailure(Component.literal(e)); return 0; }
                        return 1;
                    }))
                    .then(Commands.literal("point").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("player", net.minecraft.commands.arguments.EntityArgument.player())
                            .then(Commands.argument("x", com.mojang.brigadier.arguments.FloatArgumentType.floatArg(0, 1920))
                                .then(Commands.argument("y", com.mojang.brigadier.arguments.FloatArgumentType.floatArg(0, 1080))
                                    .executes(c -> FinderScreen.qaPoint(net.minecraft.commands.arguments.EntityArgument.getPlayer(c, "player"),
                                            com.mojang.brigadier.arguments.FloatArgumentType.getFloat(c, "x"),
                                            com.mojang.brigadier.arguments.FloatArgumentType.getFloat(c, "y")) ? 1 : 0)))))
                    .then(Commands.literal("click").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("player", net.minecraft.commands.arguments.EntityArgument.player())
                            .executes(c -> FinderScreen.click(net.minecraft.commands.arguments.EntityArgument.getPlayer(c, "player"), false) ? 1 : 0)))
                    .then(Commands.literal("상태").executes(c -> {
                        var p = c.getSource().getPlayerOrException();
                        c.getSource().sendSuccess(() -> Component.literal(describe(p)), false); return 1;
                    })));
        });
    }

    public static FireteamRoster roster() { return ROSTER; }
    public static Optional<FireteamRoster.Team> team(ServerPlayer p) { return ROSTER.team(p.getUUID()); }
    static Optional<ActivityLaunch> launch(FireteamRoster.Team t) { return Optional.ofNullable(LAUNCHES.get(t.id)); }
    /** The launch curtain holds this player in the dark. */
    public static boolean dark(ServerPlayer p) {
        var t = ROSTER.team(p.getUUID()).orElse(null);
        var l = t == null ? null : LAUNCHES.get(t.id);
        return l != null && l.dark(p);
    }

    static String name(ServerPlayer p) { return p.getGameProfile().name(); }
    static int now() { return server == null ? 0 : server.getTickCount(); }

    // ------------------------------------------------------------------ actions (null = success, else a reason)

    /** Recruit: a new fireteam for {@code activity}, listed in the finder. */
    static String create(ServerPlayer p, ActivityCatalog.Activity activity, boolean listed) {
        if (ROSTER.team(p.getUUID()).isPresent()) return FireteamRoster.Error.IN_FIRETEAM.message;
        if (ActivityCatalog.busy(p)) return "활동을 마친 뒤 화력팀을 만드세요.";
        if (listed && activity.maxPlayers() < 2) return "이 활동은 1인 전용이라 모집할 수 없습니다.";
        ROSTER.create(p.getUUID(), name(p), activity.id(), listed, now());
        changed(null);
        return null;
    }

    static String join(ServerPlayer p, long teamId) {
        var t = ROSTER.byId(teamId).orElse(null);
        if (t == null) return FireteamRoster.Error.GONE.message;
        if (ActivityCatalog.busy(p)) return "활동을 마친 뒤 참가하세요.";
        var activity = ActivityCatalog.find(t.activity()).orElse(null);
        if (activity == null) return FireteamRoster.Error.GONE.message;
        var e = ROSTER.join(p.getUUID(), name(p), teamId, activity.maxPlayers());
        if (e != null) return e.message;
        tell(t, name(p) + " 님이 화력팀에 합류했습니다.", true);
        changed(t);
        return null;
    }

    /** Leave (or be removed on disconnect). Cancels a countdown; the activity itself keeps its own roster. */
    public static void leave(ServerPlayer p, String why) {
        if (server != null) {
            var current = server.getPlayerList().getPlayer(p.getUUID());
            if (current != null && current != p) return; // A late disconnect cannot remove a replacement connection's team.
        }
        var t = ROSTER.team(p.getUUID()).orElse(null);
        if (t == null) return;
        var l = LAUNCHES.get(t.id);
        if (l != null && l.cancelable() && l.owns(p)) l.cancel(name(p) + " 님이 화력팀을 떠났습니다.");
        boolean wasLeader = t.leader().equals(p.getUUID());
        ROSTER.leave(p.getUUID());
        if (t.size() > 0) {
            tell(t, name(p) + " 님이 " + (why == null ? "화력팀을 떠났습니다." : why), false);
            if (wasLeader) tell(t, t.name(t.leader()) + " 님이 화력팀장이 되었습니다.", true);
        } else if (l != null && LAUNCHES.remove(t.id, l)) l.abort();
        changed(t);
    }

    static String kick(ServerPlayer leader, UUID target) {
        var t = ROSTER.team(leader.getUUID()).orElse(null);
        String targetName = t == null ? "?" : t.name(target);
        var e = ROSTER.kick(leader.getUUID(), target);
        if (e != null) return e.message;
        var kicked = server.getPlayerList().getPlayer(target);
        if (kicked != null) kicked.sendSystemMessage(Component.literal("화력팀에서 제외되었습니다.").withColor(0xE0645A));
        tell(t, targetName + " 님을 화력팀에서 제외했습니다.", false);
        changed(t);
        return null;
    }

    static String promote(ServerPlayer leader, UUID target) {
        var t = ROSTER.team(leader.getUUID()).orElse(null);
        var e = ROSTER.promote(leader.getUUID(), target);
        if (e != null) return e.message;
        tell(t, t.name(target) + " 님이 화력팀장이 되었습니다.", true);
        changed(t);
        return null;
    }

    static String retarget(ServerPlayer leader, ActivityCatalog.Activity activity) {
        if (server == null || !server.isSameThread() || server.getPlayerList().getPlayer(leader.getUUID()) != leader
                || leader.hasDisconnected() || leader.isRemoved()) return "현재 접속에서 다시 시도하세요.";
        var oldTeam = ROSTER.team(leader.getUUID()).orElse(null);
        String previous = oldTeam == null ? null : oldTeam.activity();
        var e = ROSTER.retarget(leader.getUUID(), activity.id(), activity.maxPlayers());
        if (e != null) return e.message;
        var t = ROSTER.team(leader.getUUID()).orElseThrow();
        if (Objects.equals(previous, activity.id())) return null;
        if (activity.maxPlayers() < 2) ROSTER.listed(leader.getUUID(), false);
        tell(t, "목표 활동: " + activity.name(), true, false);
        for (var id : t.members()) {
            var player = server.getPlayerList().getPlayer(id);
            if (player != null) FinderSounds.activityChanged(player, previous, activity.id());
        }
        changed(t);
        return null;
    }

    static String listed(ServerPlayer leader, boolean listed) {
        var t = ROSTER.team(leader.getUUID()).orElse(null);
        if (listed && t != null && ActivityCatalog.find(t.activity()).map(a -> a.maxPlayers() < 2).orElse(false))
            return "이 활동은 1인 전용이라 모집할 수 없습니다.";
        var e = ROSTER.listed(leader.getUUID(), listed);
        if (e != null) return e.message;
        changed(t);
        return null;
    }

    static String toggleTag(ServerPlayer leader, String tag) {
        var e = ROSTER.toggleTag(leader.getUUID(), tag);
        if (e != null) return e.message;
        changed(ROSTER.team(leader.getUUID()).orElse(null));
        return null;
    }

    /**
     * 플레이: the leader launches the fireteam's activity (a Guardian without a fireteam launches solo). Checks the
     * fireteam size and the activity's own preconditions before the countdown starts.
     */
    static String play(ServerPlayer p, ActivityCatalog.Activity soloActivity) {
        if (server == null || !server.isSameThread() || server.getPlayerList().getPlayer(p.getUUID()) != p
                || p.hasDisconnected() || p.isRemoved()) return "현재 접속에서 다시 시도하세요.";
        var t = ROSTER.team(p.getUUID()).orElse(null);
        if (t == null) {
            if (soloActivity == null) return "활동을 먼저 고르세요.";
            if (ActivityCatalog.busy(p)) return "진행 중인 활동을 마친 뒤 시작하세요.";
            t = ROSTER.create(p.getUUID(), name(p), soloActivity.id(), false, now());
        }
        if (!t.leader().equals(p.getUUID())) return "화력팀장만 활동을 시작할 수 있습니다.";
        if (LAUNCHES.containsKey(t.id)) return "이미 출발 준비 중입니다.";
        if (t.inActivity()) return "화력팀이 이미 활동 중입니다.";
        var activity = ActivityCatalog.find(t.activity()).orElse(null);
        if (activity == null) return "알 수 없는 활동입니다.";
        if (t.size() < activity.minPlayers() || t.size() > activity.maxPlayers())
            return activity.name() + "은(는) " + activity.sizeLabel() + " 활동입니다.";
        var online = new ArrayList<ServerPlayer>();
        for (var id : t.members()) {
            var m = server.getPlayerList().getPlayer(id);
            if (m == null || m.hasDisconnected()) return t.name(id) + " 님이 접속 중이 아닙니다.";
            online.add(m);
        }
        String error = activity.launcher().check(online);
        if (error != null) return error;
        ROSTER.launching(t, true);
        var launch = new ActivityLaunch(server, t, activity, List.copyOf(online));
        LAUNCHES.put(t.id, launch);
        // The countdown plays over the world (Destiny closes the director when the launch starts).
        for (var m : online) FinderScreen.close(m);
        launch.accept();
        tell(t, activity.name() + " · 1초 뒤 출발 카운트다운이 시작됩니다. /화력팀 취소로 멈출 수 있습니다.", true, false);
        changed(t);
        return null;
    }

    static String cancel(ServerPlayer leader) {
        var t = ROSTER.team(leader.getUUID()).orElse(null);
        if (t == null) return FireteamRoster.Error.NO_FIRETEAM.message;
        if (!t.leader().equals(leader.getUUID())) return FireteamRoster.Error.NOT_LEADER.message;
        var l = LAUNCHES.get(t.id);
        if (l == null || !l.cancelable() || !l.owns(leader)
                || server.getPlayerList().getPlayer(leader.getUUID()) != leader) return "취소할 수 있는 출발이 없습니다.";
        l.cancel("화력팀장이 취소했습니다.");
        return null;
    }

    // ------------------------------------------------------------------ tick & notifications

    private static void tick(MinecraftServer s) {
        FinderSounds.tick(s);
        for (var e : List.copyOf(LAUNCHES.entrySet())) {
            var l = e.getValue();
            try { l.tick(); }
            catch (RuntimeException ex) {
                kim.biryeong.destiny.DestinyGuardians.LOGGER.error("[Fireteams] launch tick failed", ex); l.abort();
            }
            if (l.phase() == ActivityLaunch.Phase.DONE && LAUNCHES.remove(e.getKey(), l)) {
                ROSTER.launching(l.team, false);
                changed(l.team);
            }
        }
        if (s.getTickCount() % 20 != 0) return;
        for (var t : List.copyOf(ROSTER.all())) {
            var activity = ActivityCatalog.find(t.activity()).orElse(null);
            boolean inside = false;
            if (activity != null) for (var id : t.members()) {
                var p = s.getPlayerList().getPlayer(id);
                if (p != null && activity.launcher().participating(p)) { inside = true; break; }
            }
            if (inside != t.inActivity()) { ROSTER.inActivity(t, inside); changed(t); }
        }
    }

    private static void tell(FireteamRoster.Team t, String text, boolean good) { tell(t, text, good, true); }
    private static void tell(FireteamRoster.Team t, String text, boolean good, boolean sound) {
        if (t == null || server == null) return;
        for (var id : t.members()) {
            var p = server.getPlayerList().getPlayer(id);
            if (p == null) continue;
            p.sendSystemMessage(Component.literal("[화력팀] ").withColor(0x7FB2E5).append(Component.literal(text).withColor(good ? 0xD8E2EA : 0xE0A35A)));
            if (sound) FinderSounds.play(p, SoundEvents.NOTE_BLOCK_CHIME, .4f, good ? 1.4f : .9f);
        }
    }

    /** Roster change: refresh every open finder (listings are shared). */
    private static void changed(FireteamRoster.Team t) { FinderScreen.refreshAll(); }

    public static String describe(ServerPlayer p) {
        var t = ROSTER.team(p.getUUID()).orElse(null);
        if (t == null) return "fireteam=-";
        var l = LAUNCHES.get(t.id);
        var names = new ArrayList<String>();
        for (var id : t.members()) names.add(t.name(id));
        return "fireteam=" + t.id + " activity=" + t.activity() + " leader=" + t.name(t.leader()) + " members=" + names
                + " listed=" + t.listed() + " tags=" + t.tags() + " launching=" + t.launching() + " inActivity=" + t.inActivity()
                + " launch=" + (l == null ? "-" : l.phase() + "/" + l.secondsLeft());
    }
}
