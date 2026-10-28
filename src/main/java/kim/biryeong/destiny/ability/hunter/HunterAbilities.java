package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Loadout;
import net.minecraft.resources.Identifier;

import java.util.EnumMap;
import java.util.Map;

/** 헌터 능력 등록과 속성별 기본 장착 (docs/design/Destiny_Guardians 3-1-3). */
public final class HunterAbilities {
    public static final Identifier DOUBLE_JUMP = id("double_jump");
    public static final Identifier TRIPLE_JUMP = id("triple_jump");
    public static final Identifier GAMBLERS_DODGE = id("gamblers_dodge");
    public static final Identifier MARKSMANS_DODGE = id("marksmans_dodge");
    public static final Identifier ARC_FLASHBANG = id("arc_flashbang");
    public static final Identifier SOLAR_INCENDIARY = id("solar_incendiary");
    public static final Identifier VOID_VORTEX = id("void_vortex");
    public static final Identifier ARC_COMBINATION_BLOW = id("arc_combination_blow");
    public static final Identifier SOLAR_KNIFE = id("solar_knife");
    public static final Identifier VOID_SMOKE_BOMB = id("void_smoke_bomb");
    public static final Identifier ARC_STAFF = id("arc_staff");
    public static final Identifier GOLDEN_GUN = id("golden_gun");
    public static final Identifier SHADOWSHOT = id("shadowshot");

    private HunterAbilities() {
    }

    private static Identifier id(String path) {
        return DestinyGuardians.id("hunter/" + path);
    }

    public static void register() {
        AbilityRegistry.register(new HunterJump(DOUBLE_JUMP, "2단 점프", 1, 0.55));
        AbilityRegistry.register(new HunterJump(TRIPLE_JUMP, "3단 점프", 2, 0.45));
        AbilityRegistry.register(new HunterDodge(GAMBLERS_DODGE, "도박꾼의 회피", HunterDodge.Variant.GAMBLER, 11));
        AbilityRegistry.register(new HunterDodge(MARKSMANS_DODGE, "명사수의 회피", HunterDodge.Variant.MARKSMAN, 8));
        AbilityRegistry.register(new HunterGrenade(ARC_FLASHBANG, "섬광 수류탄", Element.ARC, 40));
        AbilityRegistry.register(new HunterGrenade(SOLAR_INCENDIARY, "소이 수류탄", Element.SOLAR, 40));
        AbilityRegistry.register(new HunterGrenade(VOID_VORTEX, "소용돌이 수류탄", Element.VOID, 45));
        AbilityRegistry.register(new HunterMelee(ARC_COMBINATION_BLOW, "연속 타격", Element.ARC, 22));
        AbilityRegistry.register(new HunterMelee(SOLAR_KNIFE, "칼 투척", Element.SOLAR, 18));
        AbilityRegistry.register(new HunterMelee(VOID_SMOKE_BOMB, "연막탄", Element.VOID, 25));
        AbilityRegistry.register(new HunterSuper(ARC_STAFF, "아크 지팡이", Element.ARC));
        AbilityRegistry.register(new HunterSuper(GOLDEN_GUN, "황금 총", Element.SOLAR));
        AbilityRegistry.register(new HunterSuper(SHADOWSHOT, "그림자 사격", Element.VOID));
        HunterExpandedSupers.register();
    }

    /** 속성별 기본 장착. */
    public static Loadout preset(Element element) {
        Map<AbilitySlot, Identifier> map = new EnumMap<>(AbilitySlot.class);
        map.put(AbilitySlot.JUMP, DOUBLE_JUMP);
        switch (element) {
            case SOLAR -> {
                map.put(AbilitySlot.SUPER, GOLDEN_GUN);
                map.put(AbilitySlot.GRENADE, SOLAR_INCENDIARY);
                map.put(AbilitySlot.MELEE, SOLAR_KNIFE);
                map.put(AbilitySlot.CLASS_ABILITY, MARKSMANS_DODGE);
            }
            case VOID -> {
                map.put(AbilitySlot.SUPER, SHADOWSHOT);
                map.put(AbilitySlot.GRENADE, VOID_VORTEX);
                map.put(AbilitySlot.MELEE, VOID_SMOKE_BOMB);
                map.put(AbilitySlot.CLASS_ABILITY, GAMBLERS_DODGE);
            }
            default -> {
                map.put(AbilitySlot.SUPER, ARC_STAFF);
                map.put(AbilitySlot.GRENADE, ARC_FLASHBANG);
                map.put(AbilitySlot.MELEE, ARC_COMBINATION_BLOW);
                map.put(AbilitySlot.CLASS_ABILITY, GAMBLERS_DODGE);
            }
        }
        return new Loadout(map);
    }
}
