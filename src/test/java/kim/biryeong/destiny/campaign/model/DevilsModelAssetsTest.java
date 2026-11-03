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
    @Test void retiredModelsAreArchivedOnlyWhileStillOwned() throws Exception {
        Path models = config.resolve("bettermodel/models"), markers = config.resolve("destiny/devils_lair/models");
        byte[] original = "owned model".getBytes(StandardCharsets.UTF_8);
        RisingModelAssets.installOwned(models, markers, "dl_skiff", original);
        assertTrue(ModelAssetRetirement.retireOwned(models, markers, "dl_skiff"));
        assertFalse(Files.exists(models.resolve("dl_skiff.bbmodel")));
        assertArrayEquals(original, Files.readAllBytes(markers.resolve("dl_skiff."
                + RisingModelAssets.sha256(original) + ".retired.bbmodel")));
        assertFalse(ModelAssetRetirement.retireOwned(models, markers, "dl_skiff"));
        Files.writeString(models.resolve("dl_skiff.bbmodel"), "user edited model");
        assertFalse(ModelAssetRetirement.retireOwned(models, markers, "dl_skiff"));
        assertEquals("user edited model", Files.readString(models.resolve("dl_skiff.bbmodel")));
        Files.delete(models.resolve("dl_skiff.bbmodel"));
        Files.createSymbolicLink(models.resolve("dl_skiff.bbmodel"), markers.resolve("dl_skiff.sha256"));
        assertFalse(ModelAssetRetirement.retireOwned(models, markers, "dl_skiff"));
        assertTrue(Files.isSymbolicLink(models.resolve("dl_skiff.bbmodel")));
        assertFalse(DevilsModelAssets.MODELS.contains("dl_skiff"));
    }
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
            assertEquals(1, model.getAsJsonArray("textures").size(), name);
            var clips = new HashSet<String>();
            for (var entry : model.getAsJsonArray("animations")) {
                var animation = entry.getAsJsonObject();
                assertTrue(clips.add(animation.get("name").getAsString()), "Duplicate clip in " + name);
                assertTrue(animation.get("length").getAsDouble() > 0, name);
            }
            for (String clip : new String[]{"idle", "walk", "run", "shoot", "damage", "death", "spawn"})
                assertTrue(clips.contains(clip), name + ": " + clip);
            if (name.equals("dl_sepiks")) assertTrue(clips.contains("source_80e10752_sepix_intro"));
            if (name.equals("dl_marauder")) assertTrue(clips.contains("melee"));
            if (name.equals("dl_brig")) assertTrue(clips.contains("armor_break"));
        }
    }
}
