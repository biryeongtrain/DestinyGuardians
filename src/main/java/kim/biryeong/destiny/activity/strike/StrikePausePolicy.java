package kim.biryeong.destiny.activity.strike;

/** Cinematic input locks remove combat targets without removing the audience for story progression. */
public record StrikePausePolicy(boolean progress, boolean actors) {
    public static StrikePausePolicy forPresence(boolean suspended, boolean readyLivingAudience, boolean combatTargets) {
        return new StrikePausePolicy(suspended || !readyLivingAudience, suspended || !combatTargets);
    }
}
