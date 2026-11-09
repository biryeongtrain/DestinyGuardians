package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;
import java.util.stream.Collectors;
import static org.junit.jupiter.api.Assertions.*;

/** Pure profile/source/math tests; no Minecraft server, native input or mutable live stacks. */
class RapidHitProfileW169Test {
    private static final String ART = "art/weapons/w169/rapid-hit/";
    private static final String RESOURCE = "src/main/resources/destiny/weapons/w169-rapid-hit.json";
    private static final int[] BONUSES = {5, 30, 35, 42, 60};
    private static final int[] STABILITY = {2, 12, 14, 18, 25};
    private static final double[] SCALARS = {.99, .96, .95, .945, .92};
    private static final Set<String> IDS = Set.of("duke_mk_44", "patron_of_lost_causes", "long_arm",
        "allied_demand", "lonesome", "brass_attacks", "biting_winds", "bite_of_the_fox", "apostate",
        "line_in_the_sand", "stormchaser");
    private static JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static double solve(JsonObject curve, int stat) {
        return (curve.has("evpp") ? curve.get("evpp").getAsDouble() : 0) * stat * stat
            + (curve.has("vpp") ? curve.get("vpp").getAsDouble() : 0) * stat + curve.get("offset").getAsDouble();
    }
    private static String sha(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }

    @Test void exactElevenOfficialBaseSocketsCoverFullSelected65AndDenyEnhancedCopies() throws Exception {
        var proof = json(ART + "official-sockets.json");
        assertEquals(65, WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList().size());
        assertEquals(65, proof.get("selectedCount").getAsInt());
        assertEquals(11, proof.get("supportedCount").getAsInt());
        assertEquals(11, proof.get("randomizedCount").getAsInt());
        assertEquals(0, proof.get("fixedCuratedCount").getAsInt());
        assertEquals(54, proof.getAsJsonArray("unsupportedSelectedIds").size());
        var scans = proof.getAsJsonArray("allSelectedPoolScans");
        assertEquals(65, scans.size());
        assertEquals(WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList().stream().map(WeaponCatalog.Entry::id).collect(Collectors.toSet()),
            scans.asList().stream().map(e -> e.getAsJsonObject().get("id").getAsString()).collect(Collectors.toSet()));
        var rolls = RapidHitProfile.rolls();
        assertEquals(11, rolls.size());
        assertEquals(IDS, rolls.stream().map(WeaponPerks.Roll::id).collect(Collectors.toSet()));
        assertThrows(UnsupportedOperationException.class, rolls::clear);
        var seen = new HashSet<String>();
        for (var element : proof.getAsJsonArray("weapons")) {
            var row = element.getAsJsonObject();
            String id = row.get("id").getAsString();
            assertTrue(seen.add(id));
            var actual = rolls.stream().filter(r -> r.id().equals(id)).findFirst().orElseThrow();
            assertEquals(row.get("hash").getAsLong(), actual.hash());
            assertEquals(WeaponCharacteristics.of(entry(id)).bungieHash(), actual.hash());
            assertFalse(WeaponCharacteristics.of(entry(id)).exotic());
            assertEquals(row.get("socket").getAsInt(), actual.socket());
            assertEquals(row.get("plugSetHash").getAsLong(), actual.plugSetHash());
            assertEquals(247725512L, actual.perkHash());
            assertEquals(4241085061L, row.get("socketCategoryHash").getAsLong());
            assertEquals("randomized", row.get("selection").getAsString());
            assertEquals("randomizedPlugSetHash", row.get("plugSetField").getAsString());
            assertFalse(row.get("isFakePlugSet").getAsBoolean());
            assertEquals(actual.plugSetHash(), row.getAsJsonObject("socketEntry").get("randomizedPlugSetHash").getAsLong());
            assertEquals(1, row.getAsJsonArray("matchingEntries").size());
            var match = row.getAsJsonArray("matchingEntries").get(0).getAsJsonObject().getAsJsonObject("item");
            assertTrue(match.get("currentlyCanRoll").getAsBoolean());
            assertEquals(RapidHitProfile.HASH, match.get("plugItemHash").getAsLong());
            assertEquals(0, match.get("weight").getAsDouble()); // zero weight does not mean unrollable
        }
        assertEquals(IDS, seen);
        var definitions = proof.getAsJsonArray("perkDefinitions").asList();
        assertEquals(Set.of(247725512L, 2938480696L, 3708253562L, 2578928835L), definitions.stream()
            .map(e -> e.getAsJsonObject().get("hash").getAsLong()).collect(Collectors.toSet()));
        for (var definition : definitions) assertEquals(definition.getAsJsonObject().get("hash").getAsLong() == 247725512L,
            definition.getAsJsonObject().get("accepted").getAsBoolean());
        var duke = rolls.stream().filter(r -> r.id().equals("duke_mk_44")).findFirst().orElseThrow();
        assertEquals(new WeaponPerks.Roll("duke_mk_44", 2112909414L, 2, 247725512L, 3744182842L), duke);
    }

