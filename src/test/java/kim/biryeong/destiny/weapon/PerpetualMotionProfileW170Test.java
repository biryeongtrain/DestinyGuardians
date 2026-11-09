package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;
import java.util.stream.Collectors;
import static org.junit.jupiter.api.Assertions.*;

/** Pure source/contract/math regression. No movement lifecycle or native-game claims. */
class PerpetualMotionProfileW170Test {
    private static final String ART = "art/weapons/w170/perpetual-motion/";
    private static final String RESOURCE = "src/main/resources/destiny/weapons/w170-perpetual-motion.json";
    private static JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static double solve(JsonObject c, int stat) {
        return (c.has("evpp") ? c.get("evpp").getAsDouble() : 0) * stat * stat
            + c.get("vpp").getAsDouble() * stat + c.get("offset").getAsDouble();
    }
    private static String sha(Path p) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));
    }
    @Test void exactTwoBaseRollsAndFull65RandomizedScan() throws Exception {
        assertEquals("perpetual_motion", PerpetualMotionProfile.ID);
        assertEquals(1428297954L, PerpetualMotionProfile.HASH);
        var rolls = PerpetualMotionProfile.rolls();
        assertEquals(Set.of(new WeaponPerks.Roll("aishas_embrace", 2638190703L, 3, 1428297954L, 7997267L),
            new WeaponPerks.Roll("retraced_path", 548958835L, 3, 1428297954L, 2945646047L)), Set.copyOf(rolls));
        assertThrows(UnsupportedOperationException.class, () -> rolls.clear());
        var sockets = json(ART + "official-sockets.json");
        assertEquals(65, sockets.get("selectedCount").getAsInt());
        assertEquals(2, sockets.get("supportedCount").getAsInt());
        assertEquals(2, sockets.get("randomizedCount").getAsInt());
        assertEquals(0, sockets.get("fixedCuratedCount").getAsInt());
        assertEquals(63, sockets.getAsJsonArray("unsupportedSelectedIds").size());
        var scans = sockets.getAsJsonArray("allSelectedPoolScans");
        assertEquals(65, scans.size());
        assertEquals(WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id()) && !WeaponExotics.expanded(legacy)).toList().stream().map(WeaponCatalog.Entry::id).collect(Collectors.toSet()),
            scans.asList().stream().map(e -> e.getAsJsonObject().get("id").getAsString()).collect(Collectors.toSet()));
        for (var e : sockets.getAsJsonArray("weapons")) {
            var r = e.getAsJsonObject();
            assertEquals("randomizedPlugSetHash", r.get("plugSetField").getAsString());
            assertEquals(4241085061L, r.get("socketCategoryHash").getAsLong());
            assertFalse(r.get("isFakePlugSet").getAsBoolean());
            for (var match : r.getAsJsonArray("matchingEntries")) {
                var m = match.getAsJsonObject().getAsJsonObject("item");
                assertEquals(1428297954L, m.get("plugItemHash").getAsLong());
                assertTrue(m.get("currentlyCanRoll").getAsBoolean());
            }
        }
        var definitions = sockets.getAsJsonArray("perkDefinitions");
        assertEquals(2, definitions.size());
        for (var e : definitions) {
            var d = e.getAsJsonObject();
            assertEquals(d.get("hash").getAsLong() == 1428297954L, d.get("accepted").getAsBoolean());
        }
    }
    @Test void pinnedClarityMechanicsAndMasterOwnedUnknowns() throws Exception {
        assertEquals(2.0, PerpetualMotionProfile.minSpeed());
        assertEquals(40, PerpetualMotionProfile.firstStackTicks());
        assertEquals(200, PerpetualMotionProfile.secondStackTicks());
        assertEquals(10, PerpetualMotionProfile.stopGraceTicks());
        assertEquals(2, PerpetualMotionProfile.maxStacks());
        assertTrue(PerpetualMotionProfile.worksStowed());
        var source = json(ART + "clarity-source.json");
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", source.get("commit").getAsString());
        assertEquals("881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384", source.get("sourceSha256").getAsString());
        assertEquals(2014892510L, source.get("enhancedExcludedHash").getAsLong());
        String text = source.getAsJsonObject("base").toString();
        for (var fragment : List.of("minimum of 2 meters per second", "after 2 seconds and a second Stack after 10 seconds",
            "Each Stack provides 10 Stability, 10 Handling, and 10 Reload Speed", "below 2 m/s for 0.5 seconds", "Works and can activate while stowed"))
            assertTrue(text.contains(fragment), fragment);
        var policies = json(RESOURCE).getAsJsonObject("policies");
        for (var key : List.of("sourceMovementSampling", "sourceDiscontinuities", "sourceBriefPauseProgress", "sourceCombinedPerks"))
            assertEquals("UNKNOWN_MASTER_OWNED_LOCAL_POLICY", policies.get(key).getAsString());
        assertEquals(100, policies.get("statCap").getAsInt());
        assertEquals(1.0, policies.get("durationMultiplier").getAsDouble());
    }
    @Test void allFourExactTimingContracts() {
        assertEquals(new PerpetualMotionProfile.Timing("aishas_embrace", 1, 42, 9, 9, 8, 10, 10, 10), PerpetualMotionProfile.timing(entry("aishas_embrace"), 1));
        assertEquals(new PerpetualMotionProfile.Timing("aishas_embrace", 2, 39, 9, 8, 7, 20, 20, 20), PerpetualMotionProfile.timing(entry("aishas_embrace"), 2));
        assertEquals(new PerpetualMotionProfile.Timing("retraced_path", 1, 39, 8, 7, 6, 10, 10, 10), PerpetualMotionProfile.timing(entry("retraced_path"), 1));
        assertEquals(new PerpetualMotionProfile.Timing("retraced_path", 2, 38, 7, 7, 6, 20, 20, 20), PerpetualMotionProfile.timing(entry("retraced_path"), 2));
    }
    @Test void independentPinnedCurveMathReproducesBaseAndModifiedEvidence() throws Exception {
        var formulas = json("art/weapons/w46/weapon_formulas.json");
        int plans = 0;
        for (var e : json(ART + "timings.json").getAsJsonArray("entries")) {
            var r = e.getAsJsonObject();
            String id = r.get("id").getAsString();
            var category = formulas.getAsJsonObject(r.get("family").getAsString()).getAsJsonObject("cat").getAsJsonObject(r.get("category").getAsString());
            var curves = r.getAsJsonObject("curves");
            assertEquals(category.getAsJsonObject("reload"), curves.getAsJsonObject("reload"));
            for (var field : List.of("ready", "stow", "ads"))
                assertEquals(category.getAsJsonObject("handling").get(field), curves.get(field));
            int reload = r.get("baseReloadStat").getAsInt(), handling = r.get("baseHandlingStat").getAsInt();
            int[] expectedBase = id.equals("aishas_embrace") ? new int[]{46,10,10,8} : new int[]{42,8,8,7};
            int index = 0;
            for (var field : List.of("reload", "ready", "stow", "ads"))
                assertEquals(expectedBase[index++], r.getAsJsonObject("baseline").get(field + "Ticks").getAsInt());
            for (var m : r.getAsJsonArray("modified")) {
                var modified = m.getAsJsonObject();
                int stacks = modified.get("stacks").getAsInt();
                var plan = PerpetualMotionProfile.timing(entry(id), stacks);
                var actual = Map.of("reload", plan.reloadTicks(), "ready", plan.readyTicks(), "stow", plan.stowTicks(), "ads", plan.adsTicks());
                for (var field : List.of("reload", "ready", "stow", "ads")) {
                    var c = curves.getAsJsonObject(field);
                    int stat = Math.min(100, (field.equals("reload") ? reload : handling) + 10 * stacks);
                    double seconds = solve(c, stat);
                    if (field.equals("stow")) seconds = Math.max(seconds, solve(c, 100));
                    assertEquals(seconds, modified.getAsJsonObject("seconds").get(field).getAsDouble(), 1e-14);
                    int ticks = (int) Math.ceil(seconds * 20);
                    if (field.equals("ads")) ticks = Math.clamp(ticks, 2, 20);
                    assertEquals(ticks, actual.get(field));
                }
                assertEquals(Math.min(100, r.get("baseStabilityStat").getAsInt() + stacks * 10), modified.get("effectiveStabilityStat").getAsInt());
                plans++;
            }
        }
        assertEquals(4, plans);
        // Rounding and curve evaluation must not be replaced by a percent reduction of base ticks.
        assertNotEquals((int) Math.ceil(46 * .8), PerpetualMotionProfile.timing(entry("aishas_embrace"), 2).reloadTicks());
    }
    @Test void safeClampsFiniteDurationsAndSingleCeil() {
        assertEquals(100, PerpetualMotionProfile.effectiveStat(Integer.MAX_VALUE, 2));
        assertEquals(0, PerpetualMotionProfile.effectiveStat(Integer.MIN_VALUE, 2));
        assertEquals(100, PerpetualMotionProfile.effectiveStat(95, 1));
        assertEquals(2, PerpetualMotionProfile.durationTicks(.001, true));
        assertEquals(20, PerpetualMotionProfile.durationTicks(2, true));
        assertEquals(1, PerpetualMotionProfile.durationTicks(.001, false));
        assertEquals(21, PerpetualMotionProfile.durationTicks(1.0001, false));
        for (double value : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY, 0, -.1, 61})
            assertThrows(IllegalStateException.class, () -> PerpetualMotionProfile.durationTicks(value, false));
    }
    @Test void invalidCountsUnsupportedAndForgedEntriesFailClosed() {
        var a = entry("aishas_embrace");
        for (int count : new int[]{-1,0,3,Integer.MAX_VALUE})
            assertThrows(IllegalArgumentException.class, () -> PerpetualMotionProfile.timing(a, count));
        assertThrows(IllegalArgumentException.class, () -> PerpetualMotionProfile.timing(null, 1));
        for (var w : WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id()) && !WeaponExotics.expanded(legacy)).toList()) if (!Set.of("aishas_embrace", "retraced_path").contains(w.id()))
            assertThrows(IllegalArgumentException.class, () -> PerpetualMotionProfile.timing(w, 1), w.id());
        var forged = new WeaponCatalog.Entry(a.id(), "shotgun", a.frame(), a.name(), a.source_frame_label(), a.item_model());
        assertThrows(IllegalArgumentException.class, () -> PerpetualMotionProfile.timing(forged, 1));
    }
    private static void rejects(Consumer<JsonObject> mutation) throws Exception {
        var root = json(RESOURCE);
        mutation.accept(root);
        assertThrows(IllegalStateException.class, () -> PerpetualMotionProfile.validateResource(root.toString()));
    }
    @Test void mutatedEligibilityAndMechanicsRejected() throws Exception {
        rejects(r -> r.getAsJsonArray("weapons").remove(0));
        rejects(r -> r.getAsJsonArray("weapons").set(1, r.getAsJsonArray("weapons").get(0).deepCopy()));
        for (var field : List.of("hash", "socket", "plugSetHash"))
            rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(field, 1));
        rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("perkHash", 2014892510L));
        for (var field : List.of("minSpeed", "firstStackTicks", "secondStackTicks", "stopGraceTicks", "maxStacks"))
            rejects(r -> r.getAsJsonObject("perk").addProperty(field, 1));
        rejects(r -> r.getAsJsonObject("perk").addProperty("worksStowed", false));
        rejects(r -> r.getAsJsonObject("policies").addProperty("durationMultiplier", .9));
        rejects(r -> r.getAsJsonObject("policies").addProperty("sourceBriefPauseProgress", "INVENTED"));
    }
    @Test void mutatedFourTimingsBonusesAndCoefficientsRejected() throws Exception {
        rejects(r -> r.getAsJsonArray("timings").remove(0));
        rejects(r -> r.getAsJsonArray("timings").set(1, r.getAsJsonArray("timings").get(0).deepCopy()));
        for (int i = 0; i < 4; i++) {
            int row = i;
            for (var field : List.of("reloadTicks", "readyTicks", "stowTicks", "adsTicks", "stabilityBonus", "handlingBonus", "reloadBonus"))
                rejects(r -> r.getAsJsonArray("timings").get(row).getAsJsonObject().addProperty(field, 1));
        }
        for (var field : List.of("reload", "ready", "stow", "ads"))
            rejects(r -> r.getAsJsonArray("curves").get(0).getAsJsonObject().getAsJsonObject(field).addProperty("offset", .1));
        rejects(r -> r.getAsJsonArray("curves").get(0).getAsJsonObject().getAsJsonObject("reload").addProperty("offset", "NaN"));
        rejects(r -> r.getAsJsonArray("curves").get(0).getAsJsonObject().addProperty("baseHandlingStat", 100));
    }
    @Test void allConsumedPinsAndGeneratedHashesMatch() throws Exception {
        var manifest = json(ART + "manifest.json");
        for (var e : manifest.getAsJsonObject("sourcePins").entrySet()) {
            var pin = e.getValue().getAsJsonObject();
            var verified = PinnedProfileSourcesW234.verify(pin);
            assertEquals(pin.get("sha256").getAsString(), verified.sha256(), e.getKey());
            assertEquals(pin.get("bytes").getAsLong(), verified.bytes(), e.getKey());
        }
        assertEquals(manifest.get("generatorSha256").getAsString(), sha(Path.of(manifest.get("generator").getAsString())));
        for (var e : manifest.getAsJsonObject("outputSha256").entrySet())
            assertEquals(e.getValue().getAsString(), sha(Path.of(e.getKey())), e.getKey());
    }
    @Test void freshProfileInitializationAndJsonValidationNeverLoadSelectedRegistries() throws Exception {
        String prefix = "kim.biryeong.destiny.weapon.";
        var forbidden = Set.of(prefix + "WeaponCatalog", prefix + "WeaponCharacteristics", prefix + "WeaponTiming",
            prefix + "WeaponExotics", prefix + "WeaponPerks");
        var isolated = new ClassLoader(getClass().getClassLoader()) {
            @Override protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
                if (forbidden.contains(name)) throw new AssertionError("Recursive registry load: " + name);
                if (!name.startsWith(prefix + "PerpetualMotionProfile")) return super.loadClass(name, resolve);
                synchronized (getClassLoadingLock(name)) {
                    var type = findLoadedClass(name);
                    if (type == null) {
                        try (var in = getParent().getResourceAsStream(name.replace('.', '/') + ".class")) {
                            assertNotNull(in);
                            byte[] bytes = in.readAllBytes();
                            type = defineClass(name, bytes, 0, bytes.length);
                        } catch (java.io.IOException e) { throw new ClassNotFoundException(name, e); }
                    }
                    if (resolve) resolveClass(type);
                    return type;
                }
            }
        };
        var type = Class.forName(prefix + "PerpetualMotionProfile", true, isolated);
        assertEquals(40, type.getMethod("firstStackTicks").invoke(null));
        assertEquals(2, ((List<?>) type.getMethod("rolls").invoke(null)).size());
        var validate = type.getDeclaredMethod("validateResource", String.class);
        validate.setAccessible(true);
        validate.invoke(null, Files.readString(Path.of(RESOURCE)));
    }
}
