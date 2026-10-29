package kim.biryeong.destiny;

import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.command.GuardianCommands;
import kim.biryeong.destiny.debug.DebugCommands;
import kim.biryeong.destiny.guardian.Guardians;
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
        kim.biryeong.destiny.fx.HunterModelAssets.prepare();
        kim.biryeong.destiny.fx.ClassSuperModelAssets.prepare();
        kim.biryeong.destiny.fx.HunterVfxAssets.prepare();
        // destiny 네임스페이스 에셋을 서버 리소스팩에 포함시킨다.
        PolymerResourcePackUtils.addModAssets(MOD_ID);
        PolymerResourcePackUtils.markAsRequired();
        kim.biryeong.destiny.compat.pack.WeaponPackOptimizer.init();

        kim.biryeong.destiny.experimental.ProfileArmProbe.init();
        Guardians.init();
        kim.biryeong.destiny.inventory.WeaponScreen.init();
        HunterAbilities.register();
        kim.biryeong.destiny.ability.titan.TitanAbilities.register();
        kim.biryeong.destiny.ability.warlock.WarlockAbilities.register();
        AbilityRegistry.registerReloadListener();
        AbilityService.init();
        kim.biryeong.destiny.world.TowerSpawnWorld.init();
        GuardianCommands.register();
        DebugCommands.register();
        kim.biryeong.destiny.debug.HunterQa.init();
        if (FabricLoader.getInstance().isModLoaded("gcb-server")) {
            initGcb();
        }

        logDependency("polymer-core");
        logDependency("bettermodel");
        logDependency("minigamelib");
        logDependency("gcb-server");
        LOGGER.info("Destiny Guardians initialized");
    }

    private static void initGcb() {
        try {
            Class.forName("kim.biryeong.destiny.compat.gcb.GcbInputBridge").getMethod("init").invoke(null);
            LOGGER.info("GCB input bridge enabled");
        } catch (ReflectiveOperationException e) {
            LOGGER.warn("gcb-server is loaded but the bridge is not compiled in: {}", e.toString());
        }
    }

    private static void logDependency(String modId) {
        String version = FabricLoader.getInstance().getModContainer(modId)
                .map(c -> c.getMetadata().getVersion().getFriendlyString())
                .orElse("missing");
        LOGGER.info("  {} = {}", modId, version);
    }
}