    @Test void exactClarityTriggerIncludesDebuffedBodyHitsAndFiveSourcedTiers() throws Exception {
        assertEquals("rapid_hit", RapidHitProfile.ID);
        assertEquals(247725512L, RapidHitProfile.HASH);
        assertEquals(40, RapidHitProfile.durationTicks());
        assertEquals(5, RapidHitProfile.maxStacks());
        var source = json(ART + "clarity-source.json");
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", source.get("commit").getAsString());
        assertEquals("881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384", source.get("sourceFileSha256").getAsString());
        var base = source.getAsJsonObject("entries").getAsJsonObject("247725512");
        assertEquals(247725512L, base.get("hash").getAsLong());
        assertEquals("Weapon Trait", base.get("type").getAsString());
        assertEquals(1723480728683L, base.get("lastUpload").getAsLong());
        String text = source.getAsJsonObject("communitySource").get("text").getAsString();
        assertTrue(text.contains("grant 1 Stack of Rapid Hit for 2 seconds. Maximum of 5 Stacks."));
        assertTrue(text.contains("Precision Hits or Hits against debuffed targets."));
        assertTrue(text.contains("2|12|14|18|25 Stability"));
        assertTrue(text.contains("5|30|35|42|60 Reload Speed"));
        assertTrue(text.contains("0.99x|0.96x|0.95x|0.945x|0.92x Reload Duration Multiplier"));
        assertFalse(source.getAsJsonObject("communitySource").get("primary").getAsBoolean());
        assertTrue(source.getAsJsonObject("officialTrigger").get("primary").getAsBoolean());
        assertEquals(0, RapidHitProfile.stabilityBonus(0));
        var tiers = source.getAsJsonArray("tiers");
        for (int i = 0; i < 5; i++) {
            var tier = tiers.get(i).getAsJsonObject();
            assertEquals(i + 1, tier.get("stacks").getAsInt());
            assertEquals(STABILITY[i], RapidHitProfile.stabilityBonus(i + 1));
            assertEquals(STABILITY[i], tier.get("stabilityBonus").getAsInt());
            assertEquals(BONUSES[i], tier.get("reloadBonus").getAsInt());
            assertEquals(SCALARS[i], tier.get("durationMultiplier").getAsDouble());
        }
    }

    @Test void sourceUnknownsRemainSeparateFromMastersExplicitLifecyclePolicies() {
        var p = RapidHitProfile.policies();
        assertEquals("UNKNOWN", p.sourceRefreshScope());
        assertEquals("UNKNOWN", p.sourceExpirationMode());
        assertEquals("UNKNOWN", p.sourceStowPersistence());
        assertEquals("UNKNOWN", p.sourceReloadConsumption());
        assertEquals("UNKNOWN", p.sourceReloadSnapshot());
        assertEquals("UNKNOWN", p.sourceCombinedReloadPerks());
        assertEquals("WHOLE_WINDOW_40_TICKS_LOCAL_POLICY", p.hitRefresh());
        assertEquals("READ_ONLY_EXPIRE_LOCAL_POLICY", p.expiration());
        assertEquals("SAME_IDENTITY_CLOCK_CONTINUES_LOCAL_POLICY", p.stowPersistence());
        assertEquals("AT_RELOAD_START_NONCONSUMING_NO_REFRESH_LOCAL_POLICY", p.reloadSnapshot());
        assertEquals("SOURCE_WEAKENED_AT_ACTUAL_IMPACT_LOCAL_MAPPING", p.weakenedBodyHits());
        assertEquals("MINECRAFT_CURVE_MASTER_OWNED_LOCAL_POLICY", p.stabilityIntegration());
        assertEquals("SOURCE_INSERT_UNKNOWN_LOCAL_BASE_PHASE_RATIO", p.longArmTiming());
        assertEquals(100, p.statCap());
        assertEquals(85, p.bowStatCap());
    }

