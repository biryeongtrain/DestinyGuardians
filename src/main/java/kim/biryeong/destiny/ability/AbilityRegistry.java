package kim.biryeong.destiny.ability;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.GuardianClass;
import net.fabricmc.fabric.api.resource.v1.ResourceLoader;
import net.minecraft.resources.FileToIdConverter;
import net.minecraft.resources.Identifier;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.server.packs.resources.SimpleJsonResourceReloadListener;
import net.minecraft.util.profiling.ProfilerFiller;

import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** 능력 구현 등록부 + JSON 수치 로더. */
public final class AbilityRegistry {
    private static final Map<Identifier, Ability> ABILITIES = new LinkedHashMap<>();
    private static volatile Map<Identifier, AbilityTuning> tunings = Map.of();

    private AbilityRegistry() {
    }

    public static <T extends Ability> T register(T ability) {
        if (ABILITIES.putIfAbsent(ability.id(), ability) != null) {
            throw new IllegalStateException("Duplicate ability " + ability.id());
        }
        return ability;
    }

    public static Optional<Ability> get(Identifier id) {
        return Optional.ofNullable(ABILITIES.get(id));
    }

    public static Collection<Ability> all() {
        return ABILITIES.values();
    }

    public static List<Ability> of(GuardianClass cls, AbilitySlot slot) {
        return ABILITIES.values().stream().filter(a -> a.guardianClass() == cls && a.slot() == slot).toList();
    }

    public static AbilityTuning tuning(Identifier id) {
        return tunings.getOrDefault(id, AbilityTuning.EMPTY);
    }

    /** 테스트용: 수치를 직접 넣는다. */
    public static void setTuningsForTest(Map<Identifier, AbilityTuning> values) {
        tunings = Map.copyOf(values);
    }

    public static void registerReloadListener() {
        ResourceLoader.get(PackType.SERVER_DATA).registerReloadListener(DestinyGuardians.id("abilities"), new Loader());
    }

    private static final class Loader extends SimpleJsonResourceReloadListener<AbilityTuning> {
        Loader() {
            super(AbilityTuning.CODEC, FileToIdConverter.json("destiny_ability"));
        }

        @Override
        protected void apply(Map<Identifier, AbilityTuning> loaded, ResourceManager manager, ProfilerFiller profiler) {
            tunings = Map.copyOf(loaded);
            DestinyGuardians.LOGGER.info("Loaded {} ability tunings", loaded.size());
        }
    }
}
