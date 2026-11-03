package kim.biryeong.destiny.campaign.model;

import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.loader.api.FabricLoader;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;

/** Installs the strike-owned models before BetterModel scans its model directory. */
public final class DevilsModelAssets {
    public static final List<String> MODELS = List.of("dl_thrall", "dl_acolyte", "dl_knight", "dl_wizard",
            "dl_servitor", "dl_sepiks", "dl_brig", "dl_marauder", "dl_skiff");
    private DevilsModelAssets() { }
    static byte[] bundled(String name) throws IOException {
        if (!MODELS.contains(name)) throw new IllegalArgumentException("Not a Devils Lair model: " + name);
        try (var in = DevilsModelAssets.class.getResourceAsStream("/destiny/devils_lair/models/" + name + ".bbmodel")) {
            if (in == null) throw new IOException("Missing strike model: " + name);
            return in.readAllBytes();
        }
    }
    static RisingModelAssets.Outcome install(Path config, String name) throws IOException {
        return RisingModelAssets.installOwned(config.resolve("bettermodel/models"),
                config.resolve("destiny/devils_lair/models"), name, bundled(name));
    }
    public static void prepare() {
        for (String name : MODELS) try {
            var outcome = install(FabricLoader.getInstance().getConfigDir(), name);
            if (outcome == RisingModelAssets.Outcome.KEPT_USER_COPY || outcome == RisingModelAssets.Outcome.SKIPPED_LINK)
                DestinyGuardians.LOGGER.warn("Devils Lair model {}: {}; preserving external copy", name, outcome);
            else if (outcome != RisingModelAssets.Outcome.CURRENT)
                DestinyGuardians.LOGGER.info("Devils Lair model {} {}", name, outcome);
        } catch (IOException e) {
            DestinyGuardians.LOGGER.error("Cannot install Devils Lair model {}", name, e);
        }
    }
}
