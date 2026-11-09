package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import javax.imageio.ImageIO;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static kim.biryeong.destiny.weapon.ShotgunSpread.Shape.*;
import static org.junit.jupiter.api.Assertions.*;

/** Historical qualitative shapes; numerical coordinates and ADS remain local Minecraft tuning. */
class ShotgunPatternW105Test {
    // Frozen pre-W327 roster assertions retain their original counts; new identities have separate coverage.
    private static final double EPS = 1e-11;
    private static final Map<String, ShotgunSpread.Shape> SHAPES = Map.of(
            "mindbender_s_ambition_adept", CONE, "dust_rock_blues", VERTICAL_OVAL,
            "parcel_of_stardust_fell_to_earth", DIAMOND, "ikelos_sg_v1_0_1", SQUARE,
            "first_in_last_out", SLUG);
    private static final Map<String, Double> BUDGETS = Map.of(
            "mindbender_s_ambition_adept", 18.4, "dust_rock_blues", 16.,
            "parcel_of_stardust_fell_to_earth", 15.2, "ikelos_sg_v1_0_1", 13.6,
            "first_in_last_out", 13.);

    // Independent golden coordinates: do not obtain expectations from production offsets().
    private static List<ShotgunSpread.Point> expected(ShotgunSpread.Shape shape) {
        return switch (shape) {
            case CONE -> points(0, 0, -.35, .35, .35, .35, .35, -.35, -.35, -.35,
                    0, 1, .78, .62, .97, -.22, .43, -.90, -.43, -.90, -.97, -.22, -.78, .62);
            case VERTICAL_OVAL -> points(-.22, 1, .22, 1, .48, .48, .61, 0, .48, -.48,
                    .22, -1, -.22, -1, -.48, -.48, -.61, 0, -.48, .48, 0, .32, 0, -.32);
            case DIAMOND -> points(0, .85, 1, 0, 0, -.85, -1, 0, .49, .49, .49, -.49,
                    -.49, -.49, -.49, .49, 0, .38, .38, 0, 0, -.38, -.38, 0);
            case SQUARE -> points(-.60, .60, 0, .60, .60, .60, .60, 0, .60, -.60,
                    0, -.60, -.60, -.60, -.60, 0, -.32, .32, .32, .32, .32, -.32, -.32, -.32);
            case SLUG -> points(0, 0);
        };
    }

    private static List<ShotgunSpread.Point> points(double... xy) {
        var result = new java.util.ArrayList<ShotgunSpread.Point>();
        for (int i = 0; i < xy.length; i += 2) result.add(new ShotgunSpread.Point(xy[i], xy[i+1]));
        return List.copyOf(result);
    }

    private static double dot(ShotgunSpread.Vector a, ShotgunSpread.Vector b) {
        return a.x()*b.x() + a.y()*b.y() + a.z()*b.z();
    }

    private static void finite(ShotgunSpread.Vector v) {
        assertTrue(Double.isFinite(v.x()) && Double.isFinite(v.y()) && Double.isFinite(v.z()));
    }

    @Test
    void independentCoordinatesCountSymmetryAndFilledShapeExtentsAreStableAndImmutable() {
        for (var shape : ShotgunSpread.Shape.values()) {
            var actual = ShotgunSpread.offsets(shape);
            var golden = expected(shape);
            assertEquals(shape == SLUG ? 1 : 12, actual.size(), shape.toString());
            assertEquals(actual.size(), new HashSet<>(actual).size(), "No duplicate pellets");
            for (int i = 0; i < actual.size(); i++) {
                var p = actual.get(i);
                assertEquals(golden.get(i).x(), p.x(), EPS, shape + " x " + i);
                assertEquals(golden.get(i).y(), p.y(), EPS, shape + " y " + i);
                assertTrue(actual.stream().anyMatch(other -> Math.abs(other.x()+p.x()) < EPS
                        && Math.abs(other.y()-p.y()) < EPS), "Horizontal mirror for " + shape);
                if (shape != CONE) assertTrue(actual.stream().anyMatch(other -> Math.abs(other.x()+p.x()) < EPS
                        && Math.abs(other.y()+p.y()) < EPS), "Opposite pellet for " + shape);
            }
            assertEquals(0, actual.stream().mapToDouble(ShotgunSpread.Point::x).sum(), EPS);
            assertEquals(0, actual.stream().mapToDouble(ShotgunSpread.Point::y).sum(), EPS);
            assertThrows(UnsupportedOperationException.class, () -> actual.add(new ShotgunSpread.Point(9, 9)));
            assertThrows(UnsupportedOperationException.class, () -> actual.set(0, new ShotgunSpread.Point(9, 9)));
            assertEquals(actual, ShotgunSpread.offsets(shape));
        }
        var cone = ShotgunSpread.offsets(CONE);
        assertEquals(5, cone.stream().filter(p -> Math.hypot(p.x(), p.y()) < .5).count(),
                "Aggressive cone has a center plus four interior witnesses, not a hollow ring");
        assertTrue(ShotgunSpread.offsets(VERTICAL_OVAL).stream().mapToDouble(p -> Math.abs(p.x())).max().orElseThrow()
                < ShotgunSpread.offsets(VERTICAL_OVAL).stream().mapToDouble(p -> Math.abs(p.y())).max().orElseThrow());
        assertTrue(ShotgunSpread.offsets(DIAMOND).stream().allMatch(p -> Math.abs(p.x())+Math.abs(p.y()) <= 1+EPS));
        assertTrue(ShotgunSpread.offsets(SQUARE).stream().anyMatch(p -> Math.abs(p.x()) > .59 && Math.abs(p.y()) > .59));
    }

