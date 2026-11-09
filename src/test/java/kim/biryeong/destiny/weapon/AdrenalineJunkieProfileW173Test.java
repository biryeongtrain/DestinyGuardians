package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;
import java.util.stream.Collectors;
import static org.junit.jupiter.api.Assertions.*;

/** Standalone source/API/math regressions; runtime kill attribution and native QA are master-owned. */
class AdrenalineJunkieProfileW173Test {
    private static final String ART = "art/weapons/w173/adrenaline-junkie/";
    private static final String RESOURCE = "src/main/resources/destiny/weapons/w173-adrenaline-junkie.json";
    private static final Set<String> IDS = Set.of("ammit_ar2", "long_arm", "farewell", "goldtusk", "nezarec_s_whisper");
    private static JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static String sha(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }
    private static double solve(JsonObject c, int stat) {
        return (c.has("evpp") ? c.get("evpp").getAsDouble() : 0) * stat * stat
            + c.get("vpp").getAsDouble() * stat + c.get("offset").getAsDouble();
    }
    private static void rejects(Consumer<JsonObject> mutation) throws Exception {
        var root = json(RESOURCE); mutation.accept(root);
        assertThrows(IllegalStateException.class, () -> AdrenalineJunkieProfile.validateResource(root.toString()));
    }
    @Test void exactFiveBaseRollsAcrossFullSelected65OfficialScan() throws Exception {
        assertEquals("adrenaline_junkie", AdrenalineJunkieProfile.ID);
        assertEquals(11612903L, AdrenalineJunkieProfile.HASH);
        assertEquals(Set.of(
            new WeaponPerks.Roll("ammit_ar2", 2119346509L, 4, 11612903L, 560115158L),
            new WeaponPerks.Roll("long_arm", 8293111L, 4, 11612903L, 619833418L),
            new WeaponPerks.Roll("farewell", 541188001L, 4, 11612903L, 3819615926L),
            new WeaponPerks.Roll("goldtusk", 3371413057L, 4, 11612903L, 700250835L),
            new WeaponPerks.Roll("nezarec_s_whisper", 254636484L, 4, 11612903L, 699056095L)),
            Set.copyOf(AdrenalineJunkieProfile.rolls()));
        var sockets = json(ART + "official-sockets.json");
        assertEquals(65, sockets.get("selectedCount").getAsInt());
        assertEquals(5, sockets.get("supportedCount").getAsInt());
        assertEquals(5, sockets.get("randomizedCount").getAsInt());
        assertEquals(0, sockets.get("fixedCuratedCount").getAsInt());
        assertEquals(60, sockets.getAsJsonArray("unsupportedSelectedIds").size());
        var scan = sockets.getAsJsonArray("selectedScan");
        assertEquals(65, scan.size());
        assertEquals(WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id()) && !WeaponExotics.expanded(legacy)).toList().stream().map(WeaponCatalog.Entry::id).collect(Collectors.toSet()),
            scan.asList().stream().map(e -> e.getAsJsonObject().get("id").getAsString()).collect(Collectors.toSet()));
        for (var e : sockets.getAsJsonArray("weapons")) {
            var row = e.getAsJsonObject();
            assertEquals("randomizedPlugSetHash", row.get("plugSetField").getAsString());
            assertEquals(4241085061L, row.get("socketCategoryHash").getAsLong());
            assertFalse(row.get("isFakePlugSet").getAsBoolean());
            for (var m : row.getAsJsonArray("matchingEntries")) {
                var item = m.getAsJsonObject().getAsJsonObject("item");
                assertEquals(11612903L, item.get("plugItemHash").getAsLong());
                assertTrue(item.get("currentlyCanRoll").getAsBoolean());
            }
        }
        var defs = sockets.getAsJsonArray("perkDefinitions");
        assertEquals(Set.of(11612903L, 2422968039L), defs.asList().stream()
            .map(e -> e.getAsJsonObject().get("hash").getAsLong()).collect(Collectors.toSet()));
        for (var e : defs) {
            var d = e.getAsJsonObject();
            assertEquals(d.get("hash").getAsLong() == 11612903L, d.get("accepted").getAsBoolean());
        }
    }
    @Test void pinnedClarityKillStacksStowedGrenadeDurationHandlingAndDamage() throws Exception {
        assertEquals(90, AdrenalineJunkieProfile.durationTicks());
        assertEquals(20, AdrenalineJunkieProfile.handlingBonus());
        var p = AdrenalineJunkieProfile.perk();
        assertEquals(5, p.maxStacks());
        assertEquals(1, p.weaponKillStacks());
        assertEquals(5, p.grenadeKillStacks());
        assertTrue(p.grenadeKillsWorkStowed());
        var source = json(ART + "clarity-source.json");
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", source.get("commit").getAsString());
        assertEquals("881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384", source.get("sourceSha256").getAsString());
        assertEquals(2422968039L, source.get("enhancedExcludedHash").getAsLong());
        var text = source.getAsJsonObject("base").toString();
        for (var fragment : List.of("Weapon Kills grant 1 Stack of Adrenaline Junkie for 4.5 seconds.",
            "Grenade Kills grant all 5 Stacks instantly even if the weapon is stowed.", "20 Handling",
            "6.7%|13.3%|20%|26.6%|33.3% increased damage at 1|2|3|4|5 Stacks")) assertTrue(text.contains(fragment));
    }
    @Test void stackMultipliersClampSafelyAndRemainImmutable() {
        float[] values = {1, 1.067f, 1.133f, 1.2f, 1.266f, 1.333f};
        for (int n = 0; n < values.length; n++) assertEquals(values[n], AdrenalineJunkieProfile.damageMultiplier(n));
        assertEquals(1f, AdrenalineJunkieProfile.damageMultiplier(Integer.MIN_VALUE));
        assertEquals(1f, AdrenalineJunkieProfile.damageMultiplier(-1));
        assertEquals(1.333f, AdrenalineJunkieProfile.damageMultiplier(6));
        assertEquals(1.333f, AdrenalineJunkieProfile.damageMultiplier(Integer.MAX_VALUE));
        assertThrows(UnsupportedOperationException.class, AdrenalineJunkieProfile.rolls()::clear);
        assertThrows(UnsupportedOperationException.class, AdrenalineJunkieProfile.perk().damageMultipliers()::clear);
    }
    @Test void exactFourSupportedTimingContracts() {
        assertEquals(new AdrenalineJunkieProfile.Timing("ammit_ar2", true, 7, 7, 6, true), AdrenalineJunkieProfile.timing(entry("ammit_ar2")));
        assertEquals(new AdrenalineJunkieProfile.Timing("long_arm", true, 7, 7, 6, true), AdrenalineJunkieProfile.timing(entry("long_arm")));
        assertEquals(new AdrenalineJunkieProfile.Timing("farewell", true, 5, 6, 4, true), AdrenalineJunkieProfile.timing(entry("farewell")));
        assertEquals(new AdrenalineJunkieProfile.Timing("nezarec_s_whisper", true, 6, 7, 2, false), AdrenalineJunkieProfile.timing(entry("nezarec_s_whisper")));
    }
    @Test void swordDamageMembershipSurvivesExplicitUnsupportedHandlingWithoutInventedCurve() throws Exception {
        assertTrue(AdrenalineJunkieProfile.supports("goldtusk"));
        assertTrue(AdrenalineJunkieProfile.supports(entry("goldtusk")));
        assertEquals(new AdrenalineJunkieProfile.Timing("goldtusk", false, null, null, null, false), AdrenalineJunkieProfile.timing(entry("goldtusk")));
        assertThrows(UnsupportedOperationException.class, () -> AdrenalineJunkieProfile.adsTicks(entry("goldtusk"), false));
        assertEquals(1.333f, AdrenalineJunkieProfile.damageMultiplier(5));
        var sword = json(ART + "timings.json").getAsJsonArray("entries").asList().stream().map(JsonElement::getAsJsonObject)
            .filter(e -> e.get("id").getAsString().equals("goldtusk")).findFirst().orElseThrow();
        assertTrue(sword.get("curves").isJsonNull());
        assertTrue(sword.get("baseHandlingStat").isJsonNull());
        assertTrue(sword.get("baseline").isJsonNull());
        assertFalse(sword.getAsJsonObject("modified").get("supported").getAsBoolean());
        assertTrue(sword.getAsJsonArray("unsupportedEvidence").toString().contains("no Handling stat"));
    }
    @Test void independentPinnedMathReproducesAll24BaseAndActiveTimingFields() throws Exception {
        var formulas = json("art/weapons/w46/weapon_formulas.json");
        int count = 0;
        for (var e : json(ART + "timings.json").getAsJsonArray("entries")) {
            var row = e.getAsJsonObject();
            if (row.get("id").getAsString().equals("goldtusk")) continue;
            String id = row.get("id").getAsString();
            var curves = row.getAsJsonObject("curves");
            var oracle = formulas.getAsJsonObject(row.get("family").getAsString()).getAsJsonObject("cat")
                .getAsJsonObject(row.get("category").getAsString()).getAsJsonObject("handling");
            assertEquals(oracle, curves);
            for (boolean active : new boolean[]{false, true}) {
                var result = row.getAsJsonObject(active ? "modified" : "baseline");
                int base = row.get("baseHandlingStat").getAsInt();
                int stat = Math.clamp(base + (active ? 20 : 0), 0, 100);
                assertEquals(stat, result.get("effectiveHandlingStat").getAsInt());
                for (String field : List.of("ready", "stow", "ads")) {
                    var curve = curves.getAsJsonObject(field);
                    double seconds = solve(curve, stat);
                    if (field.equals("stow")) seconds = Math.max(seconds, solve(curve, 100));
                    assertEquals(seconds, result.getAsJsonObject("seconds").get(field).getAsDouble(), 1e-14);
                    int ticks = (int) Math.ceil(seconds * 20);
                    if (field.equals("ads")) ticks = Math.clamp(ticks, 2, 20);
                    assertEquals(ticks, result.get(field + "Ticks").getAsInt());
                    if (active) {
                        var t = AdrenalineJunkieProfile.timing(entry(id));
                        assertEquals(Map.of("ready", t.readyTicks(), "stow", t.stowTicks(), "ads", t.adsTicks()).get(field), ticks);
                    }
                    count++;
                }
            }
        }
        assertEquals(24, count);
        // Flat handling+20 is recomputed from seconds; damage stacks never multiply handling.
        assertEquals(66, AdrenalineJunkieProfile.effectiveStat(46));
        assertNotEquals(20, AdrenalineJunkieProfile.timing(entry("ammit_ar2")).readyTicks());
    }
    @Test void glaiveAdsIsExplicitNeutralTwoTicksWithReadyStowBenefit() throws Exception {
        var t = AdrenalineJunkieProfile.timing(entry("nezarec_s_whisper"));
        assertTrue(t.supported()); assertFalse(t.adsSupported());
        assertEquals(2, AdrenalineJunkieProfile.adsTicks(entry("nezarec_s_whisper"), false));
        assertEquals(6, t.readyTicks()); assertEquals(7, t.stowTicks());
        var c = json(RESOURCE).getAsJsonArray("curves").get(4).getAsJsonObject();
        assertTrue(c.get("neutralAds").getAsBoolean());
        assertEquals(0, solve(c.getAsJsonObject("ads"), 62));
    }
    @Test void noSelectedAjSnapshotPairIncludingFarewellAndAllTrueRequestsFailClosed() throws Exception {
        assertTrue(json(RESOURCE).getAsJsonArray("snapshotADS").isEmpty());
        assertTrue(json(ART + "official-sockets.json").getAsJsonArray("snapshotIntersection").isEmpty());
        for (var e : json("src/main/resources/destiny/weapons/w68-snapshot.json").getAsJsonArray("rolls"))
            assertFalse(IDS.contains(e.getAsJsonObject().get("id").getAsString()));
        for (String id : IDS) {
            var w = entry(id);
            assertThrows(IllegalArgumentException.class, () -> AdrenalineJunkieProfile.adsTicks(w, true), id);
            if (!id.equals("goldtusk")) assertEquals(AdrenalineJunkieProfile.timing(w).adsTicks(), AdrenalineJunkieProfile.adsTicks(w, false));
        }
        assertEquals(4, AdrenalineJunkieProfile.adsTicks(entry("farewell"), false));
    }
    @Test void snapshotMathScalesRawSecondsBeforeOneCeilAndOnlyW68Scalars() {
        assertEquals(3, AdrenalineJunkieProfile.snapshotDurationTicks(.16, .8));
        assertEquals(4, (int) Math.ceil(Math.ceil(.16 * 20) * .8));
        assertEquals(1, AdrenalineJunkieProfile.snapshotDurationTicks(.001, .5));
        assertEquals(20, AdrenalineJunkieProfile.snapshotDurationTicks(4, .5));
        for (double s : new double[]{.75, 1, 0, -.5, Double.NaN, Double.POSITIVE_INFINITY})
            assertThrows(IllegalStateException.class, () -> AdrenalineJunkieProfile.snapshotDurationTicks(.2, s));
    }
    @Test void statClampsAvoidOverflowAndDurationsRejectUnsafeValues() {
        assertEquals(100, AdrenalineJunkieProfile.effectiveStat(Integer.MAX_VALUE));
        assertEquals(0, AdrenalineJunkieProfile.effectiveStat(Integer.MIN_VALUE));
        assertEquals(20, AdrenalineJunkieProfile.effectiveStat(0));
        assertEquals(100, AdrenalineJunkieProfile.effectiveStat(90));
        assertEquals(0, AdrenalineJunkieProfile.effectiveStat(-20));
        assertEquals(1, AdrenalineJunkieProfile.durationTicks(.001, false));
        assertEquals(21, AdrenalineJunkieProfile.durationTicks(1.0001, false));
        assertEquals(2, AdrenalineJunkieProfile.durationTicks(.001, true));
        assertEquals(20, AdrenalineJunkieProfile.durationTicks(2, true));
        for (double v : new double[]{Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY, 0, -.1, 61}) {
            assertThrows(IllegalStateException.class, () -> AdrenalineJunkieProfile.durationTicks(v, false));
            assertThrows(IllegalStateException.class, () -> AdrenalineJunkieProfile.snapshotDurationTicks(v, .5));
        }
    }
    @Test void unsupportedAndEveryForgedCatalogFieldFailClosed() {
        assertFalse(AdrenalineJunkieProfile.supports((String) null));
        assertFalse(AdrenalineJunkieProfile.supports((WeaponCatalog.Entry) null));
        assertThrows(IllegalArgumentException.class, () -> AdrenalineJunkieProfile.timing(null));
        assertThrows(IllegalArgumentException.class, () -> AdrenalineJunkieProfile.adsTicks(null, true));
        for (var w : WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id()) && !WeaponExotics.expanded(legacy)).toList()) {
            assertEquals(IDS.contains(w.id()), AdrenalineJunkieProfile.supports(w));
            assertEquals(IDS.contains(w.id()), AdrenalineJunkieProfile.supports(w.id()));
            if (!IDS.contains(w.id())) assertThrows(IllegalArgumentException.class, () -> AdrenalineJunkieProfile.timing(w));
        }
        var a = entry("ammit_ar2");
        String[] fields = {a.id(), a.family(), a.frame(), a.name(), a.source_frame_label(), a.item_model()};
        for (int n = 0; n < fields.length; n++) for (String bad : new String[]{null, "FORGED"}) {
            var copy = fields.clone(); copy[n] = bad;
            var forged = new WeaponCatalog.Entry(copy[0], copy[1], copy[2], copy[3], copy[4], copy[5]);
            assertFalse(AdrenalineJunkieProfile.supports(forged));
            assertThrows(IllegalArgumentException.class, () -> AdrenalineJunkieProfile.timing(forged));
        }
    }
    @Test void mutatedMechanicsAndEveryPolicyAreRejected() throws Exception {
        for (String field : json(RESOURCE).getAsJsonObject("perk").keySet()) {
            rejects(r -> r.getAsJsonObject("perk").remove(field));
            rejects(r -> r.getAsJsonObject("perk").addProperty(field, 999));
        }
        for (String field : json(RESOURCE).getAsJsonObject("policies").keySet()) {
            rejects(r -> r.getAsJsonObject("policies").remove(field));
            rejects(r -> r.getAsJsonObject("policies").addProperty(field, "FORGED"));
        }
        rejects(r -> r.getAsJsonObject("perk").addProperty("reloadBonus", 20));
    }
    @Test void mutatedRollIdentitySocketHashPoolMissingAndDuplicatesAreRejected() throws Exception {
        for (String f : List.of("id", "hash", "socket", "perkHash", "plugSetHash")) {
            rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(f, 999));
            rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().remove(f));
        }
        rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("perkHash", 2422968039L));
        rejects(r -> r.getAsJsonArray("weapons").remove(3));
        rejects(r -> r.getAsJsonArray("weapons").set(1, r.getAsJsonArray("weapons").get(0).deepCopy()));
    }
    @Test void mutatedCurveCoefficientsStatsUnsupportedSwordAndDuplicatesAreRejected() throws Exception {
        for (int i : new int[]{0, 1, 2, 4}) {
            final int n = i;
            for (String f : List.of("baseHandlingStat", "supported", "neutralAds", "id")) {
                rejects(r -> r.getAsJsonArray("curves").get(n).getAsJsonObject().addProperty(f, 999));
                rejects(r -> r.getAsJsonArray("curves").get(n).getAsJsonObject().remove(f));
            }
            for (String f : List.of("ready", "stow", "ads")) for (String coefficient : List.of("vpp", "offset", "evpp"))
                rejects(r -> r.getAsJsonArray("curves").get(n).getAsJsonObject().getAsJsonObject(f).addProperty(coefficient, .5));
        }
        rejects(r -> r.getAsJsonArray("curves").get(3).getAsJsonObject().addProperty("supported", true));
        rejects(r -> r.getAsJsonArray("curves").get(3).getAsJsonObject().addProperty("baseHandlingStat", 50));
        rejects(r -> r.getAsJsonArray("curves").get(3).getAsJsonObject().add("ready", new JsonObject()));
        rejects(r -> r.getAsJsonArray("curves").remove(3));
        rejects(r -> r.getAsJsonArray("curves").set(1, r.getAsJsonArray("curves").get(0).deepCopy()));
    }
    @Test void mutatedTimingsFlagsMissingNullSwordFieldsAndSnapshotMembershipAreRejected() throws Exception {
        for (int i = 0; i < 5; i++) {
            final int n = i;
            for (String f : List.of("id", "supported", "readyTicks", "stowTicks", "adsTicks", "adsSupported")) {
                rejects(r -> r.getAsJsonArray("timings").get(n).getAsJsonObject().addProperty(f, 999));
                rejects(r -> r.getAsJsonArray("timings").get(n).getAsJsonObject().remove(f));
            }
        }
        rejects(r -> r.getAsJsonArray("timings").remove(3));
        rejects(r -> r.getAsJsonArray("timings").set(1, r.getAsJsonArray("timings").get(0).deepCopy()));
        rejects(r -> r.getAsJsonArray("snapshotADS").add(JsonParser.parseString("{id:farewell,scalar:0.5,adsTicks:2}")));
    }
    @Test void malformedAndMissingSectionsAreRejected() throws Exception {
        AdrenalineJunkieProfile.validateResource(Files.readString(Path.of(RESOURCE)));
        for (String f : json(RESOURCE).keySet()) {
            rejects(r -> r.remove(f));
            rejects(r -> r.add(f, JsonNull.INSTANCE));
        }
        rejects(r -> r.addProperty("stage", "W172"));
        rejects(r -> r.addProperty("reloadBonus", 20));
        for (String text : List.of("null", "[]", "{", "{}"))
            assertThrows(IllegalStateException.class, () -> AdrenalineJunkieProfile.validateResource(text));
    }
    @Test void noReloadBonusCurveOrTimingOverrideIsIntroduced() throws Exception {
        var r = json(RESOURCE);
        assertFalse(r.getAsJsonObject("perk").has("reloadBonus"));
        for (String array : List.of("curves", "timings")) for (var e : r.getAsJsonArray(array)) {
            assertFalse(e.getAsJsonObject().has("reload"));
            assertFalse(e.getAsJsonObject().has("reloadTicks"));
            assertFalse(e.getAsJsonObject().has("baseReloadStat"));
        }
    }
    @Test void manifestSourceAndOutputHashesMatchCurrentOwnedBytes() throws Exception {
        var m = json(ART + "manifest.json");
        assertEquals(65, m.get("selectedCount").getAsInt());
        assertEquals(5, m.get("supportedCount").getAsInt());
        assertEquals(4, m.get("supportedHandlingPlans").getAsInt());
        assertEquals("245114.26.10.13.2000-1-bnet.66137", m.get("manifestVersion").getAsString());
        var pins = m.getAsJsonObject("sourcePins");
        assertEquals("b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c", pins.getAsJsonObject("inventory").get("sha256").getAsString());
        assertEquals("8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959", pins.getAsJsonObject("plugSets").get("sha256").getAsString());
        assertEquals("bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce", pins.getAsJsonObject("manifest").get("sha256").getAsString());
        for (var pin : pins.entrySet()) {
            var row = pin.getValue().getAsJsonObject();
            var path = Path.of(row.get("path").getAsString());
            if (!path.isAbsolute()) {
                assertEquals(row.get("sha256").getAsString(), sha(path), pin.getKey());
                assertEquals(row.get("bytes").getAsLong(), Files.size(path));
            }
        }
        for (var output : m.getAsJsonObject("outputSha256").entrySet())
            assertEquals(output.getValue().getAsString(), sha(Path.of(output.getKey())), output.getKey());
        assertEquals(m.get("generatorSha256").getAsString(), sha(Path.of(m.get("generator").getAsString())));
    }
}
