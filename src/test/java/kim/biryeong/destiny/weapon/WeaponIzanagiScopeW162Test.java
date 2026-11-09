package kim.biryeong.destiny.weapon;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/** Pure assets/profile and actual 26.3 client codecs. Runtime/pack rendering remain separate. */
class WeaponIzanagiScopeW162Test {
    // Frozen pre-W327 roster assertions retain their original counts; new identities have separate coverage.
    private static final Path ASSETS = Path.of("src/main/resources/assets/destiny");
    private static final String NAME = "scope_w162_izanagis_burden_";
    private static WeaponCatalog.Entry izanagi() { return WeaponCatalog.find("izanagis_burden").orElseThrow(); }
    private static JsonObject json(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }

    @Test void addsOnlyIzanagiToFiveExistingScopesAndNeverAHandCannon() throws Exception {
        var ids = Set.of("bite_of_the_fox", "beloved", "apostate", "line_in_the_sand", "stormchaser", "izanagis_burden");
        assertFalse(WeaponScopes.supports(null));
        for (var entry : WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id())).toList()) {
            assertEquals(ids.contains(entry.id()), WeaponScopes.supports(entry), entry.id());
            if (entry.family().equals("hand_cannon")) assertFalse(WeaponScopes.supports(entry));
            if (WeaponScopes.supports(entry))
                assertEquals("destiny:weapon_scope_w45/" + entry.id(), WeaponScopes.model(entry).toString());
        }
        var e = izanagi();
        assertFalse(WeaponScopes.supports(new WeaponCatalog.Entry(e.id(), "hand_cannon", e.frame(),
                e.name(), e.source_frame_label(), e.item_model())));
        try (var files = Files.list(ASSETS.resolve("items/weapon_scope_w45"))) {
            assertEquals(ids.stream().map(id -> id + ".json").collect(Collectors.toSet()),
                    files.map(p -> p.getFileName().toString()).collect(Collectors.toSet()));
        }
    }

    @Test void existingSourceZoomAndFiniteHonedFundingStayUnchanged() {
        assertEquals(45, WeaponCharacteristics.of(izanagi()).stats().get("3555269338"));
        var aim = WeaponAimProfile.of(izanagi());
        assertEquals(4.5f, aim.zoom()); assertEquals(9, aim.transitionTicks());
        assertEquals(4.5f, aim.falloffScalar());
        assertEquals(61, WeaponProfile.forEntry(izanagi()).reloadTicks());
        assertEquals(WeaponModels.Grip.TWO_HAND, WeaponModels.defaultGrip(izanagi()));
        var ammo = new WeaponMagazine(WeaponProfile.forEntry(izanagi()), 1, 5);
        assertTrue(ammo.compressRounds(4));
        assertEquals(1, ammo.rounds()); assertEquals(2, ammo.reserve()); assertEquals(3, ammo.total());
        assertEquals(3.91f, WeaponIzanagi.multiplier(4, true, false));
    }

    @Test void generatedAssetsAndResearchInputsMatchManifestPins() throws Exception {
        var m = json(Path.of("art/weapons/w162/izanagi-scope.json"));
        assertTrue(m.get("artwork").getAsString().contains("Authored approximation"));
        assertEquals(7, m.getAsJsonObject("sha256").size());
        for (String key : List.of("sourceSha256", "sha256")) for (var pin : m.getAsJsonObject(key).entrySet()) {
            assertEquals(pin.getValue().getAsString(), HexFormat.of().formatHex(
                    MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of(pin.getKey())))), pin.getKey());
        }
    }

    @Test void maskCoversUltrawideEdgesWhileHollowAimAndWorldWindowStayClear() throws Exception {
        var frame = ImageIO.read(ASSETS.resolve("textures/item/hud/" + NAME + "frame.png").toFile());
        assertEquals(1024, frame.getWidth()); assertEquals(1024, frame.getHeight());
        assertEquals(255, frame.getRGB(32, 512) >>> 24);
        assertEquals(255, frame.getRGB(992, 512) >>> 24);
        assertEquals(255, frame.getRGB(320, 380) >>> 24, "Clipped corner");
        assertEquals(0, frame.getRGB(330, 430) >>> 24, "Wide opening");
        for (int y = 480; y < 544; y++) for (int x = 480; x < 544; x++)
            assertEquals(0, frame.getRGB(x, y) >>> 24, "Unobstructed world at the real aim ray");
        var sight = ImageIO.read(ASSETS.resolve("textures/item/hud/" + NAME + "reticle.png").toFile());
        assertEquals(128, sight.getWidth()); assertEquals(0, sight.getRGB(64, 64) >>> 24);
        assertTrue((sight.getRGB(64, 58) >>> 24) > 100);
    }

    @Test void actualClientCodecsAcceptScopeWrapperAndBothTintedHudQuads() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap(); ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        for (String item : List.of("weapon_scope_w45/izanagis_burden", "gui/hud/" + NAME + "frame", "gui/hud/" + NAME + "reticle")) {
            var result = ItemModels.CODEC.parse(JsonOps.INSTANCE, json(ASSETS.resolve("items/" + item + ".json")).get("model"));
            assertTrue(result.isSuccess(), () -> item + ": " + result.error());
        }
        for (String part : List.of("frame", "reticle")) {
            var model = json(ASSETS.resolve("models/gui/hud/" + NAME + part + ".json"));
            assertNotNull(CuboidModel.fromStream(new StringReader(model.toString())));
            assertEquals("destiny:item/hud/" + NAME + part, model.getAsJsonObject("textures").get("0").getAsString());
            assertEquals("destiny:item/hud/" + NAME + part, model.getAsJsonObject("textures").get("particle").getAsString());
            assertTrue(Files.isRegularFile(ASSETS.resolve("textures/item/hud/" + NAME + part + ".png")),
                    "Actual items-atlas file must exist; JSON codec alone cannot prove atlas resolution");
        }
    }

    @Test void emptyBranchesAreOnlyFirstPersonAndNonFpStillUsesChargeAndGripSelectors() throws Exception {
        var wrapper = json(ASSETS.resolve("items/weapon_scope_w45/izanagis_burden.json"));
        assertFalse(wrapper.get("hand_animation_on_swap").getAsBoolean());
        var model = wrapper.getAsJsonObject("model");
        assertEquals("minecraft:display_context", model.get("property").getAsString());
        var cases = model.getAsJsonArray("cases"); assertEquals(1, cases.size());
        assertEquals(JsonParser.parseString("[\"firstperson_righthand\",\"firstperson_lefthand\"]"), cases.get(0).getAsJsonObject().get("when"));
        assertEquals("minecraft:empty", cases.get(0).getAsJsonObject().getAsJsonObject("model").get("type").getAsString());
        var fallback = model.getAsJsonObject("fallback");
        assertEquals("minecraft:range_dispatch", fallback.get("type").getAsString());
        assertEquals(6, fallback.get("index").getAsInt());
        assertTrue(fallback.toString().contains("izanagis_burden_scope_twohand"));
        assertTrue(fallback.toString().contains("weapon_izanagi_w91/charged_"));
        assertFalse(fallback.toString().contains("minecraft:empty"));
    }
}