    @Test
    void angularSeparationAndBasisSurviveAllPitchIncludingExactAndNearlyVerticalAim() {
        for (double yaw : new double[]{-180, -135, -90, -45, 0, 45, 90, 135, 180}) {
            for (double pitch : new double[]{-90, -89.999999, -89.9, -60, -15, 0, 15, 60, 89.9, 89.999999, 90}) {
                double y = Math.toRadians(yaw), p = Math.toRadians(pitch);
                var forward = new ShotgunSpread.Vector(-Math.sin(y)*Math.cos(p), -Math.sin(p), Math.cos(y)*Math.cos(p));
                double horizontal = Math.hypot(forward.x(), forward.z());
                var right = horizontal < 1e-12 ? new ShotgunSpread.Vector(1, 0, 0)
                        : new ShotgunSpread.Vector(-forward.z()/horizontal, 0, forward.x()/horizontal);
                var up = new ShotgunSpread.Vector(-right.z()*forward.y(),
                        right.z()*forward.x()-right.x()*forward.z(), right.x()*forward.y());
                assertEquals(0, dot(forward, right), EPS);
                assertEquals(0, dot(forward, up), EPS);
                assertEquals(0, dot(right, up), EPS);
                for (var shape : ShotgunSpread.Shape.values()) for (var point : expected(shape)) {
                    for (double spread : new double[]{0, .078, .099, .12}) {
                        var result = ShotgunSpread.direction(forward, point, spread);
                        finite(result);
                        assertEquals(1, result.length(), EPS);
                        double along = dot(result, forward);
                        assertTrue(along > 0, "Forward hemisphere");
                        assertEquals(point.x()*spread, dot(result, right)/along, EPS, "Horizontal tangent");
                        assertEquals(point.y()*spread, dot(result, up)/along, EPS, "Vertical tangent");
                        double angle = Math.atan2(Math.hypot(dot(result, right), dot(result, up)), along);
                        assertEquals(Math.atan(Math.hypot(point.x(), point.y())*spread), angle, EPS);
                        assertEquals(result, ShotgunSpread.direction(forward, point, spread), "No random roll or jitter");
                        var scaled = new ShotgunSpread.Vector(forward.x()*7, forward.y()*7, forward.z()*7);
                        var repeated = ShotgunSpread.direction(scaled, point, spread);
                        assertEquals(result.x(), repeated.x(), EPS);
                        assertEquals(result.y(), repeated.y(), EPS);
                        assertEquals(result.z(), repeated.z(), EPS);
                    }
                }
            }
        }
    }

    @Test
    void malformedDirectionsOffsetsAndSpreadsReturnDeterministicFiniteFallbacks() {
        var point = new ShotgunSpread.Point(.5, -.5);
        for (var forward : new ShotgunSpread.Vector[]{null, new ShotgunSpread.Vector(0, 0, 0),
                new ShotgunSpread.Vector(Double.NaN, 1, 0), new ShotgunSpread.Vector(1, Double.POSITIVE_INFINITY, 0),
                new ShotgunSpread.Vector(0, 0, Double.NEGATIVE_INFINITY), new ShotgunSpread.Vector(1e-20, 0, 0)}) {
            var actual = ShotgunSpread.direction(forward, point, .12);
            finite(actual);
            assertEquals(new ShotgunSpread.Vector(0, 0, 0), actual);
        }
        var forward = new ShotgunSpread.Vector(3, 0, 0);
        for (double spread : new double[]{0, -1, Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY})
            assertEquals(new ShotgunSpread.Vector(1, 0, 0), ShotgunSpread.direction(forward, point, spread));
        for (var invalid : new ShotgunSpread.Point[]{null, new ShotgunSpread.Point(Double.NaN, 0),
                new ShotgunSpread.Point(0, Double.POSITIVE_INFINITY)})
            assertEquals(new ShotgunSpread.Vector(1, 0, 0), ShotgunSpread.direction(forward, invalid, .12));
    }

