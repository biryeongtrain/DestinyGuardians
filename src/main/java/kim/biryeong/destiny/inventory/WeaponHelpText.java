package kim.biryeong.destiny.inventory;

import java.util.Map;

/** Korean beginner help keyed by catalog family ID, independent of Minecraft and UI state. */
public final class WeaponHelpText {
    private static final String UNKNOWN =
            "무기군 설명이 없습니다. 무기 이름과 프레임을 확인하세요.";

    // The UI has 17 family labels; the two grenade-launcher IDs have distinct controls.
    private static final Map<String, String> FAMILIES = Map.ofEntries(
            Map.entry("hand_cannon",
                    "중거리에서 머리를 노리는 단발 무기입니다. 좌클릭으로 조준을 켜고 우클릭으로 쏘세요. 사격 사이에는 가까운 엄폐물에 몸을 숨기세요."),
            Map.entry("auto_rifle",
                    "중거리에서 우클릭을 누른 채 연속 사격하는 소총입니다. 좌클릭으로 조준을 켜고, 연사 중 반동으로 조준이 흐트러지면 버튼을 놓아 사격을 끊으세요."),
            Map.entry("pulse_rifle",
                    "중거리에서 탄을 묶어 쏘는 점발 소총입니다. 좌클릭으로 조준을 켜고 우클릭으로 발사하되, 묶음 사격 도중에도 머리를 겨눠 이어지는 탄을 맞히세요."),
            Map.entry("scout_rifle",
                    "중장거리의 적을 머리 조준으로 상대하는 소총입니다. 좌클릭으로 조준을 켜고 우클릭으로 쏘며, 근거리 교전보다 시야가 트인 긴 통로에서 사용하세요."),
            Map.entry("submachine_gun",
                    "근거리에서 우클릭을 유지해 연사하는 무기이며, 적과 멀어지면 피해가 줄어듭니다. 엄폐물로 접근해 사격하고, 조준 화면은 좌클릭으로 켜세요."),
            Map.entry("sidearm",
                    "근거리에서 쓰는 권총형 무기이며, 점발 프레임은 탄을 묶어 쏩니다. 좌클릭으로 조준을 켜고 우클릭으로 발사하며, 가까이 다가온 적을 겨누세요."),
            Map.entry("bow",
                    "중장거리에서 우클릭으로 활을 당긴 뒤 버튼을 놓아 화살을 쏘세요. 당기기를 마치기 전에 놓으면 위력과 속도가 낮아지므로, 먼 적을 노릴 때는 끝까지 당기세요."),
            Map.entry("sniper_rifle",
                    "먼 거리에서 머리를 겨눠 쏘는 정밀 사격 무기입니다. 좌클릭으로 조준경을 켜고 우클릭으로 발사하며, 주변을 살필 때는 좌클릭으로 조준경을 끄세요."),
            Map.entry("shotgun",
                    "근거리에서 우클릭으로 산탄을 쏘며, 좌클릭으로 조준하면 탄이 퍼지는 폭을 줄입니다. 정밀 납탄 프레임은 단일 탄을 쏘므로 적의 머리를 겨누세요."),
            Map.entry("fusion_rifle",
                    "근중거리에서 우클릭을 유지하면 충전을 마친 뒤 탄을 묶어 쏩니다. 발사 전에 버튼을 놓으면 충전을 취소하므로, 적의 몸을 겨누고 발사할 때까지 누르세요."),
            Map.entry("linear_fusion_rifle",
                    "먼 거리에서 좌클릭으로 조준을 켜고 머리를 겨누는 충전 무기입니다. 우클릭을 유지해 충전 후 발사하며, 점발 프레임은 묶음 사격이 끝날 때까지 조준하세요."),
            Map.entry("trace_rifle",
                    "중거리에서 광선을 적에게 대고 연속으로 피해를 주는 무기입니다. 좌클릭으로 조준을 켜고 우클릭을 유지하며, 움직이는 표적은 마우스로 따라 겨누세요."),
            Map.entry("grenade_launcher",
                    "중거리에서 경량 유탄은 우클릭으로 쏜 뒤 반 초 이상 유지하다 놓아 원격 폭발시키세요. 파동 프레임은 적 앞의 땅을 맞혀 지면을 따라 공격하세요."),
            Map.entry("heavy_grenade_launcher",
                    "중거리에서 모인 적에게 우클릭으로 유탄을 쏘되, 아래로 떨어지는 궤적을 고려하세요. 압축 파동 프레임은 적 앞의 땅을 맞혀 지면을 따라 공격하세요."),
            Map.entry("rocket_launcher",
                    "중장거리에서 모여 있는 적을 폭발로 공격하는 무기입니다. 좌클릭으로 조준을 켜고 우클릭으로 쏘되, 로켓의 비행 시간과 앞을 막는 벽을 고려하세요."),
            Map.entry("machine_gun",
                    "중거리에서 우클릭을 유지해 연속 사격하는 중화기입니다. 좌클릭으로 조준을 켜고 사격하되, 기본 재장전 시간이 길어 탄창이 비기 전에 숨을 곳을 잡으세요."),
            Map.entry("sword",
                    "근거리에서 웅크리기를 풀고 좌클릭 약공격, 우클릭 강공격을 하세요. 강공격은 누를 때마다 시도합니다. 탄약과 에너지가 있으면 웅크려 방어 가능한 정면 몹 공격의 피해를 줄이세요."),
            Map.entry("glaive",
                    "근거리에서는 웅크리기를 풀고 좌클릭으로 탄약 없이 찌르고, 중거리에서는 우클릭으로 쏘세요. 사격 적중으로 방패 에너지를 채워 웅크리면 방어 가능한 정면 몹 공격의 피해를 줄입니다.")
    );

    private WeaponHelpText() {}

    /** Returns help for an exact family ID; null, blank and unknown IDs use generic help. */
    public static String family(String id) {
        return id == null ? UNKNOWN : FAMILIES.getOrDefault(id, UNKNOWN);
    }
}
