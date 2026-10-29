package kim.biryeong.destiny.fx;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/** Native parsing and routing only; master Vision owns the actual rendered acceptance. */
class GrenadeModelsW255Test {
    private static final Path ROOT = Path.of("src/main/resources/assets/destiny");
    private static final String PREFIX = "ability_w255/grenade/";
    private static final Map<String, String> DELIVERED = Map.of(
            "titan/solar_grenade", "fusion", "warlock/solar_grenade", "solar",
            "hunter/void_vortex", "vortex", "warlock/void_grenade", "vortex", "warlock/arc_grenade", "storm");
    private static final Map<String, String> FALLBACKS = Map.of(
            "hunter/arc_flashbang", "explosion", "hunter/solar_incendiary", "explosion",
            "titan/void_grenade", "explosion", "titan/arc_grenade", "pulse");

    @BeforeAll static void bootstrap() {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        // Same pure-JUnit fixture as SwordHandPacketsW139Test: 26.3 item defaults
        // are data-pack-bound; routing explicitly sets ITEM_MODEL on a PAPER carrier.
        var paper = (net.minecraft.core.Holder.Reference<net.minecraft.world.item.Item>)
                net.minecraft.core.registries.BuiltInRegistries.ITEM.wrapAsHolder(net.minecraft.world.item.Items.PAPER);
        if (!paper.areComponentsBound()) paper.bindComponents(net.minecraft.core.component.DataComponentMap.EMPTY);
        ItemModels.bootstrap();
        ItemTintSources.bootstrap();
    }

    @Test void exactAbilitiesSelectSeparateHeldAndFlightModelsWithoutReplacingMissingSpecies() {
        for (var entry : DELIVERED.entrySet()) {
            var ability = id(entry.getKey());
            var held = GrenadeModels.item(ability);
            var flight = GrenadeModels.projectile(ability);
            assertEquals(id(PREFIX + entry.getValue() + "_held"), model(held));
            assertEquals(id(PREFIX + entry.getValue() + "_projectile"), model(flight));
            assertNotEquals(model(held), model(flight));
            var enemy = AbilityVisualVariants.item(held, true);
            assertEquals(id(PREFIX + entry.getValue() + "_held_enemy"), model(enemy));
            assertNotSame(held, enemy);
            assertEquals(id(PREFIX + entry.getValue() + "_held"), model(held), "Do not mutate shared ally stack");
            assertEquals(id(PREFIX + entry.getValue() + "_projectile_enemy"),
                    model(AbilityVisualVariants.item(flight, true)));
        }
        for (var entry : FALLBACKS.entrySet()) {
            var expected = id("ability_w252/ripped_grenade/" + entry.getValue());
            assertEquals(expected, model(GrenadeModels.item(id(entry.getKey()))));
            assertEquals(expected, model(GrenadeModels.projectile(id(entry.getKey()))));
        }
        for (var unknown : List.of(id("warlock/solar_super"), id("titan/solar_grenade_extra"),
                Identifier.fromNamespaceAndPath("other", "titan/solar_grenade"))) {
            assertTrue(GrenadeModels.item(unknown).isEmpty());
            assertTrue(GrenadeModels.projectile(unknown).isEmpty());
        }
        assertTrue(GrenadeModels.item((Identifier) null).isEmpty());
        assertTrue(GrenadeModels.projectile(null).isEmpty());
        assertTrue(GrenadeModels.item(null, Element.SOLAR).isEmpty());
        assertTrue(GrenadeModels.item(GuardianClass.NONE, Element.SOLAR).isEmpty());
        assertTrue(GrenadeModels.item(GuardianClass.WARLOCK, null).isEmpty());
        assertTrue(GrenadeModels.item(GuardianClass.HUNTER, Element.KINETIC).isEmpty());
    }

    @Test void classDefaultsUseTheSameHeldCandidates() {
        for (var cls : List.of(GuardianClass.HUNTER, GuardianClass.TITAN, GuardianClass.WARLOCK)) {
            for (var element : List.of(Element.ARC, Element.SOLAR, Element.VOID)) {
                String path = switch (cls) {
                    case HUNTER -> switch (element) {
                        case ARC -> "hunter/arc_flashbang";
                        case SOLAR -> "hunter/solar_incendiary";
                        default -> "hunter/void_vortex";
                    };
                    case TITAN -> "titan/" + element.getSerializedName() + "_grenade";
                    default -> "warlock/" + element.getSerializedName() + "_grenade";
                };
                assertEquals(model(GrenadeModels.item(id(path))), model(GrenadeModels.item(cls, element)));
            }
        }
    }

