package kim.biryeong.destiny.campaign;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/** Server-thread mission state. World callbacks must carry their instance and encounter token. */
public final class GuardianRisesProgress {
    public enum Stage {
        GHOST_SCAN, GATEWAY, BREACH_DARK, ARM_YOURSELF, BREACH_FIGHT,
        SUPPLY_CACHE, DIVIDE_WALKER, DOCK_13, SHIP_DEFENSE, DEPARTURE, COMPLETE
    }
    public record Token(UUID instance, long generation) { }
    public record Snapshot(Stage checkpoint, boolean musicStarted, boolean completed) { }
    private final UUID instance;
    private Stage stage;
    private Stage checkpoint;
    private long generation;
    private boolean musicStarted;
    private boolean encounterSealed;
    private final Set<UUID> enemies = new HashSet<>();

    public GuardianRisesProgress(UUID instance) {
        this(instance, new Snapshot(Stage.GHOST_SCAN, false, false));
    }
    public GuardianRisesProgress(UUID instance, Snapshot saved) {
        this.instance = java.util.Objects.requireNonNull(instance);
        if (!isCheckpoint(saved.checkpoint())) throw new IllegalArgumentException("Invalid checkpoint");
        checkpoint = saved.checkpoint();
        stage = saved.completed() ? Stage.COMPLETE : checkpoint;
        musicStarted = saved.musicStarted();
    }
    public Stage stage() { return stage; }
    public Token token() { return new Token(instance, generation); }
    public int enemiesRemaining() { return enemies.size(); }
    public Snapshot snapshot() { return new Snapshot(checkpoint, musicStarted, stage == Stage.COMPLETE); }
    public boolean startMusicOnce() {
        if (musicStarted || stage == Stage.COMPLETE) return false;
        musicStarted = true;
        return true;
    }
    public boolean owns(Token token) { return token().equals(token); }
    public boolean registerEnemy(Token token, UUID enemy) {
        return owns(token) && combatStage() && !encounterSealed && enemies.add(java.util.Objects.requireNonNull(enemy));
    }
    /** Seal only after all mandatory spawns succeeded; a partial spawn failure must not clear combat. */
    public boolean sealEncounter(Token token) {
        if (!owns(token) || !combatStage() || encounterSealed) return false;
        encounterSealed = true;
        return true;
    }
    public boolean enemyDefeated(Token token, UUID enemy) { return owns(token) && enemies.remove(enemy); }
    /**
     * A mandatory enemy left the world without a kill and was respawned. Allowed after sealing because the
     * replacement keeps the mandatory count unchanged; it never adds a new slot.
     */
    public boolean replaceEnemy(Token token, UUID lost, UUID replacement) {
        java.util.Objects.requireNonNull(replacement);
        if (!owns(token) || !combatStage() || !enemies.contains(lost) || enemies.contains(replacement)) return false;
        enemies.remove(lost);
        enemies.add(replacement);
        return true;
    }
    public boolean tracks(Token token, UUID enemy) { return owns(token) && enemies.contains(enemy); }
    public boolean encounterCleared() { return combatStage() && encounterSealed && enemies.isEmpty(); }
    /** Called by validated world objectives, never by timers alone for combat or Tower arrival. */
    public boolean advance(Token token) {
        if (!owns(token) || stage == Stage.COMPLETE || (combatStage() && !encounterCleared())) return false;
        stage = Stage.values()[stage.ordinal() + 1];
        if (isCheckpoint(stage)) checkpoint = stage;
        invalidateEncounter();
        return true;
    }
    public boolean restartCheckpoint() {
        if (stage == Stage.COMPLETE) return false;
        stage = checkpoint;
        invalidateEncounter();
        return true;
    }
    /** Operator QA: jump to a stage; the checkpoint becomes the last one at or before it. */
    public boolean forceStage(Stage target) {
        java.util.Objects.requireNonNull(target);
        if (stage == Stage.COMPLETE || target == Stage.COMPLETE) return false;
        stage = target;
        for (int i = target.ordinal(); i >= 0; i--) {
            if (isCheckpoint(Stage.values()[i])) { checkpoint = Stage.values()[i]; break; }
        }
        invalidateEncounter();
        return true;
    }
    public Stage checkpoint() { return checkpoint; }
    public boolean sealed() { return encounterSealed; }
    public boolean combat() { return combatStage(); }
    private void invalidateEncounter() {
        generation++;
        enemies.clear();
        encounterSealed = false;
    }
    private boolean combatStage() {
        return stage == Stage.BREACH_FIGHT || stage == Stage.DIVIDE_WALKER || stage == Stage.SHIP_DEFENSE;
    }
    public static boolean isCheckpoint(Stage stage) {
        return stage == Stage.GHOST_SCAN || stage == Stage.ARM_YOURSELF
                || stage == Stage.DIVIDE_WALKER || stage == Stage.DOCK_13;
    }
}