    @Test void all55PlansUsePinnedFamilyCurveStatCapScalarAndOneCeilAndNeverSlow() throws Exception {
        var evidence = json(ART + "reload-timings.json");
        var formulas = json("art/weapons/w46/weapon_formulas.json");
        int count = 0;
        var audited = new HashSet<String>();
        for (var element : evidence.getAsJsonArray("entries")) {
            var row = element.getAsJsonObject();
            String id = row.get("id").getAsString();
            assertTrue(audited.add(id));
            var weapon = entry(id);
            var curve = row.getAsJsonObject("curve");
            assertEquals(formulas.getAsJsonObject(row.get("family").getAsString()).getAsJsonObject("cat")
                .getAsJsonObject(row.get("category").getAsString()).getAsJsonObject("reload"), curve);
            int cap = id.equals("biting_winds") ? 85 : 100;
            assertEquals(cap, row.get("statCap").getAsInt());
            int stat = WeaponCharacteristics.of(weapon).stats().get("4188031367");
            assertEquals(stat, row.get("baseReloadStat").getAsInt());
            int previous = WeaponTiming.forEntry(weapon).reloadTicks().orElseThrow();
            double baseSeconds = solve(curve, Math.min(cap, stat));
            assertEquals(previous, (int) Math.ceil(baseSeconds * 20));
            for (int stacks = 1; stacks <= 5; stacks++) {
                int effective = Math.min(cap, stat + BONUSES[stacks - 1]);
                double seconds = solve(curve, effective) * SCALARS[stacks - 1];
                var plan = RapidHitProfile.reload(weapon, stacks);
                assertEquals(stat, plan.baseReloadStat());
                assertEquals(effective, plan.effectiveReloadStat());
                assertEquals((int) Math.ceil(seconds * 20), plan.firstTicks());
                assertEquals(plan.firstTicks(), plan.intervalTicks());
                assertTrue(plan.firstTicks() <= previous);
                double ratio = RapidHitProfile.reloadMultiplier(weapon, stacks);
                assertEquals(seconds / baseSeconds, ratio, 1e-14);
                assertTrue(ratio > 0 && ratio <= 1);
                previous = plan.firstTicks();
                count++;
            }
        }
        assertEquals(IDS, audited);
        assertEquals(55, count);
        assertEquals(57, RapidHitProfile.reload(entry("duke_mk_44"), 1).firstTicks());
        assertEquals(36, RapidHitProfile.reload(entry("duke_mk_44"), 5).firstTicks());
        assertEquals(41, RapidHitProfile.reload(entry("apostate"), 5).firstTicks());
    }

    @Test void bowPlansAreNockOnlyWith85CapAndDoNotInventMagazineOrChangeDraw() throws Exception {
        var bow = entry("biting_winds");
        var base = WeaponTiming.forEntry(bow);
        assertEquals(14, base.drawTicks().orElseThrow());
        assertTrue(base.magazine().isEmpty());
        assertEquals(16, base.reloadTicks().orElseThrow());
        assertEquals(15, RapidHitProfile.reload(bow, 1).firstTicks());
        assertEquals(12, RapidHitProfile.reload(bow, 5).firstTicks());
        assertEquals(85, RapidHitProfile.reload(bow, 5).effectiveReloadStat());
        assertEquals("HISTORICAL_W46_NOCK_ONLY_DRAW_UNCHANGED", RapidHitProfile.policies().bowTiming());
        var row = json(ART + "reload-timings.json").getAsJsonArray("entries").asList().stream()
            .map(JsonElement::getAsJsonObject).filter(r -> r.get("id").getAsString().equals("biting_winds")).findFirst().orElseThrow();
        assertEquals(14, row.get("drawTicksUnchanged").getAsInt());
    }

    @Test void longArmUsesUnroundedRatioForLocalDistinctPhasesWithoutInventingSourceInsertTiming() throws Exception {
        var arm = entry("long_arm");
        var first = new int[5];
        var interval = new int[5];
        for (int stacks = 1; stacks <= 5; stacks++) {
            double ratio = RapidHitProfile.reloadMultiplier(arm, stacks);
            first[stacks - 1] = (int) Math.ceil(20 * ratio);
            interval[stacks - 1] = (int) Math.ceil(13 * ratio);
            assertTrue(first[stacks - 1] <= 20 && interval[stacks - 1] <= 13);
            assertTrue(first[stacks - 1] > interval[stacks - 1]);
        }
        assertArrayEquals(new int[]{19, 15, 15, 14, 13}, first);
        assertArrayEquals(new int[]{13, 10, 10, 9, 8}, interval);
        var evidence = json(ART + "reload-timings.json").getAsJsonArray("entries").asList().stream()
            .map(JsonElement::getAsJsonObject).filter(r -> r.get("id").getAsString().equals("long_arm")).findFirst().orElseThrow();
        assertEquals("SOURCE_INSERT_UNKNOWN_LOCAL_BASE_PHASE_RATIO", evidence.get("classification").getAsString());
        assertTrue(evidence.get("reloadInitialTicks").isJsonNull());
        assertTrue(evidence.get("phaseRatioPolicy").getAsString().contains("LOCAL approximation"));
        assertNotEquals(RapidHitProfile.reload(arm, 5).firstTicks(), first[4]);
        assertNotEquals(RapidHitProfile.reload(arm, 1).firstTicks() / 42.0, RapidHitProfile.reloadMultiplier(arm, 1));
    }

