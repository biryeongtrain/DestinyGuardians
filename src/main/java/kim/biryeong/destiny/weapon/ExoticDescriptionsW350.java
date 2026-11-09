package kim.biryeong.destiny.weapon;

import net.minecraft.network.chat.Component;
import net.minecraft.ChatFormatting;
import java.util.List;

/** Player-facing summaries of the implemented base intrinsics; no catalyst claims. */
public final class ExoticDescriptionsW350 {
    private ExoticDescriptionsW350() {}
    public static List<Component> lore(WeaponCatalog.Entry entry) {
        String text = switch (entry.id()) {
            case "crimson" -> "3점사 · 처치 시 회복 · 정밀 처치 시 탄창 충전";
            case "thorn" -> "지속 독 피해 · 처치 잔류물 획득 시 탄약 회수와 독 강화";
            case "outbreak_perfected" -> "연속 적중·정밀 처치 시 나노입자 생성 · 감염된 적에게 추가 피해";
            case "sunshot" -> "폭발 탄환 · 처치한 적이 폭발하며 주변 적에게 연소 부여";
            case "graviton_lance" -> "강력한 두 번째 탄환 · 처치 시 공허 폭발과 추적 구체 생성";
            case "jotunn" -> "충전 추적탄 · 폭발과 지속 화상 · 태양 보호막 파괴 시 실명";
            case "gjallarhorn" -> "추적 로켓과 늑대 무리 탄약 · 근처 아군의 전설 로켓 강화";
            case "whisper_of_the_worm" -> "빠른 정밀 적중 3회 시 탄약 회수 · 빗나간 탄약을 확률적으로 반환";
            case "tractor_cannon" -> "근거리 충격파 · 억압과 약화 · 적중 시 이동과 조작성 강화";
            default -> null;
        };
        return text == null ? List.of() : List.of(Component.literal(text).withStyle(ChatFormatting.YELLOW));
    }
}
