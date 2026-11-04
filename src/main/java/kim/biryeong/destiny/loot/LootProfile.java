package kim.biryeong.destiny.loot;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import java.util.ArrayList;
import java.util.List;

/** Persistent per-Guardian loot state: the one-time starter grant and held (undecoded) engrams. */
public record LootProfile(boolean starter, List<String> engrams) {
    /** Destiny's engram inventory holds ten. */
    public static final int ENGRAM_CAP = 10;
    public static final Codec<LootProfile> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.BOOL.optionalFieldOf("starter", false).forGetter(LootProfile::starter),
            Codec.STRING.listOf().optionalFieldOf("engrams", List.of()).forGetter(LootProfile::engrams)
    ).apply(i, LootProfile::new));
    public static final LootProfile EMPTY = new LootProfile(false, List.of());

    public LootProfile { engrams = List.copyOf(engrams); }

    public LootProfile withStarter() { return new LootProfile(true, engrams); }
    public LootProfile plus(String tier) {
        var next = new ArrayList<>(engrams); next.add(tier); return new LootProfile(starter, next);
    }
    public LootProfile minus(int index) {
        var next = new ArrayList<>(engrams); next.remove(index); return new LootProfile(starter, next);
    }
}