    @Test void exactExistingReloadPerkCrossSocketPairsAndSameSocketExclusionsAreRecorded() throws Exception {
        var overlaps = json(ART + "official-sockets.json").getAsJsonArray("reloadPerkOverlaps");
        var cross = new HashSet<String>();
        var exclusive = new HashSet<String>();
        assertEquals(7, overlaps.size());
        for (var element : overlaps) {
            var row = element.getAsJsonObject();
            String id = row.get("id").getAsString();
            String perk = row.get("otherPerk").getAsString();
            String key = id + ":" + perk + ":" + row.get("rapidHitSocket").getAsInt() + ":" + row.get("otherSocket").getAsInt();
            if (row.get("crossSocket").getAsBoolean()) cross.add(key); else exclusive.add(key);
            String file = switch (perk) {
                case "outlaw" -> "w62-outlaw.json";
                case "feeding_frenzy" -> "w108-feeding-frenzy.json";
                case "kill_clip" -> "w61-kill-clip.json";
                default -> throw new AssertionError(perk);
            };
            assertTrue(json("src/main/resources/destiny/weapons/" + file).getAsJsonArray("weapons").asList().stream()
                .map(JsonElement::getAsJsonObject).anyMatch(o -> o.get("id").getAsString().equals(id)
                    && o.get("socket").getAsInt() == row.get("otherSocket").getAsInt()
                    && o.get("plugSetHash").getAsLong() == row.get("otherPlugSetHash").getAsLong()));
        }
        assertEquals(Set.of("apostate:outlaw:4:3", "duke_mk_44:kill_clip:2:4", "lonesome:kill_clip:3:4"), cross);
        assertEquals(Set.of("duke_mk_44:outlaw:2:2", "lonesome:outlaw:3:3", "brass_attacks:feeding_frenzy:3:3", "apostate:kill_clip:4:4"), exclusive);
    }

    @Test void sourcePinsAndAllGeneratedBytesMatchManifestWithoutPrivateCacheRequirement() throws Exception {
        var manifest = json(ART + "manifest.json");
        assertEquals(sha(Path.of("scripts/build_rapid_hit_profile_w169.py")), manifest.get("generatorSha256").getAsString());
        for (var pair : manifest.getAsJsonObject("outputSha256").entrySet())
            assertEquals(pair.getValue().getAsString(), sha(Path.of(pair.getKey())), pair.getKey());
        for (var pair : manifest.getAsJsonObject("sourcePins").entrySet()) {
            var pin = pair.getValue().getAsJsonObject();
            var path = Path.of(pin.get("path").getAsString());
            if (!path.isAbsolute()) assertEquals(pin.get("sha256").getAsString(), sha(path), pair.getKey());
        }
    }

