package kim.biryeong.destiny.guardian;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.hud.CombatHud;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;

import java.util.Comparator;
import java.util.EnumMap;
import java.util.List;

/** Shared selection rules for commands and the character menu; no additional persistent state. */
public final class CharacterLoadouts {
    private static final List<Element> SUBCLASSES = List.of(Element.ARC, Element.SOLAR, Element.VOID);

    private CharacterLoadouts() { }

    /** Returns null for a non-guardian or an absent/invalid equipped super. Does not repair data. */
    public static Element subclass(GuardianData data) {
        return data == null ? null : subclass(data.guardianClass(), data.loadout().orElse(null));
    }

    public static List<Element> subclasses(GuardianClass cls) {
        if (!playable(cls)) return List.of();
        return SUBCLASSES.stream().filter(element -> !options(cls, element, AbilitySlot.SUPER).isEmpty()).toList();
    }

    /** Immutable, ID-ordered registered options. Kinetic is shared only in this class's jump/class-ability slots. */
    public static List<Ability> options(GuardianClass cls, Element element, AbilitySlot slot) {
        if (!playable(cls) || !GuardianPresets.supported(element) || slot == null) return List.of();
        return AbilityRegistry.all().stream().filter(ability -> compatible(ability, cls, element, slot))
                .sorted(Comparator.comparing(ability -> ability.id().toString())).toList();
    }

    /** All selection methods return null on success, or a Korean error without changing state. */
    public static String selectClass(ServerPlayer player, GuardianClass cls) {
        String error = eligibility(player);
        if (error != null) return error;
        if (cls == null) return "알 수 없는 직업입니다.";
        GuardianData data = player.getAttachedOrElse(Guardians.DATA, null);
        GuardianClass current = data == null ? GuardianClass.NONE : data.guardianClass();
        if (current == cls) return null;

        Loadout restored = null;
        if (cls != GuardianClass.NONE) {
            Loadout saved = data == null ? null : data.loadout(cls);
            Element element = subclass(cls, saved);
            restored = normalized(cls, element == null ? Element.ARC : element, saved);
            if (restored == null) return "이 직업의 기본 능력이 등록되지 않았습니다.";
        }

        // Validation and the complete replacement are ready before retiring any live ability work.
        prepareChange(player);
        if (data == null) data = Guardians.data(player);
        if (restored != null) data.setLoadout(cls, restored);
        data.setGuardianClass(cls);
        data.setSuperEnergy(0f);
        CombatHud.update(player);
        return null;
    }

    public static String selectSubclass(ServerPlayer player, Element element) {
        String error = eligibility(player);
        if (error != null) return error;
        if (!GuardianPresets.supported(element)) return "지원하는 하위직업은 아크, 솔라, 공허입니다.";
        GuardianData data = player.getAttachedOrElse(Guardians.DATA, null);
        if (data == null || !playable(data.guardianClass())) return "먼저 수호자 직업을 선택하세요.";
        if (subclass(data) == element) return null;
        Loadout replacement = normalized(data.guardianClass(), element, data.loadout().orElse(null));
        if (replacement == null) return "이 하위직업의 기본 능력이 등록되지 않았습니다.";

        prepareChange(player);
        data.setLoadout(data.guardianClass(), replacement);
        data.setSuperEnergy(0f);
        CombatHud.update(player);
        return null;
    }

    public static String selectAbility(ServerPlayer player, AbilitySlot slot, Identifier id) {
        String error = eligibility(player);
        if (error != null) return error;
        if (slot == null) return "알 수 없는 능력 슬롯입니다.";
        Ability ability = id == null ? null : AbilityRegistry.get(id).orElse(null);
        if (ability == null) return "등록되지 않은 능력입니다.";
        GuardianData data = player.getAttachedOrElse(Guardians.DATA, null);
        if (data == null || !playable(data.guardianClass())) return "먼저 수호자 직업을 선택하세요.";
        if (ability.guardianClass() != data.guardianClass()) return "현재 직업의 능력만 선택할 수 있습니다.";
        if (ability.slot() != slot) return "선택한 슬롯에 장착할 수 없는 능력입니다.";
        Element element = subclass(data);
        if (element == null) return "먼저 유효한 하위직업을 선택하세요.";
        if (!compatible(ability, data.guardianClass(), element, slot)) {
            return "현재 하위직업과 같은 속성의 능력만 선택할 수 있습니다.";
        }
        Loadout current = data.loadout().orElse(null);
        if (current == null) return "먼저 하위직업을 선택하세요.";
        if (id.equals(current.get(slot))) return null;
        Loadout replacement = current.with(slot, id);

        prepareChange(player);
        data.setLoadout(data.guardianClass(), replacement);
        if (slot == AbilitySlot.SUPER) data.setSuperEnergy(0f);
        CombatHud.update(player);
        return null;
    }

    private static boolean playable(GuardianClass cls) {
        return cls != null && cls != GuardianClass.NONE;
    }

    private static Element subclass(GuardianClass cls, Loadout loadout) {
        if (!playable(cls) || loadout == null) return null;
        Identifier id = loadout.get(AbilitySlot.SUPER);
        Ability ability = id == null ? null : AbilityRegistry.get(id).orElse(null);
        return ability != null && ability.guardianClass() == cls && ability.slot() == AbilitySlot.SUPER
                && GuardianPresets.supported(ability.element()) ? ability.element() : null;
    }

    private static boolean compatible(Ability ability, GuardianClass cls, Element element, AbilitySlot slot) {
        return ability != null && ability.guardianClass() == cls && ability.slot() == slot
                && (ability.element() == element || ability.element() == Element.KINETIC
                && (slot == AbilitySlot.CLASS_ABILITY || slot == AbilitySlot.JUMP));
    }

    /** Keep compatible saved choices, replacing only missing, unknown, or incompatible entries. */
    private static Loadout normalized(GuardianClass cls, Element element, Loadout saved) {
        Loadout preset = GuardianPresets.preset(cls, element);
        var abilities = new EnumMap<AbilitySlot, Identifier>(AbilitySlot.class);
        for (AbilitySlot slot : AbilitySlot.values()) {
            Identifier id = saved == null ? null : saved.get(slot);
            Ability ability = id == null ? null : AbilityRegistry.get(id).orElse(null);
            if (!compatible(ability, cls, element, slot)) {
                id = preset.get(slot);
                ability = id == null ? null : AbilityRegistry.get(id).orElse(null);
                if (!compatible(ability, cls, element, slot)) return null;
            }
            abilities.put(slot, id);
        }
        return new Loadout(abilities);
    }

    private static String eligibility(ServerPlayer player) {
        if (player == null) return "플레이어를 찾을 수 없습니다.";
        if (!player.level().getServer().isSameThread()) return "서버 메인 스레드에서만 변경할 수 있습니다.";
        if (!player.isAlive() || player.isRemoved() || player.hasDisconnected()) return "살아 있는 접속 플레이어만 변경할 수 있습니다.";
        if (player.isSpectator()) return "관전자 상태에서는 변경할 수 없습니다.";
        // Even an identical selection during a super fails without ending or replacing its session.
        if (AbilityService.inSuper(player)) return "궁극기 사용 중에는 장비 구성을 변경할 수 없습니다.";
        return null;
    }

    private static void prepareChange(ServerPlayer player) {
        AbilityService.cleanup(player);
        // End dodge protection, but preserve jump usage, input capabilities and action/cooldown history.
        Guardians.runtimeIfPresent(player).ifPresent(runtime -> runtime.invulnerableTicks = 0);
        // WeaponScreen owns its session and freeze modifiers; neither is retired by this service.
    }
}
