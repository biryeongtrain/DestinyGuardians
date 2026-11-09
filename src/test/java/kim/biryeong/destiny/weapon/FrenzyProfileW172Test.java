package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;
import java.util.stream.Collectors;
import static org.junit.jupiter.api.Assertions.*;

/** Standalone source/API/math regression. Native combat and combined-perk behavior are master-owned. */
class FrenzyProfileW172Test {
    /** Historical source assertions remain frozen; new identities require exact official tuples. */
    private static java.util.List<WeaponPerks.Roll> legacyRolls() {
        var all = FrenzyProfile.rolls();
        var added = all.stream().filter(r -> LegendaryWeapons.contains(r.id())).toList();
        assertEquals(java.util.Set.of("apex_predator", "forbearance", "igneous_hammer", "insidious", "palmyra_b", "phyllotactic_spiral", "rufuss_fury", "submission"), added.stream().map(WeaponPerks.Roll::id)
            .collect(java.util.stream.Collectors.toSet()));
        for (var roll : added) assertTrue(LegendaryWeapons.exactRoll(roll), roll.toString());
        assertEquals(all.size(), new java.util.HashSet<>(all).size());
        return all.stream().filter(r -> !LegendaryWeapons.contains(r.id())).toList();
    }

    private static final String ART = "art/weapons/w172/frenzy/";
    private static final String RESOURCE = "src/main/resources/destiny/weapons/w172-frenzy.json";
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
    @Test void exactTenBaseRollsAndFull65RandomizedScan() throws Exception {
        assertEquals("frenzy", FrenzyProfile.ID);
        assertEquals(4104185692L, FrenzyProfile.HASH);
        var rolls = legacyRolls();
        assertEquals(Set.of(
            new WeaponPerks.Roll("austringer", 3055790362L, 4, 4104185692L, 785215120L),
            new WeaponPerks.Roll("allied_demand", 1532276803L, 4, 4104185692L, 703779397L),
            new WeaponPerks.Roll("farewell", 541188001L, 4, 4104185692L, 3819615926L),
            new WeaponPerks.Roll("brass_attacks", 2121785039L, 4, 4104185692L, 3403850295L),
            new WeaponPerks.Roll("dream_breaker", 2931957300L, 4, 4104185692L, 1206254527L),
            new WeaponPerks.Roll("stormchaser", 3652506829L, 4, 4104185692L, 4213354588L),
            new WeaponPerks.Roll("retraced_path", 548958835L, 4, 4104185692L, 398391969L),
            new WeaponPerks.Roll("code_duello", 2496242052L, 4, 4104185692L, 147528717L),
            new WeaponPerks.Roll("retrofit_escapade", 3103325054L, 4, 4104185692L, 2461260598L),
            new WeaponPerks.Roll("nezarec_s_whisper", 254636484L, 4, 4104185692L, 699056095L)), Set.copyOf(rolls));
        assertThrows(UnsupportedOperationException.class, rolls::clear);
        var sockets = json(ART + "official-sockets.json");
        assertEquals(65, sockets.get("selectedCount").getAsInt());
        assertEquals(10, sockets.get("supportedCount").getAsInt());
        assertEquals(10, sockets.get("randomizedCount").getAsInt());
        assertEquals(0, sockets.get("fixedCuratedCount").getAsInt());
        assertEquals(55, sockets.getAsJsonArray("unsupportedSelectedIds").size());
        var scans = sockets.getAsJsonArray("selectedScan");
        assertEquals(65, scans.size());
        assertEquals(WeaponCatalog.all().stream().filter(w -> !LegendaryWeapons.contains(w.id())).map(WeaponCatalog.Entry::id).collect(Collectors.toSet()),
            scans.asList().stream().map(e -> e.getAsJsonObject().get("id").getAsString()).collect(Collectors.toSet()));
        for (var e : sockets.getAsJsonArray("weapons")) {
            var row = e.getAsJsonObject();
            assertEquals("randomizedPlugSetHash", row.get("plugSetField").getAsString());
            assertEquals(4241085061L, row.get("socketCategoryHash").getAsLong());
            assertFalse(row.get("isFakePlugSet").getAsBoolean());
            for (var match : row.getAsJsonArray("matchingEntries")) {
                var m = match.getAsJsonObject().getAsJsonObject("item");
                assertEquals(4104185692L, m.get("plugItemHash").getAsLong());
                assertTrue(m.get("currentlyCanRoll").getAsBoolean());
            }
        }
        var definitions = sockets.getAsJsonArray("perkDefinitions");
        assertEquals(Set.of(4104185692L, 3007133316L), definitions.asList().stream()
            .map(e -> e.getAsJsonObject().get("hash").getAsLong()).collect(Collectors.toSet()));
        for (var e : definitions) {
            var d = e.getAsJsonObject();
            assertEquals(d.get("hash").getAsLong() == 4104185692L, d.get("accepted").getAsBoolean());
        }
    }
    @Test void pinnedClarityCombatDurationRefreshAndExcludedDamage() throws Exception {
        assertEquals(240, FrenzyProfile.activationTicks());
        assertEquals(100, FrenzyProfile.combatGraceTicks());
        assertEquals(144, FrenzyProfile.durationTicks());
        assertEquals(1.15f, FrenzyProfile.multiplier());
        assertEquals(100, FrenzyProfile.handlingBonus());
        assertEquals(100, FrenzyProfile.reloadBonus());
        assertTrue(FrenzyProfile.worksStowed());
        assertTrue(FrenzyProfile.perk().refreshOnDealtDamage());
        assertTrue(FrenzyProfile.perk().refreshOnReceivedDamage());
        assertFalse(FrenzyProfile.perk().selfDamageCounts());
        assertFalse(FrenzyProfile.perk().environmentalDamageCounts());
        var source = json(ART + "clarity-source.json");
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", source.get("commit").getAsString());
        assertEquals("881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384", source.get("sourceSha256").getAsString());
        assertEquals(3007133316L, source.get("enhancedExcludedHash").getAsLong());
        String text = source.getAsJsonObject("base").toString();
        for (var fragment : List.of("After being in Combat for 12 seconds:",
            "15% increased damage, 100 Handling, and 100 Reload Speed for 7.2 seconds.",
            "Works and can activate while stowed. Dealing and receiving damage refreshes the buff duration.",
            "having either dealt or received damage within the last 5 seconds.",
            "Self-damage and environmental damage do not count.")) assertTrue(text.contains(fragment), fragment);
    }
    @Test void tenExactActiveTimingContracts() {
        assertEquals(new FrenzyProfile.Timing("austringer", 37, 4, 5, 4), FrenzyProfile.timing(entry("austringer")));
        assertEquals(new FrenzyProfile.Timing("allied_demand", 23, 4, 5, 3), FrenzyProfile.timing(entry("allied_demand")));
        assertEquals(new FrenzyProfile.Timing("farewell", 23, 4, 5, 3), FrenzyProfile.timing(entry("farewell")));
        assertEquals(new FrenzyProfile.Timing("brass_attacks", 23, 4, 5, 3), FrenzyProfile.timing(entry("brass_attacks")));
        assertEquals(new FrenzyProfile.Timing("dream_breaker", 30, 8, 4, 5), FrenzyProfile.timing(entry("dream_breaker")));
        assertEquals(new FrenzyProfile.Timing("stormchaser", 30, 8, 4, 5), FrenzyProfile.timing(entry("stormchaser")));
        assertEquals(new FrenzyProfile.Timing("retraced_path", 32, 5, 5, 5), FrenzyProfile.timing(entry("retraced_path")));
        assertEquals(new FrenzyProfile.Timing("code_duello", 53, 6, 5, 7), FrenzyProfile.timing(entry("code_duello")));
        assertEquals(new FrenzyProfile.Timing("retrofit_escapade", 80, 6, 6, 7), FrenzyProfile.timing(entry("retrofit_escapade")));
        assertEquals(new FrenzyProfile.Timing("nezarec_s_whisper", 35, 5, 5, 2), FrenzyProfile.timing(entry("nezarec_s_whisper")));
    }
    @Test void independentPinnedCurveMathReproducesAll80BaseAndActiveTimes() throws Exception {
        var formulas = json("art/weapons/w46/weapon_formulas.json");
        int count = 0;
        for (var e : json(ART + "timings.json").getAsJsonArray("entries")) {
            var row = e.getAsJsonObject();
            String id = row.get("id").getAsString();
            var category = formulas.getAsJsonObject(row.get("family").getAsString()).getAsJsonObject("cat").getAsJsonObject(row.get("category").getAsString());
            var curves = row.getAsJsonObject("curves");
            assertEquals(category.getAsJsonObject("reload"), curves.getAsJsonObject("reload"));
            for (var field : List.of("ready", "stow", "ads")) assertEquals(category.getAsJsonObject("handling").get(field), curves.get(field));
            for (boolean active : new boolean[]{false, true}) {
                var result = row.getAsJsonObject(active ? "modified" : "baseline");
                for (var field : List.of("reload", "ready", "stow", "ads")) {
                    int base = row.get(field.equals("reload") ? "baseReloadStat" : "baseHandlingStat").getAsInt();
                    int stat = Math.min(100, base + (active ? 100 : 0));
                    double seconds = solve(curves.getAsJsonObject(field), stat);
                    if (field.equals("stow")) seconds = Math.max(seconds, solve(curves.getAsJsonObject(field), 100));
                    assertEquals(seconds, result.getAsJsonObject("seconds").get(field).getAsDouble(), 1e-14);
                    int ticks = (int) Math.ceil(seconds * 20);
                    if (field.equals("ads")) ticks = Math.clamp(ticks, 2, 20);
                    assertEquals(ticks, result.get(field + "Ticks").getAsInt(), id + field);
                    if (active) {
                        var p = FrenzyProfile.timing(entry(id));
                        assertEquals(Map.of("reload", p.reloadTicks(), "ready", p.readyTicks(), "stow", p.stowTicks(), "ads", p.adsTicks()).get(field), ticks);
                    }
                    count++;
                }
            }
            assertEquals(100, row.getAsJsonObject("modified").get("effectiveReloadStat").getAsInt());
            assertEquals(100, row.getAsJsonObject("modified").get("effectiveHandlingStat").getAsInt());
            assertFalse(row.getAsJsonObject("modified").get("shellReload").getAsBoolean());
            assertTrue(row.getAsJsonObject("modified").get("reloadInitialTicks").isJsonNull());
            assertTrue(row.getAsJsonObject("modified").get("reloadPerRoundTicks").isJsonNull());
        }
        assertEquals(80, count);
        // Bonus is physical stat+100, not a duration multiplier or reduction of rounded base ticks.
        assertNotEquals((int) Math.ceil(53 / 1.15), FrenzyProfile.timing(entry("austringer")).reloadTicks());
    }
    @Test void glaiveRetainedWithExplicitUnsupportedAdsEvidence() throws Exception {
        var entries = json(ART + "timings.json").getAsJsonArray("entries");
        var glaive = entries.asList().stream().map(JsonElement::getAsJsonObject)
            .filter(e -> e.get("id").getAsString().equals("nezarec_s_whisper")).findFirst().orElseThrow();
        assertFalse(glaive.getAsJsonObject("modified").get("adsSupported").getAsBoolean());
        assertEquals(1, glaive.getAsJsonArray("unsupportedEvidence").size());
        assertEquals(0.0, glaive.getAsJsonObject("modified").getAsJsonObject("seconds").get("ads").getAsDouble());
        assertEquals(2, FrenzyProfile.timing(entry("nezarec_s_whisper")).adsTicks());
        assertTrue(FrenzyProfile.supports(entry("nezarec_s_whisper")));
    }
    @Test void snapshotDistinctSocketIntersectionScalesSecondsBeforeQuantizing() throws Exception {
        var pairs = json(RESOURCE).getAsJsonArray("snapshotADS");
        assertEquals(2, pairs.size());
        assertEquals(Set.of("austringer", "dream_breaker"), pairs.asList().stream()
            .map(e -> e.getAsJsonObject().get("id").getAsString()).collect(Collectors.toSet()));
        var official = json(ART + "official-sockets.json").getAsJsonArray("snapshotIntersection");
        assertEquals(2, official.size());
        for (var e : official) {
            var pair = e.getAsJsonObject();
            assertEquals(4, pair.get("frenzySocket").getAsInt());
            assertEquals(3, pair.get("socket").getAsInt());
            assertEquals(957782887L, pair.get("perkHash").getAsLong());
            assertFalse(pair.get("isFakePlugSet").getAsBoolean());
            assertEquals("randomizedPlugSetHash", pair.get("plugSetField").getAsString());
            assertTrue(pair.getAsJsonObject("matchingEntry").getAsJsonObject("item").get("currentlyCanRoll").getAsBoolean());
        }
        assertEquals(2, FrenzyProfile.adsTicks(entry("austringer"), true));
        assertEquals(4, FrenzyProfile.adsTicks(entry("dream_breaker"), true));
        for (var roll : legacyRolls()) {
            var w = entry(roll.id());
            assertEquals(FrenzyProfile.timing(w).adsTicks(), FrenzyProfile.adsTicks(w, false));
            if (!Set.of("austringer", "dream_breaker").contains(w.id()))
                assertThrows(IllegalArgumentException.class, () -> FrenzyProfile.adsTicks(w, true));
        }
        for (var e : pairs) {
            var pair = e.getAsJsonObject();
            double seconds = pair.get("adsSeconds").getAsDouble(), scalar = pair.get("scalar").getAsDouble();
            assertEquals(Math.clamp((int) Math.ceil(seconds * scalar * 20), 1, 20),
                FrenzyProfile.adsTicks(entry(pair.get("id").getAsString()), true));
        }
        // This synthetic boundary distinguishes order even where selected pairs happen to round equally.
        assertEquals(3, FrenzyProfile.snapshotDurationTicks(.16, .8));
        assertEquals(4, (int) Math.ceil(Math.ceil(.16 * 20) * .8));
        assertEquals(1, FrenzyProfile.snapshotDurationTicks(.001, .5));
        assertThrows(IllegalStateException.class, () -> FrenzyProfile.snapshotDurationTicks(.2, 1.0));
        assertThrows(IllegalStateException.class, () -> FrenzyProfile.snapshotDurationTicks(Double.NaN, .5));
        assertThrows(IllegalArgumentException.class, () -> FrenzyProfile.adsTicks(null, true));
    }
    @Test void reloadDurationScalarAppliesToRawStat100SecondsBeforeOneCeil() throws Exception {
        var resource = json(RESOURCE);
        for (var roll : legacyRolls()) {
            var w = entry(roll.id());
            assertEquals(FrenzyProfile.timing(w).reloadTicks(), FrenzyProfile.reloadTicks(w, 1.0));
            var curve = resource.getAsJsonArray("curves").asList().stream().map(JsonElement::getAsJsonObject)
                .filter(e -> e.get("id").getAsString().equals(w.id())).findFirst().orElseThrow();
            double seconds = solve(curve.getAsJsonObject("reload"), 100);
            for (double scalar : new double[]{.9, .8, .5, .9 * .8, Double.MIN_VALUE})
                assertEquals((int) Math.ceil(seconds * scalar * 20), FrenzyProfile.reloadTicks(w, scalar), w.id());
        }
        var a = entry("austringer");
        assertEquals(37, FrenzyProfile.reloadTicks(a, 1.0));
        assertEquals(33, FrenzyProfile.reloadTicks(a, .9));
        assertEquals(34, (int) Math.ceil(FrenzyProfile.timing(a).reloadTicks() * .9));
    }
    @Test void reloadDurationScalarRejectsInvalidAndUnsupportedInputs() {
        var a = entry("austringer");
        for (double scalar : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY, 0, -.1, 1.00001})
            assertThrows(IllegalArgumentException.class, () -> FrenzyProfile.reloadTicks(a, scalar));
        assertThrows(IllegalArgumentException.class, () -> FrenzyProfile.reloadTicks(null, .9));
        assertThrows(IllegalArgumentException.class, () -> FrenzyProfile.reloadTicks(entry("ace_of_spades"), .9));
        var forged = new WeaponCatalog.Entry(a.id(), "shotgun", a.frame(), a.name(), a.source_frame_label(), a.item_model());
        assertThrows(IllegalArgumentException.class, () -> FrenzyProfile.reloadTicks(forged, .9));
    }
    @Test void activeStat100ThenPrimaryHalfGivesAustringer2VersusNormal4() throws Exception {
        var a = entry("austringer");
        var c = json(RESOURCE).getAsJsonArray("curves").asList().stream().map(JsonElement::getAsJsonObject)
            .filter(e -> e.get("id").getAsString().equals("austringer")).findFirst().orElseThrow();
        assertEquals(100, FrenzyProfile.effectiveStat(c.get("baseHandlingStat").getAsInt()));
        assertEquals(.165, solve(c.getAsJsonObject("ads"), 100));
        assertEquals(4, FrenzyProfile.adsTicks(a, false));
        assertEquals(2, FrenzyProfile.adsTicks(a, true));
        // Entry-only Snapshot is a consumer choice; the normal active/exit timing remains four ticks.
        assertEquals(4, FrenzyProfile.timing(a).adsTicks());
    }
    @Test void mutatedSnapshotSocketSecondsScalarAndMembershipRejected() throws Exception {
        rejects(r -> r.getAsJsonArray("snapshotADS").remove(0));
        rejects(r -> r.getAsJsonArray("snapshotADS").set(1, r.getAsJsonArray("snapshotADS").get(0).deepCopy()));
        for (var field : List.of("frenzySocket", "snapshotSocket", "snapshotPlugSetHash", "perkHash", "ammoType", "scalar", "adsSeconds", "adsTicks"))
            rejects(r -> r.getAsJsonArray("snapshotADS").get(0).getAsJsonObject().addProperty(field, 999));
        rejects(r -> r.getAsJsonArray("snapshotADS").get(1).getAsJsonObject().addProperty("scalar", .75));
        rejects(r -> r.getAsJsonArray("snapshotADS").get(0).getAsJsonObject().addProperty("id", "farewell"));
    }
    @Test void safeStatClampsFiniteDurationsAndSingleCeil() {
        assertEquals(100, FrenzyProfile.effectiveStat(Integer.MAX_VALUE));
        assertEquals(0, FrenzyProfile.effectiveStat(Integer.MIN_VALUE));
        assertEquals(100, FrenzyProfile.effectiveStat(0));
        assertEquals(2, FrenzyProfile.durationTicks(.001, true));
        assertEquals(20, FrenzyProfile.durationTicks(2, true));
        assertEquals(1, FrenzyProfile.durationTicks(.001, false));
        assertEquals(21, FrenzyProfile.durationTicks(1.0001, false));
        for (double v : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY, 0, -.1, 61})
            assertThrows(IllegalStateException.class, () -> FrenzyProfile.durationTicks(v, false));
    }
    @Test void unsupportedAndEveryForgedCatalogFieldFailClosed() {
        assertFalse(FrenzyProfile.supports(null));
        assertThrows(IllegalArgumentException.class, () -> FrenzyProfile.timing(null));
        var ids = FrenzyProfile.rolls().stream().map(WeaponPerks.Roll::id).collect(Collectors.toSet());
        for (var w : WeaponCatalog.all()) {
            assertEquals(ids.contains(w.id()), FrenzyProfile.supports(w), w.id());
            if (!ids.contains(w.id())) assertThrows(IllegalArgumentException.class, () -> FrenzyProfile.timing(w), w.id());
        }
        var a = entry("austringer");
        assertFalse(FrenzyProfile.supports(new WeaponCatalog.Entry(null, a.family(), a.frame(), a.name(), a.source_frame_label(), a.item_model())));
        String[] fields = {a.id(), a.family(), a.frame(), a.name(), a.source_frame_label(), a.item_model()};
        for (int i = 0; i < fields.length; i++) {
            var copy = fields.clone(); copy[i] = "FORGED";
            var forged = new WeaponCatalog.Entry(copy[0], copy[1], copy[2], copy[3], copy[4], copy[5]);
            assertFalse(FrenzyProfile.supports(forged));
            assertThrows(IllegalArgumentException.class, () -> FrenzyProfile.timing(forged));
        }
    }
    private static void rejects(Consumer<JsonObject> mutation) throws Exception {
        var root = json(RESOURCE); mutation.accept(root);
        assertThrows(IllegalStateException.class, () -> FrenzyProfile.validateResource(root.toString()));
    }
    @Test void malformedAndMutatedMechanicsMembershipAndTopologyRejected() throws Exception {
        assertThrows(IllegalStateException.class, () -> FrenzyProfile.validateResource("null"));
        assertThrows(IllegalStateException.class, () -> FrenzyProfile.validateResource("{"));
        rejects(r -> r.getAsJsonArray("weapons").remove(0));
        rejects(r -> r.getAsJsonArray("weapons").set(1, r.getAsJsonArray("weapons").get(0).deepCopy()));
        for (var field : List.of("hash", "socket", "plugSetHash", "perkHash"))
            rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(field, 1));
        for (var field : List.of("activationTicks", "combatGraceTicks", "durationTicks", "damageMultiplier", "handlingBonus", "reloadBonus"))
            rejects(r -> r.getAsJsonObject("perk").addProperty(field, 1));
        for (var field : List.of("worksStowed", "refreshOnDealtDamage", "refreshOnReceivedDamage"))
            rejects(r -> r.getAsJsonObject("perk").addProperty(field, false));
        for (var field : List.of("selfDamageCounts", "environmentalDamageCounts"))
            rejects(r -> r.getAsJsonObject("perk").addProperty(field, true));
        rejects(r -> r.getAsJsonObject("policies").addProperty("durationMultiplier", .9));
        rejects(r -> r.getAsJsonArray("timings").remove(0));
        rejects(r -> r.getAsJsonArray("timings").set(1, r.getAsJsonArray("timings").get(0).deepCopy()));
        for (int i = 0; i < 10; i++) {
            int row = i;
            for (var field : List.of("reloadTicks", "readyTicks", "stowTicks", "adsTicks", "reloadPerRoundTicks", "reloadInitialTicks"))
                rejects(r -> r.getAsJsonArray("timings").get(row).getAsJsonObject().addProperty(field, 1));
            rejects(r -> r.getAsJsonArray("timings").get(row).getAsJsonObject().addProperty("shellReload", true));
            rejects(r -> r.getAsJsonArray("curves").get(row).getAsJsonObject().addProperty("baseHandlingStat", 100));
        }
        for (var field : List.of("reload", "ready", "stow", "ads"))
            rejects(r -> r.getAsJsonArray("curves").get(0).getAsJsonObject().getAsJsonObject(field).addProperty("offset", .1));
        rejects(r -> r.getAsJsonArray("curves").get(0).getAsJsonObject().getAsJsonObject("reload").addProperty("offset", "NaN"));
        rejects(r -> r.getAsJsonArray("timings").get(9).getAsJsonObject().addProperty("adsSupported", true));
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
    @Test void freshProfileInitializationAndValidationNeverLoadOuterRegistries() throws Exception {
        String prefix = "kim.biryeong.destiny.weapon.";
        var forbidden = Set.of(prefix + "WeaponCatalog", prefix + "WeaponCharacteristics", prefix + "WeaponTiming",
            prefix + "WeaponExotics", prefix + "WeaponPerks", prefix + "SnapshotAimProfile");
        var isolated = new ClassLoader(getClass().getClassLoader()) {
            @Override protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
                if (forbidden.contains(name)) throw new AssertionError("Recursive registry load: " + name);
                if (!name.startsWith(prefix + "FrenzyProfile")) return super.loadClass(name, resolve);
                synchronized (getClassLoadingLock(name)) {
                    var type = findLoadedClass(name);
                    if (type == null) {
                        try (var in = getParent().getResourceAsStream(name.replace('.', '/') + ".class")) {
                            assertNotNull(in); byte[] bytes = in.readAllBytes();
                            type = defineClass(name, bytes, 0, bytes.length);
                        } catch (java.io.IOException e) { throw new ClassNotFoundException(name, e); }
                    }
                    if (resolve) resolveClass(type);
                    return type;
                }
            }
        };
        var type = Class.forName(prefix + "FrenzyProfile", true, isolated);
        assertEquals(240, type.getMethod("activationTicks").invoke(null));
        assertEquals(10 + LegendaryPerks.extraRolls("frenzy").size(), ((List<?>) type.getMethod("rolls").invoke(null)).size());
        var validate = type.getDeclaredMethod("validateResource", String.class);
        validate.setAccessible(true);
        validate.invoke(null, Files.readString(Path.of(RESOURCE)));
    }
}
