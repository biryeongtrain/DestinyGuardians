package kim.biryeong.destiny.fireteam;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import javax.imageio.ImageIO;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import static org.junit.jupiter.api.Assertions.*;

class LaunchLoadingScreenTest {
    @Test void spinnerOrbitsOnceEveryTwentyFourTicksAndStaysInTheFontRange() {
        assertEquals('\ue500', LaunchLoadingScreen.spinner(0));
        assertEquals('\ue500', LaunchLoadingScreen.spinner(1));
        assertEquals('\ue501', LaunchLoadingScreen.spinner(2));
        assertEquals('\ue50b', LaunchLoadingScreen.spinner(23));
        assertEquals('\ue500', LaunchLoadingScreen.spinner(24));
        for (int age = 0; age < 1000; age++) {
            char c = LaunchLoadingScreen.spinner(age);
            assertTrue(c >= '\ue500' && c <= '\ue50b');
        }
    }

    @Test void barHasAFixedWidthWhateverTheProgress() {
        for (int i = 0; i <= 200; i++) {
            float p = i / 200f;
            assertEquals(LaunchLoadingScreen.SEGMENTS, LaunchLoadingScreen.bar(p, false).length());
            assertEquals(LaunchLoadingScreen.SEGMENTS, LaunchLoadingScreen.bar(p, true).length());
        }
        assertEquals(LaunchLoadingScreen.SEGMENTS, LaunchLoadingScreen.bar(-4, false).length());
        assertEquals(LaunchLoadingScreen.SEGMENTS, LaunchLoadingScreen.bar(9, true).length());
    }

    @Test void barFillsLeftToRightWithOnePartialSegmentAndAGoldHead() {
        assertEquals(String.valueOf(LaunchLoadingScreen.BAR_EMPTY).repeat(LaunchLoadingScreen.SEGMENTS), LaunchLoadingScreen.bar(0, false));
        assertEquals(String.valueOf(LaunchLoadingScreen.BAR_FULL).repeat(LaunchLoadingScreen.SEGMENTS), LaunchLoadingScreen.bar(1, true));
        String half = LaunchLoadingScreen.bar(.5f, false);
        int full = 0; while (full < half.length() && half.charAt(full) == LaunchLoadingScreen.BAR_FULL) full++;
        assertEquals(LaunchLoadingScreen.SEGMENTS / 2 - 1, full, "the last whole segment is the head");
        assertEquals(LaunchLoadingScreen.BAR_HEAD, half.charAt(full));
        for (int i = full + 1; i < half.length(); i++) assertEquals(LaunchLoadingScreen.BAR_EMPTY, half.charAt(i));
        // A partial segment is one of the intermediate glyphs and follows only full ones.
        String third = LaunchLoadingScreen.bar(.33f, false);
        long partial = third.chars().filter(c -> c > LaunchLoadingScreen.BAR_EMPTY && c < LaunchLoadingScreen.BAR_FULL).count();
        assertTrue(partial <= 1);
    }

    @Test void shownProgressNeverRunsBackwardsAndHoldsBackUntilTheDestinationIsLoaded() {
        float shown = 0;
        float last = 0;
        for (int age = 0; age < 3000; age++) {
            float measured = age < 600 ? Math.min(.88f, age / 600f * .88f) : age < 700 ? .5f : -1f;   // a glitchy measurement dips
            shown = LaunchLoadingScreen.ease(shown, LaunchLoadingScreen.goal(measured, age, false), false);
            assertTrue(shown >= last, "monotonic at " + age);
            assertTrue(shown <= LaunchLoadingScreen.WAITING_CAP + 1e-4f, "never complete before loaded: " + shown);
            assertTrue(LaunchLoadingScreen.percent(shown, false) <= 99);
            last = shown;
        }
        for (int i = 0; i < 40; i++) shown = LaunchLoadingScreen.ease(shown, LaunchLoadingScreen.goal(.9f, 0, true), true);
        assertEquals(1f, shown, .001f);
        assertEquals(100, LaunchLoadingScreen.percent(shown, true));
    }

    @Test void anUnmeasuredActivityStillMovesButNeverFinishes() {
        float early = LaunchLoadingScreen.goal(-1, 20, false), mid = LaunchLoadingScreen.goal(-1, 400, false), late = LaunchLoadingScreen.goal(-1, 100_000, false);
        assertTrue(early > 0 && early < mid && mid < late);
        assertTrue(late <= LaunchLoadingScreen.WAITING_CAP);
    }

    @Test void fontDefinitionPointsAtSheetsThatMatchTheirGlyphGrid() throws Exception {
        try (var in = getClass().getResourceAsStream("/assets/destiny/font/loading_ui.json")) {
            assertNotNull(in);
            var providers = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonArray("providers");
            assertEquals(2, providers.size());
            for (var element : providers) {
                var provider = element.getAsJsonObject();
                assertEquals("bitmap", provider.get("type").getAsString());
                var file = provider.get("file").getAsString();
                assertTrue(file.startsWith("destiny:font/"));
                var chars = provider.getAsJsonArray("chars");
                try (var sheet = getClass().getResourceAsStream("/assets/destiny/textures/" + file.substring("destiny:".length()))) {
                    assertNotNull(sheet, file);
                    var image = ImageIO.read(sheet);
                    int columns = chars.get(0).getAsString().length();
                    assertEquals(0, image.getWidth() % columns, file + " width must divide into the glyph columns");
                    assertEquals(provider.get("height").getAsInt(), image.getHeight() / chars.size(), file + " cell height");
                    assertTrue(provider.get("ascent").getAsInt() <= provider.get("height").getAsInt());
                }
            }
            assertEquals(LaunchLoadingScreen.SPINNER_FRAMES, providers.get(0).getAsJsonObject().getAsJsonArray("chars").get(0).getAsString().length());
            assertEquals(LaunchLoadingScreen.BAR_HEAD - LaunchLoadingScreen.BAR_EMPTY + 1,
                    providers.get(1).getAsJsonObject().getAsJsonArray("chars").get(0).getAsString().length());
        }
    }
}
