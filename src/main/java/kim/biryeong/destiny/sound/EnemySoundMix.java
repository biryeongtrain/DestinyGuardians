package kim.biryeong.destiny.sound;

/** Shared local PvE enemy mix. Source recordings retain their original duration and samples. */
public final class EnemySoundMix {
    public static final float COMBAT = .55f, DEATH = .35f, HURT = .25f, FOLEY = .3f;
    private EnemySoundMix() { }
    public static float volume(String event) {
        return switch (event) {
            case "death" -> DEATH;
            case "hurt" -> HURT;
            case "impact" -> .45f;
            default -> COMBAT;
        };
    }
}
