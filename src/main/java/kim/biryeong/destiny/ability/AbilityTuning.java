package kim.biryeong.destiny.ability;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import java.util.Map;
import java.util.Optional;

/**
 * 능력 수치 (data/&lt;ns&gt;/destiny_ability/**.json). 코드 기본값을 덮어쓴다.
 * <pre>{ "cooldown_seconds": 40, "params": { "damage": 8, "radius": 4 } }</pre>
 */
public record AbilityTuning(Optional<Double> cooldownSeconds, Map<String, Double> params) {
    public static final AbilityTuning EMPTY = new AbilityTuning(Optional.empty(), Map.of());
    public static final Codec<AbilityTuning> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.DOUBLE.optionalFieldOf("cooldown_seconds").forGetter(AbilityTuning::cooldownSeconds),
            Codec.unboundedMap(Codec.STRING, Codec.DOUBLE).optionalFieldOf("params", Map.of()).forGetter(AbilityTuning::params)
    ).apply(i, AbilityTuning::new));

    public double param(String key, double fallback) {
        return params.getOrDefault(key, fallback);
    }
}
