package kim.biryeong.destiny.campaign.model;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import static org.junit.jupiter.api.Assertions.*;

class DevilsModelAssetsTest {
    @TempDir Path config;
    @Test void allStrikeAssetsInstallAndPreserveForeignCopies() throws Exception {
        for (String name : DevilsModelAssets.MODELS) {
            assertEquals(RisingModelAssets.Outcome.INSTALLED, DevilsModelAssets.install(config, name));
            Path target = config.resolve("bettermodel/models/" + name + ".bbmodel");
            assertArrayEquals(DevilsModelAssets.bundled(name), Files.readAllBytes(target));
            assertEquals(RisingModelAssets.Outcome.CURRENT, DevilsModelAssets.install(config, name));
            Files.writeString(target, "external edit");
            assertEquals(RisingModelAssets.Outcome.KEPT_USER_COPY, DevilsModelAssets.install(config, name));
            assertEquals("external edit", Files.readString(target));
        }
        assertThrows(IllegalArgumentException.class, () -> DevilsModelAssets.install(config, "rg_walker"));
        assertFalse(Files.exists(config.resolve("bettermodel/models/rg_walker.bbmodel")));
    }
    @Test void runtimeAliasesAndRequiredIntroExistInBundledModels() throws Exception {
        for (String name : DevilsModelAssets.MODELS) {
            var model = JsonParser.parseString(new String(DevilsModelAssets.bundled(name), StandardCharsets.UTF_8)).getAsJsonObject();
            assertFalse(model.getAsJsonArray("elements").isEmpty(), name);
            assertEquals(name.equals("dl_skiff") ? 2 : 1, model.getAsJsonArray("textures").size(), name);
            var clips = new HashSet<String>();
            for (var entry : model.getAsJsonArray("animations")) {
                var animation = entry.getAsJsonObject();
                assertTrue(clips.add(animation.get("name").getAsString()), "Duplicate clip in " + name);
                assertTrue(animation.get("length").getAsDouble() > 0, name);
            }
            if (name.equals("dl_skiff")) {
                assertEquals(12000, model.getAsJsonArray("elements").size());
                assertEquals(java.util.Set.of("source_80a8a4e2", "source_80a8a51d", "source_80a8a51e",
                        "source_80a8a51f", "source_80a8a520", "source_80a8a521"), clips);
                continue; // An invulnerable presentation prop has no infantry attack/death aliases.
            }
            for (String clip : new String[]{"idle", "walk", "run", "shoot", "damage", "death", "spawn"})
                assertTrue(clips.contains(clip), name + ": " + clip);
            if (name.equals("dl_sepiks")) assertTrue(clips.contains("source_80e10752_sepix_intro"));
            if (name.equals("dl_marauder")) assertTrue(clips.contains("melee"));
            if (name.equals("dl_brig")) assertTrue(clips.contains("armor_break"));
        }
    }
}
