package kim.biryeong.destiny.strike.devils;

/** Cinematic input locks remove combat targets without removing the audience for story progression. */
public record DevilsPausePolicy(boolean progress, boolean actors) {
    public static DevilsPausePolicy forPresence(boolean suspended, boolean readyLivingAudience, boolean combatTargets) {
        return new DevilsPausePolicy(suspended || !readyLivingAudience, suspended || !combatTargets);
    }
}
