package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;
import static org.junit.jupiter.api.Assertions.*;

/** Pure pinned-source, profile validation and arithmetic contracts; no server or live-stack fixtures. */
class FeedingFrenzyProfileTest {
    /** Historical source assertions remain frozen; new identities require exact official tuples. */
    private static java.util.List<WeaponPerks.Roll> legacyRolls() {
        var all = FeedingFrenzyProfile.rolls();
        var added = all.stream().filter(r -> LegendaryWeapons.contains(r.id())).toList();
        assertEquals(java.util.Set.of("brigands_law", "circular_logic", "commemoration", "origin_story"), added.stream().map(WeaponPerks.Roll::id)
            .collect(java.util.stream.Collectors.toSet()));
        for (var roll : added) assertTrue(LegendaryWeapons.exactRoll(roll), roll.toString());
        assertEquals(all.size(), new java.util.HashSet<>(all).size());
        return all.stream().filter(r -> !LegendaryWeapons.contains(r.id())).toList();
    }

    private static final String REF = "art/weapons/w108/references/";
    private static final String RESOURCE = "src/main/resources/destiny/weapons/w108-feeding-frenzy.json";
    private static final int[] BONUSES = {8, 50, 60, 75, 100};
    private static final double[] SCALARS = {.975, .9, .87, .84, .8};

