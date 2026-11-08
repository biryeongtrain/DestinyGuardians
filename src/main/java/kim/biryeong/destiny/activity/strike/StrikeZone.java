package kim.biryeong.destiny.activity.strike;

/**
 * One separately built region of a strike's run world. A strike declares its zones as an enum implementing this, so the
 * shared map loader, world builder and instance manager can address them without knowing which strike they belong to.
 * The zone's {@code name()} prefixes its anchor ids ({@code RY.IN}); {@link #resourceName()} names its map files.
 */
public interface StrikeZone {
    String name();
    int ordinal();
    /** File stem of the zone's map template and its key inside {@code markers.json}. */
    String resourceName();
}
