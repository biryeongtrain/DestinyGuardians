package kim.biryeong.destiny.inventory;

import kim.biryeong.destiny.crucible.CrucibleAmmoRules;

/** Menu copy derives amounts from the live policy; it does not change grants or caps. */
public final class CrucibleAmmoHelpText {
    private CrucibleAmmoHelpText() { }
    public static String shortSpecial(String family) {
        return "시련의 장: 시작·부활 " + CrucibleAmmoRules.starting(family)
                + "발 · 공용 탄약 " + CrucibleAmmoRules.brick(family) + "발";
    }
    public static String description(String family, String ammo) {
        if ("SPECIAL".equals(ammo)) return shortSpecial(family)
                + "\n장착한 특수 화기마다 지급 · 2개 장착해도 분할 없음"
                + "\n사망 시 탄창·예비 특수탄이 남아 있으면 공용 녹색 탄약 1개 드롭"
                + "\n살아 있는 양 팀 참가자 누구나 획득 · 사망 시 남은 탄약은 소멸"
                + "\n특수탄 처치 게이지·주기 보급 상자는 사용하지 않습니다.";
        if ("HEAVY".equals(ammo)) return "시련의 장에서는 중화기 탄약 없이 시작합니다. 보급으로 탄약을 얻고, 사망하면 남은 중화기 탄약을 잃습니다.";
        return "주 무기는 예비 탄약 제한 없이 사용합니다. 탄창이 비면 재장전하세요. 시련의 장 특수탄은 시작·부활과 공용 녹색 탄약으로 얻습니다.";
    }
}