    @Test
    void onlyExactFiveCatalogShotgunsParticipateAndLegacyBodyBudgetsSurviveTwelvePellets() {
        assertEquals(SHAPES.keySet(), WeaponCatalog.family("shotgun").stream().filter(e -> !LegendaryWeapons.contains(e.id()) && !WeaponExotics.expanded(e))
                .map(WeaponCatalog.Entry::id).collect(java.util.stream.Collectors.toSet()));
        for (var entry : WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id()) && !WeaponExotics.expanded(e)).toList()) {
            var actual = ShotgunPatternProfile.shape(entry);
            var profile = WeaponProfile.forEntry(entry);
            if (SHAPES.containsKey(entry.id())) {
                assertEquals(SHAPES.get(entry.id()), actual.orElseThrow(), entry.id());
                int count = SHAPES.get(entry.id()) == SLUG ? 1 : 12;
                assertEquals(count, ShotgunPatternProfile.pellets(entry));
                assertEquals(count, profile.pellets());
                assertEquals(BUDGETS.get(entry.id()), profile.damage()*profile.pellets(), 2e-5, entry.id());
                assertEquals(count == 1 ? 0 : .12, profile.spread(), EPS);
            } else {
                assertTrue(actual.isEmpty(), entry.id());
                assertEquals(0, ShotgunPatternProfile.pellets(entry), entry.id());
                assertEquals(1, profile.pellets(), "Other families retain original single-ray/bolt profile: " + entry.id());
            }
        }
        var real = WeaponCatalog.find("dust_rock_blues").orElseThrow();
        for (var impostor : List.of(
                new WeaponCatalog.Entry("unknown_shotgun", "shotgun", "precision", "Unknown", "", "destiny:weapon/unknown_shotgun"),
                new WeaponCatalog.Entry(real.id(), "auto_rifle", real.frame(), real.name(), real.source_frame_label(), real.item_model()),
                new WeaponCatalog.Entry(real.id(), real.family(), "unknown_frame", real.name(), real.source_frame_label(), real.item_model()))) {
            assertTrue(ShotgunPatternProfile.shape(impostor).isEmpty(), "Identity/family/frame must all match");
            assertEquals(0, ShotgunPatternProfile.pellets(impostor));
        }
    }

    @Test
    void retainedLocalAdsRuleIsAppliedExactlyOnceAndClampsProgress() {
        for (float ads : new float[]{-1, 0, .25f, .5f, .75f, 1, 2, Float.NaN, Float.POSITIVE_INFINITY}) {
            double progress = Float.isFinite(ads) ? Math.clamp(ads, 0, 1) : 0;
            double expected = .12*(1-.35*progress);
            double spread = ShotgunPatternProfile.spread(.12, ads);
            assertEquals(expected, spread, EPS);
            var ray = ShotgunSpread.direction(new ShotgunSpread.Vector(1, 0, 0), new ShotgunSpread.Point(0, 1), spread);
            assertEquals(expected, ray.y()/ray.x(), EPS, "No second ADS shrink inside direction()");
        }
        assertEquals(.078, ShotgunPatternProfile.spread(.12, 1), EPS);
    }

    @Test
    void fourFrameAssetsResolveToDistinctTransparentFlatQuadsWithoutNewHudNodes() throws Exception {
        var root = Path.of("src/main/resources/assets/destiny");
        var textures = new HashSet<String>();
        for (String frame : Set.of("aggressive", "precision", "lightweight", "rapid_fire")) {
            String name = "reticle_w105_shotgun_" + frame;
            var item = JsonParser.parseString(Files.readString(root.resolve("items/gui/hud/"+name+".json"))).getAsJsonObject();
            var model = item.getAsJsonObject("model");
            assertEquals("destiny:gui/hud/"+name, model.get("model").getAsString());
            assertEquals("minecraft:model", model.get("type").getAsString());
            var quad = JsonParser.parseString(Files.readString(root.resolve("models/gui/hud/"+name+".json"))).getAsJsonObject();
            assertEquals("destiny:item/hud/"+name, quad.getAsJsonObject("textures").get("0").getAsString());
            assertEquals(1, quad.getAsJsonArray("elements").size());
            var element = quad.getAsJsonArray("elements").get(0).getAsJsonObject();
            assertEquals(element.getAsJsonArray("from").get(2), element.getAsJsonArray("to").get(2), "Flat quad");
            var png = root.resolve("textures/item/hud/"+name+".png");
            var image = ImageIO.read(png.toFile());
            assertNotNull(image);
            assertTrue(image.getColorModel().hasAlpha());
            assertEquals(0, image.getRGB(0, 0) >>> 24);
            assertEquals(0, image.getRGB(image.getWidth()/2, image.getHeight()/2) >>> 24, "Existing dot owns center");
            textures.add(java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256")
                    .digest(Files.readAllBytes(png))));
        }
        assertEquals(4, textures.size());
        assertEquals(2, kim.biryeong.destiny.hud.WeaponReticleHud.MAX_NODES);
    }
}
