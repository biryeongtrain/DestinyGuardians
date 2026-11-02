package kim.biryeong.destiny.campaign.presentation;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ObjectiveTypographyTest {
    @Test void wrapsLongKoreanObjectivesWithinTheCard() {
        for (String text : new String[]{"고스트가 시동을 거는 동안 버티세요", "보행 탱크와 몰락자를 처치하세요",
                "띄어쓰기없는아주긴한글목표문장을화면밖으로넘치지않게나눕니다", "장비 설정 · 직업도 언제든 변경 가능"}) {
            var lines = ObjectiveTypography.wrap(text, 220, 20);
            assertEquals(text.replace(" ", ""), String.join("", lines).replace(" ", ""));
            for (var row : lines) assertTrue(ObjectiveTypography.width(row, 20, false) <= 220, row);
        }
    }

    @Test void fontMetricsCoverHangulAndScaleWithTheHud() {
        for (int cp = 0xAC00; cp <= 0xD7A3; cp++) {
            var s = Character.toString(cp);
            float width = ObjectiveTypography.width(s, 20, false);
            assertTrue(width > 10 && width <= 32, s);
            assertEquals(width / 2, ObjectiveTypography.width(s, 10, false));
        }
        assertTrue(ObjectiveTypography.width("WWW", 20, false) > ObjectiveTypography.width("iii", 20, false));
    }

    @Test void controlInstructionWrapsAtWordsInsteadOfLeavingTheLastSyllableAlone() {
        var lines = ObjectiveTypography.wrap("수류탄 · 근접 능력도 사용하세요", 225, 18);
        assertTrue(lines.size() > 1);
        assertEquals("사용하세요", lines.getLast());
    }
}