    private static void rejects(Consumer<JsonObject> edit) throws Exception {
        var data = json(RESOURCE);
        edit.accept(data);
        assertThrows(IllegalStateException.class, () -> RapidHitProfile.validateResource(data.toString()));
    }
    @Test void validationRejectsCorruptSocketsIncompleteTiersCurvesPlansAndInventedPolicies() throws Exception {
        RapidHitProfile.validateResource(Files.readString(Path.of(RESOURCE)));
        rejects(d -> d.addProperty("stage", "W170"));
        rejects(d -> d.getAsJsonObject("perk").addProperty("durationTicks", 41));
        rejects(d -> d.getAsJsonObject("perk").addProperty("maxStacks", 6));
        rejects(d -> d.getAsJsonArray("weapons").remove(0));
        rejects(d -> d.getAsJsonArray("weapons").add(d.getAsJsonArray("weapons").get(0).deepCopy()));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("hash", 1));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("perkHash", 2938480696L));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("socket", 3));
        rejects(d -> d.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("plugSetHash", 1));
        rejects(d -> d.getAsJsonArray("tiers").remove(0));
        rejects(d -> d.getAsJsonArray("tiers").get(0).getAsJsonObject().addProperty("stacks", 2));
        rejects(d -> d.getAsJsonArray("tiers").get(0).getAsJsonObject().addProperty("stabilityBonus", 10));
        rejects(d -> d.getAsJsonArray("tiers").get(0).getAsJsonObject().addProperty("reloadBonus", 10));
        rejects(d -> d.getAsJsonArray("tiers").get(0).getAsJsonObject().addProperty("durationMultiplier", .9));
        rejects(d -> d.getAsJsonArray("curves").remove(0));
        rejects(d -> d.getAsJsonArray("curves").get(0).getAsJsonObject().addProperty("offset", 0));
        rejects(d -> d.getAsJsonArray("curves").get(6).getAsJsonObject().addProperty("statCap", 100));
        rejects(d -> d.getAsJsonArray("reloads").remove(0));
        rejects(d -> d.getAsJsonArray("reloads").get(0).getAsJsonObject().addProperty("stacks", 0));
        for (String field : List.of("firstTicks", "intervalTicks", "baseReloadStat", "effectiveReloadStat"))
            rejects(d -> d.getAsJsonArray("reloads").get(0).getAsJsonObject().addProperty(field, 999));
        for (String field : List.of("sourceRefreshScope", "sourceExpirationMode", "sourceStowPersistence",
                "sourceReloadConsumption", "sourceReloadSnapshot", "sourceCombinedReloadPerks"))
            rejects(d -> d.getAsJsonObject("policies").addProperty(field, "PROVEN"));
        for (String field : List.of("hitRefresh", "expiration", "stowPersistence", "reloadSnapshot", "weakenedBodyHits",
                "stabilityIntegration", "bowTiming", "longArmTiming", "rounding"))
            rejects(d -> d.getAsJsonObject("policies").remove(field));
    }

    @Test void inactiveInvalidUnsupportedAndForgedRequestsFailClosed() {
        for (int stacks : new int[]{Integer.MIN_VALUE, -1, 0, 6, Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> RapidHitProfile.reload(entry("duke_mk_44"), stacks));
            assertThrows(IllegalArgumentException.class, () -> RapidHitProfile.reloadMultiplier(entry("long_arm"), stacks));
        }
        for (int stacks : new int[]{-1, 6, Integer.MIN_VALUE, Integer.MAX_VALUE})
            assertThrows(IllegalArgumentException.class, () -> RapidHitProfile.stabilityBonus(stacks));
        assertThrows(IllegalArgumentException.class, () -> RapidHitProfile.reload(null, 1));
        for (var unsupported : WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList()) if (!IDS.contains(unsupported.id()))
            assertThrows(IllegalArgumentException.class, () -> RapidHitProfile.reload(unsupported, 1), unsupported.id());
        var actual = entry("duke_mk_44");
        var forged = new WeaponCatalog.Entry(actual.id(), "shotgun", actual.frame(), actual.name(), actual.source_frame_label(), actual.item_model());
        assertThrows(IllegalArgumentException.class, () -> RapidHitProfile.reload(forged, 1));
        assertThrows(IllegalArgumentException.class, () -> RapidHitProfile.reloadMultiplier(forged, 1));
    }

    @Test void freshProfileInitializationAndJsonValidationNeverLoadSelectedRegistries() throws Exception {
        String prefix = "kim.biryeong.destiny.weapon.";
        var forbidden = Set.of(prefix + "WeaponCatalog", prefix + "WeaponCharacteristics", prefix + "WeaponTiming",
            prefix + "WeaponExotics", prefix + "WeaponPerks");
        var isolated = new ClassLoader(getClass().getClassLoader()) {
            @Override protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
                if (forbidden.contains(name)) throw new AssertionError("Recursive registry load: " + name);
                if (!name.startsWith(prefix + "RapidHitProfile")) return super.loadClass(name, resolve);
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
        var type = Class.forName(prefix + "RapidHitProfile", true, isolated);
        assertEquals(40, type.getMethod("durationTicks").invoke(null));
        assertEquals(11, ((List<?>) type.getMethod("rolls").invoke(null)).size());
        var validate = type.getDeclaredMethod("validateResource", String.class);
        validate.setAccessible(true);
        validate.invoke(null, Files.readString(Path.of(RESOURCE)));
    }
}
