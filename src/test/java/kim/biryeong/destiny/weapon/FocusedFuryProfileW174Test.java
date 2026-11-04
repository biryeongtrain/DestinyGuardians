package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.math.BigInteger;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;
import java.util.stream.Collectors;
import static org.junit.jupiter.api.Assertions.*;

/** Pure source/profile/threshold regressions. Shared registry, combat cycle and native QA belong to master. */
class FocusedFuryProfileW174Test {
    private static final String RESOURCE = "src/main/resources/destiny/weapons/w174-focused-fury.json";
    private static final String ART = "art/weapons/w174/focused-fury/";
    private static final Set<String> IDS = Set.of("aishas_embrace", "retraced_path", "fixed_odds");
    private static JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static String sha(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }
    private static void rejects(Consumer<JsonObject> mutation) throws Exception {
        var root = json(RESOURCE);
        mutation.accept(root);
        assertThrows(IllegalStateException.class, () -> FocusedFuryProfile.validateResource(root.toString()));
    }
    @Test void exactBaseApiAndThreeOfficialSocketTuples() {
        assertEquals("focused_fury", FocusedFuryProfile.ID);
        assertEquals(2896038713L, FocusedFuryProfile.HASH);
        assertEquals(220, FocusedFuryProfile.durationTicks());
        assertEquals(1.25f, FocusedFuryProfile.multiplier());
        assertEquals(Set.of(
            new WeaponPerks.Roll("aishas_embrace", 2638190703L, 4, 2896038713L, 4211351701L),
            new WeaponPerks.Roll("retraced_path", 548958835L, 4, 2896038713L, 398391969L),
            new WeaponPerks.Roll("fixed_odds", 2194955522L, 4, 2896038713L, 1686775256L)),
            Set.copyOf(FocusedFuryProfile.rolls()));
    }
    @Test void scannerCoversSelected65IncludingBothExotics() throws Exception {
        var sockets = json(ART + "official-sockets.json");
        assertEquals(65, sockets.get("selectedCount").getAsInt());
        assertEquals(3, sockets.get("supportedCount").getAsInt());
        assertEquals(3, sockets.get("randomizedCount").getAsInt());
        assertEquals(0, sockets.get("fixedCuratedCount").getAsInt());
        assertEquals(62, sockets.getAsJsonArray("unsupportedSelectedIds").size());
        var scan = sockets.getAsJsonArray("selectedScan");
        assertEquals(65, scan.size());
        assertEquals(WeaponCatalog.all().stream().map(WeaponCatalog.Entry::id).collect(Collectors.toSet()),
            scan.asList().stream().map(e -> e.getAsJsonObject().get("id").getAsString()).collect(Collectors.toSet()));
        assertEquals(2, scan.asList().stream().filter(e -> e.getAsJsonObject().get("exotic").getAsBoolean()).count());
        for (var e : WeaponCatalog.all()) assertEquals(IDS.contains(e.id()), FocusedFuryProfile.supports(e));
    }
    @Test void eachProofIsRealRollableBaseTraitPool() throws Exception {
        for (var e : json(ART + "official-sockets.json").getAsJsonArray("weapons")) {
            var r = e.getAsJsonObject();
            assertTrue(IDS.contains(r.get("id").getAsString()));
            assertEquals(4, r.get("socket").getAsInt());
            assertEquals(4241085061L, r.get("socketCategoryHash").getAsLong());
            assertEquals("randomizedPlugSetHash", r.get("plugSetField").getAsString());
            assertFalse(r.get("isFakePlugSet").getAsBoolean());
            assertEquals(r.get("plugSetHash"), r.getAsJsonObject("socketEntry").get("randomizedPlugSetHash"));
            for (var m : r.getAsJsonArray("matchingEntries")) {
                var item = m.getAsJsonObject().getAsJsonObject("item");
                assertEquals(2896038713L, item.get("plugItemHash").getAsLong());
                assertTrue(item.get("currentlyCanRoll").getAsBoolean());
            }
        }
    }
    @Test void enhancedAndUnselectedReferencesDoNotBecomeMembership() throws Exception {
        var defs = json(ART + "official-sockets.json").getAsJsonArray("perkDefinitions");
        assertEquals(Set.of(2896038713L, 2402480669L), defs.asList().stream()
            .map(e -> e.getAsJsonObject().get("hash").getAsLong()).collect(Collectors.toSet()));
        for (var e : defs) {
            var r = e.getAsJsonObject();
            assertEquals(r.get("hash").getAsLong() == 2896038713L, r.get("accepted").getAsBoolean());
        }
        assertFalse(FocusedFuryProfile.supports("cataclysmic"));
        assertFalse(FocusedFuryProfile.supports("ace_of_spades"));
        assertFalse(FocusedFuryProfile.supports("the_recluse"));
        assertFalse(FocusedFuryProfile.supports((String) null));
        assertFalse(FocusedFuryProfile.supports((WeaponCatalog.Entry) null));
    }
    @Test void immutableThresholdsMatchActualCurrentProfilesAndOfficialBaseMagazines() throws Exception {
        Map<String, Integer> magazines = Map.of("aishas_embrace", 17, "retraced_path", 94, "fixed_odds", 44);
        Map<String, Integer> thresholds = Map.of("aishas_embrace", 6, "retraced_path", 33, "fixed_odds", 16);
        for (String id : IDS) {
            var e = entry(id);
            assertEquals(magazines.get(id).intValue(), WeaponProfile.forEntry(e).magazine());
            assertEquals(magazines.get(id).intValue(), WeaponTiming.forEntry(e).magazine().orElseThrow());
            assertEquals(magazines.get(id).intValue(), WeaponCharacteristics.of(e).stats().get("3871231066").intValue());
            assertEquals(thresholds.get(id).intValue(), FocusedFuryProfile.threshold(e));
        }
        var sockets = json(ART + "official-sockets.json");
        assertTrue(sockets.getAsJsonArray("magazineDiscrepancies").isEmpty());
        for (var raw : sockets.getAsJsonArray("magazineAudit")) {
            var a = raw.getAsJsonObject();
            String id = a.get("id").getAsString();
            for (String key : List.of("officialBaseMagazine", "selectedW40Magazine", "currentW46ProfileMagazine"))
                assertEquals(magazines.get(id).intValue(), a.get(key).getAsInt());
            assertEquals(thresholds.get(id).intValue(), a.get("threshold").getAsInt());
            assertFalse(a.get("discrepancy").getAsBoolean());
        }
    }
    @Test void rationalCeilHandlesFractionalBoundariesAndLargestPositiveInt() {
        for (int magazine : new int[]{1, 2, 3, 17, 19, 20, 21, 39, 40, 41, 44, 60, 80, 94, 100, Integer.MAX_VALUE}) {
            int expected = BigInteger.valueOf(magazine).multiply(BigInteger.valueOf(35))
                .add(BigInteger.valueOf(99)).divide(BigInteger.valueOf(100)).intValueExact();
            assertEquals(expected, FocusedFuryProfile.thresholdForMagazine(magazine));
        }
        for (int invalid : new int[]{0, -1, Integer.MIN_VALUE})
            assertThrows(IllegalArgumentException.class, () -> FocusedFuryProfile.thresholdForMagazine(invalid));
    }
    @Test void canonicalIdentityGuardsEveryFieldAndThresholdRejectsUnsupported() {
        var e = entry("aishas_embrace");
        assertTrue(FocusedFuryProfile.supports(new WeaponCatalog.Entry(e.id(), e.family(), e.frame(), e.name(),
            e.source_frame_label(), e.item_model())));
        String[] fields = {e.id(), e.family(), e.frame(), e.name(), e.source_frame_label(), e.item_model()};
        for (int field = 0; field < fields.length; field++) {
            var changed = fields.clone(); changed[field] = "forged";
            var forged = new WeaponCatalog.Entry(changed[0], changed[1], changed[2], changed[3], changed[4], changed[5]);
            assertFalse(FocusedFuryProfile.supports(forged));
            assertThrows(IllegalArgumentException.class, () -> FocusedFuryProfile.threshold(forged));
        }
        assertThrows(IllegalArgumentException.class, () -> FocusedFuryProfile.threshold(null));
        assertThrows(IllegalArgumentException.class, () -> FocusedFuryProfile.threshold(entry("ammit_ar2")));
        assertThrows(UnsupportedOperationException.class, FocusedFuryProfile.rolls()::clear);
    }
    @Test void malformedSelectionCannotForgeEnhancedHashWeaponHashSocketOrPool() throws Exception {
        for (String field : List.of("hash", "socket", "perkHash", "plugSetHash")) {
            rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(field, 1));
            rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().remove(field));
            rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().add(field, JsonNull.INSTANCE));
        }
        rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("perkHash", 2402480669L));
        rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("id", "cataclysmic"));
        rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("socket", 4.1));
        rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("hash", "2638190703"));
        rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("extra", true));
    }
    @Test void missingDuplicateExtraAndNullMembershipFailClosed() throws Exception {
        rejects(r -> r.getAsJsonArray("weapons").remove(0));
        rejects(r -> r.getAsJsonArray("weapons").add(r.getAsJsonArray("weapons").get(0).deepCopy()));
        rejects(r -> r.getAsJsonArray("weapons").set(1, r.getAsJsonArray("weapons").get(0).deepCopy()));
        rejects(r -> r.getAsJsonArray("weapons").set(0, JsonNull.INSTANCE));
        // Resource order is not semantic membership.
        var root = json(RESOURCE);
        var rows = root.getAsJsonArray("weapons");
        var first = rows.remove(0); rows.add(first);
        FocusedFuryProfile.validateResource(root.toString());
    }
    @Test void thresholdsRejectChangedBaseRoundingAndMagazineSelection() throws Exception {
        rejects(r -> r.getAsJsonArray("magazines").get(0).getAsJsonObject().addProperty("baseMagazine", 18));
        rejects(r -> r.getAsJsonArray("magazines").get(0).getAsJsonObject().addProperty("threshold", 5));
        rejects(r -> r.getAsJsonArray("magazines").get(0).getAsJsonObject().addProperty("threshold", 6.1));
        rejects(r -> r.getAsJsonArray("magazines").get(0).getAsJsonObject().remove("threshold"));
        rejects(r -> r.getAsJsonArray("magazines").get(0).getAsJsonObject().addProperty("id", "ammit_ar2"));
        rejects(r -> r.getAsJsonArray("magazines").remove(0));
        rejects(r -> r.getAsJsonArray("magazines").set(1, r.getAsJsonArray("magazines").get(0).deepCopy()));
        rejects(r -> r.getAsJsonArray("magazines").set(0, JsonNull.INSTANCE));
    }
    @Test void outdatedTuningEnhancedDurationAndUndocumentedPoliciesAreRejected() throws Exception {
        rejects(r -> r.getAsJsonObject("perk").addProperty("precisionFraction", .5));
        rejects(r -> r.getAsJsonObject("perk").addProperty("damageMultiplier", 1.2));
        rejects(r -> r.getAsJsonObject("perk").addProperty("durationTicks", 240));
        rejects(r -> r.getAsJsonObject("perk").addProperty("hash", 2402480669L));
        rejects(r -> r.getAsJsonObject("policies").addProperty("refresh", "EVERY_PRECISION_HIT"));
        rejects(r -> r.getAsJsonObject("policies").addProperty("deadline", "PAUSED_WHILE_STOWED"));
        rejects(r -> r.addProperty("reloadBonus", 100));
    }
    @Test void malformedJsonAndMissingSectionsAreRejected() throws Exception {
        FocusedFuryProfile.validateResource(Files.readString(Path.of(RESOURCE)));
        for (String key : json(RESOURCE).keySet()) {
            rejects(r -> r.remove(key));
            rejects(r -> r.add(key, JsonNull.INSTANCE));
        }
        for (String malformed : List.of("null", "[]", "{", "{}", "1", "false"))
            assertThrows(IllegalStateException.class, () -> FocusedFuryProfile.validateResource(malformed));
    }
    @Test void currentClarityAndExternalResearchKeepLocalRefreshPolicyHonest() throws Exception {
        var source = json(ART + "clarity-source.json");
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", source.get("commit").getAsString());
        assertEquals(2402480669L, source.get("enhancedExcludedHash").getAsLong());
        String text = source.getAsJsonObject("base").toString();
        for (String fragment : List.of("35% of the Base Magazine Capacity", "25% increased damage for 11 seconds",
            "Stowing or Reloading the weapon resets the Precision Hit counter", "buff remains active while stowed",
            "Does not buff the Splash/Explosive damage elements of other perks")) assertTrue(text.contains(fragment));
        assertTrue(source.getAsJsonObject("localPolicies").has("counter"));
        assertTrue(source.getAsJsonObject("localPolicies").has("orderingLifecycle"));
        assertFalse(source.getAsJsonArray("unresolved").isEmpty());
        assertEquals("OFFICIAL_PATCH_NOTES", source.getAsJsonArray("externalResearch").get(0)
            .getAsJsonObject().get("kind").getAsString());
    }
    @Test void reproducibleSourcePinsGeneratorAndOutputBytesMatch() throws Exception {
        var m = json(ART + "manifest.json");
        assertEquals(65, m.get("selectedCount").getAsInt());
        assertEquals(3, m.get("supportedCount").getAsInt());
        assertEquals("245114.26.10.13.2000-1-bnet.66137", m.get("manifestVersion").getAsString());
        var pins = m.getAsJsonObject("sourcePins");
        assertEquals("b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c", pins.getAsJsonObject("inventory").get("sha256").getAsString());
        assertEquals("8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959", pins.getAsJsonObject("plugSets").get("sha256").getAsString());
        assertEquals("bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce", pins.getAsJsonObject("manifest").get("sha256").getAsString());
        assertEquals("881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384", pins.getAsJsonObject("clarity").get("sha256").getAsString());
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
