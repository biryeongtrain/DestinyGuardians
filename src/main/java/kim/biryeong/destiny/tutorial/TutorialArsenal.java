package kim.biryeong.destiny.tutorial;

import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponCharacteristics;
import java.util.List;

/** One real representative for every implemented weapon family, ordered by ammunition economy. */
public final class TutorialArsenal {
    public record Lesson(String id, String family, String title, String description, double distance) {
        public WeaponCatalog.Entry weapon() { return WeaponCatalog.find(id).orElseThrow(); }
        public String ammunition() { return WeaponCharacteristics.of(weapon()).ammo().name(); }
        public String ammoLabel() {
            return switch (ammunition()) { case "PRIMARY" -> "일반탄 · 예비 무한";
                case "SPECIAL" -> "특수탄 · 초록색 탄약"; default -> "중화기 · 보라색 탄약"; };
        }
    }
    public static final List<Lesson> LESSONS = List.of(
        new Lesson("austringer", "hand_cannon", "핸드 캐논", "한 발의 위력이 높은 권총입니다. 반동이 가라앉으면 다음 발을 정확히 쏘세요.", 12),
        new Lesson("ammit_ar2", "auto_rifle", "자동 소총", "발사 버튼을 누르고 있으면 연속 사격합니다. 움직이는 표적을 따라 조준하세요.", 12),
        new Lesson("bygones", "pulse_rifle", "파동 소총", "한 번 격발하면 여러 발이 점사됩니다. 점사 사이에 조준을 다시 맞추세요.", 16),
        new Lesson("patron_of_lost_causes", "scout_rifle", "정찰 소총", "먼 적을 정밀하게 상대합니다. 거리를 두고 머리를 노려 보세요.", 22),
        new Lesson("antiope_d", "submachine_gun", "기관단총", "근거리에서 빠르게 탄을 쏟아붓습니다. 먼 적보다 가까운 적에게 효과적입니다.", 8),
        new Lesson("lonesome", "sidearm", "보조 무기", "가까운 적에게 빠르게 대응하는 권총입니다. 짧은 교전에서 다루기 좋습니다.", 8),
        new Lesson("biting_winds", "bow", "활", "발사 버튼을 눌러 시위를 당긴 뒤 놓으세요. 충분히 당겨야 강하고 정확합니다.", 16),
        new Lesson("dust_rock_blues", "shotgun", "산탄총", "여러 산탄을 한꺼번에 발사합니다. 가까이서 맞혀야 많은 산탄이 적중합니다.", 5),
        new Lesson("beloved", "sniper_rifle", "저격총", "높은 배율과 정밀 피해를 활용하세요. 탄이 귀하니 정조준 후 머리를 노리세요.", 24),
        new Lesson("hollow_words", "fusion_rifle", "융합 소총", "발사 버튼을 누르고 충전이 끝날 때까지 기다리면 에너지 탄을 연속 방출합니다.", 10),
        new Lesson("retraced_path", "trace_rifle", "추적 소총", "발사 버튼을 유지해 광선을 쏘세요. 광선을 적에게 계속 맞추는 무기입니다.", 12),
        new Lesson("salvager_s_salvo", "grenade_launcher", "유탄 발사기", "곡사로 발사합니다. 누른 채 발사하고 놓으면 원격 폭발합니다. 적 근처를 노리세요.", 12),
        new Lesson("nezarec_s_whisper", "glaive", "글레이브", "특수탄 투사체와 근접 공격을 함께 씁니다. 이번에는 투사체를 발사하세요. 웅크리면 방패를 듭니다.", 10),
        new Lesson("hammerhead", "machine_gun", "기관총", "중화기 탄약으로 지속 사격합니다. 여러 적을 처리할 때 유용하지만 예비 탄약은 유한합니다.", 14),
        new Lesson("edge_transit", "heavy_grenade_launcher", "중화기 유탄 발사기", "탄창에 여러 유탄을 장전합니다. 적 무리나 강한 적에게 폭발 피해를 집중하세요.", 14),
        new Lesson("bad_omens", "rocket_launcher", "로켓 발사기", "강한 폭발을 한 발에 담습니다. 주변에 여유를 두고 표적 중심을 겨누세요.", 18),
        new Lesson("line_in_the_sand", "linear_fusion_rifle", "선형 융합 소총", "정조준한 채 충전해 정밀 사격합니다. 강한 적의 약점을 노리세요.", 22),
        new Lesson("abide_the_return", "sword", "검", "마지막은 근접 중화기입니다. 가까이 다가가 좌클릭으로 베세요. 검도 탄약을 소비하고 재장전은 없습니다.", 2.3)
    );
    private TutorialArsenal() { }
    public static String ammoExplanation(String kind) {
        return switch (kind) {
            case "PRIMARY" -> "일반탄은 예비 탄약이 무한하지만 탄창은 재장전해야 합니다. 1·2번 장비 칸과 일반·특수 탄약 분류는 서로 다릅니다.";
            case "SPECIAL" -> "특수탄은 위력이 높고 예비 탄약이 제한됩니다. 초록색 탄약으로 보충하세요. 1·2번 칸 모두 일반탄 또는 특수탄 무기를 넣을 수 있습니다.";
            default -> "중화기는 3번 칸을 사용합니다. 보라색 탄약은 귀하므로 강한 적이나 적 무리를 상대할 때 쓰세요. 이곳에서만 연습 탄약을 보충합니다.";
        };
    }
}
