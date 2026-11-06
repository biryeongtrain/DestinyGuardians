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
        // W244: native movement-speed FOV only. Omit the optional projection override
        // even when an older server config still enables it; keep HUD/core shaders intact.
        var shaderConfig=kim.biryeong.minigamelib.shaderfx.impl.ModConfig.getInstance();
        if(shaderConfig.dynamicFovShader) {
            shaderConfig.dynamicFovShader=false;
            kim.biryeong.minigamelib.shaderfx.impl.ModConfig.save();
            LOGGER.info("Dynamic FOV projection disabled; ADS uses native movement speed");
        }
        kim.biryeong.destiny.fx.HunterModelAssets.prepare();
        kim.biryeong.destiny.fx.ClassSuperModelAssets.prepare();
        kim.biryeong.destiny.fx.SwordModelAssets.prepare();
        kim.biryeong.destiny.fx.SwordStanceAssets.prepare();
        kim.biryeong.destiny.fx.SwordPoseW140Assets.prepare();
        kim.biryeong.destiny.fx.SwordPoseW146Assets.prepare();
        kim.biryeong.destiny.fx.HunterVfxAssets.prepare();
        kim.biryeong.destiny.campaign.model.RisingModelAssets.prepare();
        kim.biryeong.destiny.campaign.model.DevilsModelAssets.prepare();
        // destiny 네임스페이스 에셋을 서버 리소스팩에 포함시킨다.
        PolymerResourcePackUtils.addModAssets(MOD_ID);
        PolymerResourcePackUtils.markAsRequired();
        kim.biryeong.destiny.fx.SwordHandModelAssets.register();
        kim.biryeong.destiny.compat.pack.ParticleTextureFallbacks.init();
        kim.biryeong.destiny.compat.pack.WeaponPackOptimizer.init();
        // W115 R2 is an opt-in native candidate until alpha/shading/art acceptance.
        if (Boolean.getBoolean("destiny.weapon.surface.w115")) {
            kim.biryeong.destiny.weapon.WeaponSurfaceAssets.init();
        }
        // W123 migration namespace now carries thirty-four W126-W138 weapons and moving parts.
        // Explicit W115 keeps its two legacy weapons without overlapping converters.
        // Keep a server-side art fallback without changing gameplay or item IDs.
        if (Boolean.parseBoolean(System.getProperty("destiny.weapon.surface.w123", "true"))) {
            kim.biryeong.destiny.weapon.WeaponSurfaceW123Assets.init();
        }

        if (FabricLoader.getInstance().isModLoaded("polymer-autohost")) {
            kim.biryeong.destiny.compat.pack.StartupPackCoordinator.init();
        }

        kim.biryeong.destiny.experimental.ProfileArmProbe.init();
        kim.biryeong.destiny.weapon.ProfileWeaponView.init();
        kim.biryeong.destiny.activity.presentation.CinematicHands.init();
        Guardians.init();
        kim.biryeong.destiny.input.ClientControls.init();
        kim.biryeong.destiny.inventory.WeaponScreen.init();
        kim.biryeong.destiny.loot.Loot.init();
        kim.biryeong.destiny.economy.Economy.init();
        kim.biryeong.destiny.fireteam.Fireteams.init();
        kim.biryeong.destiny.hud.IncomingDamageHud.init();
        kim.biryeong.destiny.weapon.WeaponPreviewItem.init();
        kim.biryeong.destiny.weapon.WeaponRuntime.init();
        kim.biryeong.destiny.weapon.WeaponSkinArms.init();
        kim.biryeong.destiny.fx.WeaponDamageNumbers.init();
        kim.biryeong.destiny.weapon.AmmoEconomy.init();
        HunterAbilities.register();
        kim.biryeong.destiny.ability.titan.TitanAbilities.register();
        kim.biryeong.destiny.ability.warlock.WarlockAbilities.register();
        AbilityRegistry.registerReloadListener();
        AbilityService.init();
        kim.biryeong.destiny.world.TowerSpawnWorld.init();
        kim.biryeong.destiny.down.GuardianDown.init();
        kim.biryeong.destiny.crucible.CrucibleRuntime.init();
        // W300 Guardian Rises services must register before the campaign entry (Tutorial.init -> RisingCampaign.init).
        kim.biryeong.destiny.campaign.fallen.RisingFallen.init();
        kim.biryeong.destiny.campaign.map.RisingZones.init();
        kim.biryeong.destiny.campaign.presentation.RisingPresentation.init();
        kim.biryeong.destiny.tutorial.Tutorial.init();
        kim.biryeong.destiny.strike.devils.DevilsLair.init();
        GuardianCommands.register();
        kim.biryeong.destiny.weapon.WeaponCommands.register();
        kim.biryeong.destiny.sound.SoundCommands.register();
        DebugCommands.register();
        kim.biryeong.destiny.debug.HunterQa.init();
        if (FabricLoader.getInstance().isModLoaded("gcb-server")) {
            initGcb();
        }
        // Last pack hook: lossless output compression after every other converter.
        kim.biryeong.destiny.compat.pack.PackCompression.init();

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
