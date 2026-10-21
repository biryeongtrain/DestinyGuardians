package kim.biryeong.destiny;

import kim.biryeong.destiny.debug.DebugCommands;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class DestinyGuardians implements ModInitializer {
    public static final String MOD_ID = "destiny";
    public static final Logger LOGGER = LoggerFactory.getLogger("DestinyGuardians");

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MOD_ID, path);
    }

    @Override
    public void onInitialize() {
        // destiny 네임스페이스 에셋을 서버 리소스팩에 포함시킨다.
        PolymerResourcePackUtils.addModAssets(MOD_ID);
        PolymerResourcePackUtils.markAsRequired();

        DebugCommands.register();

        logDependency("polymer-core");
        logDependency("bettermodel");
        logDependency("minigamelib");
        LOGGER.info("Destiny Guardians initialized");
    }

    private static void logDependency(String modId) {
        String version = FabricLoader.getInstance().getModContainer(modId)
                .map(c -> c.getMetadata().getVersion().getFriendlyString())
                .orElse("missing");
        LOGGER.info("  {} = {}", modId, version);
    }
}
