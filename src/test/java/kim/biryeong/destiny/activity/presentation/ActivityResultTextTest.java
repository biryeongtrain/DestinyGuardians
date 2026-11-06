package kim.biryeong.destiny.activity.presentation;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class ActivityResultTextTest {
    @Test void longUnicodeNamesFitMeasuredColumnAndFractionalDamageIsNotDiscarded() {
        String name = "아주긴수호자이름LongGuardianName".repeat(4);
        String fit = ActivityResultText.fit(name, 25, 400);
        assertTrue(fit.endsWith("…")); assertTrue(ActivityResultText.width(fit, 25) <= 400);
        assertEquals("1,234", ActivityResultText.damage(1234)); assertEquals("1,234.5", ActivityResultText.damage(1234.5));
    }
}
