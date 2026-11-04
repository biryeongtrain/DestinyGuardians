package kim.biryeong.destiny.loot;

/** Optional enemy hint for kill drops; untagged enemies are classified by maximum health. */
public interface LootTagged {
    enum Tier { MINOR, MAJOR, BOSS, NONE }
    Tier lootTier();
}
