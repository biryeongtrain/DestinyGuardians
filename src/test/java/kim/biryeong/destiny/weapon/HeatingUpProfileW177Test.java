package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;
import static org.junit.jupiter.api.Assertions.*;

class HeatingUpProfileW177Test {
    private static final String TARGET = "src/main/resources/destiny/weapons/w177-heating-up.json";
    private static final String ART = "art/weapons/w177/heating-up/";
    private static final Set<String> IDS = Set.of("farewell", "dream_breaker", "null_composure", "retrofit_escapade");
    private static JsonElement json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path)));
    }
    private static JsonObject object(String path) throws Exception { return json(path).getAsJsonObject(); }
    private static List<WeaponCatalog.Entry> catalog() throws Exception {
        var gson = new Gson();
        var rows = new ArrayList<WeaponCatalog.Entry>();
        for (var e : json("src/main/resources/destiny/weapons/w30.json").getAsJsonArray())
            rows.add(gson.fromJson(e, WeaponCatalog.Entry.class));
        for (var file : List.of("w83-exotics.json", "w84-exotics.json"))
            for (var e : json("src/main/resources/destiny/weapons/" + file).getAsJsonArray())
                rows.add(gson.fromJson(e.getAsJsonObject().get("catalog"), WeaponCatalog.Entry.class));
        return rows;
    }
    private static void rejects(Consumer<JsonObject> change) throws Exception {
        var bad = object(TARGET);
        change.accept(bad);
        assertThrows(IllegalStateException.class, () -> HeatingUpProfile.validateResource(bad.toString()));
    }
    private static String sha(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }

    @Test void exactThreeOfficialBaseSocketsAreImmutable() {
        assertEquals("heating_up", HeatingUpProfile.ID);
        assertEquals(1570042021L, HeatingUpProfile.HASH);
        assertEquals(Set.of(
            new WeaponPerks.Roll("farewell", 541188001L, 3, 1570042021L, 284168234L),
            new WeaponPerks.Roll("dream_breaker", 2931957300L, 3, 1570042021L, 3785896921L),
            new WeaponPerks.Roll("null_composure", 1644680957L, 3, 1570042021L, 272L), // W320 curated fixed roll
            new WeaponPerks.Roll("retrofit_escapade", 3103325054L, 3, 1570042021L, 3756086698L)),
            new HashSet<>(HeatingUpProfile.rolls()));
        assertEquals(4, HeatingUpProfile.rolls().size());
        assertThrows(UnsupportedOperationException.class, () -> HeatingUpProfile.rolls().clear());
    }

    @Test void supportsOnlyCanonicalEntriesFromExactSelected65() throws Exception {
        var entries = catalog();
        assertEquals(65, entries.size());
        assertEquals(entries, WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id()) && !WeaponExotics.expanded(legacy)).toList());
        for (var e : entries) assertEquals(IDS.contains(e.id()), HeatingUpProfile.supports(e), e.id());
        assertFalse(HeatingUpProfile.supports(null));
        assertFalse(HeatingUpProfile.supports(new WeaponCatalog.Entry(null, null, null, null, null, null)));
        for (var e : entries) if (IDS.contains(e.id())) {
            assertTrue(HeatingUpProfile.supports(new WeaponCatalog.Entry(e.id(), e.family(), e.frame(),
                e.name(), e.source_frame_label(), e.item_model())));
            assertFalse(HeatingUpProfile.supports(new WeaponCatalog.Entry(e.id(), "other", e.frame(), e.name(), e.source_frame_label(), e.item_model())));
            assertFalse(HeatingUpProfile.supports(new WeaponCatalog.Entry(e.id(), e.family(), "other", e.name(), e.source_frame_label(), e.item_model())));
            assertFalse(HeatingUpProfile.supports(new WeaponCatalog.Entry(e.id(), e.family(), e.frame(), "other", e.source_frame_label(), e.item_model())));
            assertFalse(HeatingUpProfile.supports(new WeaponCatalog.Entry(e.id(), e.family(), e.frame(), e.name(), "other", e.item_model())));
            assertFalse(HeatingUpProfile.supports(new WeaponCatalog.Entry(e.id(), e.family(), e.frame(), e.name(), e.source_frame_label(), "other")));
        }
    }

    @Test void sourcedTiersAreNeutralAtZeroAndBoundedAtTwo() {
        assertEquals(110, HeatingUpProfile.durationTicks());
        assertEquals(HeatingUpCycle.DURATION_TICKS, HeatingUpProfile.durationTicks());
        for (int n : new int[]{Integer.MIN_VALUE, -1, 0, 1, 2, 3, Integer.MAX_VALUE}) {
            int tier = Math.min(2, Math.max(0, n));
            assertEquals(new int[]{0, 15, 30}[tier], HeatingUpProfile.stabilityBonus(n));
            assertEquals(new int[]{0, 20, 40}[tier], HeatingUpProfile.recoilDirectionBonus(n));
            assertEquals(new double[]{1, .85, .75}[tier], HeatingUpProfile.accuracyScalar(n));
        }
    }

    @Test void malformedSchemaMechanicsAndExtraBonusesFailClosed() throws Exception {
        HeatingUpProfile.validateResource(Files.readString(Path.of(TARGET)));
        rejects(r -> r.addProperty("stage", "W176"));
        rejects(r -> r.addProperty("extra", true));
        rejects(r -> r.remove("weapons"));
        rejects(r -> r.add("perk", JsonNull.INSTANCE));
        for (var edit : List.<Consumer<JsonObject>>of(
            p -> p.addProperty("hash", 2748258257L), p -> p.addProperty("durationTicks", 130),
            p -> p.addProperty("maxStacks", 3), p -> p.addProperty("remainsWhileStowed", false),
            p -> p.add("stabilityBonus", JsonParser.parseString("[0,10,30]")),
            p -> p.add("recoilDirectionBonus", JsonParser.parseString("[0,20,30]")),
            p -> p.add("accuracyScalar", JsonParser.parseString("[1,0.85,0.85]")),
            p -> p.addProperty("handlingBonus", 10), p -> p.addProperty("reloadBonus", 10),
            p -> p.addProperty("damageBonus", 10), p -> p.addProperty("durationTicks", "110")))
            rejects(r -> edit.accept(r.getAsJsonObject("perk")));
        for (var malformed : List.of("null", "[]", "{", "{}"))
            assertThrows(IllegalStateException.class, () -> HeatingUpProfile.validateResource(malformed));
    }

    @Test void malformedRollIdentityCoverageAndUnknownFieldsFailClosed() throws Exception {
        rejects(r -> r.getAsJsonArray("weapons").remove(0));
        rejects(r -> r.getAsJsonArray("weapons").add(r.getAsJsonArray("weapons").get(0)));
        rejects(r -> r.getAsJsonArray("weapons").set(1, r.getAsJsonArray("weapons").get(0)));
        rejects(r -> r.getAsJsonArray("weapons").set(0, JsonNull.INSTANCE));
        for (var edit : List.<Consumer<JsonObject>>of(
            p -> p.addProperty("id", "ace_of_spades"), p -> p.addProperty("hash", 1),
            p -> p.addProperty("socket", 4), p -> p.addProperty("socket", 3.5),
            p -> p.addProperty("socket", "3"), p -> p.addProperty("perkHash", 2748258257L),
            p -> p.addProperty("plugSetHash", 1), p -> p.addProperty("extra", true), p -> p.remove("id")))
            rejects(r -> edit.accept(r.getAsJsonArray("weapons").get(0).getAsJsonObject()));
        assertEquals(4, HeatingUpProfile.rolls().size());
    }

    @Test void scannerEvidenceCovers65AndEveryAcceptedCurrentRandomizedSocket() throws Exception {
        var proof = object(ART + "official-sockets.json");
        assertEquals(65, proof.get("selectedCount").getAsInt());
        assertEquals(65, proof.getAsJsonArray("scans").size());
        var scanned = new HashSet<String>();
        for (var scan : proof.getAsJsonArray("scans"))
            assertTrue(scanned.add(scan.getAsJsonObject().get("id").getAsString()));
        assertEquals(new HashSet<>(catalog().stream().map(WeaponCatalog.Entry::id).toList()), scanned);
        assertEquals(4, proof.getAsJsonArray("accepted").size());
        var accepted = new HashSet<WeaponPerks.Roll>();
        for (var e : proof.getAsJsonArray("accepted")) {
            var p = e.getAsJsonObject();
            var roll = new Gson().fromJson(p, WeaponPerks.Roll.class);
            assertTrue(accepted.add(roll));
            assertEquals(1570042021L, roll.perkHash());
            assertEquals(4241085061L, p.get("socketCategoryHash").getAsLong());
            // W320: curated fixed-roll legendaries use a reusable "fake" plug set as their trait column.
            String field = p.get("plugSetField").getAsString();
            assertTrue(field.equals("randomizedPlugSetHash") || field.equals("reusablePlugSetHash"));
            assertEquals(field.equals("reusablePlugSetHash"), p.get("isFakePlugSet").getAsBoolean());
            assertEquals(roll.plugSetHash(), p.getAsJsonObject("socketEntry").get(field).getAsLong());
            var match = p.getAsJsonArray("matchingEntries").get(0).getAsJsonObject().getAsJsonObject("item");
            assertTrue(match.get("currentlyCanRoll").getAsBoolean());
            assertEquals(1570042021L, match.get("plugItemHash").getAsLong());
        }
        assertEquals(new HashSet<>(HeatingUpProfile.rolls()), accepted);
    }

    @Test void provenancePinsClarityAndAllGeneratedBytes() throws Exception {
        var manifest = object(ART + "manifest.json");
        var clarity = object(ART + "clarity-source.json");
        assertEquals(2748258257L, clarity.get("enhancedExcludedHash").getAsLong());
        assertEquals("881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384", clarity.get("sourceSha256").getAsString());
        assertEquals(object(TARGET).get("perk"), clarity.get("verifiedMechanics"));
        var text = clarity.getAsJsonObject("base").getAsJsonObject("descriptions").toString();
        assertTrue(text.contains("5.5 seconds. Maximum of 2 Stacks."));
        assertTrue(text.contains("Buff remains active while stowed."));
        assertTrue(clarity.get("localPolicy").getAsString().contains("Master owns reload survival"));
        for (var p : manifest.getAsJsonObject("outputs").entrySet()) {
            var path = Path.of(p.getKey());
            assertEquals(p.getValue().getAsJsonObject().get("sha256").getAsString(), sha(path));
            assertEquals(p.getValue().getAsJsonObject().get("bytes").getAsLong(), Files.size(path));
        }
        var generator = manifest.getAsJsonObject("generator");
        assertEquals(generator.get("sha256").getAsString(), sha(Path.of(generator.get("path").getAsString())));
        for (var p : manifest.getAsJsonObject("sources").entrySet()) if (p.getKey().contains("/"))
            assertEquals(p.getValue().getAsJsonObject().get("sha256").getAsString(), sha(Path.of(p.getKey())));
    }
}
