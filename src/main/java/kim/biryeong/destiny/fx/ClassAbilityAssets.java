package kim.biryeong.destiny.fx;

/** Presence means an actual packaged model; a missing source never silently maps to a Hunter prop. */
public final class ClassAbilityAssets {
    private ClassAbilityAssets() { }
    public static boolean has(String path) {
        return ClassAbilityAssets.class.getResource("/assets/destiny/items/class_ability/" + path + ".json") != null;
    }
}
