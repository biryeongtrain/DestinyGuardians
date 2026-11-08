package kim.biryeong.destiny.strike.devils;

/**
 * What an actor runtime needs from whatever decides when actors spawn and when an encounter is over. The Devils Lair
 * director and the Exodus Crash encounter director both implement it; the actors never know which strike they are in.
 */
public interface ActorDirector {
    void defeated(DevilsDirector.ActorRef ref);
    /** The actor vanished (void, discard) without being defeated; the director decides whether to replace it. */
    void lost(DevilsDirector.ActorRef ref, double health, double shield);
    /** Incoming damage the director allows; return 0 to make the actor immune right now. */
    double allowedDamage(DevilsDirector.ActorRef ref, double currentHealth, double requested);
    void healthChanged(DevilsDirector.ActorRef ref, double health, double shield);
    /** Sepiks-style phase gates; strikes without them leave both false. */
    default boolean damagePhase() { return false; }
    default boolean shieldPhase() { return false; }
}
