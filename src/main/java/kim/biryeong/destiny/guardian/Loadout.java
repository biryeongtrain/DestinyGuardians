package kim.biryeong.destiny.guardian;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.resources.Identifier;

import java.util.EnumMap;
import java.util.Map;

/**
 * 한 직업의 장착 능력. 슬롯마다 능력 ID 하나. Prism 방식이라 속성을 섞을 수 있다.
 */
public record Loadout(Map<AbilitySlot, Identifier> abilities) {
    public static final Codec<Loadout> CODEC = RecordCodecBuilder.create(i -> i.group(
            Codec.unboundedMap(AbilitySlot.CODEC, Identifier.CODEC).fieldOf("abilities").forGetter(Loadout::abilities)
    ).apply(i, Loadout::new));

    public Loadout {
        abilities = Map.copyOf(abilities);
    }

    public Identifier get(AbilitySlot slot) {
        return abilities.get(slot);
    }

    public Loadout with(AbilitySlot slot, Identifier ability) {
        Map<AbilitySlot, Identifier> copy = new EnumMap<>(AbilitySlot.class);
        copy.putAll(abilities);
        copy.put(slot, ability);
        return new Loadout(copy);
    }
}
