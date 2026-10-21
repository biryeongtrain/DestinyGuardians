package kim.biryeong.destiny.guardian;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import java.util.EnumMap;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * 플레이어에 저장되는 수호자 상태 (Fabric 데이터 첨부, 사망 후에도 유지).
 * 쿨타임은 남은 틱. 궁극기 에너지는 0~1.
 */
public final class GuardianData {
    public static final Codec<GuardianData> CODEC = RecordCodecBuilder.create(i -> i.group(
            GuardianClass.CODEC.optionalFieldOf("class", GuardianClass.NONE).forGetter(d -> d.guardianClass),
            Codec.unboundedMap(GuardianClass.CODEC, Loadout.CODEC).optionalFieldOf("loadouts", Map.of()).forGetter(d -> d.loadouts),
            Codec.unboundedMap(AbilitySlot.CODEC, Codec.INT).optionalFieldOf("cooldowns", Map.of()).forGetter(d -> d.cooldowns),
            Codec.FLOAT.optionalFieldOf("super_energy", 0f).forGetter(d -> d.superEnergy)
    ).apply(i, GuardianData::new));

    private GuardianClass guardianClass;
    private final Map<GuardianClass, Loadout> loadouts = new EnumMap<>(GuardianClass.class);
    private final Map<AbilitySlot, Integer> cooldowns = new EnumMap<>(AbilitySlot.class);
    private float superEnergy;

    public GuardianData() {
        this(GuardianClass.NONE, Map.of(), Map.of(), 0f);
    }

    private GuardianData(GuardianClass guardianClass, Map<GuardianClass, Loadout> loadouts, Map<AbilitySlot, Integer> cooldowns, float superEnergy) {
        this.guardianClass = guardianClass;
        this.loadouts.putAll(loadouts);
        this.cooldowns.putAll(cooldowns);
        this.superEnergy = superEnergy;
    }

    public GuardianClass guardianClass() {
        return guardianClass;
    }

    public void setGuardianClass(GuardianClass guardianClass) {
        this.guardianClass = guardianClass;
    }

    public Optional<Loadout> loadout() {
        return Optional.ofNullable(loadouts.get(guardianClass));
    }

    public Loadout loadout(GuardianClass cls) {
        return loadouts.get(cls);
    }

    public void setLoadout(GuardianClass cls, Loadout loadout) {
        loadouts.put(cls, loadout);
    }

    public int cooldown(AbilitySlot slot) {
        return cooldowns.getOrDefault(slot, 0);
    }

    public void setCooldown(AbilitySlot slot, int ticks) {
        if (ticks <= 0) {
            cooldowns.remove(slot);
        } else {
            cooldowns.put(slot, ticks);
        }
    }

    /** 모든 쿨타임을 1틱 줄인다. 바뀐 슬롯이 있으면 true. */
    public boolean tickCooldowns() {
        if (cooldowns.isEmpty()) {
            return false;
        }
        cooldowns.replaceAll((slot, ticks) -> ticks - 1);
        cooldowns.values().removeIf(t -> t <= 0);
        return true;
    }

    public float superEnergy() {
        return superEnergy;
    }

    public void setSuperEnergy(float value) {
        this.superEnergy = Math.max(0f, Math.min(1f, value));
    }

    public Map<AbilitySlot, Integer> cooldownsView() {
        return Map.copyOf(cooldowns);
    }

    public GuardianData copy() {
        return new GuardianData(guardianClass, new HashMap<>(loadouts), new HashMap<>(cooldowns), superEnergy);
    }
}
