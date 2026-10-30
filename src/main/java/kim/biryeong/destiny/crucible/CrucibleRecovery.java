package kim.biryeong.destiny.crucible;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.GameType;

/** Saved with player data so a restart cannot strand an arena player in adventure mode. */
final class CrucibleRecovery {
    record State(String mode, String team, boolean noGravity) {
        static final Codec<State> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.STRING.fieldOf("mode").forGetter(State::mode),
                Codec.STRING.optionalFieldOf("team", "").forGetter(State::team),
                Codec.BOOL.optionalFieldOf("no_gravity", false).forGetter(State::noGravity)
        ).apply(i, State::new));
    }
    static final AttachmentType<State> DATA = AttachmentRegistry.create(
            DestinyGuardians.id("crucible_return"), b -> b.persistent(State.CODEC).copyOnDeath());

    private CrucibleRecovery() { }
    static void init() { }
    static boolean pending(ServerPlayer p) { return p.getAttached(DATA) != null; }
    static void remember(ServerPlayer p) {
        if (!pending(p)) p.setAttached(DATA, new State(p.gameMode().getName(),
                p.getTeam() == null ? "" : p.getTeam().getName(), p.isNoGravity()));
    }
    static void restore(ServerPlayer p) {
        State state = p.getAttached(DATA);
        if (state == null) return;
        p.setGameMode(GameType.byName(state.mode(), GameType.SURVIVAL));
        p.setNoGravity(state.noGravity());
        var board = p.level().getServer().getScoreboard();
        // A different system's later team assignment is not ours to remove.
        if (p.getTeam() == null || p.getTeam().getName().startsWith("dg_control_")) {
            if (p.getTeam() != null) board.removePlayerFromTeam(p.getScoreboardName());
            if (!state.team().isEmpty() && board.getPlayerTeam(state.team()) != null)
                board.addPlayerToTeam(p.getScoreboardName(), board.getPlayerTeam(state.team()));
        }
    }
    static void finish(ServerPlayer p) { p.removeAttached(DATA); }
}
