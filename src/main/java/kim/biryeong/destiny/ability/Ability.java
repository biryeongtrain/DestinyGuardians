package kim.biryeong.destiny.ability;

import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;

/**
 * 능력 하나. 수치는 {@link #tuning()} 에서 읽어 JSON 으로 조정할 수 있게 한다.
 */
public abstract class Ability {
    private final Identifier id;
    private final GuardianClass guardianClass;
    private final AbilitySlot slot;
    private final Element element;
    private final double defaultCooldownSeconds;
    private final String displayName;

    protected Ability(Identifier id, GuardianClass guardianClass, AbilitySlot slot, Element element,
                      double defaultCooldownSeconds, String displayName) {
        this.id = id;
        this.guardianClass = guardianClass;
        this.slot = slot;
        this.element = element;
        this.defaultCooldownSeconds = defaultCooldownSeconds;
        this.displayName = displayName;
    }

    /** 능력을 실행한다. 실제로 실행됐으면 true (쿨타임 시작). */
    public abstract boolean activate(ServerPlayer player);

    public final AbilityTuning tuning() {
        return AbilityRegistry.tuning(id);
    }

    public final double param(String key, double fallback) {
        return tuning().param(key, fallback);
    }

    public final int cooldownTicks() {
        return (int) Math.round(tuning().cooldownSeconds().orElse(defaultCooldownSeconds) * 20.0);
    }

    public Identifier id() {
        return id;
    }

    public GuardianClass guardianClass() {
        return guardianClass;
    }

    public AbilitySlot slot() {
        return slot;
    }

    public Element element() {
        return element;
    }

    public String displayName() {
        return displayName;
    }
}
