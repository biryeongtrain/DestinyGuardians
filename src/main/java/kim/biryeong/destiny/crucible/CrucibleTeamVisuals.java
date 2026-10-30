package kim.biryeong.destiny.crucible;

import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetPlayerTeamPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.scores.PlayerTeam;
import net.minecraft.world.scores.Scoreboard;
import net.minecraft.world.scores.Team;
import net.minecraft.world.scores.TeamColor;

import java.util.*;

/** Connection-owned vanilla nameplates. No server team mutation, glow, or through-wall enemy names. */
public final class CrucibleTeamVisuals {
    public static final int FRIEND = TeamColor.AQUA.rgb(), ENEMY = TeamColor.RED.rgb();
    private static final Map<UUID, View> VIEWS = new HashMap<>();
    private record Assignment(int group, PlayerTeam authoritative) { }
    private static final class View {
        final ServerPlayer player;
        final List<PlayerTeam> teams;
        Map<String, Assignment> assigned = Map.of();
        boolean installed;
        View(ServerPlayer player) {
            this.player = player;
            var board = new Scoreboard();
            String prefix;
            // Client-only names never shadow an existing authoritative team.
            do { prefix = "dgV" + UUID.randomUUID().toString().replace("-", "").substring(0, 10); }
            while (player.level().getServer().getScoreboard().getPlayerTeam(prefix + "0") != null
                    || player.level().getServer().getScoreboard().getPlayerTeam(prefix + "1") != null
                    || player.level().getServer().getScoreboard().getPlayerTeam(prefix + "2") != null);
            var groups = new ArrayList<PlayerTeam>();
            for (int i = 0; i < 3; i++) {
                var team = board.addPlayerTeam(prefix + i);
                team.setColor(Optional.of(i == 0 ? TeamColor.AQUA : TeamColor.RED));
                team.setPlayerPrefix(Component.literal(i == 0 ? "◆ 아군 · " : "◆ 적 · ")
                        .withColor(i == 0 ? FRIEND : ENEMY));
                team.setAllowFriendlyFire(false);
                team.setSeeFriendlyInvisibles(false);
                team.setCollisionRule(Team.CollisionRule.NEVER);
                team.setNameTagVisibility(i == 2 ? Team.Visibility.NEVER : Team.Visibility.ALWAYS);
                groups.add(team);
            }
            teams = List.copyOf(groups);
        }
    }
    private CrucibleTeamVisuals() { }

    /** Call after roster/authoritative-team changes and on the normal match tick. */
    public static void refresh(Collection<ServerPlayer> roster) {
        var players = List.copyOf(roster);
        for (View view : List.copyOf(VIEWS.values()))
            if (!players.contains(view.player) || view.player.hasDisconnected()) remove(view.player);
        for (ServerPlayer viewer : players) {
            if (viewer.hasDisconnected() || viewer.isRemoved() || CrucibleRuntime.team(viewer) == null) continue;
            View view = VIEWS.get(viewer.getUUID());
            if (view != null && view.player != viewer) { remove(view.player); view = null; }
            if (view == null) { view = new View(viewer); VIEWS.put(viewer.getUUID(), view); }
            var desired = new LinkedHashMap<String, Assignment>();
            for (ServerPlayer target : players) {
                var side = CrucibleRuntime.team(target);
                PlayerTeam actual = target.getTeam();
                // A foreign scoreboard owner wins. We only decorate the match's own assignments.
                if (side == null || target.level() != viewer.level() || actual == null
                        || !actual.getName().equals("dg_control_" + side.name().toLowerCase(Locale.ROOT))) continue;
                boolean friend = CrucibleRuntime.team(viewer) == side;
                int group = friend ? 0 : visibleEnemy(viewer, target) ? 1 : 2;
                desired.put(target.getScoreboardName(), new Assignment(group, actual));
            }
            if (!view.assigned.equals(desired)) rebuild(view, desired);
        }
    }

    private static boolean visibleEnemy(ServerPlayer viewer, ServerPlayer target) {
        return viewer.isAlive() && target.isAlive() && !target.isInvisible() && !target.isSpectator()
                && viewer.getEyePosition().distanceToSqr(target.getEyePosition()) <= 48 * 48
                && viewer.level().clip(new ClipContext(viewer.getEyePosition(), target.getEyePosition(),
                    ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, viewer)).getType() == HitResult.Type.MISS;
    }

    private static void rebuild(View view, Map<String, Assignment> desired) {
        CameraViews.sending(() -> {
            uninstall(view);
            for (var team : view.teams) team.getPlayers().clear();
            desired.forEach((name, assignment) -> view.teams.get(assignment.group()).getPlayers().add(name));
            view.assigned = Map.copyOf(desired);
            for (var team : view.teams) view.player.connection.send(ClientboundSetPlayerTeamPacket.createAddOrModifyPacket(team, true));
            view.installed = true;
        });
    }

    private static void uninstall(View view) {
        if (!view.installed) return;
        view.installed = false;
        if (view.player.hasDisconnected()) return;
        // Remove whole owned teams: never issue REMOVE-player against a possibly newer foreign assignment.
        for (var team : view.teams) view.player.connection.send(ClientboundSetPlayerTeamPacket.createRemovePacket(team));
        var scoreboard = view.player.level().getServer().getScoreboard();
        for (String name : view.assigned.keySet()) {
            PlayerTeam current = scoreboard.getPlayersTeam(name);
            if (current != null) {
                view.player.connection.send(ClientboundSetPlayerTeamPacket.createAddOrModifyPacket(current, false));
                view.player.connection.send(ClientboundSetPlayerTeamPacket.createPlayerPacket(current, name,
                        ClientboundSetPlayerTeamPacket.Action.ADD));
            }
        }
    }

    /** Reapply after a native scoreboard membership broadcast (join/respawn). */
    public static void invalidate() {
        for (View view : List.copyOf(VIEWS.values())) {
            CameraViews.sending(() -> uninstall(view));
            view.assigned = Map.of();
        }
    }
    public static void remove(ServerPlayer player) {
        View view = VIEWS.get(player.getUUID());
        if (view == null || view.player != player || !VIEWS.remove(player.getUUID(), view)) return;
        CameraViews.sending(() -> uninstall(view));
    }
    public static void clear() { for (View view : List.copyOf(VIEWS.values())) remove(view.player); }
}
