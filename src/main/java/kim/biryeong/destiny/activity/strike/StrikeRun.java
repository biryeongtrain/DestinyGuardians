package kim.biryeong.destiny.activity.strike;

import kim.biryeong.destiny.down.GuardianDown;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import java.util.UUID;

/**
 * One live run of a strike for one fireteam, as {@link StrikeHost} drives it. The strike implements this around its own
 * director, encounter and presentation; the host owns the run's lifetime (world, admission, ticking, return, cleanup).
 */
public interface StrikeRun {
    UUID id();
    ServerLevel level();
    /** Still part of the run: listed and not departed. */
    boolean member(UUID id);
    boolean closed();
    /** Players are in the world and the run is live (briefing included). */
    boolean running();
    /** The run is in its opening briefing, before combat is released. */
    boolean briefing();
    /** False while this run forbids the player to fight or use abilities. Called only for members. */
    boolean allows(ServerPlayer player);
    /** Preparation progress 0..1 for the launch loading screen. */
    float loadProgress();
    /** @param buildBudgetNanos what is left of the per-tick world-build budget shared by all runs */
    void tick(long now, long buildBudgetNanos);
    void disconnected(ServerPlayer player, long now);
    /** True when the player was seated back into the run; false sends them home. */
    boolean rejoin(ServerPlayer player, long now);
    void leave(ServerPlayer player);
    void stop(String reason);
    /** Release everything at server shutdown. */
    void drain();
    /** Down-and-revive rule for a death inside the run, or null to use the default. */
    GuardianDown.Options downed(ServerPlayer player);
}