    @Test void nativeCodecsAcceptAllSixteenPropsWithSmallAtlasesAndMatchingEnemyCoverage() throws Exception {
        for (String ability : List.of("fusion", "solar", "vortex", "storm")) {
            for (String phase : List.of("held", "projectile")) {
                String base = ability + "_" + phase;
                var ally = json(ROOT.resolve("models/item/" + PREFIX + base + ".json"));
                var enemy = json(ROOT.resolve("models/item/" + PREFIX + base + "_enemy.json"));
                assertEquals(ally.get("elements"), enemy.get("elements"), "Geometry/UV/light do not change for enemies");
                int count = ally.getAsJsonArray("elements").size();
                assertTrue(count > 0 && count <= 1000, base);
                for (String suffix : List.of("", "_enemy")) {
                    String name = base + suffix;
                    var item = json(ROOT.resolve("items/" + PREFIX + name + ".json"));
                    var parsed = ItemModels.CODEC.parse(JsonOps.INSTANCE, item.get("model"));
                    assertTrue(parsed.isSuccess(), name + " " + parsed.error());
                    assertEquals("destiny:item/" + PREFIX + name,
                            item.getAsJsonObject("model").get("model").getAsString());
                    var path = ROOT.resolve("models/item/" + PREFIX + name + ".json");
                    assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))));
                    var model = json(path);
                    assertEquals("destiny:item/" + PREFIX + name, model.getAsJsonObject("textures").get("0").getAsString());
                }
                var a = ImageIO.read(ROOT.resolve("textures/item/" + PREFIX + base + ".png").toFile());
                var b = ImageIO.read(ROOT.resolve("textures/item/" + PREFIX + base + "_enemy.png").toFile());
                assertEquals(512, a.getWidth()); assertEquals(512, a.getHeight());
                assertEquals(a.getWidth(), b.getWidth()); assertEquals(a.getHeight(), b.getHeight());
                int opaque = 0, colored = 0;
                for (int y = 0; y < a.getHeight(); y++) for (int x = 0; x < a.getWidth(); x++) {
                    int pixel = a.getRGB(x, y), red = b.getRGB(x, y);
                    assertEquals(pixel >>> 24, red >>> 24, base + " coverage");
                    if ((pixel >>> 24) >= 128) {
                        opaque++;
                        if (((pixel >> 16) & 255) != ((pixel >> 8) & 255)) colored++;
                        assertTrue(((red >> 16) & 255) > ((red >> 8) & 255), "Enemy is red");
                    }
                }
                assertTrue(opaque > 0 && colored > opaque / 4, "No neutral grey inspection shell: " + base);
            }
        }
    }

    @Test void manifestPinsEveryOutputAndRecordsProvisionalPhasesAndVisiblePassSelection() throws Exception {
        var manifest = json(Path.of("art/abilities/w255/grenade-manifest.json"));
        var outputs = manifest.getAsJsonObject("outputs");
        assertEquals(48, outputs.size());
        for (var entry : outputs.entrySet()) {
            String actual = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of(entry.getKey()))));
            assertEquals(entry.getValue().getAsString(), actual, entry.getKey());
        }
        var models = manifest.getAsJsonObject("models");
        assertEquals(8, models.size());
        for (var entry : models.entrySet()) {
            var record = entry.getValue().getAsJsonObject();
            assertTrue(record.getAsJsonObject("candidate").get("status").getAsString().contains("candidate"));
            assertTrue(record.get("elements").getAsInt() <= 1000);
            assertTrue(record.get("geometry_mapping_max_error_units").getAsDouble() < 1e-7);
            var selected = record.getAsJsonArray("selected_parts");
            assertEquals(entry.getKey().equals("fusion_projectile") || entry.getKey().equals("solar_projectile") ? 2 : 1, selected.size());
            assertEquals(0, selected.get(0).getAsInt());
        }
        assertTrue(manifest.getAsJsonArray("limitations").toString().contains("unsupported"));
    }

    private static Identifier id(String path) { return Identifier.fromNamespaceAndPath("destiny", path); }
    private static Identifier model(ItemStack stack) { return stack.get(DataComponents.ITEM_MODEL); }
    private static JsonObject json(Path path) throws Exception { return JsonParser.parseString(Files.readString(path)).getAsJsonObject(); }
}
