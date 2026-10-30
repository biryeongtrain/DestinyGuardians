package kim.biryeong.destiny.inventory;

import kim.biryeong.destiny.crucible.CrucibleAmmoRules;

/** Menu copy derives amounts from the live policy; it does not change grants or caps. */
public final class CrucibleAmmoHelpText {
    private CrucibleAmmoHelpText() { }
    public static String shortSpecial(String family) {
        return "시련의 장: 시작 " + CrucibleAmmoRules.starting(family)
                + " · 상자 " + CrucibleAmmoRules.specialPayout(family, true)
                + " · 게이지 " + CrucibleAmmoRules.specialPayout(family, false) + "발";
    }
    public static String description(String family, String ammo) {
        if ("SPECIAL".equals(ammo)) return shortSpecial(family)
                + "\n특수 화기 1개 기준 · 부활 재지급 없음"
                + "\n사망 시 남은 탄약 중 최대 " + CrucibleAmmoRules.retained(Long.MAX_VALUE, CrucibleAmmoRules.starting(family)) + "발 보존"
                + "\n특수 화기 2개: 지급량 분할, 각각 최소 1발";
        if ("HEAVY".equals(ammo)) return "시련의 장에서는 중화기 탄약 없이 시작합니다. 보급으로 탄약을 얻고, 사망하면 남은 중화기 탄약을 잃습니다.";
        return "주 무기는 예비 탄약 제한 없이 사용합니다. 탄창이 비면 재장전하세요. 시련의 장에서 적을 처치하거나 처치를 도우면 탄약 게이지를 채웁니다.";
    }
}