    private static JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }

    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }

    @Test void exactThirteenSocketsDistinguishElevenRandomizedAndTwoCuratedInitialTraits() throws Exception {
        var proof = json(REF + "socket-pools.json");
        assertEquals(63, proof.get("selectedCount").getAsInt());
        assertEquals(13, proof.get("supportedCount").getAsInt());
        assertEquals(11, proof.get("randomizedCount").getAsInt());
        assertEquals(2, proof.get("fixedCuratedCount").getAsInt());
        assertEquals(63, proof.getAsJsonArray("allSelectedPoolScans").size());
        assertEquals(50, proof.getAsJsonArray("unsupportedSelectedIds").size());
        var rolls = legacyRolls();
        assertEquals(13, rolls.size());
        assertEquals(13, rolls.stream().map(WeaponPerks.Roll::id).distinct().count());
        assertThrows(UnsupportedOperationException.class, rolls::clear);
        var seen = new HashSet<String>();
        int randomized = 0, fixed = 0;
        for (var element : proof.getAsJsonArray("weapons")) {
            var row = element.getAsJsonObject();
            String id = row.get("id").getAsString();
            var actual = rolls.stream().filter(r -> r.id().equals(id)).findFirst().orElseThrow();
            var socket = row.getAsJsonObject("socketEntry");
            assertTrue(seen.add(id));
            assertEquals(row.get("hash").getAsLong(), actual.hash());
            assertEquals(row.get("socket").getAsInt(), actual.socket());
            assertEquals(row.get("plugSetHash").getAsLong(), actual.plugSetHash());
            assertEquals(2779035018L, actual.perkHash());
            assertEquals(WeaponCharacteristics.of(entry(id)).bungieHash(), actual.hash());
            assertFalse(WeaponCharacteristics.of(entry(id)).exotic());
            assertEquals(4241085061L, row.get("socketCategoryHash").getAsLong());
            assertEquals(1, row.getAsJsonArray("matchingEntries").size());
            var match = row.getAsJsonArray("matchingEntries").get(0).getAsJsonObject().getAsJsonObject("item");
            assertEquals(FeedingFrenzyProfile.HASH, match.get("plugItemHash").getAsLong());
            assertTrue(match.get("currentlyCanRoll").getAsBoolean());
            if (row.get("selection").getAsString().equals("randomized")) {
                randomized++;
                assertFalse(row.get("isFakePlugSet").getAsBoolean());
                assertEquals(actual.plugSetHash(), socket.get("randomizedPlugSetHash").getAsLong());
            } else {
                fixed++;
                assertEquals("fixedCuratedInitialTrait", row.get("selection").getAsString());
                assertTrue(row.get("isFakePlugSet").getAsBoolean());
                assertFalse(socket.has("randomizedPlugSetHash"));
                assertEquals(FeedingFrenzyProfile.HASH, socket.get("singleInitialItemHash").getAsLong());
                assertEquals(actual.plugSetHash(), socket.get("reusablePlugSetHash").getAsLong());
                var options = row.getAsJsonArray("fixedSelectablePerkHashes").asList().stream()
                    .map(JsonElement::getAsLong).toList();
                if (id.equals("the_recluse")) {
                    assertEquals(242L, actual.plugSetHash());
                    assertEquals(List.of(2779035018L), options);
                } else {
                    assertEquals("null_composure", id);
                    assertEquals(272L, actual.plugSetHash());
                    assertEquals(List.of(2779035018L, 1570042021L), options);
                }
            }
        }
        assertEquals(11, randomized);
        assertEquals(2, fixed);
        assertEquals(13, seen.size());
        assertEquals(Set.of("retraced_path", "fixed_odds", "retrofit_escapade"),
            proof.getAsJsonArray("enhancedOptionsExcluded").asList().stream().map(JsonElement::getAsJsonObject)
                .map(r -> r.get("id").getAsString()).collect(java.util.stream.Collectors.toSet()));
        assertTrue(rolls.stream().noneMatch(r -> r.perkHash() == 1171147302L));
    }

    @Test void exactBaseClaritySourceProvesDurationBonusesAndScalarsButLeavesLifecycleUnknown() throws Exception {
        assertEquals("feeding_frenzy", FeedingFrenzyProfile.ID);
        assertEquals(2779035018L, FeedingFrenzyProfile.HASH);
        assertEquals(70, FeedingFrenzyProfile.durationTicks());
        assertEquals(5, FeedingFrenzyProfile.maxStacks());
        var mechanics = json(REF + "mechanics.json");
        var source = json(REF + "clarity-source.json");
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", source.get("commit").getAsString());
        assertEquals("881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384",
            source.get("sourceFileSha256").getAsString());
        assertEquals("2026-10-08T21:35:34Z", source.get("commitDate").getAsString());
        var base = source.getAsJsonObject("entries").getAsJsonObject("2779035018");
        assertEquals(2779035018L, base.get("hash").getAsLong());
        assertEquals("Weapon Trait", base.get("type").getAsString());
        assertEquals(1766867819246L, base.get("lastUpload").getAsLong());
        String text = mechanics.getAsJsonObject("communitySource").get("text").getAsString();
        assertTrue(text.contains("Weapon Kills grant 1 Stack of Feeding Frenzy for 3.5 seconds"));
        assertTrue(text.contains("Maximum of 5 Stacks."));
        assertTrue(text.contains("8|50|60|75|100 Reload Speed"));
        assertTrue(text.contains("2.5%|10%|13%|16%|20% decreased Reload Animation Duration"));
        assertFalse(mechanics.getAsJsonObject("communitySource").get("primary").getAsBoolean());
        assertEquals("Each rapid kill with this weapon progressively increases reload speed for a short time.",
            mechanics.getAsJsonObject("officialTrigger").get("description").getAsString());
        assertTrue(mechanics.getAsJsonObject("officialTrigger").get("primary").getAsBoolean());
        var policies = FeedingFrenzyProfile.policies();
        assertEquals("UNKNOWN", policies.stowPersistence());
        assertEquals("UNKNOWN", policies.reloadConsumption());
        assertEquals("UNKNOWN", policies.killRefreshAllStacks());
        assertEquals("UNKNOWN", policies.expirationAllOrOneStack());
        assertEquals("AT_RELOAD_START_LOCAL_POLICY", policies.reloadSnapshot());
        for (String field : List.of("stowPersistence", "reloadConsumption", "killRefreshAllStacks", "expirationAllOrOneStack"))
            assertTrue(mechanics.getAsJsonObject("unknownLifecycle").get(field).isJsonNull());
        var tiers = mechanics.getAsJsonArray("tiers");
        assertEquals(5, tiers.size());
        for (int i = 0; i < 5; i++) {
            var tier = tiers.get(i).getAsJsonObject();
            assertEquals(i + 1, tier.get("stacks").getAsInt());
            assertEquals(BONUSES[i], tier.get("reloadBonus").getAsInt());
            assertEquals(SCALARS[i], tier.get("durationMultiplier").getAsDouble());
        }
    }

    @Test void allSixtyFivePlansUseSameHistoricalCurveAsW62WithStatThenScalarThenSingleCeil() throws Exception {
        var evidence = json(REF + "reload-timings.json");
        var formulas = json("art/weapons/w46/weapon_formulas.json");
        var audited = new HashSet<String>();
        int count = 0;
        for (var element : evidence.getAsJsonArray("entries")) {
            var row = element.getAsJsonObject();
            String id = row.get("id").getAsString();
            assertTrue(audited.add(id));
            var weapon = entry(id);
            var curve = row.getAsJsonObject("curve");
            var historical = formulas.getAsJsonObject(row.get("family").getAsString()).getAsJsonObject("cat")
                .getAsJsonObject(row.get("category").getAsString()).getAsJsonObject("reload");
            assertEquals(historical, curve);
            assertFalse(row.get("shellReload").getAsBoolean());
            var baseline = WeaponProfile.forEntry(weapon);
            assertFalse(baseline.shellReload());
            int stat = WeaponCharacteristics.of(weapon).stats().get("4188031367");
            int previous = baseline.reloadTicks();
            for (int stacks = 1; stacks <= 5; stacks++) {
                int effective = Math.min(100, stat + BONUSES[stacks - 1]);
                double seconds = (curve.get("evpp").getAsDouble() * effective * effective
                    + curve.get("vpp").getAsDouble() * effective + curve.get("offset").getAsDouble()) * SCALARS[stacks - 1];
                int expected = (int) Math.ceil(seconds * 20);
                var actual = FeedingFrenzyProfile.reload(weapon, stacks);
                assertEquals(stat, actual.baseReloadStat());
                assertEquals(effective, actual.effectiveReloadStat());
                assertEquals(expected, actual.firstTicks());
                assertEquals(expected, actual.intervalTicks());
                assertTrue(expected <= previous);
                previous = expected;
                count++;
            }
        }
        assertEquals(13, audited.size());
        assertEquals(65, count);
        assertEquals(40, FeedingFrenzyProfile.reload(entry("the_recluse"), 1).firstTicks());
        assertEquals(22, FeedingFrenzyProfile.reload(entry("the_recluse"), 5).firstTicks());
        assertEquals(26, FeedingFrenzyProfile.reload(entry("blast_furnace"), 2).firstTicks());
        assertNotEquals((int) Math.ceil(WeaponProfile.forEntry(entry("the_recluse")).reloadTicks() * .8),
            FeedingFrenzyProfile.reload(entry("the_recluse"), 5).firstTicks());
    }

    @Test void exactSelectedOutlawIsExclusiveButBrassAttacksCanSelectDragonflyAlongsideFeedingFrenzy() throws Exception {
        int outlaw = 0, dragonfly = 0, payload = 0;
        for (var ff : legacyRolls()) {
            for (var other : OutlawProfile.rolls()) if (ff.hash() == other.hash()) {
                outlaw++;
                assertEquals("blast_furnace", ff.id());
                assertEquals(3, ff.socket());
                assertEquals(ff.socket(), other.socket());
                assertEquals(ff.plugSetHash(), other.plugSetHash());
            }
            for (var element : json("src/main/resources/destiny/weapons/w77-dragonfly.json").getAsJsonArray("weapons")) {
                var other = element.getAsJsonObject();
                if (ff.hash() == other.get("hash").getAsLong()) {
                    dragonfly++;
                    assertEquals("brass_attacks", ff.id());
                    assertEquals(3, ff.socket());
                    assertEquals(4, other.get("socket").getAsInt());
                    assertNotEquals(ff.socket(), other.get("socket").getAsInt());
                }
            }
            for (var element : json("src/main/resources/destiny/weapons/w80-payload.json").getAsJsonArray("weapons"))
                if (ff.hash() == element.getAsJsonObject().get("hash").getAsLong()) payload++;
        }
        assertEquals(1, outlaw);
        assertEquals(1, dragonfly);
        assertEquals(0, payload);
        var attribution = json(REF + "mechanics.json").getAsJsonObject("dragonflySecondaryKillFeedingFrenzyCredit");
        assertFalse(attribution.get("verifiedDestinyBehavior").getAsBoolean());
        assertTrue(attribution.get("sourceProven").isJsonNull());
    }

    @Test void sourceAndGeneratedBytesMatchPinsWithoutDependingOnPrivateTempCaches() throws Exception {
        var provenance = json(REF + "provenance.json");
        var sha = MessageDigest.getInstance("SHA-256");
        assertEquals(provenance.get("runtimeSha256").getAsString(),
            HexFormat.of().formatHex(sha.digest(Files.readAllBytes(Path.of(RESOURCE)))));
        assertEquals(provenance.get("generatorSha256").getAsString(),
            HexFormat.of().formatHex(sha.digest(Files.readAllBytes(Path.of("scripts/extract_feeding_frenzy_w108.py")))));
        for (var pin : provenance.getAsJsonObject("sourcePins").entrySet()) {
            var source = pin.getValue().getAsJsonObject();
            var path = Path.of(source.get("path").getAsString());
            if (path.isAbsolute()) continue; // Private official source cache is not required by Java tests.
            assertEquals(source.get("sha256").getAsString(),
                HexFormat.of().formatHex(sha.digest(Files.readAllBytes(path))), pin.getKey());
        }
    }

    private static void rejects(Consumer<JsonObject> edit) throws Exception {
        var data = json(RESOURCE);
        edit.accept(data);
        assertThrows(IllegalStateException.class, () -> FeedingFrenzyProfile.validateResource(data.toString()));
    }

    @Test void strictLoaderRejectsIncompleteMembershipTierMathStatsAndUnprovedPolicies() throws Exception {
        FeedingFrenzyProfile.validateResource(Files.readString(Path.of(RESOURCE)));
        rejects(d -> d.addProperty("stage", "W109"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("durationTicks", 80));
        rejects(d -> d.getAsJsonObject("perk").addProperty("maxStacks", 6));
        rejects(d -> d.getAsJsonArray("weapons").remove(0));
        rejects(d -> d.getAsJsonArray("weapons").add(d.getAsJsonArray("weapons").get(0).deepCopy()));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("hash", 3037520409L));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("socket", 3));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("perkHash", 1171147302L));
        rejects(d -> d.getAsJsonArray("tiers").remove(0));
        rejects(d -> d.getAsJsonArray("tiers").get(0).getAsJsonObject().addProperty("stacks", 2));
        rejects(d -> d.getAsJsonArray("tiers").get(0).getAsJsonObject().addProperty("reloadBonus", 10));
        rejects(d -> d.getAsJsonArray("tiers").get(0).getAsJsonObject().addProperty("durationMultiplier", .9));
        rejects(d -> d.getAsJsonArray("curves").remove(0));
        rejects(d -> d.getAsJsonArray("curves").get(0).getAsJsonObject().addProperty("offset", 3.7));
        rejects(d -> d.getAsJsonArray("reloads").remove(0));
        rejects(d -> d.getAsJsonArray("reloads").get(0).getAsJsonObject().addProperty("stacks", 0));
        rejects(d -> d.getAsJsonArray("reloads").get(0).getAsJsonObject().addProperty("baseReloadStat", 48));
        rejects(d -> d.getAsJsonArray("reloads").get(0).getAsJsonObject().addProperty("effectiveReloadStat", 58));
        rejects(d -> d.getAsJsonArray("reloads").get(0).getAsJsonObject().addProperty("firstTicks", 47));
        rejects(d -> d.getAsJsonArray("reloads").get(0).getAsJsonObject().addProperty("intervalTicks", 47));
        rejects(d -> d.getAsJsonObject("policies").addProperty("stowPersistence", "PROVEN_TRUE"));
        rejects(d -> d.getAsJsonObject("policies").addProperty("reloadConsumption", "PROVEN_FALSE"));
        rejects(d -> d.getAsJsonObject("policies").addProperty("killRefreshAllStacks", "PROVEN_TRUE"));
        rejects(d -> d.getAsJsonObject("policies").addProperty("expirationAllOrOneStack", "ALL"));
        rejects(d -> d.getAsJsonObject("policies").addProperty("reloadSnapshot", "MID_RELOAD_ACCELERATION"));
        rejects(d -> d.getAsJsonObject("policies").addProperty("statCap", 200));
        rejects(d -> d.getAsJsonObject("policies").addProperty("rounding", "ROUND_OLD_TICKS"));
        rejects(d -> d.getAsJsonObject("policies").remove("shellFirstDelay"));
        rejects(d -> d.getAsJsonObject("policies").addProperty("combinedOutlaw", "MULTIPLY_BOTH"));
    }

    @Test void inactiveInvalidUnsupportedAndForgedRequestsAreRejected() {
        for (int stacks : new int[]{Integer.MIN_VALUE, -1, 0, 6, Integer.MAX_VALUE})
            assertThrows(IllegalArgumentException.class, () -> FeedingFrenzyProfile.reload(entry("the_recluse"), stacks));
        assertThrows(IllegalArgumentException.class, () -> FeedingFrenzyProfile.reload(null, 1));
        assertThrows(IllegalArgumentException.class, () -> FeedingFrenzyProfile.reload(entry("bad_omens"), 1));
        var actual = entry("the_recluse");
        var forged = new WeaponCatalog.Entry(actual.id(), "shotgun", actual.frame(), actual.name(),
            actual.source_frame_label(), actual.item_model());
        assertThrows(IllegalArgumentException.class, () -> FeedingFrenzyProfile.reload(forged, 1));
    }
}
