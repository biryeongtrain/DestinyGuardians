package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.loader.api.FabricLoader;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/** Bundled versioned BetterModel defaults. An installed artist's file is never overwritten. */
public final class HunterVfxAssets {
    public static final List<String> MODELS = List.of("destiny_vfx_arc_h14", "destiny_vfx_solar_h14",
            "destiny_vfx_vortex_h14", "destiny_vfx_smoke_h14");
    public static final List<String> SUPER_MODELS = List.of("destiny_super_arc_sweep_h15",
            "destiny_super_solar_muzzle_h15", "destiny_super_solar_impact_h15", "destiny_super_void_anchor_h15");

    public static List<String> allModels() {
        return java.util.stream.Stream.concat(MODELS.stream(), SUPER_MODELS.stream()).toList();
    }

    private HunterVfxAssets() { }

    public static void prepare() {
        try {
            int installed = install(FabricLoader.getInstance().getConfigDir().resolve("bettermodel/models"));
            if (installed > 0) DestinyGuardians.LOGGER.info("Installed {} hunter VFX model defaults", installed);
        } catch (IOException e) {
            // Cosmetic failure must not prevent the gameplay server from starting.
            DestinyGuardians.LOGGER.error("Cannot install hunter VFX defaults; existing particles remain available", e);
        }
    }

    public static int install(Path directory) throws IOException {
        Files.createDirectories(directory);
        int installed = 0;
        for (String name : allModels()) {
            Path target = directory.resolve(name + ".bbmodel");
            if (Files.exists(target)) continue;
            try (var resource = HunterVfxAssets.class.getResourceAsStream("/destiny/vfx/" + name + ".bbmodel")) {
                if (resource == null) throw new IOException("Missing bundled VFX model " + name);
                Files.copy(resource, target); // Deliberately no REPLACE_EXISTING.
                installed++;
            }
        }
        return installed;
    }
}
