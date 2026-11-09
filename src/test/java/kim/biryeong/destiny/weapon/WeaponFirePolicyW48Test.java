package kim.biryeong.destiny.weapon;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Pure catalog/artifact tests: no server, registry bootstrap or gameplay integration. */
class WeaponFirePolicyW48Test {
    // Frozen pre-W327 roster assertions retain their original counts; new identities have separate coverage.
    private static final Set<String> BASE = Set.of("auto_rifle", "submachine_gun", "trace_rifle", "machine_gun");
    private static final Map<String, Long> EXPLICIT = Map.of(
            "aishas_embrace", 3920852688L,
            "dead_man_walking_xx7463", 806997698L,
            "ikelos_sg_v1_0_1", 996573084L);

    private static JsonObject artifact(String file) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of("art/weapons/w48", file))).getAsJsonObject();
    }
    private static Map<String, JsonObject> entries(String file) throws Exception {
        Map<String, JsonObject> result = new HashMap<>();
        for (var row : artifact(file).getAsJsonArray("entries")) {
            var r = row.getAsJsonObject();
            assertNull(result.put(r.get("id").getAsString(), r), "Duplicate W48 ID");
        }
        return result;
    }
    private static boolean automatic(String id) {
        return WeaponFirePolicy.supportsAutomatic(WeaponCatalog.find(id).orElseThrow());
    }

    @Test void all63PoliciesExactlyMatchPureHelperAndSelectedOfficialHashes() throws Exception {
        var policies = entries("fire-policy.json");
        var evidence = entries("fire-policy-evidence.json");
        assertEquals(63, WeaponCatalogTest.originalW30Entries().size()); assertEquals(63, policies.size());
        assertEquals(policies.keySet(), evidence.keySet());
        assertEquals(Set.copyOf(WeaponCatalogTest.originalW30Entries().stream().map(WeaponCatalog.Entry::id).toList()), policies.keySet());
        int automaticCount = 0;
        for (var e : WeaponCatalogTest.originalW30Entries()) {
            var row = policies.get(e.id()); assertNotNull(row, e.id());
            assertEquals(e.family(), row.get("family").getAsString());
            assertEquals(WeaponCharacteristics.of(e).bungieHash(), row.get("bungieHash").getAsLong());
            assertEquals(row.get("supportsAutomatic").getAsBoolean(), WeaponFirePolicy.supportsAutomatic(e), e.id());
            assertEquals(row.get("policy"), evidence.get(e.id()).get("policy"));
            if (automatic(e.id())) automaticCount++;
        }
        assertEquals(15, automaticCount);
    }

    @Test void exactThreeAdditionalIdsHaveExplicitOfficialIntrinsicFullAutoText() throws Exception {
        var evidence = entries("fire-policy-evidence.json");
        for (var expected : EXPLICIT.entrySet()) {
            assertTrue(automatic(expected.getKey()));
            var row = evidence.get(expected.getKey());
            var plug = row.getAsJsonObject("intrinsicPlug");
            assertEquals(expected.getValue().longValue(), plug.get("hash").getAsLong());
            assertEquals("Intrinsic", plug.get("itemTypeDisplayName").getAsString());
            assertEquals("intrinsics", plug.get("plugCategoryIdentifier").getAsString());
            assertTrue(plug.get("description").getAsString().toLowerCase(java.util.Locale.ROOT).contains("full auto"));
            assertEquals("EXPLICIT_INTRINSIC_FULL_AUTO", row.get("policy").getAsString());
        }
        assertEquals("Fires full auto with deeper ammo reserves. Faster reload when weapon is empty.",
                evidence.get("aishas_embrace").getAsJsonObject("intrinsicPlug").get("description").getAsString());
        assertEquals("Full auto. Deeper ammo reserves. Slightly faster reload when magazine is empty.",
                evidence.get("dead_man_walking_xx7463").getAsJsonObject("intrinsicPlug").get("description").getAsString());
    }

    @Test void existingAutomaticFamiliesRemainAutomaticAcrossEverySelectedFrame() {
        int count = 0;
        for (var e : WeaponCatalog.all().stream().filter(e -> !LegendaryWeapons.contains(e.id())).toList()) {
            if (BASE.contains(e.family())) { assertTrue(automatic(e.id()), e.id()); count++; }
            else assertEquals(EXPLICIT.containsKey(e.id()), automatic(e.id()), e.id());
        }
        assertEquals(12, count);
        for (var id : Set.of("halfdan_d", "ammit_ar2", "gnawing_hunger", "steelfeather_repeater",
                "antiope_d", "bug_out_bag", "ikelos_smg_v1_0_1", "the_recluse", "retraced_path",
                "fixed_odds", "hammerhead", "retrofit_escapade")) assertTrue(automatic(id), id);
    }

    @Test void rapidFireNameAndSharedGenericPlugCannotEnablePulseFusionSniperOrHeavyGl() throws Exception {
        var evidence = entries("fire-policy-evidence.json");
        for (var id : Set.of("claws_of_the_wolf", "null_composure", "apostate", "canis_major")) {
            assertFalse(automatic(id), id);
            var row = evidence.get(id);
            assertEquals("Rapid-Fire Frame", row.getAsJsonObject("intrinsicPlug").get("name").getAsString());
            assertFalse(row.get("explicitFullAutoText").getAsBoolean());
        }
        assertEquals(878286503L, evidence.get("claws_of_the_wolf").getAsJsonObject("intrinsicPlug").get("hash").getAsLong());
        assertEquals(878286503L, evidence.get("null_composure").getAsJsonObject("intrinsicPlug").get("hash").getAsLong());
        assertEquals(878286503L, evidence.get("steelfeather_repeater").getAsJsonObject("intrinsicPlug").get("hash").getAsLong());
        assertTrue(automatic("steelfeather_repeater")); // Family policy, not a globally automatic plug hash.
        for (var e : WeaponCatalog.all())
            if (Set.of("pulse_rifle", "fusion_rifle", "linear_fusion_rifle").contains(e.family())) assertFalse(automatic(e.id()), e.id());
    }

    @Test void actualFullAutoTriggerSystemTraitsAreRecordedButNeverMisreadAsIntrinsic() throws Exception {
        var evidence = entries("fire-policy-evidence.json");
        int excluded = 0;
        for (var row : evidence.values()) {
            for (var value : row.getAsJsonArray("excludedNonIntrinsicFullAutoSockets")) {
                excluded++;
                var socket = value.getAsJsonObject();
                var plug = socket.getAsJsonObject("initialPlug");
                assertEquals(4267945040L, plug.get("hash").getAsLong());
                assertEquals("Trait", plug.get("itemTypeDisplayName").getAsString());
                assertEquals("Full Auto Trigger System", plug.get("name").getAsString());
                assertNotEquals(row.get("socketIndex"), socket.get("socketIndex"));
                assertFalse(automatic(row.get("id").getAsString()));
            }
        }
        assertEquals(4, excluded);
        for (var id : Set.of("bygones", "chattering_bone", "claws_of_the_wolf", "high_albedo")) {
            assertFalse(automatic(id), id);
            assertEquals(1, evidence.get(id).getAsJsonArray("excludedNonIntrinsicFullAutoSockets").size());
        }
    }

    @Test void everyEvidenceRowConnectsExactSocketInitialHashToIntrinsicPlugDefinition() throws Exception {
        var policies = entries("fire-policy.json");
        for (var entry : entries("fire-policy-evidence.json").entrySet()) {
            var row = entry.getValue();
            var socket = row.getAsJsonObject("socketEntry");
            var plug = row.getAsJsonObject("intrinsicPlug");
            assertTrue(row.get("socketIndex").getAsInt() >= 0);
            assertEquals(socket.get("singleInitialItemHash").getAsLong(), plug.get("hash").getAsLong());
            assertEquals(plug.get("hash").getAsLong(), policies.get(entry.getKey()).get("intrinsicPlugHash").getAsLong());
            assertEquals(1744546145L, plug.get("plugCategoryHash").getAsLong());
            assertEquals("Intrinsic", plug.get("itemTypeDisplayName").getAsString());
            assertEquals("intrinsics", plug.get("plugCategoryIdentifier").getAsString());
            assertTrue(plug.get("definitionCanonicalSha256").getAsString().matches("[a-f0-9]{64}"));
            assertTrue(row.get("itemDefinitionCanonicalSha256").getAsString().matches("[a-f0-9]{64}"));
        }
    }

    @Test void provenancePinsOfficialVersionInventoryAndAllSelectedSourceBytes() throws Exception {
        var evidence = artifact("fire-policy-evidence.json");
        var policy = artifact("fire-policy.json");
        assertEquals("245114.26.10.13.2000-1-bnet.66137", evidence.getAsJsonObject("manifest").get("version").getAsString());
        assertEquals("b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c", evidence.get("inventorySha256").getAsString());
        assertEquals(evidence.get("manifest"), policy.get("manifest"));
        assertEquals(evidence.get("sourceHashes"), policy.get("sourceHashes"));
        assertEquals(63, policy.get("selectedCount").getAsInt());
        assertEquals(15, policy.get("automaticCount").getAsInt());
        assertEquals(evidence.get("firePolicySha256").getAsString(), sha(Files.readAllBytes(Path.of("art/weapons/w48/fire-policy.json"))));
        for (var pin : evidence.getAsJsonObject("sourceHashes").entrySet())
            assertEquals(pin.getValue().getAsString(), sha(Files.readAllBytes(Path.of(pin.getKey()))), pin.getKey());
    }

    @Test void nullUnknownAndForgedCatalogMetadataFailClosedWithoutGlobalAccessibilityFallback() {
        assertFalse(WeaponFirePolicy.supportsAutomatic(null));
        assertFalse(WeaponFirePolicy.supportsAutomatic(new WeaponCatalog.Entry(
                "unknown", "auto_rifle", "rapid_fire", "Unknown", "Rapid-Fire Frame", "destiny:item/unknown")));
        var pulse = WeaponCatalog.find("claws_of_the_wolf").orElseThrow();
        assertFalse(WeaponFirePolicy.supportsAutomatic(new WeaponCatalog.Entry(pulse.id(), "auto_rifle",
                pulse.frame(), pulse.name(), pulse.source_frame_label(), pulse.item_model())));
        for (var id : Set.of("austringer", "long_arm", "frontier_justice", "allied_demand", "brass_attacks",
                "dust_rock_blues", "beloved", "salvager_s_salvo", "bad_omens", "nezarec_s_whisper")) assertFalse(automatic(id), id);
    }

    private static String sha(byte[] raw) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }
}
